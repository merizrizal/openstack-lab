
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
	$(GO) build -o bin/aiops ./cmd/aiops
