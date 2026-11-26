//go:build linux && amd64

package protectedstore

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"os"
	"regexp"
	"syscall"
	"time"
)

// Cross-process writer arbitration and restart-visible session health
// (manual §§5.2, 5.3.1–5.3.3; ADR B4).
//
// The single provisioned lock is held for the whole life of a Session as a
// process-lifetime lease, so writers and admissions are serialized across
// independent processes: a second process refuses after a bounded wait. A
// Session exists only after the holder's own durable ACTIVE witness; nothing
// that could do work is reachable before that. ACTIVE and CLEAN are
// two-bank control records. Restart relies on device-verified state only
// (Verified), never on process memory, a page-cache reread or an earlier
// holder's barrier. Every state that is not an exact promoted BOOTSTRAP pair
// or a device-verified exact orderly-close pair pauses: nothing is repaired,
// overwritten or reported healthy.

const (
	// ReasonStaleActive: the highest valid control generation is an ACTIVE
	// (including a complete first ACTIVE). Prior-session uncertainty is
	// preserved and reported; no automatic admission.
	ReasonStaleActive Reason = "stale-active"
	// ReasonUnprovenClose: a CLEAN certificate is not the exact orderly-close
	// pair linked to its ACTIVE.
	ReasonUnprovenClose Reason = "unproven-close"
	// ReasonCapacity: the startup capacity check refused or is unavailable.
	ReasonCapacity Reason = "capacity-unavailable"

	sessionPayloadVersion = 1
	maxSessionField       = 256
	sessionIDHexLen       = 32
)

var (
	sessionIDPattern        = regexp.MustCompile(`^[0-9a-f]{32}$`)
	partitionScopePattern   = regexp.MustCompile(`^s-[0-9a-f]{40}$`)
	partitionRequestPattern = regexp.MustCompile(`^r-[0-9a-f]{40}$`)
)

// --- startup capacity seam -------------------------------------------------------

// capacityCheck describes the control transition the startup capacity check
// must cover before ACTIVE may be written.
type capacityCheck struct {
	namespaceID    string
	manifestDigest [32]byte
	nextGeneration uint64
	// holder is the lease holder whose trusted handles the real check observes.
	// It is set only by openSession, which holds its lock.
	holder *holder
}

// capacityChecker is the private startup capacity seam. The only production
// implementation is realCapacity, which performs the real trusted-binding,
// accounting and complete threshold check and has no success path that skips
// it; other implementations exist only in same-package tests and are
// unreachable from exported constructors. A synthetic result is not capacity
// evidence.
type capacityChecker interface {
	checkBeforeActive(capacityCheck) error
}

// productionCapacity is the only checker the exported constructor binds.
func productionCapacity() capacityChecker {
	return realCapacity{}
}

// --- ACTIVE / CLEAN payloads -------------------------------------------------------

// activePayload links a session to the exact generation it started from, the
// manifest and the operator promotion identity.
type activePayload struct {
	namespaceID     string
	sessionID       string
	predKind        bankKind
	predGeneration  uint64
	predDigest      [32]byte
	manifestDigest  [32]byte
	promotionDigest [32]byte
}

// cleanPayload binds the namespace, the exact preceding durable ACTIVE
// generation and session identity. Its own generation is the bank generation.
type cleanPayload struct {
	namespaceID      string
	sessionID        string
	activeGeneration uint64
	activeDigest     [32]byte
	manifestDigest   [32]byte
}

func appendField(out, v []byte) []byte {
	var n [4]byte
	binary.BigEndian.PutUint32(n[:], uint32(len(v)))
	return append(append(out, n[:]...), v...)
}

func appendU64(out []byte, v uint64) []byte {
	var b [8]byte
	binary.BigEndian.PutUint64(b[:], v)
	return append(out, b[:]...)
}

func encodeActive(p activePayload) []byte {
	out := []byte{sessionPayloadVersion, byte(kindActive)}
	out = appendField(out, []byte(p.namespaceID))
	out = appendField(out, []byte(p.sessionID))
	out = append(out, byte(p.predKind))
	out = appendU64(out, p.predGeneration)
	out = append(out, p.predDigest[:]...)
	out = append(out, p.manifestDigest[:]...)
	out = append(out, p.promotionDigest[:]...)
	return out
}

func encodeClean(p cleanPayload) []byte {
	out := []byte{sessionPayloadVersion, byte(kindClean)}
	out = appendField(out, []byte(p.namespaceID))
	out = appendField(out, []byte(p.sessionID))
	out = appendU64(out, p.activeGeneration)
	out = append(out, p.activeDigest[:]...)
	out = append(out, p.manifestDigest[:]...)
	return out
}

type payloadReader struct {
	b   []byte
	bad bool
}

func (r *payloadReader) take(n int) []byte {
	if r.bad || n < 0 || n > len(r.b) {
		r.bad = true
		return nil
	}
	v := r.b[:n]
	r.b = r.b[n:]
	return v
}

func (r *payloadReader) field() []byte {
	n := r.take(4)
	if n == nil {
		return nil
	}
	l := int(binary.BigEndian.Uint32(n))
	if l > maxSessionField {
		r.bad = true
		return nil
	}
	return r.take(l)
}

func (r *payloadReader) u64() uint64 {
	v := r.take(8)
	if v == nil {
		return 0
	}
	return binary.BigEndian.Uint64(v)
}

func (r *payloadReader) digest() (d [32]byte) {
	if v := r.take(32); v != nil {
		copy(d[:], v)
	}
	return d
}

func (r *payloadReader) header(kind bankKind) {
	h := r.take(2)
	if h == nil || h[0] != sessionPayloadVersion || h[1] != byte(kind) {
		r.bad = true
	}
}

func payloadCorrupt() error {
	return refuse(ReasonCorrupt, "session-control payload is malformed", nil)
}

func decodeActive(raw []byte) (activePayload, error) {
	r := &payloadReader{b: raw}
	r.header(kindActive)
	var p activePayload
	p.namespaceID = string(r.field())
	p.sessionID = string(r.field())
	if k := r.take(1); k != nil {
		p.predKind = bankKind(k[0])
	}
	p.predGeneration = r.u64()
	p.predDigest = r.digest()
	p.manifestDigest = r.digest()
	p.promotionDigest = r.digest()
	if r.bad || len(r.b) != 0 || !sessionIDPattern.MatchString(p.sessionID) ||
		!namespaceIDPattern.MatchString(p.namespaceID) ||
		(p.predKind != kindBootstrap && p.predKind != kindClean) {
		return activePayload{}, payloadCorrupt()
	}
	return p, nil
}

func decodeClean(raw []byte) (cleanPayload, error) {
	r := &payloadReader{b: raw}
	r.header(kindClean)
	var p cleanPayload
	p.namespaceID = string(r.field())
	p.sessionID = string(r.field())
	p.activeGeneration = r.u64()
	p.activeDigest = r.digest()
	p.manifestDigest = r.digest()
	if r.bad || len(r.b) != 0 || !sessionIDPattern.MatchString(p.sessionID) ||
		!namespaceIDPattern.MatchString(p.namespaceID) {
		return cleanPayload{}, payloadCorrupt()
	}
	return p, nil
}

// promotionDigest binds the operator promotion identity into every ACTIVE.
func promotionDigest(p Promotion) [32]byte {
	h := sha256.New()
	h.Write([]byte("aiops-protectedstore-promotion\x00"))
	writeLengthPrefixed(h, []byte(p.ManifestDigest))
	writeLengthPrefixed(h, []byte(p.BootstrapDigest))
	writeLengthPrefixed(h, []byte(p.InactiveBankDigest))
	var b [8]byte
	for _, v := range []uint64{p.BootstrapGeneration, p.LockDevice, p.LockInode} {
		binary.BigEndian.PutUint64(b[:], v)
		h.Write(b[:])
	}
	var out [32]byte
	copy(out[:], h.Sum(nil))
	return out
}

// newSessionID derives a session identity from the namespace, the generation
// and predecessor it starts from, and the process and instant of the attempt.
// Uniqueness is not a safety dependency: the lease serializes holders and the
// generation orders them.
func newSessionID(namespaceID string, generation uint64, pred [32]byte) string {
	h := sha256.New()
	h.Write([]byte("aiops-protectedstore-session\x00"))
	writeLengthPrefixed(h, []byte(namespaceID))
	out := appendU64(nil, generation)
	out = append(out, pred[:]...)
	out = appendU64(out, uint64(os.Getpid()))
	out = appendU64(out, uint64(time.Now().UnixNano()))
	h.Write(out)
	return hex.EncodeToString(h.Sum(nil))[:sessionIDHexLen]
}

// --- restart classification ----------------------------------------------------------

type controlDecision struct {
	predKind       bankKind
	pred           bank
	predRaw        []byte
	target         uint8
	nextGeneration uint64
}

// classifyControl applies the manual §5.3.2 startup/restart decision table to
// the control region loaded under the lease. It returns a decision only for
// the two states that permit a new ACTIVE: the exact promoted BOOTSTRAP pair
// and an exact orderly-close pair (CLEAN linked to the ACTIVE in the other
// bank). Every other state refuses; nothing is written.
func (h *holder) classifyControl(promo Promotion) (controlDecision, error) {
	b0, b1 := h.control[0], h.control[1]
	if b0.kind == kindBootstrap && b1.kind == kindInactive {
		if err := h.checkExactBootstrap(); err != nil {
			return controlDecision{}, err
		}
		return controlDecision{
			predKind:       kindBootstrap,
			pred:           b0,
			predRaw:        h.controlRaw[bankOffset(0) : bankOffset(0)+bankUnit],
			target:         1,
			nextGeneration: b0.generation + 1,
		}, nil
	}
	if b0.generation == b1.generation {
		return controlDecision{}, refuse(ReasonCorrupt, "control banks have an ambiguous equal generation", nil)
	}
	hi, lo := uint8(0), uint8(1)
	if b1.generation > b0.generation {
		hi, lo = 1, 0
	}
	high, other := h.control[hi], h.control[lo]
	switch high.kind {
	case kindActive:
		return controlDecision{}, refuse(ReasonStaleActive, "the highest control generation is an ACTIVE session witness; operator-controlled recovery is required", nil)
	case kindClean:
	default:
		return controlDecision{}, refuse(ReasonUnexpectedState, "control region is not a recognized session-control state", nil)
	}
	unproven := func(detail string) (controlDecision, error) {
		return controlDecision{}, refuse(ReasonUnprovenClose, detail, nil)
	}
	if other.kind != kindActive {
		return unproven("CLEAN is not paired with an ACTIVE in the other bank")
	}
	if other.generation == ^uint64(0) || high.generation != other.generation+1 {
		return unproven("CLEAN generation does not follow its ACTIVE")
	}
	cp, err := decodeClean(high.payload)
	if err != nil {
		return controlDecision{}, err
	}
	ap, err := decodeActive(other.payload)
	if err != nil {
		return controlDecision{}, err
	}
	otherRaw := h.controlRaw[bankOffset(lo) : bankOffset(lo)+bankUnit]
	manifestDigest := h.manifestDigest
	switch {
	case cp.namespaceID != h.cfg.NamespaceID || ap.namespaceID != h.cfg.NamespaceID:
		return unproven("session-control namespace identity mismatch")
	case cp.manifestDigest != manifestDigest || ap.manifestDigest != manifestDigest:
		return unproven("session-control manifest binding mismatch")
	case ap.promotionDigest != promotionDigest(promo):
		return unproven("ACTIVE does not carry this operator promotion identity")
	case cp.sessionID != ap.sessionID:
		return unproven("CLEAN session identity differs from its ACTIVE")
	case cp.activeGeneration != other.generation:
		return unproven("CLEAN does not name the exact ACTIVE generation")
	case cp.activeDigest != sha256.Sum256(otherRaw):
		return unproven("CLEAN does not name the exact ACTIVE bank")
	}
	switch ap.predKind {
	case kindBootstrap:
		wantDigest, err := hex.DecodeString(h.manifest.BootstrapDigest)
		if err != nil || len(wantDigest) != 32 || !bytes.Equal(wantDigest, ap.predDigest[:]) ||
			ap.predGeneration != h.manifest.BootstrapGeneration || other.generation != ap.predGeneration+1 {
			return unproven("first ACTIVE is not linked to the bound BOOTSTRAP generation")
		}
	case kindClean:
		if ap.predGeneration == 0 || other.generation != ap.predGeneration+1 {
			return unproven("ACTIVE is not linked to a preceding CLEAN generation")
		}
	}
	return controlDecision{
		predKind:       kindClean,
		pred:           high,
		predRaw:        h.controlRaw[bankOffset(hi) : bankOffset(hi)+bankUnit],
		target:         lo,
		nextGeneration: high.generation + 1,
	}, nil
}

// validateRecordsInventory structurally validates every record region file
// reachable from the records directory: partition names, scope, file type and
// mode, size, both banks, identity and location. A stray, unexpected or
// unclassifiable entry refuses. It does not interpret record content.
func (h *holder) validateRecordsInventory() error {
	bad := func(detail string) error { return refuse(ReasonUnexpectedState, detail, nil) }
	scopes, err := readDirNames(h.recordsFD)
	if err != nil {
		return err
	}
	wantScope := partitionName("s", h.cfg.Scope.Cloud, h.cfg.Scope.Project)
	files := 0
	for _, sname := range scopes {
		if !partitionScopePattern.MatchString(sname) || sname != wantScope {
			return bad("records directory holds an unexpected partition")
		}
		sfd, err := h.openPartition(h.recordsFD, sname, false)
		if err != nil {
			return err
		}
		err = h.validateScopePartition(sfd, sname, &files)
		syscall.Close(sfd)
		if err != nil {
			return err
		}
	}
	return nil
}

func (h *holder) validateScopePartition(sfd int, sname string, files *int) error {
	bad := func(detail string) error { return refuse(ReasonUnexpectedState, detail, nil) }
	requests, err := readDirNames(sfd)
	if err != nil {
		return err
	}
	for _, rname := range requests {
		if !partitionRequestPattern.MatchString(rname) {
			return bad("scope partition holds an unexpected entry")
		}
		rfd, err := h.openPartition(sfd, rname, false)
		if err != nil {
			return err
		}
		names, err := readDirNames(rfd)
		if err == nil {
			for _, name := range names {
				if *files++; *files > maxDirEntries {
					err = refuse(ReasonLimit, "too many record files to validate", nil)
					break
				}
				if err = h.validateRecordFile(rfd, sname, rname, name); err != nil {
					break
				}
			}
		}
		syscall.Close(rfd)
		if err != nil {
			return err
		}
	}
	return nil
}

func (h *holder) validateRecordFile(rfd int, sname, rname, name string) error {
	const suffix = ".rec"
	if len(name) <= len(suffix) || name[len(name)-len(suffix):] != suffix || !recordNamePattern.MatchString(name[:len(name)-len(suffix)]) {
		return refuse(ReasonUnexpectedState, "request partition holds an unexpected entry", nil)
	}
	fd, st, err := h.openStoreFile(rfd, name, syscall.O_RDONLY)
	if err != nil {
		return refuse(ReasonUnsafePath, "record file refused", err)
	}
	defer syscall.Close(fd)
	if st.Size != regionFileSize {
		return refuse(ReasonCorrupt, "record file has unexpected size", nil)
	}
	raw := make([]byte, regionFileSize)
	if err := readFull(fd, raw, 0); err != nil {
		return refuse(ReasonCorrupt, "record file unreadable", err)
	}
	relative := recordsName + "/" + sname + "/" + rname + "/" + name
	cur, _, err := selectRegion(raw, regionIdentity(h.cfg.NamespaceID, relative))
	if err != nil {
		return err
	}
	key, _, err := decodeRecordPayload(cur.payload)
	if err != nil {
		return err
	}
	gotScope, gotRequest, gotFile, _ := key.paths()
	if key.scope != h.cfg.Scope || gotScope != sname || gotRequest != rname || gotFile != name {
		return refuse(ReasonCorrupt, "record identity conflicts with its location", nil)
	}
	return nil
}

// --- session -------------------------------------------------------------------------

// SessionInfo describes an established session witness.
type SessionInfo struct {
	NamespaceID      string
	SessionID        string
	ActiveGeneration uint64
	// Predecessor is "BOOTSTRAP" for the first ACTIVE and "CLEAN" otherwise.
	Predecessor string
	Verify      VerifyReport
	Mount       MountReport
}

// Session is a live holder of the provisioned lock as a process-lifetime
// lease, with this holder's own durable ACTIVE witness. It is constructed
// only after that witness is durable. Releasing the lease (or dying) never
// erases the witness; only an orderly close writes CLEAN.
type Session struct {
	h        *holder
	ctlFD    int
	info     SessionInfo
	active   bank
	activeAt uint8
	raw      []byte
}

// isCapacityRefusal reports whether err is already a distinct capacity outcome
// (binding, managed limit, quota, filesystem or unavailable), which is passed
// through unchanged so the outcomes stay distinguishable.
func isCapacityRefusal(err error) bool {
	for _, r := range []Reason{ReasonCapacity, ReasonCapacityBinding, ReasonManagedLimit, ReasonQuotaExhausted, ReasonFilesystemExhausted} {
		if IsRefusal(err, r) {
			return true
		}
	}
	return false
}

// OpenSession acquires the lease, classifies restart state and, when allowed,
// runs the real startup capacity check and then durably commits this holder's
// ACTIVE. A capacity refusal happens before anything is written.
func OpenSession(cfg Config) (*Session, error) {
	return openSession(cfg, productionMounts(), productionCapacity(), nil)
}

func openSession(cfg Config, src mountOptionSource, capacity capacityChecker, hooks *faultHooks) (*Session, error) {
	if err := cfg.validate(); err != nil {
		return nil, err
	}
	if cfg.InitializationOnly {
		return nil, refuse(ReasonConfig, "initialization-only configuration never opens a session", nil)
	}
	if cfg.Promotion == nil || !cfg.Promotion.complete() {
		return nil, refuse(ReasonUnpromoted, "no complete operator promotion is configured", nil)
	}
	if capacity == nil {
		return nil, refuse(ReasonConfig, "startup capacity checker missing", nil)
	}
	h, err := openLocked(cfg, src, hooks)
	if err != nil {
		return nil, err
	}
	ok := false
	defer func() {
		if !ok {
			h.close()
		}
	}()
	h.mu.Lock()
	defer h.mu.Unlock()

	if err := h.loadState(); err != nil {
		return nil, err
	}
	if err := h.checkPromotion(cfg.Promotion); err != nil {
		return nil, err
	}
	dec, err := h.classifyControl(*cfg.Promotion)
	if err != nil {
		return nil, err
	}
	if dec.predKind == kindClean {
		if err := h.validateRecordsInventory(); err != nil {
			return nil, err
		}
	}
	report, err := h.verified(verifyTarget{dirFD: h.nsFD, name: controlName, fd: h.controlFD, expected: h.controlRaw})
	if err != nil {
		return nil, err
	}
	if dec.pred.generation == ^uint64(0) {
		return nil, refuse(ReasonLimit, "control generation would wrap", nil)
	}
	if err := capacity.checkBeforeActive(capacityCheck{
		namespaceID:    cfg.NamespaceID,
		manifestDigest: h.manifestDigest,
		nextGeneration: dec.nextGeneration,
		holder:         h,
	}); err != nil {
		if isCapacityRefusal(err) {
			return nil, err
		}
		return nil, refuse(ReasonCapacity, "startup capacity check failed", err)
	}
	if err := h.revalidate(); err != nil {
		return nil, err
	}
	if err := h.checkMounts(); err != nil {
		return nil, err
	}

	ctlFD, active, raw, err := h.commitActive(dec, *cfg.Promotion)
	if err != nil {
		return nil, err
	}
	pred := "CLEAN"
	if dec.predKind == kindBootstrap {
		pred = "BOOTSTRAP"
	}
	ap, _ := decodeActive(active.payload)
	s := &Session{
		h:        h,
		ctlFD:    ctlFD,
		active:   active,
		activeAt: dec.target,
		raw:      raw,
		info: SessionInfo{
			NamespaceID:      cfg.NamespaceID,
			SessionID:        ap.sessionID,
			ActiveGeneration: active.generation,
			Predecessor:      pred,
			Verify:           report,
			Mount:            h.lastMount,
		},
	}
	ok = true
	return s, nil
}

// commitActive durably writes this holder's ACTIVE into the target bank under
// the lease: complete bounded write on the validated control file, then the
// holder's own file barrier. Any failure faults the holder and is reported as
// not durable; nothing is retried or repaired. It returns the writable
// descriptor, the ACTIVE bank and the exact expected region bytes.
func (h *holder) commitActive(dec controlDecision, promo Promotion) (int, bank, []byte, error) {
	fd, st, err := h.openStoreFile(h.nsFD, controlName, syscall.O_RDWR)
	if err != nil {
		return -1, bank{}, nil, refuse(ReasonUnsafePath, "control region unavailable for writing", err)
	}
	done := false
	defer func() {
		if !done {
			syscall.Close(fd)
		}
	}()
	id, _, err := identityOf(fd)
	held, _, herr := identityOf(h.controlFD)
	if err != nil || herr != nil || id != held || st.Ino != h.manifest.ControlInode || st.Size != regionFileSize {
		return -1, bank{}, nil, refuse(ReasonUnexpectedState, "control region identity or size changed before the ACTIVE write", nil)
	}
	cur := make([]byte, regionFileSize)
	if err := readFull(fd, cur, 0); err != nil {
		return -1, bank{}, nil, refuse(ReasonCorrupt, "control region unreadable before the ACTIVE write", err)
	}
	if !bytes.Equal(cur, h.controlRaw) {
		return -1, bank{}, nil, refuse(ReasonUnexpectedState, "control region changed after validation", nil)
	}

	predDigest := sha256.Sum256(dec.predRaw)
	payload := encodeActive(activePayload{
		namespaceID:     h.cfg.NamespaceID,
		sessionID:       newSessionID(h.cfg.NamespaceID, dec.nextGeneration, predDigest),
		predKind:        dec.predKind,
		predGeneration:  dec.pred.generation,
		predDigest:      predDigest,
		manifestDigest:  h.manifestDigest,
		promotionDigest: promotionDigest(promo),
	})
	active := bank{index: dec.target, kind: kindActive, generation: dec.nextGeneration, region: regionIdentity(h.cfg.NamespaceID, controlName), payload: payload}
	enc, err := encodeBank(active)
	if err != nil {
		return -1, bank{}, nil, err
	}
	if err := h.writeFull(fd, enc, bankOffset(dec.target)); err != nil {
		return -1, bank{}, nil, h.setFault("incomplete ACTIVE write", err)
	}
	if err := h.fsync(fd, "file"); err != nil {
		return -1, bank{}, nil, h.setFault("ACTIVE sync failed", err)
	}
	raw := append([]byte(nil), h.controlRaw...)
	copy(raw[bankOffset(dec.target):], enc)
	done = true
	return fd, active, raw, nil
}

// Info returns the established session witness description.
func (s *Session) Info() SessionInfo { return s.info }

// CheckBeforeAdmission revalidates the held lease, the namespace entries and
// ancestors, the effective mount options and the durable control region
// against this session's own witness. Memory alone is never health: any
// failure faults the session so no CLEAN can be written over it.
func (s *Session) CheckBeforeAdmission() error {
	h := s.h
	h.mu.Lock()
	defer h.mu.Unlock()
	if err := h.usable(); err != nil {
		return err
	}
	err := h.revalidate()
	if err == nil {
		err = h.checkMounts()
	}
	if err == nil {
		err = s.controlMatchesWitness()
	}
	if err != nil {
		h.fault = err
	}
	return err
}

func (s *Session) controlMatchesWitness() error {
	cur := make([]byte, regionFileSize)
	if err := readFull(s.ctlFD, cur, 0); err != nil {
		return refuse(ReasonCorrupt, "control region unreadable", err)
	}
	if !bytes.Equal(cur, s.raw) {
		return refuse(ReasonUnexpectedState, "control region no longer matches this session's witness", nil)
	}
	return nil
}

// CloseOrderly writes CLEAN, only if this holder is unfaulted, still owns the
// exact control state it wrote and no write has failed, then releases the
// lease. CLEAN goes into the bank holding the generation before this session's
// ACTIVE (the predecessor bank, which this session has superseded). A failed
// or ambiguous CLEAN write is reported, faults the holder and writes nothing
// further; the lease is released either way. The caller must treat a returned
// error as "no orderly close".
func (s *Session) CloseOrderly() error {
	err := s.writeClean()
	s.release()
	return err
}

func (s *Session) writeClean() error {
	h := s.h
	h.mu.Lock()
	defer h.mu.Unlock()
	if err := h.usable(); err != nil {
		return err
	}
	fail := func(err error) error {
		h.fault = err
		return err
	}
	if err := h.revalidate(); err != nil {
		return fail(err)
	}
	if err := h.checkMounts(); err != nil {
		return fail(err)
	}
	if err := s.controlMatchesWitness(); err != nil {
		return fail(err)
	}
	if s.active.generation == ^uint64(0) {
		return fail(refuse(ReasonLimit, "control generation would wrap", nil))
	}
	target := 1 - s.activeAt
	activeRaw := s.raw[bankOffset(s.activeAt) : bankOffset(s.activeAt)+bankUnit]
	ap, err := decodeActive(s.active.payload)
	if err != nil {
		return fail(err)
	}
	clean := bank{
		index:      target,
		kind:       kindClean,
		generation: s.active.generation + 1,
		region:     s.active.region,
		payload: encodeClean(cleanPayload{
			namespaceID:      h.cfg.NamespaceID,
			sessionID:        ap.sessionID,
			activeGeneration: s.active.generation,
			activeDigest:     sha256.Sum256(activeRaw),
			manifestDigest:   h.manifestDigest,
		}),
	}
	enc, err := encodeBank(clean)
	if err != nil {
		return fail(err)
	}
	if err := h.writeFull(s.ctlFD, enc, bankOffset(target)); err != nil {
		return h.setFault("incomplete CLEAN write", err)
	}
	if err := h.fsync(s.ctlFD, "file"); err != nil {
		return h.setFault("CLEAN sync failed", err)
	}
	copy(s.raw[bankOffset(target):], enc)
	return nil
}

// Release releases the lease without writing CLEAN, as process exit would.
// The ACTIVE witness stays in place.
func (s *Session) Release() error {
	s.release()
	return nil
}

func (s *Session) release() {
	h := s.h
	h.mu.Lock()
	if s.ctlFD >= 0 {
		syscall.Close(s.ctlFD)
		s.ctlFD = -1
	}
	h.mu.Unlock()
	h.close()
}

// commitRecord is the only path to a record write from a session, and a
// session exists only after the durable ACTIVE witness.
func (s *Session) commitRecord(k recordKey, value []byte) (uint64, error) {
	return s.h.commitRecord(k, value)
}

// readRecord reads a scoped record through the session's lease.
func (s *Session) readRecord(k recordKey) ([]byte, uint64, error) {
	return s.h.readRecord(k)
}
