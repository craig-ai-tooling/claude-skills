# Claude Skills Repository

Single source of truth for custom Claude Agent Skills with automated building and deployment via GitHub Actions.

**Spectro SAs:** start with [TEAM-BOOTSTRAP.md](TEAM-BOOTSTRAP.md). It installs these skills and the SA CLIs from one prompt.

## Quick Start

```bash
# Create a new skill
make init SKILL=my-skill-name

# Edit the skill
vim skills/my-skill-name/SKILL.md

# Validate
make validate SKILL=my-skill-name

# Test locally with Claude Code
make sync

# Upload to Anthropic API
export ANTHROPIC_API_KEY=sk-ant-...
make upload SKILL=my-skill-name
```

## Commands

| Command | Description |
|---------|-------------|
| `make init SKILL=name` | Create new skill from template |
| `make build` | Package all skills to `dist/` |
| `make build SKILL=name` | Package specific skill |
| `make upload SKILL=name` | Upload specific skill to API |
| `make upload-all` | Upload all skills to API |
| `make sync` | Symlink skills to `~/.claude/skills` |
| `make sync-project` | Symlink skills to `.claude/skills` |
| `make validate` | Validate all skills |
| `make validate SKILL=name` | Validate specific skill |
| `make list` | List all local skills |
| `make list-remote` | List skills on Anthropic API |
| `make delete ID=skill_id` | Delete skill from API |
| `make clean` | Remove `dist/` |

## Skill Structure

```
skills/
└── my-skill/
    ├── SKILL.md           # Required - main skill definition
    ├── scripts/           # Optional - automation scripts
    ├── references/        # Optional - additional documentation
    └── assets/            # Optional - images, templates, etc.
```

### SKILL.md Requirements

```yaml
---
name: kebab-case-name      # Required, max 64 chars
description: Short desc    # Required, max 1024 chars, no angle brackets
display_title: Nice Name   # Optional, used in API upload
---

# Skill Title

Skill content here...
```

### Design Principles

From Anthropic's skill-creator guidance:

1. **Concise is key** - Claude is already smart, only add context it doesn't have
2. **Progressive disclosure** - Metadata (~100 words) always loaded, SKILL.md body (<5k words) when triggered, bundled resources as needed
3. **Set appropriate degrees of freedom** - Match specificity to task fragility
4. **Size limits** - SKILL.md should stay under 500 lines; split into `references/` when approaching this limit

## Local Development

### Testing with Claude Code

Symlink your skills to Claude Code's skills directory:

```bash
# Global (all Claude Code sessions)
make sync

# Project-specific (current directory only)
make sync-project
```

After syncing, your skills will be available in Claude Code. Edit the source files and re-run Claude Code to test changes.

### Validation

```bash
# Validate all skills
make validate

# Validate specific skill
make validate SKILL=my-skill-name
```

Validation checks:
- YAML frontmatter exists and is valid
- `name` is kebab-case, max 64 characters
- `description` is present, max 1024 characters, no angle brackets
- SKILL.md is under 500 lines
- Body content is under 5000 words

## CI/CD Pipeline

### Pull Requests

`.github/workflows/ci.yml` runs on PRs that modify `skills/**`:
- Validates all changed skills
- Fails PR if validation errors found

### Deployment

`.github/workflows/deploy.yml` runs on push to `main` when `skills/**` changes:
- Detects which skills changed
- Validates each changed skill
- Packages each to `.skill` file
- Uploads to Anthropic API
- Stores packaged skills as artifacts

Manual deployment via workflow dispatch:
- Deploy specific skill by name
- Deploy all skills at once

### Releases

When you create a Git tag, the deploy workflow will:
- Package all skills
- Create a GitHub Release with `.skill` files attached

## GitHub Setup

### Required Secrets

Add to your repository's Settings → Secrets and variables → Actions:

| Secret | Description |
|--------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key for skill uploads |

### Getting an API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Navigate to API Keys
3. Create a new key
4. Add it as a repository secret

## API Reference

### Upload Skill

```bash
curl -X POST "https://api.anthropic.com/v1/skills" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: skills-2025-10-02" \
  -F "display_title=My Skill Name" \
  -F "files=@my-skill.zip"
```

### List Skills

```bash
curl "https://api.anthropic.com/v1/skills" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: skills-2025-10-02"
```

### Delete Skill

```bash
curl -X DELETE "https://api.anthropic.com/v1/skills/skill_01abc123" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: skills-2025-10-02"
```

## Directory Structure

```
claude-skills/
├── skills/                     # All skills live here
│   └── doc-writer/             # one directory per skill
│       └── SKILL.md
├── scripts/                    # Tooling scripts
│   ├── init_skill.py           # Initialize new skill
│   ├── package_skill.py        # Package skill to .skill/.zip
│   ├── quick_validate.py       # Validate SKILL.md frontmatter
│   ├── upload_skill.py         # Upload to Anthropic API
│   └── sync_local.sh           # Symlink to ~/.claude/skills
├── .github/
│   └── workflows/
│       ├── ci.yml              # Validate on PR
│       └── deploy.yml          # Build + upload on push to main
├── dist/                       # Output directory (gitignored)
├── Makefile
├── .gitignore
└── README.md
```

## License

MIT
