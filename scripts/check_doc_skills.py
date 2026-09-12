#!/usr/bin/env python3
"""Cross-check the four document-producing skills for a consistent PDF route.

Each of doc-writer, docs-site-generator, exec-doc-generator and
slide-deck-generator must declare exactly one `PDF route: ` line in its
SKILL.md. This also checks that the docs-site-generator and
spectrocloud-poc-docs copies of brand.css have not drifted apart, since that
drift is the other way this milestone's "one source of truth" claim can break.

Exits 1 naming the offending file on any violation.
"""

import filecmp
import sys
from pathlib import Path

DOC_SKILLS = [
    "doc-writer",
    "docs-site-generator",
    "exec-doc-generator",
    "slide-deck-generator",
]

BRAND_CSS_A = Path("skills/docs-site-generator/assets/brand.css")
BRAND_CSS_B = Path("skills/spectrocloud-poc-docs/references/templates/brand.css")


def main() -> int:
    ok = True
    routes = {}

    for skill in DOC_SKILLS:
        skill_md = Path("skills") / skill / "SKILL.md"
        lines = skill_md.read_text().splitlines()
        matches = [line[len("PDF route: "):] for line in lines
                   if line.startswith("PDF route: ")]

        if len(matches) != 1:
            print(f"{skill_md}: expected exactly one 'PDF route: ' line, found {len(matches)}",
                  file=sys.stderr)
            ok = False
            continue

        routes[skill] = matches[0]

    for skill, route in routes.items():
        print(f"{skill}: {route}")

    if not (BRAND_CSS_A.is_file() and BRAND_CSS_B.is_file()):
        print(f"{BRAND_CSS_A} or {BRAND_CSS_B}: missing", file=sys.stderr)
        ok = False
    elif not filecmp.cmp(BRAND_CSS_A, BRAND_CSS_B, shallow=False):
        print(f"{BRAND_CSS_B}: drifted from {BRAND_CSS_A}", file=sys.stderr)
        ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
