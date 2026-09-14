# cos-prior-art — planning checks what already exists before it plans a build

Craig, 9/14/26: "I'd like to make sure that I don't recreate the wheel if things
already exist... If the tooling isn't built well or doesn't include all the use
cases we need, then let's go ahead and make sure we build it."

`ralph-ready-planning` Phase 0 investigates the repo in front of it and never
looks outside. `gws-axi` sat installed and unused from 9/8 to 9/14/26 while 33
sessions failed on raw `gws`; the https://axi.md catalog lists 74 tools.

## Files touched

```allowlist
skills/ralph-ready-planning/SKILL.md
ralph/IMPLEMENTATION_PLAN.md
```

## Tasks

- [x] Phase 0 of `skills/ralph-ready-planning/SKILL.md`: when the plan builds a tool, CLI or integration, check the axi.md catalog, `npm search`, PyPI, GitHub and `~/code/ai-lawnmower/REGISTRY.md` first; the PRD records what was checked and the missing use case, or the plan adopts instead. Verify: `grep -q 'axi.md' skills/ralph-ready-planning/SKILL.md` exits 0 and `make validate` exits 0.
