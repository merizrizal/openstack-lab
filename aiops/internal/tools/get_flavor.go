package tools

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/gophercloud/gophercloud/v2"
	"github.com/gophercloud/gophercloud/v2/openstack/compute/v2/flavors"
)

type GetFlavorTool struct {
	compute *gophercloud.ServiceClient
}

func NewGetFlavorTool(compute *gophercloud.ServiceClient) *GetFlavorTool {
	return &GetFlavorTool{compute: compute}
}

func (t *GetFlavorTool) Name() string {
	return "get_flavor"
}

func (t *GetFlavorTool) Description() string {
	return "Retrieve an OpenStack Nova flavor and its extra specs using an exact flavor ID. This tool is read-only."
}

type getFlavorArguments struct {
	FlavorID string `json:"flavor_id"`
}

type FlavorObservation struct {
	ID              string            `json:"id"`
	Name            string            `json:"name"`
	VCPUs           int               `json:"vcpus"`
	RAMMB           int               `json:"ram_mb"`
	DiskGB          int               `json:"disk_gb"`
	EphemeralGB     int               `json:"ephemeral_gb"`
	SwapMB          int               `json:"swap_mb"`
	ExtraSpecs      map[string]string `json:"extra_specs,omitempty"`
	ExtraSpecsError string            `json:"extra_specs_error,omitempty"`
}

func (t *GetFlavorTool) Execute(ctx context.Context, rawArguments json.RawMessage) (json.RawMessage, error) {
	var arguments getFlavorArguments

	decoder := json.NewDecoder(bytes.NewReader(rawArguments))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&arguments); err != nil {
		return nil, fmt.Errorf("decode get_flavor arguments: %w", err)
	}

	arguments.FlavorID = strings.TrimSpace(arguments.FlavorID)
	if arguments.FlavorID == "" {
		return nil, fmt.Errorf("flavor_id is required")
	}

	flavor, err := flavors.Get(ctx, t.compute, arguments.FlavorID).Extract()
	if err != nil {
		return nil, fmt.Errorf("get Nova flavor %q: %w", arguments.FlavorID, err)
	}

	observation := FlavorObservation{
		ID:          flavor.ID,
		Name:        flavor.Name,
		VCPUs:       flavor.VCPUs,
		RAMMB:       flavor.RAM,
		DiskGB:      flavor.Disk,
		EphemeralGB: flavor.Ephemeral,
		SwapMB:      flavor.Swap,
	}

	extraSpecs, err := flavors.ListExtraSpecs(ctx, t.compute, arguments.FlavorID).Extract()
	if err != nil {
		observation.ExtraSpecsError = err.Error()
	} else {
		observation.ExtraSpecs = extraSpecs
	}

	result, err := json.Marshal(observation)
	if err != nil {
		return nil, fmt.Errorf("encode flavor observation: %w", err)
	}

	return result, nil
}
