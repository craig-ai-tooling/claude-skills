#!/usr/bin/env python3
"""check_docs.py — T0 static QA for a POC docs-site (spectrocloud-poc-docs skill).

Checks, in order:
  1. `mkdocs build --strict` (skippable with --no-build)
  2. Markdown source lint:
       - every opening code fence declares a language
       - "Step N" headings per page are unique and strictly increasing
  3. Secret / lab-leak scan over site sources (customer-facing hygiene):
       - op:// secret references, 1Password service-account tokens
       - credentials embedded in URLs (user:pass@host)
       - private key material, AWS access key IDs
       - literal API keys / bearer tokens (long literals where a $VAR belongs)
       - Palette edge host registration tokens: an edgeHostToken / *TOKEN value,
         or the bare 44-char base64 shape anywhere (prose, tables, inline code)
       - lab-range RFC-1918 IPs: 172.16.0.0/12 is an ERROR by default;
         10.0.0.0/8 and 192.168.0.0/16 are WARNs (ERRORs with --strict-ips)
       - extra regexes from --denylist FILE (one regex per line, # comments)
  4. Built-HTML internal link + anchor check (needs the build from step 1)

Suppress a finding on a specific line by putting `check-docs:allow` in an HTML
comment on that line or the line above (use sparingly, and say why).

Exit status: 0 = clean (warnings allowed), 1 = errors found, 2 = usage/setup error.

Usage:
  check_docs.py <docs-site-dir> [--no-build] [--strict-ips] [--denylist FILE] [--json]
  check_docs.py <docs-site-dir> --secrets-only   # the pre-publish gate the deploy scripts run
"""

from __future__ import annotations

import argparse
import base64
import html.parser
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCAN_SUFFIXES = {".md", ".yml", ".yaml", ".toml", ".css", ".html", ".json", ".txt"}
SKIP_DIRS = {"site", ".wrangler", ".git", ".venv", "node_modules", ".poc-test-artifacts"}
ALLOW_MARKER = "check-docs:allow"

# (name, severity, compiled regex) — severity: "error" | "warn"
SECRET_PATTERNS = [
    # A real 1Password ref has vault/item after the scheme; a bare `op://` in
    # prose (docs about the rule itself) does not match.
    ("op-secret-ref", "error", re.compile(r"op://[\w.-]+/[^\s`'\"]+")),
    ("op-service-token", "error", re.compile(r"\bops_[A-Za-z0-9+/=_-]{20,}")),
    ("op-env-token", "error", re.compile(r"OP_SERVICE\w*_TOKEN\s*=\s*\S+")),
    ("creds-in-url", "error", re.compile(r"://[A-Za-z0-9._%-]+:[^@/\s'\"<>$]+@")),
    ("private-key", "error", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY")),
    ("aws-access-key", "error", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    # Literal secrets where a variable or <placeholder> belongs.
    ("literal-api-key", "error",
     re.compile(r"(?i)\b(?:apikey|api[-_]key|authorization:\s*bearer)\b['\"]?\s*[:=]?\s*['\"]?"
                r"(?!\$|\{\{|<)[A-Za-z0-9+/=_-]{24,}")),
    # A working user-data pasted into a guide carries the tenant's registration
    # token. Placeholders (<token>, $TOKEN, {{ .token }}) do not match.
    ("palette-edge-token", "error",
     re.compile(r"(?i)edgeHostToken['\"]?\s*[:=]\s*['\"]?(?!\$|\{\{|<)[A-Za-z0-9+/=]{20,}")),
    ("literal-token", "error",
     re.compile(r"(?i)\b\w*token\w*['\"]?\s*[:=]\s*['\"]?(?!\$|\{\{|<)[A-Za-z0-9+/]{40,}={0,2}")),
]
# Palette registration tokens are base64 of a 32-char, mostly-hex string: 44
# chars ending in '='. Catches one quoted bare in prose, where no key names it.
PALETTE_TOKEN_SHAPE = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{43}=(?![A-Za-z0-9+/=])")
IP_LAB_RANGE = re.compile(r"\b172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b")
IP_OTHER_PRIVATE = re.compile(r"\b(?:10\.\d{1,3}|192\.168)\.\d{1,3}\.\d{1,3}\b")

FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
STEP_HEADING_RE = re.compile(r"^#{2,4}\s+Step\s+(\d+)\b")


class Finding:
    def __init__(self, severity: str, path: str, line: int, check: str, message: str):
        self.severity, self.path, self.line, self.check, self.message = (
            severity, path, line, check, message)

    def __str__(self) -> str:
        loc = f"{self.path}:{self.line}" if self.line else self.path
        return f"{self.severity.upper()} [{self.check}] {loc}: {self.message}"

    def as_dict(self):
        return {"severity": self.severity, "path": self.path, "line": self.line,
                "check": self.check, "message": self.message}


def iter_source_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        yield path


def line_allowed(lines: list[str], idx: int) -> bool:
    """True if this 0-based line (or the previous one) carries the allow marker."""
    if ALLOW_MARKER in lines[idx]:
        return True
    return idx > 0 and ALLOW_MARKER in lines[idx - 1]


def check_fences_and_steps(path: Path, rel: str, text: str, findings: list[Finding]):
    lines = text.splitlines()
    in_fence = False
    fence_marker = ""
    fence_indent = 0
    last_step = 0
    seen_steps: set[int] = set()

    for i, line in enumerate(lines):
        m = FENCE_RE.match(line)
        if m:
            indent, marker, info = len(m.group(1)), m.group(2), m.group(3).strip()
            if in_fence:
                # A closing fence uses the same char, at least as long, no info string.
                if marker[0] == fence_marker[0] and len(marker) >= len(fence_marker) and not info:
                    in_fence = False
                continue
            in_fence, fence_marker, fence_indent = True, marker, indent
            if not info and not line_allowed(lines, i):
                findings.append(Finding("error", rel, i + 1, "fence-language",
                                        "code fence has no language (``` needs e.g. ```bash)"))
            continue

        if in_fence:
            continue

        sm = STEP_HEADING_RE.match(line)
        if sm:
            n = int(sm.group(1))
            if n in seen_steps:
                findings.append(Finding("error", rel, i + 1, "step-numbering",
                                        f"duplicate 'Step {n}' heading in this page"))
            elif n <= last_step:
                findings.append(Finding("error", rel, i + 1, "step-numbering",
                                        f"'Step {n}' after 'Step {last_step}' — steps must increase"))
            seen_steps.add(n)
            last_step = max(last_step, n)

    if in_fence:
        findings.append(Finding("error", rel, len(lines), "fence-language",
                                "unclosed code fence at end of file"))


def looks_like_palette_token(value: str) -> bool:
    try:
        raw = base64.b64decode(value, validate=True)
    except ValueError:
        return False
    if len(raw) != 32:
        return False
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError:
        return False
    return sum(c in "0123456789abcdef" for c in text) >= 28


def scan_secrets(rel: str, text: str, findings: list[Finding], strict_ips: bool,
                 extra_patterns: list[tuple[str, re.Pattern]]):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line_allowed(lines, i):
            continue
        named = False
        for name, severity, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                named = True
                findings.append(Finding(severity, rel, i + 1, name,
                                        f"possible secret/internal reference: {line.strip()[:120]}"))
        if not named and any(looks_like_palette_token(m.group(0))
                             for m in PALETTE_TOKEN_SHAPE.finditer(line)):
            findings.append(Finding("error", rel, i + 1, "palette-edge-token",
                                    f"Palette registration token shape: {line.strip()[:120]}"))
        if IP_LAB_RANGE.search(line):
            findings.append(Finding("error", rel, i + 1, "lab-ip",
                                    f"172.16-31.x.x address (lab range) in customer docs: {line.strip()[:120]}"))
        elif IP_OTHER_PRIVATE.search(line):
            sev = "error" if strict_ips else "warn"
            findings.append(Finding(sev, rel, i + 1, "private-ip",
                                    f"RFC-1918 address — confirm it is a placeholder example: {line.strip()[:120]}"))
        for name, pattern in extra_patterns:
            if pattern.search(line):
                findings.append(Finding("error", rel, i + 1, f"denylist:{name}",
                                        f"denylisted pattern: {line.strip()[:120]}"))


class _AnchorCollector(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[tuple[int, str]] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a" and a.get("name"):
            self.ids.add(a["name"])
        if tag == "a" and a.get("href"):
            self.links.append((self.getpos()[0], a["href"]))


def check_built_html(site_dir: Path, root: Path, findings: list[Finding]):
    pages: dict[Path, _AnchorCollector] = {}
    for page in sorted(site_dir.rglob("*.html")):
        parser = _AnchorCollector()
        try:
            parser.feed(page.read_text(encoding="utf-8", errors="replace"))
        except Exception as exc:  # noqa: BLE001 — report, don't crash the run
            findings.append(Finding("warn", str(page.relative_to(root)), 0, "html-parse",
                                    f"could not parse built HTML: {exc}"))
            continue
        pages[page] = parser

    def resolve(page: Path, target: str) -> Path:
        candidate = (page.parent / target).resolve()
        if candidate.is_dir():
            candidate = candidate / "index.html"
        return candidate

    for page, parser in pages.items():
        rel = str(page.relative_to(root))
        # Skip generated boilerplate pages (search, 404) — only content matters.
        if page.name == "404.html":
            continue
        for line_no, href in parser.links:
            if re.match(r"^[a-z][a-z0-9+.-]*:", href) or href.startswith("//"):
                continue  # external / mailto / tel
            if href.startswith("#"):
                frag, target_page = href[1:], page
            else:
                path_part, _, frag = href.partition("#")
                target_page = resolve(page, path_part)
                if not target_page.exists():
                    findings.append(Finding("error", rel, line_no, "broken-link",
                                            f"internal link target missing: {href}"))
                    continue
            if frag and target_page in pages and frag not in pages[target_page].ids:
                findings.append(Finding("error", rel, line_no, "broken-anchor",
                                        f"anchor #{frag} not found in {target_page.name}: {href}"))


def run_mkdocs_build(root: Path, findings: list[Finding]) -> Path | None:
    if not (root / "mkdocs.yml").exists():
        findings.append(Finding("error", "mkdocs.yml", 0, "build", "mkdocs.yml not found"))
        return None
    if shutil.which("mkdocs") is None:
        findings.append(Finding("error", "mkdocs", 0, "build",
                                "mkdocs not on PATH — pip/pipx install mkdocs-material"))
        return None
    out_dir = Path(tempfile.mkdtemp(prefix="check-docs-site-"))
    proc = subprocess.run(
        ["mkdocs", "build", "--strict", "--site-dir", str(out_dir)],
        cwd=root, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout).strip().splitlines()[-15:]
        findings.append(Finding("error", "mkdocs.yml", 0, "build",
                                "mkdocs build --strict failed:\n    " + "\n    ".join(tail)))
        return None
    return out_dir


def load_denylist(path: Path) -> list[tuple[str, re.Pattern]]:
    patterns = []
    for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            patterns.append((f"{path.name}:{i}", re.compile(line)))
        except re.error as exc:
            print(f"denylist {path}:{i}: bad regex ({exc})", file=sys.stderr)
            sys.exit(2)
    return patterns


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docs_site", type=Path, help="docs-site directory (contains mkdocs.yml)")
    ap.add_argument("--no-build", action="store_true", help="skip mkdocs build + HTML checks")
    ap.add_argument("--strict-ips", action="store_true",
                    help="treat 10.x / 192.168.x addresses as errors too")
    ap.add_argument("--denylist", type=Path, action="append", default=[],
                    help="extra regex denylist file(s) — e.g. your lab's hostnames")
    ap.add_argument("--secrets-only", action="store_true",
                    help="secret scan only (implies --no-build); run before every publish")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    root = args.docs_site.resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    extra = []
    for dl in args.denylist:
        extra.extend(load_denylist(dl))

    findings: list[Finding] = []

    for path in iter_source_files(root):
        rel = str(path.relative_to(root))
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix.lower() == ".md" and not args.secrets_only:
            check_fences_and_steps(path, rel, text, findings)
        scan_secrets(rel, text, findings, args.strict_ips, extra)

    if not (args.no_build or args.secrets_only):
        site_dir = run_mkdocs_build(root, findings)
        if site_dir is not None:
            check_built_html(site_dir, site_dir, findings)
            shutil.rmtree(site_dir, ignore_errors=True)

    errors = [f for f in findings if f.severity == "error"]
    warns = [f for f in findings if f.severity == "warn"]

    if args.json:
        print(json.dumps({"errors": len(errors), "warnings": len(warns),
                          "findings": [f.as_dict() for f in findings]}, indent=2))
    else:
        for f in findings:
            print(f)
        print(f"\ncheck_docs: {len(errors)} error(s), {len(warns)} warning(s) in {root.name}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
