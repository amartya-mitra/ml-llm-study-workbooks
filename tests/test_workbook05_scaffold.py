"""Structural tests for the workbook 05 scaffold (no chapter content
drafted yet -- see reports/05_llm_training_scope_and_source_decision.md
and the scaffolding commit's own report).

These check that the *structure* is correct, not that any chapter has
real content: chapter files exist in the right order with unique
section identifiers, every source id a chapter file cites already
exists in the registry, the workbook_qa.py registry entry resolves,
output paths follow the established convention, no generated PDF sits
under chapters/, and workbook 04 is untouched by any of this.
"""
import os
import re
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from _yaml_lite import safe_load_path  # noqa: E402

WB05_DIR = os.path.join(REPO_ROOT, "workbooks", "05-llm-training")
CHAPTERS_DIR = os.path.join(WB05_DIR, "chapters")

EXPECTED_CHAPTER_FILES = [
    "01-pretraining-objectives-and-data.qmd",
    "02-multi-token-prediction.qmd",
    "03-optimization-and-scaling-laws.qmd",
    "04-distributed-parallelism.qmd",
    "05-training-memory-and-communication.qmd",
    "06-reading-real-pretraining-runs.qmd",
]

EXPECTED_SEC_IDS = [f"sec-ch{n}" for n in range(1, 7)]

SOURCE_ID_RE = re.compile(r"@(src-\d+)")


def _registry_ids():
    registry = safe_load_path(os.path.join(REPO_ROOT, "sources", "registry.yaml"))
    return {s["id"] for s in registry["sources"]}


class TestWorkbook05ChapterStructure(unittest.TestCase):
    def test_all_six_chapters_exist(self):
        for fname in EXPECTED_CHAPTER_FILES:
            path = os.path.join(CHAPTERS_DIR, fname)
            self.assertTrue(os.path.isfile(path), msg=f"missing chapter file: {fname}")

    def test_no_extra_chapter_files(self):
        actual = sorted(f for f in os.listdir(CHAPTERS_DIR) if f.endswith(".qmd"))
        self.assertEqual(actual, EXPECTED_CHAPTER_FILES,
                          msg="chapters/ directory contains files other than the six approved chapters")

    def test_chapter_order_in_index_matches_approved_list(self):
        index_path = os.path.join(WB05_DIR, "index.qmd")
        with open(index_path, encoding="utf-8") as f:
            content = f.read()
        include_re = re.compile(r"\{\{< include chapters/([a-z0-9-]+\.qmd) >\}\}")
        included = include_re.findall(content)
        self.assertEqual(included, EXPECTED_CHAPTER_FILES,
                          msg="index.qmd does not include the six chapters in the approved order")

    def test_each_chapter_has_a_unique_section_identifier(self):
        seen = []
        heading_re = re.compile(r"^##\s+.+?\{#(sec-ch\d+)\}", re.MULTILINE)
        for fname in EXPECTED_CHAPTER_FILES:
            path = os.path.join(CHAPTERS_DIR, fname)
            with open(path, encoding="utf-8") as f:
                content = f.read()
            matches = heading_re.findall(content)
            self.assertEqual(len(matches), 1, msg=f"{fname} must have exactly one top-level #sec-chN heading")
            seen.append(matches[0])
        self.assertEqual(seen, EXPECTED_SEC_IDS, msg="chapter section ids are not sec-ch1..sec-ch6 in order")
        self.assertEqual(len(seen), len(set(seen)), msg="duplicate section identifiers across chapters")

    def test_every_referenced_source_id_exists_in_registry(self):
        registry_ids = _registry_ids()
        cited = set()
        for fname in EXPECTED_CHAPTER_FILES:
            path = os.path.join(CHAPTERS_DIR, fname)
            with open(path, encoding="utf-8") as f:
                content = f.read()
            cited |= set(SOURCE_ID_RE.findall(content))
        self.assertTrue(cited, msg="no source ids were found in any chapter file -- test itself may be broken")
        missing = cited - registry_ids
        self.assertEqual(missing, set(), msg=f"chapter files cite source ids not present in sources/registry.yaml: {missing}")

    DRAFTED_CHAPTER_FILES = [
        "01-pretraining-objectives-and-data.qmd",
        "02-multi-token-prediction.qmd",
        "03-optimization-and-scaling-laws.qmd",
    ]

    def test_undrafted_chapters_have_an_explicit_pending_status_note(self):
        # Chapters 1-3 were drafted (2026-09-26 and 2026-09-27,
        # reports/05_llm_training_scope_and_source_decision.md's approval
        # gates) and no longer carry this marker -- checked separately
        # below. Chapters 4-6 remain scaffold-only and must still say so
        # explicitly.
        for fname in EXPECTED_CHAPTER_FILES:
            if fname in self.DRAFTED_CHAPTER_FILES:
                continue
            path = os.path.join(CHAPTERS_DIR, fname)
            with open(path, encoding="utf-8") as f:
                content = f.read()
            self.assertIn("drafting has not yet begun", content,
                          msg=f"{fname} is missing its explicit pending-drafting status note")

    def test_drafted_chapters_are_not_scaffolds(self):
        required_sections = [
            "### Learning objectives", "### Why this matters", "### Technical core",
            "### Worked example", "### Check your understanding",
            "### Chapter recap", "### Sources and further reading",
        ]
        for fname in self.DRAFTED_CHAPTER_FILES:
            path = os.path.join(CHAPTERS_DIR, fname)
            with open(path, encoding="utf-8") as f:
                content = f.read()
            self.assertNotIn("drafting has not yet begun", content,
                              msg=f"{fname} should no longer carry the scaffold-only pending marker")
            for required_section in required_sections:
                self.assertIn(required_section, content,
                              msg=f"{fname} is missing drafted section: {required_section}")


class TestWorkbook05RegistryAndOutputConventions(unittest.TestCase):
    def test_workbook_qa_registry_entry_resolves(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
        import workbook_qa  # noqa: E402
        self.assertIn("05-llm-training", workbook_qa.WORKBOOK_REGISTRY)
        cfg = workbook_qa.WORKBOOK_REGISTRY["05-llm-training"]
        self.assertEqual(cfg["title"], "LLM Pretraining and Distributed Training")
        self.assertEqual(cfg["canonical_pdf"], "05-llm-training-workbook.pdf")

    def test_canonical_output_path_matches_convention(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
        import workbook_qa  # noqa: E402
        cfg = workbook_qa.WORKBOOK_REGISTRY["05-llm-training"]
        self.assertEqual(cfg["canonical_pdf"], "05-llm-training-workbook.pdf")

    def test_no_generated_pdf_under_chapters_directory(self):
        for fname in os.listdir(CHAPTERS_DIR):
            self.assertFalse(fname.endswith(".pdf"), msg=f"a generated PDF exists under chapters/: {fname}")

    def test_release_and_development_directories_not_prematurely_created(self):
        # This scaffolding task does not generate an RC PDF; if a
        # scaffold-validation build has run, its evidence must live
        # under outputs/_development/, never outputs/_releases/ (which
        # is reserved for actual, reviewed release candidates).
        releases_dir = os.path.join(REPO_ROOT, "outputs", "_releases", "05-llm-training")
        if os.path.isdir(releases_dir):
            contents = os.listdir(releases_dir)
            self.assertEqual(contents, [], msg="outputs/_releases/05-llm-training/ must stay empty until an actual RC is produced")


class TestWorkbook04Untouched(unittest.TestCase):
    def test_workbook04_index_qmd_unchanged_marker(self):
        # A cheap, fast sanity check: workbook 04's index.qmd still
        # declares the RC7 subtitle exactly as it did before this
        # scaffolding task -- not a full checksum (see the scaffolding
        # commit's own report for that), but enough to catch an
        # accidental edit inside a test run.
        path = os.path.join(REPO_ROOT, "workbooks", "04-llm-architecture", "index.qmd")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Release Candidate 7", content,
                       msg="workbook 04's index.qmd subtitle changed -- workbook 04 must remain untouched")

    def test_workbook04_canonical_pdf_still_present(self):
        pdf_path = os.path.join(REPO_ROOT, "outputs", "04-modern-llm-architecture-workbook.pdf")
        self.assertTrue(os.path.isfile(pdf_path), msg="workbook 04's canonical PDF is missing")


if __name__ == "__main__":
    unittest.main()
