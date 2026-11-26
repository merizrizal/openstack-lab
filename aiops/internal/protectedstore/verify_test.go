//go:build linux && amd64

package protectedstore

import (
	"bytes"
	"os"
	"syscall"
	"testing"
	"unsafe"
)

func controlTarget(h *holder) verifyTarget {
	return verifyTarget{dirFD: h.nsFD, name: controlName, fd: h.controlFD, expected: append([]byte(nil), h.controlRaw...)}
}

func runVerified(h *holder, t verifyTarget) (VerifyReport, error) {
	h.mu.Lock()
	defer h.mu.Unlock()
	return h.verified(t)
}

// Positive case on the real ext4 fixture: own barrier, mount check,
// STATX_DIOALIGN-confirmed O_DIRECT reread and comparison all succeed.
func TestVerifiedRealExt4Positive(t *testing.T) {
	f := newFixture(t)
	f.initialize(t)
	h := f.openState(t, nil)
	report, err := runVerified(h, controlTarget(h))
	if err != nil {
		t.Fatalf("Verified on real ext4: %v", err)
	}
	t.Logf("STATX_DIOALIGN observed: stx_dio_mem_align=%d stx_dio_offset_align=%d; bank_unit=%d bytes=%d; mount %s %s %s",
		report.DioMemAlign, report.DioOffsetAlign, report.BankUnit, report.Bytes, report.Mount.Device, report.Mount.Barrier, report.Mount.DataMode)
	if report.DioMemAlign == 0 || report.DioOffsetAlign == 0 {
		t.Fatal("positive verification without direct-I/O support")
	}
}

func TestVerifiedRefusesUnsupportedOrMisalignedDirectIO(t *testing.T) {
	cases := map[string]func(st *statxT){
		"mem align 0":                  func(st *statxT) { st.DioMemAlign = 0 },
		"offset align 0":               func(st *statxT) { st.DioOffsetAlign = 0 },
		"STATX_DIOALIGN not reported":  func(st *statxT) { st.Mask &^= statxDioAlign },
		"offset align not power of 2":  func(st *statxT) { st.DioOffsetAlign = 3 },
		"offset align beyond bank":     func(st *statxT) { st.DioOffsetAlign = 2 * bankUnit },
		"mem align beyond page buffer": func(st *statxT) { st.DioMemAlign = uint32(4 * os.Getpagesize()) },
	}
	for name, mutate := range cases {
		t.Run(name, func(t *testing.T) {
			f := newFixture(t)
			f.initialize(t)
			h := f.openState(t, &faultHooks{statxDio: func(fd int) (statxT, error) {
				st, err := statxFD(fd, statxBasicStats|statxDioAlign)
				mutate(&st)
				return st, err
			}})
			_, err := runVerified(h, controlTarget(h))
			expectRefusal(t, err, ReasonVerifyUnsupported)
		})
	}
}

func TestVerifiedRefusesBufferedFallback(t *testing.T) {
	f := newFixture(t)
	f.initialize(t)
	h := f.openState(t, &faultHooks{directFlags: func(fd int) (int, error) {
		flags, err := fcntlGetFlags(fd)
		return flags &^ syscall.O_DIRECT, err
	}})
	_, err := runVerified(h, controlTarget(h))
	expectRefusal(t, err, ReasonVerifyUnsupported)
}

func TestVerifiedRefusesMismatchWithExpectedBytes(t *testing.T) {
	f := newFixture(t)
	f.initialize(t)
	h := f.openState(t, nil)
	target := controlTarget(h)
	target.expected[bankHeaderSize] ^= 0x01
	_, err := runVerified(h, target)
	expectRefusal(t, err, ReasonVerifyMismatch)
}

// Injected fault seam (not evidence of A2): the device read returns bytes
// that differ from the page cache, as after a failed writeback.
func TestVerifiedReportsCacheDeviceDiscrepancy(t *testing.T) {
	f := newFixture(t)
	f.initialize(t)
	h := f.openState(t, &faultHooks{directRead: func(fd int, p []byte, off int64) (int, error) {
		n, err := syscall.Pread(fd, p, off)
		if n > 0 {
			p[0] ^= 0xff
		}
		return n, err
	}})
	_, err := runVerified(h, controlTarget(h))
	expectRefusal(t, err, ReasonCacheDeviceDiscrepancy)
}

// A reread whose buffer already holds the expected bytes but receives no
// device data must not verify: the buffer is poisoned before every read.
func TestVerifiedStaleMatchBufferDoesNotVerify(t *testing.T) {
	f := newFixture(t)
	f.initialize(t)
	var expected []byte
	sawPoison := false
	h := f.openState(t, &faultHooks{
		allocBuffer: func(n int) ([]byte, func(), error) {
			buf, release, err := allocDirectBuffer(n)
			if err != nil {
				return nil, nil, err
			}
			copy(buf, expected) // simulate reused memory holding the expected bytes
			return buf, release, nil
		},
		directRead: func(fd int, p []byte, off int64) (int, error) {
			sawPoison = bytes.Count(p, []byte{poisonByte}) == len(p)
			return len(p), nil // reports success but delivers no device data
		},
	})
	target := controlTarget(h)
	expected = target.expected
	_, err := runVerified(h, target)
	if err == nil {
		t.Fatal("stale-match buffer verified")
	}
	if !IsRefusal(err, ReasonCacheDeviceDiscrepancy) && !IsRefusal(err, ReasonVerifyMismatch) {
		t.Fatalf("unexpected refusal: %v", err)
	}
	if !sawPoison {
		t.Fatal("direct-read buffer was not poisoned before the read")
	}
}

func TestVerifiedRefusesShortOrMisalignedDirectRead(t *testing.T) {
	for name, read := range map[string]func(int, []byte, int64) (int, error){
		"zero-length read": func(int, []byte, int64) (int, error) { return 0, nil },
		"misaligned read":  func(fd int, p []byte, off int64) (int, error) { return syscall.Pread(fd, p[:1], off) },
		"read error":       func(int, []byte, int64) (int, error) { return 0, syscall.EIO },
	} {
		t.Run(name, func(t *testing.T) {
			f := newFixture(t)
			f.initialize(t)
			h := f.openState(t, &faultHooks{directRead: read})
			_, err := runVerified(h, controlTarget(h))
			expectRefusal(t, err, ReasonVerifyUnsupported)
		})
	}
}

func TestVerifiedRefusesWhenOwnBarrierFails(t *testing.T) {
	for _, kind := range []string{"file", "dir"} {
		t.Run(kind, func(t *testing.T) {
			f := newFixture(t)
			f.initialize(t)
			h := f.openState(t, &faultHooks{fsync: func(fd int, k string) error {
				if k == kind {
					return syscall.EIO
				}
				return syscall.Fsync(fd)
			}})
			_, err := runVerified(h, controlTarget(h))
			expectRefusal(t, err, ReasonVerifyUnsupported)
		})
	}
}

func TestVerifiedRepeatsMountOptionCheck(t *testing.T) {
	f := newFixture(t)
	f.initialize(t)
	h := f.openState(t, nil)
	h.mounts = optionsSource("rw\nnobarrier\ndata=ordered\n")
	_, err := runVerified(h, controlTarget(h))
	expectRefusal(t, err, ReasonMountOptions)
}

func TestDirectBufferIsAlignedFreshMapping(t *testing.T) {
	buf, release, err := allocDirectBuffer(regionFileSize)
	if err != nil {
		t.Fatalf("allocDirectBuffer (mmap + MADV_DONTFORK): %v", err)
	}
	defer release()
	if len(buf) != regionFileSize {
		t.Fatalf("buffer length %d", len(buf))
	}
	if uintptr(unsafe.Pointer(&buf[0]))%uintptr(os.Getpagesize()) != 0 {
		t.Fatal("buffer is not page aligned")
	}
	if !allZero(buf) {
		t.Fatal("fresh anonymous mapping is not zero-filled")
	}
	if bytes.Contains([]byte{bankMagic[0], bankMagic[1]}, []byte{poisonByte}) || bytes.IndexByte(bankMagic[:], poisonByte) >= 0 {
		t.Fatal("poison byte appears in the bank magic")
	}
}
