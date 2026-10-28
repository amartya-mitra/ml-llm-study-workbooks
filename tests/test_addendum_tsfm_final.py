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
REVIEW = os.path.join(REPO_ROOT, "outputs", "_development", "addendum-04-05-tsfm", "v1.1.0-review", "addendum-04-05-tsfm-v1.1.0-review.pdf")


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
        self.assertIn('EDITION_VERSION = "1.1.0"', src)
        self.assertIn('FINAL_SUBTITLE = f"Final Edition, version {EDITION_VERSION}"', src)
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

    def test_registry_content_status_and_lifecycle_values_are_consistent(self):
        reg = safe_load_path(os.path.join(REPO_ROOT, "config", "chapter-status-registry.yaml"))
        status = reg["workbooks"]["addendum-04-05-tsfm"]["status"]
        self.assertIn(status, ("accepted_frozen", "drafted_pending_human_review"))
        if status != "accepted_frozen":
            # an open, human-instructed reopening must explain why; the final
            # builder then refuses to run, so the canonical PDF cannot be replaced
            open_ = [r for r in reg.get("reopenings", []) if r["workbook"] == "addendum-04-05-tsfm"
                     and r["state"].startswith("open")]
            self.assertEqual(len(open_), 1)
            self.assertEqual(open_[0]["granted_by"], "human")
        self.assertIn(reg["publications"]["addendum-04-05-tsfm"]["status"], ("accepted_frozen", "canonical_built", "published"))
        if status == "accepted_frozen":
            closed = [r for r in reg.get("reopenings", []) if r["workbook"] == "addendum-04-05-tsfm" and r["revision"] == "v1.1.0"]
            self.assertEqual(closed[0]["state"], "closed_accepted")

    @unittest.skipUnless(all(os.path.exists(p) for p in (FINAL, RC1, REVIEW)), "local PDFs not present")
    def test_final_matches_the_accepted_review_apart_from_the_edition_subtitle(self):
        r = subprocess.run([sys.executable, CHECKER], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, msg=r.stdout[-2500:])
        self.assertIn("RESULT: clean", r.stdout)


if __name__ == "__main__":
    unittest.main()
