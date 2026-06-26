#!/usr/bin/env bash
# uninstall.sh — reverse install.sh for persona-review-kit.
#
# Removes only the skill symlinks that point back into THIS kit clone (from ~/.claude/skills/
# and ~/.codex/skills/) and its personas directory. A same-named symlink the user created
# pointing elsewhere, real directories, and your own claude_shared_runner.py are left
# untouched. Idempotent. Respects $HOME.

set -euo pipefail
: "${HOME:?HOME must be set and non-empty}"   # scoped rm -rf targets depend on it

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_SKILLS="${HOME}/.claude/skills"
CODEX_SKILLS="${HOME}/.codex/skills"
KIT_CONFIG="${HOME}/.config/persona-review-kit"

CLAUDE_SIDE=(persona-registry codex-review codex-plan-review codex-strategy-review)
CODEX_SIDE=(persona-registry claude-review claude-plan-review claude-strategy-review)

unlink_skill() {  # unlink_skill <skill> <dest-skills-dir>
    local skill="$1" dst="$2/$1"
    if [ -L "${dst}" ]; then
        # Only remove symlinks that point into THIS kit clone — never a user's own same-named link.
        if [ "$(readlink "${dst}")" = "${SCRIPT_DIR}/skills/${skill}" ]; then
            rm -f "${dst}"
            echo "  removed symlink ${dst}"
        else
            echo "  left ${dst} (symlink to $(readlink "${dst}") — not this kit)"
        fi
    elif [ -e "${dst}" ]; then
        echo "  left ${dst} (not a symlink — not managed by this kit)"
    fi
}

echo "persona-review-kit: uninstalling"
for s in "${CLAUDE_SIDE[@]}"; do unlink_skill "${s}" "${CLAUDE_SKILLS}"; done
for s in "${CODEX_SIDE[@]}";  do unlink_skill "${s}" "${CODEX_SKILLS}";  done

if [ -d "${KIT_CONFIG}" ]; then
    rm -rf "${KIT_CONFIG}"
    echo "  removed ${KIT_CONFIG}"
fi

echo "persona-review-kit: uninstall complete."
