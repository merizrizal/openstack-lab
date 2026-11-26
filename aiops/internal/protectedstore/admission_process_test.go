//go:build linux && amd64

package protectedstore

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"testing"
	"time"
)

// Independent-process tests. The test binary re-executes itself as a child
// (os/exec is used in _test.go files only; production code stays exec-free).
// Children are commanded over stdin/stdout with line-delimited JSON, so the
// parent can sequence real flock contention, process death and restart
// without sleeps. Every child is test-spawned, bounded in number and reaped.

const (
	helperRoleEnv         = "AIOPS_PS_TEST_HELPER"
	helperCfgEnv          = "AIOPS_PS_TEST_CONFIG"
	maxConcurrentChildren = 16
	maxTotalChildren      = 500
	replyTimeout          = 30 * time.Second
	waitTimeout           = 20 * time.Second
)

var childStats struct {
	mu                  sync.Mutex
	spawned, live, peak int
}

func TestMain(m *testing.M) {
	if os.Getenv(helperRoleEnv) != "" {
		os.Exit(runHelper())
	}
	code := m.Run()
	childStats.mu.Lock()
	spawned, live, peak := childStats.spawned, childStats.live, childStats.peak
	childStats.mu.Unlock()
	fmt.Fprintf(os.Stderr, "child processes: spawned=%d peak-concurrent=%d unreaped=%d\n", spawned, peak, live)
	if live != 0 {
		fmt.Fprintln(os.Stderr, "FAIL: test-spawned child processes were not reaped")
		code = 1
	}
	os.Exit(code)
}

// --- child side --------------------------------------------------------------------------

type helperRequest struct {
	Op         string `json:"op"`
	LockWaitMs int    `json:"lock_wait_ms,omitempty"`
	Exported   bool   `json:"exported,omitempty"`
	FailWrites bool   `json:"fail_writes,omitempty"`
	FailFsync  bool   `json:"fail_fsync,omitempty"`
	Request    string `json:"request,omitempty"`
	Name       string `json:"name,omitempty"`
	Value      string `json:"value,omitempty"`
}

type helperReply struct {
	OK          bool   `json:"ok"`
	Reason      string `json:"reason,omitempty"`
	Detail      string `json:"detail,omitempty"`
	Generation  uint64 `json:"generation,omitempty"`
	Predecessor string `json:"predecessor,omitempty"`
	Session     string `json:"session,omitempty"`
	Pid         int    `json:"pid"`
	ElapsedMs   int64  `json:"elapsed_ms"`
}

func runHelper() int {
	var cfg Config
	if err := json.Unmarshal([]byte(os.Getenv(helperCfgEnv)), &cfg); err != nil {
		fmt.Fprintln(os.Stderr, "helper: bad configuration:", err)
		return 2
	}
	var failWrites, failFsync atomic.Bool
	hooks := &faultHooks{
		pwrite: func(fd int, p []byte, off int64) (int, error) {
			if failWrites.Load() {
				return 0, syscall.EIO
			}
			return syscall.Pwrite(fd, p, off)
		},
		fsync: func(fd int, kind string) error {
			if failFsync.Load() && kind == "file" {
				return syscall.EIO
			}
			for {
				if err := syscall.Fsync(fd); err != syscall.EINTR {
					return err
				}
			}
		},
	}
	var sess *Session
	var boot *BootstrapHolder
	enc := json.NewEncoder(os.Stdout)
	dec := json.NewDecoder(os.Stdin)
	for {
		var req helperRequest
		if err := dec.Decode(&req); err != nil {
			break // stdin closed: release and exit
		}
		start := time.Now()
		rep := helperReply{Pid: os.Getpid()}
		var err error
		noSession := refuse(ReasonClosed, "no session in this process", nil)
		switch req.Op {
		case "open-session":
			c := cfg
			if req.LockWaitMs > 0 {
				c.LockWait = time.Duration(req.LockWaitMs) * time.Millisecond
			}
			if req.Exported {
				sess, err = OpenSession(c)
			} else {
				sess, err = openSession(c, procMountSource{}, &syntheticCapacity{}, hooks)
			}
			if err == nil {
				info := sess.Info()
				rep.Generation, rep.Predecessor, rep.Session = info.ActiveGeneration, info.Predecessor, info.SessionID
			}
		case "open-bootstrap":
			boot, err = openBootstrap(cfg, procMountSource{}, nil)
		case "set-faults":
			failWrites.Store(req.FailWrites)
			failFsync.Store(req.FailFsync)
		case "commit-record":
			if sess == nil {
				err = noSession
				break
			}
			_, err = sess.commitRecord(recordKey{scope: cfg.Scope, requestID: req.Request, name: req.Name}, []byte(req.Value))
		case "check":
			if sess == nil {
				err = noSession
				break
			}
			err = sess.CheckBeforeAdmission()
		case "close-orderly":
			if sess == nil {
				err = noSession
				break
			}
			err = sess.CloseOrderly()
		default:
			err = fmt.Errorf("unknown op %q", req.Op)
		}
		rep.ElapsedMs = time.Since(start).Milliseconds()
		rep.OK = err == nil
		if err != nil {
			rep.Reason = "error"
			var r *RefusalError
			if errors.As(err, &r) {
				rep.Reason, rep.Detail = string(r.Reason), r.Detail
			} else {
				rep.Detail = err.Error()
			}
		}
		if enc.Encode(rep) != nil {
			break
		}
	}
	if sess != nil {
		sess.Release()
	}
	if boot != nil {
		boot.Close()
	}
	return 0
}

// --- parent side -------------------------------------------------------------------------

type replyWriter struct {
	mu  sync.Mutex
	buf []byte
	out chan helperReply
}

func (w *replyWriter) Write(p []byte) (int, error) {
	w.mu.Lock()
	defer w.mu.Unlock()
	w.buf = append(w.buf, p...)
	for {
		i := bytes.IndexByte(w.buf, '\n')
		if i < 0 {
			return len(p), nil
		}
		var r helperReply
		if err := json.Unmarshal(w.buf[:i], &r); err == nil {
			w.out <- r
		}
		w.buf = w.buf[i+1:]
	}
}

type child struct {
	t       *testing.T
	cmd     *exec.Cmd
	stdin   io.WriteCloser
	replies chan helperReply
	stderr  *bytes.Buffer
	done    chan error
	pid     int

	mu     sync.Mutex
	reaped bool
	ws     syscall.WaitStatus
}

func startChild(t *testing.T, cfg Config) *child {
	t.Helper()
	exe := os.Args[0]
	if !filepath.IsAbs(exe) {
		t.Fatalf("test binary path %q is not absolute", exe)
	}
	raw, err := json.Marshal(cfg)
	if err != nil {
		t.Fatal(err)
	}
	cmd := exec.Command(exe)
	cmd.Env = append(os.Environ(), helperRoleEnv+"=1", helperCfgEnv+"="+string(raw))
	c := &child{t: t, cmd: cmd, replies: make(chan helperReply, 256), stderr: &bytes.Buffer{}, done: make(chan error, 1)}
	cmd.Stdout = &replyWriter{out: c.replies}
	cmd.Stderr = c.stderr
	if c.stdin, err = cmd.StdinPipe(); err != nil {
		t.Fatal(err)
	}
	childStats.mu.Lock()
	if childStats.live >= maxConcurrentChildren || childStats.spawned >= maxTotalChildren {
		childStats.mu.Unlock()
		t.Fatalf("authorized child process bound exceeded (live %d, total %d)", childStats.live, childStats.spawned)
	}
	if err := cmd.Start(); err != nil {
		childStats.mu.Unlock()
		t.Fatalf("starting child: %v", err)
	}
	childStats.spawned++
	childStats.live++
	if childStats.live > childStats.peak {
		childStats.peak = childStats.live
	}
	childStats.mu.Unlock()
	c.pid = cmd.Process.Pid
	go func() { c.done <- cmd.Wait() }()
	t.Cleanup(c.reap)
	return c
}

func (c *child) callErr(req helperRequest) (helperReply, error) {
	b, err := json.Marshal(req)
	if err != nil {
		return helperReply{}, err
	}
	if _, err := c.stdin.Write(append(b, '\n')); err != nil {
		return helperReply{}, fmt.Errorf("child %d: write: %v; stderr: %s", c.pid, err, c.stderr.String())
	}
	select {
	case r := <-c.replies:
		return r, nil
	case <-time.After(replyTimeout):
		return helperReply{}, fmt.Errorf("child %d did not reply to %q within %v", c.pid, req.Op, replyTimeout)
	}
}

func (c *child) call(req helperRequest) helperReply {
	c.t.Helper()
	r, err := c.callErr(req)
	if err != nil {
		c.t.Fatal(err)
	}
	return r
}

func (c *child) expect(req helperRequest) helperReply {
	c.t.Helper()
	r := c.call(req)
	if !r.OK {
		c.t.Fatalf("child %d %s: %s (%s)", c.pid, req.Op, r.Reason, r.Detail)
	}
	return r
}

func (c *child) expectRefusal(req helperRequest, reason Reason) helperReply {
	c.t.Helper()
	r := c.call(req)
	if r.OK || r.Reason != string(reason) {
		c.t.Fatalf("child %d %s: expected refusal %q, got ok=%v reason=%q (%s)", c.pid, req.Op, reason, r.OK, r.Reason, r.Detail)
	}
	return r
}

// wait reaps the child exactly once and returns its wait status.
func (c *child) wait() syscall.WaitStatus {
	c.t.Helper()
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.reaped {
		return c.ws
	}
	select {
	case <-c.done:
	case <-time.After(waitTimeout):
		syscall.Kill(c.pid, syscall.SIGKILL)
		<-c.done
		c.t.Errorf("child %d did not exit within %v and was killed", c.pid, waitTimeout)
	}
	c.ws = c.cmd.ProcessState.Sys().(syscall.WaitStatus)
	c.reaped = true
	childStats.mu.Lock()
	childStats.live--
	childStats.mu.Unlock()
	if err := syscall.Kill(c.pid, 0); err != syscall.ESRCH {
		c.t.Errorf("child %d still exists after being reaped (kill(0) = %v)", c.pid, err)
	}
	return c.ws
}

// kill simulates process death with SIGKILL of this test-spawned child.
func (c *child) kill() syscall.WaitStatus {
	c.t.Helper()
	syscall.Kill(c.pid, syscall.SIGKILL)
	ws := c.wait()
	if !ws.Signaled() || ws.Signal() != syscall.SIGKILL {
		c.t.Fatalf("child %d status %v, want killed by SIGKILL", c.pid, ws)
	}
	return ws
}

// finish closes the child's stdin so it releases its lease and exits 0.
func (c *child) finish() {
	c.t.Helper()
	c.stdin.Close()
	if ws := c.wait(); !ws.Exited() || ws.ExitStatus() != 0 {
		c.t.Fatalf("child %d status %v stderr %s, want exit 0", c.pid, ws, c.stderr.String())
	}
}

func (c *child) reap() {
	c.mu.Lock()
	reaped := c.reaped
	c.mu.Unlock()
	if !reaped {
		syscall.Kill(c.pid, syscall.SIGKILL)
		c.wait()
	}
}

// probeLock is an actual lock observation by an independent open file
// description: a non-blocking exclusive flock on the provisioned lock.
func probeLock(t *testing.T, path string) error {
	t.Helper()
	fd, err := syscall.Open(path, syscall.O_RDONLY|syscall.O_CLOEXEC, 0)
	if err != nil {
		t.Fatalf("open lock for probing: %v", err)
	}
	defer syscall.Close(fd)
	err = syscall.Flock(fd, syscall.LOCK_EX|syscall.LOCK_NB)
	if err == nil {
		syscall.Flock(fd, syscall.LOCK_UN)
	}
	return err
}

func controlSummary(t *testing.T, f *fixture) string {
	t.Helper()
	b := controlBanksOf(t, f)
	return fmt.Sprintf("bank0=%d/g%d bank1=%d/g%d", b[0].kind, b[0].generation, b[1].kind, b[1].generation)
}

func recordFiles(f *fixture) []string {
	var out []string
	filepath.Walk(filepath.Join(f.nsPath, recordsName), func(p string, info os.FileInfo, err error) error {
		if err == nil && info.Mode().IsRegular() && strings.HasSuffix(p, ".rec") {
			out = append(out, p)
		}
		return nil
	})
	return out
}

// --- tests -------------------------------------------------------------------------------

func TestProcessLiveSessionContention(t *testing.T) {
	f := newFixture(t)
	cfg := promote(t, f)

	a := startChild(t, cfg)
	ra := a.expect(helperRequest{Op: "open-session"})
	if ra.Generation != 2 || ra.Predecessor != "BOOTSTRAP" {
		t.Fatalf("first session = %+v", ra)
	}
	witness := f.hashTree(t)
	if err := probeLock(t, f.lockAbs); err != syscall.EWOULDBLOCK {
		t.Fatalf("independent flock probe while the live session holds the lease: %v, want EWOULDBLOCK", err)
	}
	t.Logf("flock probe while child %d holds the lease: EWOULDBLOCK (%s)", a.pid, controlSummary(t, f))

	b := startChild(t, cfg)
	rb := b.expectRefusal(helperRequest{Op: "open-session", LockWaitMs: 300}, ReasonLock)
	if rb.ElapsedMs < 250 || rb.ElapsedMs > 10000 {
		t.Fatalf("second process waited %dms; want a bounded wait near 300ms", rb.ElapsedMs)
	}
	t.Logf("second process %d refused after %dms: %s", b.pid, rb.ElapsedMs, rb.Detail)
	sameTree(t, witness, f.hashTree(t), "a refused contender")

	a.expect(helperRequest{Op: "close-orderly"})
	if err := probeLock(t, f.lockAbs); err != nil {
		t.Fatalf("lock not released after the orderly close: %v", err)
	}
	c := startChild(t, cfg)
	rc := c.expect(helperRequest{Op: "open-session"})
	if rc.Generation != 4 || rc.Predecessor != "CLEAN" {
		t.Fatalf("restart after an orderly close = %+v", rc)
	}
	for _, p := range []*child{a, b, c} {
		p.finish()
	}
	t.Logf("exit statuses 0; final control %s", controlSummary(t, f))
}

func TestProcessDeathLeavesWitnessAndReleasesLock(t *testing.T) {
	f := newFixture(t)
	cfg := promote(t, f)
	a := startChild(t, cfg)
	a.expect(helperRequest{Op: "open-session"})
	a.expect(helperRequest{Op: "commit-record", Request: "req-1", Name: "state", Value: "healthy"})
	if err := probeLock(t, f.lockAbs); err != syscall.EWOULDBLOCK {
		t.Fatalf("probe while live: %v", err)
	}
	witness := f.hashTree(t)
	ws := a.kill()
	t.Logf("child %d terminated: %v", a.pid, ws)
	if err := probeLock(t, f.lockAbs); err != nil {
		t.Fatalf("the OS did not release the lock after process death: %v", err)
	}
	// Process death releases the OS lock, not the durable witness. Every later
	// holder pauses despite otherwise healthy-looking records.
	for i := 0; i < 2; i++ {
		b := startChild(t, cfg)
		b.expectRefusal(helperRequest{Op: "open-session"}, ReasonStaleActive)
		b.finish()
		sameTree(t, witness, f.hashTree(t), "a paused restart")
	}
	if _, err := OpenBootstrap(cfg); !IsRefusal(err, ReasonUnexpectedState) {
		t.Fatalf("BOOTSTRAP must not be reusable after a durable first ACTIVE: %v", err)
	}
	if len(recordFiles(f)) != 1 {
		t.Fatalf("record files = %v", recordFiles(f))
	}
}

func TestProcessDeathBeforeActiveKeepsBootstrapForLaterFirstActive(t *testing.T) {
	f := newFixture(t)
	cfg := promote(t, f)
	bootRaw := readControlRaw(t, f)
	a := startChild(t, cfg)
	a.expect(helperRequest{Op: "open-bootstrap"})
	if err := probeLock(t, f.lockAbs); err != syscall.EWOULDBLOCK {
		t.Fatalf("probe while the bootstrap holder lives: %v", err)
	}
	a.kill() // a pre-work failure: nothing was committed
	if !bytes.Equal(bootRaw, readControlRaw(t, f)) {
		t.Fatal("the verified bootstrap pair changed")
	}
	if err := probeLock(t, f.lockAbs); err != nil {
		t.Fatalf("lock not released: %v", err)
	}
	b := startChild(t, cfg)
	rb := b.expect(helperRequest{Op: "open-session"})
	if rb.Generation != 2 || rb.Predecessor != "BOOTSTRAP" {
		t.Fatalf("later first ACTIVE = %+v", rb)
	}
	b.finish()
}

func TestProcessCompetingHoldersExactlyOneWins(t *testing.T) {
	f := newFixture(t)
	cfg := promote(t, f)
	bootRaw := readControlRaw(t, f)
	const n = 6
	kids := make([]*child, n)
	for i := range kids {
		kids[i] = startChild(t, cfg)
	}
	replies := make([]helperReply, n)
	errs := make([]error, n)
	start := make(chan struct{})
	var wg sync.WaitGroup
	for i := range kids {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			<-start
			replies[i], errs[i] = kids[i].callErr(helperRequest{Op: "open-session", LockWaitMs: 600})
		}(i)
	}
	close(start)
	wg.Wait()
	winner := -1
	for i := range kids {
		if errs[i] != nil {
			t.Fatal(errs[i])
		}
		switch {
		case replies[i].OK:
			if winner >= 0 {
				t.Fatalf("two holders were admitted: %d and %d", winner, i)
			}
			winner = i
		case replies[i].Reason != string(ReasonLock):
			t.Fatalf("loser %d refused with %q, want a bounded lock refusal", i, replies[i].Reason)
		}
	}
	if winner < 0 {
		t.Fatal("no holder was admitted")
	}
	banks := controlBanksOf(t, f)
	ap, err := decodeActive(banks[1].payload)
	if err != nil || banks[1].kind != kindActive || banks[1].generation != 2 || ap.sessionID != replies[winner].Session {
		t.Fatalf("control does not show exactly the winner's ACTIVE: %v %+v", err, banks)
	}
	if !bytes.Equal(readControlRaw(t, f)[:bankUnit], bootRaw[:bankUnit]) {
		t.Fatal("the BOOTSTRAP bank changed")
	}
	for i, k := range kids {
		if i == winner {
			k.kill()
		} else {
			k.finish()
		}
	}
	t.Logf("competing holders: winner=%d of %d, losers refused with lock (%s)", winner, n, controlSummary(t, f))
}

func TestProcessSerializedHoldersDoNotInterleave(t *testing.T) {
	f := newFixture(t)
	cfg := promote(t, f)
	const n = 5
	kids := make([]*child, n)
	for i := range kids {
		kids[i] = startChild(t, cfg)
	}
	open := make([]helperReply, n)
	errs := make([]error, n)
	start := make(chan struct{})
	var wg sync.WaitGroup
	for i := range kids {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			<-start
			if open[i], errs[i] = kids[i].callErr(helperRequest{Op: "open-session", LockWaitMs: 15000}); errs[i] != nil || !open[i].OK {
				return
			}
			_, errs[i] = kids[i].callErr(helperRequest{Op: "close-orderly"})
		}(i)
	}
	close(start)
	wg.Wait()
	var gens []int
	seen := map[string]bool{}
	var slowest int64
	for i := range kids {
		if errs[i] != nil || !open[i].OK {
			t.Fatalf("holder %d: %+v %v", i, open[i], errs[i])
		}
		gens = append(gens, int(open[i].Generation))
		if seen[open[i].Session] {
			t.Fatal("a session identity was admitted twice")
		}
		seen[open[i].Session] = true
		if open[i].ElapsedMs > slowest {
			slowest = open[i].ElapsedMs
		}
	}
	sort.Ints(gens)
	for i, g := range gens {
		if g != 2+2*i {
			t.Fatalf("admitted generations %v: holders interleaved or a write was lost", gens)
		}
	}
	banks := controlBanksOf(t, f)
	if banks[0].kind != kindClean || banks[0].generation != 2*n+1 || banks[1].kind != kindActive || banks[1].generation != 2*n {
		t.Fatalf("final control %s", controlSummary(t, f))
	}
	for _, k := range kids {
		k.finish()
	}
	t.Logf("serialized holders: generations %v, slowest admission %dms, final %s", gens, slowest, controlSummary(t, f))
}

func TestProcessInitialWriteFailureLeavesOnlyTheDurableWitness(t *testing.T) {
	f := newFixture(t)
	cfg := promote(t, f)
	a := startChild(t, cfg)
	a.expect(helperRequest{Op: "open-session"})
	witness := readControlRaw(t, f)
	a.expect(helperRequest{Op: "set-faults", FailWrites: true})
	// A required initial write fails; no intent exists, and the marker write
	// that would follow fails too (an unwritable marker).
	a.expectRefusal(helperRequest{Op: "commit-record", Request: "req-1", Name: "intent", Value: "x"}, ReasonNotDurable)
	a.expectRefusal(helperRequest{Op: "close-orderly"}, ReasonFaulted)
	a.finish()
	if !bytes.Equal(witness, readControlRaw(t, f)) {
		t.Fatal("the pre-failure witness changed")
	}
	if got := recordFiles(f); len(got) != 0 {
		t.Fatalf("an intent or marker record exists: %v", got)
	}
	b := startChild(t, cfg)
	b.expectRefusal(helperRequest{Op: "open-session"}, ReasonStaleActive)
	b.finish()
}

func TestProcessCloseResidualRestartsFromTheVerifiedPair(t *testing.T) {
	f := newFixture(t)
	cfg := promote(t, f)
	a := startChild(t, cfg)
	a.expect(helperRequest{Op: "open-session"})
	a.expect(helperRequest{Op: "set-faults", FailFsync: true})
	a.expectRefusal(helperRequest{Op: "close-orderly"}, ReasonNotDurable) // closer reports locally
	a.finish()
	if banks := controlBanksOf(t, f); banks[0].kind != kindClean {
		t.Fatalf("the exact CLEAN bytes did not persist: %s", controlSummary(t, f))
	}
	b := startChild(t, cfg)
	rb := b.expect(helperRequest{Op: "open-session"})
	if rb.Predecessor != "CLEAN" || rb.Generation != 4 {
		t.Fatalf("restart over the close residual = %+v", rb)
	}
	b.finish()
}

func TestProcessRepeatedRestart(t *testing.T) {
	f := newFixture(t)
	cfg := promote(t, f)
	for cycle := 0; cycle < 3; cycle++ {
		c := startChild(t, cfg)
		r := c.expect(helperRequest{Op: "open-session"})
		if r.Generation != uint64(2+2*cycle) {
			t.Fatalf("cycle %d admitted generation %d", cycle, r.Generation)
		}
		c.expect(helperRequest{Op: "commit-record", Request: "req-1", Name: "state", Value: fmt.Sprintf("v%d", cycle)})
		c.expect(helperRequest{Op: "close-orderly"})
		c.finish()
	}
	d := startChild(t, cfg)
	if r := d.expect(helperRequest{Op: "open-session"}); r.Generation != 8 {
		t.Fatalf("generation %d", r.Generation)
	}
	d.kill() // dies holding a durable ACTIVE
	witness := f.hashTree(t)
	for i := 0; i < 3; i++ {
		e := startChild(t, cfg)
		e.expectRefusal(helperRequest{Op: "open-session"}, ReasonStaleActive)
		e.finish()
		sameTree(t, witness, f.hashTree(t), "a repeated paused restart")
	}
}

// Real-check success and refusal at the independent-process seam. Every open
// here uses the exported OpenSession in a separate process, so it binds the
// production capacity checker, not the test seam. The facility is the
// authorized local ext4 parent: this is code-behaviour evidence only, not
// supported-stack evidence, and no disk is filled.
func TestProcessRealCapacityCheckSuccessAndRefusal(t *testing.T) {
	open := helperRequest{Op: "open-session", Exported: true}

	t.Run("success, contention and restart", func(t *testing.T) {
		f := newFixture(t)
		cfg := promote(t, f)
		a := startChild(t, cfg)
		r := a.expect(open)
		if r.Generation != 2 || r.Predecessor != "BOOTSTRAP" {
			t.Fatalf("first ACTIVE after the real check = %+v", r)
		}
		// A second independent process is refused by the lease, with the real
		// check never reached and nothing written.
		witness := f.hashTree(t)
		b := startChild(t, cfg)
		b.expectRefusal(helperRequest{Op: "open-session", Exported: true, LockWaitMs: 100}, ReasonLock)
		b.finish()
		sameTree(t, witness, f.hashTree(t), "a contending real-check open")
		a.expect(helperRequest{Op: "close-orderly"})
		a.finish()
		// A new process restarts from the verified orderly-close pair through
		// the same real check, now accounting the store's own records.
		c := startChild(t, cfg)
		if r := c.expect(open); r.Generation != 4 || r.Predecessor != "CLEAN" {
			t.Fatalf("restart ACTIVE after the real check = %+v", r)
		}
		c.finish()
	})

	t.Run("managed limit refuses before ACTIVE", func(t *testing.T) {
		f := newFixture(t)
		f.cfg.Capacity.ManagedLimitBytes = 1 << 20 // below the complete threshold
		cfg := promote(t, f)
		bootRaw := readControlRaw(t, f)
		before := f.hashTree(t)
		a := startChild(t, cfg)
		a.expectRefusal(open, ReasonManagedLimit)
		a.finish()
		sameTree(t, before, f.hashTree(t), "a managed-limit refusal")
		if !bytes.Equal(bootRaw, readControlRaw(t, f)) {
			t.Fatal("control region changed by a refused open")
		}
		if err := probeLock(t, f.lockAbs); err != nil {
			t.Fatalf("the refused open left the lock held: %v", err)
		}
	})

	t.Run("changed policy refuses pending revalidation", func(t *testing.T) {
		f := newFixture(t)
		cfg := promote(t, f)
		before := f.hashTree(t)
		cfg.Capacity.PolicyRevision++
		a := startChild(t, cfg)
		a.expectRefusal(open, ReasonCapacityBinding)
		a.finish()
		sameTree(t, before, f.hashTree(t), "a changed-policy refusal")
	})
}
