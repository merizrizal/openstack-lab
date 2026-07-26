#!/usr/bin/env python3
"""Assistant-owned factory for the reviewed local MCP bridge."""

from __future__ import annotations

import argparse
import asyncio
import os
import socket
from collections.abc import Mapping, Sequence

from aiops_mcp_server import (
    AdapterPaths,
    default_adapter_paths,
    invoke_runner,
    new_request_id,
)
from openstack_ai_ops_orchestrator.contracts import RuntimePolicy, ToolCallRequest
from openstack_ai_ops_orchestrator.mcp_bridge import (
    AssistantBridgeExecutor,
    AssistantRunnerBridgeAdapter,
    UnixSocketBridge,
)


async def _invoke_existing_runner(
    request: ToolCallRequest,
    request_id: str,
    *,
    paths: AdapterPaths,
    timeout_seconds: int,
) -> Mapping[str, object]:
    """Delegate only to the established assistant-owned runner contract."""
    return await invoke_runner(
        request.tool_name,
        dict(request.arguments),
        request_id,
        paths,
        timeout_seconds,
    )


def create_assistant_bridge(
    *,
    approved_peer_uid: int,
    policy: RuntimePolicy,
    paths: AdapterPaths | None = None,
) -> UnixSocketBridge:
    """Build the fixed bridge without creating a listener or runner path."""
    resolved_paths = default_adapter_paths() if paths is None else paths

    async def runner(request: ToolCallRequest, request_id: str) -> Mapping[str, object]:
        return await _invoke_existing_runner(
            request,
            request_id,
            paths=resolved_paths,
            timeout_seconds=policy.per_tool_call_timeout_seconds,
        )

    adapter = AssistantRunnerBridgeAdapter(
        runner=runner,
        request_id_factory=new_request_id,
    )
    executor = AssistantBridgeExecutor(policy=policy, runner=adapter)
    return UnixSocketBridge(
        approved_peer_uid=approved_peer_uid,
        executor=executor,
        timeout_seconds=policy.per_tool_call_timeout_seconds,
    )

_FIXED_BRIDGE_POLICY = RuntimePolicy(
    deadline_seconds=30,
    maximum_event_count=3,
    maximum_output_bytes=1024,
    model_alias="assistant-mcp-bridge",
    fixed_working_directory="/opt/openstack-ai-ops",
)
_SYSTEMD_LISTEN_FD = 3


def activated_unix_listener() -> socket.socket:
    """Take exactly one Unix-stream listener inherited from systemd."""
    if (
        os.environ.get("LISTEN_PID") != str(os.getpid())
        or os.environ.get("LISTEN_FDS") != "1"
    ):
        raise RuntimeError("assistant bridge requires one activated listener")
    listener = socket.socket(fileno=_SYSTEMD_LISTEN_FD)
    try:
        if (
            listener.family != socket.AF_UNIX
            or listener.type != socket.SOCK_STREAM
            or not listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN)
        ):
            raise RuntimeError("assistant bridge listener is invalid")
    except Exception:
        listener.close()
        raise
    return listener


async def run_activated_bridge(
    *,
    approved_peer_uid: int,
    listener: socket.socket | None = None,
    paths: AdapterPaths | None = None,
) -> None:
    """Serve only the inherited Unix listener until systemd stops this service."""
    bridge = create_assistant_bridge(
        approved_peer_uid=approved_peer_uid,
        policy=_FIXED_BRIDGE_POLICY,
        paths=paths,
    )
    activated_listener = activated_unix_listener() if listener is None else listener
    server = await asyncio.start_unix_server(bridge.serve, sock=activated_listener)
    try:
        async with server:
            await server.serve_forever()
    finally:
        await bridge.aclose()


def main(arguments: Sequence[str] | None = None) -> int:
    """Run the reviewed socket-activated bridge with a root-supplied peer UID."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--approved-peer-uid", type=int, required=True)
    parsed = parser.parse_args(arguments)
    asyncio.run(run_activated_bridge(approved_peer_uid=parsed.approved_peer_uid))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
