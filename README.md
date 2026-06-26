# persona-review-kit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
![Claude Code](https://img.shields.io/badge/Claude%20Code-compatible-7c3aed)
![Codex](https://img.shields.io/badge/Codex-compatible-444)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

## Structured Cross-Model Reviews

**Independent, cross-model review across Claude and Codex — for your code, plans, and strategy.**

You get the best results when you play the two frontier models off each other. If you build with
[Claude Code](https://claude.com/claude-code) and [OpenAI Codex](https://github.com/openai/codex),
persona-review-kit adds the step that's missing: a rigorous second pass from the *other* model. Each
one checks the other's work — and because they have different blind spots, each catches what the
other waves through. It runs both directions: from Claude Code you call Codex; from Codex you call
Claude.

**Three reviews, available each way:**

- **`[claude/codex]-review`** — checks a diff, file, or branch for logic errors, broken contracts, bad edge cases, and security holes.
- **`[claude/codex]-plan-review`** — checks a plan, design, or spec for missing requirements, shaky assumptions, and dependency gaps — before you build.
- **`[claude/codex]-strategy-review`** — adversarially stress-tests a strategy, decision, or argument: do the conclusions actually follow, and what's the hidden assumption?

## Guardrails

Calling another model is a one-liner. The skills wrap each cross-platform call in Python guardrails to
avoid improvisation — when an LLM rolls its own approach every time, you get timeouts and failures. The
built-in guardrails make the reviews both honest and dependable:

- **Independent by construction** — the reviewer never sees your reasoning or prior comments, so it judges the work, not your conclusion.
- **Can't be gamed** — the artifact under review is treated as data, never instructions; text buried in a diff can't talk the reviewer into a PASS.
- **Focus without blind spots** — steer the review toward what matters; every CRITICAL and HIGH finding still surfaces.
- **Read-only** — reviewers review; they never touch your files.
- **Bounded and isolated** — each run has a timeout and a watchdog that stops only its own review, so it never runs away or disturbs other work.
- **Structured verdicts** — every review returns a clean PASS / CONDITIONAL PASS / FAIL plus a findings table you can act on or automate.

## Global personas

Personas go hand in hand with the reviews. A lightweight, global persona registry keeps them
consistent across both platforms, so you can invoke the same lens from either side — e.g. *"have the
**Architect** review this plan here and via `/codex-plan-review`,"* or *"ask the **Quant** persona to
check these conclusions here and via `/claude-strategy-review`."* Add a persona once and it's
available to every skill, in both directions.

## Requirements

- **Claude Code** and the **Claude CLI** — needed to run the kit from Claude, and the `claude-*`
  twins shell out to `claude` when invoked from Codex.
- **OpenAI Codex CLI** (`npm install -g @openai/codex`, then `codex login`) — needed to run the kit
  from Codex, and the `codex-*` twins shell out to `codex` when invoked from Claude.
- **Python 3.10+** — standard library only; no third-party packages.
- **[Serena MCP server](https://github.com/oraios/serena)** — *optional*, used by the code-review
  skills to build token-efficient, symbol-level review packages on large diffs; without it they send
  the diff and relevant files.

You only need the platform you're *calling out to*: to use `/codex-review` from Claude you need the
Codex CLI; to use `/claude-review` from Codex you need the Claude CLI.

## Quickstart

```bash
git clone https://github.com/dgrissen2/persona-review-kit.git
cd persona-review-kit
./install.sh
```

`install.sh` is **global-only**. It:
- symlinks the codex-\* twins + `persona-registry` into `~/.claude/skills/`,
- symlinks the claude-\* twins + `persona-registry` into `~/.codex/skills/`, and
- copies the personas into `~/.config/persona-review-kit/personas/`.

It writes nothing into any project directory, and re-running it is safe (idempotent). Keep the
cloned repo in place — the installed skills are symlinks back into it.

```bash
./uninstall.sh   # removes only this kit's symlinks + personas dir; leaves everything else alone
```

## Usage

You don't run scripts or pass flags by hand. Invoke a skill by name in your CLI and just say what you
want — it works out the scope, **picks up your intent and focus automatically** from how you phrase
it, and runs the review.

### From Claude Code — review with Codex

```text
/codex-review branch — focus on whether the auth refactor is correct, skip style nits
/codex-plan-review plan.md spec.md — check it with the architect and red-team lenses
check after you're done with /codex-strategy-review — do the conclusions actually hold? use quant and cio personas
have richard feynman's global persona review here and with /codex-strategy-review to write a tight conclusion
```

### From Codex — review with Claude

```text
review for logic adherence when complete with /claude-review
check with architect here and with /claude-plan-review to ensure the plan is simple and robust
/claude-strategy-review strategy.md — stress-test the hidden assumptions, use the CIO and portfolio manager personas
```

Both directions return the same shape: a `PASS / CONDITIONAL PASS / FAIL` verdict and a findings
table. Each persona runs independently, then a synthesis pass deduplicates across them.

### Intent and focus are automatic

You never type flags. Whatever you say *becomes* the review's framing. In
`/codex-review branch — focus on whether the auth refactor is correct, skip style nits`, the kit
captures the **intent** ("the auth refactor") and the **focus** ("is the logic correct, skip style")
and applies them for you. A guardrail still surfaces every CRITICAL/HIGH finding even when it falls
outside your focus. (Power users can set `--intent` / `--focus` explicitly, but you rarely need to.)

## Personas reference

The kit ships **13 personas**. Name them in your request — e.g. *"…review this plan with the
**architect** and **red-team** lenses"* — to run several as independent overlays on one artifact,
synthesized into a single verdict. See [`DISCLAIMER.md`](./DISCLAIMER.md) about the real-named personas.

| Persona | What it is | Use it to… |
|---|---|---|
| [`architect`](./personas/engineering/architect.md) | Systems architect | check integration, contracts, and architectural fit |
| [`cto`](./personas/engineering/cto.md) | Pragmatic engineering exec | weigh type safety, performance, and complexity budget |
| [`red-team`](./personas/engineering/red-team.md) | Adversarial security reviewer | hunt injection, edge cases, and trust-boundary failures |
| [`software-architect`](./personas/engineering/software-architect.md) | Production-systems architect | pressure-test data contracts, failure modes, and determinism |
| [`junior-engineer`](./personas/engineering/junior-engineer.md) | Sharp, literal "honest reader" | surface ambiguity and unstated assumptions in a spec |
| [`cio`](./personas/strategy/cio.md) | Decision authority | judge what's implementable vs. what needs human judgment |
| [`portfolio-manager`](./personas/strategy/portfolio-manager.md) | Risk & governance PM | check risk, sizing, and governance |
| [`quant`](./personas/strategy/quant.md) | Senior quant researcher | stress-test math, assumptions, and evidence |
| [`arbiter`](./personas/strategy/arbiter.md) | Decision reconciler | reconcile conflicting reviews into one call |
| [`charlie-mcelligott`](./personas/market/charlie-mcelligott.md) | Positioning / market-structure lens | read flows, positioning, and second-order effects |
| [`degen-wsb-trader`](./personas/market/degen-wsb-trader.md) | Retail momentum / meme speculator | sanity-check narrative, hype, and retail-flow risk |
| [`language-learning-expert`](./personas/education/language-learning-expert.md) | Italian / CEFR language pedagogy | review language-learning plans and exercises |
| [`richard-feynman`](./personas/education/richard-feynman.md) | First-principles explainer | demand a clear, simple, honest explanation |

**Add your own** — drop a markdown file with a small frontmatter block into the library (or a
project-local folder). List what's available from either platform:

```bash
python3 ~/.claude/skills/persona-registry/scripts/persona_registry.py --list
```

Discovery order (first match wins): `PERSONA_PATHS` env → `--persona-dir` → the installed kit
library (`~/.config/persona-review-kit/personas/`) → project-local `./.claude/personas`,
`./personas`, `./docs/personas` → `~/.claude/personas`. See
[`docs/persona-registry-guide.md`](./docs/persona-registry-guide.md) and
[`CONTRIBUTING.md`](./CONTRIBUTING.md).

## Documentation

- [`docs/persona-registry-guide.md`](./docs/persona-registry-guide.md) — the persona registry and how to add personas.
- [`docs/running-reviews-guide.md`](./docs/running-reviews-guide.md) — running code / plan / strategy reviews in both directions.
- [`CHANGELOG.md`](./CHANGELOG.md) — release history.

## License

[MIT](./LICENSE). Please read the [`DISCLAIMER.md`](./DISCLAIMER.md) regarding the real-named
caricature personas.
