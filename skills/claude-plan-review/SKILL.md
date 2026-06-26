---
name: claude-plan-review
targets: [codex]
description: "Run an independent Claude Opus 4.8 plan review with tools enabled. Use for milestone roadmaps, implementation plans, architecture/design docs, specs, or planning artifacts before code is written; not for ordinary code diff review."
---

# Claude Plan Review

Independent plan review using Claude Code, pinned to `claude-opus-4-8` with
`--effort max`, `--tools default`, and `--permission-mode auto`.

## Focus

Use this for plans, not code diffs. Claude should look for:

- spec fidelity gaps: required behavior missing, invented scope, vague acceptance criteria
- internal contradictions: thresholds, formulas, naming, ranges, and definitions that disagree
- dependency mistakes: milestones ordered incorrectly or pretending to be parallel
- data contract gaps: undefined fields, schemas, enums, units, file paths, return shapes
- feasibility risks: estimates, rollout assumptions, operational constraints
- validation gaps: tests that do not cover the risk-bearing behavior

## Workflow

1. Identify the plan file and any useful context files, such as the spec, upstream model, ADR, schema, or previous roadmap.
2. Run:

```bash
python3 ~/.codex/skills/claude-plan-review/scripts/claude_plan_review.py \
  <plan_file> \
  [context_file ...]
```

3. Present Claude's findings directly. Do not include Codex's prior reasoning or other reviewer notes in the prompt unless the user explicitly asks for synthesis.

The runner streams Claude progress by default, emits heartbeat updates to
stderr, and writes durable artifacts under `~/.cache/agent-review-runs/`.
Each Claude attempt records `prompt.txt`, `stdout.stream`, `stderr.stream`,
`events.jsonl`, `result.md`, and timeout diagnostics. On SIGINT/SIGTERM/timeout,
the wrapper terminates only its own Claude process group.

If Claude times out or the wrapper cannot complete, report `TOOLING FAILURE` with
the artifact path. A tooling failure is not a `PASS`, `CONDITIONAL PASS`, or `FAIL`
plan verdict and must not be treated as plan approval.

## Personas

Personas are optional overlays resolved from the shared persona registry, not
from a hardcoded enum. Use them when a plan needs a specific lens such as
`architect`, `cto`, `red-team`, or a direct persona file.

List available personas:

```bash
python3 ~/.codex/skills/claude-plan-review/scripts/claude_plan_review.py \
  --list-personas
```

Run with persona aliases or persona file paths:

```bash
python3 ~/.codex/skills/claude-plan-review/scripts/claude_plan_review.py \
  <plan_file> \
  [context_file ...] \
  --personas architect,red-team,/path/to/custom_persona.md
```

Canonical personas live at `~/.config/persona-review-kit/personas/`, and the shared
resolver lives at
`~/.codex/skills/persona-registry/scripts/persona_registry.py`.

## Output Contract

The script asks Claude to return:

```text
## Claude Plan Review — Verdict: PASS / CONDITIONAL PASS / FAIL (N findings)
```

plus a findings table and high-risk open questions.

## Notes

- Default model: `claude-opus-4-8`
- Default effort: `max`
- Allowed effort values: `low`, `medium`, `high`, `max`, `xhigh`
- Default tools: `default`
- Default permission mode: `auto`
- Allowed permission modes: `auto`, `default`, `dontAsk`, `plan`; edit-accepting and permission-bypass modes are intentionally rejected for review runs over untrusted plans/context
- Exit code `0` means the wrapper completed and emitted a plan review; callers must parse the `PASS` / `CONDITIONAL PASS` / `FAIL` verdict from stdout. Exit code `1` means wrapper/tooling failure or invalid invocation.
- Default heartbeat: `20` seconds
- Troubleshooting flags: `--no-stream`, `--heartbeat-sec N`, `--safe-mode`,
  `--disable-slash-commands`
- Override with `CLAUDE_PLAN_REVIEW_MODEL`, `CLAUDE_PLAN_REVIEW_EFFORT`,
  `CLAUDE_PLAN_REVIEW_TOOLS`, `CLAUDE_PLAN_REVIEW_PERMISSION_MODE`,
  `CLAUDE_PLAN_REVIEW_TIMEOUT_SEC`, or `CLAUDE_PLAN_REVIEW_HEARTBEAT_SEC`.

## Intent and focus (automatic)

Derive these from the user's request — they should not need to type flags. From how they phrase the
ask, infer **intent** (what the work is trying to do) and **focus** (what to weight) and pass them as
`--intent` / `--focus`. For example, *"review the auth refactor on this branch, focus on whether the
logic is right and skip style"* -> `--intent "auth refactor" --focus "logic correctness, skip style"`.

The text is appended to the prompt as *author framing*, never as another reviewer's findings (the
review stays independent). A guardrail still surfaces every CRITICAL/HIGH finding even when it falls
outside the focus.
