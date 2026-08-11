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

### Changed
- `claude-review`, `claude-plan-review`, and `claude-strategy-review` now default to
  `--effort xhigh` (model stays `claude-opus-5`), matching the Codex twins' `xhigh`
  reasoning defaults.
- Codex twins now default to the explicit model ID `gpt-5.6-sol` (was the bare `gpt-5.6`
  alias). The Codex CLI validates against the account's model list, which exposes only the
  explicit ID during the Sol preview, so the alias failed at dispatch; the API-side alias
  still routes to Sol, and `--model` / `CODEX_MODEL` overrides are unchanged.

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
