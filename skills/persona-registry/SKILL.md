---
name: persona-registry
description: "Resolve shared review personas from the persona-review-kit library. Use when a review skill needs to list, resolve, or apply persona lenses across Claude, Codex, or project-local contexts."
---

# Persona Registry

Shared resolver for persona avatar files. Review skills should consume personas
through `scripts/persona_registry.py` instead of hardcoding persona IDs.

After installation (`install.sh`), the kit's persona library lives at:

```text
~/.config/persona-review-kit/personas/
```

## Discovery Order

The resolver uses first-match-wins alias resolution, highest priority first:

1. `PERSONA_PATHS` (explicit override; `os.pathsep`-separated files, dirs, or globs)
2. Additional `--persona-dir` files, dirs, or globs
3. `~/.config/persona-review-kit/personas/**/*.md` — the installed kit library (top default source)
4. Project-local `./.claude/personas/`, `./personas/`, `./docs/personas/`
5. `~/.claude/personas/**/*.md` — your personal global Claude folder

**Precedence contract:** because resolution is first-match-wins, the installed kit
library (3) wins over a project-local persona (4) of the same id. This is a deliberate
choice for a global-install kit — the curated library is the source of truth unless you
explicitly override it via `PERSONA_PATHS` or `--persona-dir`.

## CLI

```bash
python scripts/persona_registry.py --list
python scripts/persona_registry.py --resolve quant,pm,/path/custom.md
```
