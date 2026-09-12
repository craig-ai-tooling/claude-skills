# lm-92 — docs-site scaffolding ships prose where files belong

Four document-producing skills hand the agent code to retype instead of a file
to run. `skills/docs-site-generator/` has no `assets/` and no `scripts/`: its
`mkdocs.yml`, its `brand.css` and its landing page all live as fenced blocks in
`SKILL.md`, so every site is hand-rebuilt and drifts. `skills/exec-doc-generator/`
and `skills/slide-deck-generator/` both point at
`skills/exec-doc-generator/references/puppeteer-render.md`, which tells the agent
to write out `generate-pdf.mjs` itself, twice, from two fenced variants. And the
MkDocs stylesheet exists twice — the copy in
`skills/spectrocloud-poc-docs/references/templates/brand.css` still carries the
retired blue/purple dark mode (`#1a1a2e`, `#2d2d44`) that the docs-site skill's
own text says never to use.

This milestone turns that prose into shipped files, makes the two stylesheet
copies identical, and adds a check that fails when they drift apart again.

## Ground truth, measured on this repo before planning

- `skills/docs-site-generator/` contains only `SKILL.md` and
  `references/section-templates.md`. No `assets/`, no `scripts/`.
- `skills/exec-doc-generator/assets/` holds three SVG logos and no render script.
  `skills/slide-deck-generator/` has no `assets/` at all.
- `scripts/` holds seven files and nothing cross-checks one skill against another.
- `make validate` exits 0 today: `quick_validate.py` over every skill, then
  `secret_scan.py skills`. Keep it exiting 0.
- `scripts/package_skill.py` walks the whole skill directory and skips only
  dotfiles, `__pycache__` and `*.pyc`, so an `assets/` directory does travel
  inside the `.skill` zip.
- `quick_validate.py` caps `SKILL.md` at 500 lines;
  `skills/docs-site-generator/SKILL.md` is at 428. Moving blocks out shrinks it.
- `secret_scan.py` also scans `.mjs`, so nothing written here may name a lab
  host, a `172.18.x` address, an `op://` reference or a personal handle.
- `mkdocs-material` and `puppeteer` are NOT installed. Never make a task depend
  on `mkdocs build` or on actually rendering a PDF.
- `dist/` is gitignored — scaffold and package into it freely.

## Files touched

```allowlist
skills/docs-site-generator/SKILL.md
skills/docs-site-generator/assets/brand.css
skills/docs-site-generator/assets/mkdocs.yml.tmpl
skills/docs-site-generator/assets/index.md.tmpl
skills/docs-site-generator/scripts/scaffold_docs_site.sh
skills/spectrocloud-poc-docs/references/templates/brand.css
skills/exec-doc-generator/SKILL.md
skills/exec-doc-generator/assets/generate-pdf.mjs
skills/exec-doc-generator/references/puppeteer-render.md
skills/slide-deck-generator/SKILL.md
skills/slide-deck-generator/assets/generate-pdf.mjs
skills/doc-writer/SKILL.md
scripts/check_doc_skills.py
Makefile
ralph/IMPLEMENTATION_PLAN.md
ralph/PROGRESS.md
```

## Tasks

- [x] Create `skills/docs-site-generator/assets/brand.css` from the stylesheet block in that skill's `SKILL.md`, keeping the Ink/neutral dark mode (`#012121`, `#E0DCD7`, `#1E3332`). Verify: `grep -q '#1F7A78' skills/docs-site-generator/assets/brand.css` exits 0 and `grep -Eq '1a1a2e|2d2d44' skills/docs-site-generator/assets/brand.css` exits 1.

- [x] Overwrite `skills/spectrocloud-poc-docs/references/templates/brand.css` with a byte-identical copy of the new `skills/docs-site-generator/assets/brand.css`, retiring its blue/purple dark mode. Verify: `cmp -s skills/docs-site-generator/assets/brand.css skills/spectrocloud-poc-docs/references/templates/brand.css` exits 0.

- [x] Create `skills/docs-site-generator/assets/mkdocs.yml.tmpl` from the `mkdocs.yml` block in that skill's `SKILL.md`, using `__SITE_NAME__` as the one substitution token. Verify: `grep -q '__SITE_NAME__' skills/docs-site-generator/assets/mkdocs.yml.tmpl` exits 0 and `grep -q '{{' skills/docs-site-generator/assets/mkdocs.yml.tmpl` exits 1.

- [x] Create `skills/docs-site-generator/assets/index.md.tmpl` from the landing-page block in that skill's `SKILL.md`, using `__SITE_NAME__` as the one substitution token. Verify: `grep -q '__SITE_NAME__' skills/docs-site-generator/assets/index.md.tmpl` exits 0 and `grep -q '{{' skills/docs-site-generator/assets/index.md.tmpl` exits 1.

- [x] Create `skills/docs-site-generator/scripts/scaffold_docs_site.sh` taking `<dest> --site-name <name>`. It writes the three asset files into `<dest>` as `mkdocs.yml`, `docs/index.md` and `docs/overrides/stylesheets/brand.css`, substituting `__SITE_NAME__`. Verify: `rm -rf dist/t && bash skills/docs-site-generator/scripts/scaffold_docs_site.sh dist/t --site-name Acme` exits 0.

- [x] Make `skills/docs-site-generator/scripts/scaffold_docs_site.sh` refuse a destination that already exists and is non-empty, printing why, rather than clobbering it. Verify: with `dist/t` already scaffolded, re-running the same command exits non-zero and `md5sum dist/t/mkdocs.yml` prints the same digest before and after; `bash -n skills/docs-site-generator/scripts/scaffold_docs_site.sh` exits 0.

- [x] Leave no unfilled token in scaffolded output. Verify: after `rm -rf dist/t && bash skills/docs-site-generator/scripts/scaffold_docs_site.sh dist/t --site-name Acme`, both `grep -rn '{{' dist/t` and `grep -rn '__SITE_NAME__' dist/t` exit 1.

- [x] Cut the `mkdocs.yml`, `brand.css` and landing-page fenced blocks out of `skills/docs-site-generator/SKILL.md` and replace each with a short pointer to the scaffolder and to `assets/`. Verify: `grep -q 'scripts/scaffold_docs_site.sh' skills/docs-site-generator/SKILL.md` exits 0 and `python3 scripts/quick_validate.py skills/docs-site-generator` exits 0.

- [x] Create `skills/exec-doc-generator/assets/generate-pdf.mjs` from the Letter-format variant in `skills/exec-doc-generator/references/puppeteer-render.md`, taking `<input.html> <output.pdf>`, loading puppeteer by dynamic import only AFTER the argument check so a missing dependency cannot mask usage. Verify: `node --check skills/exec-doc-generator/assets/generate-pdf.mjs` exits 0.

- [x] Give `skills/exec-doc-generator/assets/generate-pdf.mjs` a no-argument usage path: print a first stderr line beginning `usage:` and exit 1. Verify: `node skills/exec-doc-generator/assets/generate-pdf.mjs` exits 1, its stderr starts with `usage:`, and `node skills/exec-doc-generator/assets/generate-pdf.mjs 2>&1 | grep -q ERR_MODULE_NOT_FOUND` exits 1.

- [x] Create `skills/slide-deck-generator/assets/generate-pdf.mjs` from the 16:9 variant in that same reference, with the same dynamic-import and no-argument usage behaviour. Verify: `node --check skills/slide-deck-generator/assets/generate-pdf.mjs` exits 0, `node skills/slide-deck-generator/assets/generate-pdf.mjs` exits 1 with stderr starting `usage:` and no `ERR_MODULE_NOT_FOUND`.

- [x] Rewrite the render step in `skills/exec-doc-generator/references/puppeteer-render.md` and in both skills' `SKILL.md` to run the shipped script instead of retyping the code. Verify: `grep -q 'assets/generate-pdf.mjs' skills/exec-doc-generator/SKILL.md` exits 0, `grep -q 'assets/generate-pdf.mjs' skills/slide-deck-generator/SKILL.md` exits 0, and `make validate` exits 0.

- [ ] Add exactly one line starting `PDF route: ` to each of the four document skills' `SKILL.md` — `doc-writer` and `docs-site-generator` declare no PDF route, the other two name `assets/generate-pdf.mjs`. Verify: `grep -q '^PDF route: ' skills/doc-writer/SKILL.md` exits 0, and the same holds for docs-site-generator, exec-doc-generator and slide-deck-generator.

- [ ] Create `scripts/check_doc_skills.py`: print one `<skill>: <route>` line for each of the four document skills read from their `PDF route: ` line, and exit 1 naming the offending file when a skill has zero or several such lines, or when the two `brand.css` copies are not byte-identical. Verify: `python3 scripts/check_doc_skills.py` exits 0 and prints 4 lines.

- [ ] Prove `scripts/check_doc_skills.py` is not green by construction. Verify: `printf 'x' >> skills/spectrocloud-poc-docs/references/templates/brand.css && python3 scripts/check_doc_skills.py` exits 1 and its output names that file, then `git checkout -- skills/spectrocloud-poc-docs/references/templates/brand.css && python3 scripts/check_doc_skills.py` exits 0.

- [ ] Wire `scripts/check_doc_skills.py` into the `validate` target of `Makefile`, after the secret scan. Verify: `make validate` exits 0 and `make validate 2>&1 | grep -q check_doc_skills` exits 0.

- [ ] Confirm the new assets travel inside the packaged skill. Verify: `python3 scripts/package_skill.py skills/docs-site-generator` exits 0 and `python3 -c "import zipfile;print(zipfile.ZipFile('dist/docs-site-generator.skill').namelist())"` prints both `docs-site-generator/assets/brand.css` and `docs-site-generator/assets/mkdocs.yml.tmpl`.
