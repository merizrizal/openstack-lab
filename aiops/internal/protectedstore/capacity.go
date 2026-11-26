//go:build linux && amd64

package protectedstore

import (
	"errors"
	"fmt"
	"regexp"
	"syscall"
	"unsafe"
)

// Finite managed capacity check (manual §§5.3, 5.3.2, 5.3.4; ADR B4).
//
// The check compares, under the held lease, the trusted identity and policy
// binding recorded at controlled initialization with what is observed now, and
// then requires available filesystem bytes and inodes, remaining managed
// headroom and applicable quota headroom to cover the complete finite need of
// the next transition. It is a point-in-time reading, not a reservation: a
// competing consumer, a quota or mount change or a delayed write error can
// still make a later required write fail, and every such failure stays
// fail-closed. The shared lock serializes only this store's cooperating
// processes and does not prevent competing filesystem consumers.
//
// Everything that decides is pure (decideCapacity, deriveNeed); everything
// that observes is a read-only system call on the trusted store handle
// (fstatfs, quotactl_fd Q_GETFMT/Q_GETQUOTA) plus a validated walk of the
// store's own records. Nothing here writes, repairs, evicts or cleans.

const (
	// maxManagedLimitBytes bounds a usable finite managed-data limit (1 PiB). A
	// larger value is indistinguishable from "unbounded" and is refused.
	maxManagedLimitBytes = 1 << 50
	// quotaBlockUnit is the unit of if_dqblk block limits.
	quotaBlockUnit = 1024
	maxQuotaBytes  = 1 << 60
)

var (
	policyIDPattern    = regexp.MustCompile(`^[a-z0-9][a-z0-9._-]{0,63}$`)
	filesystemIDFormat = regexp.MustCompile(`^[0-9a-f]{16}$`)
)

// QuotaPolicy is the operator-declared association of one quota type with the
// store, bound at controlled initialization. Applies=false asserts that the
// type is not enabled on the store's filesystem; the check verifies that
// assertion at every check instead of trusting it.
type QuotaPolicy struct {
	Applies bool `json:"applies"`
	// SubjectID is the uid (user quota) or gid (group quota) charged for the
	// store's files.
	SubjectID uint32 `json:"subject_id"`
	// BlockLimitBytes and InodeLimit are the enforced effective limits (0 means
	// the corresponding limit is not enforced).
	BlockLimitBytes uint64 `json:"block_limit_bytes"`
	InodeLimit      uint64 `json:"inode_limit"`
	ConfigID        string `json:"config_id"`
	ConfigRevision  uint64 `json:"config_revision"`
}

// CapacityPolicy is the trusted, operator-protected capacity configuration.
// It is compared with the binding recorded in the manifest at every check; it
// is never adopted from observation.
type CapacityPolicy struct {
	PolicyID          string      `json:"policy_id"`
	PolicyRevision    uint64      `json:"policy_revision"`
	ManagedLimitBytes uint64      `json:"managed_limit_bytes"`
	UserQuota         QuotaPolicy `json:"user_quota"`
	GroupQuota        QuotaPolicy `json:"group_quota"`
}

func (q QuotaPolicy) validate(name string) error {
	bad := func(detail string) error { return refuse(ReasonConfig, "capacity policy "+name+": "+detail, nil) }
	if !q.Applies {
		if q.SubjectID != 0 || q.BlockLimitBytes != 0 || q.InodeLimit != 0 || q.ConfigID != "" || q.ConfigRevision != 0 {
			return bad("fields are set although the quota is declared not to apply")
		}
		return nil
	}
	switch {
	case !policyIDPattern.MatchString(q.ConfigID):
		return bad("ConfigID is missing or malformed")
	case q.ConfigRevision == 0:
		return bad("ConfigRevision is required")
	case q.BlockLimitBytes == 0 && q.InodeLimit == 0:
		return bad("an applicable quota must declare at least one enforced limit")
	case q.BlockLimitBytes > maxQuotaBytes || q.BlockLimitBytes%quotaBlockUnit != 0:
		return bad("BlockLimitBytes must be a bounded multiple of 1024")
	}
	return nil
}

// validate checks the structure of a policy. It does not know the store
// owner; Config.validate adds the subject check.
func (p CapacityPolicy) validate() error {
	bad := func(detail string) error { return refuse(ReasonConfig, "capacity policy: "+detail, nil) }
	switch {
	case p.ManagedLimitBytes == 0:
		return bad("a finite managed-data limit is required; ManagedLimitBytes is absent or zero")
	case p.ManagedLimitBytes > maxManagedLimitBytes:
		return bad("ManagedLimitBytes is not a usable finite limit (it exceeds 1 PiB)")
	case !policyIDPattern.MatchString(p.PolicyID):
		return bad("PolicyID is missing or malformed")
	case p.PolicyRevision == 0:
		return bad("PolicyRevision is required")
	}
	if err := p.UserQuota.validate("user quota"); err != nil {
		return err
	}
	return p.GroupQuota.validate("group quota")
}

// capacityBinding is the trusted store, filesystem, quota and managed-limit
// policy binding recorded in the durable manifest at initialization.
type capacityBinding struct {
	FilesystemMagic uint64         `json:"filesystem_magic"`
	FilesystemID    string         `json:"filesystem_id"`
	BlockSize       uint64         `json:"block_size"`
	Policy          CapacityPolicy `json:"policy"`
}

func (b capacityBinding) wellFormed() error {
	switch {
	case b.FilesystemMagic != ext4SuperMagic:
		return refuse(ReasonCorrupt, "manifest capacity binding names an unsupported filesystem", nil)
	case !filesystemIDFormat.MatchString(b.FilesystemID):
		return refuse(ReasonCorrupt, "manifest capacity binding has no usable filesystem identity", nil)
	case b.BlockSize == 0 || b.BlockSize&(b.BlockSize-1) != 0 || bankUnit%b.BlockSize != 0:
		return refuse(ReasonCorrupt, "manifest capacity binding has an unusable block size", nil)
	}
	if err := b.Policy.validate(); err != nil {
		return refuse(ReasonCorrupt, "manifest capacity binding policy is unusable", err)
	}
	return nil
}

// --- finite record layout and the complete threshold ------------------------------------

// capacityLayout holds the reviewed finite record-layout maxima from which the
// complete threshold is derived. The manual selects no numeric values; these
// are conservative design maxima for the §5.3.3 two-bank layout and are
// reviewed with the design, not deployment settings.
type capacityLayout struct {
	// witnessWrites: ACTIVE, the deliberate recovery ACTIVE and CLEAN, each one
	// control bank write.
	witnessWrites uint64
	// One new two-bank record file each for the bounded intent, the maximum
	// sanitized outcome, the recovery/failure-gap/control state, the required
	// scoped acknowledgement, the bounded cleanup-control region and the
	// per-batch cleanup-audit record.
	intentFiles, outcomeFiles, gapFiles, ackFiles uint64
	cleanupControlFiles, cleanupAuditFiles        uint64
	// cleanupBatchRecords bounds the records in one cleanup batch. Each is
	// charged two tombstone bank writes (both banks) and one release/new
	// incarnation bank write.
	cleanupBatchRecords uint64
	// newDirs: a new scope partition and a new request partition.
	newDirs uint64
	// bankUpdatesPerFile: the later intent→outcome style update of a created
	// file. It rewrites an allocated bank in place; it is charged in full as if
	// copy-on-write, because snapshots, reflinks and compression can change
	// effective capacity (manual §5.3.4).
	bankUpdatesPerFile uint64
	// metadataBlocksPerObject: directory-entry growth and one spare extent or
	// index block for each created file or directory.
	metadataBlocksPerObject uint64
}

func reviewedLayout() capacityLayout {
	return capacityLayout{
		witnessWrites: 3,
		intentFiles:   1, outcomeFiles: 1, gapFiles: 1, ackFiles: 1,
		cleanupControlFiles: 1, cleanupAuditFiles: 1,
		cleanupBatchRecords:     8,
		newDirs:                 2,
		bankUpdatesPerFile:      1,
		metadataBlocksPerObject: 2,
	}
}

// capacityNeed is the complete finite need of the next transition. The
// managed charge Mnext equals the byte need Bnext: the manual requires the
// managed and quota byte thresholds to cover the same complete bound.
type capacityNeed struct {
	bytes  uint64 // Bnext = Mnext
	inodes uint64 // Inext
}

func addU(a, b uint64) (uint64, bool) {
	s := a + b
	return s, s >= a
}

func mulU(a, b uint64) (uint64, bool) {
	if a == 0 || b == 0 {
		return 0, true
	}
	p := a * b
	return p, p/a == b
}

func roundUpU(v, unit uint64) (uint64, bool) {
	if unit == 0 {
		return 0, false
	}
	r := v % unit
	if r == 0 {
		return v, true
	}
	return addU(v, unit-r)
}

// sumChecked accumulates overflow-checked terms.
type sumChecked struct {
	v  uint64
	ok bool
}

func (s *sumChecked) add(v uint64, ok bool) {
	if !s.ok {
		return
	}
	s.v, s.ok = addU(s.v, v)
	s.ok = s.ok && ok
}

func (s *sumChecked) addProduct(a, b uint64) {
	p, ok := mulU(a, b)
	s.add(p, ok)
}

// deriveNeed derives the complete finite threshold from the layout and the
// filesystem block size using overflow-checked arithmetic. It refuses when any
// term cannot be computed.
func deriveNeed(l capacityLayout, blockSize uint64) (capacityNeed, error) {
	unusable := func() (capacityNeed, error) {
		return capacityNeed{}, refuse(ReasonCapacity, "the complete capacity threshold cannot be computed", nil)
	}
	if blockSize == 0 {
		return unusable()
	}
	files := sumChecked{ok: true}
	for _, n := range []uint64{l.intentFiles, l.outcomeFiles, l.gapFiles, l.ackFiles, l.cleanupControlFiles, l.cleanupAuditFiles} {
		files.add(n, true)
	}
	objects := sumChecked{v: files.v, ok: files.ok}
	objects.add(l.newDirs, true)
	fileBytes, ok := roundUpU(regionFileSize, blockSize)
	if !ok {
		return unusable()
	}

	bytes := sumChecked{ok: true}
	bytes.addProduct(l.witnessWrites, bankUnit)
	perFile := sumChecked{v: fileBytes, ok: true}
	perFile.addProduct(l.bankUpdatesPerFile, bankUnit)
	bytes.addProduct(files.v, perFile.v)
	bytes.ok = bytes.ok && perFile.ok
	bytes.addProduct(l.cleanupBatchRecords, 2*bankUnit) // tombstone writes, both banks
	bytes.addProduct(l.cleanupBatchRecords, bankUnit)   // release / new incarnation
	bytes.addProduct(l.newDirs, blockSize)
	meta, ok := mulU(l.metadataBlocksPerObject, blockSize)
	bytes.add(0, ok)
	bytes.addProduct(objects.v, meta)
	if !files.ok || !objects.ok || !bytes.ok {
		return unusable()
	}
	return capacityNeed{bytes: bytes.v, inodes: objects.v}, nil
}

// --- observation ----------------------------------------------------------------------------

type quotaState int

const (
	quotaOff quotaState = iota
	quotaOn
	quotaUnknown
)

// quotaObservation is one quota type as seen now. Limits and usage are valid
// only when known is set (enabled and queried).
type quotaObservation struct {
	state      quotaState
	known      bool
	blockLimit uint64 // effective enforced bytes, 0 = none
	inodeLimit uint64 // effective enforced inodes, 0 = none
	usedBytes  uint64
	usedInodes uint64
}

type fsObservation struct {
	magic      uint64
	id         string
	blockSize  uint64
	freeBytes  uint64
	freeInodes uint64
}

type managedUsage struct {
	bytes   uint64
	objects uint64
}

type capacityObservation struct {
	fs      fsObservation
	user    quotaObservation
	group   quotaObservation
	project quotaObservation
	managed managedUsage
}

// quotaReading is the result of a read-only quota query. enabled is false only
// when the kernel definitively reports that the quota type is not enabled.
type quotaReading struct {
	enabled    bool
	haveUsage  bool
	blockLimit uint64
	inodeLimit uint64
	usedBytes  uint64
	usedInodes uint64
}

const (
	userQuotaType  = 0
	groupQuotaType = 1
	projQuotaType  = 2

	qifBlockLimits = 1
	qifSpace       = 2
	qifInodeLimits = 4
	qifInodes      = 8
)

// ifDqblk mirrors struct if_dqblk from include/uapi/linux/quota.h.
type ifDqblk struct {
	BHardLimit uint64
	BSoftLimit uint64
	CurSpace   uint64
	IHardLimit uint64
	ISoftLimit uint64
	CurInodes  uint64
	BTime      uint64
	ITime      uint64
	Valid      uint32
}

func minNonZero(a, b uint64) uint64 {
	switch {
	case a == 0:
		return b
	case b == 0:
		return a
	case a < b:
		return a
	}
	return b
}

// queryQuota is the production quota reader: Q_GETFMT to learn whether the
// type is enabled (no privilege), then Q_GETQUOTA for the declared subject
// (permitted without privilege only for the caller's own uid or a group the
// caller belongs to). It is read-only.
func queryQuota(fd int, qtype int, id uint32, wantUsage bool) (quotaReading, error) {
	var format uint32
	if err := quotactlFD(fd, qcmd(qGetFmt, qtype), 0, unsafe.Pointer(&format)); err != nil {
		if err == syscall.ESRCH {
			return quotaReading{}, nil
		}
		return quotaReading{}, err
	}
	r := quotaReading{enabled: true}
	if !wantUsage {
		return r, nil
	}
	var d ifDqblk
	if err := quotactlFD(fd, qcmd(qGetQuota, qtype), id, unsafe.Pointer(&d)); err != nil {
		return r, err
	}
	const need = qifBlockLimits | qifSpace | qifInodeLimits | qifInodes
	if d.Valid&need != need {
		return r, errors.New("quota query did not report limits and usage")
	}
	bl, ok1 := mulU(minNonZero(d.BHardLimit, d.BSoftLimit), quotaBlockUnit)
	if !ok1 {
		return r, errors.New("quota block limit overflows")
	}
	r.haveUsage = true
	r.blockLimit = bl
	r.inodeLimit = minNonZero(d.IHardLimit, d.ISoftLimit)
	r.usedBytes = d.CurSpace
	r.usedInodes = d.CurInodes
	return r, nil
}

func (h *holder) fstatfsNS() (syscall.Statfs_t, error) {
	if h.hooks != nil && h.hooks.statfs != nil {
		return h.hooks.statfs(h.nsFD)
	}
	var sfs syscall.Statfs_t
	err := syscall.Fstatfs(h.nsFD, &sfs)
	return sfs, err
}

func (h *holder) readQuota(qtype int, id uint32, wantUsage bool) (quotaReading, error) {
	if h.hooks != nil && h.hooks.quota != nil {
		return h.hooks.quota(h.nsFD, qtype, id, wantUsage)
	}
	return queryQuota(h.nsFD, qtype, id, wantUsage)
}

func observeFilesystem(sfs syscall.Statfs_t) (fsObservation, error) {
	if sfs.Bsize <= 0 {
		return fsObservation{}, refuse(ReasonCapacity, "filesystem block size is unavailable", nil)
	}
	bs := uint64(sfs.Bsize)
	free, ok := mulU(sfs.Bavail, bs)
	if !ok {
		return fsObservation{}, refuse(ReasonCapacity, "available filesystem bytes overflow", nil)
	}
	return fsObservation{
		magic:      uint64(sfs.Type),
		id:         fmt.Sprintf("%08x%08x", uint32(sfs.Fsid.X__val[0]), uint32(sfs.Fsid.X__val[1])),
		blockSize:  bs,
		freeBytes:  free,
		freeInodes: sfs.Ffree,
	}, nil
}

// observeQuotaType reads one quota type. A definitive "not enabled" is quotaOff;
// an enabled type whose subject must be charged is queried for limits and
// usage; any other error leaves the state unknown.
func (h *holder) observeQuotaType(qtype int, policy QuotaPolicy) quotaObservation {
	r, err := h.readQuota(qtype, policy.SubjectID, policy.Applies)
	switch {
	case err != nil && !r.enabled:
		return quotaObservation{state: quotaUnknown}
	case !r.enabled:
		return quotaObservation{state: quotaOff}
	case err != nil:
		return quotaObservation{state: quotaOn}
	case !policy.Applies:
		return quotaObservation{state: quotaOn}
	}
	return quotaObservation{
		state: quotaOn, known: r.haveUsage,
		blockLimit: r.blockLimit, inodeLimit: r.inodeLimit, usedBytes: r.usedBytes, usedInodes: r.usedInodes,
	}
}

// observeIdentity reads the filesystem identity and the three quota types with
// the declared subjects. It reads no managed accounting.
func (h *holder) observeIdentity(policy CapacityPolicy) (capacityObservation, error) {
	sfs, err := h.fstatfsNS()
	if err != nil {
		return capacityObservation{}, refuse(ReasonCapacity, "filesystem capacity is unavailable", err)
	}
	fs, err := observeFilesystem(sfs)
	if err != nil {
		return capacityObservation{}, err
	}
	return capacityObservation{
		fs:      fs,
		user:    h.observeQuotaType(userQuotaType, policy.UserQuota),
		group:   h.observeQuotaType(groupQuotaType, policy.GroupQuota),
		project: h.observeQuotaType(projQuotaType, QuotaPolicy{}),
	}, nil
}

// bindingFor builds the binding recorded at controlled initialization from
// the operator policy and the observed filesystem identity.
func bindingFor(policy CapacityPolicy, fs fsObservation) capacityBinding {
	return capacityBinding{FilesystemMagic: fs.magic, FilesystemID: fs.id, BlockSize: fs.blockSize, Policy: policy}
}

// --- managed accounting ------------------------------------------------------------------

// accountManaged recomputes the durable managed usage U from validated store
// records: the manifest, the control region, the records directory and every
// partition directory and record file, each charged by its logical size
// rounded up to the filesystem block size plus the per-object metadata
// allowance. Every allocated file is charged whatever its logical state, so
// incomplete, retained, reusable and ambiguous records are charged
// conservatively and nothing is ever treated as reclaimed. It never uses
// filesystem free space or st_blocks. An entry it cannot validate refuses.
func (h *holder) accountManaged(layout capacityLayout, blockSize uint64) (managedUsage, error) {
	if err := h.validateRecordsInventory(); err != nil {
		return managedUsage{}, err
	}
	meta, ok := mulU(layout.metadataBlocksPerObject, blockSize)
	if !ok {
		return managedUsage{}, refuse(ReasonCapacity, "managed charge cannot be computed", nil)
	}
	u := sumChecked{ok: true}
	var objects uint64
	charge := func(size int64, dir bool) error {
		if size < 0 {
			return refuse(ReasonCorrupt, "store object reports a negative size", nil)
		}
		logical := uint64(size)
		if dir && logical < blockSize {
			logical = blockSize
		}
		rounded, ok := roundUpU(logical, blockSize)
		u.add(rounded, ok)
		u.add(meta, true)
		objects++
		if !u.ok {
			return refuse(ReasonCapacity, "managed usage overflows", nil)
		}
		return nil
	}

	mfd, mst, err := h.openStoreFile(h.nsFD, manifestName, syscall.O_RDONLY)
	if err != nil {
		return managedUsage{}, refuse(ReasonUnsafePath, "manifest unavailable for accounting", err)
	}
	syscall.Close(mfd)
	if err := charge(mst.Size, false); err != nil {
		return managedUsage{}, err
	}
	for _, o := range []struct {
		fd  int
		dir bool
	}{{h.controlFD, false}, {h.recordsFD, true}} {
		var st syscall.Stat_t
		if err := syscall.Fstat(o.fd, &st); err != nil {
			return managedUsage{}, refuse(ReasonUnsafePath, "store object unavailable for accounting", err)
		}
		if err := charge(st.Size, o.dir); err != nil {
			return managedUsage{}, err
		}
	}

	scopes, err := readDirNames(h.recordsFD)
	if err != nil {
		return managedUsage{}, err
	}
	files := 0
	for _, sname := range scopes {
		sfd, err := h.openPartition(h.recordsFD, sname, false)
		if err != nil {
			return managedUsage{}, err
		}
		err = h.accountPartition(sfd, true, charge, &files)
		syscall.Close(sfd)
		if err != nil {
			return managedUsage{}, err
		}
	}
	return managedUsage{bytes: u.v, objects: objects}, nil
}

// accountPartition charges a scope partition and, beneath it, each request
// partition and record file.
func (h *holder) accountPartition(fd int, scope bool, charge func(int64, bool) error, files *int) error {
	var st syscall.Stat_t
	if err := syscall.Fstat(fd, &st); err != nil {
		return refuse(ReasonUnsafePath, "partition unavailable for accounting", err)
	}
	if err := charge(st.Size, true); err != nil {
		return err
	}
	names, err := readDirNames(fd)
	if err != nil {
		return err
	}
	for _, name := range names {
		if scope {
			child, err := h.openPartition(fd, name, false)
			if err != nil {
				return err
			}
			err = h.accountPartition(child, false, charge, files)
			syscall.Close(child)
			if err != nil {
				return err
			}
			continue
		}
		if *files++; *files > maxDirEntries {
			return refuse(ReasonLimit, "too many record files to account", nil)
		}
		rfd, rst, err := h.openStoreFile(fd, name, syscall.O_RDONLY)
		if err != nil {
			return refuse(ReasonUnsafePath, "record file refused during accounting", err)
		}
		syscall.Close(rfd)
		if err := charge(rst.Size, false); err != nil {
			return err
		}
	}
	return nil
}

// --- the decision --------------------------------------------------------------------------

func bindingMismatch(detail string) error {
	return refuse(ReasonCapacityBinding, detail+"; admission stays closed pending controlled operator revalidation", nil)
}

// checkQuotaBinding verifies one quota type against its bound declaration.
func checkQuotaBinding(name string, bound QuotaPolicy, o quotaObservation) error {
	if o.state == quotaUnknown {
		return refuse(ReasonCapacity, name+" quota state cannot be determined and cannot be ruled out", nil)
	}
	if !bound.Applies {
		if o.state == quotaOn {
			return bindingMismatch(name + " quota is enabled but the trusted binding declares none")
		}
		return nil
	}
	if o.state != quotaOn {
		return bindingMismatch(name + " quota is declared by the trusted binding but is not enabled")
	}
	if !o.known {
		return refuse(ReasonCapacity, name+" quota is applicable but its limits and remaining allowance cannot be queried", nil)
	}
	if o.blockLimit != bound.BlockLimitBytes || o.inodeLimit != bound.InodeLimit {
		return bindingMismatch(name + " quota enforced limits differ from the trusted binding")
	}
	return nil
}

// checkBinding compares what is observed now and the operator configuration
// with the trusted initialization binding. Ordinary free-space, inode and
// quota-usage readings are not compared; a changed or unverifiable identity or
// policy refuses and is never adopted.
func checkBinding(cfg CapacityPolicy, bound capacityBinding, obs capacityObservation) error {
	if cfg != bound.Policy {
		return bindingMismatch("operator capacity configuration differs from the trusted initialization binding")
	}
	if obs.fs.magic != bound.FilesystemMagic || obs.fs.id != bound.FilesystemID || obs.fs.blockSize != bound.BlockSize {
		return bindingMismatch("the store's filesystem identity differs from the trusted initialization binding")
	}
	if err := checkQuotaBinding("user", bound.Policy.UserQuota, obs.user); err != nil {
		return err
	}
	if err := checkQuotaBinding("group", bound.Policy.GroupQuota, obs.group); err != nil {
		return err
	}
	// Project quota cannot be queried without privilege; if it is enabled it
	// may apply to the store and its allowance cannot be established.
	switch obs.project.state {
	case quotaUnknown:
		return refuse(ReasonCapacity, "project quota state cannot be determined and cannot be ruled out", nil)
	case quotaOn:
		return refuse(ReasonCapacity, "project quota is enabled and its remaining allowance cannot be queried without privilege", nil)
	}
	return nil
}

func checkManaged(limit uint64, used uint64, need capacityNeed) error {
	if used > limit {
		return refuse(ReasonManagedLimit, "durable managed usage exceeds the managed-data limit", nil)
	}
	if limit-used < need.bytes {
		return refuse(ReasonManagedLimit, "remaining managed capacity is below the complete threshold", nil)
	}
	return nil
}

func checkFilesystem(fs fsObservation, need capacityNeed) error {
	if fs.freeBytes < need.bytes {
		return refuse(ReasonFilesystemExhausted, "available filesystem bytes are below the complete threshold", nil)
	}
	if fs.freeInodes < need.inodes {
		return refuse(ReasonFilesystemExhausted, "available filesystem inodes are below the complete threshold", nil)
	}
	return nil
}

func checkQuotaHeadroom(name string, bound QuotaPolicy, o quotaObservation, need capacityNeed) error {
	if !bound.Applies {
		return nil
	}
	if o.blockLimit != 0 && (o.usedBytes > o.blockLimit || o.blockLimit-o.usedBytes < need.bytes) {
		return refuse(ReasonQuotaExhausted, name+" quota byte headroom is below the complete threshold", nil)
	}
	if o.inodeLimit != 0 && (o.usedInodes > o.inodeLimit || o.inodeLimit-o.usedInodes < need.inodes) {
		return refuse(ReasonQuotaExhausted, name+" quota inode headroom is below the complete threshold", nil)
	}
	return nil
}

// decideCapacity is the single decision: identity and policy binding first,
// then managed, filesystem and applicable quota headroom against the complete
// need. It returns nil only after every step.
func decideCapacity(cfg CapacityPolicy, bound capacityBinding, obs capacityObservation, need capacityNeed) error {
	if err := checkBinding(cfg, bound, obs); err != nil {
		return err
	}
	if err := checkManaged(bound.Policy.ManagedLimitBytes, obs.managed.bytes, need); err != nil {
		return err
	}
	if err := checkFilesystem(obs.fs, need); err != nil {
		return err
	}
	if err := checkQuotaHeadroom("user", bound.Policy.UserQuota, obs.user, need); err != nil {
		return err
	}
	if err := checkQuotaHeadroom("group", bound.Policy.GroupQuota, obs.group, need); err != nil {
		return err
	}
	return nil
}

// checkCapacity performs the real startup check under the held lease: observe
// the filesystem and quota against the manifest's trusted binding, recompute
// managed usage from validated records, derive the complete threshold and
// decide. It writes nothing.
func (h *holder) checkCapacity() error {
	bound := h.manifest.Capacity
	if err := bound.wellFormed(); err != nil {
		return err
	}
	obs, err := h.observeIdentity(bound.Policy)
	if err != nil {
		return err
	}
	if err := checkBinding(h.cfg.Capacity, bound, obs); err != nil {
		return err
	}
	layout := reviewedLayout()
	need, err := deriveNeed(layout, obs.fs.blockSize)
	if err != nil {
		return err
	}
	if obs.managed, err = h.accountManaged(layout, obs.fs.blockSize); err != nil {
		return err
	}
	return decideCapacity(h.cfg.Capacity, bound, obs, need)
}

// bindAtInitialization observes the filesystem and quota before anything is
// created and refuses unless they match the operator policy, so a recorded
// binding is never one that the first check would refuse.
func (h *holder) bindAtInitialization() (capacityBinding, error) {
	obs, err := h.observeIdentity(h.cfg.Capacity)
	if err != nil {
		return capacityBinding{}, err
	}
	bound := bindingFor(h.cfg.Capacity, obs.fs)
	if err := bound.wellFormed(); err != nil {
		return capacityBinding{}, refuse(ReasonConfig, "the filesystem cannot be bound as a capacity identity", err)
	}
	if err := checkBinding(h.cfg.Capacity, bound, obs); err != nil {
		return capacityBinding{}, err
	}
	return bound, nil
}

// --- distinct failure outcomes ------------------------------------------------------------

type failureKind string

const (
	failureManagedLimit failureKind = "managed-limit"
	failureQuota        failureKind = "quota"
	failureFilesystem   failureKind = "filesystem"
	failureOther        failureKind = "other"
)

// failureKindOf separates managed-limit exhaustion, quota exhaustion (EDQUOT),
// actual filesystem or inode exhaustion (ENOSPC) and any other write, sync or
// device error. It classifies; it never relaxes fail-closed handling.
func failureKindOf(err error) failureKind {
	switch {
	case err == nil:
		return ""
	case IsRefusal(err, ReasonManagedLimit):
		return failureManagedLimit
	case IsRefusal(err, ReasonQuotaExhausted) || errors.Is(err, syscall.EDQUOT):
		return failureQuota
	case IsRefusal(err, ReasonFilesystemExhausted) || errors.Is(err, syscall.ENOSPC):
		return failureFilesystem
	}
	return failureOther
}

// realCapacity is the only production capacity checker. It always performs the
// real check through the holder that owns the lease; a missing holder refuses.
type realCapacity struct{}

func (realCapacity) checkBeforeActive(req capacityCheck) error {
	if req.holder == nil {
		return refuse(ReasonCapacity, "startup capacity check has no store to observe; admission stays closed", nil)
	}
	return req.holder.checkCapacity()
}
