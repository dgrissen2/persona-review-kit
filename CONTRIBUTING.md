# Contributing

Thanks for improving the persona-review-kit. This guide covers the repo layout, how to
add a persona, and the persona-discovery precedence contract.

## Repo layout

```
persona-review-kit/
├── README.md
├── LICENSE                     # MIT
├── CONTRIBUTING.md             # this file
├── DISCLAIMER.md               # real-named caricature personas
├── CHANGELOG.md  VERSION
├── install.sh / uninstall.sh   # global-only, dual-target install
├── .gitignore
├── personas/
│   ├── registry.yaml           # manifest of bundled personas (paths relative to here)
│   ├── engineering/            # architect, cto, red-team, software-architect, junior-engineer
│   ├── strategy/               # cio, portfolio-manager, quant, arbiter
│   ├── market/                 # charlie-mcelligott, degen-wsb-trader
│   └── education/              # language-learning-expert, richard-feynman
├── skills/
│   ├── persona-registry/       # the shared resolver (scripts/persona_registry.py) + SKILL.md
│   ├── codex-review/           # run from Claude -> Codex code review   (SKILL.md + scripts/)
│   ├── codex-plan-review/      # run from Claude -> Codex plan review
│   ├── codex-strategy-review/  # run from Claude -> Codex strategy review
│   ├── claude-review/          # run from Codex  -> Claude code review   (SKILL.md + scripts/ + agents/)
│   ├── claude-plan-review/     # run from Codex  -> Claude plan review
│   ├── claude-strategy-review/ # run from Codex  -> Claude strategy review
│   └── claude_shared_runner.py # shared runner imported by the claude-* twins
└── docs/
    ├── persona-registry-guide.md
    └── running-reviews-guide.md
```

> **Install targets:** the `codex-*` twins + `persona-registry` symlink into `~/.claude/skills/`;
> the `claude-*` twins + `persona-registry` symlink into `~/.codex/skills/`; personas copy into
> `~/.config/persona-review-kit/personas/`.

## Adding a new persona

A persona is one markdown file with a small YAML frontmatter block. To add one:

1. **Create the file** under the right domain folder, e.g.
   `personas/strategy/my-persona.md`:

   ```markdown
   ---
   id: my-persona
   name: "My Persona (Short Descriptor)"
   aliases: [my_persona, short-alias]
   domain: strategy
   status: canonical
   version: 2026-06-01
   ---

   # Persona Avatar: My Persona

   **Role:** ...

   ## 1. Operating Instruction
   ...
   ```

   Useful sections to include: Operating Instruction, Core Worldview, what the persona
   weights most heavily, Hard Rules (red lines), and Language & Tone. See an existing
   persona for the shape.

2. **Add a registry entry** to `personas/registry.yaml` (keep `path:` relative to the
   `personas/` directory):

   ```yaml
     - id: my-persona
       name: "My Persona (Short Descriptor)"
       domain: strategy
       path: strategy/my-persona.md
       aliases: [my_persona, short-alias]
   ```

3. **Verify it resolves**:

   ```bash
   python3 skills/persona-registry/scripts/persona_registry.py --list
   python3 skills/persona-registry/scripts/persona_registry.py --resolve my-persona
   ```

   `--list` should show your persona; `--resolve` should print its file path.

4. **Reinstall** (`./install.sh`) to copy it into `~/.config/persona-review-kit/personas/`.

> Do **not** hard-code an absolute home path (any path under your OS home directory) or a
> `source_paths:` block in a persona — keep paths relative and frontmatter portable.

## Persona discovery precedence (contract)

The resolver uses **first-match-wins** discovery in this fixed order:

1. `PERSONA_PATHS` env var (explicit override)
2. `--persona-dir` arguments
3. `~/.config/persona-review-kit/personas/` — the installed kit library
4. project-local `./.claude/personas/`, `./personas/`, `./docs/personas/`
5. `~/.claude/personas/` — your personal global Claude folder

**Important:** because resolution is first-match-wins, the installed kit library (3) wins
over a project-local persona (4) of the same `id`. This is a deliberate choice for a
global-install kit — the curated library is the source of truth. If you want a project to
override a bundled persona, point `PERSONA_PATHS` (or `--persona-dir`) at your project's
persona folder, which sits above the library in the order.

## Code style

- Python: standard library only (no third-party runtime deps), type hints on signatures,
  ruff-clean.
- Keep shipped files free of personal/home-absolute paths and any private project
  identifiers. CI-style checks reject home paths and secrets.

## Pull requests

One focused change per PR. For a new persona, include the `--list`/`--resolve` output in
the PR description so reviewers can see it resolves.
