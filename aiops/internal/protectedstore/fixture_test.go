//go:build linux && amd64

package protectedstore

import (
	"crypto/sha256"
	"os"
	"path/filepath"
	"sort"
	"syscall"
	"testing"
	"time"
)

// Test fixtures run as the invoking non-root user. Every object they create
// lives under t.TempDir() (TMPDIR is the authorized ext4 parent) or, for the
// tmpfs refusal case, under an explicitly created /tmp directory.

type fixture struct {
	root    string
	cfg     Config
	legacy  map[string][32]byte
	uid     uint32
	nsPath  string
	lockAbs string
}

// testCapacityPolicy is a synthetic finite managed-data limit with no quota
// declared. The fixture parent has no quota enabled; the check verifies that.
func testCapacityPolicy() CapacityPolicy {
	return CapacityPolicy{PolicyID: "synthetic-capacity", PolicyRevision: 1, ManagedLimitBytes: 16 << 20}
}

func requireExt4(t *testing.T, path string) {
	t.Helper()
	var sfs syscall.Statfs_t
	if err := syscall.Statfs(path, &sfs); err != nil {
		t.Fatalf("statfs %s: %v", path, err)
	}
	if sfs.Type != ext4SuperMagic {
		t.Fatalf("fixture directory %s is not on ext4 (magic %#x); set TMPDIR to the authorized ext4 parent", path, sfs.Type)
	}
}

func identity(t *testing.T, path string) (uint64, uint64) {
	t.Helper()
	var st syscall.Stat_t
	if err := syscall.Lstat(path, &st); err != nil {
		t.Fatalf("lstat %s: %v", path, err)
	}
	return uint64(st.Dev), st.Ino
}

func mkdirMode(t *testing.T, path string, mode os.FileMode) {
	t.Helper()
	if err := os.MkdirAll(path, 0o700); err != nil {
		t.Fatal(err)
	}
	if err := os.Chmod(path, mode); err != nil {
		t.Fatal(err)
	}
}

// newFixture provisions a synthetic root, namespace directory and read-only
// lock file, plus a synthetic legacy store whose files are made unreadable as
// a read trap and whose hashes are compared at cleanup.
func newFixture(t *testing.T) *fixture {
	return newFixtureAt(t, "ns")
}

func newFixtureAt(t *testing.T, nsRel string) *fixture {
	t.Helper()
	root := t.TempDir()
	requireExt4(t, root)
	// t.TempDir creates its directory with mode 0777 subject to the umask; the
	// synthetic trusted root must not be group- or other-writable.
	if err := os.Chmod(root, 0o700); err != nil {
		t.Fatal(err)
	}
	uid := uint32(os.Getuid())
	if uid == 0 {
		t.Fatal("tests must not run as root")
	}
	f := &fixture{root: root, uid: uid, nsPath: filepath.Join(root, nsRel)}
	mkdirMode(t, f.nsPath, 0o700)
	mkdirMode(t, filepath.Join(root, "lockdir"), 0o700)
	f.lockAbs = filepath.Join(root, "lockdir", "namespace.lock")
	if err := os.WriteFile(f.lockAbs, nil, 0o600); err != nil {
		t.Fatal(err)
	}
	if err := os.Chmod(f.lockAbs, 0o400); err != nil {
		t.Fatal(err)
	}
	nsDev, nsIno := identity(t, f.nsPath)
	lockDev, lockIno := identity(t, f.lockAbs)
	f.cfg = Config{
		RootPath:           root,
		NamespacePath:      nsRel,
		NamespaceDevice:    nsDev,
		NamespaceInode:     nsIno,
		NamespaceID:        "manual-diag-test",
		LockPath:           "lockdir/namespace.lock",
		LockDevice:         lockDev,
		LockInode:          lockIno,
		StoreOwnerUID:      uid,
		TrustedOwnerUIDs:   []uint32{uid},
		Scope:              Scope{Cloud: "synthetic-cloud", Project: "synthetic-project"},
		LegacyRoots:        []string{filepath.Join(root, ".openstack-ai")},
		LockWait:           2 * time.Second,
		InitializationOnly: true,
		Capacity:           testCapacityPolicy(),
	}
	f.installLegacyTrap(t)
	return f
}

// installLegacyTrap creates synthetic legacy investigation/memory/workflow/
// project files, records their hashes, removes all read permission and, at
// cleanup, restores permission and asserts the content is unchanged.
func (f *fixture) installLegacyTrap(t *testing.T) {
	t.Helper()
	base := filepath.Join(f.root, ".openstack-ai")
	files := map[string]string{
		"investigations/inv-synthetic.json": `{"id":"inv-synthetic","note":"synthetic legacy fixture"}`,
		"memories/mem-synthetic.json":       `{"id":"mem-synthetic"}`,
		"workflows/wf-synthetic.json":       `{"id":"wf-synthetic","approval":"synthetic-old-approval"}`,
		"projects/proj-synthetic.json":      `{"id":"proj-synthetic"}`,
	}
	f.legacy = map[string][32]byte{}
	var dirs []string
	for rel, content := range files {
		p := filepath.Join(base, rel)
		if err := os.MkdirAll(filepath.Dir(p), 0o700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(p, []byte(content), 0o600); err != nil {
			t.Fatal(err)
		}
		f.legacy[p] = sha256.Sum256([]byte(content))
		dirs = append(dirs, filepath.Dir(p))
		if err := os.Chmod(p, 0); err != nil {
			t.Fatal(err)
		}
	}
	for _, d := range dirs {
		if err := os.Chmod(d, 0o100); err != nil {
			t.Fatal(err)
		}
	}
	t.Cleanup(func() {
		for _, d := range dirs {
			os.Chmod(d, 0o700)
		}
		for p, want := range f.legacy {
			os.Chmod(p, 0o600)
			got, err := os.ReadFile(p)
			if err != nil {
				t.Errorf("legacy trap %s unreadable after test: %v", p, err)
				continue
			}
			if sha256.Sum256(got) != want {
				t.Errorf("legacy trap %s content changed", p)
			}
		}
	})
}

func (f *fixture) initialize(t *testing.T) InitResult {
	t.Helper()
	res, err := initialize(f.cfg, procMountSource{}, nil)
	if err != nil {
		t.Fatalf("initialize: %v", err)
	}
	return res
}

func promotionFrom(r InitResult) *Promotion {
	return &Promotion{
		ManifestDigest:      r.ManifestDigest,
		BootstrapGeneration: r.BootstrapGeneration,
		BootstrapDigest:     r.BootstrapDigest,
		InactiveBankDigest:  r.InactiveBankDigest,
		LockDevice:          r.LockDevice,
		LockInode:           r.LockInode,
	}
}

func (f *fixture) existing(p *Promotion) Config {
	cfg := f.cfg
	cfg.InitializationOnly = false
	cfg.Promotion = p
	return cfg
}

// openState opens a loaded holder on an initialized namespace without the
// bootstrap requirements, for record and Verified tests.
func (f *fixture) openState(t *testing.T, hooks *faultHooks) *holder {
	t.Helper()
	h, err := openLocked(f.existing(nil), procMountSource{}, hooks)
	if err != nil {
		t.Fatalf("openLocked: %v", err)
	}
	if err := h.loadState(); err != nil {
		h.close()
		t.Fatalf("loadState: %v", err)
	}
	t.Cleanup(h.close)
	return h
}

func (f *fixture) nsEntries(t *testing.T) []string {
	t.Helper()
	entries, err := os.ReadDir(f.nsPath)
	if err != nil {
		t.Fatal(err)
	}
	var names []string
	for _, e := range entries {
		names = append(names, e.Name())
	}
	sort.Strings(names)
	return names
}

func (f *fixture) hashTree(t *testing.T) map[string][32]byte {
	t.Helper()
	out := map[string][32]byte{}
	err := filepath.Walk(f.nsPath, func(p string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if info.Mode().IsRegular() {
			b, err := os.ReadFile(p)
			if err != nil {
				return err
			}
			out[p] = sha256.Sum256(b)
		} else {
			out[p] = sha256.Sum256([]byte(info.Mode().String()))
		}
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	return out
}

func expectRefusal(t *testing.T, err error, reason Reason) {
	t.Helper()
	if err == nil {
		t.Fatalf("expected refusal %q, got success", reason)
	}
	if !IsRefusal(err, reason) {
		t.Fatalf("expected refusal %q, got %v", reason, err)
	}
}

// fakeMounts uses the real mountinfo by default and injects effective ext4
// options. It is reachable only from same-package tests.
type fakeMounts struct {
	info    func() ([]byte, error)
	options func(device string) ([]byte, error)
}

func (m fakeMounts) mountInfo() ([]byte, error) {
	if m.info != nil {
		return m.info()
	}
	return procMountSource{}.mountInfo()
}

func (m fakeMounts) ext4Options(device string) ([]byte, error) {
	if m.options != nil {
		return m.options(device)
	}
	return procMountSource{}.ext4Options(device)
}

func optionsSource(opts string) fakeMounts {
	return fakeMounts{options: func(string) ([]byte, error) { return []byte(opts), nil }}
}

func resealBank(raw []byte) {
	length := int(uint32(raw[56])<<24 | uint32(raw[57])<<16 | uint32(raw[58])<<8 | uint32(raw[59]))
	end := bankHeaderSize + length
	sum := sha256.Sum256(raw[:end])
	copy(raw[end:end+bankSumSize], sum[:])
}
