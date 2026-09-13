---
name: spectrocloud-prompts
description: "Write the agent prompt when Palette / Spectro Cloud work is being fanned out to subagents, background loops, or another machine -- so each agent is told to READ the exact spectrocloud-* skills by name instead of improvising, and writes findings to a local ./learnings.md rather than back into the skills repo. Use when Craig says: use agents for this, fan this out, send an agent to do X, use ultracode or Fable on it, use the spectrocloud skills that make sense, push a prompt I can point Claude at, write me a prompt for this, do this on the other box. Also use when the main session is running low on context and Palette work should be delegated. Includes a mandatory critic pass over the drafted prompt before it is handed back."
---

# Spectro Cloud Prompt Generator

Generate prompts that **preserve context** and **force skill usage**.

## Critical Understanding

### Skills are GLOBAL
Claude Code automatically loads skills from `~/.claude/skills/`. You do NOT need:
- File paths to skills
- Directory references
- Any special loading

Just say "READ the `spectrocloud-common` skill" and Claude has access.

### Agents Must READ Skills
Saying "use the skill" is not enough. Agents ignore vague instructions. Be explicit:

**BAD**: "Use the spectrocloud-common skill for auth"
**GOOD**: "FIRST, READ the `spectrocloud-common` skill. Follow its API authentication pattern exactly."

### Learnings Stay Local
Don't write learnings back to the skills repo. Write to the current working directory:
- `./learnings.md` - Capture issues, solutions, new patterns
- At session end, user can review and merge to skills if valuable

---

## Agent Instructions Template

Every agent prompt MUST include this pattern:

```
BEFORE doing anything:
1. READ the `spectrocloud-[name]` skill file
2. Follow its patterns EXACTLY - do not improvise
3. If something isn't in the skill, document it in ./learnings.md

You have access to these skills (READ THEM):
- `spectrocloud-common` - [what to look for]
- `spectrocloud-[specific]` - [what to look for]
```

---

## Learnings Agent Pattern

Instead of writing back to the skills repo, use this local pattern:

```
## Learnings Tracker Agent

Your job: Document issues and solutions as they occur.

Output file: ./learnings.md (in current working directory)

Format:
```markdown
# Session Learnings - [DATE]

## Issues Encountered

### [Issue Title]
- **What happened**:
- **Root cause**:
- **Solution**:
- **Skill gap**: Which skill should have covered this?

## New Patterns Discovered
[Anything that worked well but isn't documented]

## Skill Improvement Suggestions
[Specific additions to specific skills]
```

At session end, user reviews ./learnings.md and decides what to merge into skills.
```

---

## Prompt Critic Loop (MANDATORY)

**You MUST run this loop before presenting any prompt to the user.**

### Step 1: Generate Initial Prompt
Draft the prompt based on user requirements.

### Step 2: Spawn Critic Agent
Use this exact agent prompt:

```
You are a prompt critic. Your job is to find problems, not approve.

Review this prompt against the checklist below. For EACH item:
- If it passes: brief confirmation
- If it FAILS: specific quote of the problem + how to fix it

### Checklist

**Skill Enforcement**
- [ ] Does it say "READ the skill" not just "use the skill"?
- [ ] Are skill names exact? (`spectrocloud-common` not `common`)
- [ ] Does each agent have explicit READ instructions?

**Context Efficiency**
- [ ] Heavy work delegated to agents?
- [ ] Main session orchestrates only?
- [ ] No verbose exploration in main session?

**Learnings**
- [ ] Learnings write to ./learnings.md (local)?
- [ ] No references to skills repo paths?
- [ ] User reviews learnings at end?

**Agent Specificity**
- [ ] Each agent has ONE clear job?
- [ ] Agents told exactly what to return?
- [ ] Failure handling explicit?

**Completeness**
- [ ] All user requirements addressed?
- [ ] No ambiguous placeholders without explanation?
- [ ] Demo/workflow flow makes sense?

### Response Format
ISSUES FOUND: [number]

[For each issue:]
**Issue N**: [Checklist item that failed]
- Problem: "[exact quote from prompt]"
- Fix: [specific correction]

If zero issues: "APPROVED - prompt is ready"
```

### Step 3: Iterate Until Approved
- If critic returns issues → fix them → re-submit to critic
- Repeat until critic returns "APPROVED"
- Maximum 3 iterations (if still failing, ask user for guidance)

### Step 4: Present to User
Only show the final approved prompt.

---

### Why This Matters
- Catches skill reference errors before execution fails
- Ensures context efficiency (agents do heavy lifting)
- Validates completeness against user requirements
- Forces explicit over implicit patterns

---

## Prompt: 2-Node Edge Cluster Deployment

```
## Task: Deploy 2-Node Edge Cluster

### How to Use Skills
Skills are globally available. Before each phase, READ the relevant skill files.
Do NOT improvise - follow skill patterns exactly.

### Required Skills (READ THESE)
- `spectrocloud-common` - API auth, project lookup, pack discovery with pagination
- `spectrocloud-appliance-mode` - CanvOS build, .arg config, user-data, ISO versioning
- `spectrocloud-cluster-profiles` - Pack values, version alignment, Terraform patterns
- `spectrocloud-clusters` - 2-node structure, edge tokens, Terraform patterns
- `spectrocloud-troubleshooting` - Event monitoring, known errors

### Learnings
Write any issues/discoveries to: ./learnings.md
Do NOT attempt to update the skills repo.

---

### Phase 1: Setup [Main Session]

FIRST: READ `spectrocloud-common` skill.

1. Get API key via MCP tools (pattern in skill)
2. **ASK user**: Which Palette project to use?
3. Look up project UID by name (pattern in skill)
4. READ `spectrocloud-clusters` skill for edge token creation
5. Create edge token - NOTE: tenant-scoped, NO ProjectUid header

---

### Phase 2: Build [Agent]

Spawn build agent with this prompt:

```
You are building CanvOS artifacts for a 2-node Edge cluster.

FIRST: READ the `spectrocloud-appliance-mode` skill completely.
Follow its patterns exactly.

Tasks:
1. SSH to build machine
2. Clone CanvOS repo
3. Create .arg file (skill has 2-node example - K3s, TWO_NODE=true)
4. Create user-data (skill has bridge networking example)
5. Run: earthly +iso && earthly --push +provider-image  # ISO first, then push provider images
6. IMPORTANT: Run `docker images | grep [REPO]` and capture EXACT tag
7. Rename ISO with version per skill guidance

Return to main session:
- Exact image tag from docker images output
- ISO filename with version

If anything fails or is unclear, write to ./learnings.md
```

---

### Phase 3: VMs [Main or Agent]

1. Upload versioned ISO to hypervisor
2. Create 2 VMs: 4+ CPU, 8GB+ RAM, 150GB+ disk
3. Boot order: `order=scsi0;ide2;net0` (disk first!)
4. Boot VMs, wait for edge hosts in Palette

---

### Phase 4: Terraform [Main Session]

FIRST: READ `spectrocloud-cluster-profiles` and `spectrocloud-clusters` skills.
Look specifically at: Terraform examples, registry_uid requirement, 2-node structure.

1. Create profiles/ directory with infrastructure profile
   - Use exact image tag from Phase 2
   - Match K8s pack version to what was built
   - Include registry_uid on pack data sources

2. Create clusters/ directory with cluster config
   - Reference profile via data source
   - Use two_node_role: "primary"/"secondary" (Terraform naming)
   - Set is_two_node_cluster = true

3. Apply: profiles first, then clusters

---

### Phase 5: Monitor [Agent]

Spawn monitor agent with this prompt:

```
You are monitoring cluster provisioning events.

FIRST: READ the `spectrocloud-troubleshooting` skill completely.

Tasks:
1. Poll cluster events every 10 seconds (API pattern in skill)
2. Filter noise vs actionable errors (tables in skill)
3. Report actionable issues to main session
4. Continue until cluster state = Running or explicit failure

If you see errors not in the skill, write to ./learnings.md
```

---

### On Failure

READ `spectrocloud-troubleshooting` skill for:
- Known error patterns
- SSH debug commands
- Event analysis

Write discoveries to ./learnings.md

---

### Session End

Review ./learnings.md with user.
User decides what to merge into skills.
```

---

## Prompt: Agent Mode Deployment

```
## Task: Deploy Agent Mode Edge Cluster

### Skills (READ THESE - they are globally available)
- `spectrocloud-common` - Auth, pack discovery
- `spectrocloud-agent-mode` - Installation steps, requirements
- `spectrocloud-cluster-profiles` - BYOOS with "NA" pattern
- `spectrocloud-clusters` - Cluster creation
- `spectrocloud-troubleshooting` - Event monitoring

### Learnings
Write issues to: ./learnings.md

---

### Phase 1: Setup [Main]
READ `spectrocloud-common`, then:
1. Get API key
2. **ASK user**: Which Palette project to use?
3. Look up project UID by name
4. READ `spectrocloud-clusters` for token creation
5. Create edge token (NO ProjectUid header)

### Phase 2: Install [Main]
READ `spectrocloud-agent-mode`, then:
1. Install agent on target nodes (commands in skill)
2. Wait for registration in Palette

### Phase 3: Deploy [Main]
READ `spectrocloud-cluster-profiles`, then:
1. Create profile with BYOOS system.uri: "NA"
2. Create cluster

### Phase 4: Monitor [Agent]
Spawn agent: "READ `spectrocloud-troubleshooting`. Poll events until Running."

### On Failure
Check ./learnings.md, then troubleshooting skill.
```

---

## Key Points

1. **Skills are global** - No paths needed, just READ them
2. **Agents must READ explicitly** - "READ the skill" not "use the skill"
3. **Learnings stay local** - ./learnings.md in working directory
4. **User reviews learnings** - Decides what merges to skills
5. **Don't improvise** - If it's not in a skill, document it, don't guess
