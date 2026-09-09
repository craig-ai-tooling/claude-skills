# Ralph progress notebook — lm-92

No iterations yet.

This file is the loop's memory across otherwise-fresh-context iterations —
`ralph/loop.sh` never writes to it itself; the agent does, one entry per
iteration, per the instructions in `ralph/PROMPT.md`.

One entry per iteration: which task was taken, the exact verification command
that was run, and its real output.

The loop refuses to start at all if this file already contains a line that is
exactly the exit sentinel `RALPH_COMPLETE` (see `ralph/loop.sh`), so that line
must not be added until every task in `ralph/IMPLEMENTATION_PLAN.md` is done.
