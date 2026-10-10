package team

import (
	"context"
	"encoding/json"
	"slices"
	"time"
)

const (
	Accept     = "accept"
	Revise     = "revise"
	Escalate   = "escalate"
	Accepted   = "accepted"
	NeedsHuman = "needs_human"
	Failed     = "failed"
)

type Evidence struct {
	ID         string          `json:"id"`
	TargetID   string          `json:"target_id"`
	Tool       string          `json:"tool"`
	ObservedAt time.Time       `json:"observed_at"`
	Data       json.RawMessage `json:"data"`
}

type Input struct {
	Goal     string     `json:"goal"`
	TargetID string     `json:"target_id"`
	Evidence []Evidence `json:"evidence"`
}

type Claim struct {
	ID          string   `json:"id"`
	Kind        string   `json:"kind"`
	Text        string   `json:"text"`
	EvidenceIDs []string `json:"evidence_ids"`
}

type Report struct {
	Claims          []Claim  `json:"claims"`
	MissingEvidence []string `json:"missing_evidence"`
}

type Issue struct {
	ClaimID string `json:"claim_id"`
	Reason  string `json:"reason"`
}

type Review struct {
	Digest  string  `json:"digest"`
	Verdict string  `json:"verdict"`
	Issues  []Issue `json:"issues"`
}

type Work struct {
	Input    Input   `json:"input"`
	Revision int     `json:"revision"`
	Previous *Report `json:"previous,omitempty"`
	Feedback *Review `json:"feedback,omitempty"`
}

type ReviewInput struct {
	Input    Input  `json:"input"`
	Revision int    `json:"revision"`
	Report   Report `json:"report"`
	Digest   string `json:"digest"`
}

type Investigator interface {
	Investigate(context.Context, Work) (Report, error)
}

type Reviewer interface {
	Review(context.Context, ReviewInput) (Review, error)
}

type Round struct {
	Revision int     `json:"revision"`
	Digest   string  `json:"digest"`
	Report   Report  `json:"report"`
	Review   *Review `json:"review,omitempty"`
}

type Result struct {
	Outcome     string  `json:"outcome"`
	Rounds      []Round `json:"rounds"`
	Invocations int     `json:"role_invocations"`
}

func cloneInput(in Input) Input {
	in.Evidence = slices.Clone(in.Evidence)
	for i := range in.Evidence {
		in.Evidence[i].Data = slices.Clone(in.Evidence[i].Data)
	}
	return in
}

func cloneReport(report Report) Report {
	report.Claims = slices.Clone(report.Claims)
	for i := range report.Claims {
		report.Claims[i].EvidenceIDs = slices.Clone(report.Claims[i].EvidenceIDs)
	}
	report.MissingEvidence = slices.Clone(report.MissingEvidence)
	return report
}

func cloneReview(review Review) Review {
	review.Issues = slices.Clone(review.Issues)
	return review
}
