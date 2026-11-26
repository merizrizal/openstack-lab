//go:build linux && amd64

package protectedstore

import (
	"bytes"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"syscall"
	"testing"
)

func testKey(f *fixture, request, name string) recordKey {
	return recordKey{scope: f.cfg.Scope, requestID: request, name: name}
}

func recordPath(f *fixture, k recordKey) string {
	s, r, file, _ := k.paths()
	return filepath.Join(f.nsPath, recordsName, s, r, file)
}

func TestRecordFirstCreateUpdateAndReopen(t *testing.T) {
	f := newFixture(t)
	f.initialize(t)
	h := f.openState(t, nil)
	k := testKey(f, "req-0001", "intent")
	gen, err := h.commitRecord(k, []byte("sanitized-v1"))
	if err != nil || gen != 1 {
		t.Fatalf("first commit gen=%d err=%v", gen, err)
	}
	gen, err = h.commitRecord(k, []byte("sanitized-v2"))
	if err != nil || gen != 2 {
		t.Fatalf("second commit gen=%d err=%v", gen, err)
	}
	gen, err = h.commitRecord(k, []byte("sanitized-v3"))
	if err != nil || gen != 3 {
		t.Fatalf("third commit gen=%d err=%v", gen, err)
	}
	h.close()

	h2 := f.openState(t, nil)
	value, gen, err := h2.readRecord(k)
	if err != nil || gen != 3 || string(value) != "sanitized-v3" {
		t.Fatalf("reopen read value=%q gen=%d err=%v", value, gen, err)
	}
	// The previous generation remains intact in the other bank.
	raw, err := os.ReadFile(recordPath(f, k))
	if err != nil {
		t.Fatal(err)
	}
	region := regionIdentity(f.cfg.NamespaceID, recordsName+"/"+strings.TrimPrefix(recordPath(f, k), filepath.Join(f.nsPath, recordsName)+"/"))
	b0, _, err0 := decodeBank(raw[:bankUnit], 0, region)
	b1, _, err1 := decodeBank(raw[bankUnit:], 1, region)
	if err0 != nil || err1 != nil || b0.generation != 3 || b1.generation != 2 {
		t.Fatalf("bank generations %d/%d errs %v %v", b0.generation, b1.generation, err0, err1)
	}
	info, err := os.Stat(recordPath(f, k))
	if err != nil || info.Mode().Perm() != 0o600 || info.Size() != regionFileSize {
		t.Fatalf("record file %v %v", info, err)
	}
}

func TestRecordsArePartitionedByScopeAndRequestWithoutIdentifierNames(t *testing.T) {
	f := newFixture(t)
	f.initialize(t)
	h := f.openState(t, nil)
	for _, req := range []string{"req-a", "req-b"} {
		if _, err := h.commitRecord(testKey(f, req, "intent"), []byte("v-"+req)); err != nil {
			t.Fatal(err)
		}
	}
	scopes, err := os.ReadDir(filepath.Join(f.nsPath, recordsName))
	if err != nil || len(scopes) != 1 {
		t.Fatalf("scope partitions %v %v", scopes, err)
	}
	name := regexp.MustCompile(`^[sr]-[0-9a-f]{40}$`)
	if !name.MatchString(scopes[0].Name()) {
		t.Fatalf("scope partition name %q", scopes[0].Name())
	}
	reqs, err := os.ReadDir(filepath.Join(f.nsPath, recordsName, scopes[0].Name()))
	if err != nil || len(reqs) != 2 {
		t.Fatalf("request partitions %v %v", reqs, err)
	}
	for _, r := range reqs {
		if !name.MatchString(r.Name()) || strings.Contains(r.Name(), "req-") {
			t.Fatalf("request partition leaks identifiers: %q", r.Name())
		}
	}
	for _, req := range []string{"req-a", "req-b"} {
		v, _, err := h.readRecord(testKey(f, req, "intent"))
		if err != nil || string(v) != "v-"+req {
			t.Fatalf("read %s = %q %v", req, v, err)
		}
	}
	// Another scope is refused, not silently partitioned.
	other := recordKey{scope: Scope{Cloud: "synthetic-cloud", Project: "other-project"}, requestID: "req-a", name: "intent"}
	_, err = h.commitRecord(other, []byte("x"))
	expectRefusal(t, err, ReasonScope)
	_, _, err = h.readRecord(other)
	expectRefusal(t, err, ReasonScope)
}

func TestRecordBoundsAndKeyValidation(t *testing.T) {
	f := newFixture(t)
	f.initialize(t)
	h := f.openState(t, nil)
	_, err := h.commitRecord(testKey(f, "req-1", "intent"), make([]byte, maxBankPayload))
	expectRefusal(t, err, ReasonLimit)
	for _, k := range []recordKey{
		testKey(f, "../escape", "intent"),
		testKey(f, "req-1", "Bad/Name"),
		testKey(f, "", "intent"),
		testKey(f, "req-1", ""),
	} {
		_, err := h.commitRecord(k, []byte("x"))
		expectRefusal(t, err, ReasonConfig)
	}
	_, _, err = h.readRecord(testKey(f, "req-missing", "intent"))
	expectRefusal(t, err, ReasonUnexpectedState)
}

func TestCorruptRecordsAreRefusedNotRepaired(t *testing.T) {
	type tc struct {
		name   string
		reason Reason
		mutate func(t *testing.T, f *fixture, raw []byte, region [32]byte) []byte
	}
	cases := []tc{
		{"payload byte flipped", ReasonCorrupt, func(t *testing.T, f *fixture, raw []byte, _ [32]byte) []byte {
			raw[bankHeaderSize+2] ^= 0xff
			return raw
		}},
		{"torn inactive bank", ReasonCorrupt, func(t *testing.T, f *fixture, raw []byte, _ [32]byte) []byte {
			for i := bankUnit; i < bankUnit+64; i++ {
				raw[i] = 0x77
			}
			return raw
		}},
		{"zeroed inactive bank", ReasonCorrupt, func(t *testing.T, f *fixture, raw []byte, _ [32]byte) []byte {
			for i := bankUnit; i < len(raw); i++ {
				raw[i] = 0
			}
			return raw
		}},
		{"equal generations", ReasonCorrupt, func(t *testing.T, f *fixture, raw []byte, region [32]byte) []byte {
			b0, _, _ := decodeBank(raw[:bankUnit], 0, region)
			dup, err := encodeBank(bank{index: 1, kind: kindRecord, generation: b0.generation, region: region, payload: b0.payload})
			if err != nil {
				t.Fatal(err)
			}
			return append(raw[:bankUnit], dup...)
		}},
		{"incompatible bank version", ReasonVersion, func(t *testing.T, f *fixture, raw []byte, _ [32]byte) []byte {
			raw[9] = 9
			resealBank(raw[:bankUnit])
			return raw
		}},
		{"truncated", ReasonCorrupt, func(t *testing.T, f *fixture, raw []byte, _ [32]byte) []byte {
			return raw[:bankUnit+10]
		}},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			f := newFixture(t)
			f.initialize(t)
			h := f.openState(t, nil)
			k := testKey(f, "req-1", "outcome")
			if _, err := h.commitRecord(k, []byte("sanitized")); err != nil {
				t.Fatal(err)
			}
			_, _, _, rel := k.paths()
			raw, err := os.ReadFile(recordPath(f, k))
			if err != nil {
				t.Fatal(err)
			}
			mutated := c.mutate(t, f, raw, regionIdentity(f.cfg.NamespaceID, rel))
			if err := os.WriteFile(recordPath(f, k), mutated, 0o600); err != nil {
				t.Fatal(err)
			}
			_, _, err = h.readRecord(k)
			expectRefusal(t, err, c.reason)
			_, err = h.commitRecord(k, []byte("next"))
			expectRefusal(t, err, c.reason)
			after, _ := os.ReadFile(recordPath(f, k))
			if !bytes.Equal(after, mutated) {
				t.Fatal("corrupt record was repaired or overwritten")
			}
		})
	}
}

func TestRecordIdentityAndLinkAttacks(t *testing.T) {
	t.Run("record moved to another request", func(t *testing.T) {
		f := newFixture(t)
		f.initialize(t)
		h := f.openState(t, nil)
		a, b := testKey(f, "req-a", "intent"), testKey(f, "req-b", "intent")
		for _, k := range []recordKey{a, b} {
			if _, err := h.commitRecord(k, []byte("v")); err != nil {
				t.Fatal(err)
			}
		}
		raw, _ := os.ReadFile(recordPath(f, a))
		if err := os.WriteFile(recordPath(f, b), raw, 0o600); err != nil {
			t.Fatal(err)
		}
		_, _, err := h.readRecord(b)
		expectRefusal(t, err, ReasonCorrupt)
	})
	t.Run("record hard-linked", func(t *testing.T) {
		f := newFixture(t)
		f.initialize(t)
		h := f.openState(t, nil)
		k := testKey(f, "req-a", "intent")
		if _, err := h.commitRecord(k, []byte("v")); err != nil {
			t.Fatal(err)
		}
		if err := os.Link(recordPath(f, k), filepath.Join(f.root, "record-link")); err != nil {
			t.Fatal(err)
		}
		_, _, err := h.readRecord(k)
		expectRefusal(t, err, ReasonUnsafePath)
		_, err = h.commitRecord(k, []byte("v2"))
		expectRefusal(t, err, ReasonUnsafePath)
	})
	t.Run("record replaced by symlink", func(t *testing.T) {
		f := newFixture(t)
		f.initialize(t)
		h := f.openState(t, nil)
		k := testKey(f, "req-a", "intent")
		if _, err := h.commitRecord(k, []byte("v")); err != nil {
			t.Fatal(err)
		}
		p := recordPath(f, k)
		if err := os.Rename(p, filepath.Join(f.root, "elsewhere")); err != nil {
			t.Fatal(err)
		}
		if err := os.Symlink(filepath.Join(f.root, "elsewhere"), p); err != nil {
			t.Fatal(err)
		}
		_, _, err := h.readRecord(k)
		expectRefusal(t, err, ReasonUnsafePath)
	})
	t.Run("partition directory mode widened", func(t *testing.T) {
		f := newFixture(t)
		f.initialize(t)
		h := f.openState(t, nil)
		k := testKey(f, "req-a", "intent")
		if _, err := h.commitRecord(k, []byte("v")); err != nil {
			t.Fatal(err)
		}
		dir := filepath.Dir(recordPath(f, k))
		if err := os.Chmod(dir, 0o500); err != nil {
			t.Fatal(err)
		}
		t.Cleanup(func() { os.Chmod(dir, 0o700) })
		_, err := h.commitRecord(testKey(f, "req-a", "outcome"), []byte("v"))
		expectRefusal(t, err, ReasonOwnership)
	})
}

func TestShortWritesAreLoopedToCompletion(t *testing.T) {
	f := newFixture(t)
	f.initialize(t)
	calls := 0
	h := f.openState(t, &faultHooks{pwrite: func(fd int, p []byte, off int64) (int, error) {
		calls++
		n := len(p) / 3
		if n == 0 {
			n = len(p)
		}
		return syscall.Pwrite(fd, p[:n], off)
	}})
	k := testKey(f, "req-1", "intent")
	for i, v := range []string{"a", "b"} {
		if _, err := h.commitRecord(k, []byte(v)); err != nil {
			t.Fatalf("commit %d: %v", i, err)
		}
	}
	if calls < 4 {
		t.Fatalf("short writes not exercised: %d calls", calls)
	}
	value, gen, err := h.readRecord(k)
	if err != nil || gen != 2 || string(value) != "b" {
		t.Fatalf("read %q %d %v", value, gen, err)
	}
}

// Every injected write, sync, rename or permission fault is refused, faults
// the holder, and never yields a saved-success report.
func TestInjectedFaultsNeverReportSavedSuccess(t *testing.T) {
	const (
		priorIntact   = "prior generation intact"
		absentWithTmp = "absent, temporary left, retry refused"
		unclaimed     = "bytes may be visible but durability was never claimed"
		tornRefused   = "torn inactive bank refuses; neither generation is selected"
	)
	failKind := func(kind string) func(int, string) error {
		return func(fd int, k string) error {
			if k == kind {
				return syscall.EIO
			}
			return syscall.Fsync(fd)
		}
	}
	cases := []struct {
		name   string
		update bool
		expect string
		hooks  func() *faultHooks
	}{
		{"zero-progress write on create", false, absentWithTmp, func() *faultHooks {
			return &faultHooks{pwrite: func(int, []byte, int64) (int, error) { return 0, nil }}
		}},
		{"write error on create", false, absentWithTmp, func() *faultHooks {
			return &faultHooks{pwrite: func(int, []byte, int64) (int, error) { return 0, syscall.EIO }}
		}},
		{"file sync error on create", false, absentWithTmp, func() *faultHooks {
			return &faultHooks{fsync: failKind("file")}
		}},
		{"rename error on create", false, absentWithTmp, func() *faultHooks {
			return &faultHooks{rename: func(int, string, int, string) error { return syscall.EIO }}
		}},
		{"rename permission fault on create", false, absentWithTmp, func() *faultHooks {
			return &faultHooks{rename: func(int, string, int, string) error { return syscall.EACCES }}
		}},
		{"directory sync error on create", false, unclaimed, func() *faultHooks {
			return &faultHooks{fsync: failKind("dir")}
		}},
		{"write error on update", true, priorIntact, func() *faultHooks {
			return &faultHooks{pwrite: func(int, []byte, int64) (int, error) { return 0, syscall.EIO }}
		}},
		{"short then failing write on update", true, tornRefused, func() *faultHooks {
			n := 0
			return &faultHooks{pwrite: func(fd int, p []byte, off int64) (int, error) {
				n++
				if n == 1 {
					return syscall.Pwrite(fd, p[:100], off)
				}
				return 0, syscall.ENOSPC
			}}
		}},
		{"file sync error on update", true, unclaimed, func() *faultHooks {
			return &faultHooks{fsync: failKind("file")}
		}},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			f := newFixture(t)
			f.initialize(t)
			k := testKey(f, "req-1", "intent")
			fresh := testKey(f, "req-1", "outcome")
			setup := f.openState(t, nil)
			if _, err := setup.commitRecord(k, []byte("committed-v1")); err != nil {
				t.Fatal(err)
			}
			setup.close()

			h := f.openState(t, c.hooks())
			target := fresh
			if c.update {
				target = k
			}
			gen, err := h.commitRecord(target, []byte("not-saved"))
			if err == nil || gen != 0 {
				t.Fatalf("fault reported success: gen=%d err=%v", gen, err)
			}
			expectRefusal(t, err, ReasonNotDurable)
			_, err = h.commitRecord(testKey(f, "req-2", "intent"), []byte("after-fault"))
			expectRefusal(t, err, ReasonFaulted)
			h.close()

			h2 := f.openState(t, nil)
			switch c.expect {
			case priorIntact:
				value, gen, err := h2.readRecord(k)
				if err != nil || gen != 1 || string(value) != "committed-v1" {
					t.Fatalf("prior generation not intact: %q %d %v", value, gen, err)
				}
			case absentWithTmp:
				if _, _, err := h2.readRecord(fresh); err == nil {
					t.Fatal("failed create is readable as a committed record")
				}
				tmp := filepath.Join(filepath.Dir(recordPath(f, fresh)), ".outcome.rec.tmp")
				if _, err := os.Lstat(tmp); err != nil {
					t.Fatalf("temporary missing (was it silently removed?): %v", err)
				}
				_, err := h2.commitRecord(fresh, []byte("retry"))
				expectRefusal(t, err, ReasonNotDurable)
			case tornRefused:
				_, _, err := h2.readRecord(k)
				expectRefusal(t, err, ReasonCorrupt)
			case unclaimed:
				// The writer reported failure and faulted; a later holder's
				// device-state classification belongs to the restart rules.
			}
		})
	}
}
