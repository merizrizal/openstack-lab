//go:build linux && amd64

// Package protectedstore is the protected, versioned storage primitive for
// manual-diagnostic state (task §6; ADR B4–B5; manual §§5.1, 5.3.1, 5.3.3,
// 5.3.5). It accepts only bounded, already-sanitized opaque values and does
// not import the diagnostic package or any authorization type.
//
// The package provides initialization-only namespace creation, validation of
// an operator-promoted BOOTSTRAP pair, the Verified device-readback
// primitive, the effective mount-option check, two-bank durable records and
// the cross-process session lease with restart-safe ACTIVE/CLEAN session
// control (admission.go), and the finite managed capacity check that runs
// before the first ACTIVE write (capacity.go). The check is a point-in-time
// reading, not a reservation. No request dispatch, per-dispatch recheck,
// recovery or cleanup is implemented here.
package protectedstore

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"syscall"
	"time"
	"unicode/utf8"
)

// Reason classifies a refusal. Every refusal keeps admission closed.
type Reason string

const (
	ReasonConfig                 Reason = "invalid-configuration"
	ReasonUnsafePath             Reason = "unsafe-path"
	ReasonOwnership              Reason = "ownership-or-mode"
	ReasonLock                   Reason = "lock"
	ReasonMountOptions           Reason = "mount-options"
	ReasonAlignment              Reason = "alignment"
	ReasonCorrupt                Reason = "corrupt"
	ReasonVersion                Reason = "unsupported-version"
	ReasonUnexpectedState        Reason = "unexpected-state"
	ReasonUnpromoted             Reason = "unpromoted"
	ReasonPromotionMismatch      Reason = "promotion-mismatch"
	ReasonNotDurable             Reason = "not-durable"
	ReasonFaulted                Reason = "faulted"
	ReasonVerifyUnsupported      Reason = "verify-unsupported"
	ReasonVerifyMismatch         Reason = "verify-mismatch"
	ReasonCacheDeviceDiscrepancy Reason = "cache-device-discrepancy"
	ReasonLegacy                 Reason = "legacy-overlap"
	ReasonScope                  Reason = "scope"
	ReasonLimit                  Reason = "limit"
	ReasonClosed                 Reason = "closed"

	// Capacity outcomes (capacity.go). ReasonCapacity itself (declared in
	// admission.go) means the check is unavailable, unverifiable or uncomputable.
	ReasonCapacityBinding     Reason = "capacity-binding"
	ReasonManagedLimit        Reason = "managed-limit-exhausted"
	ReasonQuotaExhausted      Reason = "quota-exhausted"
	ReasonFilesystemExhausted Reason = "filesystem-exhausted"
)

// RefusalError is returned for every refused operation. Detail never contains
// stored payload bytes.
type RefusalError struct {
	Reason Reason
	Detail string
	Err    error
}

func (e *RefusalError) Error() string {
	msg := "protected store refused (" + string(e.Reason) + "): " + e.Detail
	if e.Err != nil {
		msg += ": " + e.Err.Error()
	}
	return msg
}

func (e *RefusalError) Unwrap() error { return e.Err }

func refuse(reason Reason, detail string, err error) error {
	return &RefusalError{Reason: reason, Detail: detail, Err: err}
}

// IsRefusal reports whether err is a refusal with the given reason.
func IsRefusal(err error, reason Reason) bool {
	var r *RefusalError
	return errors.As(err, &r) && r.Reason == reason
}

const (
	maxLockWait        = 60 * time.Second
	lockPollInterval   = 5 * time.Millisecond
	maxPathComponents  = 16
	maxScopeBytes      = 128
	maxLegacyRoots     = 16
	maxManifestBytes   = 8 << 10
	maxDirEntries      = 4096
	maxWriteIterations = 4096

	manifestName = "MANIFEST"
	controlName  = "control"
	recordsName  = "records"

	bootstrapGeneration = 1
	inactiveGeneration  = 0

	// manifestFormatVersion 2 added the capacity binding. A version 1 manifest
	// is refused as unsupported; it is never silently upgraded or adopted.
	manifestFormatVersion = 2
)

var (
	namespaceIDPattern = regexp.MustCompile(`^[a-z0-9][a-z0-9-]{0,63}$`)
	componentPattern   = regexp.MustCompile(`^[A-Za-z0-9_][A-Za-z0-9._-]{0,127}$`)
	digestPattern      = regexp.MustCompile(`^[0-9a-f]{64}$`)
	manifestMagic      = []byte("AIOPSMF1\n")
	manifestSumPrefix  = []byte("sha256:")
)

// Scope is the namespace's authorized cloud/project scope. Both values are
// bounded, already-sanitized local identifiers supplied by trusted
// configuration; they are never derived from request content.
type Scope struct {
	Cloud   string
	Project string
}

// Promotion is the operator's independently protected existing-namespace
// binding (manual §5.3.1). The runtime cannot create, revert or renew it.
type Promotion struct {
	ManifestDigest      string
	BootstrapGeneration uint64
	BootstrapDigest     string
	InactiveBankDigest  string
	LockDevice          uint64
	LockInode           uint64
}

// Config is trusted, operator-protected configuration. Paths are resolved
// handle-relatively beneath RootPath; identities bind the provisioned lock and
// namespace directory.
type Config struct {
	RootPath           string
	NamespacePath      string
	NamespaceDevice    uint64
	NamespaceInode     uint64
	NamespaceID        string
	LockPath           string
	LockDevice         uint64
	LockInode          uint64
	StoreOwnerUID      uint32
	TrustedOwnerUIDs   []uint32
	Scope              Scope
	LegacyRoots        []string
	LockWait           time.Duration
	InitializationOnly bool
	Promotion          *Promotion
	// Capacity is the independently protected finite managed-data limit and
	// quota/policy association. It is compared with the binding recorded in the
	// manifest at every capacity check and is never adopted from observation.
	Capacity CapacityPolicy
}

func (c Config) validate() error {
	bad := func(detail string) error { return refuse(ReasonConfig, detail, nil) }
	if c.RootPath == "" || !filepath.IsAbs(c.RootPath) || filepath.Clean(c.RootPath) != c.RootPath {
		return bad("root path must be absolute and clean")
	}
	nsParts, err := splitRelative(c.NamespacePath)
	if err != nil {
		return bad("namespace path: " + err.Error())
	}
	lockParts, err := splitRelative(c.LockPath)
	if err != nil {
		return bad("lock path: " + err.Error())
	}
	if len(lockParts) < 2 {
		return bad("lock must be inside an operator-controlled directory beneath the root")
	}
	if isComponentPrefix(nsParts, lockParts) || isComponentPrefix(lockParts, nsParts) {
		return bad("namespace and lock paths must not contain one another")
	}
	if !namespaceIDPattern.MatchString(c.NamespaceID) {
		return bad("namespace identity is invalid")
	}
	if c.NamespaceInode == 0 || c.LockInode == 0 {
		return bad("namespace and lock identities are required")
	}
	if err := validateScope(c.Scope); err != nil {
		return err
	}
	if len(c.TrustedOwnerUIDs) == 0 {
		return bad("trusted owner set is required")
	}
	if c.LockWait <= 0 || c.LockWait > maxLockWait {
		return bad("lock wait must be positive and bounded")
	}
	if len(c.LegacyRoots) > maxLegacyRoots {
		return bad("too many legacy roots")
	}
	for _, root := range c.LegacyRoots {
		if !filepath.IsAbs(root) || filepath.Clean(root) != root {
			return bad("legacy roots must be absolute and clean")
		}
	}
	if c.InitializationOnly && c.Promotion != nil {
		return bad("initialization-only configuration cannot carry a promotion")
	}
	if err := c.Capacity.validate(); err != nil {
		return err
	}
	if q := c.Capacity.UserQuota; q.Applies && q.SubjectID != c.StoreOwnerUID {
		return bad("capacity policy user quota: SubjectID must be the store owner uid")
	}
	return nil
}

func validateScope(s Scope) error {
	for _, v := range []string{s.Cloud, s.Project} {
		if v == "" || len(v) > maxScopeBytes || !utf8.ValidString(v) {
			return refuse(ReasonScope, "scope values must be non-empty bounded UTF-8", nil)
		}
		for _, r := range v {
			if r < 0x20 || r == 0x7f {
				return refuse(ReasonScope, "scope values must not contain control characters", nil)
			}
		}
	}
	return nil
}

func (p Promotion) complete() bool {
	return digestPattern.MatchString(p.ManifestDigest) && digestPattern.MatchString(p.BootstrapDigest) &&
		digestPattern.MatchString(p.InactiveBankDigest) && p.BootstrapGeneration != 0 && p.LockInode != 0
}

func splitRelative(p string) ([]string, error) {
	if p == "" || strings.HasPrefix(p, "/") {
		return nil, errors.New("must be a non-empty relative path")
	}
	parts := strings.Split(p, "/")
	if len(parts) > maxPathComponents {
		return nil, errors.New("too many components")
	}
	for _, part := range parts {
		if part == "." || part == ".." || !componentPattern.MatchString(part) {
			return nil, errors.New("unsafe component")
		}
	}
	return parts, nil
}

func isComponentPrefix(prefix, full []string) bool {
	if len(prefix) > len(full) {
		return false
	}
	for i := range prefix {
		if prefix[i] != full[i] {
			return false
		}
	}
	return true
}

// faultHooks is an injectable fault seam for same-package tests only.
// Exported constructors always pass nil; a nil seam uses the real system
// calls. The seam is not evidence of device behaviour (manual A2).
type faultHooks struct {
	pwrite      func(fd int, p []byte, off int64) (int, error)
	fsync       func(fd int, kind string) error
	rename      func(olddirfd int, oldname string, newdirfd int, newname string) error
	statxDio    func(fd int) (statxT, error)
	directFlags func(fd int) (int, error)
	allocBuffer func(n int) ([]byte, func(), error)
	directRead  func(fd int, p []byte, off int64) (int, error)
	// statfs and quota replace the read-only capacity observations. They are not
	// capacity evidence on the supported stack and never reach production.
	statfs func(fd int) (syscall.Statfs_t, error)
	quota  func(fd int, qtype int, id uint32, wantUsage bool) (quotaReading, error)
}

// holder owns the provisioned lock, namespace handles and loaded state. All
// operations are serialized by mu, so the ordinary and direct reads of a bank
// never run concurrently with a writer in this process.
type holder struct {
	mu     sync.Mutex
	cfg    Config
	mounts mountOptionSource
	hooks  *faultHooks

	rootFD    int
	nsFD      int
	lockFD    int
	controlFD int
	recordsFD int

	closed bool
	fault  error

	manifest       manifestBody
	manifestDigest [32]byte
	control        [2]bank
	controlRaw     []byte
	lastMount      MountReport
}

type fileIdentity struct{ dev, ino uint64 }

func identityOf(fd int) (fileIdentity, syscall.Stat_t, error) {
	var st syscall.Stat_t
	if err := syscall.Fstat(fd, &st); err != nil {
		return fileIdentity{}, st, err
	}
	return fileIdentity{dev: uint64(st.Dev), ino: st.Ino}, st, nil
}

func (h *holder) trustedOwner(uid uint32) bool {
	for _, t := range h.cfg.TrustedOwnerUIDs {
		if t == uid {
			return true
		}
	}
	return false
}

func checkNoACL(fd int) error {
	acl, err := hasACL(fd)
	if err != nil {
		return refuse(ReasonOwnership, "ACL state unavailable", err)
	}
	if acl {
		return refuse(ReasonOwnership, "unexpected ACL", nil)
	}
	return nil
}

func (h *holder) validateTrustedDir(fd int) (fileIdentity, error) {
	id, st, err := identityOf(fd)
	if err != nil {
		return id, refuse(ReasonUnsafePath, "ancestor stat failed", err)
	}
	if st.Mode&syscall.S_IFMT != syscall.S_IFDIR {
		return id, refuse(ReasonUnsafePath, "ancestor is not a directory", nil)
	}
	if !h.trustedOwner(st.Uid) {
		return id, refuse(ReasonOwnership, "ancestor owner is not trusted", nil)
	}
	if st.Mode&0o022 != 0 {
		return id, refuse(ReasonOwnership, "ancestor is group- or other-writable", nil)
	}
	return id, checkNoACL(fd)
}

func (h *holder) validateNamespaceDir(fd int) (fileIdentity, error) {
	id, st, err := identityOf(fd)
	if err != nil {
		return id, refuse(ReasonUnsafePath, "namespace stat failed", err)
	}
	if st.Mode&syscall.S_IFMT != syscall.S_IFDIR {
		return id, refuse(ReasonUnsafePath, "namespace is not a directory", nil)
	}
	if id.dev != h.cfg.NamespaceDevice || id.ino != h.cfg.NamespaceInode {
		return id, refuse(ReasonUnsafePath, "namespace identity does not match trusted configuration", nil)
	}
	if st.Uid != h.cfg.StoreOwnerUID || st.Mode&0o7777 != 0o700 {
		return id, refuse(ReasonOwnership, "namespace owner or mode is not as provisioned", nil)
	}
	return id, checkNoACL(fd)
}

func (h *holder) validateLockFile(fd int) (fileIdentity, error) {
	id, st, err := identityOf(fd)
	if err != nil {
		return id, refuse(ReasonLock, "lock stat failed", err)
	}
	if st.Mode&syscall.S_IFMT != syscall.S_IFREG {
		return id, refuse(ReasonLock, "lock is not a regular file", nil)
	}
	if st.Nlink != 1 {
		return id, refuse(ReasonLock, "lock has unexpected link count", nil)
	}
	if id.dev != h.cfg.LockDevice || id.ino != h.cfg.LockInode {
		return id, refuse(ReasonLock, "lock identity does not match trusted configuration", nil)
	}
	if !h.trustedOwner(st.Uid) || st.Mode&0o7777&0o222 != 0 || st.Mode&0o7000 != 0 {
		return id, refuse(ReasonOwnership, "lock owner or mode permits replacement or writes", nil)
	}
	return id, checkNoACL(fd)
}

func (h *holder) validateStoreObject(fd int, wantDir bool) (fileIdentity, syscall.Stat_t, error) {
	id, st, err := identityOf(fd)
	if err != nil {
		return id, st, refuse(ReasonUnsafePath, "store object stat failed", err)
	}
	if id.dev != h.cfg.NamespaceDevice {
		return id, st, refuse(ReasonUnsafePath, "store object is on another device", nil)
	}
	if wantDir {
		if st.Mode&syscall.S_IFMT != syscall.S_IFDIR {
			return id, st, refuse(ReasonUnsafePath, "store object is not a directory", nil)
		}
		if st.Mode&0o7777 != 0o700 {
			return id, st, refuse(ReasonOwnership, "store directory mode is not 0700", nil)
		}
	} else {
		if st.Mode&syscall.S_IFMT != syscall.S_IFREG {
			return id, st, refuse(ReasonUnsafePath, "store object is not a regular file", nil)
		}
		if st.Mode&0o7777 != 0o600 {
			return id, st, refuse(ReasonOwnership, "store file mode is not 0600", nil)
		}
		if st.Nlink != 1 {
			return id, st, refuse(ReasonUnsafePath, "store file has unexpected link count", nil)
		}
	}
	if st.Uid != h.cfg.StoreOwnerUID {
		return id, st, refuse(ReasonOwnership, "store object owner is not the store owner", nil)
	}
	return id, st, checkNoACL(fd)
}

// openTrustedRoot opens the operator-configured trusted starting directory.
func (h *holder) openTrustedRoot() (int, fileIdentity, error) {
	fd, err := syscall.Open(h.cfg.RootPath, syscall.O_RDONLY|syscall.O_DIRECTORY|syscall.O_NOFOLLOW|syscall.O_CLOEXEC, 0)
	if err != nil {
		return -1, fileIdentity{}, refuse(ReasonUnsafePath, "trusted root unavailable", err)
	}
	id, err := h.validateTrustedDir(fd)
	if err != nil {
		syscall.Close(fd)
		return -1, id, err
	}
	return fd, id, nil
}

// walkAncestors opens each directory component beneath dirFD with openat2,
// validating each as a trusted ancestor. It returns the last directory's fd
// and every visited identity. The caller owns the returned fd.
func (h *holder) walkAncestors(dirFD int, parts []string) (int, []fileIdentity, error) {
	current := dirFD
	owned := false
	var ids []fileIdentity
	for _, part := range parts {
		next, err := openat2(current, part, syscall.O_RDONLY|syscall.O_DIRECTORY|syscall.O_NOFOLLOW, 0)
		if owned {
			syscall.Close(current)
		}
		if err != nil {
			return -1, ids, refuse(ReasonUnsafePath, "ancestor traversal refused", err)
		}
		current, owned = next, true
		id, err := h.validateTrustedDir(current)
		ids = append(ids, id)
		if err != nil {
			syscall.Close(current)
			return -1, ids, err
		}
	}
	if !owned {
		dup, err := syscall.Dup(dirFD)
		if err != nil {
			return -1, ids, refuse(ReasonUnsafePath, "descriptor duplication failed", err)
		}
		syscall.CloseOnExec(dup)
		return dup, ids, nil
	}
	return current, ids, nil
}

// openChain opens the root, namespace and lock through trusted handles and
// returns every identity on the trusted chains.
func (h *holder) openChain() ([]fileIdentity, error) {
	nsParts, _ := splitRelative(h.cfg.NamespacePath)
	lockParts, _ := splitRelative(h.cfg.LockPath)

	rootFD, rootID, err := h.openTrustedRoot()
	if err != nil {
		return nil, err
	}
	h.rootFD = rootFD
	chain := []fileIdentity{rootID}

	parentFD, ids, err := h.walkAncestors(rootFD, nsParts[:len(nsParts)-1])
	chain = append(chain, ids...)
	if err != nil {
		return chain, err
	}
	nsFD, err := openat2(parentFD, nsParts[len(nsParts)-1], syscall.O_RDONLY|syscall.O_DIRECTORY|syscall.O_NOFOLLOW, 0)
	syscall.Close(parentFD)
	if err != nil {
		return chain, refuse(ReasonUnsafePath, "namespace traversal refused", err)
	}
	h.nsFD = nsFD
	nsID, err := h.validateNamespaceDir(nsFD)
	chain = append(chain, nsID)
	if err != nil {
		return chain, err
	}

	lockDirFD, ids, err := h.walkAncestors(rootFD, lockParts[:len(lockParts)-1])
	chain = append(chain, ids...)
	if err != nil {
		return chain, err
	}
	lockFD, err := openat2(lockDirFD, lockParts[len(lockParts)-1], syscall.O_RDONLY|syscall.O_NOFOLLOW, 0)
	syscall.Close(lockDirFD)
	if err != nil {
		return chain, refuse(ReasonLock, "lock traversal refused", err)
	}
	h.lockFD = lockFD
	if _, err := h.validateLockFile(lockFD); err != nil {
		return chain, err
	}
	if len(ids) > 0 && ids[len(ids)-1] == nsID {
		return chain, refuse(ReasonLock, "lock directory is the namespace directory", nil)
	}
	return chain, nil
}

// checkLegacyOverlap refuses when the namespace or any trusted-chain
// directory is a legacy root, or a legacy root lies beneath the namespace. It
// uses metadata (stat) only and never opens or reads legacy content.
func (h *holder) checkLegacyOverlap(chain []fileIdentity) error {
	nsID := fileIdentity{dev: h.cfg.NamespaceDevice, ino: h.cfg.NamespaceInode}
	for _, legacy := range h.cfg.LegacyRoots {
		var st syscall.Stat_t
		if err := syscall.Stat(legacy, &st); err != nil {
			if err == syscall.ENOENT {
				continue
			}
			return refuse(ReasonLegacy, "legacy root identity unverifiable", err)
		}
		legacyID := fileIdentity{dev: uint64(st.Dev), ino: st.Ino}
		for _, id := range chain {
			if id == legacyID {
				return refuse(ReasonLegacy, "protected namespace overlaps a legacy store root", nil)
			}
		}
		for dir := filepath.Dir(legacy); ; dir = filepath.Dir(dir) {
			var pst syscall.Stat_t
			if err := syscall.Stat(dir, &pst); err == nil {
				if (fileIdentity{dev: uint64(pst.Dev), ino: pst.Ino}) == nsID {
					return refuse(ReasonLegacy, "a legacy store root lies beneath the protected namespace", nil)
				}
			}
			if dir == "/" {
				break
			}
		}
	}
	return nil
}

func (h *holder) acquireLock() error {
	deadline := time.Now().Add(h.cfg.LockWait)
	for {
		err := syscall.Flock(h.lockFD, syscall.LOCK_EX|syscall.LOCK_NB)
		if err == nil {
			return nil
		}
		if err == syscall.EINTR {
			continue
		}
		if err != syscall.EWOULDBLOCK {
			return refuse(ReasonLock, "lock acquisition failed", err)
		}
		if !time.Now().Before(deadline) {
			return refuse(ReasonLock, "lock wait exceeded its bound", nil)
		}
		time.Sleep(lockPollInterval)
	}
}

// revalidate re-resolves the namespace and lock entries after acquisition (and
// before any later use) and compares them with the held descriptors.
func (h *holder) revalidate() error {
	probe := &holder{cfg: h.cfg, rootFD: -1, nsFD: -1, lockFD: -1, controlFD: -1, recordsFD: -1}
	defer probe.closeFDs()
	chain, err := probe.openChain()
	if err != nil {
		return err
	}
	if err := h.checkLegacyOverlap(chain); err != nil {
		return err
	}
	for _, pair := range [][2]int{{h.nsFD, probe.nsFD}, {h.lockFD, probe.lockFD}, {h.rootFD, probe.rootFD}} {
		held, _, err := identityOf(pair[0])
		if err != nil {
			return refuse(ReasonUnsafePath, "held descriptor stat failed", err)
		}
		entry, _, err := identityOf(pair[1])
		if err != nil || held != entry {
			return refuse(ReasonUnsafePath, "directory entry no longer matches the held descriptor", err)
		}
	}
	if _, err := h.validateNamespaceDir(h.nsFD); err != nil {
		return err
	}
	if _, err := h.validateLockFile(h.lockFD); err != nil {
		return err
	}
	return nil
}

func (h *holder) checkMounts() error {
	report, err := checkMountOptions(h.mounts, h.nsFD)
	if err != nil {
		return err
	}
	h.lastMount = report
	return nil
}

// openLocked opens the trusted chain, refuses legacy overlap, acquires the
// provisioned lock with a bounded wait, revalidates and checks mount options.
func openLocked(cfg Config, src mountOptionSource, hooks *faultHooks) (*holder, error) {
	if err := cfg.validate(); err != nil {
		return nil, err
	}
	if src == nil {
		return nil, refuse(ReasonConfig, "mount option source missing", nil)
	}
	h := &holder{cfg: cfg, mounts: src, hooks: hooks, rootFD: -1, nsFD: -1, lockFD: -1, controlFD: -1, recordsFD: -1}
	chain, err := h.openChain()
	if err == nil {
		err = h.checkLegacyOverlap(chain)
	}
	if err == nil {
		err = h.acquireLock()
	}
	if err == nil {
		err = h.revalidate()
	}
	if err == nil {
		err = h.checkMounts()
	}
	if err != nil {
		h.closeFDs()
		return nil, err
	}
	return h, nil
}

func (h *holder) closeFDs() {
	for _, fd := range []*int{&h.controlFD, &h.recordsFD, &h.nsFD, &h.rootFD, &h.lockFD} {
		if *fd >= 0 {
			syscall.Close(*fd)
			*fd = -1
		}
	}
}

func (h *holder) close() {
	h.mu.Lock()
	defer h.mu.Unlock()
	h.closed = true
	h.closeFDs()
}

func (h *holder) usable() error {
	if h.closed {
		return refuse(ReasonClosed, "store holder is closed", nil)
	}
	if h.fault != nil {
		return refuse(ReasonFaulted, "store holder has an unresolved storage fault", h.fault)
	}
	return nil
}

// setFault records the first unresolved storage fault and reports the write as
// not durable. The reason stays ReasonNotDurable for every cause; the detail
// names a quota or filesystem exhaustion so it is not reported as a generic
// device error (failureKindOf).
func (h *holder) setFault(detail string, err error) error {
	switch failureKindOf(err) {
	case failureQuota:
		detail += " (quota exhaustion, EDQUOT)"
	case failureFilesystem:
		detail += " (filesystem or inode exhaustion, ENOSPC)"
	}
	if h.fault == nil {
		h.fault = refuse(ReasonNotDurable, detail, err)
	}
	return refuse(ReasonNotDurable, detail, err)
}

func readDirNames(fd int) ([]string, error) {
	dup, err := syscall.Dup(fd)
	if err != nil {
		return nil, refuse(ReasonUnsafePath, "descriptor duplication failed", err)
	}
	syscall.CloseOnExec(dup)
	f := os.NewFile(uintptr(dup), "protected-dir")
	defer f.Close()
	if _, err := f.Seek(0, 0); err != nil {
		return nil, refuse(ReasonUnsafePath, "directory rewind failed", err)
	}
	names, err := f.Readdirnames(maxDirEntries + 1)
	if err != nil && err != io.EOF {
		return nil, refuse(ReasonUnsafePath, "directory listing failed", err)
	}
	if len(names) > maxDirEntries {
		return nil, refuse(ReasonLimit, "directory has too many entries", nil)
	}
	return names, nil
}

// --- durable creation primitives -------------------------------------------

func (h *holder) pwrite(fd int, p []byte, off int64) (int, error) {
	if h.hooks != nil && h.hooks.pwrite != nil {
		return h.hooks.pwrite(fd, p, off)
	}
	return syscall.Pwrite(fd, p, off)
}

func (h *holder) fsync(fd int, kind string) error {
	if h.hooks != nil && h.hooks.fsync != nil {
		return h.hooks.fsync(fd, kind)
	}
	for {
		err := syscall.Fsync(fd)
		if err != syscall.EINTR {
			return err
		}
	}
}

func (h *holder) rename(olddirfd int, oldname string, newdirfd int, newname string) error {
	if h.hooks != nil && h.hooks.rename != nil {
		return h.hooks.rename(olddirfd, oldname, newdirfd, newname)
	}
	return renameat2NoReplace(olddirfd, oldname, newdirfd, newname)
}

// writeFull loops over bounded short writes. Zero progress or an exhausted
// iteration bound is an error, never a silent success.
func (h *holder) writeFull(fd int, p []byte, off int64) error {
	done := 0
	for i := 0; done < len(p); i++ {
		if i >= maxWriteIterations {
			return errors.New("write iteration bound exhausted")
		}
		n, err := h.pwrite(fd, p[done:], off+int64(done))
		if err == syscall.EINTR {
			continue
		}
		if err != nil {
			return err
		}
		if n <= 0 || n > len(p)-done {
			return errors.New("write made no valid progress")
		}
		done += n
	}
	return nil
}

// createFileDurable creates name in dirFD: exclusive no-follow creation of a
// same-directory temporary, ownership/mode/link validation, complete write,
// file sync, no-replace rename and directory sync. Any failure faults the
// holder; the temporary is left for operator inspection, never repaired.
func (h *holder) createFileDurable(dirFD int, name string, content []byte, regionFile bool) error {
	tmp := "." + name + ".tmp"
	fd, err := openat2(dirFD, tmp, syscall.O_WRONLY|syscall.O_CREAT|syscall.O_EXCL|syscall.O_NOFOLLOW, 0o600)
	if err != nil {
		return h.setFault("exclusive creation failed", err)
	}
	closed := false
	defer func() {
		if !closed {
			syscall.Close(fd)
		}
	}()
	if _, _, err := h.validateStoreObject(fd, false); err != nil {
		return h.setFault("created file failed validation", err)
	}
	if regionFile {
		if _, err := checkBankAlignment(fd); err != nil {
			return h.setFault("bank alignment rule not satisfiable", err)
		}
	}
	if err := h.writeFull(fd, content, 0); err != nil {
		return h.setFault("incomplete write", err)
	}
	if err := h.fsync(fd, "file"); err != nil {
		return h.setFault("file sync failed", err)
	}
	closed = true
	if err := syscall.Close(fd); err != nil {
		return h.setFault("close failed", err)
	}
	if err := h.rename(dirFD, tmp, dirFD, name); err != nil {
		return h.setFault("rename failed or ambiguous", err)
	}
	if err := h.fsync(dirFD, "dir"); err != nil {
		return h.setFault("directory sync failed", err)
	}
	return nil
}

// mkdirDurable creates a 0700 directory and syncs it and its parent.
func (h *holder) mkdirDurable(parentFD int, name string) error {
	if err := syscall.Mkdirat(parentFD, name, 0o700); err != nil {
		return h.setFault("directory creation failed", err)
	}
	fd, err := openat2(parentFD, name, syscall.O_RDONLY|syscall.O_DIRECTORY|syscall.O_NOFOLLOW, 0)
	if err != nil {
		return h.setFault("created directory reopen failed", err)
	}
	defer syscall.Close(fd)
	if _, _, err := h.validateStoreObject(fd, true); err != nil {
		return h.setFault("created directory failed validation", err)
	}
	if err := h.fsync(fd, "dir"); err != nil {
		return h.setFault("new directory sync failed", err)
	}
	if err := h.fsync(parentFD, "dir"); err != nil {
		return h.setFault("parent directory sync failed", err)
	}
	return nil
}

// --- manifest ----------------------------------------------------------------

type manifestBody struct {
	FormatVersion       int    `json:"format_version"`
	NamespaceID         string `json:"namespace_id"`
	ScopeCloud          string `json:"scope_cloud"`
	ScopeProject        string `json:"scope_project"`
	NamespaceDevice     uint64 `json:"namespace_device"`
	NamespaceInode      uint64 `json:"namespace_inode"`
	LockDevice          uint64 `json:"lock_device"`
	LockInode           uint64 `json:"lock_inode"`
	ControlInode        uint64 `json:"control_inode"`
	RecordsInode        uint64 `json:"records_inode"`
	BankUnit            uint64 `json:"bank_unit"`
	BootstrapGeneration uint64 `json:"bootstrap_generation"`
	BootstrapDigest     string `json:"bootstrap_digest"`
	InactiveBankDigest  string `json:"inactive_bank_digest"`
	// Capacity is the trusted store/filesystem identity, quota association and
	// managed-limit policy binding (manual §5.3.4), fixed at initialization.
	Capacity capacityBinding `json:"capacity"`
}

func encodeManifest(m manifestBody) ([]byte, error) {
	body, err := json.Marshal(m)
	if err != nil {
		return nil, refuse(ReasonCorrupt, "manifest encoding failed", err)
	}
	var buf bytes.Buffer
	buf.Write(manifestMagic)
	buf.Write(body)
	buf.WriteByte('\n')
	sum := sha256.Sum256(buf.Bytes())
	buf.Write(manifestSumPrefix)
	buf.WriteString(hex.EncodeToString(sum[:]))
	buf.WriteByte('\n')
	return buf.Bytes(), nil
}

func decodeManifest(raw []byte) (manifestBody, error) {
	corrupt := func(detail string) (manifestBody, error) {
		return manifestBody{}, refuse(ReasonCorrupt, "manifest "+detail, nil)
	}
	if len(raw) == 0 || raw[len(raw)-1] != '\n' {
		return corrupt("is truncated")
	}
	idx := bytes.LastIndexByte(raw[:len(raw)-1], '\n') + 1
	signed, trailer := raw[:idx], raw[idx:len(raw)-1]
	if !bytes.HasPrefix(trailer, manifestSumPrefix) {
		return corrupt("checksum missing")
	}
	sum := sha256.Sum256(signed)
	if string(trailer[len(manifestSumPrefix):]) != hex.EncodeToString(sum[:]) {
		return corrupt("checksum mismatch")
	}
	if !bytes.HasPrefix(signed, manifestMagic) {
		if bytes.HasPrefix(signed, []byte("AIOPSMF")) {
			return manifestBody{}, refuse(ReasonVersion, "unsupported manifest format", nil)
		}
		return corrupt("magic invalid")
	}
	body := signed[len(manifestMagic) : len(signed)-1]
	dec := json.NewDecoder(bytes.NewReader(body))
	dec.DisallowUnknownFields()
	var m manifestBody
	if err := dec.Decode(&m); err != nil {
		return corrupt("body invalid")
	}
	if dec.More() {
		return corrupt("has trailing content")
	}
	if m.FormatVersion != manifestFormatVersion {
		return manifestBody{}, refuse(ReasonVersion, fmt.Sprintf("unsupported manifest version %d", m.FormatVersion), nil)
	}
	return m, nil
}

// --- control (session-control two-bank region) -------------------------------

func controlBanks(namespaceID string) (bank, bank) {
	region := regionIdentity(namespaceID, controlName)
	boot := bank{index: 0, kind: kindBootstrap, generation: bootstrapGeneration, region: region, payload: []byte(namespaceID)}
	inactive := bank{index: 1, kind: kindInactive, generation: inactiveGeneration, region: region}
	return boot, inactive
}

func expectedControl(namespaceID string) ([]byte, [32]byte, [32]byte, error) {
	boot, inactive := controlBanks(namespaceID)
	b0, err := encodeBank(boot)
	if err != nil {
		return nil, [32]byte{}, [32]byte{}, err
	}
	b1, err := encodeBank(inactive)
	if err != nil {
		return nil, [32]byte{}, [32]byte{}, err
	}
	return append(b0, b1...), sha256.Sum256(b0), sha256.Sum256(b1), nil
}

func readFull(fd int, p []byte, off int64) error {
	done := 0
	for done < len(p) {
		n, err := syscall.Pread(fd, p[done:], off+int64(done))
		if err == syscall.EINTR {
			continue
		}
		if err != nil {
			return err
		}
		if n == 0 {
			return errors.New("unexpected end of file")
		}
		done += n
	}
	return nil
}

func (h *holder) openStoreFile(dirFD int, name string, flags int) (int, syscall.Stat_t, error) {
	fd, err := openat2(dirFD, name, flags|syscall.O_NOFOLLOW, 0)
	if err != nil {
		return -1, syscall.Stat_t{}, err
	}
	_, st, err := h.validateStoreObject(fd, false)
	if err != nil {
		syscall.Close(fd)
		return -1, st, err
	}
	return fd, st, nil
}

// loadState validates the complete top-level inventory, the manifest and its
// bindings, and the control region. It never treats absence as fresh state.
func (h *holder) loadState() error {
	names, err := readDirNames(h.nsFD)
	if err != nil {
		return err
	}
	want := map[string]bool{manifestName: true, controlName: true, recordsName: true}
	if len(names) != len(want) {
		return refuse(ReasonUnexpectedState, "namespace inventory is missing, partial or has unexpected entries; operator intervention required", nil)
	}
	for _, n := range names {
		if !want[n] {
			return refuse(ReasonUnexpectedState, "namespace contains an unexpected entry; operator intervention required", nil)
		}
	}

	mfd, mst, err := h.openStoreFile(h.nsFD, manifestName, syscall.O_RDONLY)
	if err != nil {
		return refuse(ReasonUnsafePath, "manifest unavailable", err)
	}
	defer syscall.Close(mfd)
	if mst.Size <= 0 || mst.Size > maxManifestBytes {
		return refuse(ReasonCorrupt, "manifest size out of bounds", nil)
	}
	raw := make([]byte, mst.Size)
	if err := readFull(mfd, raw, 0); err != nil {
		return refuse(ReasonCorrupt, "manifest unreadable", err)
	}
	m, err := decodeManifest(raw)
	if err != nil {
		return err
	}
	if m.NamespaceID != h.cfg.NamespaceID || m.ScopeCloud != h.cfg.Scope.Cloud || m.ScopeProject != h.cfg.Scope.Project ||
		m.NamespaceDevice != h.cfg.NamespaceDevice || m.NamespaceInode != h.cfg.NamespaceInode ||
		m.LockDevice != h.cfg.LockDevice || m.LockInode != h.cfg.LockInode || m.BankUnit != bankUnit {
		return refuse(ReasonUnexpectedState, "manifest bindings do not match trusted configuration", nil)
	}
	if err := m.Capacity.wellFormed(); err != nil {
		return err
	}
	h.manifest = m
	h.manifestDigest = sha256.Sum256(raw)

	cfd, cst, err := h.openStoreFile(h.nsFD, controlName, syscall.O_RDONLY)
	if err != nil {
		return refuse(ReasonUnsafePath, "control region unavailable", err)
	}
	h.controlFD = cfd
	if cst.Ino != m.ControlInode || cst.Size != regionFileSize {
		return refuse(ReasonUnexpectedState, "control region identity or size does not match the manifest", nil)
	}
	raw = make([]byte, regionFileSize)
	if err := readFull(cfd, raw, 0); err != nil {
		return refuse(ReasonCorrupt, "control region unreadable", err)
	}
	region := regionIdentity(h.cfg.NamespaceID, controlName)
	for i := uint8(0); i < 2; i++ {
		b, state, err := decodeBank(raw[bankOffset(i):bankOffset(i)+bankUnit], i, region)
		if err != nil {
			return err
		}
		if state != bankValid {
			return refuse(ReasonUnexpectedState, "control bank is unclassifiable", nil)
		}
		h.control[i] = b
	}
	h.controlRaw = raw

	rfd, err := openat2(h.nsFD, recordsName, syscall.O_RDONLY|syscall.O_DIRECTORY|syscall.O_NOFOLLOW, 0)
	if err != nil {
		return refuse(ReasonUnsafePath, "records directory unavailable", err)
	}
	h.recordsFD = rfd
	rid, _, err := h.validateStoreObject(rfd, true)
	if err != nil {
		return err
	}
	if rid.ino != m.RecordsInode {
		return refuse(ReasonUnexpectedState, "records directory identity does not match the manifest", nil)
	}
	return nil
}

// checkExactBootstrap requires the control region to hold exactly the
// initialized BOOTSTRAP pair bound by the manifest, and no records.
func (h *holder) checkExactBootstrap() error {
	expected, bootSum, inactiveSum, err := expectedControl(h.cfg.NamespaceID)
	if err != nil {
		return err
	}
	if h.manifest.BootstrapGeneration != bootstrapGeneration ||
		h.manifest.BootstrapDigest != hex.EncodeToString(bootSum[:]) ||
		h.manifest.InactiveBankDigest != hex.EncodeToString(inactiveSum[:]) {
		return refuse(ReasonUnexpectedState, "manifest does not bind the exact initialized BOOTSTRAP pair", nil)
	}
	if !bytes.Equal(h.controlRaw, expected) {
		return refuse(ReasonUnexpectedState, "control region is not the exact unchanged BOOTSTRAP pair", nil)
	}
	names, err := readDirNames(h.recordsFD)
	if err != nil {
		return err
	}
	if len(names) != 0 {
		return refuse(ReasonUnexpectedState, "later records exist; this is not an unchanged bootstrap inventory", nil)
	}
	return nil
}

// --- initialization ------------------------------------------------------------

// InitResult is the binding an operator validates before promotion.
type InitResult struct {
	ManifestDigest      string
	BootstrapGeneration uint64
	BootstrapDigest     string
	InactiveBankDigest  string
	LockDevice          uint64
	LockInode           uint64
	AlreadyInitialized  bool
	Mount               MountReport
}

// Initialize runs initialization-only mode under the provisioned lock. In a
// verified empty namespace it creates and syncs the records directory and the
// BOOTSTRAP control pair, then publishes and syncs the manifest last. If the
// namespace is not empty it only validates a completed initialization, and
// otherwise refuses; it never reinitializes. It never admits anything.
func Initialize(cfg Config) (InitResult, error) {
	return initialize(cfg, productionMounts(), nil)
}

func initialize(cfg Config, src mountOptionSource, hooks *faultHooks) (InitResult, error) {
	if err := cfg.validate(); err != nil {
		return InitResult{}, err
	}
	if !cfg.InitializationOnly {
		return InitResult{}, refuse(ReasonConfig, "initialization requires initialization-only configuration", nil)
	}
	h, err := openLocked(cfg, src, hooks)
	if err != nil {
		return InitResult{}, err
	}
	defer h.close()
	h.mu.Lock()
	defer h.mu.Unlock()

	names, err := readDirNames(h.nsFD)
	if err != nil {
		return InitResult{}, err
	}
	if len(names) == 0 {
		return h.createInitial()
	}
	if err := h.loadState(); err != nil {
		return InitResult{}, refuse(ReasonUnexpectedState, "existing namespace state is not a completed initialization; operator intervention required", err)
	}
	if err := h.checkExactBootstrap(); err != nil {
		return InitResult{}, refuse(ReasonUnexpectedState, "existing namespace state is not a completed initialization; operator intervention required", err)
	}
	res := h.initResult()
	res.AlreadyInitialized = true
	return res, nil
}

func (h *holder) initResult() InitResult {
	return InitResult{
		ManifestDigest:      hex.EncodeToString(h.manifestDigest[:]),
		BootstrapGeneration: h.manifest.BootstrapGeneration,
		BootstrapDigest:     h.manifest.BootstrapDigest,
		InactiveBankDigest:  h.manifest.InactiveBankDigest,
		LockDevice:          h.manifest.LockDevice,
		LockInode:           h.manifest.LockInode,
		Mount:               h.lastMount,
	}
}

func (h *holder) createInitial() (InitResult, error) {
	// Bind the capacity policy to the observed filesystem identity before
	// anything is created: a refusal here writes nothing.
	capacity, err := h.bindAtInitialization()
	if err != nil {
		return InitResult{}, err
	}
	if err := h.mkdirDurable(h.nsFD, recordsName); err != nil {
		return InitResult{}, err
	}
	control, bootSum, inactiveSum, err := expectedControl(h.cfg.NamespaceID)
	if err != nil {
		return InitResult{}, err
	}
	if err := h.createFileDurable(h.nsFD, controlName, control, true); err != nil {
		return InitResult{}, err
	}
	controlID, err := h.childIdentity(controlName, false)
	if err != nil {
		return InitResult{}, h.setFault("control identity unavailable", err)
	}
	recordsID, err := h.childIdentity(recordsName, true)
	if err != nil {
		return InitResult{}, h.setFault("records identity unavailable", err)
	}
	m := manifestBody{
		FormatVersion:       manifestFormatVersion,
		NamespaceID:         h.cfg.NamespaceID,
		ScopeCloud:          h.cfg.Scope.Cloud,
		ScopeProject:        h.cfg.Scope.Project,
		NamespaceDevice:     h.cfg.NamespaceDevice,
		NamespaceInode:      h.cfg.NamespaceInode,
		LockDevice:          h.cfg.LockDevice,
		LockInode:           h.cfg.LockInode,
		ControlInode:        controlID.ino,
		RecordsInode:        recordsID.ino,
		BankUnit:            bankUnit,
		BootstrapGeneration: bootstrapGeneration,
		BootstrapDigest:     hex.EncodeToString(bootSum[:]),
		InactiveBankDigest:  hex.EncodeToString(inactiveSum[:]),
		Capacity:            capacity,
	}
	raw, err := encodeManifest(m)
	if err != nil {
		return InitResult{}, err
	}
	if err := h.createFileDurable(h.nsFD, manifestName, raw, false); err != nil {
		return InitResult{}, err
	}
	h.manifest = m
	h.manifestDigest = sha256.Sum256(raw)
	return h.initResult(), nil
}

func (h *holder) childIdentity(name string, dir bool) (fileIdentity, error) {
	flags := syscall.O_RDONLY | syscall.O_NOFOLLOW
	if dir {
		flags |= syscall.O_DIRECTORY
	}
	fd, err := openat2(h.nsFD, name, flags, 0)
	if err != nil {
		return fileIdentity{}, err
	}
	defer syscall.Close(fd)
	id, _, err := h.validateStoreObject(fd, dir)
	return id, err
}

// --- bootstrap validation ----------------------------------------------------------

// BootstrapBinding describes a validated, device-verified BOOTSTRAP pair.
type BootstrapBinding struct {
	NamespaceID         string
	ManifestDigest      string
	BootstrapGeneration uint64
	BootstrapDigest     string
	InactiveBankDigest  string
	Verify              VerifyReport
	Mount               MountReport
}

// BootstrapHolder holds the provisioned lock as a session lease over a
// promoted, unchanged, device-verified BOOTSTRAP pair. It is valid input for
// a later first-ACTIVE commit, but it admits nothing: it has no request,
// admission, cleanup or session-control write method.
type BootstrapHolder struct {
	h       *holder
	binding BootstrapBinding
}

// OpenBootstrap validates, under the provisioned lock, the operator promotion,
// the manifest and control binding and the exact unchanged BOOTSTRAP pair, and
// applies Verified to that pair. Unpromoted, partial, mismatched or invalid
// state refuses; absence is never treated as bootstrap.
func OpenBootstrap(cfg Config) (*BootstrapHolder, error) {
	return openBootstrap(cfg, productionMounts(), nil)
}

func openBootstrap(cfg Config, src mountOptionSource, hooks *faultHooks) (*BootstrapHolder, error) {
	if err := cfg.validate(); err != nil {
		return nil, err
	}
	if cfg.InitializationOnly {
		return nil, refuse(ReasonConfig, "initialization-only configuration never opens for admission input", nil)
	}
	if cfg.Promotion == nil {
		return nil, refuse(ReasonUnpromoted, "no operator promotion is configured", nil)
	}
	if !cfg.Promotion.complete() {
		return nil, refuse(ReasonUnpromoted, "operator promotion is incomplete or interrupted", nil)
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
	p := cfg.Promotion
	if err := h.checkPromotion(p); err != nil {
		return nil, err
	}
	if err := h.checkExactBootstrap(); err != nil {
		return nil, err
	}
	report, err := h.verified(verifyTarget{dirFD: h.nsFD, name: controlName, fd: h.controlFD, expected: h.controlRaw})
	if err != nil {
		return nil, err
	}
	ok = true
	return &BootstrapHolder{h: h, binding: BootstrapBinding{
		NamespaceID:         h.cfg.NamespaceID,
		ManifestDigest:      p.ManifestDigest,
		BootstrapGeneration: h.manifest.BootstrapGeneration,
		BootstrapDigest:     h.manifest.BootstrapDigest,
		InactiveBankDigest:  h.manifest.InactiveBankDigest,
		Verify:              report,
		Mount:               h.lastMount,
	}}, nil
}

// checkPromotion compares the operator promotion with the loaded manifest. It
// is the single copy of the promotion binding comparison, shared by every
// existing-namespace open path.
func (h *holder) checkPromotion(p *Promotion) error {
	if p.ManifestDigest != hex.EncodeToString(h.manifestDigest[:]) ||
		p.BootstrapGeneration != h.manifest.BootstrapGeneration ||
		p.BootstrapDigest != h.manifest.BootstrapDigest ||
		p.InactiveBankDigest != h.manifest.InactiveBankDigest ||
		p.LockDevice != h.manifest.LockDevice || p.LockInode != h.manifest.LockInode {
		return refuse(ReasonPromotionMismatch, "operator promotion does not bind this initialized namespace", nil)
	}
	return nil
}

// Binding returns the validated bootstrap binding.
func (b *BootstrapHolder) Binding() BootstrapBinding { return b.binding }

// CheckBeforeAdmission is the before-admission hook for a later chunk: it
// revalidates the held lock, namespace entries and trusted ancestors and
// repeats the effective mount-option check. It does not admit anything.
func (b *BootstrapHolder) CheckBeforeAdmission() error {
	b.h.mu.Lock()
	defer b.h.mu.Unlock()
	if err := b.h.usable(); err != nil {
		return err
	}
	if err := b.h.revalidate(); err != nil {
		return err
	}
	return b.h.checkMounts()
}

// Close releases the lease. It never writes session control.
func (b *BootstrapHolder) Close() error {
	b.h.close()
	return nil
}
