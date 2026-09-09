# Ralph prompt — lm-92: docs-site scaffolding ships files, not prose

You are one iteration of a loop. You have a completely fresh context: you
remember nothing about earlier iterations except what is written on disk. Do
exactly one task, verify it, record it, commit, and stop.

The milestone: four document-producing skills in this repo hand the agent code
to retype instead of a file to run. Turn that prose into shipped files, make the
two copies of the MkDocs brand stylesheet identical, and add a check that fails
when they drift apart again.

## Do this, in order

1. Read `ralph/IMPLEMENTATION_PLAN.md`. If it has no open `- [ ]` task, stop —
   there is nothing to do. Do not invent one.
2. Read `ralph/PROGRESS.md` to see what earlier iterations already did, and do
   not redo it.
3. Read `ralph/VALIDATION_CONTRACT.md`. It is what "done" means for the whole
   milestone. Your task must move toward it and must never break an assertion
   that already holds.
4. Read this repo's `CLAUDE.md` at its root. Its working rules apply to you.
5. Take the topmost unchecked `- [ ]` task in `ralph/IMPLEMENTATION_PLAN.md`.
   Exactly one.
6. Do that task, and only that task. Stay inside the `Files touched` allowlist
   in `ralph/IMPLEMENTATION_PLAN.md` — a diff outside it is rejected before it
   can ship.
7. Run the task's own verification command, from the repository root. It must
   pass. Run `make validate` as well; it exits 0 today and must still exit 0.
8. Tick the task to `- [x]` and append to `ralph/PROGRESS.md`: the task, the
   command you ran, and its real output — not a summary of what it should have
   said.
9. Commit only the paths you touched. Never `git add -A` — other work may share
   this tree.
10. If every task is `- [x]`, append a final line to `ralph/PROGRESS.md`
    containing only the exit sentinel `RALPH_COMPLETE` — a line of its own,
    nothing else — and stop.

## Things that will waste an iteration if you forget them

- `mkdocs-material` and `puppeteer` are NOT installed here. Never verify by
  running `mkdocs build` or by rendering a PDF. `node --check` and the
  no-argument usage path are the whole check for the render scripts.
- `scripts/secret_scan.py` scans `.mjs` as well as `.md`. Nothing you write may
  contain a lab hostname, a `172.18.x` address, an `op://` reference or a
  personal handle, or `make validate` will fail.
- `scripts/quick_validate.py` caps every `SKILL.md` at 500 lines. Moving blocks
  out of a `SKILL.md` shrinks it; adding to one may not.
- `dist/` is gitignored. Scaffold and package into it freely, and never commit it.
- `.github/workflows/` is out of scope. Do not touch it.

## If you are blocked

Mark the task `- [!]`, write what blocked you in `ralph/PROGRESS.md`, commit
that, and stop. A blocked task recorded honestly beats a confident wrong diff.
