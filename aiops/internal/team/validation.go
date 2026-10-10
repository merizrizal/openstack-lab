package team

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"strings"
)

func validateInput(in Input) error {
	if strings.TrimSpace(in.Goal) == "" || strings.TrimSpace(in.TargetID) == "" {
		return fmt.Errorf("goal and target ID are required")
	}
	if len(in.Evidence) == 0 || len(in.Evidence) > 32 {
		return fmt.Errorf("provide 1..32 evidence records")
	}
	if len(in.Goal) > 8192 {
		return fmt.Errorf("goal exceeds 8192 bytes")
	}
	seen := map[string]bool{}
	bytes := 0
	for _, evidence := range in.Evidence {
		if strings.TrimSpace(evidence.ID) == "" || seen[evidence.ID] {
			return fmt.Errorf("empty or duplicate evidence ID %q", evidence.ID)
		}
		seen[evidence.ID] = true
		if evidence.TargetID != in.TargetID {
			return fmt.Errorf("evidence %q is outside the requested scope", evidence.ID)
		}
		if strings.TrimSpace(evidence.Tool) == "" || evidence.ObservedAt.IsZero() {
			return fmt.Errorf("evidence %q lacks source or observation time", evidence.ID)
		}
		if !json.Valid(evidence.Data) || string(evidence.Data) == "null" {
			return fmt.Errorf("evidence %q must contain JSON data", evidence.ID)
		}
		bytes += len(evidence.Data)
	}
	if bytes > 128*1024 {
		return fmt.Errorf("evidence data exceeds 128 KiB")
	}
	return nil
}

func validateReport(report Report, in Input) error {
	if len(report.Claims) == 0 || len(report.Claims) > 32 || report.MissingEvidence == nil {
		return fmt.Errorf("report requires 1..32 claims and an explicit missing_evidence array")
	}
	known := map[string]bool{}
	for _, evidence := range in.Evidence {
		known[evidence.ID] = true
	}
	claims := map[string]bool{}
	for _, claim := range report.Claims {
		if strings.TrimSpace(claim.ID) == "" || claims[claim.ID] {
			return fmt.Errorf("empty or duplicate claim ID %q", claim.ID)
		}
		claims[claim.ID] = true
		switch claim.Kind {
		case "observation", "interpretation", "hypothesis":
		default:
			return fmt.Errorf("invalid claim kind %q", claim.Kind)
		}
		if strings.TrimSpace(claim.Text) == "" || len(claim.Text) > 4096 || len(claim.EvidenceIDs) == 0 {
			return fmt.Errorf("claim %q needs bounded text and evidence references", claim.ID)
		}
		seen := map[string]bool{}
		for _, id := range claim.EvidenceIDs {
			if !known[id] || seen[id] {
				return fmt.Errorf("claim %q contains an unknown or duplicate evidence reference %q", claim.ID, id)
			}
			seen[id] = true
		}
	}
	if len(report.MissingEvidence) > 16 {
		return fmt.Errorf("too many missing-evidence entries")
	}
	for _, gap := range report.MissingEvidence {
		if strings.TrimSpace(gap) == "" || len(gap) > 2048 {
			return fmt.Errorf("missing-evidence descriptions must be nonempty and bounded")
		}
	}
	return nil
}

func validateReview(review Review, report Report, digest string) error {
	if review.Digest != digest {
		return fmt.Errorf("review is not bound to the current report and evidence snapshot")
	}
	if review.Issues == nil || len(review.Issues) > 32 {
		return fmt.Errorf("review requires a bounded issues array")
	}
	switch review.Verdict {
	case Accept:
		if len(review.Issues) != 0 {
			return fmt.Errorf("an accepted review must not contain unresolved issues")
		}
	case Revise, Escalate:
		if len(review.Issues) == 0 {
			return fmt.Errorf("revise/escalate requires a specific reason")
		}
	default:
		return fmt.Errorf("unknown review verdict %q", review.Verdict)
	}
	known := map[string]bool{}
	for _, claim := range report.Claims {
		known[claim.ID] = true
	}
	for _, issue := range review.Issues {
		if issue.ClaimID != "" && !known[issue.ClaimID] {
			return fmt.Errorf("review references unknown claim %q", issue.ClaimID)
		}
		if strings.TrimSpace(issue.Reason) == "" || len(issue.Reason) > 4096 {
			return fmt.Errorf("review issues require nonempty, bounded reasons")
		}
	}
	return nil
}

func bundleDigest(in Input, revision int, report Report) (string, error) {
	data, err := json.Marshal(struct {
		Input    Input  `json:"input"`
		Revision int    `json:"revision"`
		Report   Report `json:"report"`
	}{in, revision, report})
	if err != nil {
		return "", fmt.Errorf("encode review bundle: %w", err)
	}
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:]), nil
}
