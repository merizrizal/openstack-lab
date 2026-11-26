//go:build linux && amd64

package protectedstore

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"fmt"
	"os"
	"syscall"
)

// Two-bank region layout (manual §§5.3.3–5.3.4). Each region file holds two
// fixed-size banks. Bank i starts at offset i*bankUnit, so each bank starts on
// a boundary that is a multiple of every observed alignment unit and the two
// banks share no such unit.
const (
	bankUnit       = 64 << 10
	regionFileSize = 2 * bankUnit
	bankHeaderSize = 64
	bankSumSize    = sha256.Size
	maxBankPayload = bankUnit - bankHeaderSize - bankSumSize
	formatVersion  = 1

	// assumedMaxPhysicalSector is the largest physical sector size the layout
	// covers. It cannot be observed without new privilege or reads outside the
	// authorized sources; bankUnit is a multiple of it by construction.
	assumedMaxPhysicalSector = 4096
)

var bankMagic = [8]byte{'A', 'I', 'O', 'P', 'S', 'B', 'K', '1'}

type bankKind uint8

const (
	kindBootstrap bankKind = 1
	kindInactive  bankKind = 2
	kindRecord    bankKind = 3
	kindEmpty     bankKind = 4
	// Session-control kinds, written only into the control region by an
	// admitted session (manual §5.3.2).
	kindActive bankKind = 5
	kindClean  bankKind = 6
)

func (k bankKind) known() bool {
	return k >= kindBootstrap && k <= kindClean
}

type bankState int

const (
	bankZero bankState = iota
	bankValid
)

type bank struct {
	index      uint8
	kind       bankKind
	generation uint64
	region     [32]byte
	payload    []byte
}

func regionIdentity(namespaceID, relativeName string) [32]byte {
	h := sha256.New()
	h.Write([]byte("aiops-protectedstore-region\x00"))
	writeLengthPrefixed(h, []byte(namespaceID))
	writeLengthPrefixed(h, []byte(relativeName))
	var out [32]byte
	copy(out[:], h.Sum(nil))
	return out
}

type byteWriter interface{ Write([]byte) (int, error) }

func writeLengthPrefixed(w byteWriter, value []byte) {
	var n [4]byte
	binary.BigEndian.PutUint32(n[:], uint32(len(value)))
	w.Write(n[:])
	w.Write(value)
}

func encodeBank(b bank) ([]byte, error) {
	if b.index > 1 || !b.kind.known() {
		return nil, refuse(ReasonCorrupt, "invalid bank descriptor", nil)
	}
	if len(b.payload) > maxBankPayload {
		return nil, refuse(ReasonLimit, "payload exceeds the bank bound", nil)
	}
	out := make([]byte, bankUnit)
	copy(out[0:8], bankMagic[:])
	binary.BigEndian.PutUint16(out[8:10], formatVersion)
	out[10] = b.index
	out[11] = byte(b.kind)
	binary.BigEndian.PutUint64(out[16:24], b.generation)
	copy(out[24:56], b.region[:])
	binary.BigEndian.PutUint32(out[56:60], uint32(len(b.payload)))
	copy(out[bankHeaderSize:], b.payload)
	end := bankHeaderSize + len(b.payload)
	sum := sha256.Sum256(out[:end])
	copy(out[end:end+bankSumSize], sum[:])
	return out, nil
}

// decodeBank classifies raw bank bytes. An all-zero bank is reported as
// bankZero; every other non-conforming encoding is refused.
func decodeBank(raw []byte, index uint8, region [32]byte) (bank, bankState, error) {
	if len(raw) != bankUnit {
		return bank{}, 0, refuse(ReasonCorrupt, "bank has unexpected size", nil)
	}
	if allZero(raw) {
		return bank{}, bankZero, nil
	}
	if !bytes.Equal(raw[0:8], bankMagic[:]) {
		return bank{}, 0, refuse(ReasonCorrupt, "bank magic invalid", nil)
	}
	if v := binary.BigEndian.Uint16(raw[8:10]); v != formatVersion {
		return bank{}, 0, refuse(ReasonVersion, fmt.Sprintf("unsupported bank format version %d", v), nil)
	}
	length := int(binary.BigEndian.Uint32(raw[56:60]))
	if length > maxBankPayload {
		return bank{}, 0, refuse(ReasonCorrupt, "bank length out of bounds", nil)
	}
	end := bankHeaderSize + length
	sum := sha256.Sum256(raw[:end])
	if !bytes.Equal(sum[:], raw[end:end+bankSumSize]) {
		return bank{}, 0, refuse(ReasonCorrupt, "bank checksum mismatch", nil)
	}
	if !allZero(raw[12:16]) || !allZero(raw[60:64]) || !allZero(raw[end+bankSumSize:]) {
		return bank{}, 0, refuse(ReasonCorrupt, "bank reserved bytes not zero", nil)
	}
	b := bank{
		index:      raw[10],
		kind:       bankKind(raw[11]),
		generation: binary.BigEndian.Uint64(raw[16:24]),
		payload:    append([]byte(nil), raw[bankHeaderSize:end]...),
	}
	copy(b.region[:], raw[24:56])
	if b.index != index {
		return bank{}, 0, refuse(ReasonCorrupt, "bank index mismatch", nil)
	}
	if !b.kind.known() {
		return bank{}, 0, refuse(ReasonCorrupt, "bank kind unknown", nil)
	}
	if b.region != region {
		return bank{}, 0, refuse(ReasonCorrupt, "bank region identity mismatch", nil)
	}
	return b, bankValid, nil
}

func allZero(b []byte) bool {
	for _, c := range b {
		if c != 0 {
			return false
		}
	}
	return true
}

// checkBankAlignment refuses unless bankUnit is a multiple of the filesystem
// block size, the page size, the assumed physical sector bound and, when the
// file reports direct-I/O support, stx_dio_offset_align and stx_dio_mem_align.
func checkBankAlignment(fd int) (alignmentReport, error) {
	var sfs syscall.Statfs_t
	if err := syscall.Fstatfs(fd, &sfs); err != nil {
		return alignmentReport{}, refuse(ReasonAlignment, "filesystem block size unavailable", err)
	}
	sx, err := statxFD(fd, statxDioAlign)
	if err != nil {
		return alignmentReport{}, refuse(ReasonAlignment, "statx unavailable", err)
	}
	r := alignmentReport{
		BlockSize: uint64(sfs.Bsize),
		PageSize:  uint64(os.Getpagesize()),
		Sector:    assumedMaxPhysicalSector,
		BankUnit:  bankUnit,
	}
	if sx.Mask&statxDioAlign != 0 {
		r.DioMemAlign = uint64(sx.DioMemAlign)
		r.DioOffsetAlign = uint64(sx.DioOffsetAlign)
	}
	return r, validateAlignmentUnits(r)
}

// validateAlignmentUnits requires every nonzero unit to be a power of two that
// divides bankUnit, so each bank starts on a boundary of at least the largest
// unit and the two banks share no such unit.
func validateAlignmentUnits(r alignmentReport) error {
	if r.BlockSize == 0 || r.PageSize == 0 {
		return refuse(ReasonAlignment, "block or page size unavailable", nil)
	}
	for _, unit := range []uint64{r.BlockSize, r.PageSize, r.Sector, r.DioOffsetAlign, r.DioMemAlign} {
		if unit == 0 {
			continue
		}
		if unit&(unit-1) != 0 || bankUnit%unit != 0 {
			return refuse(ReasonAlignment, fmt.Sprintf("bank unit %d is not a multiple of alignment unit %d", bankUnit, unit), nil)
		}
	}
	return nil
}

type alignmentReport struct {
	BlockSize      uint64
	PageSize       uint64
	Sector         uint64
	DioMemAlign    uint64
	DioOffsetAlign uint64
	BankUnit       uint64
}

// bankOffset returns the file offset of a bank.
func bankOffset(index uint8) int64 {
	return int64(index) * bankUnit
}
