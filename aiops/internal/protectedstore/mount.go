//go:build linux && amd64

package protectedstore

import (
	"bytes"
	"fmt"
	"regexp"
	"strconv"
	"strings"
	"syscall"
)

const (
	maxMountInfoBytes    = 1 << 20
	maxExt4OptionsBytes  = 16 << 10
	procMountInfoPath    = "/proc/self/mountinfo"
	procExt4OptionsRoot  = "/proc/fs/ext4/"
	ext4OptionsLeafName  = "/options"
	requiredDataMode     = "data=ordered"
	requiredBarrierToken = "barrier"
)

var deviceNamePattern = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`)

// mountOptionSource supplies the raw effective mount-option evidence. The only
// production implementation is procMountSource. Other implementations exist
// only in same-package tests and cannot be reached from exported constructors.
type mountOptionSource interface {
	mountInfo() ([]byte, error)
	ext4Options(device string) ([]byte, error)
}

// procMountSource reads /proc/self/mountinfo for correlation and the
// world-readable /proc/fs/ext4/<device>/options, which lists every effective
// option including superblock defaults (manual §§5.3.1, 5.3.5).
type procMountSource struct{}

func (procMountSource) mountInfo() ([]byte, error) {
	return readBoundedFile(procMountInfoPath, maxMountInfoBytes)
}

func (procMountSource) ext4Options(device string) ([]byte, error) {
	if !deviceNamePattern.MatchString(device) {
		return nil, fmt.Errorf("unsafe device name")
	}
	return readBoundedFile(procExt4OptionsRoot+device+ext4OptionsLeafName, maxExt4OptionsBytes)
}

// productionMounts is the only source exported constructors bind.
func productionMounts() mountOptionSource {
	return procMountSource{}
}

func readBoundedFile(path string, limit int) ([]byte, error) {
	fd, err := syscall.Open(path, syscall.O_RDONLY|syscall.O_CLOEXEC|syscall.O_NOFOLLOW, 0)
	if err != nil {
		return nil, err
	}
	defer syscall.Close(fd)
	var out bytes.Buffer
	chunk := make([]byte, 4096)
	for {
		n, err := syscall.Read(fd, chunk)
		if err == syscall.EINTR {
			continue
		}
		if err != nil {
			return nil, err
		}
		if n == 0 {
			return out.Bytes(), nil
		}
		if out.Len()+n > limit {
			return nil, fmt.Errorf("source exceeds %d bytes", limit)
		}
		out.Write(chunk[:n])
	}
}

// MountReport records the observed, correlated effective options.
type MountReport struct {
	Device     string
	MountID    uint64
	Major      uint32
	Minor      uint32
	Barrier    string
	DataMode   string
	ReadWrite  bool
	Filesystem string
}

// checkMountOptions refuses unless the filesystem holding fd is ext4, mounted
// read-write, with barriers enabled and data=ordered, as shown by effective
// options correlated with the fd's own device and mount identity.
func checkMountOptions(src mountOptionSource, fd int) (MountReport, error) {
	var sfs syscall.Statfs_t
	if err := syscall.Fstatfs(fd, &sfs); err != nil {
		return MountReport{}, refuse(ReasonMountOptions, "filesystem type unavailable", err)
	}
	if sfs.Type != ext4SuperMagic {
		return MountReport{}, refuse(ReasonMountOptions, fmt.Sprintf("unsupported filesystem magic %#x", sfs.Type), nil)
	}
	var st syscall.Stat_t
	if err := syscall.Fstat(fd, &st); err != nil {
		return MountReport{}, refuse(ReasonMountOptions, "device identity unavailable", err)
	}
	sx, err := statxFD(fd, statxMntID)
	if err != nil {
		return MountReport{}, refuse(ReasonMountOptions, "mount identity unavailable", err)
	}
	if sx.Mask&statxMntID == 0 {
		return MountReport{}, refuse(ReasonMountOptions, "mount identity not reported", nil)
	}
	report := MountReport{MountID: sx.MntID, Major: devMajor(uint64(st.Dev)), Minor: devMinor(uint64(st.Dev))}

	info, err := src.mountInfo()
	if err != nil {
		return report, refuse(ReasonMountOptions, "mountinfo unreadable", err)
	}
	entry, err := findMountEntry(info, report.MountID)
	if err != nil {
		return report, err
	}
	if entry.major != report.Major || entry.minor != report.Minor {
		return report, refuse(ReasonMountOptions, "mountinfo device does not match the store handle", nil)
	}
	if entry.fsType != "ext4" {
		return report, refuse(ReasonMountOptions, "mountinfo filesystem is not ext4", nil)
	}
	report.Filesystem = entry.fsType
	if !hasToken(entry.mountOptions, "rw") || !hasToken(entry.superOptions, "rw") {
		return report, refuse(ReasonMountOptions, "store mount is not read-write", nil)
	}
	if !strings.HasPrefix(entry.source, "/dev/") {
		return report, refuse(ReasonMountOptions, "mount source is not correlated with a block device", nil)
	}
	device := strings.TrimPrefix(entry.source, "/dev/")
	if !deviceNamePattern.MatchString(device) {
		return report, refuse(ReasonMountOptions, "mount source device name is unsupported", nil)
	}
	report.Device = device

	raw, err := src.ext4Options(device)
	if err != nil {
		return report, refuse(ReasonMountOptions, "effective ext4 options unreadable", err)
	}
	opts, err := parseExt4Options(raw)
	if err != nil {
		return report, err
	}
	report.ReadWrite = opts.readWrite
	report.Barrier = opts.barrier
	report.DataMode = opts.dataMode
	if !opts.readWrite {
		return report, refuse(ReasonMountOptions, "effective options are not read-write", nil)
	}
	if opts.barrier != requiredBarrierToken {
		return report, refuse(ReasonMountOptions, "barriers are not enabled", nil)
	}
	if opts.dataMode != requiredDataMode {
		return report, refuse(ReasonMountOptions, "data mode is not ordered", nil)
	}
	return report, nil
}

type mountEntry struct {
	major, minor uint32
	mountOptions string
	fsType       string
	source       string
	superOptions string
}

func findMountEntry(info []byte, mountID uint64) (mountEntry, error) {
	if len(info) == 0 || info[len(info)-1] != '\n' {
		return mountEntry{}, refuse(ReasonMountOptions, "mountinfo unparseable", nil)
	}
	var found *mountEntry
	for _, line := range strings.Split(strings.TrimSuffix(string(info), "\n"), "\n") {
		fields := strings.Split(line, " ")
		sep := -1
		for i := 6; i < len(fields); i++ {
			if fields[i] == "-" {
				sep = i
				break
			}
		}
		if len(fields) < 10 || sep < 0 || len(fields) != sep+4 {
			return mountEntry{}, refuse(ReasonMountOptions, "mountinfo unparseable", nil)
		}
		id, err := strconv.ParseUint(fields[0], 10, 64)
		if err != nil {
			return mountEntry{}, refuse(ReasonMountOptions, "mountinfo unparseable", nil)
		}
		if id != mountID {
			continue
		}
		if found != nil {
			return mountEntry{}, refuse(ReasonMountOptions, "mountinfo has duplicate mount identity", nil)
		}
		majMin := strings.Split(fields[2], ":")
		if len(majMin) != 2 {
			return mountEntry{}, refuse(ReasonMountOptions, "mountinfo unparseable", nil)
		}
		major, err1 := strconv.ParseUint(majMin[0], 10, 32)
		minor, err2 := strconv.ParseUint(majMin[1], 10, 32)
		if err1 != nil || err2 != nil {
			return mountEntry{}, refuse(ReasonMountOptions, "mountinfo unparseable", nil)
		}
		found = &mountEntry{
			major:        uint32(major),
			minor:        uint32(minor),
			mountOptions: fields[5],
			fsType:       fields[sep+1],
			source:       fields[sep+2],
			superOptions: fields[sep+3],
		}
	}
	if found == nil {
		return mountEntry{}, refuse(ReasonMountOptions, "store mount not found in mountinfo", nil)
	}
	return *found, nil
}

func hasToken(list, token string) bool {
	for _, item := range strings.Split(list, ",") {
		if item == token {
			return true
		}
	}
	return false
}

type ext4Options struct {
	readWrite bool
	barrier   string
	dataMode  string
}

// parseExt4Options strictly parses one option per line. Unparseable,
// duplicated, conflicting or missing durability-relevant values refuse.
func parseExt4Options(raw []byte) (ext4Options, error) {
	unparseable := func(detail string) (ext4Options, error) {
		return ext4Options{}, refuse(ReasonMountOptions, "effective options unparseable: "+detail, nil)
	}
	if len(raw) == 0 || raw[len(raw)-1] != '\n' {
		return unparseable("missing terminator")
	}
	var opts ext4Options
	seen := map[string]bool{}
	rwCount, barrierCount, dataCount := 0, 0, 0
	for _, line := range strings.Split(strings.TrimSuffix(string(raw), "\n"), "\n") {
		if line == "" {
			return unparseable("empty option")
		}
		for i := 0; i < len(line); i++ {
			if line[i] <= ' ' || line[i] > '~' {
				return unparseable("invalid byte")
			}
		}
		if seen[line] {
			return unparseable("duplicate option")
		}
		seen[line] = true
		switch {
		case line == "rw":
			rwCount++
			opts.readWrite = true
		case line == "ro":
			rwCount++
			opts.readWrite = false
		case line == "barrier" || line == "nobarrier" || strings.HasPrefix(line, "barrier="):
			barrierCount++
			opts.barrier = line
		case strings.HasPrefix(line, "data="):
			dataCount++
			opts.dataMode = line
		}
	}
	if rwCount != 1 || barrierCount != 1 || dataCount != 1 {
		return unparseable("durability-relevant option missing or conflicting")
	}
	return opts, nil
}
