package diagnosis

import "fmt"

type Hypothesis struct {
	Summary         string   `json:"summary"`
	Confidence      string   `json:"confidence"`
	SupportingFacts []string `json:"supporting_facts"`
}

type IncidentAnalysis struct {
	Domain                string       `json:"domain"`
	PrimaryService        string       `json:"primary_service"`
	ProblemType           string       `json:"problem_type"`
	Assessment            string       `json:"assessment"`
	ObservedFacts         []string     `json:"observed_facts"`
	Hypotheses            []Hypothesis `json:"hypotheses"`
	MissingEvidence       []string     `json:"missing_evidence"`
	NextEvidenceToCollect []string     `json:"next_evidence_to_collect"`
}

func (a IncidentAnalysis) Validate() error {
	switch a.Domain {
	case "compute", "network", "storage", "identity", "image", "load_balancing", "unknown":
	default:
		return fmt.Errorf("invalid domain %q", a.Domain)
	}

	switch a.PrimaryService {
	case "nova", "placement", "neutron", "cinder", "keystone", "glance", "octavia", "ceph", "unknown":
	default:
		return fmt.Errorf("invalid primary service %q", a.PrimaryService)
	}

	switch a.Assessment {
	case "insufficient_evidence", "hypothesis_available", "root_cause_confirmed":
	default:
		return fmt.Errorf("invalid assessment %q", a.Assessment)
	}

	for i, hypothesis := range a.Hypotheses {
		switch hypothesis.Confidence {
		case "low", "medium", "high":
		default:
			return fmt.Errorf("hypothesis %d has invalid confidence %q", i, hypothesis.Confidence)
		}

		if hypothesis.Summary == "" {
			return fmt.Errorf("hypothesis %d has empty summary", i)
		}
	}

	return nil
}
