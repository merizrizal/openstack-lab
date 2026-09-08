
GO ?= go

.PHONY: fmt test build

fmt:
	$(GO) fmt ./...

test:
	$(GO) test ./...

build:
	mkdir -p bin
	$(GO) build -o bin/openstack-ai ./cmd/openstack-ai
	$(GO) build -o bin/openstack-analyze ./cmd/openstack-analyze
