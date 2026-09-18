package knowledge

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

type section struct {
	name string
	text string
}

func LoadDir(root string, maxWords, overlapWords int) ([]Chunk, error) {
	root = strings.TrimSpace(root)
	if root == "" {
		return nil, fmt.Errorf("knowledge root cannot be empty")
	}
	if maxWords <= 0 {
		maxWords = 220
	}
	if overlapWords < 0 || overlapWords >= maxWords {
		return nil, fmt.Errorf("overlap must be >= 0 and < max words")
	}

	var chunks []Chunk

	err := filepath.WalkDir(root, func(path string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}

		if entry.IsDir() {
			if path != root && strings.HasPrefix(entry.Name(), ".") {
				return filepath.SkipDir
			}
			return nil
		}

		ext := strings.ToLower(filepath.Ext(path))
		if ext != ".md" && ext != ".txt" {
			return nil
		}

		data, err := os.ReadFile(path)
		if err != nil {
			return fmt.Errorf("read knowledge file %q: %w", path, err)
		}

		relative, err := filepath.Rel(root, path)
		if err != nil {
			return fmt.Errorf("resolve relative knowledge path %q: %w", path, err)
		}

		source := filepath.ToSlash(relative)
		chunks = append(chunks, chunkFile(source, string(data), maxWords, overlapWords)...)

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("load knowledge directory: %w", err)
	}

	return chunks, nil
}

func chunkFile(source, text string, maxWords, overlapWords int) []Chunk {
	var chunks []Chunk
	step := maxWords - overlapWords

	for _, section := range splitSections(text) {
		words := strings.Fields(section.text)

		for start := 0; start < len(words); start += step {
			end := min(start+maxWords, len(words))
			chunkText := strings.Join(words[start:end], " ")

			chunks = append(chunks, Chunk{
				ID:      chunkID(source, section.name, start, chunkText),
				Source:  source,
				Section: section.name,
				Text:    chunkText,
			})

			if end == len(words) {
				break
			}
		}
	}

	return chunks
}

func splitSections(text string) []section {
	current := section{name: "document"}
	var sections []section
	var body strings.Builder

	flush := func() {
		current.text = strings.TrimSpace(body.String())
		if current.text != "" {
			sections = append(sections, current)
		}
		body.Reset()
	}

	for _, line := range strings.Split(text, "\n") {
		trimmed := strings.TrimSpace(line)

		if strings.HasPrefix(trimmed, "#") {
			heading := strings.TrimSpace(strings.TrimLeft(trimmed, "#"))
			if heading != "" {
				flush()
				current = section{name: heading}
				continue
			}
		}

		body.WriteString(line)
		body.WriteByte('\n')
	}

	flush()
	return sections
}

func chunkID(source, section string, start int, text string) string {
	value := source + "\x00" + section + "\x00" + strconv.Itoa(start) + "\x00" + text
	sum := sha256.Sum256([]byte(value))
	return hex.EncodeToString(sum[:8])
}
