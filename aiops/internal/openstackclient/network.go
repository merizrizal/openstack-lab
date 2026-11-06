package openstackclient

import (
	"context"
	"fmt"
	"os"

	"github.com/gophercloud/gophercloud/v2"
	"github.com/gophercloud/gophercloud/v2/openstack"
)

func NewNetworkClient(ctx context.Context) (*gophercloud.ServiceClient, string, error) {
	authOptions, err := openstack.AuthOptionsFromEnv()
	if err != nil {
		return nil, "", fmt.Errorf("read OpenStack auth from environment: %w", err)
	}

	provider, err := openstack.AuthenticatedClient(ctx, authOptions)
	if err != nil {
		return nil, "", fmt.Errorf("authenticate to OpenStack: %w", err)
	}

	projectID, err := ScopedProjectID(provider)
	if err != nil {
		return nil, "", err
	}

	networkClient, err := openstack.NewNetworkV2(provider, gophercloud.EndpointOpts{
		Region: os.Getenv("OS_REGION_NAME"),
	})
	if err != nil {
		return nil, "", fmt.Errorf("create Neutron client: %w", err)
	}

	return networkClient, projectID, nil
}
