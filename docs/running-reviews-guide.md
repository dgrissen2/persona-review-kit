# Running Reviews Guide

The kit gives you three review surfaces — **code**, **plan**, and **strategy/logic** — in **both
directions**: from Claude you call Codex, and from Codex you call Claude. Pick the direction by which
platform you're currently working in; you call *out* to the other one for an independent opinion.

## Pick the right review

| You have… | From Claude Code | From Codex |
|---|---|---|
| A code diff / changed files | `/codex-review` | `/claude-review` |
| A plan, roadmap, design doc, or spec | `/codex-plan-review` | `/claude-plan-review` |
| A strategy, decision memo, or argument | `/codex-strategy-review` | `/claude-strategy-review` |

Both directions return the same shape: a `PASS / CONDITIONAL PASS / FAIL` verdict plus a findings
table. The reviewer sees only the artifact (anti-anchoring), so it forms its own judgment.

## From Claude Code → Codex reviews

Require the Codex CLI (`npm install -g @openai/codex`, then `codex login`).

```bash
# Code review
~/.claude/skills/codex-review/scripts/codex_review.sh            # uncommitted changes
~/.claude/skills/codex-review/scripts/codex_review.sh branch     # current branch vs main
~/.claude/skills/codex-review/scripts/codex_review.sh src/app/handler.py

# Plan review (optional persona overlays)
python3 ~/.claude/skills/codex-plan-review/scripts/codex_plan_review.py plan.md [context ...] \
  --personas architect,red-team

# Strategy / logic review
python3 ~/.claude/skills/codex-strategy-review/scripts/codex_strategy_review.py strategy.md \
  --personas quant,cio
```

Codex defaults: model `gpt-5.5`, effort `xhigh`. Override with `--model` / `--effort`, or the
`CODEX_MODEL` / `CODEX_EFFORT` env vars (for `codex_review.sh`). Per-invocation timeout:
`CODEX_TIMEOUT` (default 300s).

## From Codex → Claude reviews

Require the Claude CLI (`claude auth login`).

```bash
# Code review
python3 ~/.codex/skills/claude-review/scripts/claude_review.py            # uncommitted changes
python3 ~/.codex/skills/claude-review/scripts/claude_review.py branch     # current branch vs main
python3 ~/.codex/skills/claude-review/scripts/claude_review.py src/app/handler.py

# Plan review (optional persona overlays)
python3 ~/.codex/skills/claude-plan-review/scripts/claude_plan_review.py plan.md [context ...] \
  --personas architect,red-team

# Strategy / logic review
python3 ~/.codex/skills/claude-strategy-review/scripts/claude_strategy_review.py strategy.md \
  --personas quant,cio
```

Claude defaults: model `claude-opus-4-8`, effort `max`, tools enabled, size-aware payloads with
automatic fallback (diff-only → per-file → segmented). Override with the `CLAUDE_REVIEW_*` env vars
documented in the skill's `SKILL.md`.

## Focusing a review (optional intent / focus)

Both directions accept an optional intent + focus to steer attention (omit both for the standard
review):

```bash
python3 ~/.claude/skills/codex-plan-review/scripts/codex_plan_review.py plan.md \
  --intent "ship the auth refactor" --focus "adherence to intended logic; skip style nitpicks"

CODEX_FOCUS="adherence to intended logic, skip nitpicks" \
  ~/.claude/skills/codex-review/scripts/codex_review.sh branch
```

A guardrail keeps CRITICAL/HIGH issues surfaced even if they fall outside the focus, and the text is
treated as your intent — never as another reviewer's findings.

## Choosing personas

List what's available, then pass a comma-separated set:

```bash
python3 ~/.claude/skills/persona-registry/scripts/persona_registry.py --list
```

Good defaults:
- **Code / plan**: `architect`, `cto`, `red-team`
- **Strategy / decision**: `quant`, `cio`, `portfolio-manager`, `arbiter`
- **Explanatory clarity**: `richard-feynman`, `junior-engineer`

Each persona runs as an independent overlay; a synthesis pass deduplicates across them. Use the
minimum number of *distinct* lenses — redundant personas add cost, not coverage. See
[`persona-registry-guide.md`](./persona-registry-guide.md) to add your own.
