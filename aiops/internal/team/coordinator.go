package team

import (
	"context"
	"fmt"
	"time"
)

type Coordinator struct {
	investigator Investigator
	reviewer     Reviewer
	maxRevisions int
	timeout      time.Duration
}

func NewCoordinator(investigator Investigator, reviewer Reviewer, maxRevisions int, timeout time.Duration) (*Coordinator, error) {
	if investigator == nil || reviewer == nil {
		return nil, fmt.Errorf("investigator and reviewer are required")
	}
	if maxRevisions < 0 || maxRevisions > 3 || timeout <= 0 {
		return nil, fmt.Errorf("use 0..3 revisions and a positive timeout")
	}
	return &Coordinator{investigator, reviewer, maxRevisions, timeout}, nil
}

func (c *Coordinator) Run(ctx context.Context, input Input) (Result, error) {
	result := Result{Outcome: Failed, Rounds: []Round{}}
	if err := validateInput(input); err != nil {
		return result, err
	}
	input = cloneInput(input)
	ctx, cancel := context.WithTimeout(ctx, c.timeout)
	defer cancel()

	var previous *Report
	var feedback *Review

	for revision := 1; revision <= c.maxRevisions+1; revision++ {
		if err := ctx.Err(); err != nil {
			return result, err
		}
		work := Work{Input: cloneInput(input), Revision: revision}
		if previous != nil {
			copy := cloneReport(*previous)
			work.Previous = &copy
		}
		if feedback != nil {
			copy := cloneReview(*feedback)
			work.Feedback = &copy
		}

		result.Invocations++
		report, err := c.investigator.Investigate(ctx, work)
		if err != nil {
			return result, fmt.Errorf("investigator revision %d: %w", revision, err)
		}
		if err := ctx.Err(); err != nil {
			return result, err
		}
		report = cloneReport(report)
		if err := validateReport(report, input); err != nil {
			return result, fmt.Errorf("invalid investigator report: %w", err)
		}
		digest, err := bundleDigest(input, revision, report)
		if err != nil {
			return result, err
		}
		result.Rounds = append(result.Rounds, Round{Revision: revision, Digest: digest, Report: report})

		result.Invocations++
		review, err := c.reviewer.Review(ctx, ReviewInput{
			Input: cloneInput(input), Revision: revision,
			Report: cloneReport(report), Digest: digest,
		})
		if err != nil {
			return result, fmt.Errorf("reviewer revision %d: %w", revision, err)
		}
		if err := ctx.Err(); err != nil {
			return result, err
		}
		review = cloneReview(review)
		if err := validateReview(review, report, digest); err != nil {
			return result, fmt.Errorf("invalid reviewer output: %w", err)
		}
		result.Rounds[len(result.Rounds)-1].Review = &review

		switch review.Verdict {
		case Accept:
			result.Outcome = Accepted
			return result, nil
		case Escalate:
			result.Outcome = NeedsHuman
			return result, nil
		case Revise:
			previous, feedback = &report, &review
		}
	}
	result.Outcome = NeedsHuman
	return result, nil
}
