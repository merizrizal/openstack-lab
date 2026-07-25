"""Assistant-owned Unix-socket bridge for one reviewed MCP tool call."""

from __future__ import annotations

import asyncio
import json
import socket
import struct
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import cast

from .contracts import ToolCallRequest

_REVIEWED_REQUEST = ToolCallRequest("project_resource_summary", (), 1)
_MAXIMUM_CORRELATION_ID_LENGTH = 128
_MAXIMUM_MESSAGE_BYTES = 270464


class McpBridgeError(RuntimeError):
    """Fixed bridge failure category that never includes tool content."""


@dataclass(frozen=True, slots=True)
class BridgeRequest:
    correlation_id: str
    tool_request: ToolCallRequest

    def __post_init__(self) -> None:
        if (
            not isinstance(self.correlation_id, str)
            or not self.correlation_id
            or len(self.correlation_id) > _MAXIMUM_CORRELATION_ID_LENGTH
        ):
            raise ValueError("bridge correlation is invalid")
        if self.tool_request != _REVIEWED_REQUEST:
            raise ValueError("bridge tool request is not reviewed")


@dataclass(frozen=True, slots=True)
class BridgeResponse:
    correlation_id: str
    request_sequence_number: int
    raw_result: Mapping[str, object]


BridgeExecutor = Callable[[BridgeRequest], Awaitable[BridgeResponse]]


class UnixSocketBridge:
    """Serve only an OS-authenticated Unix peer; never open a TCP listener."""

    def __init__(
        self, *, approved_peer_uid: int, executor: BridgeExecutor, timeout_seconds: int
    ) -> None:
        if (
            isinstance(approved_peer_uid, bool)
            or not isinstance(approved_peer_uid, int)
            or approved_peer_uid < 0
            or isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, int)
            or timeout_seconds < 1
        ):
            raise ValueError("bridge configuration is invalid")
        self._approved_peer_uid = approved_peer_uid
        self._executor = executor
        self._timeout_seconds = timeout_seconds
        self._closed = False

    async def serve(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle one framed request from an accepted Unix-domain connection."""
        try:
            peer_socket = cast(socket.socket, writer.get_extra_info("socket"))
            request = self._decode_request(await self._read_message(reader))
            response = await self.call(peer_socket, request)
            await self._write_message(
                writer,
                {
                    "correlation_id": response.correlation_id,
                    "request_sequence_number": response.request_sequence_number,
                    "raw_result": response.raw_result,
                },
            )
        except (McpBridgeError, ValueError, json.JSONDecodeError, OSError):
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    async def call(
        self, peer_socket: socket.socket, request: BridgeRequest
    ) -> BridgeResponse:
        if self._closed or self._peer_uid(peer_socket) != self._approved_peer_uid:
            raise McpBridgeError("bridge_peer_denied")
        try:
            response = await asyncio.wait_for(
                self._executor(request), timeout=self._timeout_seconds
            )
        except (TimeoutError, asyncio.CancelledError):
            raise McpBridgeError("bridge_timed_out") from None
        except Exception:
            raise McpBridgeError("bridge_execution_failed") from None
        if (
            response.correlation_id != request.correlation_id
            or response.request_sequence_number != request.tool_request.sequence_number
            or not isinstance(response.raw_result, Mapping)
        ):
            raise McpBridgeError("bridge_correlation_mismatch")
        return response

    async def aclose(self) -> None:
        self._closed = True

    @staticmethod
    def _peer_uid(peer_socket: socket.socket) -> int:
        if peer_socket.family != socket.AF_UNIX or not hasattr(socket, "SO_PEERCRED"):
            raise McpBridgeError("bridge_peer_denied")
        try:
            credentials = peer_socket.getsockopt(
                socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i")
            )
            _pid, uid, _gid = struct.unpack("3i", credentials)
        except (OSError, struct.error):
            raise McpBridgeError("bridge_peer_denied") from None
        return int(uid)

    @staticmethod
    async def _read_message(reader: asyncio.StreamReader) -> bytes:
        message = await reader.readuntil(b"\n")
        if not message or len(message) > _MAXIMUM_MESSAGE_BYTES:
            raise McpBridgeError("bridge_message_invalid")
        return message[:-1]

    @staticmethod
    async def _write_message(
        writer: asyncio.StreamWriter, value: Mapping[str, object]
    ) -> None:
        encoded = json.dumps(value, separators=(",", ":")).encode("utf-8")
        if len(encoded) > _MAXIMUM_MESSAGE_BYTES:
            raise McpBridgeError("bridge_message_invalid")
        writer.write(encoded + b"\n")
        await writer.drain()

    @staticmethod
    def _decode_request(message: bytes) -> BridgeRequest:
        value = json.loads(message)
        if not isinstance(value, Mapping) or set(value) != {"correlation_id", "tool"}:
            raise ValueError("bridge request is invalid")
        correlation_id, tool = value["correlation_id"], value["tool"]
        if not isinstance(correlation_id, str) or not isinstance(tool, Mapping):
            raise ValueError("bridge request is invalid")
        return BridgeRequest(correlation_id, ToolCallRequest.from_mapping(tool))
