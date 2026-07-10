---
name: codex-strategy-review
description: "Run an independent Codex adversarial strategy and logic review using GPT-5.6 with xhigh reasoning. Generic by default; flexible for optional persona lenses resolved from the persona registry. Use for strategy docs, research conclusions, optimizer proposals, risk frameworks, decision memos, or arguments that need stress-testing."
---

# Codex Strategy Review

Independent adversarial logic review using Codex (`gpt-5.6`,
`model_reasoning_effort=xhigh`). This skill is generic by default and flexible for different personas.

> Requires the `codex` CLI (`npm install -g @openai/codex`, then `codex login`).
> Persona listing/resolution works without it.

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

Personas are optional lenses, not a fixed enum. Decide which to use up front when the
review is initiated. Example lenses: `architect`, `cto`, `red-team`, `quant`,
`portfolio-manager` — or pass a direct path to a persona `.md` file.

Run without personas for a generic review; pass `--personas a,b,/path/to/persona.md` for a panel.

List what's available via the shared resolver (works even without Codex):

```bash
python3 ~/.claude/skills/persona-registry/scripts/persona_registry.py --list
```

## Model & reasoning effort

Defaults: **model `gpt-5.6`**, **reasoning effort `xhigh`**. To change (no reinstall): pass `--model` /
`--effort`, or edit `DEFAULT_MODEL` / `DEFAULT_EFFORT` at the top of the script.

## Workflow

Generic review:

```bash
python ~/.claude/skills/codex-strategy-review/scripts/codex_strategy_review.py \
  <strategy_file> \
  [context_file ...]
```

Generic review plus persona overlays:

```bash
python ~/.claude/skills/codex-strategy-review/scripts/codex_strategy_review.py \
  <strategy_file> \
  [context_file ...] \
  --personas quant,pm,/path/to/custom_persona.md
```

Legacy form still works:

```bash
python ~/.claude/skills/codex-strategy-review/scripts/codex_strategy_review.py \
  <strategy_file> \
  quant,pm \
  [context_file ...]
```

Each persona pass is independent. The final synthesis may see all completed
outputs and deduplicates agreement, disagreement, and unique catches.

## Output Contract

Generic:

```text
## Codex Strategy Review — Generic Logic
```

Persona:

```text
## Codex Strategy Review — <Persona Name>
```

Synthesis:

```text
## Codex Strategy Review — Panel Synthesis
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
