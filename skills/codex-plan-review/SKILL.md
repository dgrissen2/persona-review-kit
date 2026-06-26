---
name: codex-plan-review
description: "Run an independent Codex plan review using GPT-5.5 with xhigh reasoning. Use for milestone roadmaps, implementation plans, architecture/design docs, and specs before implementation. Generic by default; flexible for optional persona lenses resolved from the persona registry."
---

# Codex Plan Review

Independent plan review using Codex (`gpt-5.5`, `model_reasoning_effort=xhigh`).
This is for plans, roadmaps, specs, and design docs, not ordinary code diffs.

> Requires the `codex` CLI (`npm install -g @openai/codex`, then `codex login`).
> Persona listing/resolution works without it.

## Focus

The generic review checks:

- spec fidelity: missing requirements, invented scope, ambiguous acceptance criteria
- internal consistency: formulas, thresholds, score ranges, naming, and definitions
- dependency ordering: milestones that depend on unbuilt or underspecified pieces
- data contracts: fields, enums, units, return shapes, schemas, and file paths
- feasibility: work estimates, validation budgets, operational assumptions
- edge cases: empty inputs, boundaries, NaN/None, rollback and failure modes
- test adequacy: whether tests cover the actual risks in the plan

## Personas

Personas are optional lenses, not a fixed enum. Decide which to use up front when the
review is initiated. Example lenses: `architect`, `cto`, `red-team`, `software-architect`,
`quant` — or pass a direct path to a persona `.md` file.

Run without personas for a generic review; pass `--personas a,b,/path/to/persona.md` for a panel.

List what's available via the shared resolver (works even without Codex):

```bash
python3 ~/.claude/skills/persona-registry/scripts/persona_registry.py --list
```

## Model & reasoning effort

Defaults: **model `gpt-5.5`**, **reasoning effort `xhigh`**. To change (no reinstall): pass `--model` /
`--effort`, or edit `DEFAULT_MODEL` / `DEFAULT_EFFORT` at the top of the script.

## Workflow

Generic review:

```bash
python ~/.claude/skills/codex-plan-review/scripts/codex_plan_review.py \
  <plan_file> \
  [context_file ...]
```

Generic review plus persona overlays:

```bash
python ~/.claude/skills/codex-plan-review/scripts/codex_plan_review.py \
  <plan_file> \
  [context_file ...] \
  --personas architect,red-team,/path/to/custom_persona.md
```

The script writes review artifacts next to the plan file and prints the combined
output. Persona passes are independent; synthesis sees only completed outputs.

## Output Contract

Generic:

```text
## Codex Plan Review — Verdict: PASS / CONDITIONAL PASS / FAIL (N findings)
```

Persona:

```text
## Codex Plan Review — <Persona Name>
```

Synthesis:

```text
## Codex Plan Review — Panel Synthesis
```

## Persona resolution

Personas resolve via the shared resolver
(`persona-registry/scripts/persona_registry.py`), which is installed regardless of Codex.
The Codex script locates it automatically. Search order (first existing wins):

1. `$PERSONA_REGISTRY_DIR` (explicit override, if set)
2. co-located with the Codex script
3. the skill dir / skills root (repo layouts)
4. the sibling `persona-registry` skill (in-repo layout)
5. `~/.claude/skills/persona-registry/scripts` (installed canonical resolver)

Persona *discovery* (which `.md` files are available) is governed by the persona-registry
skill: `PERSONA_PATHS` / `--persona-dir`, then the installed kit library
(`~/.config/persona-review-kit/personas/`), then project-local folders, then
`~/.claude/personas/`.

## Intent and focus (automatic)

Derive these from the user's request — they should not need to type flags. From how they phrase the
ask, infer **intent** (what the work is trying to do) and **focus** (what to weight) and pass them as
`--intent` / `--focus`. For example, *"review the auth refactor on this branch, focus on whether the
logic is right and skip style"* -> `--intent "auth refactor" --focus "logic correctness, skip style"`.

The text is appended to the prompt as *author framing*, never as another reviewer's findings (the
review stays independent). A guardrail still surfaces every CRITICAL/HIGH finding even when it falls
outside the focus.
