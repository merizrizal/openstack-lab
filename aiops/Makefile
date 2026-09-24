
GO ?= go

.PHONY: all fmt test build

all: fmt test build

tidy:
	$(GO) mod tidy

fmt:
	$(GO) fmt ./...

test:
	$(GO) test ./...

build:
	mkdir -p bin
	$(GO) build -o bin/openstack-ai ./cmd/openstack-ai
	$(GO) build -o bin/openstack-agent ./cmd/openstack-agent
	$(GO) build -o bin/openstack-workflow ./cmd/openstack-workflow
	$(GO) build -o bin/openstack-project ./cmd/openstack-project
