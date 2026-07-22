from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest

from openstack_ai_ops_orchestrator.contracts import RuntimePolicy, ToolCallRequest
from openstack_ai_ops_orchestrator.mcp_client import (
    LocalMcpClient,
    McpClientContractError,
)


def policy() -> RuntimePolicy:
    return RuntimePolicy(60, 5, 8192, "model", "/fixed")


class Fake:
    def __init__(
        self,
        tools=("project_resource_summary", "server_basic_info", "server_network_info"),
    ) -> None:
        self.closed = False
        self.tools = tools

    async def initialize(self) -> None:
        pass

    async def list_tools(self):
        return SimpleNamespace(tools=[SimpleNamespace(name=x) for x in self.tools])

    async def list_resources(self):
        return SimpleNamespace(
            resources=[
                SimpleNamespace(uri=x)
                for x in (
                    "aiops://architecture/lab-summary",
                    "aiops://policy/diagnostic-safety",
                    "aiops://runbooks/metadata-troubleshooting",
                )
            ]
        )

    async def list_prompts(self):
        return SimpleNamespace(
            prompts=[
                SimpleNamespace(name=x)
                for x in ("metadata_diagnosis", "project_summary", "server_inspection")
            ]
        )

    async def call_tool(self, n, a):
        return {"name": n, "arguments": a}


@asynccontextmanager
async def context(fake):
    try:
        yield fake
    finally:
        fake.closed = True


def test_fixed_client_validates_and_closes_fixture() -> None:
    fake = Fake()

    async def run():
        async with LocalMcpClient(
            policy(), session_factory=lambda: context(fake)
        ) as client:
            assert await client.call_tool(
                ToolCallRequest("project_resource_summary", (), 1)
            ) == {"name": "project_resource_summary", "arguments": {}}

    asyncio.run(run())
    assert fake.closed


def test_capability_drift_closes_fixture() -> None:
    fake = Fake(("project_resource_summary",))

    async def run():
        with pytest.raises(McpClientContractError, match="MCP contract failed"):
            async with LocalMcpClient(policy(), session_factory=lambda: context(fake)):
                pass

    asyncio.run(run())
    assert fake.closed
