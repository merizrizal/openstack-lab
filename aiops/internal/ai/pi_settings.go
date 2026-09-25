package ai

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
)

func (c *PiClient) checkSettings() error {
	data, err := os.ReadFile(filepath.Join(c.config.AgentDir, "settings.json"))
	if err != nil {
		return fmt.Errorf("read dedicated Pi settings (see example-pi-settings.json): %w", err)
	}
	if len(data) > 64*1024 {
		return errors.New("Pi settings exceed size budget")
	}
	if _, err := piDecodeJSON(data); err != nil {
		return errors.New("Pi settings are not strict JSON")
	}
	var settings struct {
		CacheWarming string `json:"cacheWarming"`
		Compaction   struct {
			Enabled *bool `json:"enabled"`
		} `json:"compaction"`
		Retry struct {
			Enabled  *bool `json:"enabled"`
			Provider struct {
				MaxRetries *int `json:"maxRetries"`
			} `json:"provider"`
		} `json:"retry"`
	}
	if err := json.Unmarshal(data, &settings); err != nil {
		return errors.New("Pi settings have invalid types")
	}
	if settings.CacheWarming != "off" || settings.Compaction.Enabled == nil || *settings.Compaction.Enabled ||
		settings.Retry.Enabled == nil || *settings.Retry.Enabled || settings.Retry.Provider.MaxRetries == nil || *settings.Retry.Provider.MaxRetries != 0 {
		return errors.New("disable Pi cache warming, compaction, agent retry and provider retry explicitly in dedicated settings")
	}
	return nil
}
