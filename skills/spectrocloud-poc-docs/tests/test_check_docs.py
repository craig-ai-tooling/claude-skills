"""Unit tests for scripts/check_docs.py (T0 static QA).

Run from the skill root:  python3 -m unittest discover tests
These tests use --no-build (no mkdocs needed) except one optional build test
that self-skips when mkdocs/material is unavailable.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
CHECK = SKILL / "scripts" / "check_docs.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def run_check(*args):
    proc = subprocess.run([sys.executable, str(CHECK), *args, "--json"],
                          capture_output=True, text=True)
    data = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return proc.returncode, data


class CleanSiteTests(unittest.TestCase):
    def test_clean_site_no_build_passes(self):
        rc, data = run_check(str(FIXTURES / "clean_site"), "--no-build")
        self.assertEqual(data["errors"], 0, data)
        self.assertEqual(rc, 0)

    @unittest.skipUnless(shutil.which("mkdocs"), "mkdocs not installed")
    def test_clean_site_full_build_passes(self):
        rc, data = run_check(str(FIXTURES / "clean_site"))
        checks = [f["check"] for f in data["findings"]]
        if "build" in checks:  # material theme missing in this env
            self.skipTest("mkdocs-material not available for build test")
        self.assertEqual(data["errors"], 0, data)
        self.assertEqual(rc, 0)


class DirtySiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.denylist = tempfile.NamedTemporaryFile(  # noqa: SIM115
            "w", suffix=".txt", delete=False)
        cls.denylist.write("# fake internal hostnames\n\\.lab\\.example\\b\n")
        cls.denylist.close()
        cls.rc, cls.data = run_check(str(FIXTURES / "dirty_site"), "--no-build",
                                     "--denylist", cls.denylist.name)
        cls.checks = [f["check"] for f in cls.data["findings"]]
        cls.errors = [f for f in cls.data["findings"] if f["severity"] == "error"]

    @classmethod
    def tearDownClass(cls):
        Path(cls.denylist.name).unlink(missing_ok=True)

    def test_exit_code_nonzero(self):
        self.assertEqual(self.rc, 1)

    def test_flags_op_reference(self):
        self.assertIn("op-secret-ref", self.checks)

    def test_flags_lab_range_ip_as_error(self):
        lab = [f for f in self.errors if f["check"] == "lab-ip"]
        self.assertTrue(any("172.30.99.7" in f["message"] for f in lab), self.errors)

    def test_flags_creds_in_url(self):
        self.assertIn("creds-in-url", self.checks)

    def test_flags_missing_fence_language(self):
        self.assertIn("fence-language", self.checks)

    def test_flags_step_numbering_both_ways(self):
        msgs = [f["message"] for f in self.data["findings"]
                if f["check"] == "step-numbering"]
        self.assertTrue(any("must increase" in m for m in msgs), msgs)
        self.assertTrue(any("duplicate" in m for m in msgs), msgs)

    def test_flags_literal_api_key(self):
        self.assertIn("literal-api-key", self.checks)

    def test_flags_edge_host_token_in_user_data(self):
        hits = [f for f in self.errors if f["check"] == "palette-edge-token"
                and "edgeHostToken" in f["message"]]
        self.assertTrue(hits, self.errors)

    def test_flags_bare_registration_token_in_prose(self):
        hits = [f for f in self.errors if f["check"] == "palette-edge-token"
                and "Edge Host Token" in f["message"]]
        self.assertTrue(hits, self.errors)

    def test_secrets_only_still_refuses_a_token(self):
        rc, data = run_check(str(FIXTURES / "dirty_site"), "--secrets-only")
        self.assertEqual(rc, 1)
        checks = {f["check"] for f in data["findings"]}
        self.assertIn("palette-edge-token", checks)
        self.assertNotIn("fence-language", checks)

    def test_denylist_pattern_fires(self):
        self.assertTrue(any(c.startswith("denylist:") for c in self.checks), self.checks)

    def test_allow_marker_suppresses(self):
        suppressed = [f for f in self.data["findings"] if "192.168.1.50" in f["message"]]
        self.assertEqual(suppressed, [])

    def test_other_private_ip_is_warning_by_default(self):
        ten_dot = [f for f in self.data["findings"]
                   if f["check"] == "private-ip" and "10.0.0.9" in f["message"]]
        self.assertTrue(ten_dot)
        self.assertTrue(all(f["severity"] == "warn" for f in ten_dot))

    def test_strict_ips_promotes_to_error(self):
        rc, data = run_check(str(FIXTURES / "dirty_site"), "--no-build",
                             "--strict-ips")
        ten_dot = [f for f in data["findings"]
                   if f["check"] == "private-ip" and "10.0.0.9" in f["message"]]
        self.assertTrue(all(f["severity"] == "error" for f in ten_dot))


class SelfHygieneTests(unittest.TestCase):
    """The generic skill must obey its own secret rules: scan the skill's own
    docs (SKILL.md + references) for lab leaks. Fixtures are excluded — the
    dirty fixture exists to violate on purpose."""

    def test_skill_docs_are_lab_free(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            for src in [SKILL / "SKILL.md", *(SKILL / "references").rglob("*.md"),
                        *(SKILL / "scripts").rglob("*.md")]:
                dest = root / "docs" / src.name
                # fixture-free: only the skill's own prose
                dest.write_text(src.read_text())
            rc, data = run_check(str(root), "--no-build")
            secretish = [f for f in data["findings"]
                         if f["severity"] == "error" and f["check"] not in
                         ("fence-language", "step-numbering")]
            self.assertEqual(secretish, [], secretish)


if __name__ == "__main__":
    unittest.main()
