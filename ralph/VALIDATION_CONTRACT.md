# Validation contract — lm-92: docs-site scaffolding ships files, not prose

What "done" means for this milestone, decided before the work was decomposed.

A later pass checks the built system against this file as a **black box** — no
git history, no diff, no knowledge of how any of it was built. Every assertion
below therefore stands on its own and carries its own check on the same line.

Run everything from the repository root. `dist/` is gitignored, so the throwaway
scaffold and package destinations used below never pollute the tree.

## Assertions

- One command scaffolds a whole documentation site with nothing left to retype by hand: `rm -rf dist/vc-site && bash skills/docs-site-generator/scripts/scaffold_docs_site.sh dist/vc-site --site-name "Acme Docs"` exits 0, and then `test -f dist/vc-site/mkdocs.yml && test -f dist/vc-site/docs/overrides/stylesheets/brand.css` exits 0.

- What that command writes is branded on arrival rather than a bare template: after the scaffold above, `grep -q '#1F7A78' dist/vc-site/docs/overrides/stylesheets/brand.css` exits 0 (brand teal wired in) and `grep -Eq '1a1a2e|2d2d44' dist/vc-site/docs/overrides/stylesheets/brand.css` exits 1 (retired blue/purple dark mode gone).

- Nothing the scaffolder writes still carries an unfilled placeholder: after the scaffold above, `grep -rn '{{' dist/vc-site` exits 1 and `grep -rn '__SITE_NAME__' dist/vc-site` exits 1.

- Scaffolding twice into the same destination is refused instead of silently clobbering an existing site: with `dist/vc-site` already populated, re-running `bash skills/docs-site-generator/scripts/scaffold_docs_site.sh dist/vc-site --site-name "Acme Docs"` exits non-zero, and `md5sum dist/vc-site/mkdocs.yml` prints the same digest before and after that second run.

- The docs-site skill and the POC-docs skill hand out the same MkDocs brand stylesheet byte for byte — one source of truth, not two that drift: `cmp -s skills/docs-site-generator/assets/brand.css skills/spectrocloud-poc-docs/references/templates/brand.css` exits 0.

- Each PDF-producing skill ships its render step as a real runnable file rather than as prose to be retyped: `node --check skills/exec-doc-generator/assets/generate-pdf.mjs` exits 0 and `node --check skills/slide-deck-generator/assets/generate-pdf.mjs` exits 0.

- Either render step, invoked with no arguments, explains itself instead of crashing on a missing dependency: `node skills/exec-doc-generator/assets/generate-pdf.mjs` and `node skills/slide-deck-generator/assets/generate-pdf.mjs` each exit 1 and print a first stderr line beginning `usage:`, with no `ERR_MODULE_NOT_FOUND` anywhere in that output — puppeteer is not installed here and must not be needed to see usage.

- Every document-producing skill names exactly one PDF route and the four do not contradict each other: `python3 scripts/check_doc_skills.py` exits 0 and prints one line each for `doc-writer`, `docs-site-generator`, `exec-doc-generator` and `slide-deck-generator` naming that skill's single route.

- That consistency check is not green by construction — it fails when consistency actually breaks: after `printf 'x' >> skills/spectrocloud-poc-docs/references/templates/brand.css`, `python3 scripts/check_doc_skills.py` exits 1 and names that file; after `git checkout -- skills/spectrocloud-poc-docs/references/templates/brand.css` it exits 0 again.

- The shipped assets travel inside the package a consumer downloads, not merely in the working tree: `python3 scripts/package_skill.py skills/docs-site-generator` exits 0 and `python3 -c "import zipfile;print(zipfile.ZipFile('dist/docs-site-generator.skill').namelist())"` lists both `docs-site-generator/assets/brand.css` and `docs-site-generator/assets/mkdocs.yml.tmpl`.

- Every published skill stays structurally valid and free of personal-infrastructure leaks — none has outgrown the 500-line SKILL.md ceiling, none names a lab host, IP, vault or personal handle: `make validate` exits 0.

## Explicitly out of contract

Three things this milestone deliberately does not assert, so that a validator
does not go looking for them:

1. `mkdocs build` is not an acceptance check anywhere. `mkdocs-material` is not
   installed in this environment, so a Material-themed build fails for reasons
   unrelated to this milestone.
2. No PDF is rendered during validation. `puppeteer` is not installed;
   `node --check` plus the no-argument usage path is the whole check.
3. Nothing outside this repository is validated. The customer engagement repo
   that motivated this task is not reachable from here.
