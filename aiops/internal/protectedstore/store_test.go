//go:build linux && amd64

package protectedstore

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"os"
	"path/filepath"
	"reflect"
	"syscall"
	"testing"
	"time"
	"unsafe"
)

func TestStatxLayoutMatchesKernelABI(t *testing.T) {
	var st statxT
	if got := unsafe.Sizeof(st); got != 256 {
		t.Fatalf("statx size = %d, want 256", got)
	}
	if got := unsafe.Offsetof(st.MntID); got != 144 {
		t.Fatalf("stx_mnt_id offset = %d, want 144", got)
	}
	if got := unsafe.Offsetof(st.DioMemAlign); got != 152 {
		t.Fatalf("stx_dio_mem_align offset = %d, want 152", got)
	}
	if got := unsafe.Offsetof(st.DioOffsetAlign); got != 156 {
		t.Fatalf("stx_dio_offset_align offset = %d, want 156", got)
	}
	if got := unsafe.Sizeof(openHow{}); got != 24 {
		t.Fatalf("open_how size = %d, want 24", got)
	}
}

// First creation, operator promotion, bootstrap validation and reopen through
// the exported production constructors on the real ext4 fixture.
func TestFirstCreatePromoteAndReopenBootstrap(t *testing.T) {
	f := newFixture(t)
	res, err := Initialize(f.cfg)
	if err != nil {
		t.Fatalf("Initialize: %v", err)
	}
	if res.AlreadyInitialized {
		t.Fatal("fresh initialization reported as already initialized")
	}
	t.Logf("mount: device=%s mnt_id=%d dev=%d:%d %s %s rw=%v", res.Mount.Device, res.Mount.MountID, res.Mount.Major, res.Mount.Minor, res.Mount.Barrier, res.Mount.DataMode, res.Mount.ReadWrite)
	if got, want := f.nsEntries(t), []string{manifestName, controlName, recordsName}; !reflect.DeepEqual(got, want) {
		t.Fatalf("namespace entries = %v, want %v", got, want)
	}

	cfg := f.existing(promotionFrom(res))
	for round := 0; round < 2; round++ {
		b, err := OpenBootstrap(cfg)
		if err != nil {
			t.Fatalf("OpenBootstrap round %d: %v", round, err)
		}
		binding := b.Binding()
		t.Logf("verified bootstrap: generation=%d dio_mem_align=%d dio_offset_align=%d bank_unit=%d bytes=%d",
			binding.BootstrapGeneration, binding.Verify.DioMemAlign, binding.Verify.DioOffsetAlign, binding.Verify.BankUnit, binding.Verify.Bytes)
		if binding.BootstrapGeneration != bootstrapGeneration || binding.ManifestDigest != res.ManifestDigest {
			t.Fatalf("unexpected binding %+v", binding)
		}
		if _, ok := b.h.mounts.(procMountSource); !ok || b.h.hooks != nil {
			t.Fatal("production constructor did not bind the real /proc source and nil fault seam")
		}
		if err := b.CheckBeforeAdmission(); err != nil {
			t.Fatalf("CheckBeforeAdmission: %v", err)
		}
		if err := b.Close(); err != nil {
			t.Fatal(err)
		}
	}
	// Validation and reopen never changed the namespace.
	before := f.hashTree(t)
	b, err := OpenBootstrap(cfg)
	if err != nil {
		t.Fatal(err)
	}
	b.Close()
	if !reflect.DeepEqual(before, f.hashTree(t)) {
		t.Fatal("bootstrap validation changed namespace contents")
	}
}

func TestBootstrapHolderOffersNoAdmissionOrWriteMethod(t *testing.T) {
	typ := reflect.TypeOf(&BootstrapHolder{})
	allowed := map[string]bool{"Binding": true, "CheckBeforeAdmission": true, "Close": true}
	for i := 0; i < typ.NumMethod(); i++ {
		if name := typ.Method(i).Name; !allowed[name] {
			t.Fatalf("BootstrapHolder exposes unexpected method %s", name)
		}
	}
}

func TestInitializeLayoutModesAndBankAlignment(t *testing.T) {
	f := newFixture(t)
	f.initialize(t)
	for name, want := range map[string]os.FileMode{manifestName: 0o600, controlName: 0o600} {
		info, err := os.Lstat(filepath.Join(f.nsPath, name))
		if err != nil {
			t.Fatal(err)
		}
		if !info.Mode().IsRegular() || info.Mode().Perm() != want {
			t.Fatalf("%s mode %v", name, info.Mode())
		}
	}
	info, err := os.Lstat(filepath.Join(f.nsPath, recordsName))
	if err != nil || !info.IsDir() || info.Mode().Perm() != 0o700 {
		t.Fatalf("records dir: %v %v", info, err)
	}

	fd, err := syscall.Open(filepath.Join(f.nsPath, controlName), syscall.O_RDONLY|syscall.O_CLOEXEC, 0)
	if err != nil {
		t.Fatal(err)
	}
	defer syscall.Close(fd)
	report, err := checkBankAlignment(fd)
	if err != nil {
		t.Fatalf("checkBankAlignment: %v", err)
	}
	t.Logf("alignment: block=%d page=%d sector_bound=%d dio_mem=%d dio_offset=%d bank_unit=%d", report.BlockSize, report.PageSize, report.Sector, report.DioMemAlign, report.DioOffsetAlign, report.BankUnit)
	largest := report.BlockSize
	for _, u := range []uint64{report.PageSize, report.Sector, report.DioOffsetAlign, report.DioMemAlign} {
		if u > largest {
			largest = u
		}
	}
	if bankOffset(1)%int64(largest) != 0 || bankOffset(0) != 0 {
		t.Fatalf("bank 1 offset %d not aligned to largest unit %d", bankOffset(1), largest)
	}
	if bankOffset(1) < bankOffset(0)+int64(largest) || bankUnit%largest != 0 {
		t.Fatal("banks share an alignment unit")
	}
	raw, err := os.ReadFile(filepath.Join(f.nsPath, controlName))
	if err != nil {
		t.Fatal(err)
	}
	if len(raw) != regionFileSize {
		t.Fatalf("control size %d", len(raw))
	}
	region := regionIdentity(f.cfg.NamespaceID, controlName)
	b0, s0, err0 := decodeBank(raw[:bankUnit], 0, region)
	b1, s1, err1 := decodeBank(raw[bankUnit:], 1, region)
	if err0 != nil || err1 != nil || s0 != bankValid || s1 != bankValid {
		t.Fatalf("control banks invalid: %v %v", err0, err1)
	}
	if b0.kind != kindBootstrap || b0.generation != bootstrapGeneration || b1.kind != kindInactive || b1.generation != inactiveGeneration {
		t.Fatalf("control pair = %+v / %+v", b0, b1)
	}
}

func TestAlignmentUnitValidationRefusesNonDividingUnits(t *testing.T) {
	ok := alignmentReport{BlockSize: 4096, PageSize: 4096, Sector: 4096, DioMemAlign: 4, DioOffsetAlign: 512}
	if err := validateAlignmentUnits(ok); err != nil {
		t.Fatalf("valid units refused: %v", err)
	}
	for name, r := range map[string]alignmentReport{
		"block larger than bank": {BlockSize: 2 * bankUnit, PageSize: 4096},
		"non power of two":       {BlockSize: 4096, PageSize: 4096, DioOffsetAlign: 3},
		"page unavailable":       {BlockSize: 4096},
		"dio mem too large":      {BlockSize: 4096, PageSize: 4096, DioMemAlign: 4 * bankUnit},
	} {
		if err := validateAlignmentUnits(r); !IsRefusal(err, ReasonAlignment) {
			t.Fatalf("%s: got %v", name, err)
		}
	}
}

func TestSecondInitializeOnlyValidatesCompletedInitialization(t *testing.T) {
	f := newFixture(t)
	first := f.initialize(t)
	before := f.hashTree(t)
	second := f.initialize(t)
	if !second.AlreadyInitialized || second.ManifestDigest != first.ManifestDigest {
		t.Fatalf("second initialize = %+v", second)
	}
	if !reflect.DeepEqual(before, f.hashTree(t)) {
		t.Fatal("second initialize changed the namespace")
	}
}

func TestInitializeRefusesForeignOrPartialState(t *testing.T) {
	f := newFixture(t)
	if err := os.WriteFile(filepath.Join(f.nsPath, "foreign"), []byte("x"), 0o600); err != nil {
		t.Fatal(err)
	}
	_, err := initialize(f.cfg, procMountSource{}, nil)
	expectRefusal(t, err, ReasonUnexpectedState)
	if got := f.nsEntries(t); !reflect.DeepEqual(got, []string{"foreign"}) {
		t.Fatalf("refused initialization changed the namespace: %v", got)
	}
}

// An interrupted initialization (manifest publication fails) is never
// reinitialized, repaired or accepted as bootstrap.
func TestInterruptedInitializationIsNeverReinitializedOrAccepted(t *testing.T) {
	for _, tc := range []struct {
		name  string
		hooks *faultHooks
	}{
		{"manifest rename fails", &faultHooks{rename: func(od int, on string, nd int, nn string) error {
			if nn == manifestName {
				return syscall.EIO
			}
			return renameat2NoReplace(od, on, nd, nn)
		}}},
		{"control file sync fails", &faultHooks{fsync: func(fd int, kind string) error {
			if kind == "file" {
				return syscall.EIO
			}
			return syscall.Fsync(fd)
		}}},
		{"directory sync fails", &faultHooks{fsync: func(fd int, kind string) error {
			if kind == "dir" {
				return syscall.EIO
			}
			return syscall.Fsync(fd)
		}}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			f := newFixture(t)
			_, err := initialize(f.cfg, procMountSource{}, tc.hooks)
			expectRefusal(t, err, ReasonNotDurable)
			partial := f.hashTree(t)

			_, err = initialize(f.cfg, procMountSource{}, nil)
			expectRefusal(t, err, ReasonUnexpectedState)

			fake := &Promotion{ManifestDigest: hex.EncodeToString(make([]byte, 32)), BootstrapGeneration: 1,
				BootstrapDigest: hex.EncodeToString(make([]byte, 32)), InactiveBankDigest: hex.EncodeToString(make([]byte, 32)),
				LockDevice: f.cfg.LockDevice, LockInode: f.cfg.LockInode}
			_, err = OpenBootstrap(f.existing(fake))
			if err == nil {
				t.Fatal("partial initialization accepted as bootstrap")
			}
			if !reflect.DeepEqual(partial, f.hashTree(t)) {
				t.Fatal("partial state was modified or repaired")
			}
		})
	}
}

func TestOpenBootstrapRefusesAbsentStateWithoutReinitializing(t *testing.T) {
	f := newFixture(t)
	fake := &Promotion{ManifestDigest: hex.EncodeToString(make([]byte, 32)), BootstrapGeneration: 1,
		BootstrapDigest: hex.EncodeToString(make([]byte, 32)), InactiveBankDigest: hex.EncodeToString(make([]byte, 32)),
		LockDevice: f.cfg.LockDevice, LockInode: f.cfg.LockInode}
	_, err := OpenBootstrap(f.existing(fake))
	expectRefusal(t, err, ReasonUnexpectedState)
	if got := f.nsEntries(t); len(got) != 0 {
		t.Fatalf("absent state was initialized: %v", got)
	}
}

func TestModeAndPromotionPreconditions(t *testing.T) {
	f := newFixture(t)
	res := f.initialize(t)

	cfg := f.existing(nil)
	_, err := initialize(cfg, procMountSource{}, nil)
	expectRefusal(t, err, ReasonConfig)

	initCfg := f.cfg
	_, err = OpenBootstrap(initCfg)
	expectRefusal(t, err, ReasonConfig)

	_, err = OpenBootstrap(f.existing(nil))
	expectRefusal(t, err, ReasonUnpromoted)

	incomplete := []func(p *Promotion){
		func(p *Promotion) { p.ManifestDigest = "" },
		func(p *Promotion) { p.BootstrapGeneration = 0 },
		func(p *Promotion) { p.BootstrapDigest = "abc" },
		func(p *Promotion) { p.InactiveBankDigest = "" },
		func(p *Promotion) { p.LockInode = 0 },
	}
	for i, mutate := range incomplete {
		p := promotionFrom(res)
		mutate(p)
		_, err := OpenBootstrap(f.existing(p))
		if !IsRefusal(err, ReasonUnpromoted) {
			t.Fatalf("incomplete promotion %d: %v", i, err)
		}
	}
	flip := func(s string) string {
		b := []byte(s)
		if b[0] == '0' {
			b[0] = '1'
		} else {
			b[0] = '0'
		}
		return string(b)
	}
	mismatched := []func(p *Promotion){
		func(p *Promotion) { p.ManifestDigest = flip(p.ManifestDigest) },
		func(p *Promotion) { p.BootstrapGeneration = 2 },
		func(p *Promotion) { p.BootstrapDigest = flip(p.BootstrapDigest) },
		func(p *Promotion) { p.InactiveBankDigest = flip(p.InactiveBankDigest) },
		func(p *Promotion) { p.LockInode++ },
		func(p *Promotion) { p.LockDevice++ },
	}
	for i, mutate := range mismatched {
		p := promotionFrom(res)
		mutate(p)
		_, err := OpenBootstrap(f.existing(p))
		if !IsRefusal(err, ReasonPromotionMismatch) {
			t.Fatalf("mismatched promotion %d: %v", i, err)
		}
	}
}

func TestConfigValidation(t *testing.T) {
	f := newFixture(t)
	cases := map[string]func(c *Config){
		"relative root":        func(c *Config) { c.RootPath = "rel" },
		"unclean root":         func(c *Config) { c.RootPath = c.RootPath + "/." },
		"absolute namespace":   func(c *Config) { c.NamespacePath = "/ns" },
		"dotdot namespace":     func(c *Config) { c.NamespacePath = "../ns" },
		"lock at root":         func(c *Config) { c.LockPath = "namespace.lock" },
		"lock in namespace":    func(c *Config) { c.LockPath = "ns/namespace.lock" },
		"bad namespace id":     func(c *Config) { c.NamespaceID = "Bad ID" },
		"missing inode":        func(c *Config) { c.NamespaceInode = 0 },
		"empty scope":          func(c *Config) { c.Scope.Project = "" },
		"control char scope":   func(c *Config) { c.Scope.Cloud = "a\x00b" },
		"no trusted owners":    func(c *Config) { c.TrustedOwnerUIDs = nil },
		"zero lock wait":       func(c *Config) { c.LockWait = 0 },
		"unbounded lock wait":  func(c *Config) { c.LockWait = time.Hour },
		"relative legacy root": func(c *Config) { c.LegacyRoots = []string{"legacy"} },
		"init with promotion":  func(c *Config) { c.Promotion = &Promotion{} },
	}
	for name, mutate := range cases {
		cfg := f.cfg
		mutate(&cfg)
		_, err := initialize(cfg, procMountSource{}, nil)
		if err == nil || !(IsRefusal(err, ReasonConfig) || IsRefusal(err, ReasonScope)) {
			t.Fatalf("%s: got %v", name, err)
		}
	}
	if got := f.nsEntries(t); len(got) != 0 {
		t.Fatalf("invalid configuration created state: %v", got)
	}
}

func TestCorruptOrIncompatibleStateRefused(t *testing.T) {
	type mutation struct {
		name   string
		reason Reason
		apply  func(t *testing.T, f *fixture)
	}
	rewrite := func(t *testing.T, path string, mutate func([]byte) []byte) {
		t.Helper()
		raw, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(path, mutate(raw), 0o600); err != nil {
			t.Fatal(err)
		}
	}
	cases := []mutation{
		{"control payload byte flipped", ReasonCorrupt, func(t *testing.T, f *fixture) {
			rewrite(t, filepath.Join(f.nsPath, controlName), func(b []byte) []byte { b[bankHeaderSize] ^= 0xff; return b })
		}},
		{"control bank version 2", ReasonVersion, func(t *testing.T, f *fixture) {
			rewrite(t, filepath.Join(f.nsPath, controlName), func(b []byte) []byte {
				b[9] = 2
				resealBank(b[:bankUnit])
				return b
			})
		}},
		{"control bank torn", ReasonCorrupt, func(t *testing.T, f *fixture) {
			rewrite(t, filepath.Join(f.nsPath, controlName), func(b []byte) []byte {
				for i := bankUnit; i < bankUnit+100; i++ {
					b[i] = 0x5a
				}
				return b
			})
		}},
		{"control bank zeroed", ReasonUnexpectedState, func(t *testing.T, f *fixture) {
			rewrite(t, filepath.Join(f.nsPath, controlName), func(b []byte) []byte {
				for i := bankUnit; i < len(b); i++ {
					b[i] = 0
				}
				return b
			})
		}},
		{"control truncated", ReasonUnexpectedState, func(t *testing.T, f *fixture) {
			rewrite(t, filepath.Join(f.nsPath, controlName), func(b []byte) []byte { return b[:bankUnit] })
		}},
		{"control changed to a later valid generation", ReasonUnexpectedState, func(t *testing.T, f *fixture) {
			rewrite(t, filepath.Join(f.nsPath, controlName), func(b []byte) []byte {
				later, err := encodeBank(bank{index: 1, kind: kindRecord, generation: 2, region: regionIdentity(f.cfg.NamespaceID, controlName), payload: []byte("later")})
				if err != nil {
					t.Fatal(err)
				}
				return append(b[:bankUnit], later...)
			})
		}},
		{"manifest byte flipped", ReasonCorrupt, func(t *testing.T, f *fixture) {
			rewrite(t, filepath.Join(f.nsPath, manifestName), func(b []byte) []byte { b[20] ^= 0x01; return b })
		}},
		{"manifest future version", ReasonVersion, func(t *testing.T, f *fixture) {
			rewrite(t, filepath.Join(f.nsPath, manifestName), func(b []byte) []byte {
				m, err := decodeManifest(b)
				if err != nil {
					t.Fatal(err)
				}
				m.FormatVersion = manifestFormatVersion + 1
				out, err := encodeManifest(m)
				if err != nil {
					t.Fatal(err)
				}
				return out
			})
		}},
		{"manifest other format magic", ReasonVersion, func(t *testing.T, f *fixture) {
			rewrite(t, filepath.Join(f.nsPath, manifestName), func(b []byte) []byte {
				m, _ := decodeManifest(b)
				out, _ := encodeManifest(m)
				idx := bytes.LastIndexByte(out[:len(out)-1], '\n') + 1
				signed := append([]byte("AIOPSMF2\n"), out[len(manifestMagic):idx]...)
				sum := sha256Hex(signed)
				return append(signed, []byte("sha256:"+sum+"\n")...)
			})
		}},
		{"manifest unknown field", ReasonCorrupt, func(t *testing.T, f *fixture) {
			rewrite(t, filepath.Join(f.nsPath, manifestName), func(b []byte) []byte {
				idx := bytes.LastIndexByte(b[:len(b)-1], '\n') + 1
				body := bytes.TrimSuffix(b[len(manifestMagic):idx], []byte("\n"))
				body = append(body[:len(body)-1], []byte(`,"extra":1}`)...)
				signed := append(append(append([]byte{}, manifestMagic...), body...), '\n')
				return append(signed, []byte("sha256:"+sha256Hex(signed)+"\n")...)
			})
		}},
		{"manifest namespace binding changed", ReasonUnexpectedState, func(t *testing.T, f *fixture) {
			rewrite(t, filepath.Join(f.nsPath, manifestName), func(b []byte) []byte {
				m, _ := decodeManifest(b)
				m.NamespaceID = "other-namespace"
				out, _ := encodeManifest(m)
				return out
			})
		}},
		{"stray temporary entry", ReasonUnexpectedState, func(t *testing.T, f *fixture) {
			if err := os.WriteFile(filepath.Join(f.nsPath, ".control.tmp"), nil, 0o600); err != nil {
				t.Fatal(err)
			}
		}},
		{"manifest missing", ReasonUnexpectedState, func(t *testing.T, f *fixture) {
			if err := os.Rename(filepath.Join(f.nsPath, manifestName), filepath.Join(f.root, "moved-manifest")); err != nil {
				t.Fatal(err)
			}
		}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f := newFixture(t)
			res := f.initialize(t)
			cfg := f.existing(promotionFrom(res))
			tc.apply(t, f)
			before := f.hashTree(t)
			_, err := OpenBootstrap(cfg)
			expectRefusal(t, err, tc.reason)
			if !reflect.DeepEqual(before, f.hashTree(t)) {
				t.Fatal("refused state was modified")
			}
		})
	}
}

func TestOpenBootstrapRefusesLaterRecords(t *testing.T) {
	f := newFixture(t)
	res := f.initialize(t)
	h := f.openState(t, nil)
	if _, err := h.commitRecord(testKey(f, "req-1", "intent"), []byte("sanitized")); err != nil {
		t.Fatal(err)
	}
	h.close()
	_, err := OpenBootstrap(f.existing(promotionFrom(res)))
	expectRefusal(t, err, ReasonUnexpectedState)
}

func TestPathOwnershipSymlinkAndHardLinkAttacks(t *testing.T) {
	type attack struct {
		name   string
		reason Reason
		setup  func(t *testing.T, f *fixture, cfg *Config)
	}
	cases := []attack{
		{"namespace is a symlink", ReasonUnsafePath, func(t *testing.T, f *fixture, cfg *Config) {
			if err := os.Symlink("ns", filepath.Join(f.root, "nslink")); err != nil {
				t.Fatal(err)
			}
			cfg.NamespacePath = "nslink"
		}},
		{"ancestor is a symlink", ReasonUnsafePath, func(t *testing.T, f *fixture, cfg *Config) {
			mkdirMode(t, filepath.Join(f.root, "real"), 0o700)
			if err := os.Rename(f.nsPath, filepath.Join(f.root, "real", "ns")); err != nil {
				t.Fatal(err)
			}
			if err := os.Symlink("real", filepath.Join(f.root, "alias")); err != nil {
				t.Fatal(err)
			}
			cfg.NamespacePath = "alias/ns"
		}},
		{"namespace replaced", ReasonUnsafePath, func(t *testing.T, f *fixture, cfg *Config) {
			if err := os.Rename(f.nsPath, filepath.Join(f.root, "ns-old")); err != nil {
				t.Fatal(err)
			}
			mkdirMode(t, f.nsPath, 0o700)
		}},
		{"lock is a symlink", ReasonLock, func(t *testing.T, f *fixture, cfg *Config) {
			if err := os.Rename(f.lockAbs, filepath.Join(f.root, "lockdir", "real.lock")); err != nil {
				t.Fatal(err)
			}
			if err := os.Symlink("real.lock", f.lockAbs); err != nil {
				t.Fatal(err)
			}
		}},
		{"lock is hard-linked", ReasonLock, func(t *testing.T, f *fixture, cfg *Config) {
			if err := os.Link(f.lockAbs, filepath.Join(f.root, "lockdir", "second.lock")); err != nil {
				t.Fatal(err)
			}
		}},
		{"lock is writable", ReasonOwnership, func(t *testing.T, f *fixture, cfg *Config) {
			if err := os.Chmod(f.lockAbs, 0o600); err != nil {
				t.Fatal(err)
			}
		}},
		{"lock replaced", ReasonLock, func(t *testing.T, f *fixture, cfg *Config) {
			if err := os.Rename(f.lockAbs, filepath.Join(f.root, "lockdir", "old.lock")); err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(f.lockAbs, nil, 0o400); err != nil {
				t.Fatal(err)
			}
		}},
		{"namespace mode too open", ReasonOwnership, func(t *testing.T, f *fixture, cfg *Config) {
			if err := os.Chmod(f.nsPath, 0o750); err != nil {
				t.Fatal(err)
			}
		}},
		{"ancestor group-writable", ReasonOwnership, func(t *testing.T, f *fixture, cfg *Config) {
			parent := filepath.Join(f.root, "parent")
			mkdirMode(t, parent, 0o700)
			if err := os.Rename(f.nsPath, filepath.Join(parent, "ns")); err != nil {
				t.Fatal(err)
			}
			if err := os.Chmod(parent, 0o770); err != nil {
				t.Fatal(err)
			}
			cfg.NamespacePath = "parent/ns"
		}},
		{"lock directory other-writable", ReasonOwnership, func(t *testing.T, f *fixture, cfg *Config) {
			if err := os.Chmod(filepath.Join(f.root, "lockdir"), 0o703); err != nil {
				t.Fatal(err)
			}
			t.Cleanup(func() { os.Chmod(filepath.Join(f.root, "lockdir"), 0o700) })
		}},
		{"store owner mismatch", ReasonOwnership, func(t *testing.T, f *fixture, cfg *Config) {
			cfg.StoreOwnerUID = f.uid + 1
		}},
		{"untrusted ancestor owner", ReasonOwnership, func(t *testing.T, f *fixture, cfg *Config) {
			cfg.TrustedOwnerUIDs = []uint32{f.uid + 1}
		}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f := newFixture(t)
			cfg := f.cfg
			tc.setup(t, f, &cfg)
			_, err := initialize(cfg, procMountSource{}, nil)
			expectRefusal(t, err, tc.reason)
		})
	}
}

func TestStoreObjectAttacksAfterInitialization(t *testing.T) {
	cases := map[string]func(t *testing.T, f *fixture){
		"manifest hard-linked": func(t *testing.T, f *fixture) {
			if err := os.Link(filepath.Join(f.nsPath, manifestName), filepath.Join(f.root, "manifest-link")); err != nil {
				t.Fatal(err)
			}
		},
		"manifest mode widened": func(t *testing.T, f *fixture) {
			if err := os.Chmod(filepath.Join(f.nsPath, manifestName), 0o644); err != nil {
				t.Fatal(err)
			}
		},
		"control replaced by symlink": func(t *testing.T, f *fixture) {
			if err := os.Rename(filepath.Join(f.nsPath, controlName), filepath.Join(f.root, "control-real")); err != nil {
				t.Fatal(err)
			}
			if err := os.Symlink("../control-real", filepath.Join(f.nsPath, controlName)); err != nil {
				t.Fatal(err)
			}
		},
		"records replaced by symlink": func(t *testing.T, f *fixture) {
			if err := os.Rename(filepath.Join(f.nsPath, recordsName), filepath.Join(f.root, "records-real")); err != nil {
				t.Fatal(err)
			}
			if err := os.Symlink("../records-real", filepath.Join(f.nsPath, recordsName)); err != nil {
				t.Fatal(err)
			}
		},
	}
	for name, attack := range cases {
		t.Run(name, func(t *testing.T) {
			f := newFixture(t)
			res := f.initialize(t)
			attack(t, f)
			_, err := OpenBootstrap(f.existing(promotionFrom(res)))
			expectRefusal(t, err, ReasonUnsafePath)
		})
	}
}

func TestLockWaitIsBoundedUnderContention(t *testing.T) {
	f := newFixture(t)
	res := f.initialize(t)
	fd, err := syscall.Open(f.lockAbs, syscall.O_RDONLY|syscall.O_CLOEXEC, 0)
	if err != nil {
		t.Fatal(err)
	}
	defer syscall.Close(fd)
	if err := syscall.Flock(fd, syscall.LOCK_EX); err != nil {
		t.Fatal(err)
	}
	cfg := f.existing(promotionFrom(res))
	cfg.LockWait = 150 * time.Millisecond
	start := time.Now()
	_, err = OpenBootstrap(cfg)
	expectRefusal(t, err, ReasonLock)
	if elapsed := time.Since(start); elapsed > 2*time.Second {
		t.Fatalf("lock wait not bounded: %v", elapsed)
	}
	syscall.Flock(fd, syscall.LOCK_UN)
	b, err := OpenBootstrap(cfg)
	if err != nil {
		t.Fatalf("after release: %v", err)
	}
	b.Close()
}

func TestNamespaceMustBeDistinctFromLegacyRoots(t *testing.T) {
	t.Run("namespace is a legacy root", func(t *testing.T) {
		f := newFixture(t)
		cfg := f.cfg
		cfg.LegacyRoots = []string{f.nsPath}
		_, err := initialize(cfg, procMountSource{}, nil)
		expectRefusal(t, err, ReasonLegacy)
	})
	t.Run("namespace beneath a legacy root", func(t *testing.T) {
		f := newFixtureAt(t, "legacy-root/ns")
		cfg := f.cfg
		cfg.LegacyRoots = []string{filepath.Join(f.root, "legacy-root")}
		_, err := initialize(cfg, procMountSource{}, nil)
		expectRefusal(t, err, ReasonLegacy)
	})
	t.Run("legacy root beneath the namespace", func(t *testing.T) {
		f := newFixture(t)
		cfg := f.cfg
		cfg.LegacyRoots = []string{filepath.Join(f.nsPath, "workflows")}
		mkdirMode(t, filepath.Join(f.nsPath, "workflows"), 0o700)
		_, err := initialize(cfg, procMountSource{}, nil)
		expectRefusal(t, err, ReasonLegacy)
	})
}

func sha256Hex(b []byte) string {
	sum := sha256.Sum256(b)
	return hex.EncodeToString(sum[:])
}
