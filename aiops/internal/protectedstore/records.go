//go:build linux && amd64

package protectedstore

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"regexp"
	"syscall"
)

// Scoped two-bank records. These primitives are unexported: no production
// path writes records before a durable session witness exists (a later
// chunk). Values are bounded, already-sanitized opaque bytes; this package
// cannot and does not sanitize or inspect them.

var (
	requestIDPattern  = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$`)
	recordNamePattern = regexp.MustCompile(`^[a-z][a-z0-9-]{0,31}$`)
)

type recordKey struct {
	scope     Scope
	requestID string
	name      string
}

func (k recordKey) validate() error {
	if err := validateScope(k.scope); err != nil {
		return err
	}
	if !requestIDPattern.MatchString(k.requestID) || !recordNamePattern.MatchString(k.name) {
		return refuse(ReasonConfig, "record key is invalid", nil)
	}
	return nil
}

// partitionName derives a directory name from identifiers without placing
// the identifiers themselves in a filesystem name.
func partitionName(prefix string, parts ...string) string {
	h := sha256.New()
	h.Write([]byte("aiops-protectedstore-partition\x00" + prefix + "\x00"))
	for _, p := range parts {
		writeLengthPrefixed(h, []byte(p))
	}
	return prefix + "-" + hex.EncodeToString(h.Sum(nil))[:40]
}

func (k recordKey) paths() (scopeDir, requestDir, file, relative string) {
	scopeDir = partitionName("s", k.scope.Cloud, k.scope.Project)
	requestDir = partitionName("r", k.requestID)
	file = k.name + ".rec"
	relative = recordsName + "/" + scopeDir + "/" + requestDir + "/" + file
	return
}

func encodeRecordPayload(k recordKey, value []byte) []byte {
	var out []byte
	for _, part := range [][]byte{[]byte(k.scope.Cloud), []byte(k.scope.Project), []byte(k.requestID), []byte(k.name), value} {
		var n [4]byte
		binary.BigEndian.PutUint32(n[:], uint32(len(part)))
		out = append(out, n[:]...)
		out = append(out, part...)
	}
	return out
}

func decodeRecordPayload(raw []byte) (recordKey, []byte, error) {
	parts := make([][]byte, 0, 5)
	for len(parts) < 5 {
		if len(raw) < 4 {
			return recordKey{}, nil, refuse(ReasonCorrupt, "record payload truncated", nil)
		}
		n := int(binary.BigEndian.Uint32(raw[:4]))
		raw = raw[4:]
		if n > len(raw) {
			return recordKey{}, nil, refuse(ReasonCorrupt, "record payload length out of bounds", nil)
		}
		parts = append(parts, raw[:n])
		raw = raw[n:]
	}
	if len(raw) != 0 {
		return recordKey{}, nil, refuse(ReasonCorrupt, "record payload has trailing bytes", nil)
	}
	k := recordKey{scope: Scope{Cloud: string(parts[0]), Project: string(parts[1])}, requestID: string(parts[2]), name: string(parts[3])}
	return k, append([]byte(nil), parts[4]...), nil
}

// selectRegion validates both banks and returns the current record bank and
// the index of the bank that may be overwritten. Zero, torn, conflicting or
// otherwise unclassifiable banks refuse; nothing is repaired.
func selectRegion(raw []byte, region [32]byte) (bank, uint8, error) {
	var banks [2]bank
	for i := uint8(0); i < 2; i++ {
		b, state, err := decodeBank(raw[bankOffset(i):bankOffset(i)+bankUnit], i, region)
		if err != nil {
			return bank{}, 0, err
		}
		if state != bankValid {
			return bank{}, 0, refuse(ReasonCorrupt, "record bank is unclassifiable", nil)
		}
		switch b.kind {
		case kindRecord:
		case kindEmpty:
			if b.generation != 0 || len(b.payload) != 0 {
				return bank{}, 0, refuse(ReasonCorrupt, "empty bank is malformed", nil)
			}
		default:
			return bank{}, 0, refuse(ReasonCorrupt, "record region holds an unexpected bank kind", nil)
		}
		banks[i] = b
	}
	if banks[0].generation == banks[1].generation {
		return bank{}, 0, refuse(ReasonCorrupt, "record banks have an ambiguous equal generation", nil)
	}
	cur, other := uint8(0), uint8(1)
	if banks[1].generation > banks[0].generation {
		cur, other = 1, 0
	}
	if banks[cur].kind != kindRecord {
		return bank{}, 0, refuse(ReasonCorrupt, "record region has no current record", nil)
	}
	return banks[cur], other, nil
}

// openPartition opens (creating durably when create is set) one partition
// directory beneath parentFD.
func (h *holder) openPartition(parentFD int, name string, create bool) (int, error) {
	fd, err := openat2(parentFD, name, syscall.O_RDONLY|syscall.O_DIRECTORY|syscall.O_NOFOLLOW, 0)
	if err == syscall.ENOENT && create {
		if err := h.mkdirDurable(parentFD, name); err != nil {
			return -1, err
		}
		fd, err = openat2(parentFD, name, syscall.O_RDONLY|syscall.O_DIRECTORY|syscall.O_NOFOLLOW, 0)
	}
	if err != nil {
		if err == syscall.ENOENT {
			return -1, refuse(ReasonUnexpectedState, "record partition absent", err)
		}
		return -1, refuse(ReasonUnsafePath, "record partition traversal refused", err)
	}
	if _, _, err := h.validateStoreObject(fd, true); err != nil {
		syscall.Close(fd)
		return -1, err
	}
	return fd, nil
}

// commitRecord durably commits value as the next generation of the scoped
// record. A new record is created by exclusive temporary creation, complete
// write, file sync, no-replace rename and directory sync. An existing record
// is updated by writing the complete next generation into its inactive bank
// and syncing the file; the previously valid bank is never touched. Any
// failure faults the holder and is never reported as saved.
func (h *holder) commitRecord(k recordKey, value []byte) (uint64, error) {
	h.mu.Lock()
	defer h.mu.Unlock()
	if err := h.usable(); err != nil {
		return 0, err
	}
	if h.recordsFD < 0 {
		return 0, refuse(ReasonUnexpectedState, "store state is not loaded", nil)
	}
	if err := k.validate(); err != nil {
		return 0, err
	}
	if k.scope != h.cfg.Scope {
		return 0, refuse(ReasonScope, "record scope differs from the namespace's authorized scope", nil)
	}
	payload := encodeRecordPayload(k, value)
	if len(payload) > maxBankPayload {
		return 0, refuse(ReasonLimit, "record value exceeds the bank bound", nil)
	}
	scopeDir, requestDir, file, relative := k.paths()
	region := regionIdentity(h.cfg.NamespaceID, relative)

	sfd, err := h.openPartition(h.recordsFD, scopeDir, true)
	if err != nil {
		return 0, err
	}
	defer syscall.Close(sfd)
	rfd, err := h.openPartition(sfd, requestDir, true)
	if err != nil {
		return 0, err
	}
	defer syscall.Close(rfd)

	fd, st, err := h.openStoreFile(rfd, file, syscall.O_RDWR)
	if err == syscall.ENOENT {
		first, err := encodeBank(bank{index: 0, kind: kindRecord, generation: 1, region: region, payload: payload})
		if err != nil {
			return 0, err
		}
		empty, err := encodeBank(bank{index: 1, kind: kindEmpty, generation: 0, region: region})
		if err != nil {
			return 0, err
		}
		if err := h.createFileDurable(rfd, file, append(first, empty...), true); err != nil {
			return 0, err
		}
		return 1, nil
	}
	if err != nil {
		return 0, refuse(ReasonUnsafePath, "record file refused", err)
	}
	defer syscall.Close(fd)
	if st.Size != regionFileSize {
		return 0, refuse(ReasonCorrupt, "record file has unexpected size", nil)
	}
	raw := make([]byte, regionFileSize)
	if err := readFull(fd, raw, 0); err != nil {
		return 0, refuse(ReasonCorrupt, "record file unreadable", err)
	}
	cur, target, err := selectRegion(raw, region)
	if err != nil {
		return 0, err
	}
	if storedKey, _, err := decodeRecordPayload(cur.payload); err != nil {
		return 0, err
	} else if storedKey != k {
		return 0, refuse(ReasonCorrupt, "record identity conflicts with its location", nil)
	}
	if cur.generation == ^uint64(0) {
		return 0, refuse(ReasonLimit, "record generation would wrap", nil)
	}
	next := cur.generation + 1
	encoded, err := encodeBank(bank{index: target, kind: kindRecord, generation: next, region: region, payload: payload})
	if err != nil {
		return 0, err
	}
	if err := h.writeFull(fd, encoded, bankOffset(target)); err != nil {
		return 0, h.setFault("incomplete bank write", err)
	}
	if err := h.fsync(fd, "file"); err != nil {
		return 0, h.setFault("bank sync failed", err)
	}
	return next, nil
}

// readRecord returns the current generation of a scoped record after full
// validation of both banks, identity and scope.
func (h *holder) readRecord(k recordKey) ([]byte, uint64, error) {
	h.mu.Lock()
	defer h.mu.Unlock()
	if h.closed {
		return nil, 0, refuse(ReasonClosed, "store holder is closed", nil)
	}
	if h.recordsFD < 0 {
		return nil, 0, refuse(ReasonUnexpectedState, "store state is not loaded", nil)
	}
	if err := k.validate(); err != nil {
		return nil, 0, err
	}
	if k.scope != h.cfg.Scope {
		return nil, 0, refuse(ReasonScope, "record scope differs from the namespace's authorized scope", nil)
	}
	scopeDir, requestDir, file, relative := k.paths()
	sfd, err := h.openPartition(h.recordsFD, scopeDir, false)
	if err != nil {
		return nil, 0, err
	}
	defer syscall.Close(sfd)
	rfd, err := h.openPartition(sfd, requestDir, false)
	if err != nil {
		return nil, 0, err
	}
	defer syscall.Close(rfd)
	fd, st, err := h.openStoreFile(rfd, file, syscall.O_RDONLY)
	if err != nil {
		if err == syscall.ENOENT {
			return nil, 0, refuse(ReasonUnexpectedState, "record absent", err)
		}
		return nil, 0, refuse(ReasonUnsafePath, "record file refused", err)
	}
	defer syscall.Close(fd)
	if st.Size != regionFileSize {
		return nil, 0, refuse(ReasonCorrupt, "record file has unexpected size", nil)
	}
	raw := make([]byte, regionFileSize)
	if err := readFull(fd, raw, 0); err != nil {
		return nil, 0, refuse(ReasonCorrupt, "record file unreadable", err)
	}
	cur, _, err := selectRegion(raw, regionIdentity(h.cfg.NamespaceID, relative))
	if err != nil {
		return nil, 0, err
	}
	storedKey, value, err := decodeRecordPayload(cur.payload)
	if err != nil {
		return nil, 0, err
	}
	if storedKey != k {
		return nil, 0, refuse(ReasonCorrupt, "record identity conflicts with its location", nil)
	}
	return value, cur.generation, nil
}
