---
name: example-skill
description: Template skill demonstrating proper structure. Use this as a reference when creating new skills. Copy this folder and modify for your use case.
type: template
---

# Example Skill

This is a template skill. Key things to note:

## Structure

- `SKILL.md` is required with YAML frontmatter (`name`, `description`)
- Optional directories: `scripts/`, `references/`, `assets/`
- Keep SKILL.md under 500 lines

## Frontmatter Requirements

```yaml
---
name: kebab-case-name      # Required, max 64 chars
description: Short desc    # Required, max 1024 chars, no angle brackets
display_title: Nice Name   # Optional, used in API upload
---
```

## Creating a New Skill

1. Run `make init SKILL=my-skill-name`
2. Edit the generated `SKILL.md`
3. Add scripts, references, or assets as needed
4. Run `make validate SKILL=my-skill-name`
5. Run `make upload SKILL=my-skill-name`

## Design Principles

From Anthropic's skill-creator guidance:

### Concise is Key
Claude is already smart. Only add context it doesn't have. Don't over-explain.

### Progressive Disclosure
- **Metadata** (~100 words): Always loaded via frontmatter
- **SKILL.md body** (<5k words): Loaded when skill is triggered
- **Bundled resources**: Loaded as needed via `references/`

### Set Appropriate Degrees of Freedom
Match specificity to task fragility:
- High fragility (exact format needed) → Be very specific
- Low fragility (flexible approach OK) → Be general

### Size Limits
- SKILL.md should stay under 500 lines
- Split into `references/` when approaching this limit
- Total body content should be under 5000 words

## Directory Structure

```
my-skill/
├── SKILL.md           # Required - main skill definition
├── scripts/           # Optional - automation scripts
│   └── helper.py
├── references/        # Optional - additional documentation
│   └── api-guide.md
└── assets/            # Optional - images, templates, etc.
    └── template.json
```
