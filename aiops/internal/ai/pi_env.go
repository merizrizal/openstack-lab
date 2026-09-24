package ai

import (
	"context"
	"os"
)

// NewPiClientFromEnv uses the application variables described in README.md.
// It intentionally does not import arbitrary credentials or proxy variables.
// Use Pi's dedicated auth.json, or configure ExtraEnv explicitly via NewPiClient.
func NewPiClientFromEnv(authorize func(context.Context, PiOutbound) error) (*PiClient, error) {
	return NewPiClient(PiConfig{
		Binary:          os.Getenv("PI_BIN"),
		Provider:        os.Getenv("AI_MODEL_PROVIDER"),
		Model:           os.Getenv("AI_MODEL"),
		AgentDir:        os.Getenv("PI_CODING_AGENT_DIR"),
		ExpectedVersion: os.Getenv("AI_PI_VERSION"),
		Authorize:       authorize,
	})
}
