package ai

import (
	"context"
	"os"
)

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
