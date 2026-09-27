"""Tests for the reusable chapter-review workflow
(scripts/chapter_review_checks.py and scripts/build_chapter_review.py).

Safety note: these tests read Chapters 1-4's real, accepted files to
validate the checkers against real fixtures, but they NEVER invoke
build_chapter_review.py's main() (which writes ch0N-review.qmd) against
a real chapter number -- that would overwrite an accepted, committed
review document. Anything that needs to exercise file-writing logic
uses a synthetic fixture under a temp directory instead.
"""
import os
import shutil
import sys
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import chapter_review_checks as crc  # noqa: E402
import build_chapter_review as bcr  # noqa: E402

WB05 = os.path.join(REPO_ROOT, "workbooks", "05-llm-training")


class TestDiscoveryAgainstRealAcceptedChapters(unittest.TestCase):
    """Read-only checks against Chapters 1-4's real files."""

    def test_discover_chapter_files_for_every_drafted_chapter(self):
        for num in ("01", "02", "03", "04"):
            chapter_path, solutions_path = crc.discover_chapter_files("05-llm-training", num)
            self.assertTrue(os.path.exists(chapter_path))
            self.assertTrue(os.path.exists(solutions_path))

    def test_discover_chapter_files_raises_on_unknown_chapter(self):
        with self.assertRaises(FileNotFoundError):
            crc.discover_chapter_files("05-llm-training", "99")

    def test_chapter_slug_from_path(self):
        self.assertEqual(bcr.discover_chapter_title.__module__, "build_chapter_review")
        slug = crc.chapter_slug_from_path(os.path.join(WB05, "chapters", "04-distributed-parallelism.qmd"))
        self.assertEqual(slug, "distributed-parallelism")

    def test_discover_book_title(self):
        title = bcr.discover_book_title("05-llm-training")
        self.assertEqual(title, "LLM Pretraining and Distributed Training")

    def test_discover_chapter_title_chapter4(self):
        chapter_path, _ = crc.discover_chapter_files("05-llm-training", "04")
        title, text = bcr.discover_chapter_title(chapter_path, "04")
        self.assertEqual(title, "Parallelism Strategies for Distributed Training")
        self.assertIn("Learning objectives", text)

    def test_discover_figures_chapter4_finds_both_figures(self):
        chapter_path, _ = crc.discover_chapter_files("05-llm-training", "04")
        _, text = bcr.discover_chapter_title(chapter_path, "04")
        figures = bcr.discover_figures("05-llm-training", text)
        svg_ids = {f["svg_id"] for f in figures}
        self.assertEqual(svg_ids, {"fig-process-group-composition", "fig-pipeline-timeline"})
        for f in figures:
            self.assertTrue(os.path.exists(f["svg_path"]), msg=f["svg_path"])
            self.assertIsNotNone(f["script_path"], msg=f"no matching script found for {f['svg_id']}")
            self.assertTrue(os.path.exists(f["script_path"]))

    def test_discover_source_ids_chapter4(self):
        chapter_path, solutions_path = crc.discover_chapter_files("05-llm-training", "04")
        _, chapter_text = bcr.discover_chapter_title(chapter_path, "04")
        with open(solutions_path, encoding="utf-8") as f:
            solutions_text = f.read()
        ids = bcr.discover_source_ids(chapter_text, solutions_text)
        self.assertEqual(ids, ["src-17", "src-52", "src-53", "src-54"])


class TestCrossReferenceCheckAgainstRealChapters(unittest.TestCase):
    """This is the exact generalization of the Chapter 3 round-1 defect
    (Answer Key referencing the chapter-level anchor instead of "Check
    your understanding" specifically). Chapters 1-2 predate the fix and
    are EXPECTED to fail this check -- that is a real, pre-existing
    finding to report, not a bug in the checker; Chapters 3-4 are
    expected to pass since both were corrected during their own review
    rounds."""

    def _check(self, num):
        chapter_path, solutions_path = crc.discover_chapter_files("05-llm-training", num)
        return crc.check_answer_key_cross_reference(chapter_path, solutions_path)

    def test_chapter1_and_2_have_the_known_preexisting_gap(self):
        for num in ("01", "02"):
            result = self._check(num)
            self.assertFalse(result["ok"], msg=f"ch{num} unexpectedly passed -- checker regression?")
            self.assertIn("no explicit", result["issue"])

    def test_chapter3_and_4_pass(self):
        for num in ("03", "04"):
            result = self._check(num)
            self.assertTrue(result["ok"], msg=f"ch{num}: {result['issue']}")

    def test_checker_flags_a_synthetic_chapter_level_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            chapter_path = os.path.join(d, "05-fake-chapter.qmd")
            solutions_path = os.path.join(d, "05-fake-chapter-solutions.qmd")
            with open(chapter_path, "w", encoding="utf-8") as f:
                f.write("## Fake Chapter {#sec-ch5}\n\n### Check your understanding {#sec-ch5-check}\n")
            with open(solutions_path, "w", encoding="utf-8") as f:
                f.write('Full solutions to Chapter 5\'s "Check your understanding" questions\n(@sec-ch5).\n')
            result = crc.check_answer_key_cross_reference(chapter_path, solutions_path)
            self.assertFalse(result["ok"])
            self.assertIn("chapter-level anchor", result["issue"])


class TestLeakageChecker(unittest.TestCase):
    def test_clean_text_passes(self):
        text = (
            "This claim is verified by a script-backed calculation, checked programmatically "
            "against the source's own reported values. See the Bibliography for full citations."
        )
        result = crc.check_text_leakage(text)
        self.assertTrue(result["ok"], msg=result)

    def test_ordinary_learner_facing_terms_are_permitted(self):
        text = "The source states this result was verified programmatically using a script-backed calculation."
        result = crc.check_text_leakage(text)
        self.assertTrue(result["ok"], msg=result)

    def test_leaky_text_is_flagged_in_every_category(self):
        text = (
            "About this review package -- Page renders, a contact sheet, and the generating script "
            "accompany this PDF; see mtp_target_alignment.py and "
            "workbooks/05-llm-training/chapters/02-multi-token-prediction.qmd for src-43 details."
        )
        result = crc.check_text_leakage(text)
        self.assertFalse(result["ok"])
        self.assertIn("src-43", result["source_registry_ids"])
        self.assertIn("mtp_target_alignment.py", result["py_filenames"])
        self.assertIn("02-multi-token-prediction.qmd", result["qmd_filenames"])
        self.assertTrue(any("About this review" in m for m in result["review_process_phrases"]))

    def test_accepted_chapter4_review_pdf_text_is_clean(self):
        import subprocess
        pdf = os.path.join(
            REPO_ROOT, "outputs", "_development", "05-llm-training",
            "chapter-04-review", "05-llm-training-ch04-review.pdf",
        )
        if not os.path.exists(pdf):
            self.skipTest("chapter-04-review PDF not built in this environment")
        text = subprocess.run(["pdftotext", pdf, "-"], capture_output=True, text=True).stdout
        result = crc.check_text_leakage(text)
        self.assertTrue(result["ok"], msg=result)


class TestFigureAndWorkedExampleContractExistence(unittest.TestCase):
    def test_figure_invariant_test_presence_is_reported_per_figure(self):
        findings = crc.check_figure_invariant_tests(WB05)
        by_name = {f["figure_script"]: f["has_dedicated_semantic_test"] for f in findings}
        self.assertIn("fig_pipeline_timeline.py", by_name)
        self.assertTrue(by_name["fig_pipeline_timeline.py"], "fig_pipeline_timeline.py must have a dedicated test")

    def test_worked_example_scoped_test_exists_and_is_workbook_filtered(self):
        for num in ("01", "02", "03", "04"):
            result = crc.check_worked_example_scoped_test_exists("05-llm-training", num)
            self.assertTrue(result["found"], msg=f"ch{num}: {result}")
            for path in result["scoped_worked_example_test_files"]:
                full_path = os.path.join(REPO_ROOT, path)
                with open(full_path, encoding="utf-8") as f:
                    self.assertIn("05-llm-training", f.read())

    def test_workbook04_owned_files_are_excluded_by_content_filter(self):
        # tests/test_ch03_worked_examples.py and test_ch04_worked_examples.py
        # belong to Workbook 04's own Chapter 3/4 -- a real, pre-existing
        # filename collision. The content filter must exclude them.
        result03 = crc.check_worked_example_scoped_test_exists("05-llm-training", "03")
        result04 = crc.check_worked_example_scoped_test_exists("05-llm-training", "04")
        self.assertNotIn("tests/test_ch03_worked_examples.py", result03["scoped_worked_example_test_files"])
        self.assertNotIn("tests/test_ch04_worked_examples.py", result04["scoped_worked_example_test_files"])


class TestQuestionAnswerCorrespondence(unittest.TestCase):
    def test_all_four_drafted_chapters_are_synchronized(self):
        chapters = [
            ("01", "pretraining-objectives-and-data"),
            ("02", "multi-token-prediction"),
            ("03", "optimization-and-scaling-laws"),
            ("04", "distributed-parallelism"),
        ]
        for num, slug in chapters:
            chapter_path, solutions_path = crc.discover_chapter_files("05-llm-training", num)
            result = crc.check_question_answer_correspondence(
                chapter_path, solutions_path, os.path.join(WB05, "questions.yaml"), slug,
            )
            self.assertTrue(result["ok"], msg=f"ch{num}: {result}")
            self.assertEqual(result["questions_in_chapter_prose"], 5)


class TestClaimLedgerCoverage(unittest.TestCase):
    def test_all_four_drafted_chapters_have_entries_with_known_sources(self):
        for num in ("01", "02", "03", "04"):
            result = crc.check_claim_ledger_coverage(WB05, "05-llm-training", num)
            self.assertTrue(result["ok"], msg=f"ch{num}: {result}")
            self.assertGreater(result["num_claim_entries"], 0)


class TestPageDensityDiagnosticOnSyntheticFixtures(unittest.TestCase):
    """Fast, deterministic tests using fabricated page-text lists --
    no PDF rendering involved."""

    def test_clean_single_page_bibliography_is_not_flagged(self):
        pages = ["Some content here.", "Bibliography\n[1] Source one.\n[2] Source two.\n[3] Source three."]
        result = crc.diagnose_bibliography_split(pages)
        self.assertFalse(result["flagged"])

    def test_midlist_split_is_flagged(self):
        pages = [
            "Some content here.",
            "Bibliography\n[1] Source one.",
            "[2] Source two.\n[3] Source three.",
        ]
        result = crc.diagnose_bibliography_split(pages)
        self.assertTrue(result["flagged"])

    def test_long_bibliography_splitting_between_whole_entries_is_not_flagged(self):
        # Mirrors the real, accepted canonical-book case: 8 entries on
        # the heading's own page, 3 more entries on the next page --
        # a normal reflow, not a defect.
        pages = [
            "Bibliography\n" + "\n".join(f"[{i}] Source {i}." for i in range(1, 9)),
            "\n".join(f"[{i}] Source {i}." for i in range(9, 12)),
        ]
        result = crc.diagnose_bibliography_split(pages)
        self.assertFalse(result["flagged"])

    def test_sparse_bibliography_page_is_labeled_acceptable_not_failed(self):
        pages = ["Title page.", "Some content." * 20, "Bibliography\n[1] A.\n[2] B.\n[3] C."]
        bib_diag = crc.diagnose_bibliography_split(pages)
        word_counts = [len(p.split()) for p in pages]
        flags = crc.flag_sparse_pages(word_counts, bib_diag)
        page3_flags = [f for f in flags if f["page"] == 3]
        self.assertEqual(len(page3_flags), 1)
        self.assertIn("acceptable", page3_flags[0]["reason"])

    def test_no_bibliography_heading_found(self):
        result = crc.diagnose_bibliography_split(["Just some content.", "More content."])
        self.assertIsNone(result["bibliography_page"])
        self.assertFalse(result["flagged"])


class TestTemplateRendering(unittest.TestCase):
    """Exercises render_template()'s string substitution in isolation
    -- does not write into any real workbook directory."""

    def test_template_substitution_without_pagebreak(self):
        filled = bcr.render_template(
            "Some Book Title", "05", "Some Chapter Title",
            "chapters/05-some-chapter.qmd", "solutions/05-some-chapter-solutions.qmd",
            pagebreak_before_bib=False,
        )
        self.assertIn('title: "Some Book Title"', filled)
        self.assertIn("Chapter 5 Review Draft", filled)
        self.assertIn("Some Chapter Title", filled)
        self.assertIn("{{< include chapters/05-some-chapter.qmd >}}", filled)
        self.assertIn("{{< include solutions/05-some-chapter-solutions.qmd >}}", filled)
        self.assertNotIn("#pagebreak()", filled)
        self.assertNotIn("__", filled, msg="an unfilled __PLACEHOLDER__ token leaked into the output")

    def test_template_substitution_with_pagebreak(self):
        filled = bcr.render_template(
            "Some Book Title", "05", "Some Chapter Title",
            "chapters/05-some-chapter.qmd", "solutions/05-some-chapter-solutions.qmd",
            pagebreak_before_bib=True,
        )
        self.assertIn("#pagebreak()", filled)
        self.assertNotIn("__", filled)


if __name__ == "__main__":
    unittest.main()
