package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gophercloud/gophercloud/v2"
)

const (
	testServerUUID = "a8ac160f-12e5-461a-acd7-b79834dc548d"
	testServerName = "web-01"
)

func TestGetServerToolAcceptsServerUUID(t *testing.T) {
	client := newTestComputeClient(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/servers/"+testServerUUID {
			t.Errorf("request path = %q, want UUID lookup", r.URL.Path)
		}
		if r.Method != http.MethodGet {
			t.Errorf("request method = %q, want GET", r.Method)
		}

		writeServerResponse(w, testServerUUID, testServerName, "ACTIVE")
	})

	result, err := NewGetServerTool(client).Execute(
		context.Background(),
		json.RawMessage(fmt.Sprintf(`{"server_identifier":%q}`, testServerUUID)),
	)
	if err != nil {
		t.Fatalf("Execute() error = %v", err)
	}

	var observation ServerObservation
	if err := json.Unmarshal(result, &observation); err != nil {
		t.Fatalf("decode observation: %v", err)
	}
	if observation.ID != testServerUUID {
		t.Errorf("observation ID = %q, want %q", observation.ID, testServerUUID)
	}
	if observation.Name != testServerName {
		t.Errorf("observation name = %q, want %q", observation.Name, testServerName)
	}
	if observation.Status != "ACTIVE" {
		t.Errorf("observation status = %q, want ACTIVE", observation.Status)
	}
}

func TestGetServerToolResolvesServerName(t *testing.T) {
	client := newTestComputeClient(t, func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/servers/detail":
			if got := r.URL.Query().Get("name"); got != testServerName {
				t.Errorf("name filter = %q, want %q", got, testServerName)
			}
			writeJSON(w, fmt.Sprintf(`{"servers":[{"id":%q,"name":%q}]}`, testServerUUID, testServerName))
		case "/servers/" + testServerUUID:
			writeServerResponse(w, testServerUUID, testServerName, "SHUTOFF")
		default:
			http.NotFound(w, r)
		}
	})

	result, err := NewGetServerTool(client).Execute(
		context.Background(),
		json.RawMessage(fmt.Sprintf(`{"server_identifier":%q}`, testServerName)),
	)
	if err != nil {
		t.Fatalf("Execute() error = %v", err)
	}

	var observation ServerObservation
	if err := json.Unmarshal(result, &observation); err != nil {
		t.Fatalf("decode observation: %v", err)
	}
	if observation.ID != testServerUUID {
		t.Errorf("observation ID = %q, want %q", observation.ID, testServerUUID)
	}
	if observation.Status != "SHUTOFF" {
		t.Errorf("observation status = %q, want SHUTOFF", observation.Status)
	}
}

func TestGetServerToolRejectsMissingServerName(t *testing.T) {
	client := newTestComputeClient(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/servers/detail" {
			t.Errorf("request path = %q, want server detail list", r.URL.Path)
		}
		writeJSON(w, `{"servers":[]}`)
	})

	_, err := NewGetServerTool(client).Execute(
		context.Background(),
		json.RawMessage(`{"server_identifier":"missing-server"}`),
	)
	if err == nil {
		t.Fatal("Execute() error = nil, want not-found error")
	}
	if got := err.Error(); got != `get Nova server "missing-server": Unable to find server with name missing-server` {
		t.Fatalf("Execute() error = %q", got)
	}
}

func TestGetServerToolRejectsAmbiguousServerName(t *testing.T) {
	client := newTestComputeClient(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/servers/detail" {
			t.Errorf("request path = %q, want server detail list", r.URL.Path)
		}
		writeJSON(w, fmt.Sprintf(`{"servers":[{"id":"%s-1","name":%q},{"id":"%s-2","name":%q}]}`, testServerUUID, testServerName, testServerUUID, testServerName))
	})

	_, err := NewGetServerTool(client).Execute(
		context.Background(),
		json.RawMessage(fmt.Sprintf(`{"server_identifier":%q}`, testServerName)),
	)
	if err == nil {
		t.Fatal("Execute() error = nil, want ambiguous-name error")
	}
	if got := err.Error(); got != `get Nova server "web-01": Found 2 servers matching web-01` {
		t.Fatalf("Execute() error = %q", got)
	}
}

func TestGetServerToolRejectsLegacyServerIDArgument(t *testing.T) {
	_, err := NewGetServerTool(nil).Execute(
		context.Background(),
		json.RawMessage(`{"server_id":"`+testServerUUID+`"}`),
	)
	if err == nil {
		t.Fatal("Execute() error = nil, want unknown-field error")
	}
	if got := err.Error(); got != `decode get_server arguments: json: unknown field "server_id"` {
		t.Fatalf("Execute() error = %q", got)
	}
}

func newTestComputeClient(t *testing.T, handler http.HandlerFunc) *gophercloud.ServiceClient {
	t.Helper()

	server := httptest.NewServer(handler)
	t.Cleanup(server.Close)

	return &gophercloud.ServiceClient{
		ProviderClient: &gophercloud.ProviderClient{
			HTTPClient: *server.Client(),
			TokenID:    "test-token",
		},
		Endpoint: server.URL + "/",
	}
}

func writeJSON(w http.ResponseWriter, body string) {
	w.Header().Set("Content-Type", "application/json")
	fmt.Fprint(w, body)
}

func writeServerResponse(w http.ResponseWriter, id, name, status string) {
	writeJSON(w, fmt.Sprintf(`{"server":{"id":%q,"name":%q,"status":%q,"flavor":{"id":"m1.small"}}}`, id, name, status))
}
