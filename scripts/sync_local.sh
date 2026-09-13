#!/usr/bin/env bash
#
# Symlink skills from this repo to Claude Code's skills directory.
# Usage:
#   ./sync_local.sh           # Symlink to ~/.claude/skills/
#   ./sync_local.sh --project # Symlink to ./.claude/skills/
#

set -euo pipefail

# Determine script and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_SRC="$REPO_ROOT/skills"

# Default target directory
TARGET_DIR="$HOME/.claude/skills"
PROJECT_MODE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --project|-p)
            PROJECT_MODE=true
            TARGET_DIR=".claude/skills"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Symlink skills from this repo to Claude Code's skills directory."
            echo ""
            echo "Options:"
            echo "  --project, -p    Symlink to .claude/skills/ in current directory"
            echo "  --help, -h       Show this help message"
            echo ""
            echo "By default, symlinks to ~/.claude/skills/"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Counter for tracking
synced=0
skipped=0
templates=0

# Check a SKILL.md's frontmatter for an exact `type: template` marker.
# Template skills (e.g. skills/example-skill) are reference material, not
# real invokable skills, and must never be symlinked into a live session.
is_template() {
    awk '/^---$/{c++; next} c==1' "$1" | grep -Eq '^type:[[:space:]]*template[[:space:]]*$'
}

echo "Syncing skills to: $TARGET_DIR"
echo ""

# Find all skill directories (directories containing SKILL.md)
for skill_dir in "$SKILLS_SRC"/*/; do
    # Skip if not a directory
    [[ -d "$skill_dir" ]] || continue

    skill_name="$(basename "$skill_dir")"
    skill_md="$skill_dir/SKILL.md"

    # Skip if no SKILL.md
    if [[ ! -f "$skill_md" ]]; then
        echo "  SKIP: $skill_name (no SKILL.md)"
        ((skipped++)) || true
        continue
    fi

    target_link="$TARGET_DIR/$skill_name"

    # Skip template skills (reference material, not real invokable skills).
    # If a symlink from a previous sync already exists, remove it too.
    if is_template "$skill_md"; then
        if [[ -L "$target_link" ]]; then
            rm "$target_link"
            echo "  REMOVE: $skill_name (template, was linked)"
        else
            echo "  SKIP: $skill_name (template)"
        fi
        ((templates++)) || true
        continue
    fi

    # Remove existing symlink or directory
    if [[ -L "$target_link" ]]; then
        rm "$target_link"
    elif [[ -d "$target_link" ]]; then
        echo "  WARN: $skill_name exists as directory, skipping (remove manually to sync)"
        ((skipped++)) || true
        continue
    fi

    # Create symlink
    # Use absolute path for global, relative for project
    if [[ "$PROJECT_MODE" == true ]]; then
        # For project mode, use absolute path to repo
        ln -s "$skill_dir" "$target_link"
    else
        ln -s "$skill_dir" "$target_link"
    fi

    echo "  LINK: $skill_name -> $skill_dir"
    ((synced++)) || true
done

echo ""
echo "Done! Synced $synced skill(s), skipped $skipped, templates $templates"

if [[ "$PROJECT_MODE" == true ]]; then
    echo ""
    echo "Note: Add .claude/ to your project's .gitignore if not already present"
fi
