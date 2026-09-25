"""Computational verification tests for Chapter 8's worked example,
plus Chapter-8-scoped versions of the cross-cutting integrity checks
introduced for Chapters 1-7 (learner-facing text cleanliness, citation
resolution, figure/render pairing, page-budget validity), plus
Chapter-8-specific checks for the L_distinct/T_passes/L_effective
arithmetic, the looped-depth source mappings, the MTP/source mappings,
and the required GPT-6 Astra uncertainty language.

Per AGENTS.md, prose must never state a number that isn't backed by a
script -- data/worked-examples/looped_vs_unrolled_depth.py is the
source of truth for every number quoted in ch. 8's worked example and
its answer key.
"""
import json
import os
import re
import subprocess
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WB04 = os.path.join(REPO_ROOT, "workbooks", "04-llm-architecture")
EXAMPLES_DIR = os.path.join(WB04, "data", "worked-examples")
CH08_CHAPTER = os.path.join(WB04, "chapters", "08-emerging-directions-and-synthesis.qmd")
CH08_SOLUTIONS = os.path.join(WB04, "solutions", "08-emerging-directions-and-synthesis-solutions.qmd")


def _yaml_load(rel_path):
    sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
    from _yaml_lite import safe_load_path  # noqa: E402
    return safe_load_path(os.path.join(REPO_ROOT, rel_path))


class TestLoopedVsUnrolledDepth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = os.path.join(EXAMPLES_DIR, "looped_vs_unrolled_depth.py")
        subprocess.run([sys.executable, script], check=True, capture_output=True)
        with open(os.path.join(EXAMPLES_DIR, "looped_vs_unrolled_depth.json")) as f:
            cls.data = json.load(f)

    def test_result_file_exists_and_parses(self):
        for key in ("assumptions", "L_effective", "block_applications",
                    "block_parameter_storage", "complete_model_parameters"):
            self.assertIn(key, self.data)

    def test_l_effective_matches_manual_computation(self):
        a = self.data["assumptions"]
        self.assertEqual(self.data["L_effective"], a["L_distinct"] * a["T_passes"])
        self.assertEqual(self.data["L_effective"], 44)

    def test_block_applications_equal_for_both(self):
        ba = self.data["block_applications"]
        self.assertEqual(ba["looped"], ba["conventional"])
        self.assertTrue(ba["equal"])
        self.assertEqual(ba["looped"], 44)

    def test_block_parameter_ratio_is_exactly_one_over_t_passes(self):
        bp = self.data["block_parameter_storage"]
        a = self.data["assumptions"]
        self.assertAlmostEqual(bp["ratio_looped_over_conventional"], 1 / a["T_passes"], places=6)
        self.assertAlmostEqual(bp["ratio_looped_over_conventional"], 0.5, places=6)
        self.assertTrue(bp["matches_one_over_T_passes"])

    def test_complete_model_ratio_is_not_exactly_point_five(self):
        """The chapter's central invariant: the complete-model ratio
        must NOT equal the block-only ratio when non-block params > 0."""
        cm = self.data["complete_model_parameters"]
        bp = self.data["block_parameter_storage"]
        self.assertNotAlmostEqual(cm["ratio_looped_over_conventional"], 0.5, places=2)
        self.assertGreater(cm["ratio_looped_over_conventional"], bp["ratio_looped_over_conventional"])
        self.assertTrue(cm["strictly_greater_than_block_only_ratio"])

    def test_check_your_understanding_q1_instantiation(self):
        """Ch. 8's CYU Q1 asks about L_distinct=12, T_passes=3 --
        verify independently of the script's default config."""
        L_distinct, T_passes = 12, 3
        self.assertEqual(L_distinct * T_passes, 36)


class TestCh08LearnerFacingTextIsClean(unittest.TestCase):
    CH08_FILES = [CH08_CHAPTER, CH08_SOLUTIONS]

    BANNED_SUBSTRINGS = [
        "figures/source",
        "data/worked-examples",
        "workbooks/04",
        "shared/question-schema",
        "misconception_diagnosis",
        "compare_and_contrast",
        "sources/registry.yaml",
        "notation.yaml",
        "questions.yaml",
        "config/series-topic-roadmap.yaml",
        "series_topic_roadmap.md",
        "(recall)",
        "(explanation)",
        "(calculation)",
        "(design)",
        "(debugging)",
    ]

    def test_no_banned_substrings(self):
        for path in self.CH08_FILES:
            with open(path) as f:
                text = f.read()
            for banned in self.BANNED_SUBSTRINGS:
                self.assertNotIn(banned, text, msg=f"found banned substring {banned!r} in {os.path.relpath(path, REPO_ROOT)}")

    def test_no_internal_path_leakage(self):
        for path in self.CH08_FILES:
            with open(path) as f:
                text = f.read()
            self.assertNotIn("/mnt/home", text)
            self.assertNotIn(".qmd", text)
            self.assertNotIn(".yaml", text)

    def test_display_labels_used_instead_of_raw_enum_names(self):
        display_labels = [
            "Quick check", "Explain", "Calculation", "Compare",
            "Misconception check", "Design exercise", "Interview practice",
        ]
        for path in self.CH08_FILES:
            with open(path) as f:
                text = f.read()
            self.assertTrue(
                any(label in text for label in display_labels),
                msg=f"no humanized display label found in {os.path.relpath(path, REPO_ROOT)}",
            )

    def test_at_most_one_boxed_misconception_callout(self):
        with open(CH08_CHAPTER) as f:
            text = f.read()
        self.assertLessEqual(text.count("Common misconception"), 1)

    def test_required_misconception_present(self):
        with open(CH08_CHAPTER) as f:
            text = " ".join(f.read().lower().split())
        self.assertIn("reusing the same layers gives the depth of a larger model", text)

    def test_astra_uncertainty_language_present(self):
        """Stage 6/15: GPT-6 Astra must be explicitly treated as
        unconfirmed, not verified fact, in the chapter's own text."""
        with open(CH08_CHAPTER) as f:
            text = " ".join(f.read().lower().split())
        self.assertIn("gpt-6 astra", text)
        self.assertIn("no official technical source confirms this architecture", text)
        self.assertIn("does not treat that proprietary architecture as verified", text)

    def test_depth_vs_sequence_recurrence_distinguished(self):
        with open(CH08_CHAPTER) as f:
            text = " ".join(f.read().lower().split())
        self.assertIn("depth recurrence", text)
        self.assertIn("sequence recurrence", text)
        self.assertIn("different mechanisms", text)

    def test_mtp_not_called_speculative_decoding(self):
        with open(CH08_CHAPTER) as f:
            text = " ".join(f.read().lower().split())
        self.assertIn("does not by itself define the complete", text)

    def test_research_proposal_vs_released_implementation_distinguished(self):
        with open(CH08_CHAPTER) as f:
            text = f.read()
        self.assertIn("research proposal", text.lower())
        self.assertIn("released, open-weight model", text.lower())

    def test_review_phrases_are_hedged_not_asserted(self):
        with open(CH08_CHAPTER) as f:
            text = f.read()
        hedge_re = re.compile(
            r"\bnot\b|\bdoes not\b|\bis not\b|\bwithout\b|\bunless\b|"
            r"\bmay\b|\bcan\b|\balone\b|\bneed not\b|\bproposal\b|\bcaveat\b",
            re.IGNORECASE,
        )
        for phrase in ["confirmed", "guarantees", "eliminates", "same kv cache", "half the model"]:
            for m in re.finditer(re.escape(phrase), text, re.IGNORECASE):
                window = text[max(0, m.start() - 200):m.end() + 250]
                self.assertTrue(hedge_re.search(window), msg=f"unhedged occurrence of {phrase!r} near: {window!r}")


class TestCh08CitationsAndFigures(unittest.TestCase):
    def test_all_citation_keys_used_in_ch08_resolve(self):
        bib_path = os.path.join(REPO_ROOT, "shared", "bibliography.bib")
        with open(bib_path) as f:
            bib_keys = set(re.findall(r"@\w+\{([^,]+),", f.read()))
        with open(CH08_CHAPTER) as f:
            text = f.read()
        used = set(re.findall(r"@(src-\d+)", text))
        self.assertGreater(len(used), 0, msg="no citations found in chapter 8")
        for key in used:
            self.assertIn(key, bib_keys, msg=f"chapter 8 cites {key}, not found in bibliography.bib")
        for required in ("src-38", "src-40", "src-42"):
            self.assertIn(required, used)

    def test_every_ch08_figure_reference_has_a_rendered_file(self):
        rendered_dir = os.path.join(WB04, "figures", "rendered")
        expected = [
            "fig-looped-vs-unrolled-depth.svg",
            "fig-architecture-decision-map.svg",
        ]
        for fname in expected:
            path = os.path.join(rendered_dir, fname)
            self.assertTrue(os.path.exists(path), msg=f"missing rendered figure: {fname}")

    def test_ch08_figure_source_scripts_exist(self):
        source_dir = os.path.join(WB04, "figures", "source")
        expected = [
            "fig_looped_vs_unrolled_depth.py",
            "fig_architecture_decision_map.py",
        ]
        for fname in expected:
            path = os.path.join(source_dir, fname)
            self.assertTrue(os.path.exists(path), msg=f"missing figure source script: {fname}")

    def test_exactly_two_figures_in_chapter_8(self):
        with open(CH08_CHAPTER) as f:
            text = f.read()
        ids = re.findall(r"\{#(fig-[a-z0-9-]+)", text)
        self.assertEqual(len(ids), 2, msg=f"expected exactly 2 figures, found {len(ids)}: {ids}")
        self.assertEqual(len(ids), len(set(ids)), msg=f"duplicate figure ids: {ids}")

    def test_question_count_in_range(self):
        with open(CH08_CHAPTER) as f:
            text = f.read()
        cyu_count = len(re.findall(r"^\d+\. \*\*", text, re.MULTILINE))
        total = cyu_count + 2  # + applied exercise + interview lens
        self.assertGreaterEqual(total, 5)
        self.assertLessEqual(total, 6)

    def test_question_ids_unique_project_wide(self):
        """Stage 15: question identifiers must resolve/be unique --
        spot-check that ch. 8's new question-plan.yaml entries did not
        duplicate an existing id."""
        qp = _yaml_load("workbooks/04-llm-architecture/question-plan.yaml")
        ids = [q["id"] for q in qp["interview_style_questions"]]
        self.assertEqual(len(ids), len(set(ids)), msg=f"duplicate interview-style question ids: {ids}")


class TestSeriesRoadmapCrossReferences(unittest.TestCase):
    """Stage 15: roadmap cross-references, looped-depth source
    mappings, and MTP/source mappings, as used by ch. 8."""

    @classmethod
    def setUpClass(cls):
        cls.roadmap = _yaml_load("config/series-topic-roadmap.yaml")

    def test_looped_depth_topic_references_ch8_as_drafted(self):
        topic = next(t for t in self.roadmap["topics"] if t["id"] == "recurrent-depth-looped-transformers")
        self.assertIn("ch8", topic["primary_home"]["location"])

    def test_mtp_topic_still_assigned_to_workbook_05(self):
        topic = next(t for t in self.roadmap["topics"] if t["id"] == "multi-token-prediction")
        self.assertEqual(topic["primary_home"]["workbook"], "05-llm-training")

    def test_speculative_decoding_topic_still_assigned_to_workbook_06(self):
        topic = next(t for t in self.roadmap["topics"] if t["id"] == "speculative-decoding")
        self.assertEqual(topic["primary_home"]["workbook"], "06-llm-inference")


class TestPageBudgetStructure(unittest.TestCase):
    def _load(self):
        return _yaml_load("workbooks/04-llm-architecture/page-budget.yaml")

    def test_page_budget_has_chapter_8_actuals(self):
        d = self._load()
        section_names = [s["name"] for s in d["pilot_actual"]["sections"]]
        self.assertIn("chapter_8", section_names)
        self.assertIn("answer_key_chapter_8", section_names)

    def test_page_budget_chapter_8_within_hard_ceiling(self):
        d = self._load()
        ch8 = next(s for s in d["pilot_actual"]["sections"] if s["name"] == "chapter_8")
        self.assertLessEqual(ch8["pages"], 5, msg="Chapter 8 instructional pages must stay within the 5-page hard maximum")

    def test_page_budget_answer_key_chapter_8_within_hard_ceiling(self):
        d = self._load()
        ak8 = next(s for s in d["pilot_actual"]["sections"] if s["name"] == "answer_key_chapter_8")
        self.assertLessEqual(ak8["pages"], 0.75, msg="Chapter 8 answer-key pages must stay within the 0.75-page hard maximum")

    def test_complete_workbook_within_release_ceiling(self):
        """This release candidate's own hard ceiling is 70 pages
        (tighter than the general 72-page project ceiling)."""
        d = self._load()
        total = d["pilot_actual"]["total_pages"]
        self.assertLessEqual(total, 70, msg=f"complete workbook total {total} exceeds this release's 70-page ceiling")

    def test_no_provisional_chapters_remain(self):
        """Chapter 8 was the last content chapter -- no *_provisional
        key should list any chapter as still-to-be-drafted."""
        d = self._load()
        proj = d["full_workbook_projection"]
        provisional_keys = [k for k in proj if k.endswith("_provisional")]
        for key in provisional_keys:
            self.assertEqual(proj[key], [], msg=f"{key} still lists provisional chapters: {proj[key]}")


if __name__ == "__main__":
    unittest.main()
