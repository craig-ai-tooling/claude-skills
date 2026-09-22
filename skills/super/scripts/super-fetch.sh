#!/usr/bin/env bash
# =============================================================================
# super-fetch.sh — fetch the answer for a Super (Slite) thread.
#
# The `ask-super` MCP tool never returns the answer itself. It always replies:
#
#   "The answer is still being prepared. Fetch it with GET /v1/threads/<id>"
#
# ...and re-asking creates a NEW thread rather than returning the pending one.
# So the workflow is always two steps:
#
#   1. ask via the ask-super MCP tool  -> note the thread id it returns
#   2. scripts/super-fetch.sh <thread-id>
#
# Usage:
#   scripts/super-fetch.sh k8z9qWfU5IuEo8            # poll until answered
#   scripts/super-fetch.sh k8z9qWfU5IuEo8 --json     # raw JSON
#   scripts/super-fetch.sh k8z9qWfU5IuEo8 --once     # single attempt
#
# The API key is read from ~/.claude.json (the same key the MCP server uses).
# It is never echoed.
#
# Note: answers cite internal sources as {5L1T3-NN} markers. Those IDs are not
# resolvable from the API response — treat them as "grounded in internal docs,
# not independently verified".
# =============================================================================
set -euo pipefail

BASE="${SUPER_API_BASE:-https://api.slite.com/v1/threads}"
TIMEOUT="${SUPER_TIMEOUT:-180}"   # seconds to keep polling
INTERVAL="${SUPER_INTERVAL:-10}"

TID="${1:-}"
MODE="${2:-}"

if [ -z "$TID" ]; then
  grep '^#' "$0" | sed 's/^# \{0,1\}//'
  exit 1
fi

KEY=$(jq -r '
  .mcpServers.super.env.SUPER_API_KEY
  // (.projects | to_entries[] | .value.mcpServers.super.env.SUPER_API_KEY)
' ~/.claude.json 2>/dev/null | grep -v '^null$' | head -1)

if [ -z "$KEY" ]; then
  echo "FATAL: no SUPER_API_KEY found in ~/.claude.json" >&2
  exit 1
fi

fetch() { curl -s -m 30 -H "x-slite-api-key: $KEY" "$BASE/$TID"; }

deadline=$(( SECONDS + TIMEOUT ))
body=""
status=""

until [ "$status" = "completed" ] || [ "$SECONDS" -ge "$deadline" ]; do
  body=$(fetch)
  status=$(printf '%s' "$body" | jq -r '.status // "unknown"' 2>/dev/null || echo unknown)
  [ "$MODE" = "--once" ] && break
  [ "$status" = "completed" ] && break
  echo "… status=$status, waiting ${INTERVAL}s (thread $TID)" >&2
  sleep "$INTERVAL"
done

if [ "$MODE" = "--json" ]; then
  printf '%s\n' "$body" | jq '.'
  exit 0
fi

printf '%s' "$body" | jq -r '
  "# " + (.title // "(untitled)") + "   [" + (.status // "?") + "]",
  "",
  (.rounds[]? | "## Q\n" + .question + "\n\n## A\n" + (.answer // "(pending)"))
'

if [ "$status" != "completed" ]; then
  echo >&2
  echo "NOTE: thread not yet completed (status=$status). Re-run to poll again." >&2
fi
