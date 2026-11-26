//go:build linux && amd64

package protectedstore

import (
	"syscall"
	"unsafe"
)

// Raw Linux system call numbers for x86-64 that the standard library syscall
// package does not name. Only the standard library is used; no new dependency.
const (
	sysRenameat2 = 316
	sysStatx     = 332
	sysOpenat2   = 437
	// sysQuotactlFd is quotactl_fd (Linux 5.14+). It takes a descriptor on the
	// store's filesystem, so no device node path is needed; the capacity check
	// uses only the read-only Q_GETFMT and Q_GETQUOTA commands.
	sysQuotactlFd = 443
)

const (
	qGetFmt   = 0x800004
	qGetQuota = 0x800007
)

const (
	resolveNoMagiclinks = 0x02
	resolveNoSymlinks   = 0x04
	resolveBeneath      = 0x08
	// Every handle-relative traversal uses all three resolve restrictions.
	resolveFlags = resolveBeneath | resolveNoSymlinks | resolveNoMagiclinks

	statxBasicStats = 0x000007ff
	statxMntID      = 0x00001000
	statxDioAlign   = 0x00002000
	atEmptyPath     = 0x1000

	renameNoReplace = 0x1

	ext4SuperMagic  = 0xEF53
	tmpfsSuperMagic = 0x01021994
)

type openHow struct {
	Flags   uint64
	Mode    uint64
	Resolve uint64
}

type statxTimestamp struct {
	Sec  int64
	Nsec uint32
	_    int32
}

// statxT mirrors struct statx from include/uapi/linux/stat.h (256 bytes).
type statxT struct {
	Mask           uint32
	Blksize        uint32
	Attributes     uint64
	Nlink          uint32
	UID            uint32
	GID            uint32
	Mode           uint16
	_              uint16
	Ino            uint64
	Size           uint64
	Blocks         uint64
	AttributesMask uint64
	Atime          statxTimestamp
	Btime          statxTimestamp
	Ctime          statxTimestamp
	Mtime          statxTimestamp
	RdevMajor      uint32
	RdevMinor      uint32
	DevMajor       uint32
	DevMinor       uint32
	MntID          uint64
	DioMemAlign    uint32
	DioOffsetAlign uint32
	_              [12]uint64
}

var emptyPath = [1]byte{0}

// openat2 opens path beneath dirfd with RESOLVE_BENEATH, RESOLVE_NO_SYMLINKS
// and RESOLVE_NO_MAGICLINKS. Callers also pass O_NOFOLLOW. There is no
// fallback: when openat2 is unavailable the call fails and the caller refuses.
func openat2(dirfd int, path string, flags int, mode uint32) (int, error) {
	p, err := syscall.BytePtrFromString(path)
	if err != nil {
		return -1, err
	}
	how := openHow{Flags: uint64(flags | syscall.O_CLOEXEC), Mode: uint64(mode), Resolve: resolveFlags}
	for {
		r, _, errno := syscall.Syscall6(sysOpenat2, uintptr(dirfd), uintptr(unsafe.Pointer(p)), uintptr(unsafe.Pointer(&how)), unsafe.Sizeof(how), 0, 0)
		if errno == syscall.EINTR {
			continue
		}
		if errno != 0 {
			return -1, errno
		}
		return int(r), nil
	}
}

func statxFD(fd int, mask uint32) (statxT, error) {
	var st statxT
	for {
		_, _, errno := syscall.Syscall6(sysStatx, uintptr(fd), uintptr(unsafe.Pointer(&emptyPath[0])), atEmptyPath, uintptr(mask), uintptr(unsafe.Pointer(&st)), 0)
		if errno == syscall.EINTR {
			continue
		}
		if errno != 0 {
			return statxT{}, errno
		}
		return st, nil
	}
}

// qcmd encodes a quota command and type as QCMD does in the quota ABI.
func qcmd(cmd, qtype int) uint32 {
	return uint32(cmd)<<8 | uint32(qtype)&0xff
}

// quotactlFD issues a read-only quota query on the filesystem holding fd.
func quotactlFD(fd int, cmd uint32, id uint32, addr unsafe.Pointer) error {
	for {
		_, _, errno := syscall.Syscall6(sysQuotactlFd, uintptr(fd), uintptr(cmd), uintptr(id), uintptr(addr), 0, 0)
		if errno == syscall.EINTR {
			continue
		}
		if errno != 0 {
			return errno
		}
		return nil
	}
}

func renameat2NoReplace(olddirfd int, oldpath string, newdirfd int, newpath string) error {
	oldp, err := syscall.BytePtrFromString(oldpath)
	if err != nil {
		return err
	}
	newp, err := syscall.BytePtrFromString(newpath)
	if err != nil {
		return err
	}
	_, _, errno := syscall.Syscall6(sysRenameat2, uintptr(olddirfd), uintptr(unsafe.Pointer(oldp)), uintptr(newdirfd), uintptr(unsafe.Pointer(newp)), renameNoReplace, 0)
	if errno != 0 {
		return errno
	}
	return nil
}

// hasACL reports whether an access or default POSIX ACL is attached to fd.
func hasACL(fd int) (bool, error) {
	for _, name := range []string{"system.posix_acl_access", "system.posix_acl_default"} {
		p, err := syscall.BytePtrFromString(name)
		if err != nil {
			return false, err
		}
		_, _, errno := syscall.Syscall6(syscall.SYS_FGETXATTR, uintptr(fd), uintptr(unsafe.Pointer(p)), 0, 0, 0, 0)
		switch errno {
		case 0:
			return true, nil
		case syscall.ENODATA, syscall.EOPNOTSUPP:
			continue
		default:
			return false, errno
		}
	}
	return false, nil
}

func fcntlGetFlags(fd int) (int, error) {
	r, _, errno := syscall.Syscall(syscall.SYS_FCNTL, uintptr(fd), syscall.F_GETFL, 0)
	if errno != 0 {
		return 0, errno
	}
	return int(r), nil
}

func devMajor(dev uint64) uint32 {
	return uint32(((dev >> 8) & 0xfff) | ((dev >> 32) &^ 0xfff))
}

func devMinor(dev uint64) uint32 {
	return uint32((dev & 0xff) | ((dev >> 12) &^ 0xff))
}
