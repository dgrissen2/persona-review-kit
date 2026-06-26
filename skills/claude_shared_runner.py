#!/usr/bin/env python3
"""Shared Claude CLI runner for review skills.

The runner provides the operational contract that review wrappers need:

* durable prompt/stdout/stderr/event artifacts
* stream-json progress when available
* periodic heartbeats even when Claude is thinking silently
* timeout diagnostics before process-group cleanup
* SIGINT/SIGTERM cleanup so child Claude processes are not orphaned
"""

from __future__ import annotations

import json
import math
import os
import re
import selectors
import signal
import subprocess
import sys
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, TextIO


DEFAULT_RUN_ROOT = Path.home() / ".cache" / "agent-review-runs"
MAX_TAIL_LINES = 80


def env_positive_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        print(f"[claude-runner] ignoring invalid {name}={raw!r}; using {default}", file=sys.stderr)
        return default
    if not math.isfinite(value) or value <= 0:
        print(f"[claude-runner] ignoring invalid {name}={raw!r}; using {default}", file=sys.stderr)
        return default
    return value


DEFAULT_HEARTBEAT_SEC = env_positive_float("CLAUDE_REVIEW_HEARTBEAT_SEC", 20.0)


class ClaudeRunnerTimeout(RuntimeError):
    """Raised when a Claude invocation exceeds its attempt timeout."""


@dataclass(frozen=True)
class ClaudeRunArtifacts:
    """Durable files for one Claude invocation."""

    run_dir: Path
    prompt_path: Path
    stdout_path: Path
    stderr_path: Path
    events_path: Path
    result_path: Path
    diagnostics_path: Path


def run_claude_with_progress(
    *,
    root: Path,
    prompt: str,
    model: str,
    effort: str,
    tools: str,
    permission_mode: str,
    timeout_sec: int,
    run_kind: str,
    scope_label: str,
    mode_label: str,
    add_dirs: Iterable[Path] = (),
    stream: bool = True,
    heartbeat_sec: float = DEFAULT_HEARTBEAT_SEC,
    safe_mode: bool = False,
    disable_slash_commands: bool = False,
    progress_stream: TextIO = sys.stderr,
) -> str:
    """Run Claude and return the final assistant text.

    Progress and diagnostics are written to ``progress_stream``; review content
    is returned to callers so existing wrapper output contracts remain stable.
    """
    if timeout_sec <= 0:
        raise RuntimeError("timeout_sec must be positive")
    if not math.isfinite(heartbeat_sec) or heartbeat_sec <= 0:
        raise RuntimeError("heartbeat_sec must be a positive finite number")

    artifacts = _create_artifacts(run_kind=run_kind, scope_label=scope_label, mode_label=mode_label)
    artifacts.prompt_path.write_text(prompt, encoding="utf-8")
    _emit_event(
        artifacts,
        "spawn_prepared",
        {
            "cwd": str(root),
            "model": model,
            "effort": effort,
            "tools": tools,
            "permission_mode": permission_mode,
            "timeout_sec": timeout_sec,
            "stream": stream,
            "safe_mode": safe_mode,
            "disable_slash_commands": disable_slash_commands,
            "prompt_bytes": _byte_len(prompt),
        },
    )

    cmd = _build_claude_command(
        model=model,
        effort=effort,
        tools=tools,
        permission_mode=permission_mode,
        add_dirs=add_dirs,
        stream=stream,
        safe_mode=safe_mode,
        disable_slash_commands=disable_slash_commands,
    )
    _progress(
        progress_stream,
        artifacts,
        (
            f"starting {run_kind} mode={mode_label} pid=? "
            f"payload={_byte_len(prompt)}B timeout={timeout_sec}s"
        ),
    )

    proc = subprocess.Popen(
        cmd,
        cwd=root,
        text=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        start_new_session=True,
    )
    pgid = os.getpgid(proc.pid)
    _emit_event(artifacts, "spawned", {"pid": proc.pid, "pgid": pgid, "cmd": _redacted_cmd(cmd)})
    _progress(
        progress_stream,
        artifacts,
        f"spawned pid={proc.pid} pgid={pgid} mode={mode_label}",
    )

    old_handlers = _install_signal_cleanup(proc, artifacts, progress_stream)
    start = time.monotonic()
    deadline = start + timeout_sec
    last_heartbeat = start
    assistant_text_parts: list[str] = []
    final_result: str | None = None
    stderr_tail: deque[str] = deque(maxlen=MAX_TAIL_LINES)
    stdout_tail: deque[str] = deque(maxlen=MAX_TAIL_LINES)
    partial_since_log = 0

    selector = selectors.DefaultSelector()
    try:
        assert proc.stdin is not None
        assert proc.stdout is not None
        assert proc.stderr is not None
        proc.stdin.write(prompt)
        proc.stdin.close()
        selector.register(proc.stdout, selectors.EVENT_READ, "stdout")
        selector.register(proc.stderr, selectors.EVENT_READ, "stderr")

        with artifacts.stdout_path.open("w", encoding="utf-8") as stdout_file, artifacts.stderr_path.open(
            "w", encoding="utf-8"
        ) as stderr_file:
            while True:
                now = time.monotonic()
                if now >= deadline:
                    _write_timeout_diagnostics(proc, artifacts)
                    _terminate_process_group(proc, signal.SIGTERM)
                    time.sleep(2)
                    if proc.poll() is None:
                        _terminate_process_group(proc, signal.SIGKILL)
                    _emit_event(
                        artifacts,
                        "timeout",
                        {"pid": proc.pid, "pgid": pgid, "elapsed_sec": round(now - start, 3)},
                    )
                    raise ClaudeRunnerTimeout(
                        f"Claude {run_kind} timed out after {timeout_sec}s in {mode_label}; "
                        f"artifacts: {artifacts.run_dir}"
                    )

                if now - last_heartbeat >= heartbeat_sec:
                    elapsed = int(now - start)
                    remaining = max(0, int(deadline - now))
                    _progress(
                        progress_stream,
                        artifacts,
                        (
                            f"heartbeat pid={proc.pid} pgid={pgid} mode={mode_label} "
                            f"elapsed={elapsed}s remaining={remaining}s "
                            f"stdout_lines={len(stdout_tail)} stderr_lines={len(stderr_tail)}"
                        ),
                    )
                    last_heartbeat = now

                if proc.poll() is not None and not selector.get_map():
                    break

                events = selector.select(timeout=0.5)
                if not events and proc.poll() is not None:
                    _drain_ready(selector, stdout_file, stderr_file, stdout_tail, stderr_tail)
                    break

                for key, _mask in events:
                    stream_name = key.data
                    line = key.fileobj.readline()
                    if line == "":
                        selector.unregister(key.fileobj)
                        continue
                    if stream_name == "stdout":
                        stdout_file.write(line)
                        stdout_file.flush()
                        stdout_tail.append(line.rstrip())
                        if stream:
                            delta, result = _handle_stream_json_line(line, artifacts, progress_stream)
                            if delta:
                                assistant_text_parts.append(delta)
                                partial_since_log += len(delta)
                                if partial_since_log >= 240 or "\n" in delta:
                                    _progress(
                                        progress_stream,
                                        artifacts,
                                        f"partial assistant output chars={len(''.join(assistant_text_parts))}",
                                    )
                                    partial_since_log = 0
                            if result is not None:
                                final_result = result
                        else:
                            assistant_text_parts.append(line)
                    else:
                        stderr_file.write(line)
                        stderr_file.flush()
                        stderr_tail.append(line.rstrip())
                        _progress(progress_stream, artifacts, f"stderr: {line.rstrip()}")

        return_code = proc.wait()
        elapsed = round(time.monotonic() - start, 3)
        output = final_result if final_result is not None else "".join(assistant_text_parts).strip()
        artifacts.result_path.write_text(output, encoding="utf-8")
        _emit_event(
            artifacts,
            "completed",
            {"return_code": return_code, "elapsed_sec": elapsed, "result_bytes": _byte_len(output)},
        )
        _progress(
            progress_stream,
            artifacts,
            f"completed rc={return_code} elapsed={elapsed}s result_bytes={_byte_len(output)}",
        )
        if return_code != 0:
            details = "\n".join(stderr_tail) or "\n".join(stdout_tail) or "unknown Claude CLI error"
            raise RuntimeError(f"Claude {run_kind} failed rc={return_code}: {details}\nArtifacts: {artifacts.run_dir}")
        if not output:
            raise RuntimeError(
                f"Claude {run_kind} completed rc=0 but produced no parseable assistant output. "
                f"Artifacts: {artifacts.run_dir}"
            )
        return output
    finally:
        selector.close()
        _restore_signal_handlers(old_handlers)


def _build_claude_command(
    *,
    model: str,
    effort: str,
    tools: str,
    permission_mode: str,
    add_dirs: Iterable[Path],
    stream: bool,
    safe_mode: bool,
    disable_slash_commands: bool,
) -> list[str]:
    cmd = [
        "claude",
        "-p",
        "--tools",
        tools,
        "--no-session-persistence",
        "--permission-mode",
        permission_mode,
        "--model",
        model,
        "--effort",
        effort,
    ]
    if stream:
        cmd.extend(["--verbose", "--output-format", "stream-json", "--include-partial-messages"])
    if safe_mode:
        cmd.append("--safe-mode")
    if disable_slash_commands:
        cmd.append("--disable-slash-commands")
    for directory in add_dirs:
        cmd.extend(["--add-dir", str(directory)])
    return cmd


def _handle_stream_json_line(
    line: str,
    artifacts: ClaudeRunArtifacts,
    progress_stream: TextIO,
) -> tuple[str, str | None]:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return "", None

    event_type = payload.get("type")
    subtype = payload.get("subtype")
    if event_type == "system" and subtype in {"init", "status", "hook_started", "hook_response"}:
        summary = {"type": event_type, "subtype": subtype}
        if "status" in payload:
            summary["status"] = payload.get("status")
        if "hook_name" in payload:
            summary["hook_name"] = payload.get("hook_name")
        if "tools" in payload:
            summary["tools_count"] = len(payload.get("tools") or [])
        _emit_event(artifacts, "claude_system", summary)
        if subtype in {"init", "status"}:
            _progress(progress_stream, artifacts, f"claude {subtype}: {summary}")
        return "", None

    if event_type == "rate_limit_event":
        info = payload.get("rate_limit_info") or {}
        _emit_event(artifacts, "rate_limit", info)
        _progress(progress_stream, artifacts, f"rate_limit: {info.get('status')} resetsAt={info.get('resetsAt')}")
        return "", None

    if event_type == "stream_event":
        event = payload.get("event") or {}
        if event.get("type") == "content_block_delta":
            delta = event.get("delta") or {}
            return str(delta.get("text") or ""), None
        if event.get("type") == "message_start":
            _emit_event(artifacts, "message_start", {"ttft_ms": payload.get("ttft_ms")})
        return "", None

    if event_type == "result":
        result = str(payload.get("result") or "")
        _emit_event(
            artifacts,
            "claude_result",
            {
                "subtype": payload.get("subtype"),
                "duration_ms": payload.get("duration_ms"),
                "is_error": payload.get("is_error"),
                "terminal_reason": payload.get("terminal_reason"),
            },
        )
        return "", result

    if event_type == "assistant":
        message = payload.get("message") or {}
        text_parts = [
            block.get("text", "")
            for block in message.get("content", [])
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        if text_parts:
            return "", "".join(text_parts)
    return "", None


def _create_artifacts(*, run_kind: str, scope_label: str, mode_label: str) -> ClaudeRunArtifacts:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = _slug(f"{run_kind}-{mode_label}-{scope_label}")[:80]
    base = DEFAULT_RUN_ROOT / f"{timestamp}-{slug}-{os.getpid()}"
    base.mkdir(parents=True, exist_ok=True)
    return ClaudeRunArtifacts(
        run_dir=base,
        prompt_path=base / "prompt.txt",
        stdout_path=base / "stdout.stream",
        stderr_path=base / "stderr.stream",
        events_path=base / "events.jsonl",
        result_path=base / "result.md",
        diagnostics_path=base / "process_snapshot_on_timeout.txt",
    )


def _install_signal_cleanup(
    proc: subprocess.Popen[str],
    artifacts: ClaudeRunArtifacts,
    progress_stream: TextIO,
) -> dict[int, signal.Handlers]:
    old_handlers: dict[int, signal.Handlers] = {}

    def handler(signum: int, _frame: object) -> None:
        _emit_event(artifacts, "signal", {"signum": signum, "pid": proc.pid})
        _progress(progress_stream, artifacts, f"received signal {signum}; terminating pid={proc.pid}")
        _write_timeout_diagnostics(proc, artifacts)
        _terminate_process_group(proc, signal.SIGTERM)
        time.sleep(1)
        if proc.poll() is None:
            _terminate_process_group(proc, signal.SIGKILL)
        raise SystemExit(128 + signum)

    for signum in (signal.SIGINT, signal.SIGTERM):
        old_handlers[signum] = signal.getsignal(signum)
        signal.signal(signum, handler)
    return old_handlers


def _restore_signal_handlers(old_handlers: dict[int, signal.Handlers]) -> None:
    for signum, handler in old_handlers.items():
        signal.signal(signum, handler)


def _terminate_process_group(proc: subprocess.Popen[str], sig: signal.Signals) -> None:
    try:
        os.killpg(os.getpgid(proc.pid), sig)
    except ProcessLookupError:
        return


def _write_timeout_diagnostics(proc: subprocess.Popen[str], artifacts: ClaudeRunArtifacts) -> None:
    sections: list[str] = [_process_group_snapshot(proc)]
    commands = [["lsof", "-p", str(proc.pid)]]
    for command in commands:
        try:
            result = subprocess.run(command, text=True, capture_output=True, check=False, timeout=10)
            sections.append(f"$ {' '.join(command)}\n{result.stdout}\n{result.stderr}")
        except (OSError, subprocess.TimeoutExpired) as exc:
            sections.append(f"$ {' '.join(command)}\nERROR: {exc}")

    tmp_root = Path("/private/tmp/claude-501")
    if tmp_root.exists():
        try:
            task_files = sorted(tmp_root.glob("**/tasks/**/*"), key=lambda path: path.stat().st_mtime, reverse=True)
            lines = [f"{path} size={path.stat().st_size}" for path in task_files[:80] if path.is_file()]
            sections.append("Claude temp task files:\n" + "\n".join(lines))
        except OSError as exc:
            sections.append(f"Claude temp task files:\nERROR: {exc}")

    artifacts.diagnostics_path.write_text("\n\n---\n\n".join(sections), encoding="utf-8")


def _process_group_snapshot(proc: subprocess.Popen[str]) -> str:
    try:
        pgid = os.getpgid(proc.pid)
    except ProcessLookupError:
        pgid = None
    try:
        result = subprocess.run(
            ["ps", "-axo", "pid,ppid,pgid,stat,etime,command"],
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"$ ps -axo pid,ppid,pgid,stat,etime,command\nERROR: {exc}"

    lines = result.stdout.splitlines()
    if not lines:
        return "$ ps -axo pid,ppid,pgid,stat,etime,command\n(no output)"
    header, rows = lines[0], lines[1:]
    relevant = [line for line in rows if _ps_row_matches_process(line, proc.pid, pgid)]
    body = "\n".join([header, *relevant]) if relevant else f"{header}\n(no rows for pid={proc.pid} pgid={pgid})"
    return f"$ ps -axo pid,ppid,pgid,stat,etime,command [filtered to Claude process group]\n{body}"


def _ps_row_matches_process(line: str, pid: int, pgid: int | None) -> bool:
    parts = line.split(None, 5)
    if len(parts) < 3:
        return False
    row_pid, row_ppid, row_pgid = parts[0], parts[1], parts[2]
    pid_text = str(pid)
    pgid_text = str(pgid) if pgid is not None else None
    return row_pid == pid_text or row_ppid == pid_text or (pgid_text is not None and row_pgid == pgid_text)


def _drain_ready(
    selector: selectors.BaseSelector,
    stdout_file: TextIO,
    stderr_file: TextIO,
    stdout_tail: deque[str],
    stderr_tail: deque[str],
) -> None:
    for key in list(selector.get_map().values()):
        for line in key.fileobj:
            if key.data == "stdout":
                stdout_file.write(line)
                stdout_tail.append(line.rstrip())
            else:
                stderr_file.write(line)
                stderr_tail.append(line.rstrip())


def _emit_event(artifacts: ClaudeRunArtifacts, event: str, payload: dict[str, object]) -> None:
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **payload,
    }
    with artifacts.events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _progress(stream: TextIO, artifacts: ClaudeRunArtifacts, message: str) -> None:
    print(f"[claude-runner] {message} | artifacts={artifacts.run_dir}", file=stream, flush=True)


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "run"


def _byte_len(value: str) -> int:
    return len(value.encode("utf-8"))


def _redacted_cmd(cmd: list[str]) -> list[str]:
    # The prompt is passed via stdin, not argv; command arguments contain no
    # tokens in normal use. Keep this helper anyway so the artifact contract is explicit.
    return list(cmd)
