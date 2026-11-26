//go:build linux && amd64 && aiops_enospc

package protectedstore

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"testing"
)

// Real filesystem and inode exhaustion (ENOSPC) on a supplied bounded
// filesystem. This file is compiled only with -tags aiops_enospc so the default
// suite neither runs it nor reports a green skip for it: without the tag the
// element is NOT_RUN, and with the tag a missing or unsuitable facility FAILS.
//
//	AIOPS_ENOSPC_DIR        mount point of the bounded filesystem (also TMPDIR)
//	AIOPS_ENOSPC_MAX_BYTES  upper bound on that filesystem's total size
//
// The test refuses to run unless the directory is the root of its own ext4
// mount, separate from "/" and from its parent, no larger than the stated
// bound, and unless TMPDIR is that directory. It runs as a non-root user, fills
// only that filesystem, and every object it creates is under t.TempDir() there.
// These are real kernel ENOSPC results; they are code-behaviour evidence on the
// named facility, not supported-stack evidence.

const (
	enospcDirEnv = "AIOPS_ENOSPC_DIR"
	enospcMaxEnv = "AIOPS_ENOSPC_MAX_BYTES"
)

func requireBoundedFixture(t *testing.T) syscall.Statfs_t {
	t.Helper()
	dir, maxS := os.Getenv(enospcDirEnv), os.Getenv(enospcMaxEnv)
	if dir == "" || maxS == "" {
		t.Fatalf("real ENOSPC needs %s and %s; the facility is missing (this is never a skip)", enospcDirEnv, enospcMaxEnv)
	}
	maxBytes, err := strconv.ParseUint(maxS, 10, 64)
	if err != nil || maxBytes == 0 {
		t.Fatalf("%s is not a positive byte count: %q", enospcMaxEnv, maxS)
	}
	if os.Getuid() == 0 {
		t.Fatal("real ENOSPC must run as a non-root user")
	}
	if !filepath.IsAbs(dir) || filepath.Clean(dir) != dir || filepath.Clean(os.TempDir()) != dir {
		t.Fatalf("%s must be a clean absolute path and equal TMPDIR (TMPDIR=%q)", enospcDirEnv, os.TempDir())
	}
	var sfs syscall.Statfs_t
	if err := syscall.Statfs(dir, &sfs); err != nil {
		t.Fatal(err)
	}
	total := sfs.Blocks * uint64(sfs.Bsize)
	if sfs.Type != ext4SuperMagic || total == 0 || total > maxBytes {
		t.Fatalf("%s is not an ext4 filesystem within %d bytes (magic %#x, total %d)", dir, maxBytes, sfs.Type, total)
	}
	var st, root, parent syscall.Stat_t
	for _, s := range []struct {
		path string
		out  *syscall.Stat_t
	}{{dir, &st}, {"/", &root}, {filepath.Dir(dir), &parent}} {
		if err := syscall.Stat(s.path, s.out); err != nil {
			t.Fatal(err)
		}
	}
	if st.Dev == root.Dev || st.Dev == parent.Dev {
		t.Fatalf("%s is not the root of its own mount, separate from / and its parent", dir)
	}
	info, err := procMountSource{}.mountInfo()
	if err != nil {
		t.Fatal(err)
	}
	isMount := false
	for _, line := range strings.Split(string(info), "\n") {
		if fields := strings.Fields(line); len(fields) > 4 && fields[4] == dir {
			isMount = true
		}
	}
	if !isMount {
		t.Fatalf("%s is not a mount point in /proc/self/mountinfo", dir)
	}
	return sfs
}

func logCapacity(t *testing.T, label, path string) syscall.Statfs_t {
	t.Helper()
	var s syscall.Statfs_t
	if err := syscall.Statfs(path, &s); err != nil {
		t.Fatal(err)
	}
	bs := uint64(s.Bsize)
	t.Logf("REAL capacity %-22s total=%d free=%d avail(unprivileged)=%d bytes; inodes total=%d free=%d",
		label, s.Blocks*bs, s.Bfree*bs, s.Bavail*bs, s.Files, s.Ffree)
	return s
}

// fillBytes writes to path until the kernel reports ENOSPC on a write, first in
// large chunks and then block by block, and returns the bytes written.
func fillBytes(t *testing.T, path string, limit uint64) uint64 {
	t.Helper()
	f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0o600)
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()
	var written uint64
	for _, chunk := range []int{1 << 20, 4096} {
		buf := make([]byte, chunk)
		for i := range buf {
			buf[i] = 0xA5
		}
		for {
			if written > limit {
				t.Fatalf("no ENOSPC after %d bytes, more than the filesystem holds", written)
			}
			n, err := f.Write(buf)
			written += uint64(n)
			if err == nil {
				continue
			}
			if !errors.Is(err, syscall.ENOSPC) {
				t.Fatalf("filling failed with %v, not ENOSPC", err)
			}
			break
		}
	}
	if err := f.Sync(); err != nil && !errors.Is(err, syscall.ENOSPC) {
		t.Fatalf("fill sync: %v", err)
	}
	t.Logf("REAL ENOSPC observed while writing the unmanaged fill file after %d bytes", written)
	return written
}

// fillInodes creates empty files until the kernel reports ENOSPC on create.
func fillInodes(t *testing.T, dir string, limit uint64) int {
	t.Helper()
	if err := os.Mkdir(dir, 0o700); err != nil {
		t.Fatal(err)
	}
	for i := uint64(0); i <= limit; i++ {
		f, err := os.OpenFile(filepath.Join(dir, fmt.Sprintf("i%06d", i)), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0o600)
		if err != nil {
			if errors.Is(err, syscall.ENOSPC) {
				t.Logf("REAL ENOSPC observed creating file number %d (inode exhaustion)", i)
				return int(i)
			}
			t.Fatalf("inode fill failed with %v, not ENOSPC", err)
		}
		f.Close()
	}
	t.Fatalf("no ENOSPC after %d files, more inodes than the filesystem reports", limit)
	return 0
}

type exhaustion struct {
	name string
	// fill exhausts the resource under root and returns a function that frees it.
	fill func(t *testing.T, root string, sfs syscall.Statfs_t) (free func())
	// exhausted reports whether the unprivileged-available resource is below need.
	exhausted func(s syscall.Statfs_t, need capacityNeed) bool
	// plentiful reports that the other resource is not what ran out.
	plentiful func(s syscall.Statfs_t, need capacityNeed) bool
	detail    string
}

func exhaustions() []exhaustion {
	return []exhaustion{
		{
			name: "bytes",
			fill: func(t *testing.T, root string, sfs syscall.Statfs_t) func() {
				path := filepath.Join(root, "unmanaged-fill.bin")
				fillBytes(t, path, sfs.Blocks*uint64(sfs.Bsize))
				return func() { os.Remove(path) }
			},
			exhausted: func(s syscall.Statfs_t, n capacityNeed) bool { return s.Bavail*uint64(s.Bsize) < n.bytes },
			plentiful: func(s syscall.Statfs_t, n capacityNeed) bool { return s.Ffree >= n.inodes },
			detail:    "bytes",
		},
		{
			name: "inodes",
			fill: func(t *testing.T, root string, sfs syscall.Statfs_t) func() {
				dir := filepath.Join(root, "unmanaged-inode-fill")
				fillInodes(t, dir, sfs.Files)
				return func() { os.RemoveAll(dir) }
			},
			exhausted: func(s syscall.Statfs_t, n capacityNeed) bool { return s.Ffree < n.inodes },
			plentiful: func(s syscall.Statfs_t, n capacityNeed) bool { return s.Bavail*uint64(s.Bsize) >= n.bytes },
			detail:    "inodes",
		},
	}
}

// The real startup capacity check refuses on genuinely exhausted bytes or
// inodes, before ACTIVE and without writing anything, with a filesystem outcome
// that is distinct from managed-limit exhaustion; freeing the space is an
// ordinary reading change, not an identity change.
func TestRealENOSPCRefusesTheStartupCapacityCheck(t *testing.T) {
	sfs := requireBoundedFixture(t)
	need := mustNeed(t, reviewedLayout())
	for _, ex := range exhaustions() {
		t.Run(ex.name, func(t *testing.T) {
			f := newFixture(t)
			cfg := promote(t, f)
			logCapacity(t, "before fill", f.root)
			bootRaw := readControlRaw(t, f)
			before := f.hashTree(t)

			free := ex.fill(t, f.root, sfs)
			defer free()
			after := logCapacity(t, "exhausted", f.root)
			if !ex.exhausted(after, need) || !ex.plentiful(after, need) {
				t.Fatalf("the %s fill did not leave exactly that resource exhausted: %+v", ex.name, after)
			}

			s, err := openSession(cfg, procMountSource{}, productionCapacity(), nil)
			if s != nil {
				s.Release()
				t.Fatal("ACTIVE was established on an exhausted filesystem")
			}
			expectRefusal(t, err, ReasonFilesystemExhausted)
			if IsRefusal(err, ReasonManagedLimit) || failureKindOf(err) != failureFilesystem {
				t.Fatalf("filesystem exhaustion reported as %q: %v", failureKindOf(err), err)
			}
			if !strings.Contains(err.Error(), ex.detail) {
				t.Fatalf("the refusal does not name the exhausted resource (%s): %v", ex.detail, err)
			}
			if string(bootRaw) != string(readControlRaw(t, f)) {
				t.Fatal("the control region changed")
			}
			sameTree(t, before, f.hashTree(t), "a real-ENOSPC capacity refusal")

			free()
			logCapacity(t, "after freeing", f.root)
			s, err = openSession(cfg, procMountSource{}, productionCapacity(), nil)
			if err != nil {
				t.Fatalf("freeing space is a reading change; the real check must pass again: %v", err)
			}
			s.Release()
		})
	}
}

// After the real check passed, a required write that hits real ENOSPC stays
// fail-closed and is reported as filesystem exhaustion, not as managed-limit
// exhaustion and not as a generic device error: the holder is faulted, no CLEAN
// is written, the durable ACTIVE witness stays, and a later holder pauses.
func TestRealENOSPCOnARequiredWriteStaysFailClosed(t *testing.T) {
	sfs := requireBoundedFixture(t)
	need := mustNeed(t, reviewedLayout())
	for _, ex := range exhaustions() {
		t.Run(ex.name, func(t *testing.T) {
			f := newFixture(t)
			cfg := promote(t, f)
			bs := blockSizeOf(t, f.nsPath)

			s, err := openSession(cfg, procMountSource{}, productionCapacity(), nil)
			if err != nil {
				t.Fatalf("the real check must pass with ample space: %v", err)
			}
			logCapacity(t, "ACTIVE, before fill", f.root)

			free := ex.fill(t, f.root, sfs)
			defer free()
			after := logCapacity(t, "exhausted", f.root)
			if !ex.exhausted(after, need) {
				t.Fatalf("the fill did not exhaust %s: %+v", ex.name, after)
			}
			// Managed headroom is untouched: this is not managed exhaustion.
			s.h.mu.Lock()
			u, uerr := s.h.accountManaged(reviewedLayout(), bs)
			s.h.mu.Unlock()
			if uerr != nil {
				t.Fatal(uerr)
			}
			if limit := cfg.Capacity.ManagedLimitBytes; u.bytes > limit || limit-u.bytes < need.bytes {
				t.Fatalf("managed headroom is not intact (usage %d, limit %d)", u.bytes, limit)
			}

			_, err = s.commitRecord(testKey(f, "req-1", "intent"), []byte("not-saved"))
			if err == nil {
				t.Fatal("a required write reported success on an exhausted filesystem")
			}
			expectRefusal(t, err, ReasonNotDurable)
			if !errors.Is(err, syscall.ENOSPC) {
				t.Fatalf("the write failed with %v, not the kernel's real ENOSPC", err)
			}
			if got := failureKindOf(err); got != failureFilesystem || !strings.Contains(err.Error(), "ENOSPC") {
				t.Fatalf("real ENOSPC classified %q: %v", got, err)
			}
			if IsRefusal(err, ReasonManagedLimit) {
				t.Fatal("real ENOSPC reported as managed-limit exhaustion")
			}
			t.Logf("REAL write failure after a passing check: %v", err)

			// Fail closed: the holder is faulted, so no later write and no CLEAN.
			_, err = s.commitRecord(testKey(f, "req-2", "intent"), []byte("after-fault"))
			expectRefusal(t, err, ReasonFaulted)
			if err := s.CloseOrderly(); err == nil {
				t.Fatal("an orderly close was reported after a write fault")
			}
			for _, b := range controlBanksOf(t, f) {
				if b.kind == kindClean {
					t.Fatal("a CLEAN certificate was written over the fault")
				}
			}
			free()
			expectPaused(t, f, cfg, nil, ReasonStaleActive, "")
		})
	}
}
