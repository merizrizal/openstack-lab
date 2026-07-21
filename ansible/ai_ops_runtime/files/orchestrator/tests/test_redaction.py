"""Tests for fail-closed orchestrator-owned redaction."""

from __future__ import annotations

import pytest

from openstack_ai_ops_orchestrator.contracts import ToolResultCategory
from openstack_ai_ops_orchestrator.redaction import (
    RedactionError,
    redact_operator_context,
    redact_tool_result,
)


def test_operator_context_redacts_canonical_identity_and_secret_labels() -> None:
    result = redact_operator_context(
        "username=phase10-user password=phase10-secret", 8192, 100
    )

    assert result.content == "username=[REDACTED] password=[REDACTED]"
    assert result.classification == "redacted"
    assert result.redaction_count == 2
    assert "phase10-user" not in repr(result)
    assert "phase10-secret" not in repr(result)


@pytest.mark.parametrize(
    "context, category",
    [
        ('{"username":"phase10-user","note":"phase10-user"}', "redacted"),
        (
            '{"password":"phase10-secret","nested":{"message":"phase10-secret"}}',
            "redacted",
        ),
        ('{"username":"first","username":"second"}', "duplicate_json_key"),
        ('{"password":"phase10-secret"', "malformed_json"),
        ("secret phase10-secret", "ambiguous_sensitive_label"),
    ],
)
def test_operator_context_fails_closed_or_removes_protected_values(
    context: str, category: str
) -> None:
    if category == "redacted":
        result = redact_operator_context(context, 8192, 100)
        assert "phase10-user" not in result.content
        assert "phase10-secret" not in result.content
    else:
        with pytest.raises(RedactionError, match=f"^{category}$") as error:
            redact_operator_context(context, 8192, 100)
        assert "phase10-secret" not in repr(error.value)


def test_operator_context_rejects_oversized_content() -> None:
    with pytest.raises(RedactionError, match="^content_too_large$"):
        redact_operator_context("safe", 3, 100)


def test_tool_result_is_redacted_before_safe_factory_and_retains_only_category() -> (
    None
):
    result = redact_tool_result(
        {
            "tool_name": "project_resource_summary",
            "category": "ok",
            "content": '{"username":"phase10-user","note":"phase10-user"}',
            "truncated": False,
            "request_sequence_number": 1,
        },
        maximum_raw_bytes=8192,
        maximum_content_bytes=8192,
        maximum_redactions=100,
    )

    assert result.category is ToolResultCategory.OK
    assert "phase10-user" not in result.redacted_content
    assert result.redaction_count == 3
    assert "phase10-user" not in repr(result)


@pytest.mark.parametrize(
    "raw_result, category",
    [
        (
            {
                "tool_name": "project_resource_summary",
                "category": "ok",
                "content": "safe",
                "truncated": False,
                "request_sequence_number": 1,
            },
            "unsupported_content",
        ),
        (
            {
                "tool_name": "project_resource_summary",
                "category": "unknown",
                "content": "safe",
                "truncated": False,
                "request_sequence_number": 1,
            },
            "invalid_tool_result",
        ),
        (
            {
                "tool_name": "project_resource_summary",
                "category": "ok",
                "content": b"binary",
                "truncated": False,
                "request_sequence_number": 1,
            },
            "invalid_tool_result",
        ),
        (
            {
                "tool_name": "project_resource_summary",
                "category": "ok",
                "content": '{"value":NaN}',
                "truncated": False,
                "request_sequence_number": 1,
            },
            "non_finite_json_number",
        ),
    ],
)
def test_tool_result_rejects_tainted_or_invalid_content(
    raw_result: dict[str, object], category: str
) -> None:
    with pytest.raises(RedactionError, match=f"^{category}$") as error:
        redact_tool_result(
            raw_result,
            maximum_raw_bytes=8192,
            maximum_content_bytes=8192,
            maximum_redactions=100,
        )
    assert "binary" not in repr(error.value)
