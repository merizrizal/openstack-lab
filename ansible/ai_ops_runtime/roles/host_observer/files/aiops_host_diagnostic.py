#!/usr/bin/env python3
import json
import os
import re
import shlex
import subprocess
import sys
from collections import deque
from pathlib import Path
from typing import Any, Callable, TextIO

COMMAND_NAME = "aiops-host-diagnostic"
ALLOWED_KINDS = frozenset({"metadata", "nova", "neutron"})
WINDOW_SINCE = {
    "15m": "15 minutes ago",
    "30m": "30 minutes ago",
    "1h": "1 hour ago",
}
SECTION_LINE_LIMIT = 200
PAYLOAD_BYTE_LIMIT = 49_152
COMMAND_TIMEOUT_SECONDS = 10
REDACTED_VALUE = "[REDACTED]"
REDACTION_PATTERN = re.compile(
    r"(?i)\b(password|passwd|token|secret|api[_-]?key|private[_-]?key)\b\s*([=:])\s*([^\s,;]+)"
)
SOURCE_MAPS = {
    "metadata": {
        "units": ("neutron-metadata-agent", "apache2"),
        "log_patterns": (
            "/var/log/neutron/neutron-metadata-agent.log",
            "/var/log/apache2/nova_metadata_error.log",
            "/var/log/apache2/nova_metadata_access.log",
        ),
        "match_terms": (
            "metadata",
            "proxy",
            "timeout",
            "bad gateway",
            "169.254.169.254",
        ),
        "port": 8775,
    },
    "nova": {
        "units": (
            "nova-scheduler",
            "nova-conductor",
            "nova-novncproxy",
            "nova-compute",
        ),
        "log_patterns": ("/var/log/nova/*.log",),
        "match_terms": ("error", "exception", "traceback", "timeout"),
        "port": None,
    },
    "neutron": {
        "units": (
            "neutron-rpc-server",
            "neutron-l3-agent",
            "neutron-openvswitch-agent",
            "neutron-dhcp-agent",
            "neutron-metadata-agent",
        ),
        "log_patterns": ("/var/log/neutron/*.log",),
        "match_terms": ("error", "exception", "traceback", "timeout"),
        "port": None,
    },
}
FIXED_UNITS = frozenset(
    unit for source_map in SOURCE_MAPS.values() for unit in source_map["units"]
)
RunCommand = Callable[..., subprocess.CompletedProcess[str]]


def parse_forced_command(original_command: str) -> tuple[str, str]:
    if not isinstance(original_command, str) or not original_command.strip():
        raise ValueError("forced command must not be empty")
    try:
        tokens = shlex.split(original_command, posix=True, comments=False)
    except ValueError as exc:
        raise ValueError("forced command is malformed") from exc
    if len(tokens) != 3 or tokens[0] != COMMAND_NAME:
        raise ValueError("forced command must use the approved diagnostic grammar")
    return validate_kind_and_window(tokens[1], tokens[2])


def validate_kind_and_window(kind: str, time_window: str) -> tuple[str, str]:
    if kind not in ALLOWED_KINDS:
        raise ValueError("diagnostic kind is not allowed")
    if time_window not in WINDOW_SINCE:
        raise ValueError("time window is not allowed")
    return kind, time_window


def build_fixed_journal_argv(unit: str, time_window: str, line_limit: int) -> list[str]:
    if time_window not in WINDOW_SINCE:
        raise ValueError("time window is not allowed")
    if unit not in FIXED_UNITS:
        raise ValueError("journal unit is not allowed")
    if (
        isinstance(line_limit, bool)
        or not isinstance(line_limit, int)
        or not 1 <= line_limit <= SECTION_LINE_LIMIT
    ):
        raise ValueError("journal line limit is not allowed")
    return [
        "journalctl",
        "--no-pager",
        "--output=short-iso",
        "--since",
        WINDOW_SINCE[time_window],
        "--unit",
        unit,
        "--lines",
        str(line_limit),
    ]


def collect_fixed_log_tail(path: Path, line_limit: int) -> dict[str, Any]:
    if (
        isinstance(line_limit, bool)
        or not isinstance(line_limit, int)
        or not 1 <= line_limit <= SECTION_LINE_LIMIT
    ):
        raise ValueError("log line limit is not allowed")
    try:
        total_lines = 0
        lines: deque[str] = deque(maxlen=line_limit)
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                total_lines += 1
                lines.append(redact_line(line.rstrip("\n")))
    except FileNotFoundError:
        return {"source": str(path), "status": "unavailable", "lines": []}
    except OSError as exc:
        return {"source": str(path), "status": "error", "lines": [], "error": str(exc)}

    truncated = total_lines > line_limit
    return {
        "source": str(path),
        "status": "partial" if truncated else "ok",
        "lines": list(lines),
        "truncated": truncated,
    }


def collect_service_state(unit: str, run_command: RunCommand) -> dict[str, Any]:
    if unit not in FIXED_UNITS:
        raise ValueError("service unit is not allowed")
    argv = ["systemctl", "is-active", unit]
    try:
        completed = run_command(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=COMMAND_TIMEOUT_SECONDS,
            shell=False,
            check=False,
        )
    except OSError as exc:
        return {
            "source": unit,
            "status": "error",
            "state": "unknown",
            "error": str(exc),
        }

    state = completed.stdout.strip() or completed.stderr.strip() or "unknown"
    return {
        "source": unit,
        "status": "ok" if completed.returncode == 0 else "unavailable",
        "state": redact_line(state),
    }


def redact_line(text: str) -> str:
    return REDACTION_PATTERN.sub(
        lambda match: f"{match.group(1)}{match.group(2)}{REDACTED_VALUE}", text
    )


def serialized_payload_size(payload: dict[str, Any]) -> int:
    return len(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def bound_payload(payload: dict[str, Any], byte_limit: int) -> dict[str, Any]:
    if (
        isinstance(byte_limit, bool)
        or not isinstance(byte_limit, int)
        or byte_limit < 1
    ):
        raise ValueError("payload byte limit must be positive")
    bounded = json.loads(json.dumps(payload))
    truncated = False
    while serialized_payload_size(bounded) > byte_limit:
        sections = bounded.get("sections")
        if not isinstance(sections, list):
            break
        removed_line = False
        for section in reversed(sections):
            lines = section.get("lines") if isinstance(section, dict) else None
            if isinstance(lines, list) and lines:
                lines.pop()
                section["status"] = "partial"
                section["truncated"] = True
                removed_line = True
                truncated = True
                break
        if not removed_line:
            break
    if truncated:
        bounded["truncated"] = True
    if serialized_payload_size(bounded) > byte_limit:
        bounded = {
            "kind": bounded.get("kind"),
            "time_window": bounded.get("time_window"),
            "sections": [],
            "truncated": True,
        }
    return bounded


def collect_journal_section(
    unit: str,
    time_window: str,
    match_terms: tuple[str, ...],
    run_command: RunCommand,
) -> dict[str, Any]:
    argv = build_fixed_journal_argv(unit, time_window, SECTION_LINE_LIMIT)
    try:
        completed = run_command(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=COMMAND_TIMEOUT_SECONDS,
            shell=False,
            check=False,
        )
    except OSError as exc:
        return {
            "source": f"journal:{unit}",
            "status": "error",
            "lines": [],
            "error": str(exc),
        }
    if completed.returncode != 0:
        return {
            "source": f"journal:{unit}",
            "status": "unavailable",
            "lines": [],
        }
    lowered_terms = tuple(term.lower() for term in match_terms)
    lines = [
        redact_line(line)
        for line in completed.stdout.splitlines()[-SECTION_LINE_LIMIT:]
        if any(term in line.lower() for term in lowered_terms)
    ]
    return {
        "source": f"journal:{unit}",
        "status": "ok" if lines else "unavailable",
        "lines": lines,
    }


def collect_log_pattern_sections(
    pattern: str,
    match_terms: tuple[str, ...],
) -> list[dict[str, Any]]:
    pattern_path = Path(pattern)
    paths = sorted(pattern_path.parent.glob(pattern_path.name))
    if not paths:
        return [{"source": pattern, "status": "unavailable", "lines": []}]
    lowered_terms = tuple(term.lower() for term in match_terms)
    sections = []
    for path in paths:
        section = collect_fixed_log_tail(path, SECTION_LINE_LIMIT)
        lines = section.get("lines", [])
        if isinstance(lines, list):
            section["lines"] = [
                line
                for line in lines
                if any(term in line.lower() for term in lowered_terms)
            ]
            if section["status"] == "ok" and not section["lines"]:
                section["status"] = "unavailable"
        sections.append(section)
    return sections


def collect_port_listener(port: int, run_command: RunCommand) -> dict[str, Any]:
    if port != 8775:
        raise ValueError("listener port is not allowed")
    argv = ["ss", "-ltn", "sport", "=", ":8775"]
    try:
        completed = run_command(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=COMMAND_TIMEOUT_SECONDS,
            shell=False,
            check=False,
        )
    except OSError as exc:
        return {
            "source": "listener:8775",
            "status": "error",
            "lines": [],
            "error": str(exc),
        }
    lines = [redact_line(line) for line in completed.stdout.splitlines()]
    return {
        "source": "listener:8775",
        "status": "ok" if completed.returncode == 0 and lines else "unavailable",
        "lines": lines,
    }


def parse_collection_request(request: str) -> tuple[str, str]:
    return parse_forced_command(f"{COMMAND_NAME} {request.strip()}")


def collect_diagnostic(
    kind: str,
    time_window: str,
    run_command: RunCommand = subprocess.run,
) -> dict[str, Any]:
    kind, time_window = validate_kind_and_window(kind, time_window)
    source_map = SOURCE_MAPS[kind]
    match_terms = source_map["match_terms"]
    sections = []
    for unit in source_map["units"]:
        sections.append(collect_service_state(unit, run_command))
        sections.append(
            collect_journal_section(unit, time_window, match_terms, run_command)
        )
    for pattern in source_map["log_patterns"]:
        sections.extend(collect_log_pattern_sections(pattern, match_terms))
    if source_map["port"] is not None:
        sections.append(collect_port_listener(source_map["port"], run_command))
    return bound_payload(
        {
            "kind": kind,
            "time_window": time_window,
            "sections": sections,
        },
        PAYLOAD_BYTE_LIMIT,
    )


def main(
    argv: list[str] | None = None,
    environ: dict[str, str] | None = None,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    run_command: RunCommand = subprocess.run,
) -> int:
    effective_argv = list(sys.argv[1:] if argv is None else argv)
    effective_environ = os.environ if environ is None else environ
    effective_stdin = sys.stdin if stdin is None else stdin
    effective_stdout = sys.stdout if stdout is None else stdout
    effective_stderr = sys.stderr if stderr is None else stderr

    if effective_argv == ["--collect"]:
        try:
            kind, time_window = parse_collection_request(effective_stdin.read())
            payload = collect_diagnostic(kind, time_window, run_command)
        except ValueError as exc:
            effective_stderr.write(f"{exc}\n")
            return 64
        json.dump(payload, effective_stdout, sort_keys=True)
        effective_stdout.write("\n")
        return 0

    if effective_argv:
        effective_stderr.write("collector accepts no direct arguments\n")
        return 64

    try:
        kind, time_window = parse_forced_command(
            effective_environ.get("SSH_ORIGINAL_COMMAND", "")
        )
    except ValueError as exc:
        effective_stderr.write(f"{exc}\n")
        return 64

    try:
        completed = run_command(
            ["sudo", "-n", str(Path(__file__).resolve()), "--collect"],
            input=f"{kind} {time_window}\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=COMMAND_TIMEOUT_SECONDS,
            shell=False,
            check=False,
        )
    except OSError as exc:
        effective_stderr.write(f"{exc}\n")
        return 1
    effective_stdout.write(completed.stdout)
    effective_stderr.write(completed.stderr)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
