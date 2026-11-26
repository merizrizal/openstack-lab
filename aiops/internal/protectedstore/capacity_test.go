//go:build linux && amd64

package protectedstore

import (
	"bytes"
	"errors"
	"math"
	"os"
	"path/filepath"
	"strings"
	"syscall"
	"testing"
)

// Capacity tests. Decision tests use synthetic observations through the pure
// decision and are not filesystem evidence. Real-filesystem tests use the
// authorized local ext4 parent with real fstatfs, quotactl_fd and accounting.
// Injected write errors (including ENOSPC and EDQUOT) come from the fault seam
// and are not real exhaustion. No disk is filled and real ENOSPC is not run.

// --- synthetic bindings and observations ------------------------------------------

func boundBoth() (CapacityPolicy, capacityBinding) {
	pol := CapacityPolicy{
		PolicyID: "synthetic-capacity", PolicyRevision: 3, ManagedLimitBytes: 16 << 20,
		UserQuota:  QuotaPolicy{Applies: true, SubjectID: 1000, BlockLimitBytes: 1 << 30, InodeLimit: 1 << 20, ConfigID: "uq", ConfigRevision: 2},
		GroupQuota: QuotaPolicy{Applies: true, SubjectID: 1000, BlockLimitBytes: 2 << 30, InodeLimit: 2 << 20, ConfigID: "gq", ConfigRevision: 5},
	}
	return pol, capacityBinding{FilesystemMagic: ext4SuperMagic, FilesystemID: "00000000deadbeef", BlockSize: 4096, Policy: pol}
}

func roomy(b capacityBinding) capacityObservation {
	q := func(p QuotaPolicy) quotaObservation {
		if !p.Applies {
			return quotaObservation{state: quotaOff}
		}
		return quotaObservation{state: quotaOn, known: true, blockLimit: p.BlockLimitBytes, inodeLimit: p.InodeLimit}
	}
	return capacityObservation{
		fs:      fsObservation{magic: b.FilesystemMagic, id: b.FilesystemID, blockSize: b.BlockSize, freeBytes: 1 << 40, freeInodes: 1 << 30},
		user:    q(b.Policy.UserQuota),
		group:   q(b.Policy.GroupQuota),
		project: quotaObservation{state: quotaOff},
		managed: managedUsage{bytes: 1 << 20},
	}
}

func mustNeed(t *testing.T, l capacityLayout) capacityNeed {
	t.Helper()
	n, err := deriveNeed(l, 4096)
	if err != nil {
		t.Fatal(err)
	}
	return n
}

// operationOnlyLayout is the layout when only the bounded intent and the
// maximum sanitized outcome records (with their partitions) are counted: the
// derivation a check would use if it omitted every other applicable need.
func operationOnlyLayout() capacityLayout {
	l := reviewedLayout()
	l.witnessWrites, l.gapFiles, l.ackFiles = 0, 0, 0
	l.cleanupControlFiles, l.cleanupAuditFiles, l.cleanupBatchRecords = 0, 0, 0
	return l
}

// --- policy validation ----------------------------------------------------------------

func TestCapacityPolicyMustBeFiniteAndUsable(t *testing.T) {
	user := QuotaPolicy{Applies: true, SubjectID: uint32(os.Getuid()), BlockLimitBytes: 1 << 20, InodeLimit: 100, ConfigID: "uq", ConfigRevision: 1}
	cases := []struct {
		name   string
		mutate func(*CapacityPolicy)
		hint   string
	}{
		{"absent limit", func(p *CapacityPolicy) { p.ManagedLimitBytes = 0 }, "ManagedLimitBytes"},
		{"nonfinite limit", func(p *CapacityPolicy) { p.ManagedLimitBytes = math.MaxUint64 }, "ManagedLimitBytes"},
		{"limit above any usable bound", func(p *CapacityPolicy) { p.ManagedLimitBytes = maxManagedLimitBytes + 1 }, "ManagedLimitBytes"},
		{"missing policy identity", func(p *CapacityPolicy) { p.PolicyID = "" }, "PolicyID"},
		{"malformed policy identity", func(p *CapacityPolicy) { p.PolicyID = "Bad Id" }, "PolicyID"},
		{"missing policy revision", func(p *CapacityPolicy) { p.PolicyRevision = 0 }, "PolicyRevision"},
		{"quota without identity", func(p *CapacityPolicy) { q := user; q.ConfigID = ""; p.UserQuota = q }, "ConfigID"},
		{"quota without revision", func(p *CapacityPolicy) { q := user; q.ConfigRevision = 0; p.UserQuota = q }, "ConfigRevision"},
		{"quota without any enforced limit", func(p *CapacityPolicy) { q := user; q.BlockLimitBytes, q.InodeLimit = 0, 0; p.UserQuota = q }, "limit"},
		{"quota block limit not a multiple of 1024", func(p *CapacityPolicy) { q := user; q.BlockLimitBytes = 1000; p.UserQuota = q }, "BlockLimitBytes"},
		{"quota block limit unbounded", func(p *CapacityPolicy) { q := user; q.BlockLimitBytes = math.MaxUint64 &^ 1023; p.UserQuota = q }, "BlockLimitBytes"},
		{"half-set quota declared not to apply", func(p *CapacityPolicy) { p.GroupQuota = QuotaPolicy{InodeLimit: 5} }, "not to apply"},
		{"user quota for a subject other than the store owner", func(p *CapacityPolicy) { q := user; q.SubjectID++; p.UserQuota = q }, "store owner"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f := newFixture(t)
			cfg := f.cfg
			tc.mutate(&cfg.Capacity)
			err := cfg.validate()
			expectRefusal(t, err, ReasonConfig)
			if !strings.Contains(err.Error(), tc.hint) {
				t.Fatalf("refusal is not actionable (want %q): %v", tc.hint, err)
			}
			// Startup refuses before anything is created or opened.
			before := f.hashTree(t)
			_, err = initialize(cfg, procMountSource{}, nil)
			expectRefusal(t, err, ReasonConfig)
			if got := f.nsEntries(t); len(got) != 0 {
				t.Fatalf("a refused initialization created %v", got)
			}
			sameTree(t, before, f.hashTree(t), "refused initialization")
		})
	}

	t.Run("an initialized store refuses to start without a usable limit", func(t *testing.T) {
		f := newFixture(t)
		cfg := promote(t, f)
		before := f.hashTree(t)
		cfg.Capacity.ManagedLimitBytes = 0
		s, err := openSession(cfg, procMountSource{}, productionCapacity(), nil)
		if s != nil {
			s.Release()
			t.Fatal("a session started without a managed-data limit")
		}
		expectRefusal(t, err, ReasonConfig)
		sameTree(t, before, f.hashTree(t), "a startup without a limit")
	})
}

// --- the complete threshold -------------------------------------------------------------

func TestCompleteThresholdIsDerivedFromTheFiniteLayout(t *testing.T) {
	full := mustNeed(t, reviewedLayout())
	// Hand-derived for a 4096-byte block: 3 witness bank writes (196608), six new
	// two-bank files each with one bank update (6*196608), 8 cleanup records with
	// two tombstone writes and one release write (1572864), two new directories
	// (8192) and 8 objects with two metadata blocks each (65536).
	if full.bytes != 3022848 || full.inodes != 8 {
		t.Fatalf("complete need = %+v, want {3022848 8}", full)
	}

	removals := []struct {
		name   string
		mutate func(*capacityLayout)
		inodes bool
	}{
		{"session-witness transitions", func(l *capacityLayout) { l.witnessWrites = 0 }, false},
		{"bounded intent", func(l *capacityLayout) { l.intentFiles = 0 }, true},
		{"maximum sanitized outcome", func(l *capacityLayout) { l.outcomeFiles = 0 }, true},
		{"recovery and failure-gap state", func(l *capacityLayout) { l.gapFiles = 0 }, true},
		{"required acknowledgement", func(l *capacityLayout) { l.ackFiles = 0 }, true},
		{"cleanup-control region", func(l *capacityLayout) { l.cleanupControlFiles = 0 }, true},
		{"retained per-batch cleanup audit", func(l *capacityLayout) { l.cleanupAuditFiles = 0 }, true},
		{"cleanup clear and release/reuse writes", func(l *capacityLayout) { l.cleanupBatchRecords = 0 }, false},
		{"new partition directories", func(l *capacityLayout) { l.newDirs = 0 }, true},
		{"bank updates", func(l *capacityLayout) { l.bankUpdatesPerFile = 0 }, false},
		{"alignment and metadata allowance", func(l *capacityLayout) { l.metadataBlocksPerObject = 0 }, false},
	}
	for _, r := range removals {
		t.Run("omitting "+r.name+" lowers the need", func(t *testing.T) {
			l := reviewedLayout()
			r.mutate(&l)
			got := mustNeed(t, l)
			if got.bytes >= full.bytes {
				t.Fatalf("bytes %d not below the complete %d: the component is not counted", got.bytes, full.bytes)
			}
			if r.inodes && got.inodes >= full.inodes {
				t.Fatalf("inodes %d not below the complete %d", got.inodes, full.inodes)
			}
		})
	}

	// The need grows with the filesystem block size (alignment is applied).
	if big, err := deriveNeed(reviewedLayout(), 65536); err != nil || big.bytes <= full.bytes {
		t.Fatalf("a 64 KiB block must raise the need: %+v %v", big, err)
	}

	overflows := []struct {
		name   string
		mutate func(*capacityLayout)
	}{
		{"witness writes", func(l *capacityLayout) { l.witnessWrites = math.MaxUint64 }},
		{"file count", func(l *capacityLayout) { l.intentFiles = math.MaxUint64 }},
		{"directory count", func(l *capacityLayout) { l.newDirs = math.MaxUint64 }},
		{"cleanup batch", func(l *capacityLayout) { l.cleanupBatchRecords = 1 << 60 }},
		{"bank updates", func(l *capacityLayout) { l.bankUpdatesPerFile = math.MaxUint64 }},
		{"metadata allowance", func(l *capacityLayout) { l.metadataBlocksPerObject = math.MaxUint64 }},
	}
	for _, o := range overflows {
		t.Run("overflow of "+o.name, func(t *testing.T) {
			l := reviewedLayout()
			o.mutate(&l)
			if n, err := deriveNeed(l, 4096); err == nil || !IsRefusal(err, ReasonCapacity) {
				t.Fatalf("threshold overflow was not refused: %+v %v", n, err)
			}
		})
	}
	for _, bs := range []uint64{0, math.MaxUint64} {
		if n, err := deriveNeed(reviewedLayout(), bs); err == nil {
			t.Fatalf("block size %d produced a threshold: %+v", bs, n)
		}
	}
}

// The discriminating case: headroom that covers the operation records alone
// passes an operation-only derivation but not the complete threshold, which
// also counts the session-witness, gap, acknowledgement, cleanup-control,
// retained cleanup-audit and release/reuse work. Each dimension has its own
// counterpart.
func TestDiscriminatingCompleteThreshold(t *testing.T) {
	pol, bound := boundBoth()
	op := mustNeed(t, operationOnlyLayout())
	full := mustNeed(t, reviewedLayout())
	if op.bytes >= full.bytes || op.inodes >= full.inodes {
		t.Fatalf("operation-only need %+v must be strictly below the complete need %+v", op, full)
	}
	if err := decideCapacity(pol, bound, roomy(bound), full); err != nil {
		t.Fatalf("ample headroom refused: %v", err)
	}

	dims := []struct {
		name   string
		reason Reason
		inodes bool
		set    func(o *capacityObservation, headroom uint64)
	}{
		{"filesystem bytes", ReasonFilesystemExhausted, false, func(o *capacityObservation, h uint64) { o.fs.freeBytes = h }},
		{"filesystem inodes", ReasonFilesystemExhausted, true, func(o *capacityObservation, h uint64) { o.fs.freeInodes = h }},
		{"managed headroom", ReasonManagedLimit, false, func(o *capacityObservation, h uint64) { o.managed.bytes = bound.Policy.ManagedLimitBytes - h }},
		{"user quota bytes", ReasonQuotaExhausted, false, func(o *capacityObservation, h uint64) { o.user.usedBytes = o.user.blockLimit - h }},
		{"user quota inodes", ReasonQuotaExhausted, true, func(o *capacityObservation, h uint64) { o.user.usedInodes = o.user.inodeLimit - h }},
		{"group quota bytes", ReasonQuotaExhausted, false, func(o *capacityObservation, h uint64) { o.group.usedBytes = o.group.blockLimit - h }},
		{"group quota inodes", ReasonQuotaExhausted, true, func(o *capacityObservation, h uint64) { o.group.usedInodes = o.group.inodeLimit - h }},
	}
	pick := func(n capacityNeed, inodes bool) uint64 {
		if inodes {
			return n.inodes
		}
		return n.bytes
	}
	for _, d := range dims {
		t.Run(d.name, func(t *testing.T) {
			obs := roomy(bound)
			d.set(&obs, pick(op, d.inodes))
			if err := decideCapacity(pol, bound, obs, op); err != nil {
				t.Fatalf("an operation-only derivation must pass at operation-only headroom: %v", err)
			}
			err := decideCapacity(pol, bound, obs, full)
			expectRefusal(t, err, d.reason)

			// Exact boundary of the complete threshold in this dimension.
			obs = roomy(bound)
			d.set(&obs, pick(full, d.inodes))
			if err := decideCapacity(pol, bound, obs, full); err != nil {
				t.Fatalf("headroom exactly equal to the complete need must pass: %v", err)
			}
			obs = roomy(bound)
			d.set(&obs, pick(full, d.inodes)-1)
			expectRefusal(t, decideCapacity(pol, bound, obs, full), d.reason)
		})
	}

	t.Run("managed usage above the limit", func(t *testing.T) {
		obs := roomy(bound)
		obs.managed.bytes = bound.Policy.ManagedLimitBytes + 1
		expectRefusal(t, decideCapacity(pol, bound, obs, capacityNeed{}), ReasonManagedLimit)
	})
}

// --- identity and policy binding --------------------------------------------------------

func TestBindingChangesRefuseAndOrdinaryReadingsDoNot(t *testing.T) {
	pol, bound := boundBoth()
	need := mustNeed(t, reviewedLayout())

	identity := []struct {
		name   string
		mutate func(cfg *CapacityPolicy, o *capacityObservation)
	}{
		{"managed limit changed", func(c *CapacityPolicy, o *capacityObservation) { c.ManagedLimitBytes++ }},
		{"policy identity changed", func(c *CapacityPolicy, o *capacityObservation) { c.PolicyID = "other-policy" }},
		{"policy revision changed", func(c *CapacityPolicy, o *capacityObservation) { c.PolicyRevision++ }},
		{"quota configuration identity changed", func(c *CapacityPolicy, o *capacityObservation) { c.UserQuota.ConfigID = "other" }},
		{"quota configuration revision changed", func(c *CapacityPolicy, o *capacityObservation) { c.GroupQuota.ConfigRevision++ }},
		{"quota subject changed", func(c *CapacityPolicy, o *capacityObservation) { c.UserQuota.SubjectID++ }},
		{"filesystem type changed", func(c *CapacityPolicy, o *capacityObservation) { o.fs.magic = tmpfsSuperMagic }},
		{"filesystem identity changed", func(c *CapacityPolicy, o *capacityObservation) { o.fs.id = "00000000cafef00d" }},
		{"block size changed", func(c *CapacityPolicy, o *capacityObservation) { o.fs.blockSize = 1024 }},
		{"declared quota is not enabled", func(c *CapacityPolicy, o *capacityObservation) { o.user = quotaObservation{state: quotaOff} }},
		{"enforced byte limit changed", func(c *CapacityPolicy, o *capacityObservation) { o.user.blockLimit /= 2 }},
		{"enforced inode limit changed", func(c *CapacityPolicy, o *capacityObservation) { o.group.inodeLimit++ }},
	}
	for _, tc := range identity {
		t.Run(tc.name, func(t *testing.T) {
			cfg, obs := pol, roomy(bound)
			tc.mutate(&cfg, &obs)
			expectRefusal(t, decideCapacity(cfg, bound, obs, need), ReasonCapacityBinding)
		})
	}
	t.Run("undeclared quota appeared", func(t *testing.T) {
		// The trusted binding declares no group quota, but one is now enabled.
		b := bound
		b.Policy.GroupQuota = QuotaPolicy{}
		obs := roomy(b)
		obs.group = quotaObservation{state: quotaOn}
		expectRefusal(t, decideCapacity(b.Policy, b, obs, need), ReasonCapacityBinding)
	})

	unverifiable := []struct {
		name   string
		mutate func(o *capacityObservation)
	}{
		{"user quota state unknown", func(o *capacityObservation) { o.user = quotaObservation{state: quotaUnknown} }},
		{"group quota state unknown", func(o *capacityObservation) { o.group = quotaObservation{state: quotaUnknown} }},
		{"applicable quota allowance cannot be queried", func(o *capacityObservation) { o.user.known = false }},
		{"project quota state unknown", func(o *capacityObservation) { o.project = quotaObservation{state: quotaUnknown} }},
		{"project quota enabled", func(o *capacityObservation) { o.project = quotaObservation{state: quotaOn} }},
	}
	for _, tc := range unverifiable {
		t.Run(tc.name, func(t *testing.T) {
			obs := roomy(bound)
			tc.mutate(&obs)
			expectRefusal(t, decideCapacity(pol, bound, obs, need), ReasonCapacity)
		})
	}

	// Ordinary consumption between two checks is a reading, never an identity
	// change: free bytes, free inodes, managed usage and quota usage all move.
	for i, move := range []func(o *capacityObservation){
		func(o *capacityObservation) { o.fs.freeBytes, o.fs.freeInodes = 1<<35, 1<<28 },
		func(o *capacityObservation) { o.managed.bytes = 5 << 20 },
		func(o *capacityObservation) { o.user.usedBytes, o.user.usedInodes = 1<<28, 1<<10 },
		func(o *capacityObservation) { o.group.usedBytes, o.group.usedInodes = 1<<29, 1<<11 },
	} {
		obs := roomy(bound)
		move(&obs)
		if err := decideCapacity(pol, bound, obs, need); err != nil {
			t.Fatalf("ordinary reading change %d was refused: %v", i, err)
		}
	}
}

// --- real filesystem observation ---------------------------------------------------------

func blockSizeOf(t *testing.T, path string) uint64 {
	t.Helper()
	var sfs syscall.Statfs_t
	if err := syscall.Statfs(path, &sfs); err != nil {
		t.Fatal(err)
	}
	return uint64(sfs.Bsize)
}

// independentUsage recomputes the managed charge with os.Walk, independently of
// the production walker: every store object except the namespace directory,
// logical size rounded up to a block (directories at least one block) plus the
// two-block metadata allowance. st_blocks is not used.
func independentUsage(t *testing.T, f *fixture, bs uint64) uint64 {
	t.Helper()
	var u uint64
	err := filepath.Walk(f.nsPath, func(p string, info os.FileInfo, err error) error {
		if err != nil || p == f.nsPath {
			return err
		}
		size := uint64(info.Size())
		if info.IsDir() && size < bs {
			size = bs
		}
		u += (size+bs-1)/bs*bs + 2*bs
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	return u
}

func TestRealQuotaQueryReportsTheFixtureFilesystem(t *testing.T) {
	f := newFixture(t)
	fd, err := syscall.Open(f.root, syscall.O_RDONLY|syscall.O_DIRECTORY, 0)
	if err != nil {
		t.Fatal(err)
	}
	defer syscall.Close(fd)
	for name, qtype := range map[string]int{"user": userQuotaType, "group": groupQuotaType, "project": projQuotaType} {
		r, err := queryQuota(fd, qtype, uint32(os.Getuid()), true)
		if err != nil {
			t.Fatalf("%s quota query on the ext4 fixture failed (cannot be ruled out): %v", name, err)
		}
		if r.enabled {
			t.Fatalf("%s quota is enabled on the fixture filesystem; this check's expectations were written for none", name)
		}
	}
}

func TestRealCheckObservesAndBindsTheFixtureFilesystem(t *testing.T) {
	f := newFixture(t)
	f.initialize(t)
	h := f.openState(t, nil)
	bs := blockSizeOf(t, f.nsPath)

	obs, err := h.observeIdentity(h.cfg.Capacity)
	if err != nil {
		t.Fatal(err)
	}
	if obs.fs.magic != ext4SuperMagic || obs.fs.blockSize != bs || obs.fs.freeBytes == 0 || obs.fs.freeInodes == 0 {
		t.Fatalf("filesystem observation = %+v", obs.fs)
	}
	bound := h.manifest.Capacity
	if bound.FilesystemMagic != obs.fs.magic || bound.FilesystemID != obs.fs.id || bound.BlockSize != obs.fs.blockSize || bound.Policy != f.cfg.Capacity {
		t.Fatalf("manifest binding %+v does not record the observed identity and the operator policy", bound)
	}
	if obs.user.state != quotaOff || obs.group.state != quotaOff || obs.project.state != quotaOff {
		t.Fatalf("quota states on the fixture = %v %v %v", obs.user.state, obs.group.state, obs.project.state)
	}
	if err := h.checkCapacity(); err != nil {
		t.Fatalf("the real check refused the healthy fixture: %v", err)
	}

	// Managed usage is recomputed from the validated store, not from free space
	// or st_blocks, and equals the independent walk.
	u, err := h.accountManaged(reviewedLayout(), bs)
	if err != nil {
		t.Fatal(err)
	}
	if want := independentUsage(t, f, bs); u.bytes != want {
		t.Fatalf("managed usage %d, independent walk %d", u.bytes, want)
	}
}

func TestManagedUsageChargesEveryStoreObjectAndIgnoresUnmanagedAllocation(t *testing.T) {
	f := newFixture(t)
	cfg := promote(t, f)
	bs := blockSizeOf(t, f.nsPath)
	s := mustSession(t, cfg, nil)
	h := s.h

	usage := func() uint64 {
		h.mu.Lock()
		defer h.mu.Unlock()
		u, err := h.accountManaged(reviewedLayout(), bs)
		if err != nil {
			t.Fatal(err)
		}
		return u.bytes
	}
	base := usage()
	if base != independentUsage(t, f, bs) {
		t.Fatalf("usage after ACTIVE %d, independent walk %d", base, independentUsage(t, f, bs))
	}
	if _, err := s.commitRecord(testKey(f, "req-1", "intent"), []byte("a")); err != nil {
		t.Fatal(err)
	}
	first := usage()
	// A new scope partition, a new request partition and one record file.
	if want := base + 2*(bs+2*bs) + (regionFileSize + 2*bs); first != want {
		t.Fatalf("usage after the first record %d, want %d", first, want)
	}
	if _, err := s.commitRecord(testKey(f, "req-1", "outcome"), []byte("b")); err != nil {
		t.Fatal(err)
	}
	if want := first + regionFileSize + 2*bs; usage() != want {
		t.Fatalf("a second file in the same request must add one file charge, got %d want %d", usage(), want)
	}
	// An update of an existing record rewrites an allocated bank: no new object.
	before := usage()
	if _, err := s.commitRecord(testKey(f, "req-1", "outcome"), []byte("b2")); err != nil {
		t.Fatal(err)
	}
	if usage() != before {
		t.Fatal("a bank update changed the managed usage")
	}
	if usage() != independentUsage(t, f, bs) {
		t.Fatalf("usage %d, independent walk %d", usage(), independentUsage(t, f, bs))
	}

	// Synthetic unmanaged legacy allocation outside the store: not charged,
	// never evicted.
	legacy := filepath.Join(f.root, "unmanaged-legacy-allocation.bin")
	if err := os.WriteFile(legacy, bytes.Repeat([]byte{0xA5}, 1<<20), 0o600); err != nil {
		t.Fatal(err)
	}
	if usage() != before {
		t.Fatal("an allocation outside the store changed the managed usage")
	}
	// A conservative charge: a stray entry the accounting cannot validate
	// refuses instead of being under-charged.
	stray := filepath.Join(f.nsPath, "records", "unexpected-entry")
	if err := os.WriteFile(stray, []byte("x"), 0o600); err != nil {
		t.Fatal(err)
	}
	h.mu.Lock()
	_, err := h.accountManaged(reviewedLayout(), bs)
	h.mu.Unlock()
	expectRefusal(t, err, ReasonUnexpectedState)
	os.Remove(stray)
}

// Quota, limits and filesystem identity are driven through the real production
// checker with the read-only observation seams (fstatfs and quota readings are
// injected, so these are not filesystem evidence). A refusal writes nothing,
// evicts nothing and keeps the verified bootstrap pair usable.
func TestRealCheckQuotaAndIdentityOutcomes(t *testing.T) {
	uid := uint32(os.Getuid())
	declared := QuotaPolicy{Applies: true, SubjectID: uid, BlockLimitBytes: 64 << 20, InodeLimit: 100000, ConfigID: "uq", ConfigRevision: 1}
	reading := func(usedBytes, usedInodes uint64) quotaReading {
		return quotaReading{enabled: true, haveUsage: true, blockLimit: declared.BlockLimitBytes, inodeLimit: declared.InodeLimit, usedBytes: usedBytes, usedInodes: usedInodes}
	}
	need := mustNeed(t, reviewedLayout())

	type script map[int]struct {
		r   quotaReading
		err error
	}
	hooksFor := func(s script, mutate func(*syscall.Statfs_t)) *faultHooks {
		return &faultHooks{
			quota: func(fd int, qtype int, id uint32, wantUsage bool) (quotaReading, error) {
				e, ok := s[qtype]
				if !ok {
					return quotaReading{}, nil
				}
				r := e.r
				if !wantUsage {
					r.haveUsage = false
				}
				return r, e.err
			},
			statfs: func(fd int) (syscall.Statfs_t, error) {
				var sfs syscall.Statfs_t
				err := syscall.Fstatfs(fd, &sfs)
				if mutate != nil {
					mutate(&sfs)
				}
				return sfs, err
			},
		}
	}
	healthy := script{userQuotaType: {r: reading(1<<20, 10)}}

	setup := func(t *testing.T) (*fixture, Config) {
		f := newFixture(t)
		f.cfg.Capacity.UserQuota = declared
		res, err := initialize(f.cfg, procMountSource{}, hooksFor(healthy, nil))
		if err != nil {
			t.Fatalf("initialize with a declared and present quota: %v", err)
		}
		return f, f.existing(promotionFrom(res))
	}

	cases := []struct {
		name   string
		s      script
		sfs    func(*syscall.Statfs_t)
		reason Reason
	}{
		{"quota exhausted (bytes)", script{userQuotaType: {r: reading(declared.BlockLimitBytes-need.bytes+1, 10)}}, nil, ReasonQuotaExhausted},
		{"quota exhausted (inodes)", script{userQuotaType: {r: reading(0, declared.InodeLimit-need.inodes+1)}}, nil, ReasonQuotaExhausted},
		{"quota already over its limit", script{userQuotaType: {r: reading(declared.BlockLimitBytes+1, 0)}}, nil, ReasonQuotaExhausted},
		{"declared quota is no longer enabled", script{}, nil, ReasonCapacityBinding},
		{"quota enforced limits changed", script{userQuotaType: {r: func() quotaReading { r := reading(0, 0); r.blockLimit *= 2; return r }()}}, nil, ReasonCapacityBinding},
		{"unusable quota: allowance cannot be queried", script{userQuotaType: {r: quotaReading{enabled: true}, err: syscall.EPERM}}, nil, ReasonCapacity},
		{"unusable quota: usage not reported", script{userQuotaType: {r: quotaReading{enabled: true}}}, nil, ReasonCapacity},
		{"unknown quota state", script{userQuotaType: {err: syscall.EPERM}}, nil, ReasonCapacity},
		{"undeclared group quota appeared", script{userQuotaType: {r: reading(0, 0)}, groupQuotaType: {r: quotaReading{enabled: true}}}, nil, ReasonCapacityBinding},
		{"project quota enabled", script{userQuotaType: {r: reading(0, 0)}, projQuotaType: {r: quotaReading{enabled: true}}}, nil, ReasonCapacity},
		{"filesystem identity changed", healthy, func(s *syscall.Statfs_t) { s.Fsid.X__val[0] ^= 0x5a5a }, ReasonCapacityBinding},
		{"block size changed", healthy, func(s *syscall.Statfs_t) { s.Bsize /= 2 }, ReasonCapacityBinding},
		{"filesystem bytes exhausted", healthy, func(s *syscall.Statfs_t) { s.Bavail = (need.bytes - 1) / uint64(s.Bsize) }, ReasonFilesystemExhausted},
		{"filesystem inodes exhausted", healthy, func(s *syscall.Statfs_t) { s.Ffree = need.inodes - 1 }, ReasonFilesystemExhausted},
		// A synthetic unmanaged legacy allocation outside the quota and the
		// managed limit consumes filesystem space only: managed and quota
		// headroom are untouched, so the filesystem counterpart refuses.
		{"unmanaged legacy allocation exhausts only the filesystem", healthy, func(s *syscall.Statfs_t) { s.Bavail = 1 }, ReasonFilesystemExhausted},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f, cfg := setup(t)
			bootRaw := readControlRaw(t, f)
			before := f.hashTree(t)
			s, err := openSession(cfg, procMountSource{}, productionCapacity(), hooksFor(tc.s, tc.sfs))
			if s != nil {
				s.Release()
				t.Fatal("ACTIVE was established despite a refusing capacity check")
			}
			expectRefusal(t, err, tc.reason)
			if !bytes.Equal(bootRaw, readControlRaw(t, f)) {
				t.Fatal("the control region changed")
			}
			sameTree(t, before, f.hashTree(t), "a capacity refusal (no write, no eviction)")
			if bh, err := OpenBootstrap(cfg); err != nil {
				t.Fatalf("a refusal left the bootstrap pair unusable: %v", err)
			} else {
				bh.Close()
			}
		})
	}

	t.Run("ordinary free-space, inode and quota-usage changes are readings", func(t *testing.T) {
		_, cfg := setup(t)
		for i, h := range []*faultHooks{
			hooksFor(script{userQuotaType: {r: reading(2<<20, 20)}}, func(s *syscall.Statfs_t) { s.Bavail, s.Ffree = s.Bavail/2, s.Ffree/2 }),
			hooksFor(script{userQuotaType: {r: reading(30<<20, 500)}}, nil),
		} {
			s, err := openSession(cfg, procMountSource{}, productionCapacity(), h)
			if err != nil {
				t.Fatalf("restart %d refused on an ordinary reading change: %v", i, err)
			}
			if err := s.CloseOrderly(); err != nil {
				t.Fatal(err)
			}
		}
	})

	t.Run("an undeclared quota at initialization writes nothing", func(t *testing.T) {
		f := newFixture(t)
		_, err := initialize(f.cfg, procMountSource{}, hooksFor(script{groupQuotaType: {r: quotaReading{enabled: true}}}, nil))
		expectRefusal(t, err, ReasonCapacityBinding)
		if got := f.nsEntries(t); len(got) != 0 {
			t.Fatalf("a refused initialization created %v", got)
		}
	})
}

// --- managed exhaustion, never eviction ---------------------------------------------------

func TestManagedLimitExhaustionRefusesWithoutEviction(t *testing.T) {
	f := newFixture(t)
	bs := blockSizeOf(t, f.nsPath)
	need := mustNeed(t, reviewedLayout())
	// manifest, control and records directory, each with the metadata allowance.
	u0 := (bs + 2*bs) + (regionFileSize + 2*bs) + (bs + 2*bs)
	f.cfg.Capacity.ManagedLimitBytes = need.bytes + u0 + bs
	cfg := promote(t, f)

	s, err := openSession(cfg, procMountSource{}, productionCapacity(), nil)
	if err != nil {
		t.Fatalf("the first session must fit exactly one block above the complete threshold: %v", err)
	}
	if _, err := s.commitRecord(testKey(f, "req-1", "intent"), []byte("unexpired-record")); err != nil {
		t.Fatal(err)
	}
	if err := s.CloseOrderly(); err != nil {
		t.Fatal(err)
	}

	before := f.hashTree(t)
	s, err = openSession(cfg, procMountSource{}, productionCapacity(), nil)
	if s != nil {
		s.Release()
		t.Fatal("ACTIVE was established above the managed limit")
	}
	expectRefusal(t, err, ReasonManagedLimit)
	sameTree(t, before, f.hashTree(t), "a managed-limit refusal must not evict or rewrite anything")
	if failureKindOf(err) != failureManagedLimit {
		t.Fatalf("managed exhaustion classified as %q", failureKindOf(err))
	}
	// The unexpired record is still intact and readable.
	h := f.openState(t, nil)
	if v, gen, err := h.readRecord(testKey(f, "req-1", "intent")); err != nil || gen != 1 || string(v) != "unexpired-record" {
		t.Fatalf("record after the refusal: %q %d %v", v, gen, err)
	}
}

// --- old-format and unusable binding --------------------------------------------------------

func TestOldFormatManifestIsRefusedNeverUpgraded(t *testing.T) {
	cases := []struct {
		name   string
		reason Reason
		mutate func(m *manifestBody)
	}{
		{"version 1 without a capacity binding", ReasonVersion, func(m *manifestBody) { m.FormatVersion = 1; m.Capacity = capacityBinding{} }},
		{"current version with an empty binding", ReasonCorrupt, func(m *manifestBody) { m.Capacity = capacityBinding{} }},
		{"binding names a non-ext4 filesystem", ReasonCorrupt, func(m *manifestBody) { m.Capacity.FilesystemMagic = tmpfsSuperMagic }},
		{"binding without a managed limit", ReasonCorrupt, func(m *manifestBody) { m.Capacity.Policy.ManagedLimitBytes = 0 }},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f := newFixture(t)
			cfg := promote(t, f)
			path := filepath.Join(f.nsPath, manifestName)
			raw, err := os.ReadFile(path)
			if err != nil {
				t.Fatal(err)
			}
			m, err := decodeManifest(raw)
			if err != nil {
				t.Fatal(err)
			}
			tc.mutate(&m)
			mutated, err := encodeManifest(m)
			if err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(path, mutated, 0o600); err != nil {
				t.Fatal(err)
			}
			before := f.hashTree(t)
			s, err := openSession(cfg, procMountSource{}, productionCapacity(), nil)
			if s != nil {
				s.Release()
				t.Fatal("a session opened on a manifest without a usable capacity binding")
			}
			expectRefusal(t, err, tc.reason)
			_, err = openBootstrap(cfg, procMountSource{}, nil)
			expectRefusal(t, err, tc.reason)
			icfg := f.cfg
			_, err = initialize(icfg, procMountSource{}, nil)
			if err == nil {
				t.Fatal("Initialize accepted a namespace without a usable capacity binding")
			}
			sameTree(t, before, f.hashTree(t), "refusal of an old-format manifest (never upgraded)")
		})
	}
}

// --- distinct failure outcomes -------------------------------------------------------------

// After the real check passes, an unexpected required-write failure still
// fails closed, and each cause is reported distinctly. The ENOSPC and EDQUOT
// errors here are injected through the write seam; they are not real
// filesystem or quota exhaustion.
func TestWriteFailureKindsAreDistinctAndStayFailClosed(t *testing.T) {
	failWith := func(errno syscall.Errno) *faultHooks {
		return &faultHooks{pwrite: func(int, []byte, int64) (int, error) { return 0, errno }}
	}
	cases := []struct {
		name   string
		errno  syscall.Errno
		kind   failureKind
		detail string
	}{
		{"injected ENOSPC", syscall.ENOSPC, failureFilesystem, "ENOSPC"},
		{"injected EDQUOT", syscall.EDQUOT, failureQuota, "EDQUOT"},
		{"injected EIO", syscall.EIO, failureOther, ""},
	}
	seen := map[failureKind]bool{}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f := newFixture(t)
			cfg := promote(t, f)
			before := f.hashTree(t)
			s, err := openSession(cfg, procMountSource{}, productionCapacity(), failWith(tc.errno))
			if s != nil {
				s.Release()
				t.Fatal("ACTIVE established although its write failed")
			}
			expectRefusal(t, err, ReasonNotDurable)
			if got := failureKindOf(err); got != tc.kind {
				t.Fatalf("classified %q, want %q", got, tc.kind)
			}
			if tc.detail != "" && !strings.Contains(err.Error(), tc.detail) {
				t.Fatalf("detail does not name the cause: %v", err)
			}
			if tc.detail == "" && (strings.Contains(err.Error(), "ENOSPC") || strings.Contains(err.Error(), "EDQUOT")) {
				t.Fatalf("a generic device error is reported as exhaustion: %v", err)
			}
			seen[failureKindOf(err)] = true
			sameTree(t, before, f.hashTree(t), tc.name+" before any byte landed")
		})
	}
	if len(seen) != 3 {
		t.Fatalf("distinct outcomes seen = %v", seen)
	}

	// Capacity-check outcomes are distinct from write errors and from each other.
	want := map[Reason]failureKind{
		ReasonManagedLimit:        failureManagedLimit,
		ReasonQuotaExhausted:      failureQuota,
		ReasonFilesystemExhausted: failureFilesystem,
		ReasonCapacity:            failureOther,
		ReasonCapacityBinding:     failureOther,
	}
	for reason, kind := range want {
		if got := failureKindOf(refuse(reason, "x", nil)); got != kind {
			t.Errorf("%s classified %q, want %q", reason, got, kind)
		}
	}
	if failureKindOf(nil) != "" || failureKindOf(errors.New("io")) != failureOther {
		t.Fatal("nil and unknown errors are mis-classified")
	}

	t.Run("a sync failure after a passing check keeps the witness and pauses", func(t *testing.T) {
		f := newFixture(t)
		cfg := promote(t, f)
		// The first file barrier is the pre-ACTIVE Verified barrier; the second
		// is the ACTIVE barrier. The ACTIVE bytes land but are not reported durable.
		n := 0
		hooks := &faultHooks{fsync: func(fd int, kind string) error {
			if kind == "file" {
				if n++; n > 1 {
					return syscall.EIO
				}
			}
			return syscall.Fsync(fd)
		}}
		s, err := openSession(cfg, procMountSource{}, productionCapacity(), hooks)
		if s != nil {
			s.Release()
			t.Fatal("ACTIVE reported durable after a failed barrier")
		}
		expectRefusal(t, err, ReasonNotDurable)
		expectPaused(t, f, cfg, nil, ReasonStaleActive, "")
	})
}
