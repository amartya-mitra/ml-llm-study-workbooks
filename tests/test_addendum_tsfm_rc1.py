"""RC1-specific tests for the TSFM addendum.

Source-level tests run anywhere. The PDF-level test runs the verification
script only when the local RC1 and accepted review PDFs exist (they are
git-ignored build products), and is skipped otherwise.
"""
import os
import re
import subprocess
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from _yaml_lite import safe_load_path  # noqa: E402

BUILDER = os.path.join(REPO_ROOT, "scripts", "build_addendum_rc1.py")
CHECKER = os.path.join(REPO_ROOT, "scripts", "check_addendum_rc1.py")
INDEX = os.path.join(REPO_ROOT, "workbooks", "addendum-04-05-tsfm", "index.qmd")
RC1 = os.path.join(REPO_ROOT, "outputs", "_releases", "addendum-04-05-tsfm", "addendum-04-05-tsfm-rc1.pdf")
REVIEW = os.path.join(REPO_ROOT, "outputs", "_development", "addendum-04-05-tsfm", "integrated-review", "addendum-04-05-tsfm-review.pdf")


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


class TestRc1Builder(unittest.TestCase):
    def test_builder_writes_only_the_rc1_path_and_never_a_canonical_pdf(self):
        src = read(BUILDER)
        self.assertIn('f"{WB_ID}-rc1.pdf"', src)
        self.assertIn('"outputs", "_releases", WB_ID', src)
        code = src.split('"""', 2)[2]  # skip the module docstring, which names RC2 only to rule it out
        self.assertNotIn("rc2", code.lower())
        self.assertNotRegex(src, r"outputs[\"'],\s*f?[\"']\{?WB_ID\}?\.pdf")
        self.assertNotIn("git push", src)
        self.assertNotIn("git tag", src)

    def test_builder_renders_from_source_and_does_not_copy_the_review_pdf(self):
        src = read(BUILDER)
        self.assertIn('"quarto", "render", STAGING_QMD', src)
        self.assertNotIn("integrated-review", src)  # never reads or copies the review PDF

    def test_builder_requires_the_accepted_frozen_status(self):
        self.assertIn('entry.get("status") != "accepted_frozen"', read(BUILDER))

    def test_builder_changes_only_the_subtitle(self):
        src = read(INDEX)
        subtitle_lines = re.findall(r'^subtitle:\s*".*"\s*$', src, re.MULTILINE)
        self.assertEqual(len(subtitle_lines), 1)
        self.assertIn('SUBTITLE = "Release Candidate 1"', read(BUILDER))

    def test_accepted_index_source_keeps_its_descriptive_subtitle(self):
        # RC1 labeling lives in the builder; the frozen source is untouched
        self.assertNotIn("Release Candidate", read(INDEX))

    def test_builder_removes_its_staging_files_from_the_source_tree(self):
        self.assertIn("finally:", read(BUILDER))
        for name in ("rc1-build.qmd", "rc1-build.pdf"):
            self.assertFalse(os.path.exists(os.path.join(REPO_ROOT, "workbooks", "addendum-04-05-tsfm", name)))


class TestRc1State(unittest.TestCase):
    def test_publication_record_is_not_canonical_or_published(self):
        reg = safe_load_path(os.path.join(REPO_ROOT, "config", "chapter-status-registry.yaml"))
        self.assertEqual(reg["publications"]["addendum-04-05-tsfm"]["status"], "review_pending")
        self.assertNotIn("release_tag", reg["publications"]["addendum-04-05-tsfm"])

    def test_no_canonical_pdf_tag_or_rc2(self):
        rel = os.path.join(REPO_ROOT, "outputs", "_releases", "addendum-04-05-tsfm")
        if os.path.isdir(rel):
            names = [n for n in os.listdir(rel) if not re.search(r"\.prev-[0-9a-f]+$", n)]
            self.assertEqual(names, ["addendum-04-05-tsfm-rc1.pdf"])
        tags = subprocess.run(["git", "tag", "-l"], cwd=REPO_ROOT, capture_output=True, text=True).stdout.split()
        self.assertIn("workbook-04-v1.0.0", tags)
        self.assertIn("workbook-05-v1.0.0", tags)
        self.assertEqual([t for t in tags if t.startswith("addendum") and "rc" in t], [])

    def test_no_pdf_or_page_renders_are_tracked(self):
        out = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True).stdout.splitlines()
        offenders = [p for p in out if p.startswith("outputs/") and p != "outputs/.gitkeep"]
        self.assertEqual(offenders, [])
        self.assertEqual([p for p in out if "addendum-04-05-tsfm" in p and p.endswith((".pdf", ".png"))], [])

    @unittest.skipUnless(os.path.exists(RC1) and os.path.exists(REVIEW), "local RC1/review PDFs not present")
    def test_rc1_matches_the_accepted_review_apart_from_the_subtitle(self):
        r = subprocess.run([sys.executable, CHECKER], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, msg=r.stdout[-2500:])
        self.assertIn("RESULT: clean", r.stdout)


if __name__ == "__main__":
    unittest.main()
