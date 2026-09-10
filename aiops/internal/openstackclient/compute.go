package openstackclient

import (
	"context"
	"fmt"
	"os"

	"github.com/gophercloud/gophercloud/v2"
	"github.com/gophercloud/gophercloud/v2/openstack"
)

func NewComputeClient(ctx context.Context) (*gophercloud.ServiceClient, error) {
	authOptions, err := openstack.AuthOptionsFromEnv()
	if err != nil {
		return nil, fmt.Errorf("read OpenStack auth from environment: %w", err)
	}

	provider, err := openstack.AuthenticatedClient(ctx, authOptions)
	if err != nil {
		return nil, fmt.Errorf("authenticate to OpenStack: %w", err)
	}

	computeClient, err := openstack.NewComputeV2(provider, gophercloud.EndpointOpts{
		Region: os.Getenv("OS_REGION_NAME"),
	})
	if err != nil {
		return nil, fmt.Errorf("create Nova client: %w", err)
	}

	return computeClient, nil
}
