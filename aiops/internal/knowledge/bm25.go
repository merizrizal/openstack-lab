package knowledge

import (
	"context"
	"math"
	"regexp"
	"sort"
	"strings"
)

var tokenPattern = regexp.MustCompile(`[A-Za-z0-9][A-Za-z0-9_.:/-]*`)

type bm25Document struct {
	chunk  Chunk
	terms  map[string]int
	length int
}

type BM25 struct {
	documents []bm25Document
	df        map[string]int
	avgLength float64
	k1        float64
	b         float64
}

func NewBM25(chunks []Chunk) *BM25 {
	index := &BM25{
		documents: make([]bm25Document, 0, len(chunks)),
		df:        make(map[string]int),
		k1:        1.2,
		b:         0.75,
	}

	totalLength := 0

	for _, chunk := range chunks {
		tokens := tokenize(chunk.Text)
		terms := make(map[string]int)
		seen := make(map[string]struct{})

		for _, token := range tokens {
			terms[token]++

			if _, exists := seen[token]; exists {
				continue
			}

			seen[token] = struct{}{}
			index.df[token]++
		}

		index.documents = append(index.documents, bm25Document{
			chunk:  chunk,
			terms:  terms,
			length: len(tokens),
		})

		totalLength += len(tokens)
	}

	if len(index.documents) > 0 {
		index.avgLength = float64(totalLength) / float64(len(index.documents))
	}

	return index
}

func (b *BM25) Search(ctx context.Context, query string, limit int) ([]Result, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	if limit <= 0 || len(b.documents) == 0 || b.avgLength == 0 {
		return nil, nil
	}

	queryTerms := uniqueTokens(query)
	results := make([]Result, 0)

	for _, document := range b.documents {
		score := 0.0

		for _, term := range queryTerms {
			tf := document.terms[term]
			if tf == 0 {
				continue
			}

			df := b.df[term]
			n := float64(len(b.documents))
			idf := math.Log(1 + (n-float64(df)+0.5)/(float64(df)+0.5))
			lengthRatio := float64(document.length) / b.avgLength
			denominator := float64(tf) + b.k1*(1-b.b+b.b*lengthRatio)

			score += idf * (float64(tf) * (b.k1 + 1) / denominator)
		}

		if score == 0 {
			continue
		}

		results = append(results, Result{
			ID:      document.chunk.ID,
			Source:  document.chunk.Source,
			Section: document.chunk.Section,
			Text:    document.chunk.Text,
			Score:   score,
		})
	}

	sort.Slice(results, func(i, j int) bool {
		return results[i].Score > results[j].Score
	})

	if len(results) > limit {
		results = results[:limit]
	}

	return results, nil
}

func tokenize(value string) []string {
	raw := tokenPattern.FindAllString(strings.ToLower(value), -1)
	tokens := make([]string, 0, len(raw))

	for _, token := range raw {
		token = strings.TrimSpace(token)
		if token != "" {
			tokens = append(tokens, token)
		}
	}

	return tokens
}

func uniqueTokens(value string) []string {
	seen := make(map[string]struct{})
	tokens := make([]string, 0)

	for _, token := range tokenize(value) {
		if _, exists := seen[token]; exists {
			continue
		}

		seen[token] = struct{}{}
		tokens = append(tokens, token)
	}

	return tokens
}
