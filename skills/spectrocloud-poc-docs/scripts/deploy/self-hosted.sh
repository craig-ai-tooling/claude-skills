#!/usr/bin/env bash
# self-hosted.sh — DOCUMENTED STUB deploy provider for a self-hosted docs host
# (spectrocloud-poc-docs). Implements the provider interface (deploy/README.md)
# for stacks like: reverse proxy (Caddy/nginx) + email-OTP auth service + rsync'd
# static sites, one slug per docs-site.
#
# This stub is intentionally environment-agnostic. Point it at your stack with:
#   DOCS_HOST        ssh target serving the sites          (e.g. docs.example.com)
#   DOCS_USER        ssh user                              (default: ubuntu)
#   DOCS_ROOT        remote path holding per-slug sites    (default: /srv/docs)
#   ADMIN_API_BASE   https base of your site-admin API     (optional)
#   ADMIN_API_TOKEN  bearer token for that API             (optional)
#
# deploy: builds --strict and rsyncs site/ to $DOCS_ROOT/<slug>/site/, registering
#         the slug + allowed_domains with the admin API when configured.
# gate:   no-op WHEN the host's auth layer gates every site by default (the
#         recommended design — deny-by-default, allowlist per slug). If your host
#         serves sites publicly until registered, implement gating here and make
#         it fail closed.
# verify: probes the site URL and requires a non-2xx (auth challenge) response.
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
[ -n "$SITE_DIR" ] || { echo "usage: self-hosted.sh {deploy|gate|verify} --site-dir DIR" >&2; exit 2; }
[ -n "$CONFIG" ] || CONFIG="$SITE_DIR/deploy.yaml"

: "${DOCS_USER:=ubuntu}"
: "${DOCS_ROOT:=/srv/docs}"

SLUG="" DOMAINS=""
if [ -f "$CONFIG" ]; then
  SLUG=$(awk '/^project:/ {print $2; exit}' "$CONFIG")
  DOMAINS=$(awk '/^allowed_domains:/{f=1;next} /^[a-zA-Z]/{f=0} f && /^ *- /{sub(/^ *- */,""); print}' "$CONFIG" | tr '\n' ' ')
fi
[ -n "$SLUG" ] || { echo "deploy.yaml must set project: (used as the site slug)" >&2; exit 2; }

case "$CMD" in
  deploy)
    : "${DOCS_HOST:?set DOCS_HOST to your docs server (this is a stub — see header)}"
    command -v mkdocs >/dev/null || { echo "mkdocs not found" >&2; exit 2; }
    # Refuse before anything is built: a token in the source ships in site/.
    python3 "$SCRIPT_DIR/../check_docs.py" "$SITE_DIR" --secrets-only \
      || { echo "secret scan failed — refusing to publish (fix the findings above)" >&2; exit 1; }
    ( cd "$SITE_DIR" && mkdocs build --strict )
    if [ -n "${ADMIN_API_BASE:-}" ] && [ -n "${ADMIN_API_TOKEN:-}" ]; then
      DOMAINS_JSON=$(printf '%s\n' $DOMAINS | python3 -c 'import json,sys;print(json.dumps([d.strip() for d in sys.stdin if d.strip()]))')
      curl -fsS -X PUT "$ADMIN_API_BASE/api/sites/$SLUG" \
        -H "Authorization: Bearer $ADMIN_API_TOKEN" -H "Content-Type: application/json" \
        -d "{\"title\":\"$SLUG\",\"allowed_domains\":$DOMAINS_JSON}" >/dev/null
    fi
    ssh -o StrictHostKeyChecking=accept-new "$DOCS_USER@$DOCS_HOST" "mkdir -p $DOCS_ROOT/$SLUG/site"
    rsync -az --delete "$SITE_DIR/site/" "$DOCS_USER@$DOCS_HOST:$DOCS_ROOT/$SLUG/site/"
    echo "deployed slug '$SLUG' to $DOCS_HOST:$DOCS_ROOT/$SLUG/site/"
    echo "NOT DONE YET — run: $0 verify --site-dir $SITE_DIR"
    ;;

  gate)
    # Deny-by-default hosts gate at deploy time (allowed_domains registration above).
    # If YOUR host is public until configured, implement gating here — and exit 1
    # until it is actually in place. Never exit 0 on faith.
    if [ -z "${ADMIN_API_BASE:-}" ]; then
      echo "stub: no ADMIN_API_BASE configured — cannot confirm gating exists" >&2
      exit 1
    fi
    echo "gating handled by the docs host's auth layer (allowed_domains: $DOMAINS)"
    ;;

  verify)
    : "${DOCS_SITE_URL:?set DOCS_SITE_URL (e.g. https://$SLUG.docs.example.com) to verify}"
    status=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$DOCS_SITE_URL/" || echo 000)
    if [ "${status:0:1}" = "2" ]; then
      echo "OPEN $DOCS_SITE_URL (HTTP $status — content served without authentication)" >&2
      exit 1
    fi
    echo "gated: $DOCS_SITE_URL answered HTTP $status to an unauthenticated request"
    ;;

  *)
    echo "usage: self-hosted.sh {deploy|gate|verify} --site-dir DIR [--config deploy.yaml]" >&2
    exit 2
    ;;
esac
