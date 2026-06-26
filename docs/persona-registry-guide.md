# Persona Registry Guide

The persona registry is the shared layer every review skill uses to find and load
personas. This guide explains how it works and how to add your own personas.

## What a persona is

A persona is a markdown file that biases a language model toward a particular *mode of
analysis*. It is an analytical lens, not an impersonation. Each file starts with a small
YAML frontmatter block:

```markdown
---
id: red-team
name: "Red Team"
aliases: [redteam, adversarial, security]
domain: engineering
status: canonical
version: 2026-06-01
---

# Persona Avatar: Red Team
...
```

- `id` — the canonical identifier (kebab-case).
- `name` — human-readable display name.
- `aliases` — alternate tokens that resolve to this persona.
- `domain` — grouping (engineering, strategy, market, education, …). If omitted, the
  parent folder name is used.
- `status` — `canonical` for first-class personas.

The body is free-form; everything after the frontmatter is the lens prompt.

## How discovery works

The resolver (`skills/persona-registry/scripts/persona_registry.py`) scans a set of
sources in priority order and uses **first-match-wins** alias resolution. The order is:

1. `PERSONA_PATHS` env var — `os.pathsep`-separated files, dirs, or globs (explicit override)
2. `--persona-dir` arguments
3. `~/.config/persona-review-kit/personas/**/*.md` — the installed kit library (top default)
4. project-local `./.claude/personas/`, `./personas/`, `./docs/personas/`
5. `~/.claude/personas/**/*.md` — your personal global Claude folder

Because the first match wins, the installed library (3) takes precedence over a
project-local persona (4) with the same `id`. To make a project override a bundled
persona, point `PERSONA_PATHS` at your project's folder — it sits above the library.

## CLI

```bash
# List every persona the resolver can see (markdown table)
python3 skills/persona-registry/scripts/persona_registry.py --list

# Same, as JSON
python3 skills/persona-registry/scripts/persona_registry.py --list --json

# Resolve a mix of ids, aliases, and direct file paths
python3 skills/persona-registry/scripts/persona_registry.py \
  --resolve architect,security,/path/to/custom_persona.md

# Add an extra source for this invocation only
python3 skills/persona-registry/scripts/persona_registry.py \
  --list --persona-dir ./my-team-personas
```

`--resolve` exits non-zero and prints the known aliases if a token can't be resolved,
which makes it easy to script as a validation check.

> **Before installing:** run `--list` from the repo root so the project-local `./personas/`
> default source is picked up — e.g. `python3 skills/persona-registry/scripts/persona_registry.py --list`.
> From a subdirectory (or after `./install.sh`), the resolver reads the installed library at
> `~/.config/persona-review-kit/personas/` instead. To list the bundled personas from anywhere
> pre-install, pass `--persona-dir /path/to/repo/personas`.

## Adding a persona

1. Drop an `.md` file (with frontmatter) into one of the discovery locations — usually a
   new file under `personas/<domain>/` in this repo, or your project's
   `./.claude/personas/`.
2. If you add it to this repo, also add a `registry.yaml` entry (see `CONTRIBUTING.md`).
3. Run `--list` to confirm it appears, and `--resolve <id>` to confirm it loads.
4. Run `./install.sh` to copy repo personas into the global library.

Keep persona files portable: relative paths only, no `source_paths:` block, no
home-absolute paths.

## Using personas from other skills

Review skills don't hardcode persona ids — they call the resolver. For example, the codex
skills accept `--personas architect,red-team` and resolve each token through this
registry, so any persona you add is immediately available to them.
