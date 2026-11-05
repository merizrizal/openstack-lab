package scopedtools

import (
	"context"
	"errors"
	"sync"
	"testing"
)

const (
	serverA  = "11111111-1111-4111-8111-111111111111"
	serverB  = "22222222-2222-4222-8222-222222222222"
	projectA = "project-a"
)

func fakeReaders(n *int) ReaderFuncs {
	return ReaderFuncs{
		GetServer: func(_ context.Context, id string) (ServerSnapshot, error) {
			*n++
			return ServerSnapshot{ID: id, ProjectID: projectA, FlavorID: "small", Status: "ERROR", Fault: "NoValidHost"}, nil
		},
		GetFlavor: func(_ context.Context, id string) (FlavorSnapshot, error) {
			*n++
			return FlavorSnapshot{ID: id, VCPUs: 2, RAMMiB: 4096}, nil
		},
		GetPorts: func(_ context.Context, projectID, id string) ([]PortSnapshot, error) {
			*n++
			return []PortSnapshot{{ID: "port-1", ProjectID: projectID, DeviceID: id, Status: "DOWN"}}, nil
		},
	}
}

func assignment(role string) Assignment {
	return Assignment{Role: role, ProjectID: projectA, TargetID: serverA, FlavorID: "small"}
}

func invoke(b *Broker, a Assignment, name, key, value string) (Result, error) {
	return b.Execute(context.Background(), a, Call{Name: name, Arguments: map[string]string{key: value}})
}

func TestComputeAndNetworkCapabilities(t *testing.T) {
	calls := 0
	broker, err := NewBroker(fakeReaders(&calls), 4)
	if err != nil {
		t.Fatal(err)
	}
	server, err := invoke(broker, assignment(Compute), "get_server", "server_id", serverA)
	if err != nil {
		t.Fatal(err)
	}
	flavor, err := invoke(broker, assignment(Compute), "get_flavor", "flavor_id", "small")
	if err != nil {
		t.Fatal(err)
	}
	ports, err := invoke(broker, assignment(Network), "get_ports", "device_id", serverA)
	if err != nil {
		t.Fatal(err)
	}
	if server.Evidence.ID == flavor.Evidence.ID || server.Evidence.ID == ports.Evidence.ID {
		t.Fatal("duplicate evidence IDs")
	}
	if server.Evidence.ObservedAt.IsZero() || server.Evidence.TargetID != serverA {
		t.Fatal("invalid evidence provenance")
	}
	if calls != 3 || broker.CallsUsed() != 3 {
		t.Fatalf("calls=%d budget=%d", calls, broker.CallsUsed())
	}
}

func TestDeniedBeforeReaderCall(t *testing.T) {
	cases := []struct {
		name string
		a    Assignment
		call Call
	}{
		{"compute cannot query ports", assignment(Compute), Call{"get_ports", map[string]string{"device_id": serverA}}},
		{"network cannot query flavor", assignment(Network), Call{"get_flavor", map[string]string{"flavor_id": "small"}}},
		{"unknown tool", assignment(Compute), Call{"delete_server", map[string]string{"server_id": serverA}}},
		{"wrong server", assignment(Compute), Call{"get_server", map[string]string{"server_id": serverB}}},
		{"wrong port device", assignment(Network), Call{"get_ports", map[string]string{"device_id": serverB}}},
		{"wrong flavor", assignment(Compute), Call{"get_flavor", map[string]string{"flavor_id": "large"}}},
		{"extra args", assignment(Compute), Call{"get_server", map[string]string{"server_id": serverA, "all_tenants": "1"}}},
		{"unknown role", assignment("superuser"), Call{"get_server", map[string]string{"server_id": serverA}}},
		{"no verified flavor", Assignment{Role: Compute, ProjectID: projectA, TargetID: serverA}, Call{"get_flavor", map[string]string{"flavor_id": "small"}}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			calls := 0
			broker, _ := NewBroker(fakeReaders(&calls), 2)
			_, err := broker.Execute(context.Background(), tc.a, tc.call)
			if !errors.Is(err, ErrDenied) {
				t.Fatalf("expected denial, got %v", err)
			}
			if calls != 0 || broker.CallsUsed() != 0 {
				t.Fatalf("denied call reached adapter or consumed budget: %d", calls)
			}
		})
	}
}

func TestResponseScopeIsChecked(t *testing.T) {
	cases := []struct {
		name   string
		call   Call
		modify func(*ReaderFuncs)
	}{
		{"server wrong project", Call{"get_server", map[string]string{"server_id": serverA}}, func(f *ReaderFuncs) {
			f.GetServer = func(context.Context, string) (ServerSnapshot, error) {
				return ServerSnapshot{ID: serverA, ProjectID: "other", FlavorID: "small"}, nil
			}
		}},
		{"server flavor drift", Call{"get_server", map[string]string{"server_id": serverA}}, func(f *ReaderFuncs) {
			f.GetServer = func(context.Context, string) (ServerSnapshot, error) {
				return ServerSnapshot{ID: serverA, ProjectID: projectA, FlavorID: "changed"}, nil
			}
		}},
		{"flavor wrong identity", Call{"get_flavor", map[string]string{"flavor_id": "small"}}, func(f *ReaderFuncs) {
			f.GetFlavor = func(context.Context, string) (FlavorSnapshot, error) { return FlavorSnapshot{ID: "large"}, nil }
		}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			n := 0
			f := fakeReaders(&n)
			tc.modify(&f)
			b, _ := NewBroker(f, 1)
			_, err := b.Execute(context.Background(), assignment(Compute), tc.call)
			if !errors.Is(err, ErrDenied) {
				t.Fatalf("expected denial, got %v", err)
			}
			if b.CallsUsed() != 1 {
				t.Fatalf("expected budget consumed, got %d", b.CallsUsed())
			}
		})
	}
}

func TestPortsMustBelongToTargetAndProject(t *testing.T) {
	for _, tc := range []PortSnapshot{
		{ID: "x", ProjectID: "other", DeviceID: serverA},
		{ID: "x", ProjectID: projectA, DeviceID: serverB},
	} {
		n := 0
		f := fakeReaders(&n)
		f.GetPorts = func(context.Context, string, string) ([]PortSnapshot, error) { return []PortSnapshot{tc}, nil }
		b, _ := NewBroker(f, 1)
		_, err := invoke(b, assignment(Network), "get_ports", "device_id", serverA)
		if !errors.Is(err, ErrDenied) {
			t.Fatalf("expected denial, got %v", err)
		}
	}
}

func TestSharedBudgetAndConcurrentAttempts(t *testing.T) {
	var mu sync.Mutex
	calls := 0
	f := ReaderFuncs{
		GetServer: func(_ context.Context, id string) (ServerSnapshot, error) {
			mu.Lock()
			calls++
			mu.Unlock()
			return ServerSnapshot{ID: id, ProjectID: projectA, FlavorID: "small"}, nil
		},
		GetFlavor: func(_ context.Context, id string) (FlavorSnapshot, error) { return FlavorSnapshot{ID: id}, nil },
		GetPorts:  func(context.Context, string, string) ([]PortSnapshot, error) { return []PortSnapshot{}, nil },
	}
	b, _ := NewBroker(f, 2)
	var wg sync.WaitGroup
	success, limited := 0, 0
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			_, err := invoke(b, assignment(Compute), "get_server", "server_id", serverA)
			mu.Lock()
			defer mu.Unlock()
			switch {
			case err == nil:
				success++
			case errors.Is(err, ErrBudget):
				limited++
			default:
				t.Errorf("unexpected error: %v", err)
			}
		}()
	}
	wg.Wait()
	if success != 2 || limited != 6 || calls != 2 {
		t.Fatalf("success=%d limited=%d reader=%d", success, limited, calls)
	}
}

func TestCanceledRequestNeverReachesReader(t *testing.T) {
	calls := 0
	b, _ := NewBroker(fakeReaders(&calls), 2)
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	_, err := b.Execute(ctx, assignment(Compute), Call{Name: "get_server", Arguments: map[string]string{"server_id": serverA}})
	if !errors.Is(err, context.Canceled) || calls != 0 || b.CallsUsed() != 0 {
		t.Fatalf("error=%v calls=%d", err, calls)
	}
}
