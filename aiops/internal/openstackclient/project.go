package openstackclient

import (
	"fmt"
	"strings"

	"github.com/gophercloud/gophercloud/v2"
	"github.com/gophercloud/gophercloud/v2/openstack/identity/v3/tokens"
)

func ScopedProjectID(provider *gophercloud.ProviderClient) (string, error) {
	if provider == nil {
		return "", fmt.Errorf("OpenStack provider is nil")
	}

	result := provider.GetAuthResult()
	if result == nil {
		return "", fmt.Errorf("OpenStack authentication result is unavailable")
	}

	extractor, ok := result.(interface {
		ExtractProject() (*tokens.Project, error)
	})
	if !ok {
		return "", fmt.Errorf("authentication result does not support Keystone v3 project extraction: %T", result)
	}

	project, err := extractor.ExtractProject()
	if err != nil {
		return "", fmt.Errorf("extract authenticated project: %w", err)
	}

	if project == nil || strings.TrimSpace(project.ID) == "" {
		return "", fmt.Errorf("OpenStack token is not project-scoped")
	}

	return project.ID, nil
}
