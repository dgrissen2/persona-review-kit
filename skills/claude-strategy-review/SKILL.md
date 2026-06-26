---
name: claude-strategy-review
targets: [codex]
description: "Run an independent Claude Opus 4.8 adversarial strategy and logic review with tools enabled and optional persona lenses. Use for strategy docs, research conclusions, optimizer proposals, risk frameworks, decision memos, plans, or arguments that need stress-testing; generic by default and not trading-specific."
---

# Claude Strategy Review

Independent adversarial logic review using Claude Code, pinned to `claude-opus-4-8`
with `--effort max`, `--tools default`, and `--permission-mode auto`.

## Focus

Use this to stress-test a strategy, argument, proposal, research conclusion, risk
framework, optimizer design, decision memo, or any other plan where the question is
"does this logic hold up?"

The generic review checks:

- conclusions that do not follow from premises
- hidden, circular, fragile, or unstated assumptions
- made-up thresholds, constants, weights, or scoring rules
- missing evidence, counterexamples, and falsification tests
- incorrect math, units, base rates, or time horizons
- feasibility, incentives, adoption, and operational constraints
- downside, tail risks, failure modes, monitoring, and reversibility
- contradictions between goals, constraints, and proposed mechanisms

## Personas

Personas are optional lenses, not a fixed enum. The runner discovers persona
markdown files through the shared persona registry. Examples include
`quant`, `pm`, `brent`, `architect`, `red-team`, `marcus`, or a direct persona
file.

If the user provides personas, use them. If the user asks for a panel or persona
lenses without naming them, ask one concise question about which lenses to
include. Otherwise run the generic logic review by default.

List discovered personas with:

```bash
python3 ~/.codex/skills/claude-strategy-review/scripts/claude_strategy_review.py \
  --list-personas
```

## Workflow

Run a generic-only review:

```bash
python3 ~/.codex/skills/claude-strategy-review/scripts/claude_strategy_review.py \
  <strategy_file> \
  [context_file ...]
```

Run with persona aliases or persona file paths:

```bash
python3 ~/.codex/skills/claude-strategy-review/scripts/claude_strategy_review.py \
  <strategy_file> \
  [context_file ...] \
  --personas quant,pm,/path/to/custom_persona.md
```

Each persona pass is independent: do not feed one persona's output into another.
The final synthesis may see all outputs and should deduplicate agreement,
disagreement, and unique catches.

The runner streams Claude progress by default, emits heartbeat updates to
stderr, and writes durable artifacts under `~/.cache/agent-review-runs/`.
Each Claude attempt records `prompt.txt`, `stdout.stream`, `stderr.stream`,
`events.jsonl`, `result.md`, and timeout diagnostics. On SIGINT/SIGTERM/timeout,
the wrapper terminates only its own Claude process group.

If Claude times out or the wrapper cannot complete, report `TOOLING FAILURE` with
the artifact path. A tooling failure is not a strategy verdict and must not be
treated as approval, rejection, or evidence about the strategy itself.

Canonical personas live at `~/.config/persona-review-kit/personas/`, and the shared
resolver lives at
`~/.codex/skills/persona-registry/scripts/persona_registry.py`.

## Output Contract

The script returns a generic review, optional persona reviews, and optional synthesis:

```text
## Claude Strategy Review — Generic Logic
## Claude Strategy Review — <Persona Name>
## Claude Strategy Review — Panel Synthesis
```

## Notes

- Default model: `claude-opus-4-8`
- Default effort: `max`
- Allowed effort values: `low`, `medium`, `high`, `max`, `xhigh`
- Default tools: `default`
- Default permission mode: `auto`
- Allowed permission modes: `auto`, `default`, `dontAsk`, `plan`; edit-accepting and permission-bypass modes are intentionally rejected for review runs over untrusted strategy/context
- Exit code `0` means the wrapper completed and emitted a strategy review; callers must inspect the review text. Exit code `1` means wrapper/tooling failure or invalid invocation.
- Default heartbeat: `20` seconds
- Troubleshooting flags: `--no-stream`, `--heartbeat-sec N`, `--safe-mode`,
  `--disable-slash-commands`
- Override with `CLAUDE_STRATEGY_REVIEW_MODEL`, `CLAUDE_STRATEGY_REVIEW_EFFORT`,
  `CLAUDE_STRATEGY_REVIEW_TOOLS`, `CLAUDE_STRATEGY_REVIEW_PERMISSION_MODE`,
  `CLAUDE_STRATEGY_REVIEW_TIMEOUT_SEC`, or `CLAUDE_STRATEGY_REVIEW_HEARTBEAT_SEC`.

## Intent and focus (automatic)

Derive these from the user's request — they should not need to type flags. From how they phrase the
ask, infer **intent** (what the work is trying to do) and **focus** (what to weight) and pass them as
`--intent` / `--focus`. For example, *"review the auth refactor on this branch, focus on whether the
logic is right and skip style"* -> `--intent "auth refactor" --focus "logic correctness, skip style"`.

The text is appended to the prompt as *author framing*, never as another reviewer's findings (the
review stays independent). A guardrail still surfaces every CRITICAL/HIGH finding even when it falls
outside the focus.
