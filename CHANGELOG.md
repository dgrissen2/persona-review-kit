# Changelog

All notable changes to **persona-review-kit** are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

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
