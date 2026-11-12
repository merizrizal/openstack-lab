# Baseline Tooling Setup Runbook

Use this runbook on the assistant runtime host to install and verify the baseline tooling described in `docs/ai-ops/runtime/README.md`.

This is operator-run setup only. Do not expose these commands as AI-facing tools.

## Purpose

Phase 01 tooling should support later diagnostics without adding authority. The goal is to install the tools, verify their versions, and record evidence.

## Prerequisites

- The runtime host already exists or has been designated.
- The workspace layout in `docs/ai-ops/runtime/workspace-setup.md` is already in place.
- You have normal operator access on the runtime host.
- You are **not** adding OpenStack credentials yet.

## Install baseline packages

Install the host packages for your distro. The exact package manager may vary.

Example package categories:

- Python 3 runtime
- Python virtual environment support
- Python package tooling
- SSH client
- curl
- JSON parser
- fast text search tool
- Git client

Example Debian/Ubuntu-style command:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip openssh-client curl jq ripgrep git
```

If your distro uses different package names, install the equivalent tools.

## Create an isolated Python environment

Create a virtual environment for the AI-OPS tooling:

```bash
python3 -m venv /opt/openstack-ai-ops/.venv
source /opt/openstack-ai-ops/.venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

## Install OpenStack Python tooling

Install the OpenStack client and SDK into the isolated environment:

```bash
python -m pip install openstackclient openstacksdk
```

## Verify baseline versions

Record the versions from the runtime shell or the activated virtual environment:

```bash
python3 --version
python --version
python -m pip --version
openstack --version
python -c 'import openstacksdk; print(openstacksdk.__version__)'
ssh -V
curl --version | head -n 1
jq --version
rg --version | head -n 1
git --version
```

If `openstack --version` or `python -c 'import openstacksdk; ...'` fails because credentials are missing, that is expected in Phase 01. The command should fail for auth reasons, not because the tooling is absent.

## Record evidence

Write the observed versions into one of these places:

- `docs/ai-ops/runtime/README.md`
- a dated note under `docs/ai-ops/runtime/`
- `diagnostics/summaries/` on the runtime host

Capture at minimum:

- tool name
- version output
- date
- runtime host name
- note that OpenStack auth is not yet configured

## Verification checklist

Before moving on, confirm:

- the virtual environment exists
- the OpenStack CLI is available inside the virtual environment
- the OpenStack SDK imports inside the virtual environment
- version outputs were captured
- OpenStack credential failure is auth-related, not missing-tool related

## Stop conditions

Stop and investigate if any of the following are true:

- Python or virtual environment support is missing.
- OpenStack CLI or SDK cannot be installed in the isolated environment.
- Version evidence is not available.
- Credentials were added during Phase 01.
- OpenStack commands fail because the client tooling is missing rather than because credentials are absent.
