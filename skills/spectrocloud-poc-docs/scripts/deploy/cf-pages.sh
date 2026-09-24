#!/usr/bin/env bash
# cf-pages.sh — Cloudflare Pages deploy provider (spectrocloud-poc-docs).
#
# Subcommands (see deploy/README.md for the provider interface):
#   deploy --site-dir DIR [--config deploy.yaml]   build --strict + wrangler pages deploy
#   gate   --site-dir DIR [--config deploy.yaml]   ensure a Cloudflare Access OTP app covers
#                                                  the apex AND the *.project.pages.dev wildcard
#   verify --site-dir DIR [--config deploy.yaml]   probe apex + a preview-style hostname; fail
#                                                  unless BOTH redirect to Access login
#
# Requirements:
#   deploy: wrangler (logged in, or CLOUDFLARE_API_TOKEN with Pages:Edit)
#   gate:   CLOUDFLARE_API_TOKEN (Access:Edit) + CLOUDFLARE_ACCOUNT_ID
#   verify: curl only
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CMD="${1:-}"; shift || true
SITE_DIR="" CONFIG=""
while [ $# -gt 0 ]; do
  case "$1" in
    --site-dir) SITE_DIR="$2"; shift 2 ;;
    --config)   CONFIG="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[ -n "$SITE_DIR" ] || { echo "usage: cf-pages.sh {deploy|gate|verify} --site-dir DIR [--config deploy.yaml]" >&2; exit 2; }
[ -n "$CONFIG" ] || CONFIG="$SITE_DIR/deploy.yaml"

# --- minimal deploy.yaml parsing (project + allowed_domains) -------------------
PROJECT=""
DOMAINS=""
if [ -f "$CONFIG" ]; then
  PROJECT=$(awk '/^project:/ {print $2; exit}' "$CONFIG")
  DOMAINS=$(awk '/^allowed_domains:/{f=1;next} /^[a-zA-Z]/{f=0} f && /^ *- /{sub(/^ *- */,""); print}' "$CONFIG" | tr '\n' ' ')
fi
if [ -z "$PROJECT" ] && [ -f "$SITE_DIR/wrangler.toml" ]; then
  PROJECT=$(awk -F'"' '/^name/ {print $2; exit}' "$SITE_DIR/wrangler.toml")
fi
[ -n "$PROJECT" ] || { echo "could not determine project (deploy.yaml project: or wrangler.toml name)" >&2; exit 2; }

APEX="$PROJECT.pages.dev"
WILDCARD="*.$PROJECT.pages.dev"

case "$CMD" in
  deploy)
    command -v mkdocs >/dev/null   || { echo "mkdocs not found (pipx install mkdocs-material)" >&2; exit 2; }
    command -v wrangler >/dev/null || { echo "wrangler not found (npm i -g wrangler)" >&2; exit 2; }
    # Refuse before anything is built: a token in the source ships in site/.
    python3 "$SCRIPT_DIR/../check_docs.py" "$SITE_DIR" --secrets-only \
      || { echo "secret scan failed — refusing to publish (fix the findings above)" >&2; exit 1; }
    ( cd "$SITE_DIR" && mkdocs build --strict && wrangler pages deploy site --project-name "$PROJECT" )
    echo
    echo "Deployed: https://$APEX"
    echo "NOT DONE YET — run: $0 gate --site-dir $SITE_DIR   then   $0 verify --site-dir $SITE_DIR"
    ;;

  gate)
    [ -n "$DOMAINS" ] || { echo "deploy.yaml has no allowed_domains — refusing to gate with an empty allowlist" >&2; exit 2; }
    "$SCRIPT_DIR/cf_access_gate.sh" --project "$PROJECT" --domains "$DOMAINS"
    ;;

  verify)
    "$SCRIPT_DIR/verify_gating.sh" --project "$PROJECT"
    ;;

  *)
    echo "usage: cf-pages.sh {deploy|gate|verify} --site-dir DIR [--config deploy.yaml]" >&2
    exit 2
    ;;
esac
