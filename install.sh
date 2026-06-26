#!/usr/bin/env bash
# install.sh — global-only installer for persona-review-kit.
#
# The kit is symmetric: skills you run FROM Claude Code (the codex-* twins) install into
# ~/.claude/skills/, and skills you run FROM Codex (the claude-* twins) install into
# ~/.codex/skills/. The shared persona-registry installs into both. Personas copy into
# ~/.config/persona-review-kit/personas/. Nothing is written into any project directory.
#
# Idempotent: re-running produces the same state without error. The skill symlinks point
# back into this cloned repo, so keep the repo in place after installing. Respects $HOME.

set -euo pipefail
: "${HOME:?HOME must be set and non-empty}"   # scoped rm -rf targets depend on it

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CLAUDE_SKILLS="${HOME}/.claude/skills"   # run from Claude Code -> the codex-* twins live here
CODEX_SKILLS="${HOME}/.codex/skills"     # run from Codex        -> the claude-* twins live here
KIT_PERSONAS="${HOME}/.config/persona-review-kit/personas"

# persona-registry installs on BOTH sides so either platform's resolver finds it.
CLAUDE_SIDE=(persona-registry codex-review codex-plan-review codex-strategy-review)
CODEX_SIDE=(persona-registry claude-review claude-plan-review claude-strategy-review)

link_skill() {  # link_skill <skill> <dest-skills-dir>
    local skill="$1" destdir="$2"
    local src="${SCRIPT_DIR}/skills/${skill}" dst="${destdir}/${skill}"
    if [ ! -d "${src}" ]; then
        echo "  ! missing skill source: ${src}" >&2
        exit 1
    fi
    if [ -L "${dst}" ]; then
        # Existing symlink: only refresh if it already points into THIS kit clone; never
        # silently repoint a symlink the user created to somewhere else.
        if [ "$(readlink "${dst}")" != "${src}" ]; then
            echo "  ! ${dst} is a symlink to $(readlink "${dst}") (not this kit); skipping" >&2
            return
        fi
    elif [ -e "${dst}" ]; then
        echo "  ! ${dst} exists and is not a symlink — not managed by this kit; skipping" >&2
        return
    fi
    ln -sfn "${src}" "${dst}"
    echo "  linked ${skill} -> ${destdir}"
}

echo "persona-review-kit: installing (global only)"
echo "  source repo : ${SCRIPT_DIR}"
mkdir -p "${CLAUDE_SKILLS}" "${CODEX_SKILLS}"
for s in "${CLAUDE_SIDE[@]}"; do link_skill "${s}" "${CLAUDE_SKILLS}"; done
for s in "${CODEX_SIDE[@]}";  do link_skill "${s}" "${CODEX_SKILLS}";  done

# Copy personas into the neutral global library (idempotent: clear + recopy).
# Verify the source exists BEFORE wiping the previous install's personas (fail-fast).
[ -d "${SCRIPT_DIR}/personas" ] || { echo "  ! missing personas source: ${SCRIPT_DIR}/personas" >&2; exit 1; }
mkdir -p "$(dirname "${KIT_PERSONAS}")"
rm -rf "${KIT_PERSONAS}"
mkdir -p "${KIT_PERSONAS}"
cp -R "${SCRIPT_DIR}/personas/." "${KIT_PERSONAS}/"
echo "  copied personas -> ${KIT_PERSONAS}"

echo "persona-review-kit: install complete."
echo "  From Claude Code:  /codex-review  /codex-plan-review  /codex-strategy-review"
echo "  From Codex:        /claude-review  /claude-plan-review  /claude-strategy-review"
