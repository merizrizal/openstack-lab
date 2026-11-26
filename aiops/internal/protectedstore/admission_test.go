//go:build linux && amd64

package protectedstore

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"sync"
	"syscall"
	"testing"
	"time"
)

// syntheticCapacity is a private, test-only startup capacity seam with
// synthetic results. It is not capacity evidence and is unreachable from the
// exported constructor, which binds only the real capacity check.
type syntheticCapacity struct {
	mu     sync.Mutex
	err    error
	calls  []capacityCheck
	onCall func(capacityCheck)
}

func (c *syntheticCapacity) checkBeforeActive(req capacityCheck) error {
	c.mu.Lock()
	c.calls = append(c.calls, req)
	fn, err := c.onCall, c.err
	c.mu.Unlock()
	if fn != nil {
		fn(req)
	}
	return err
}

func promote(t *testing.T, f *fixture) Config {
	t.Helper()
	return f.existing(promotionFrom(f.initialize(t)))
}

func attempt(cfg Config, hooks *faultHooks) (*Session, error) {
	return openSession(cfg, procMountSource{}, &syntheticCapacity{}, hooks)
}

func mustSession(t *testing.T, cfg Config, hooks *faultHooks) *Session {
	t.Helper()
	s, err := attempt(cfg, hooks)
	if err != nil {
		t.Fatalf("openSession: %v", err)
	}
	t.Cleanup(func() { s.Release() })
	return s
}

func (f *fixture) controlPath() string { return filepath.Join(f.nsPath, controlName) }

func readControlRaw(t *testing.T, f *fixture) []byte {
	t.Helper()
	raw, err := os.ReadFile(f.controlPath())
	if err != nil {
		t.Fatal(err)
	}
	if len(raw) != regionFileSize {
		t.Fatalf("control size %d", len(raw))
	}
	return raw
}

func controlBanksOf(t *testing.T, f *fixture) [2]bank {
	t.Helper()
	raw := readControlRaw(t, f)
	var out [2]bank
	for i := uint8(0); i < 2; i++ {
		b, st, err := decodeBank(raw[bankOffset(i):bankOffset(i)+bankUnit], i, regionIdentity(f.cfg.NamespaceID, controlName))
		if err != nil || st != bankValid {
			t.Fatalf("control bank %d: state %v err %v", i, st, err)
		}
		out[i] = b
	}
	return out
}

func writeControlAt(t *testing.T, f *fixture, off int64, p []byte) {
	t.Helper()
	file, err := os.OpenFile(f.controlPath(), os.O_WRONLY, 0)
	if err != nil {
		t.Fatal(err)
	}
	defer file.Close()
	if _, err := file.WriteAt(p, off); err != nil {
		t.Fatal(err)
	}
	if err := file.Sync(); err != nil {
		t.Fatal(err)
	}
}

func rewriteBank(t *testing.T, f *fixture, idx uint8, mutate func(*bank)) {
	t.Helper()
	b := controlBanksOf(t, f)[idx]
	mutate(&b)
	enc, err := encodeBank(b)
	if err != nil {
		t.Fatal(err)
	}
	writeControlAt(t, f, bankOffset(idx), enc)
}

// relinkClean recomputes the CLEAN certificate's link to the current ACTIVE
// bank bytes so that a test can isolate a different check.
func relinkClean(t *testing.T, f *fixture, cleanIdx uint8) {
	t.Helper()
	raw := readControlRaw(t, f)
	activeRaw := raw[bankOffset(1-cleanIdx) : bankOffset(1-cleanIdx)+bankUnit]
	rewriteBank(t, f, cleanIdx, func(b *bank) {
		cp, err := decodeClean(b.payload)
		if err != nil {
			t.Fatal(err)
		}
		cp.activeDigest = sha256.Sum256(activeRaw)
		b.payload = encodeClean(cp)
	})
}

func refusalDetail(err error) string {
	var r *RefusalError
	if errors.As(err, &r) {
		return r.Detail
	}
	return ""
}

func sameTree(t *testing.T, want, got map[string][32]byte, what string) {
	t.Helper()
	if !reflect.DeepEqual(want, got) {
		t.Fatalf("%s changed the namespace", what)
	}
}

// expectPaused asserts that an open attempt refuses with the exact reason,
// writes nothing and can be repeated with the same result.
func expectPaused(t *testing.T, f *fixture, cfg Config, hooks *faultHooks, reason Reason, detail string) {
	t.Helper()
	before := f.hashTree(t)
	for i := 0; i < 2; i++ {
		s, err := attempt(cfg, hooks)
		if s != nil {
			s.Release()
			t.Fatalf("attempt %d established ACTIVE; expected %q", i, reason)
		}
		expectRefusal(t, err, reason)
		if detail != "" && !strings.Contains(refusalDetail(err), detail) {
			t.Fatalf("refusal detail %q does not contain %q", refusalDetail(err), detail)
		}
		sameTree(t, before, f.hashTree(t), "a paused attempt")
	}
}

// --- production cannot admit ---------------------------------------------------------

// The production constructor binds the real check: on a store whose trusted
// binding and capacity pass it establishes ACTIVE, and the same constructor
// refuses without writing anything when the check refuses. The check has no
// holder-less success path.
func TestProductionOpenSessionRunsTheRealCheck(t *testing.T) {
	f := newFixture(t)
	cfg := promote(t, f)
	bootRaw := readControlRaw(t, f)

	if err := productionCapacity().checkBeforeActive(capacityCheck{}); !IsRefusal(err, ReasonCapacity) {
		t.Fatalf("the production checker must refuse without a store to observe, got %v", err)
	}

	// Refusal: a policy that differs from the trusted binding is refused by the
	// real check before ACTIVE, writing nothing and releasing the lease.
	changed := cfg
	changed.Capacity.ManagedLimitBytes++
	before := f.hashTree(t)
	s, err := OpenSession(changed)
	if s != nil {
		s.Release()
		t.Fatal("production OpenSession established ACTIVE under a changed capacity policy")
	}
	expectRefusal(t, err, ReasonCapacityBinding)
	sameTree(t, before, f.hashTree(t), "a refused production OpenSession")
	if !bytes.Equal(bootRaw, readControlRaw(t, f)) {
		t.Fatal("control region changed by a refused open")
	}

	// Success: the real check passes on the ext4 fixture and ACTIVE is durable.
	s, err = OpenSession(cfg)
	if err != nil {
		t.Fatalf("production OpenSession with a matching binding: %v", err)
	}
	defer s.Release()
	if info := s.Info(); info.ActiveGeneration != 2 || info.Predecessor != "BOOTSTRAP" {
		t.Fatalf("session = %+v", info)
	}
	if got := controlBanksOf(t, f); got[1].kind != kindActive {
		t.Fatalf("control banks after the real check: %+v", got)
	}
}

// --- first launch ------------------------------------------------------------------------

func TestFirstActiveLinksBootstrapAndConsumesFirstLaunchAuthority(t *testing.T) {
	f := newFixture(t)
	cfg := promote(t, f)
	bootRaw := readControlRaw(t, f)

	var mu sync.Mutex
	var trace []string
	add := func(s string) { mu.Lock(); trace = append(trace, s); mu.Unlock() }
	capacity := &syntheticCapacity{onCall: func(capacityCheck) { add("capacity") }}
	hooks := &faultHooks{
		pwrite: func(fd int, p []byte, off int64) (int, error) {
			add(fmt.Sprintf("pwrite len=%d off=%d", len(p), off))
			return syscall.Pwrite(fd, p, off)
		},
		fsync: func(fd int, kind string) error { add("fsync-" + kind); return syscall.Fsync(fd) },
	}
	s, err := openSession(cfg, procMountSource{}, capacity, hooks)
	if err != nil {
		t.Fatal(err)
	}
	info := s.Info()
	if info.ActiveGeneration != 2 || info.Predecessor != "BOOTSTRAP" || !sessionIDPattern.MatchString(info.SessionID) {
		t.Fatalf("unexpected session info %+v", info)
	}
	if len(capacity.calls) != 1 || capacity.calls[0].nextGeneration != 2 || capacity.calls[0].namespaceID != cfg.NamespaceID {
		t.Fatalf("capacity check calls = %+v", capacity.calls)
	}

	// Ordering: Verified barriers, then the capacity check, then exactly one
	// control write followed by the holder's own file barrier; nothing else.
	mu.Lock()
	got := append([]string(nil), trace...)
	mu.Unlock()
	capAt, writeAt := -1, -1
	for i, e := range got {
		switch {
		case e == "capacity":
			capAt = i
		case strings.HasPrefix(e, "pwrite"):
			if writeAt >= 0 {
				t.Fatalf("more than one write before the witness was durable: %v", got)
			}
			writeAt = i
		}
	}
	wantWrite := fmt.Sprintf("pwrite len=%d off=%d", bankUnit, bankOffset(1))
	if capAt < 0 || writeAt < 0 || capAt > writeAt || got[writeAt] != wantWrite || got[len(got)-1] != "fsync-file" || writeAt != len(got)-2 {
		t.Fatalf("unexpected operation order: %v", got)
	}

	s.Release()
	raw := readControlRaw(t, f)
	if !bytes.Equal(raw[:bankUnit], bootRaw[:bankUnit]) {
		t.Fatal("the BOOTSTRAP bank was modified by the first ACTIVE")
	}
	banks := controlBanksOf(t, f)
	if banks[1].kind != kindActive || banks[1].generation != 2 || banks[0].kind != kindBootstrap {
		t.Fatalf("control banks = %v / %v", banks[0].kind, banks[1].kind)
	}
	ap, err := decodeActive(banks[1].payload)
	if err != nil {
		t.Fatal(err)
	}
	wantBoot, _ := hex.DecodeString(cfg.Promotion.BootstrapDigest)
	wantManifest, _ := hex.DecodeString(cfg.Promotion.ManifestDigest)
	if ap.predKind != kindBootstrap || ap.predGeneration != 1 || !bytes.Equal(ap.predDigest[:], wantBoot) ||
		ap.predDigest != sha256.Sum256(bootRaw[:bankUnit]) || !bytes.Equal(ap.manifestDigest[:], wantManifest) ||
		ap.promotionDigest != promotionDigest(*cfg.Promotion) || ap.sessionID != info.SessionID {
		t.Fatalf("ACTIVE is not linked to the BOOTSTRAP digest and promotion identity: %+v", ap)
	}

	// First-launch authority is consumed: BOOTSTRAP is never reusable, and
	// the next holder pauses on the durable ACTIVE.
	_, err = OpenBootstrap(cfg)
	expectRefusal(t, err, ReasonUnexpectedState)
	expectPaused(t, f, cfg, nil, ReasonStaleActive, "")
}

func TestFailedPreWorkFirstAttemptLeavesBootstrapUnchangedForLaterFirstActive(t *testing.T) {
	cases := []struct {
		name   string
		reason Reason
		src    mountOptionSource
		cap    error
		hooks  *faultHooks
	}{
		{name: "capacity refuses", reason: ReasonCapacity, cap: refuse(ReasonCapacity, "synthetic refusal", nil)},
		{name: "capacity fails with a plain error", reason: ReasonCapacity, cap: errors.New("synthetic failure")},
		{name: "mount options unsupported", reason: ReasonMountOptions, src: optionsSource("rw\nbarrier\ndata=writeback\n")},
		{name: "write fails before any byte lands", reason: ReasonNotDurable, hooks: &faultHooks{
			pwrite: func(int, []byte, int64) (int, error) { return 0, syscall.EIO }}},
		{name: "device reread differs", reason: ReasonCacheDeviceDiscrepancy, hooks: &faultHooks{
			directRead: func(fd int, p []byte, off int64) (int, error) {
				for i := range p {
					p[i] = 0
				}
				return len(p), nil
			}}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f := newFixture(t)
			cfg := promote(t, f)
			bootRaw := readControlRaw(t, f)
			before := f.hashTree(t)
			var src mountOptionSource = procMountSource{}
			if tc.src != nil {
				src = tc.src
			}
			s, err := openSession(cfg, src, &syntheticCapacity{err: tc.cap}, tc.hooks)
			if s != nil {
				s.Release()
				t.Fatal("a failed pre-work attempt established ACTIVE")
			}
			expectRefusal(t, err, tc.reason)
			if !bytes.Equal(bootRaw, readControlRaw(t, f)) {
				t.Fatal("the verified bootstrap pair changed")
			}
			sameTree(t, before, f.hashTree(t), tc.name)
			// A later holder verifies the unchanged pair and commits first ACTIVE.
			s2 := mustSession(t, cfg, nil)
			if s2.Info().ActiveGeneration != 2 || s2.Info().Predecessor != "BOOTSTRAP" {
				t.Fatalf("later first ACTIVE = %+v", s2.Info())
			}
		})
	}
}

func TestFirstActiveFailuresPauseLaterHolders(t *testing.T) {
	cases := []struct {
		name       string
		hooks      func() *faultHooks
		laterState Reason
	}{
		{"torn first ACTIVE", func() *faultHooks {
			return &faultHooks{pwrite: func(fd int, p []byte, off int64) (int, error) {
				// The whole ACTIVE bank is under 300 bytes; tear it mid-payload.
				n, err := syscall.Pwrite(fd, p[:100], off)
				if err != nil {
					return n, err
				}
				return n, syscall.EIO
			}}
		}, ReasonCorrupt},
		{"cache-only first ACTIVE (barrier fails after a complete write)", func() *faultHooks {
			// Verified's own file barrier is the first; fail the ACTIVE write's.
			calls := 0
			return &faultHooks{fsync: func(fd int, kind string) error {
				if kind == "file" {
					if calls++; calls == 2 {
						return syscall.EIO
					}
				}
				return syscall.Fsync(fd)
			}}
		}, ReasonStaleActive},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f := newFixture(t)
			cfg := promote(t, f)
			bootRaw := readControlRaw(t, f)
			s, err := attempt(cfg, tc.hooks())
			if s != nil {
				s.Release()
				t.Fatal("a failed or ambiguous ACTIVE was reported established")
			}
			expectRefusal(t, err, ReasonNotDurable)
			if !bytes.Equal(readControlRaw(t, f)[:bankUnit], bootRaw[:bankUnit]) {
				t.Fatal("the BOOTSTRAP bank was overwritten")
			}
			entries, rerr := os.ReadDir(filepath.Join(f.nsPath, recordsName))
			if rerr != nil || len(entries) != 0 {
				t.Fatalf("work was performed before a durable witness: %v %v", entries, rerr)
			}
			expectPaused(t, f, cfg, nil, tc.laterState, "")
		})
	}

	t.Run("complete first ACTIVE then process death", func(t *testing.T) {
		f := newFixture(t)
		cfg := promote(t, f)
		mustSession(t, cfg, nil).Release()
		expectPaused(t, f, cfg, nil, ReasonStaleActive, "ACTIVE session witness")
	})
}

func TestFirstStartRefusals(t *testing.T) {
	t.Run("unpromoted", func(t *testing.T) {
		f := newFixture(t)
		f.initialize(t)
		_, err := attempt(f.existing(nil), nil)
		expectRefusal(t, err, ReasonUnpromoted)
	})
	t.Run("incomplete promotion", func(t *testing.T) {
		f := newFixture(t)
		p := promotionFrom(f.initialize(t))
		p.BootstrapDigest = ""
		_, err := attempt(f.existing(p), nil)
		expectRefusal(t, err, ReasonUnpromoted)
	})
	t.Run("mismatched promotion", func(t *testing.T) {
		f := newFixture(t)
		p := promotionFrom(f.initialize(t))
		p.BootstrapGeneration = 7
		before := f.hashTree(t)
		_, err := attempt(f.existing(p), nil)
		expectRefusal(t, err, ReasonPromotionMismatch)
		sameTree(t, before, f.hashTree(t), "a mismatched promotion")
	})
	t.Run("initialization-only configuration", func(t *testing.T) {
		f := newFixture(t)
		f.initialize(t)
		_, err := attempt(f.cfg, nil)
		expectRefusal(t, err, ReasonConfig)
	})
	t.Run("missing capacity checker", func(t *testing.T) {
		f := newFixture(t)
		cfg := promote(t, f)
		_, err := openSession(cfg, procMountSource{}, nil, nil)
		expectRefusal(t, err, ReasonConfig)
	})
	t.Run("absent state is not bootstrap", func(t *testing.T) {
		f := newFixture(t)
		p := promotionFrom(f.initialize(t))
		if err := os.Remove(filepath.Join(f.nsPath, manifestName)); err != nil {
			t.Fatal(err)
		}
		before := f.hashTree(t)
		_, err := attempt(f.existing(p), nil)
		expectRefusal(t, err, ReasonUnexpectedState)
		sameTree(t, before, f.hashTree(t), "a partial namespace")
	})
	t.Run("damaged control", func(t *testing.T) {
		f := newFixture(t)
		cfg := promote(t, f)
		writeControlAt(t, f, 100, []byte{0xFF})
		expectPaused(t, f, cfg, nil, ReasonCorrupt, "")
	})
}

// --- orderly close and restart ---------------------------------------------------------

func TestOrderlyCloseAndRepeatedRestartAreDeviceVerified(t *testing.T) {
	f := newFixture(t)
	cfg := promote(t, f)
	key := testKey(f, "req-1", "state")

	var sessions []string
	for cycle := 0; cycle < 3; cycle++ {
		s := mustSession(t, cfg, nil)
		info := s.Info()
		wantGen := uint64(2 + 2*cycle)
		wantPred := "CLEAN"
		if cycle == 0 {
			wantPred = "BOOTSTRAP"
		}
		if info.ActiveGeneration != wantGen || info.Predecessor != wantPred || info.Verify.Bytes != regionFileSize {
			t.Fatalf("cycle %d: info %+v", cycle, info)
		}
		for _, prev := range sessions {
			if prev == info.SessionID {
				t.Fatal("session identity reused")
			}
		}
		sessions = append(sessions, info.SessionID)
		if err := s.CheckBeforeAdmission(); err != nil {
			t.Fatal(err)
		}
		if _, err := s.commitRecord(key, []byte(fmt.Sprintf("value-%d", cycle))); err != nil {
			t.Fatal(err)
		}
		if err := s.CloseOrderly(); err != nil {
			t.Fatal(err)
		}
		banks := controlBanksOf(t, f)
		if banks[0].kind != kindClean || banks[0].generation != wantGen+1 || banks[1].kind != kindActive || banks[1].generation != wantGen {
			t.Fatalf("cycle %d: banks %v/%d and %v/%d", cycle, banks[0].kind, banks[0].generation, banks[1].kind, banks[1].generation)
		}
		cp, err := decodeClean(banks[0].payload)
		if err != nil {
			t.Fatal(err)
		}
		raw := readControlRaw(t, f)
		if cp.sessionID != info.SessionID || cp.activeGeneration != wantGen || cp.activeDigest != sha256.Sum256(raw[bankUnit:]) {
			t.Fatalf("CLEAN does not bind its ACTIVE: %+v", cp)
		}
		if s.CloseOrderly() == nil || s.CheckBeforeAdmission() == nil {
			t.Fatal("a closed session must refuse further use")
		}
	}
	// The record survives restarts and is read through a session.
	s := mustSession(t, cfg, nil)
	value, gen, err := s.readRecord(key)
	if err != nil || string(value) != "value-2" || gen != 3 {
		t.Fatalf("record = %q gen %d err %v", value, gen, err)
	}
}

func TestSecondHolderPausesOnActiveDespiteHealthyRecords(t *testing.T) {
	f := newFixture(t)
	cfg := promote(t, f)
	s := mustSession(t, cfg, nil)
	key := testKey(f, "req-1", "state")
	if _, err := s.commitRecord(key, []byte("healthy")); err != nil {
		t.Fatal(err)
	}
	s.Release() // holder exits without an orderly close
	expectPaused(t, f, cfg, nil, ReasonStaleActive, "")
	// Repeated restart: still paused, nothing consumed, nothing cleared.
	expectPaused(t, f, cfg, nil, ReasonStaleActive, "")
}

func TestKnownLaterFailureKeepsWitnessAndNeverWritesClean(t *testing.T) {
	t.Run("initial write failure with no marker", func(t *testing.T) {
		f := newFixture(t)
		cfg := promote(t, f)
		failWrites := false
		s := mustSession(t, cfg, &faultHooks{pwrite: func(fd int, p []byte, off int64) (int, error) {
			if failWrites {
				return 0, syscall.EIO
			}
			return syscall.Pwrite(fd, p, off)
		}})
		witness := readControlRaw(t, f)
		failWrites = true
		if _, err := s.commitRecord(testKey(f, "req-1", "intent"), []byte("x")); !IsRefusal(err, ReasonNotDurable) {
			t.Fatalf("expected not-durable, got %v", err)
		}
		// Every later write fails too (an unwritable marker), and nothing is
		// attempted to make the state look healthier.
		if err := s.CloseOrderly(); !IsRefusal(err, ReasonFaulted) {
			t.Fatalf("a faulted holder must not close orderly, got %v", err)
		}
		if !bytes.Equal(witness, readControlRaw(t, f)) {
			t.Fatal("the durable pre-failure witness changed")
		}
		var recs []string
		filepath.Walk(filepath.Join(f.nsPath, recordsName), func(p string, info os.FileInfo, err error) error {
			if err == nil && info.Mode().IsRegular() {
				recs = append(recs, filepath.Base(p))
			}
			return nil
		})
		for _, name := range recs {
			if strings.HasSuffix(name, ".rec") {
				t.Fatalf("an intent or marker record exists: %s", name)
			}
		}
		expectPaused(t, f, cfg, nil, ReasonStaleActive, "")
	})
	t.Run("CLEAN write fails with an unwritable marker", func(t *testing.T) {
		f := newFixture(t)
		cfg := promote(t, f)
		failWrites := false
		s := mustSession(t, cfg, &faultHooks{pwrite: func(fd int, p []byte, off int64) (int, error) {
			if failWrites {
				return 0, syscall.EIO
			}
			return syscall.Pwrite(fd, p, off)
		}})
		witness := readControlRaw(t, f)
		failWrites = true
		if err := s.CloseOrderly(); !IsRefusal(err, ReasonNotDurable) {
			t.Fatalf("expected not-durable, got %v", err)
		}
		if !bytes.Equal(witness, readControlRaw(t, f)) {
			t.Fatal("the witness changed")
		}
		expectPaused(t, f, cfg, nil, ReasonStaleActive, "")
	})
}

func TestCloseResidualAcceptedOnlyWhenTheExactBytesPersisted(t *testing.T) {
	t.Run("final barrier errors but the exact bytes persisted", func(t *testing.T) {
		f := newFixture(t)
		cfg := promote(t, f)
		failFsync := false
		s := mustSession(t, cfg, &faultHooks{fsync: func(fd int, kind string) error {
			if failFsync && kind == "file" {
				return syscall.EIO
			}
			return syscall.Fsync(fd)
		}})
		failFsync = true
		// The closer stops and reports locally: no orderly close is claimed.
		if err := s.CloseOrderly(); !IsRefusal(err, ReasonNotDurable) {
			t.Fatalf("closer must report the barrier error, got %v", err)
		}
		next := mustSession(t, cfg, nil)
		if next.Info().Predecessor != "CLEAN" || next.Info().ActiveGeneration != 4 {
			t.Fatalf("next holder = %+v", next.Info())
		}
	})
	t.Run("final barrier errors and the bytes did not persist", func(t *testing.T) {
		f := newFixture(t)
		cfg := promote(t, f)
		failClose := false
		s := mustSession(t, cfg, &faultHooks{
			pwrite: func(fd int, p []byte, off int64) (int, error) {
				if failClose {
					return 0, syscall.EIO
				}
				return syscall.Pwrite(fd, p, off)
			},
		})
		failClose = true
		if err := s.CloseOrderly(); err == nil {
			t.Fatal("expected a refusal")
		}
		expectPaused(t, f, cfg, nil, ReasonStaleActive, "")
	})
}

// --- restart decision table ------------------------------------------------------------

func TestRestartClassificationTable(t *testing.T) {
	type state struct {
		f       *fixture
		cfg     Config
		bootRaw []byte
	}
	// cycle runs one healthy session (optionally writing a record) and an
	// orderly close, leaving an exact orderly-close pair.
	cycle := func(t *testing.T, withRecord bool) state {
		f := newFixture(t)
		cfg := promote(t, f)
		st := state{f: f, cfg: cfg, bootRaw: readControlRaw(t, f)}
		s := mustSession(t, cfg, nil)
		if withRecord {
			if _, err := s.commitRecord(testKey(f, "req-1", "state"), []byte("v")); err != nil {
				t.Fatal(err)
			}
		}
		if err := s.CloseOrderly(); err != nil {
			t.Fatal(err)
		}
		return st
	}
	mutateClean := func(t *testing.T, st state, fn func(*cleanPayload)) {
		rewriteBank(t, st.f, 0, func(b *bank) {
			cp, err := decodeClean(b.payload)
			if err != nil {
				t.Fatal(err)
			}
			fn(&cp)
			b.payload = encodeClean(cp)
		})
	}
	mutateActive := func(t *testing.T, st state, fn func(*activePayload)) {
		rewriteBank(t, st.f, 1, func(b *bank) {
			ap, err := decodeActive(b.payload)
			if err != nil {
				t.Fatal(err)
			}
			fn(&ap)
			b.payload = encodeActive(ap)
		})
		relinkClean(t, st.f, 0)
	}
	flipByte := func(t *testing.T, st state, idx uint8, at int) {
		writeControlAt(t, st.f, bankOffset(idx)+int64(at), []byte{readControlRaw(t, st.f)[bankOffset(idx)+int64(at)] ^ 0xFF})
	}

	cases := []struct {
		name   string
		setup  func(t *testing.T) state
		reason Reason
		detail string
	}{
		{"stale ACTIVE after the first session", func(t *testing.T) state {
			f := newFixture(t)
			cfg := promote(t, f)
			mustSession(t, cfg, nil).Release()
			return state{f: f, cfg: cfg}
		}, ReasonStaleActive, "ACTIVE session witness"},
		{"stale ACTIVE after a later session", func(t *testing.T) state {
			st := cycle(t, false)
			mustSession(t, st.cfg, nil).Release()
			return st
		}, ReasonStaleActive, ""},
		{"CLEAN names a different session", func(t *testing.T) state {
			st := cycle(t, false)
			mutateClean(t, st, func(p *cleanPayload) { p.sessionID = strings.Repeat("a", sessionIDHexLen) })
			return st
		}, ReasonUnprovenClose, "session identity"},
		{"CLEAN names a different ACTIVE bank", func(t *testing.T) state {
			st := cycle(t, false)
			mutateClean(t, st, func(p *cleanPayload) { p.activeDigest[0] ^= 1 })
			return st
		}, ReasonUnprovenClose, "exact ACTIVE bank"},
		{"CLEAN names a different ACTIVE generation", func(t *testing.T) state {
			st := cycle(t, false)
			mutateClean(t, st, func(p *cleanPayload) { p.activeGeneration++ })
			return st
		}, ReasonUnprovenClose, "exact ACTIVE generation"},
		{"CLEAN from another namespace", func(t *testing.T) state {
			st := cycle(t, false)
			mutateClean(t, st, func(p *cleanPayload) { p.namespaceID = "other-namespace" })
			return st
		}, ReasonUnprovenClose, "namespace identity"},
		{"CLEAN bound to another manifest", func(t *testing.T) state {
			st := cycle(t, false)
			mutateClean(t, st, func(p *cleanPayload) { p.manifestDigest[3] ^= 1 })
			return st
		}, ReasonUnprovenClose, "manifest binding"},
		{"ACTIVE without this promotion identity", func(t *testing.T) state {
			st := cycle(t, false)
			mutateActive(t, st, func(p *activePayload) { p.promotionDigest[0] ^= 1 })
			return st
		}, ReasonUnprovenClose, "promotion identity"},
		{"first ACTIVE not linked to the bound BOOTSTRAP", func(t *testing.T) state {
			st := cycle(t, false)
			mutateActive(t, st, func(p *activePayload) { p.predDigest[0] ^= 1 })
			return st
		}, ReasonUnprovenClose, "bound BOOTSTRAP"},
		{"CLEAN generation does not follow its ACTIVE", func(t *testing.T) state {
			st := cycle(t, false)
			rewriteBank(t, st.f, 0, func(b *bank) { b.generation = 9 })
			return st
		}, ReasonUnprovenClose, "does not follow"},
		{"CLEAN paired with BOOTSTRAP instead of ACTIVE", func(t *testing.T) state {
			st := cycle(t, false)
			clean := controlBanksOf(t, st.f)[0]
			clean.index = 1
			enc, err := encodeBank(clean)
			if err != nil {
				t.Fatal(err)
			}
			writeControlAt(t, st.f, bankOffset(1), enc)
			writeControlAt(t, st.f, 0, st.bootRaw[:bankUnit])
			return st
		}, ReasonUnprovenClose, "not paired with an ACTIVE"},
		{"equal control generations", func(t *testing.T) state {
			st := cycle(t, false)
			rewriteBank(t, st.f, 0, func(b *bank) { b.generation = 2 })
			return st
		}, ReasonCorrupt, "equal generation"},
		{"torn CLEAN", func(t *testing.T) state {
			st := cycle(t, false)
			flipByte(t, st, 0, bankHeaderSize+3)
			return st
		}, ReasonCorrupt, "checksum"},
		{"torn ACTIVE", func(t *testing.T) state {
			st := cycle(t, false)
			flipByte(t, st, 1, bankHeaderSize+3)
			return st
		}, ReasonCorrupt, "checksum"},
		{"half-written CLEAN", func(t *testing.T) state {
			st := cycle(t, false)
			writeControlAt(t, st.f, 40, make([]byte, bankUnit-40))
			return st
		}, ReasonCorrupt, ""},
		{"unknown bank kind", func(t *testing.T) state {
			st := cycle(t, false)
			raw := readControlRaw(t, st.f)
			bk := append([]byte(nil), raw[:bankUnit]...)
			bk[11] = 9
			resealBank(bk)
			writeControlAt(t, st.f, 0, bk)
			return st
		}, ReasonCorrupt, "kind unknown"},
		{"incompatible bank format version", func(t *testing.T) state {
			st := cycle(t, false)
			writeControlAt(t, st.f, 9, []byte{2})
			return st
		}, ReasonVersion, ""},
		{"zeroed control bank", func(t *testing.T) state {
			st := cycle(t, false)
			writeControlAt(t, st.f, 0, make([]byte, bankUnit))
			return st
		}, ReasonUnexpectedState, "unclassifiable"},
		{"record kind in the control region", func(t *testing.T) state {
			st := cycle(t, false)
			rewriteBank(t, st.f, 0, func(b *bank) { b.kind = kindRecord })
			return st
		}, ReasonUnexpectedState, "not a recognized"},
		{"altered BOOTSTRAP pair", func(t *testing.T) state {
			f := newFixture(t)
			cfg := promote(t, f)
			rewriteBank(t, f, 0, func(b *bank) { b.payload = []byte("altered") })
			return state{f: f, cfg: cfg}
		}, ReasonUnexpectedState, "exact unchanged BOOTSTRAP"},
		{"healthy pair with a damaged record", func(t *testing.T) state {
			st := cycle(t, true)
			var recFile string
			filepath.Walk(filepath.Join(st.f.nsPath, recordsName), func(p string, info os.FileInfo, err error) error {
				if err == nil && info.Mode().IsRegular() && strings.HasSuffix(p, ".rec") {
					recFile = p
				}
				return nil
			})
			if recFile == "" {
				t.Fatal("record file not found")
			}
			file, err := os.OpenFile(recFile, os.O_WRONLY, 0)
			if err != nil {
				t.Fatal(err)
			}
			defer file.Close()
			if _, err := file.WriteAt([]byte{0xFF}, bankHeaderSize+2); err != nil {
				t.Fatal(err)
			}
			return st
		}, ReasonCorrupt, "checksum"},
		{"healthy pair with a stray records entry", func(t *testing.T) state {
			st := cycle(t, false)
			if err := os.WriteFile(filepath.Join(st.f.nsPath, recordsName, "stray"), []byte("x"), 0o600); err != nil {
				t.Fatal(err)
			}
			return st
		}, ReasonUnexpectedState, "unexpected partition"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			st := tc.setup(t)
			expectPaused(t, st.f, st.cfg, nil, tc.reason, tc.detail)
		})
	}

	t.Run("positive: exact orderly-close pair with a healthy record", func(t *testing.T) {
		st := cycle(t, true)
		s := mustSession(t, st.cfg, nil)
		if s.Info().Predecessor != "CLEAN" || s.Info().ActiveGeneration != 4 {
			t.Fatalf("info %+v", s.Info())
		}
	})
}

func TestCacheOnlyOrMismatchedSuccessorDoesNotVerify(t *testing.T) {
	// Orderly-close pair on the page cache, but the device still holds the
	// older stale-ACTIVE state: an injected writeback failure. The holder's own
	// later barrier succeeds and an ordinary reread shows the CLEAN, yet the
	// page-cache-bypassing reread differs, so nothing is accepted.
	f := newFixture(t)
	cfg := promote(t, f)
	s := mustSession(t, cfg, nil)
	deviceBefore := readControlRaw(t, f) // BOOTSTRAP + ACTIVE: what the device still holds
	if err := s.CloseOrderly(); err != nil {
		t.Fatal(err)
	}
	cacheAfter := readControlRaw(t, f)
	if bytes.Equal(deviceBefore, cacheAfter) {
		t.Fatal("fixture error: CLEAN did not change the region")
	}
	stale := &faultHooks{directRead: func(fd int, p []byte, off int64) (int, error) {
		copy(p, deviceBefore[off:off+int64(len(p))])
		return len(p), nil
	}}
	expectPaused(t, f, cfg, stale, ReasonCacheDeviceDiscrepancy, "")
	// Device-verified: the same bytes read back through the real direct path.
	s2 := mustSession(t, cfg, nil)
	if s2.Info().Predecessor != "CLEAN" {
		t.Fatalf("device-verified pair not accepted: %+v", s2.Info())
	}
}

func TestCacheOnlyBootstrapDoesNotVerify(t *testing.T) {
	f := newFixture(t)
	cfg := promote(t, f)
	zero := &faultHooks{directRead: func(fd int, p []byte, off int64) (int, error) {
		for i := range p {
			p[i] = 0
		}
		return len(p), nil
	}}
	expectPaused(t, f, cfg, zero, ReasonCacheDeviceDiscrepancy, "")
	mustSession(t, cfg, nil)
}

// --- lease, ordering and durable divergence ---------------------------------------------

func TestSessionHoldsLeaseAndRefusesSecondHolderWithinBound(t *testing.T) {
	f := newFixture(t)
	cfg := promote(t, f)
	s := mustSession(t, cfg, nil)
	second := cfg
	second.LockWait = 200 * time.Millisecond
	start := time.Now()
	s2, err := attempt(second, nil)
	elapsed := time.Since(start)
	if s2 != nil {
		s2.Release()
		t.Fatal("a second holder was admitted while the lease was live")
	}
	expectRefusal(t, err, ReasonLock)
	if elapsed < 150*time.Millisecond || elapsed > 5*time.Second {
		t.Fatalf("lock wait took %v; want a bounded wait near 200ms", elapsed)
	}
	s.Release()
}

func TestNoWorkBeforeTheDurableWitness(t *testing.T) {
	f := newFixture(t)
	cfg := promote(t, f)
	var mu sync.Mutex
	var trace []string
	add := func(e string) { mu.Lock(); trace = append(trace, e); mu.Unlock() }
	hooks := &faultHooks{
		pwrite: func(fd int, p []byte, off int64) (int, error) {
			add(fmt.Sprintf("pwrite len=%d", len(p)))
			return syscall.Pwrite(fd, p, off)
		},
		fsync: func(fd int, kind string) error { add("fsync-" + kind); return syscall.Fsync(fd) },
	}
	s := mustSession(t, cfg, hooks)
	mu.Lock()
	mark := len(trace)
	mu.Unlock()
	if _, err := s.commitRecord(testKey(f, "req-1", "state"), []byte("v")); err != nil {
		t.Fatal(err)
	}
	mu.Lock()
	defer mu.Unlock()
	for i, e := range trace[:mark] {
		if e == fmt.Sprintf("pwrite len=%d", regionFileSize) {
			t.Fatalf("a record write precedes the durable witness at %d: %v", i, trace)
		}
	}
	if trace[mark-1] != "fsync-file" || trace[mark-2] != fmt.Sprintf("pwrite len=%d", bankUnit) {
		t.Fatalf("the witness is not the last pre-session action: %v", trace[:mark])
	}
	firstAfter := ""
	for _, e := range trace[mark:] {
		if strings.HasPrefix(e, "pwrite") {
			firstAfter = e
			break
		}
	}
	if firstAfter != fmt.Sprintf("pwrite len=%d", regionFileSize) {
		t.Fatalf("the first post-witness write is not the record: %v", trace[mark:])
	}
}

func TestCheckBeforeAdmissionDetectsDurableDivergence(t *testing.T) {
	// A holder's memory of a healthy session is not health: the durable
	// control region is compared on every check.
	f := newFixture(t)
	cfg := promote(t, f)
	s := mustSession(t, cfg, nil)
	if err := s.CheckBeforeAdmission(); err != nil {
		t.Fatal(err)
	}
	writeControlAt(t, f, 0, make([]byte, bankUnit)) // an unauthorized writer alters the other bank
	err := s.CheckBeforeAdmission()
	expectRefusal(t, err, ReasonUnexpectedState)
	if err := s.CloseOrderly(); !IsRefusal(err, ReasonFaulted) {
		t.Fatalf("a diverged session must not write CLEAN, got %v", err)
	}
	if !allZero(readControlRaw(t, f)[:bankUnit]) {
		t.Fatal("CLEAN was written over a diverged control region")
	}
}

func TestSessionPayloadCodecRefusals(t *testing.T) {
	ap := activePayload{namespaceID: "manual-diag-test", sessionID: strings.Repeat("0", sessionIDHexLen), predKind: kindClean, predGeneration: 3}
	enc := encodeActive(ap)
	if got, err := decodeActive(enc); err != nil || got != ap {
		t.Fatalf("round trip: %+v %v", got, err)
	}
	cp := cleanPayload{namespaceID: "manual-diag-test", sessionID: strings.Repeat("f", sessionIDHexLen), activeGeneration: 4}
	if got, err := decodeClean(encodeClean(cp)); err != nil || got != cp {
		t.Fatalf("round trip: %+v %v", got, err)
	}
	bad := map[string][]byte{
		"empty":      nil,
		"truncated":  enc[:len(enc)-1],
		"trailing":   append(append([]byte(nil), enc...), 0),
		"wrong kind": append([]byte{sessionPayloadVersion, byte(kindClean)}, enc[2:]...),
		"wrong ver":  append([]byte{9}, enc[1:]...),
		"huge field": append([]byte{sessionPayloadVersion, byte(kindActive), 0xFF, 0xFF, 0xFF, 0xFF}, enc[6:]...),
		"bad pred": func() []byte {
			b := encodeActive(activePayload{namespaceID: ap.namespaceID, sessionID: ap.sessionID, predKind: kindEmpty})
			return b
		}(),
		"bad session":  encodeActive(activePayload{namespaceID: ap.namespaceID, sessionID: "xyz", predKind: kindClean}),
		"bad namespce": encodeActive(activePayload{namespaceID: "Bad Name", sessionID: ap.sessionID, predKind: kindClean}),
	}
	for name, raw := range bad {
		if _, err := decodeActive(raw); !IsRefusal(err, ReasonCorrupt) {
			t.Errorf("%s: expected corrupt refusal, got %v", name, err)
		}
	}
	if _, err := decodeClean(enc); !IsRefusal(err, ReasonCorrupt) {
		t.Errorf("an ACTIVE payload decoded as CLEAN: %v", err)
	}
}
