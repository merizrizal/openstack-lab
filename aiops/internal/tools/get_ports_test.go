package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"

	"github.com/gophercloud/gophercloud/v2"
)

const (
	testServerID  = "11111111-1111-4111-8111-111111111111"
	testProjectID = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
)

func testGetPortsTool(t *testing.T, handler http.HandlerFunc) *GetPortsTool {
	t.Helper()

	server := httptest.NewServer(handler)
	t.Cleanup(server.Close)

	client := &gophercloud.ServiceClient{
		ProviderClient: &gophercloud.ProviderClient{HTTPClient: http.Client{}},
		Endpoint:       server.URL + "/",
		ResourceBase:   server.URL + "/v2.0/",
	}

	tool := NewGetPortsTool(client, testProjectID)
	return tool
}

func TestGetPortsTool_ReadOnlyScopedObservation(t *testing.T) {
	var requests atomic.Int32
	tool := testGetPortsTool(t, func(w http.ResponseWriter, r *http.Request) {
		requests.Add(1)
		if r.Method != http.MethodGet || r.URL.Path != "/v2.0/ports" {
			t.Errorf("unexpected operation: %s %s", r.Method, r.URL.Path)
		}
		if got := r.URL.Query().Get("device_id"); got != testServerID {
			t.Errorf("unexpected device_id filter: %q", got)
		}
		if got := r.URL.Query().Get("project_id"); got != testProjectID {
			t.Errorf("unexpected project_id filter: %q", got)
		}
		if got := r.URL.Query().Get("limit"); got != "33" {
			t.Errorf("unexpected limit: %q", got)
		}
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprintf(w, `{"ports":[{"id":"port-1","device_id":%q,"project_id":%q,"network_id":"network-1","status":"ACTIVE","admin_state_up":true,"mac_address":"aa:bb:cc:dd:ee:ff","fixed_ips":[{"ip_address":"10.0.0.7","subnet_id":"subnet-1"}]}]}`, testServerID, testProjectID)
	})

	registry, err := NewRegistry(tool)
	if err != nil {
		t.Fatalf("register tool: %v", err)
	}
	data, err := registry.Execute(context.Background(), "get_ports", json.RawMessage(fmt.Sprintf(`{"server_id":%q}`, testServerID)))
	if err != nil {
		t.Fatalf("execute get_ports: %v", err)
	}

	var result PortsObservation
	if err := json.Unmarshal(data, &result); err != nil {
		t.Fatalf("decode observation: %v", err)
	}
	if result.ServerID != testServerID || result.ProjectID != testProjectID || len(result.Ports) != 1 {
		t.Fatalf("unexpected observation: %+v", result)
	}
	if result.Ports[0].Status != "ACTIVE" || !result.Ports[0].AdminStateUp {
		t.Fatalf("unexpected status: %+v", result.Ports[0])
	}
	if strings.Contains(string(data), "mac_address") || strings.Contains(string(data), "fixed_ips") {
		t.Fatalf("observation leaked fields outside the approved projection: %s", data)
	}
	if got := requests.Load(); got != 1 {
		t.Fatalf("expected exactly one request, got %d", got)
	}
}

func TestGetPortsTool_RejectsArgumentsBeforeRequest(t *testing.T) {
	var requests atomic.Int32
	tool := testGetPortsTool(t, func(http.ResponseWriter, *http.Request) { requests.Add(1) })

	inputs := []string{
		`{}`,
		`{"server_id":""}`,
		`{"server_id":"my-vm"}`,
		`{"server_id":"11111111-1111-4111-8111-111111111111","project_id":"aaaaaaaa"}`,
		`{"server_id":"11111111-1111-4111-8111-111111111111"} {"server_id":"11111111-1111-4111-8111-111111111111"}`,
		`[]`,
		`null`,
	}

	for _, input := range inputs {
		if _, err := tool.Execute(context.Background(), json.RawMessage(input)); err == nil {
			t.Errorf("input should have been rejected: %s", input)
		}
	}
	if got := requests.Load(); got != 0 {
		t.Fatalf("invalid requests reached Neutron %d times", got)
	}
}

func TestGetPortsTool_RejectsResponseScopeMismatch(t *testing.T) {
	tests := []struct {
		name string
		body string
	}{
		{"wrong device", `{"ports":[{"id":"port-1","device_id":"22222222-2222-4222-8222-222222222222","project_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}]}`},
		{"wrong project", `{"ports":[{"id":"port-1","device_id":"11111111-1111-4111-8111-111111111111","project_id":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}]}`},
		{"missing project", `{"ports":[{"id":"port-1","device_id":"11111111-1111-4111-8111-111111111111"}]}`},
		{"conflicting legacy tenant", `{"ports":[{"id":"port-1","device_id":"11111111-1111-4111-8111-111111111111","project_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","tenant_id":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}]}`},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tool := testGetPortsTool(t, func(w http.ResponseWriter, r *http.Request) {
				w.Header().Set("Content-Type", "application/json")
				fmt.Fprint(w, tt.body)
			})
			if _, err := tool.Execute(context.Background(), json.RawMessage(fmt.Sprintf(`{"server_id":%q}`, testServerID))); err == nil {
				t.Fatal("out-of-scope port should have been rejected")
			}
		})
	}
}

func TestGetPortsTool_RejectsExcessivePortCount(t *testing.T) {
	tool := testGetPortsTool(t, func(w http.ResponseWriter, r *http.Request) {
		items := make([]map[string]any, 0, maxPortRecords+1)
		for i := 0; i < maxPortRecords+1; i++ {
			items = append(items, map[string]any{
				"id":         fmt.Sprintf("port-%d", i),
				"device_id":  testServerID,
				"project_id": testProjectID,
			})
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{"ports": items})
	})

	if _, err := tool.Execute(context.Background(), json.RawMessage(fmt.Sprintf(`{"server_id":%q}`, testServerID))); err == nil {
		t.Fatal("too many port records should have been rejected")
	}
}

func TestGetPortsTool_PropagatesNeutronPermissionError(t *testing.T) {
	tool := testGetPortsTool(t, func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusForbidden)
		fmt.Fprint(w, `{"NeutronError":{"message":"forbidden"}}`)
	})

	if _, err := tool.Execute(context.Background(), json.RawMessage(fmt.Sprintf(`{"server_id":%q}`, testServerID))); err == nil {
		t.Fatal("Neutron 403 should not be treated as an empty port list")
	}
}
