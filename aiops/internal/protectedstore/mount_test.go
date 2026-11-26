//go:build linux && amd64

package protectedstore

import (
	"errors"
	"fmt"
	"os"
	"strings"
	"syscall"
	"testing"
)

func openDir(t *testing.T, path string) int {
	t.Helper()
	fd, err := syscall.Open(path, syscall.O_RDONLY|syscall.O_DIRECTORY|syscall.O_CLOEXEC, 0)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { syscall.Close(fd) })
	return fd
}

func TestMountOptionsRealExt4Positive(t *testing.T) {
	f := newFixture(t)
	report, err := checkMountOptions(procMountSource{}, openDir(t, f.root))
	if err != nil {
		t.Fatalf("real ext4 mount check: %v", err)
	}
	t.Logf("effective options: device=%s mnt_id=%d dev=%d:%d fs=%s rw=%v %s %s", report.Device, report.MountID, report.Major, report.Minor, report.Filesystem, report.ReadWrite, report.Barrier, report.DataMode)
}

func TestMountOptionsRefuseTmpfs(t *testing.T) {
	dir, err := os.MkdirTemp("/tmp", "aiops-chunk6-tmpfs-")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { os.RemoveAll(dir) })
	var sfs syscall.Statfs_t
	if err := syscall.Statfs(dir, &sfs); err != nil {
		t.Fatal(err)
	}
	if sfs.Type != tmpfsSuperMagic {
		t.Fatalf("/tmp is not tmpfs (magic %#x); the refusal case needs a tmpfs directory", sfs.Type)
	}
	_, err = checkMountOptions(procMountSource{}, openDir(t, dir))
	expectRefusal(t, err, ReasonMountOptions)
}

// Injected effective-options source (unexported, same-package tests only).
func TestMountOptionsRefuseUnsupportedUnreadableOrUnparseable(t *testing.T) {
	f := newFixture(t)
	fd := openDir(t, f.root)
	good := "rw\nbsddf\nbarrier\ndata=ordered\nuser_xattr\n"
	if _, err := checkMountOptions(optionsSource(good), fd); err != nil {
		t.Fatalf("injected supported options refused: %v", err)
	}
	cases := map[string]fakeMounts{
		"nobarrier":            optionsSource("rw\nnobarrier\ndata=ordered\n"),
		"barrier=0":            optionsSource("rw\nbarrier=0\ndata=ordered\n"),
		"data=journal":         optionsSource("rw\nbarrier\ndata=journal\n"),
		"data=writeback":       optionsSource("rw\nbarrier\ndata=writeback\n"),
		"read-only":            optionsSource("ro\nbarrier\ndata=ordered\n"),
		"unreadable":           {options: func(string) ([]byte, error) { return nil, syscall.EACCES }},
		"empty":                optionsSource(""),
		"no terminator":        optionsSource("rw\nbarrier\ndata=ordered"),
		"blank line":           optionsSource("rw\n\nbarrier\ndata=ordered\n"),
		"embedded space":       optionsSource("rw\nbarrier \ndata=ordered\n"),
		"duplicate option":     optionsSource("rw\nbarrier\nbarrier\ndata=ordered\n"),
		"conflicting barrier":  optionsSource("rw\nbarrier\nnobarrier\ndata=ordered\n"),
		"missing data mode":    optionsSource("rw\nbarrier\n"),
		"missing barrier":      optionsSource("rw\ndata=ordered\n"),
		"two data modes":       optionsSource("rw\nbarrier\ndata=ordered\ndata=journal\n"),
		"mountinfo unreadable": {info: func() ([]byte, error) { return nil, errors.New("unreadable") }},
	}
	for name, src := range cases {
		t.Run(name, func(t *testing.T) {
			_, err := checkMountOptions(src, fd)
			expectRefusal(t, err, ReasonMountOptions)
		})
	}
}

func TestMountOptionsRefuseUncorrelatedMountinfo(t *testing.T) {
	f := newFixture(t)
	fd := openDir(t, f.root)
	real, err := procMountSource{}.mountInfo()
	if err != nil {
		t.Fatal(err)
	}
	sx, err := statxFD(fd, statxMntID)
	if err != nil {
		t.Fatal(err)
	}
	id := fmt.Sprint(sx.MntID)
	var line string
	for _, l := range strings.Split(string(real), "\n") {
		if strings.HasPrefix(l, id+" ") {
			line = l
		}
	}
	if line == "" {
		t.Fatal("fixture mount not found in mountinfo")
	}
	fields := strings.Split(line, " ")
	rewrite := func(mutate func(fields []string) []string) fakeMounts {
		cp := append([]string(nil), fields...)
		return fakeMounts{info: func() ([]byte, error) { return []byte(strings.Join(mutate(cp), " ") + "\n"), nil }}
	}
	sep := 0
	for i, v := range fields {
		if v == "-" && i >= 6 {
			sep = i
			break
		}
	}
	cases := map[string]fakeMounts{
		"mount missing":        {info: func() ([]byte, error) { return []byte("1 0 0:1 / / rw - proc proc rw\n"), nil }},
		"device mismatch":      rewrite(func(f []string) []string { f[2] = "999:999"; return f }),
		"filesystem not ext4":  rewrite(func(f []string) []string { f[sep+1] = "xfs"; return f }),
		"source not a device":  rewrite(func(f []string) []string { f[sep+2] = "UUID=abc"; return f }),
		"source nested path":   rewrite(func(f []string) []string { f[sep+2] = "/dev/mapper/vg-lv"; return f }),
		"mount read-only":      rewrite(func(f []string) []string { f[5] = "ro,relatime"; return f }),
		"superblock read-only": rewrite(func(f []string) []string { f[sep+3] = "ro"; return f }),
		"unparseable line":     {info: func() ([]byte, error) { return []byte(id + " garbage\n"), nil }},
		"duplicate identity": {info: func() ([]byte, error) {
			return []byte(line + "\n" + line + "\n"), nil
		}},
	}
	for name, src := range cases {
		t.Run(name, func(t *testing.T) {
			_, err := checkMountOptions(src, fd)
			expectRefusal(t, err, ReasonMountOptions)
		})
	}
}

func TestInitializeAndBootstrapRefuseUnsupportedOptions(t *testing.T) {
	f := newFixture(t)
	_, err := initialize(f.cfg, optionsSource("rw\nbarrier\ndata=journal\n"), nil)
	expectRefusal(t, err, ReasonMountOptions)
	if got := f.nsEntries(t); len(got) != 0 {
		t.Fatalf("refused initialization created state: %v", got)
	}
	res := f.initialize(t)
	_, err = openBootstrap(f.existing(promotionFrom(res)), optionsSource("rw\nnobarrier\ndata=ordered\n"), nil)
	expectRefusal(t, err, ReasonMountOptions)
}

func TestBeforeAdmissionHookRepeatsMountOptionCheck(t *testing.T) {
	f := newFixture(t)
	res := f.initialize(t)
	b, err := openBootstrap(f.existing(promotionFrom(res)), procMountSource{}, nil)
	if err != nil {
		t.Fatal(err)
	}
	defer b.Close()
	if err := b.CheckBeforeAdmission(); err != nil {
		t.Fatal(err)
	}
	b.h.mounts = optionsSource("rw\nbarrier=0\ndata=ordered\n")
	expectRefusal(t, b.CheckBeforeAdmission(), ReasonMountOptions)
}

func TestBeforeAdmissionHookDetectsReplacedEntries(t *testing.T) {
	f := newFixture(t)
	res := f.initialize(t)
	b, err := OpenBootstrap(f.existing(promotionFrom(res)))
	if err != nil {
		t.Fatal(err)
	}
	defer b.Close()
	if err := os.Rename(f.nsPath, f.nsPath+"-moved"); err != nil {
		t.Fatal(err)
	}
	if err := os.Mkdir(f.nsPath, 0o700); err != nil {
		t.Fatal(err)
	}
	if err := b.CheckBeforeAdmission(); err == nil {
		t.Fatal("replaced namespace entry not detected")
	}
}
