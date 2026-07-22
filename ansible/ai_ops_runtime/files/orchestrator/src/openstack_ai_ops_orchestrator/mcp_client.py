"""Fixed local stdio MCP client with exact discovery and bounded cleanup."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager, AsyncExitStack
from typing import Protocol

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .contracts import (
    FIXED_MCP_ARGUMENTS,
    FIXED_MCP_COMMAND,
    REVIEWED_MCP_CAPABILITIES,
    RuntimePolicy,
    ToolCallRequest,
)


class McpClientContractError(RuntimeError):
    """Fixed error for failed local MCP policy or lifecycle checks."""


class _Session(Protocol):
    async def initialize(self) -> object: ...
    async def list_tools(self) -> object: ...
    async def list_resources(self) -> object: ...
    async def list_prompts(self) -> object: ...
    async def call_tool(self, name: str, arguments: dict[str, str]) -> object: ...


class LocalMcpClient:
    def __init__(
        self,
        policy: RuntimePolicy,
        *,
        session_factory: Callable[[], AbstractAsyncContextManager[_Session]]
        | None = None,
    ) -> None:
        self._policy = policy
        self._factory = session_factory
        self._stack: AsyncExitStack | None = None
        self._session: _Session | None = None

    async def __aenter__(self) -> LocalMcpClient:
        stack = AsyncExitStack()
        session: _Session
        try:
            if self._factory is None:
                streams = await stack.enter_async_context(
                    stdio_client(
                        StdioServerParameters(
                            command=FIXED_MCP_COMMAND, args=list(FIXED_MCP_ARGUMENTS)
                        )
                    )
                )
                session = await stack.enter_async_context(ClientSession(*streams))
            else:
                session = await stack.enter_async_context(self._factory())
            await session.initialize()
            await self._validate(session)
        except Exception:
            await stack.aclose()
            raise McpClientContractError("MCP contract failed") from None
        self._stack, self._session = stack, session
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        del exc_type, exc, traceback
        if self._stack is not None:
            await self._stack.aclose()
        self._stack = None
        self._session = None

    async def call_tool(self, request: ToolCallRequest) -> object:
        if (
            self._session is None
            or request.tool_name not in REVIEWED_MCP_CAPABILITIES.tools
        ):
            raise McpClientContractError("MCP tool call denied")
        return await asyncio.wait_for(
            self._session.call_tool(request.tool_name, dict(request.arguments)),
            timeout=self._policy.per_tool_call_timeout_seconds,
        )

    async def _validate(self, session: _Session) -> None:
        tools, resources, prompts = await asyncio.gather(
            session.list_tools(), session.list_resources(), session.list_prompts()
        )
        self._assert_names(
            getattr(tools, "tools", ()), "name", REVIEWED_MCP_CAPABILITIES.tools
        )
        self._assert_names(
            getattr(resources, "resources", ()),
            "uri",
            REVIEWED_MCP_CAPABILITIES.resources,
        )
        self._assert_names(
            getattr(prompts, "prompts", ()), "name", REVIEWED_MCP_CAPABILITIES.prompts
        )

    @staticmethod
    def _assert_names(
        values: object, attribute: str, expected: tuple[str, ...]
    ) -> None:
        names = (
            tuple(sorted(str(getattr(value, attribute, "")) for value in values))
            if isinstance(values, list | tuple)
            else ()
        )
        if names != expected:
            raise McpClientContractError("MCP capability drift")
