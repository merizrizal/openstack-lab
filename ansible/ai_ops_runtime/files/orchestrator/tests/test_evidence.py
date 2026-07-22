"""Tests for standalone, metadata-only orchestrator evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

import pytest

from openstack_ai_ops_orchestrator.contracts import ToolResultCategory, WorkflowState
from openstack_ai_ops_orchestrator.evidence import (
    BoundedJsonlEvidenceWriter,
    CleanupOutcome,
    EvidenceError,
    EvidenceEventCategory,
    EvidenceWriteError,
    OrchestratorEvidenceRecord,
    TruncationOutcome,
    parse_evidence_record,
    serialize_evidence_record,
    validate_evidence_sequence,
)
from openstack_ai_ops_orchestrator.redaction import RedactionCategory

MAXIMUM_RECORD_BYTES = 4096
MAXIMUM_LEDGER_BYTES = 65536


class _CommonRecordFields(TypedDict):
    schema_version: int
    timestamp: str
    correlation_id: str
    workflow: str
    event_category: EvidenceEventCategory
    input_classification: RedactionCategory
    event_count: int
    turn_count: int
    tool_call_count: int
    redaction_count: int
    content_bytes: int


def record(
    event_category: EvidenceEventCategory,
    *,
    timestamp: str,
    event_count: int,
) -> OrchestratorEvidenceRecord:
    common: _CommonRecordFields = {
        "schema_version": 1,
        "timestamp": timestamp,
        "correlation_id": "phase10-correlation",
        "workflow": "project_resource_summary",
        "event_category": event_category,
        "input_classification": RedactionCategory.REDACTED,
        "event_count": event_count,
        "turn_count": 1 if event_count > 1 else 0,
        "tool_call_count": 1 if event_count > 1 else 0,
        "redaction_count": 2 if event_count > 1 else 0,
        "content_bytes": 32 if event_count > 1 else 0,
    }
    if event_category is EvidenceEventCategory.WORKFLOW_STARTED:
        return OrchestratorEvidenceRecord(
            **common,
            workflow_state=WorkflowState.RUNNING,
            error_category=None,
            tool_name=None,
            result_category=None,
            truncation_outcome=TruncationOutcome.NOT_APPLICABLE,
            cleanup_outcome=CleanupOutcome.NOT_APPLICABLE,
        )
    if event_category is EvidenceEventCategory.TOOL_COMPLETED:
        return OrchestratorEvidenceRecord(
            **common,
            workflow_state=WorkflowState.RUNNING,
            error_category=None,
            tool_name="project_resource_summary",
            result_category=ToolResultCategory.OK,
            truncation_outcome=TruncationOutcome.NOT_TRUNCATED,
            cleanup_outcome=CleanupOutcome.NOT_APPLICABLE,
        )
    return OrchestratorEvidenceRecord(
        **common,
        workflow_state=WorkflowState.COMPLETED,
        error_category=None,
        tool_name=None,
        result_category=None,
        truncation_outcome=TruncationOutcome.NOT_APPLICABLE,
        cleanup_outcome=CleanupOutcome.CLEAN,
    )


def lifecycle() -> tuple[OrchestratorEvidenceRecord, ...]:
    return (
        record(
            EvidenceEventCategory.WORKFLOW_STARTED,
            timestamp="2026-01-01T00:00:00Z",
            event_count=1,
        ),
        record(
            EvidenceEventCategory.TOOL_COMPLETED,
            timestamp="2026-01-01T00:00:01Z",
            event_count=2,
        ),
        record(
            EvidenceEventCategory.WORKFLOW_TERMINAL,
            timestamp="2026-01-01T00:00:02Z",
            event_count=3,
        ),
    )


def test_evidence_record_round_trips_with_exact_metadata_fields() -> None:
    original = lifecycle()[1]
    serialized = serialize_evidence_record(original)
    parsed = parse_evidence_record(serialized, MAXIMUM_RECORD_BYTES)

    assert parsed == original
    assert set(json.loads(serialized)) == {
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
    for forbidden in ("prompt", "context", "arguments", "output", "secret"):
        assert forbidden not in serialized


@pytest.mark.parametrize(
    "serialized",
    [
        '{"schema_version":1,"schema_version":1}',
        '{"schema_version":2}',
        '{"phase10-secret":"value"}',
        "not-json",
    ],
)
def test_parser_rejects_malformed_extra_duplicate_and_unsupported_records(
    serialized: str,
) -> None:
    with pytest.raises(EvidenceError, match="^invalid_evidence$") as error:
        parse_evidence_record(serialized, MAXIMUM_RECORD_BYTES)

    assert "phase10-secret" not in repr(error.value)


def test_parser_rejects_oversized_record() -> None:
    with pytest.raises(EvidenceError, match="^invalid_evidence$"):
        parse_evidence_record("x" * (MAXIMUM_RECORD_BYTES + 1), MAXIMUM_RECORD_BYTES)


def test_sequence_accepts_only_start_tool_completion_terminal() -> None:
    valid = lifecycle()
    validate_evidence_sequence(valid)

    with pytest.raises(EvidenceError, match="^invalid_evidence$"):
        validate_evidence_sequence((valid[0], valid[2]))
    with pytest.raises(EvidenceError, match="^invalid_evidence$"):
        validate_evidence_sequence((valid[1], valid[2]))


def test_sequence_rejects_non_monotonic_counters() -> None:
    started, tool_completed, terminal = lifecycle()
    invalid_terminal = OrchestratorEvidenceRecord(
        schema_version=terminal.schema_version,
        timestamp=terminal.timestamp,
        correlation_id=terminal.correlation_id,
        workflow=terminal.workflow,
        event_category=terminal.event_category,
        workflow_state=terminal.workflow_state,
        error_category=terminal.error_category,
        input_classification=terminal.input_classification,
        tool_name=terminal.tool_name,
        result_category=terminal.result_category,
        event_count=terminal.event_count,
        turn_count=terminal.turn_count,
        tool_call_count=0,
        redaction_count=terminal.redaction_count,
        content_bytes=terminal.content_bytes,
        truncation_outcome=terminal.truncation_outcome,
        cleanup_outcome=terminal.cleanup_outcome,
    )

    with pytest.raises(EvidenceError, match="^invalid_evidence$"):
        validate_evidence_sequence((started, tool_completed, invalid_terminal))


def test_bounded_writer_validates_lifecycle_before_appending(tmp_path: Path) -> None:
    path = tmp_path / "evidence.jsonl"
    writer = BoundedJsonlEvidenceWriter(
        path, MAXIMUM_RECORD_BYTES, MAXIMUM_LEDGER_BYTES
    )
    records = lifecycle()

    for item in records:
        writer.append(item)

    assert tuple(path.read_text().splitlines()) == tuple(
        serialize_evidence_record(item) for item in records
    )


def test_writer_fails_closed_without_writing_invalid_or_unavailable_ledger(
    tmp_path: Path,
) -> None:
    path = tmp_path / "evidence.jsonl"
    writer = BoundedJsonlEvidenceWriter(
        path, MAXIMUM_RECORD_BYTES, MAXIMUM_LEDGER_BYTES
    )

    with pytest.raises(EvidenceWriteError, match="^evidence_write_failed$") as error:
        writer.append(lifecycle()[1])
    assert not path.exists()
    assert str(path) not in repr(error.value)

    unavailable = BoundedJsonlEvidenceWriter(
        tmp_path / "missing" / "evidence.jsonl",
        MAXIMUM_RECORD_BYTES,
        MAXIMUM_LEDGER_BYTES,
    )
    with pytest.raises(EvidenceWriteError, match="^evidence_write_failed$"):
        unavailable.append(lifecycle()[0])
