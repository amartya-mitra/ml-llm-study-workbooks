"""Tests for the TSFM addendum's final-edition builder and canonical artifact.

Source-level tests run anywhere; the artifact-level test runs the read-only
verifier only when the local canonical, RC1 and review PDFs exist (they are
git-ignored build products) and is skipped otherwise.
"""
import os
import re
import subprocess
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from _yaml_lite import safe_load_path  # noqa: E402

BUILDER = os.path.join(REPO_ROOT, "scripts", "build_addendum_final.py")
CHECKER = os.path.join(REPO_ROOT, "scripts", "check_addendum_final.py")
INDEX = os.path.join(REPO_ROOT, "workbooks", "addendum-04-05-tsfm", "index.qmd")
FINAL = os.path.join(REPO_ROOT, "outputs", "addendum-04-05-tsfm.pdf")
RC1 = os.path.join(REPO_ROOT, "outputs", "_releases", "addendum-04-05-tsfm", "addendum-04-05-tsfm-rc1.pdf")
REVIEW = os.path.join(REPO_ROOT, "outputs", "_development", "addendum-04-05-tsfm", "integrated-review", "addendum-04-05-tsfm-review.pdf")


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


class TestFinalBuilder(unittest.TestCase):
    def test_requires_accepted_frozen_and_renders_from_source(self):
        src = read(BUILDER)
        self.assertIn('entry.get("status") != "accepted_frozen"', src)
        self.assertIn('"quarto", "render", STAGING_QMD', src)
        self.assertNotIn("rc1.pdf", src)            # never reads or copies RC1
        self.assertNotIn("integrated-review", src)  # nor the review PDF

    def test_writes_only_the_canonical_path_and_does_nothing_external(self):
        src = read(BUILDER)
        self.assertIn('f"{WB_ID}.pdf"', src)
        for banned in ("git push", "git tag", "api.github.com", "GH_TOKEN", "urllib"):
            self.assertNotIn(banned, src)

    def test_substitution_is_staged_checked_and_cleaned_up(self):
        src = read(BUILDER)
        self.assertIn('FINAL_SUBTITLE = "Final Edition"', src)
        self.assertIn("expected subtitle substitution did not happen", src)
        self.assertIn("finally:", src)
        for name in ("final-build.qmd", "final-build.pdf"):
            self.assertFalse(os.path.exists(os.path.join(REPO_ROOT, "workbooks", "addendum-04-05-tsfm", name)))

    def test_refuses_to_overwrite_an_unverified_canonical_pdf(self):
        src = read(BUILDER)
        self.assertIn("not overwriting", src)
        self.assertIn("MANIFEST", src)

    def test_frozen_source_keeps_its_descriptive_subtitle(self):
        self.assertNotIn("Release Candidate", read(INDEX))
        self.assertNotIn("Final Edition", read(INDEX))


class TestCanonicalArtifact(unittest.TestCase):
    def test_canonical_pdf_is_ignored_not_tracked(self):
        tracked = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True).stdout.splitlines()
        self.assertEqual([p for p in tracked if p.endswith(".pdf")], [])
        ignored = subprocess.run(["git", "check-ignore", "outputs/addendum-04-05-tsfm.pdf"], cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(ignored.returncode, 0)

    def test_registry_still_has_frozen_content_and_a_valid_lifecycle_value(self):
        reg = safe_load_path(os.path.join(REPO_ROOT, "config", "chapter-status-registry.yaml"))
        self.assertEqual(reg["workbooks"]["addendum-04-05-tsfm"]["status"], "accepted_frozen")
        self.assertIn(reg["publications"]["addendum-04-05-tsfm"]["status"], ("review_pending", "published"))

    @unittest.skipUnless(all(os.path.exists(p) for p in (FINAL, RC1, REVIEW)), "local PDFs not present")
    def test_final_matches_rc1_apart_from_the_subtitle(self):
        r = subprocess.run([sys.executable, CHECKER], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, msg=r.stdout[-2500:])
        self.assertIn("RESULT: clean", r.stdout)


if __name__ == "__main__":
    unittest.main()
