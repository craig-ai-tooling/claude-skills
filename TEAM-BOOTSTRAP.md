# Team bootstrap: Spectro Cloud SA AI toolkit

Sets up the skills and CLIs Craig Smith demoed at Demo Days on 9/22/26: the
`spectrocloud-*` Palette skills, doc/deck generators, the `super` skill, `opp-axi`,
`palette-axi`, `gh-axi`, `gws-axi`, and a private per-account folder repo.

**Pilot.** Kevin Reeuwijk and Ray Krueger go first. This repo is the pilot's home; the
kit moves to the Spectronauts org once the pilot has run. Report what broke to Craig.

## How to use it

1. Open Claude Code in your home directory (terminal or VS Code, either works).
2. Paste everything inside the fence below.
3. Answer its interview. It asks before each tier and stops at the one you choose.

| Tier | Installs | Time |
|---|---|---|
| 1 | the skills in this repo | ~10 min |
| 2 | opp-axi, palette-axi, gh-axi, gws-axi, an account-folder repo, the SE write rules | ~30 min, most of it Salesforce and Google sign-in |
| 3 | a voice skill built from your own sent mail and Slack | an afternoon |

```text
You are setting up the Spectro Cloud SA AI toolkit on this machine. Work through the tiers
below in order. Before each tier, tell me in two lines what it installs and ask whether to
continue. Stop at the first tier I decline. Never put an API key or token in a file inside
a git repo, and never print one back to me.

TOOLKIT_REPO=https://github.com/craig-ai-tooling/claude-skills

## Interview first (one message, all questions at once)
1. Your name, your initials, and your Salesforce SA assignment value (usually FirstLast,
   e.g. CraigSmith; I can look it up after sf login if you don't know it).
2. Mac or Linux? Do you use Wispr Flow or MacWhisper?
3. Where should your account folders live? (default ~/code/customer-opportunities)
4. Do you have a Palette API key, and where do you keep it (1Password vault name, or env)?
5. Which tier do you want to reach: 1 (skills), 2 (skills + CLIs + account folders),
   or 3 (adds a voice skill)?

## Tier 0: check the basics
- Confirm: claude, git, python3 >= 3.10, node >= 20, gh (logged in). Report what is
  missing with the install command for my OS. Do not install system packages yourself.
- Tell me to connect the Super (Slite) MCP in Claude Code if it is not connected; the
  super skill needs it, plus curl and jq.

## Tier 1: shared skills
- Clone TOOLKIT_REPO to ~/code/sa-ai-toolkit (or pull if it exists).
- Symlink every directory under its skills/ into ~/.claude/skills/, except
  craigcloud-design and example-skill. Do not overwrite an existing skill of the same name;
  list any conflict and ask.
- List what got installed, one line each.

## Tier 2: CLIs, account folders, write rules
- Install opp-axi and palette-axi:
    curl -fsSL https://raw.githubusercontent.com/craig-ai-tooling/opp-axi/main/scripts/install.sh | bash
    curl -fsSL https://raw.githubusercontent.com/craig-ai-tooling/palette-axi/main/scripts/install.sh | bash
- Install gh-axi and gws-axi from npm (npm install -g gh-axi gws-axi). Run
  `gws-axi doctor` and walk me through its auth steps. Do not install anything that
  adds mail sending.
- Salesforce: if `sf org list` shows no spectrocloud org, tell me to run
  `sf org login web --alias spectrocloud` myself.
- Add to my shell profile (not a repo): OPP_SE=<my SA value>, OPP_INITIALS=<initials>,
  OPP_REPO=<account folder path>, and OPP_WISPR=off unless I use Wispr Flow.
  For Palette: PALETTE_AXI_VAULT=<vault> if I use 1Password, otherwise tell me to export
  PALETTE_API_KEY in my profile myself.
- Create the account folder repo if missing: git init, a README, and an AGENTS.md
  containing the write rules below. Keep it private. Then run `opp-axi scaffold` to
  create one folder per open opp where I am the SA, and `opp-axi doctor`.
- Run `opp-axi opps` and `palette-axi --help` and show me the first few lines of each
  as proof they work.

Write rules (put these in the account repo AGENTS.md and in ~/.claude/CLAUDE.md):
- Never send email. Draft it and hand it back.
- Salesforce: SE-owned fields only, only on opps where I am the SA, only through
  opp-axi (`opp-axi activity`, `opp-axi field`). Never `sf data update record -v`.
- SE Activity entries are prepended, never overwritten, dated M/D/YY with my initials.
- Internal pricing, roadmap and competitive material never goes in anything
  customer-facing.

## Tier 2 also: my ~/.claude/CLAUDE.md
Append (do not replace) a short section with:
- the write rules above;
- "Prefer the *-axi CLIs over raw sf/gws/gh and over MCP.";
- "Use Opus to plan and review; pass model sonnet or haiku to sub-agents doing research
  or execution.";
- "Before building a customer environment from a call, read the transcript and the
  account folder's OPP.md, learnings.md and poc/.";
- "Load the spectrocloud-common skill before any Palette API work."
Show me the diff before writing.

## Tier 3: voice skill
Interview me for voice the way the voice-capture method does: ask for 20 of my sent
emails and 20 Slack messages (I will paste or point you at them), measure length,
greetings, sign-offs and hedges, then ask 10 questions about how I write to customers vs
internal. Write ~/.claude/skills/<my-first-name>-voice/SKILL.md from what you measured.
Keep any customer names out of the skill file.

## Finish
Print a checklist: each tier, done or skipped, and what I still have to do by hand.
Then give me one first prompt to try, using a real call transcript from this week:
"Read <transcript> and <account folder>. Build what we promised on this call."
```
