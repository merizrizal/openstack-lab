//go:build linux && amd64

package protectedstore

import (
	"bytes"
	"fmt"
	"os"
	"syscall"
	"unsafe"
)

// poisonByte fills every direct-read buffer before the read. A valid bank
// begins with bankMagic, which contains no poison byte, so a read that leaves
// the buffer unchanged cannot match any expected bank encoding.
const poisonByte = 0xA5

// VerifyReport records the observed direct-I/O facts of one Verified call.
type VerifyReport struct {
	DioMemAlign    uint32
	DioOffsetAlign uint32
	BankUnit       uint32
	Bytes          int
	Mount          MountReport
}

type verifyTarget struct {
	dirFD    int
	name     string
	fd       int
	expected []byte
}

func (h *holder) statxDio(fd int) (statxT, error) {
	if h.hooks != nil && h.hooks.statxDio != nil {
		return h.hooks.statxDio(fd)
	}
	return statxFD(fd, statxBasicStats|statxDioAlign)
}

func (h *holder) directFlags(fd int) (int, error) {
	if h.hooks != nil && h.hooks.directFlags != nil {
		return h.hooks.directFlags(fd)
	}
	return fcntlGetFlags(fd)
}

func (h *holder) allocBuffer(n int) ([]byte, func(), error) {
	if h.hooks != nil && h.hooks.allocBuffer != nil {
		return h.hooks.allocBuffer(n)
	}
	return allocDirectBuffer(n)
}

func (h *holder) directRead(fd int, p []byte, off int64) (int, error) {
	if h.hooks != nil && h.hooks.directRead != nil {
		return h.hooks.directRead(fd, p, off)
	}
	for {
		n, err := syscall.Pread(fd, p, off)
		if err != syscall.EINTR {
			return n, err
		}
	}
}

// allocDirectBuffer returns a fresh anonymous page-aligned mapping excluded
// from fork with MADV_DONTFORK (manual §5.3.5 fork exclusion).
func allocDirectBuffer(n int) ([]byte, func(), error) {
	buf, err := syscall.Mmap(-1, 0, n, syscall.PROT_READ|syscall.PROT_WRITE, syscall.MAP_PRIVATE|syscall.MAP_ANON)
	if err != nil {
		return nil, nil, err
	}
	if err := syscall.Madvise(buf, syscall.MADV_DONTFORK); err != nil {
		syscall.Munmap(buf)
		return nil, nil, err
	}
	return buf, func() { syscall.Munmap(buf) }, nil
}

// verified implements manual §5.3.3 rule 2 for one region file. The caller
// holds h.mu, so no other operation of this holder runs concurrently. It
// performs its own file and directory barrier, repeats the mount-option check,
// confirms STATX_DIOALIGN support and alignment, rereads every byte through
// O_DIRECT into a poisoned aligned buffer and compares the device bytes with
// the expected bytes and with an ordinary read. Every failure refuses; there
// is no buffered fallback.
func (h *holder) verified(t verifyTarget) (VerifyReport, error) {
	report := VerifyReport{BankUnit: bankUnit, Bytes: len(t.expected)}
	if len(t.expected) == 0 || len(t.expected)%bankUnit != 0 {
		return report, refuse(ReasonVerifyUnsupported, "expected bytes are not whole banks", nil)
	}
	if err := h.fsync(t.fd, "file"); err != nil {
		return report, refuse(ReasonVerifyUnsupported, "own file barrier failed", err)
	}
	if err := h.fsync(t.dirFD, "dir"); err != nil {
		return report, refuse(ReasonVerifyUnsupported, "own directory barrier failed", err)
	}
	if err := h.checkMounts(); err != nil {
		return report, err
	}
	report.Mount = h.lastMount
	fileID, fst, err := identityOf(t.fd)
	if err != nil {
		return report, refuse(ReasonVerifyUnsupported, "file identity unavailable", err)
	}
	if fileID.dev != h.cfg.NamespaceDevice {
		return report, refuse(ReasonVerifyUnsupported, "file is not on the bound store device", nil)
	}
	if fst.Size != int64(len(t.expected)) {
		return report, refuse(ReasonVerifyMismatch, "file size differs from the expected banks", nil)
	}

	sx, err := h.statxDio(t.fd)
	if err != nil {
		return report, refuse(ReasonVerifyUnsupported, "statx STATX_DIOALIGN unavailable", err)
	}
	if sx.Mask&statxDioAlign == 0 {
		return report, refuse(ReasonVerifyUnsupported, "STATX_DIOALIGN not reported", nil)
	}
	report.DioMemAlign, report.DioOffsetAlign = sx.DioMemAlign, sx.DioOffsetAlign
	mem, off := uint64(sx.DioMemAlign), uint64(sx.DioOffsetAlign)
	if mem == 0 || off == 0 {
		return report, refuse(ReasonVerifyUnsupported, "direct I/O unsupported (alignment 0)", nil)
	}
	if mem&(mem-1) != 0 || off&(off-1) != 0 || bankUnit%off != 0 || uint64(len(t.expected))%off != 0 || mem > uint64(os.Getpagesize()) {
		return report, refuse(ReasonVerifyUnsupported, fmt.Sprintf("direct I/O alignment unsupported (mem %d, offset %d)", mem, off), nil)
	}
	if _, err := checkBankAlignment(t.fd); err != nil {
		return report, err
	}

	dfd, err := openat2(t.dirFD, t.name, syscall.O_RDONLY|syscall.O_DIRECT|syscall.O_NOFOLLOW, 0)
	if err != nil {
		return report, refuse(ReasonVerifyUnsupported, "direct open failed", err)
	}
	defer syscall.Close(dfd)
	dID, _, err := identityOf(dfd)
	if err != nil || dID != fileID {
		return report, refuse(ReasonVerifyUnsupported, "direct descriptor does not match the verified file", err)
	}
	flags, err := h.directFlags(dfd)
	if err != nil || flags&syscall.O_DIRECT == 0 {
		return report, refuse(ReasonVerifyUnsupported, "direct I/O flag not in effect (buffered fallback)", err)
	}

	buf, release, err := h.allocBuffer(len(t.expected))
	if err != nil {
		return report, refuse(ReasonVerifyUnsupported, "direct buffer allocation failed", err)
	}
	defer release()
	if len(buf) != len(t.expected) || uint64(uintptr(unsafe.Pointer(&buf[0])))%mem != 0 {
		return report, refuse(ReasonVerifyUnsupported, "direct buffer misaligned", nil)
	}
	for i := range buf {
		buf[i] = poisonByte
	}
	done := 0
	for done < len(buf) {
		n, err := h.directRead(dfd, buf[done:], int64(done))
		if err != nil {
			return report, refuse(ReasonVerifyUnsupported, "direct reread failed", err)
		}
		if n <= 0 || uint64(n)%off != 0 || n > len(buf)-done {
			return report, refuse(ReasonVerifyUnsupported, "direct reread was short or misaligned", nil)
		}
		done += n
	}

	ordinary := make([]byte, len(t.expected))
	if err := readFull(t.fd, ordinary, 0); err != nil {
		return report, refuse(ReasonVerifyUnsupported, "ordinary reread failed", err)
	}

	if !bytes.Equal(buf, ordinary) {
		detail := "device bytes differ from the page-cache bytes"
		if bytes.Equal(ordinary, t.expected) {
			detail += " (cache shows the expected bytes; device does not)"
		}
		return report, refuse(ReasonCacheDeviceDiscrepancy, detail, nil)
	}
	if !bytes.Equal(buf, t.expected) {
		return report, refuse(ReasonVerifyMismatch, "device bytes differ from the expected banks", nil)
	}
	return report, nil
}
