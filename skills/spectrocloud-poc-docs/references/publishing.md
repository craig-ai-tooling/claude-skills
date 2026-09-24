# Publishing — gated deploys through a provider interface

The publish step is pluggable: `scripts/deploy/<provider>.sh` with three
subcommands — `deploy`, `gate`, `verify` (full interface: `scripts/deploy/README.md`).
Per-site config lives in `<docs-site>/deploy.yaml` (`templates/deploy.yaml.tmpl`):

```yaml
provider: cf-pages
project: acme-docs            # Pages project name / self-hosted slug
site_title: "Acme POC Guide"
allowed_domains:              # who may read the site
  - acme.com
  - spectrocloud.com
```

## The publish checklist (in order, no skipping)

1. `check_docs.py <docs-site>` — clean (T0). The secret scan matters most here:
   the site is about to leave the building.
   Both deploy providers re-run `check_docs.py --secrets-only` and refuse to
   publish on any finding. A working `user-data` pasted into a guide carries the
   tenant's edge host registration token: use `<registration-token>` instead.
2. `extract_tests.py --suite ...` clean, and ideally a PASSED T2 report in
   `.poc-test-artifacts/` — otherwise the handoff note says **UNTESTED**.
3. `deploy/<provider>.sh deploy --site-dir <docs-site>` — builds `--strict`, publishes.
4. `deploy/<provider>.sh gate --site-dir <docs-site>` — idempotently ensures access
   gating (allowed email domains, one-time PIN).
5. `deploy/<provider>.sh verify --site-dir <docs-site>` — **the deploy is not done
   until this passes.** Only after verify do you send the URL to the prospect.

## cf-pages provider (default)

Cloudflare Pages + Cloudflare Access (Zero Trust) with **one-time PIN** login —
no passwords, visitors enter an email on the allowlisted domains and get a PIN.

- `deploy` needs `wrangler` (logged in, or `CLOUDFLARE_API_TOKEN` with Pages:Edit).
- `gate`/`verify` need `CLOUDFLARE_API_TOKEN` (Access: Edit) + `CLOUDFLARE_ACCOUNT_ID`.

### The preview-URL wildcard gotcha (why `verify` exists)

Every `wrangler pages deploy` ALSO serves the site at
`https://<deployment-hash>.<project>.pages.dev`. An Access application created for
`<project>.pages.dev` alone does **not** cover those hostnames — the site looks
locked at the apex while every preview URL (printed by wrangler on each deploy,
easily pasted into a chat) serves the full site to the world.

`cf_access_gate.sh` therefore always puts **both** `<project>.pages.dev` and
`*.<project>.pages.dev` on the Access app, and `verify_gating.sh` probes the apex
*and* a synthetic preview-style hostname, requiring a redirect to
`cloudflareaccess.com` on both. Treat any 2xx as a leak.

Note: Cloudflare Zero Trust free tier has a seat cap (50 users/month across all
gated apps). Large audiences → consider the self-hosted provider.

## self-hosted provider (stub)

`deploy/self-hosted.sh` documents the pattern for a self-managed docs host
(reverse proxy + email-OTP auth + rsync'd static sites, one slug per site). It is
a **stub**: point it at your stack via `DOCS_HOST` / `DOCS_ROOT` /
`ADMIN_API_BASE` env vars, or copy it as the starting point for a new provider.
Design rule for any provider: **deny-by-default** — a site must not be readable
before its gating is registered, and `verify` must fail closed.

## Handoff note (send with the URL)

- The URL, who can access it (domains), and the login method (email OTP).
- Test status: PASSED (link/date of the T2 report) or UNTESTED.
- What phase to start with, and where support/escalation lives.
