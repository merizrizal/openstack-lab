"""Strict, metadata-only evidence records for local orchestrator workflows."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final, Protocol, cast

from .contracts import (
    TERMINAL_WORKFLOW_STATES,
    AdapterErrorCategory,
    ToolResultCategory,
    WorkflowState,
)
from .redaction import RedactionCategory

EVIDENCE_SCHEMA_VERSION: Final = 1
MAXIMUM_EVIDENCE_IDENTIFIER_LENGTH: Final = 128
MAXIMUM_EVIDENCE_COUNTER: Final = 1_000_000
REVIEWED_EVIDENCE_WORKFLOWS: Final = frozenset({"project_resource_summary"})


class EvidenceEventCategory(StrEnum):
    """The only lifecycle entries retained in an evidence ledger."""

    WORKFLOW_STARTED = "workflow_started"
    TOOL_COMPLETED = "tool_completed"
    WORKFLOW_TERMINAL = "workflow_terminal"


class TruncationOutcome(StrEnum):
    """Metadata-only result truncation classification."""

    NOT_APPLICABLE = "not_applicable"
    NOT_TRUNCATED = "not_truncated"
    TRUNCATED = "truncated"


class CleanupOutcome(StrEnum):
    """Metadata-only cleanup classification."""

    NOT_APPLICABLE = "not_applicable"
    CLEAN = "clean"
    FAILED = "failed"


class EvidenceError(ValueError):
    """Fixed validation category that never includes rejected data."""

    def __init__(self, category: str = "invalid_evidence") -> None:
        self.category = category
        super().__init__(category)


class EvidenceWriteError(RuntimeError):
    """Fixed writer category that never exposes a path or I/O detail."""

    def __init__(self) -> None:
        super().__init__("evidence_write_failed")


_TIMESTAMP_RE: Final = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
_IDENTIFIER_RE: Final = re.compile(r"[A-Za-z0-9_-]+")
_RECORD_FIELDS: Final = frozenset(
    {
        "schema_version",
        "timestamp",
        "correlation_id",
        "workflow",
        "event_category",
        "workflow_state",
        "error_category",
        "input_classification",
        "tool_name",
        "result_category",
        "event_count",
        "turn_count",
        "tool_call_count",
        "redaction_count",
        "content_bytes",
        "truncation_outcome",
        "cleanup_outcome",
    }
)


@dataclass(frozen=True, slots=True)
class OrchestratorEvidenceRecord:
    """One exact, bounded, content-free schema-version-1 lifecycle record."""

    schema_version: int
    timestamp: str
    correlation_id: str
    workflow: str
    event_category: EvidenceEventCategory
    workflow_state: WorkflowState
    error_category: AdapterErrorCategory | None
    input_classification: RedactionCategory
    tool_name: str | None
    result_category: ToolResultCategory | None
    event_count: int
    turn_count: int
    tool_call_count: int
    redaction_count: int
    content_bytes: int
    truncation_outcome: TruncationOutcome
    cleanup_outcome: CleanupOutcome

    def __post_init__(self) -> None:
        if self.schema_version != EVIDENCE_SCHEMA_VERSION:
            raise EvidenceError()
        if not isinstance(self.timestamp, str) or not _TIMESTAMP_RE.fullmatch(
            self.timestamp
        ):
            raise EvidenceError()
        if (
            not isinstance(self.correlation_id, str)
            or not (1 <= len(self.correlation_id) <= MAXIMUM_EVIDENCE_IDENTIFIER_LENGTH)
            or not _IDENTIFIER_RE.fullmatch(self.correlation_id)
        ):
            raise EvidenceError()
        if self.workflow not in REVIEWED_EVIDENCE_WORKFLOWS:
            raise EvidenceError()
        if not isinstance(self.event_category, EvidenceEventCategory) or not isinstance(
            self.workflow_state, WorkflowState
        ):
            raise EvidenceError()
        if self.error_category is not None and not isinstance(
            self.error_category, AdapterErrorCategory
        ):
            raise EvidenceError()
        if not isinstance(self.input_classification, RedactionCategory):
            raise EvidenceError()
        if self.tool_name is not None and self.tool_name != self.workflow:
            raise EvidenceError()
        if self.result_category is not None and not isinstance(
            self.result_category, ToolResultCategory
        ):
            raise EvidenceError()
        counters = (
            self.event_count,
            self.turn_count,
            self.tool_call_count,
            self.redaction_count,
            self.content_bytes,
        )
        if any(
            isinstance(counter, bool)
            or not isinstance(counter, int)
            or not 0 <= counter <= MAXIMUM_EVIDENCE_COUNTER
            for counter in counters
        ):
            raise EvidenceError()
        if not isinstance(self.truncation_outcome, TruncationOutcome) or not isinstance(
            self.cleanup_outcome, CleanupOutcome
        ):
            raise EvidenceError()
        self._validate_event_shape()

    def _validate_event_shape(self) -> None:
        if self.event_category is EvidenceEventCategory.WORKFLOW_STARTED:
            if (
                self.workflow_state is not WorkflowState.RUNNING
                or self.error_category is not None
                or self.tool_name is not None
                or self.result_category is not None
                or self.truncation_outcome is not TruncationOutcome.NOT_APPLICABLE
                or self.cleanup_outcome is not CleanupOutcome.NOT_APPLICABLE
                or (self.event_count, self.turn_count, self.tool_call_count)
                != (1, 0, 0)
                or self.redaction_count != 0
                or self.content_bytes != 0
            ):
                raise EvidenceError()
        elif self.event_category is EvidenceEventCategory.TOOL_COMPLETED:
            if (
                self.workflow_state is not WorkflowState.RUNNING
                or self.error_category is not None
                or self.tool_name is None
                or self.result_category is None
                or self.truncation_outcome is TruncationOutcome.NOT_APPLICABLE
                or self.cleanup_outcome is not CleanupOutcome.NOT_APPLICABLE
            ):
                raise EvidenceError()
        elif self.event_category is EvidenceEventCategory.WORKFLOW_TERMINAL:
            if (
                self.workflow_state not in TERMINAL_WORKFLOW_STATES
                or self.tool_name is not None
                or self.result_category is not None
                or self.truncation_outcome is not TruncationOutcome.NOT_APPLICABLE
                or self.cleanup_outcome is CleanupOutcome.NOT_APPLICABLE
                or (
                    self.workflow_state is WorkflowState.COMPLETED
                    and self.error_category is not None
                )
            ):
                raise EvidenceError()
        else:
            raise EvidenceError()


def serialize_evidence_record(record: OrchestratorEvidenceRecord) -> str:
    """Serialize only a validated evidence record with its exact field allowlist."""
    if not isinstance(record, OrchestratorEvidenceRecord):
        raise EvidenceError()
    serialized = json.dumps(
        {
            "schema_version": record.schema_version,
            "timestamp": record.timestamp,
            "correlation_id": record.correlation_id,
            "workflow": record.workflow,
            "event_category": record.event_category,
            "workflow_state": record.workflow_state,
            "error_category": record.error_category,
            "input_classification": record.input_classification,
            "tool_name": record.tool_name,
            "result_category": record.result_category,
            "event_count": record.event_count,
            "turn_count": record.turn_count,
            "tool_call_count": record.tool_call_count,
            "redaction_count": record.redaction_count,
            "content_bytes": record.content_bytes,
            "truncation_outcome": record.truncation_outcome,
            "cleanup_outcome": record.cleanup_outcome,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    parse_evidence_record(serialized, len(serialized.encode("utf-8")))
    return serialized


def parse_evidence_record(
    serialized: str, maximum_record_bytes: int
) -> OrchestratorEvidenceRecord:
    """Strictly parse one serialized record, rejecting duplicate keys and drift."""
    if (
        not isinstance(serialized, str)
        or isinstance(maximum_record_bytes, bool)
        or not isinstance(maximum_record_bytes, int)
        or maximum_record_bytes < 1
        or len(serialized.encode("utf-8")) > maximum_record_bytes
    ):
        raise EvidenceError()

    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        parsed: dict[str, object] = {}
        for key, value in pairs:
            if key in parsed:
                raise EvidenceError()
            parsed[key] = value
        return parsed

    try:
        value: object = json.loads(serialized, object_pairs_hook=reject_duplicates)
    except (TypeError, json.JSONDecodeError) as error:
        raise EvidenceError() from error
    if not isinstance(value, dict) or set(value) != _RECORD_FIELDS:
        raise EvidenceError()
    return OrchestratorEvidenceRecord(
        schema_version=_integer(value["schema_version"]),
        timestamp=_string(value["timestamp"]),
        correlation_id=_string(value["correlation_id"]),
        workflow=_string(value["workflow"]),
        event_category=cast(
            EvidenceEventCategory,
            _enum(value["event_category"], EvidenceEventCategory),
        ),
        workflow_state=cast(
            WorkflowState, _enum(value["workflow_state"], WorkflowState)
        ),
        error_category=cast(
            AdapterErrorCategory | None,
            _optional_enum(value["error_category"], AdapterErrorCategory),
        ),
        input_classification=cast(
            RedactionCategory,
            _enum(value["input_classification"], RedactionCategory),
        ),
        tool_name=_optional_string(value["tool_name"]),
        result_category=cast(
            ToolResultCategory | None,
            _optional_enum(value["result_category"], ToolResultCategory),
        ),
        event_count=_integer(value["event_count"]),
        turn_count=_integer(value["turn_count"]),
        tool_call_count=_integer(value["tool_call_count"]),
        redaction_count=_integer(value["redaction_count"]),
        content_bytes=_integer(value["content_bytes"]),
        truncation_outcome=cast(
            TruncationOutcome,
            _enum(value["truncation_outcome"], TruncationOutcome),
        ),
        cleanup_outcome=cast(
            CleanupOutcome,
            _enum(value["cleanup_outcome"], CleanupOutcome),
        ),
    )


def validate_evidence_sequence(records: Sequence[OrchestratorEvidenceRecord]) -> None:
    """Require one bounded start/tool-completion/terminal evidence lifecycle."""
    _validate_evidence_prefix(records)
    if records[-1].event_category is not EvidenceEventCategory.WORKFLOW_TERMINAL:
        raise EvidenceError()


def _validate_evidence_prefix(records: Sequence[OrchestratorEvidenceRecord]) -> None:
    """Validate an appendable lifecycle prefix without requiring its terminal entry."""
    if not records:
        raise EvidenceError()
    previous: OrchestratorEvidenceRecord | None = None
    for index, record in enumerate(records):
        if not isinstance(record, OrchestratorEvidenceRecord):
            raise EvidenceError()
        if index == 0:
            if record.event_category is not EvidenceEventCategory.WORKFLOW_STARTED:
                raise EvidenceError()
        elif record.event_category is EvidenceEventCategory.WORKFLOW_TERMINAL:
            if index != len(records) - 1:
                raise EvidenceError()
        elif record.event_category is not EvidenceEventCategory.TOOL_COMPLETED:
            raise EvidenceError()
        if previous is not None:
            _validate_monotonic(previous, record)
        previous = record


def _validate_monotonic(
    previous: OrchestratorEvidenceRecord, current: OrchestratorEvidenceRecord
) -> None:
    if (
        current.correlation_id != previous.correlation_id
        or current.workflow != previous.workflow
        or current.timestamp < previous.timestamp
        or current.event_count != previous.event_count + 1
        or current.turn_count < previous.turn_count
        or current.tool_call_count < previous.tool_call_count
        or current.redaction_count < previous.redaction_count
        or current.content_bytes < previous.content_bytes
    ):
        raise EvidenceError()
    if current.event_category is EvidenceEventCategory.TOOL_COMPLETED and (
        current.tool_call_count != previous.tool_call_count + 1
    ):
        raise EvidenceError()


class EvidenceWriter(Protocol):
    """Injected append-only contract for already-safe evidence records."""

    def append(self, record: OrchestratorEvidenceRecord) -> None:
        """Validate and append one record or raise a fixed writer error."""


class BoundedJsonlEvidenceWriter:
    """Test-only local JSONL writer with record and total-ledger byte bounds."""

    def __init__(
        self, path: Path, maximum_record_bytes: int, maximum_ledger_bytes: int
    ) -> None:
        if (
            not isinstance(path, Path)
            or isinstance(maximum_record_bytes, bool)
            or not isinstance(maximum_record_bytes, int)
            or isinstance(maximum_ledger_bytes, bool)
            or not isinstance(maximum_ledger_bytes, int)
            or maximum_record_bytes < 1
            or maximum_record_bytes > maximum_ledger_bytes
        ):
            raise EvidenceError()
        self._path = path
        self._maximum_record_bytes = maximum_record_bytes
        self._maximum_ledger_bytes = maximum_ledger_bytes

    def append(self, record: OrchestratorEvidenceRecord) -> None:
        """Serialize, parse, sequence-check, then append one bounded JSONL entry."""
        try:
            serialized = serialize_evidence_record(record)
            encoded = (serialized + "\n").encode("utf-8")
            if len(encoded) > self._maximum_record_bytes:
                raise EvidenceError()
            existing = self._path.read_bytes() if self._path.exists() else b""
            if len(existing) + len(encoded) > self._maximum_ledger_bytes:
                raise EvidenceError()
            records = _parse_ledger(existing, self._maximum_record_bytes)
            prospective = (*records, parse_evidence_record(serialized, len(encoded)))
            _validate_evidence_prefix(prospective)
            with self._path.open("ab") as ledger:
                if ledger.write(encoded) != len(encoded):
                    raise OSError("short write")
                ledger.flush()
                os.fsync(ledger.fileno())
        except (EvidenceError, OSError, UnicodeError):
            raise EvidenceWriteError() from None


def _parse_ledger(
    existing: bytes, maximum_record_bytes: int
) -> tuple[OrchestratorEvidenceRecord, ...]:
    if not existing:
        return ()
    if not existing.endswith(b"\n"):
        raise EvidenceError()
    try:
        lines = existing.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise EvidenceError() from error
    return tuple(parse_evidence_record(line, maximum_record_bytes) for line in lines)


def _string(value: object) -> str:
    if not isinstance(value, str):
        raise EvidenceError()
    return value


def _optional_string(value: object) -> str | None:
    if value is not None and not isinstance(value, str):
        raise EvidenceError()
    return value


def _integer(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise EvidenceError()
    return value


def _enum(value: object, enum_type: type[StrEnum]) -> StrEnum:
    if not isinstance(value, str):
        raise EvidenceError()
    try:
        return enum_type(value)
    except ValueError as error:
        raise EvidenceError() from error


def _optional_enum(value: object, enum_type: type[StrEnum]) -> StrEnum | None:
    if value is None:
        return None
    return _enum(value, enum_type)
