# Changelog

All notable changes to **persona-review-kit** are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- **Dynamic Claude timeouts** in `claude_shared_runner.py`: the soft timeout is estimated
  upfront from workload size (payload plus documents read via tools) and effort, then the
  deadline keeps extending while Claude is still streaming output. Runs are killed only on a
  stall (`CLAUDE_REVIEW_STALL_SEC`, default 300s of silence past the soft budget) or at the
  hard cap (`CLAUDE_REVIEW_MAX_TIMEOUT_SEC`, default 3600s). `--timeout-sec` /
  `CLAUDE_*_TIMEOUT_SEC` now pin the soft budget (0 = auto-estimate).
- Deadline-extension progress notices and richer heartbeats (elapsed / remaining / idle) on
  stderr so the calling agent always sees liveness and never mistakes a long review for a
  dead process.

- **Codex web search** via `CODEX_SEARCH=1` (adds Codex's `--search`; off by default for
  reproducible reviews) in `codex-review`, `codex-plan-review`, and `codex-strategy-review`.
- **Codex heartbeats**: all three codex skills print `still running: elapsed / idle` to stderr every
  `CODEX_HEARTBEAT_SEC` (default 20 s) while Codex thinks silently.
- `codex-review` now streams Codex's progress live to stderr and a `0600` log file, matching the
  plan/strategy skills.

### Fixed
- **Stale reviews can no longer pass as fresh.** `codex-plan-review` / `codex-strategy-review`
  delete the previous output file before running; before, a Codex dispatch failure (e.g.
  `model_not_found`) returned the *previous* run's review with exit 0.
- **`codex-review` failures are visible.** A watchdog kill exits `124`, an empty review exits
  non-zero (Codex's code, else `1`), and a non-numeric `CODEX_TIMEOUT` / `CODEX_HEARTBEAT_SEC`
  exits `2` up front (it used to silently disable the watchdog). Previously every case exited 0.
- Interrupts (Ctrl-C / SIGTERM) now terminate the Codex process group (Python twins) or Codex
  and its child processes (`codex-review`); before, Codex and its MCP servers were orphaned.
  The watchdog also kills Codex's direct children, scoped by PID/PPID (never by name).
- Progress logs are created `0600` (the Python twins used the default umask) and `*.stream.log`
  is gitignored; the log echoes the full review payload, so it must not be world-readable or
  committed.
- `codex-plan-review` and `codex-strategy-review` now send the prompt to Codex on **stdin**
  (and close it) instead of as a command-line argument. This fixes a hang where a caller that
  left stdin open (an agent harness, cron, a backgrounded job) made `codex exec` sit on
  "Reading additional input from stdin..." until the watchdog killed it after 300 s, and it keeps
  the reviewed artifact out of `ps` output and out of the OS argument-size limit.
- Codex twins no longer pass `--full-auto` (dropped by Codex CLI ≥ 0.153, which made every run fail
  at dispatch); they now run `--sandbox read-only`. `codex-review` previously ran with the user's
  Codex default sandbox and is now explicitly read-only.

### Changed
- `codex-review` timeout (`CODEX_TIMEOUT`, default 300 s) is now an inactivity cap, like the
  plan/strategy skills, instead of a fixed wall-clock limit.
- `claude-review`, `claude-plan-review`, and `claude-strategy-review` now default to
  `--effort xhigh` (model stays `claude-opus-5`), matching the Codex twins' `xhigh`
  reasoning defaults.
- Codex twins (`codex-review`, `codex-plan-review`, `codex-strategy-review`) now all default
  to the explicit model ID `gpt-6.1-sol` (was the bare `gpt-5.6` alias, then `gpt-5.6-sol`).
  The Codex CLI validates against the account's model list, which exposes only explicit IDs,
  so bare aliases fail at dispatch. `--model` / `CODEX_MODEL` overrides are unchanged.

## [0.1.0] - 2026-06-25

Initial public release.

### Added
- **Cross-model review twins** — Claude and Codex review each other:
  - From Claude Code: `codex-review`, `codex-plan-review`, `codex-strategy-review` (call Codex).
  - From Codex: `claude-review`, `claude-plan-review`, `claude-strategy-review` (call Claude).
  - Shared `persona-registry` resolver + `claude_shared_runner.py`.
- 14 analytical personas across engineering, strategy, market, and education domains, resolved
  through a shared, extensible persona registry.
- Optional **intent / focus** steering on every review skill: `--intent` / `--focus` flags (and
  `CODEX_INTENT` / `CODEX_FOCUS` env vars for `codex-review`). When unset the prompt is unchanged;
  when set, an author-framed focus block is appended with a guardrail that CRITICAL/HIGH issues are
  always surfaced even if outside the focus.
- Global-only, dual-target `install.sh` / `uninstall.sh` — codex-* twins → `~/.claude/skills/`,
  claude-* twins → `~/.codex/skills/`, persona-registry into both, personas into
  `~/.config/persona-review-kit/personas/`.
- MIT license, a disclaimer covering the real-named caricature personas, a contributor guide, and
  user guides for the registry and running reviews in both directions.
