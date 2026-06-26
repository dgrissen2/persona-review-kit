---
name: claude-review
targets: [codex]
description: "Run an independent Claude Code review using Claude Opus 4.8 with max effort and tools enabled. Use when the user says 'claude review', 'run Claude on this', 'cross-model review', or wants a second-model review of a file, directory, branch, or uncommitted diff."
---

# Claude Review

Independent code review using Claude Code, pinned to `claude-opus-4-8` with `--effort max`.
The runner is size-aware: it starts with the richest payload that fits, then automatically
falls back to diff-only, per-file batching, or segmented single-file review when the scope is
too large.

It is also untracked-file aware. Brand-new files that have no `git diff` are reviewed from
their current file contents, with content segmentation when needed; the runner must not retry
an empty diff-only payload for an untracked file.

## Why This Exists

Claude reviews from a different model family than Codex. The value comes from anti-anchoring: pass the code and diff to Claude, never prior reviewer notes or planning context. The runner keeps Claude tools enabled so it can inspect files, run read-only diagnostics, run tests, and use web tools when useful, but the prompt instructs Claude to review rather than modify.

Do not add `--bare` for normal use. Claude Code bare mode intentionally ignores OAuth/keychain login and requires `ANTHROPIC_API_KEY` or an API-key helper, so it fails after ordinary `claude auth login`. Isolation comes from independent input selection and disabled session persistence, not from disabling tools.

## Scope Rules

- If `$ARGUMENTS` contains a file path or directory: review that path.
- If `$ARGUMENTS` contains `pr`, `branch`, or `panel`: review current branch changes versus `main`.
- If `$ARGUMENTS` is empty: review all uncommitted changes.

## Workflow

1. Run:

```bash
python3 ~/.codex/skills/claude-review/scripts/claude_review.py [scope]
```

2. The script will:
   - collect the relevant git diff
   - include current file contents only when the payload is small enough
   - log review planning details to stderr
   - call Claude Code with `--model claude-opus-4-8 --effort max --tools default --no-session-persistence --permission-mode auto`
   - run Claude in stream-json mode by default and emit heartbeat/progress updates to stderr
   - write durable run artifacts under `~/.cache/agent-review-runs/`
   - retry in smaller modes on timeout
   - treat untracked files as content-first review targets, not empty diffs
   - aggregate batched Claude findings back into one structured review

3. Present Claude's findings directly.

If Claude times out or all retries fail, report `TOOLING FAILURE` with the artifact path. A
tooling failure is not a `PASS`, `CONDITIONAL PASS`, or `FAIL` review verdict.

## Output Contract

The script asks Claude to return:

```text
## Claude Review — Verdict: <PASS / CONDITIONAL PASS / FAIL>
```

plus a findings table, or `No issues found.` when clean.

## Notes

- Default model: `claude-opus-4-8`
- Default effort: `max`
- Allowed effort values: `low`, `medium`, `high`, `max`, `xhigh`
- Default tools: `default`
- Default permission mode: `auto`
- Allowed permission modes: `auto`, `default`, `dontAsk`, `plan`; edit-accepting and permission-bypass modes are intentionally rejected for review runs over untrusted code
- Exit code `0` means the wrapper completed and emitted a review; callers must parse the `PASS` / `CONDITIONAL PASS` / `FAIL` verdict from stdout. Exit code `1` means wrapper/tooling failure.
- Default timeout: `300` seconds
- Default review mode is automatic: `full` → `diff-only` → `per-file` / `diff-segment`
- Untracked file mode is automatic: `untracked-file` → `untracked-file-segment`
- No-diff explicit file mode is automatic: `context-only` → `context-segment`
- Progress is written to stderr with payload sizes, selected mode, PID/PGID, heartbeats, and artifact paths
- Each Claude attempt writes `prompt.txt`, `stdout.stream`, `stderr.stream`, `events.jsonl`, `result.md`, and timeout diagnostics under `~/.cache/agent-review-runs/`
- On SIGINT/SIGTERM/timeout, the wrapper terminates only its own Claude process group
- Troubleshooting flags:
  - `--no-stream`
  - `--heartbeat-sec N`
  - `--safe-mode`
  - `--disable-slash-commands`
- You can override with:
  - `CLAUDE_REVIEW_MODEL`
  - `CLAUDE_REVIEW_EFFORT`
  - `CLAUDE_REVIEW_TOOLS`
  - `CLAUDE_REVIEW_PERMISSION_MODE`
  - `CLAUDE_REVIEW_MAX_FILES`
  - `CLAUDE_REVIEW_MAX_PAYLOAD_BYTES`
  - `CLAUDE_REVIEW_DIFF_ONLY_BYTES`
  - `CLAUDE_REVIEW_TIMEOUT_SEC`
  - `CLAUDE_REVIEW_SEGMENT_BYTES`
  - `CLAUDE_REVIEW_HEARTBEAT_SEC`

## Intent and focus (automatic)

Derive these from the user's request — they should not need to type flags. From how they phrase the
ask, infer **intent** (what the work is trying to do) and **focus** (what to weight) and pass them as
`--intent` / `--focus`. For example, *"review the auth refactor on this branch, focus on whether the
logic is right and skip style"* -> `--intent "auth refactor" --focus "logic correctness, skip style"`.

The text is appended to the prompt as *author framing*, never as another reviewer's findings (the
review stays independent). A guardrail still surfaces every CRITICAL/HIGH finding even when it falls
outside the focus.
