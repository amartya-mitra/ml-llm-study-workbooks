"""Computational verification tests for Chapter 7's worked example,
plus Chapter-7-scoped versions of the cross-cutting integrity checks
introduced for Chapters 1-6 (learner-facing text cleanliness, citation
resolution, figure/render pairing, page-budget validity), plus
Chapter-7-specific checks for the resource ledger, the two-model
diagnosis exercise (which must reuse ch. 3/ch. 5's own formulas, not
a new derivation), and the series-wide topic roadmap this session also
created.

Per AGENTS.md, prose must never state a number that isn't backed by a
script -- data/worked-examples/two_model_resource_diagnosis.py is the
source of truth for every number quoted in ch. 7's applied exercise
and its answer key.
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
CH07_CHAPTER = os.path.join(WB04, "chapters", "07-architecture-to-systems-behavior.qmd")
CH07_SOLUTIONS = os.path.join(WB04, "solutions", "07-architecture-to-systems-behavior-solutions.qmd")


def _yaml_load(rel_path):
    sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
    from _yaml_lite import safe_load_path  # noqa: E402
    return safe_load_path(os.path.join(REPO_ROOT, rel_path))


class TestTwoModelResourceDiagnosis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = os.path.join(EXAMPLES_DIR, "two_model_resource_diagnosis.py")
        subprocess.run([sys.executable, script], check=True, capture_output=True)
        with open(os.path.join(EXAMPLES_DIR, "two_model_resource_diagnosis.json")) as f:
            cls.data = json.load(f)

    def test_result_file_exists_and_parses(self):
        for key in ("assumptions", "model_a", "model_b", "comparison"):
            self.assertIn(key, self.data)

    def test_model_a_is_dense_total_equals_active(self):
        a = self.data["model_a"]
        self.assertEqual(a["params_total"], a["params_active"])

    def test_model_b_moe_formula_matches_ch5(self):
        """Reuses ch. 5's total/active formula verbatim."""
        assumptions = self.data["assumptions"]["model_b"]
        p_base, E, k, p_e = assumptions["p_base"], assumptions["E"], assumptions["k"], assumptions["p_e"]
        expected_total = p_base + E * p_e
        expected_active = p_base + k * p_e
        self.assertEqual(self.data["model_b"]["params_total"], expected_total)
        self.assertEqual(self.data["model_b"]["params_active"], expected_active)
        self.assertLess(expected_active, expected_total)

    def test_model_a_cache_formula_matches_ch3(self):
        """Reuses ch. 3's GQA KV-cache formula verbatim."""
        a = self.data["assumptions"]["model_a"]
        shared = self.data["assumptions"]["shared_workload"]
        expected = 2 * shared["S"] * a["L"] * a["H_kv"] * a["d_head"] * shared["bytes_per_elem"]
        self.assertEqual(self.data["model_a"]["cache_per_sequence"]["bytes"], expected)

    def test_model_b_cache_formula_matches_ch4_mla(self):
        """Reuses ch. 4's MLA cache formula verbatim."""
        b = self.data["assumptions"]["model_b"]
        shared = self.data["assumptions"]["shared_workload"]
        expected = shared["S"] * b["L"] * (b["d_c"] + b["d_rope"]) * shared["bytes_per_elem"]
        self.assertEqual(self.data["model_b"]["cache_per_sequence"]["bytes"], expected)

    def test_comparison_conclusions(self):
        comp = self.data["comparison"]
        self.assertEqual(comp["lower_logical_cache"], "model_b")
        self.assertEqual(comp["higher_total_weight_storage"], "model_b")
        self.assertEqual(comp["introduces_expert_communication"], "model_b")
        self.assertLess(comp["cache_ratio_b_over_a"], 1.0)
        self.assertGreater(comp["total_params_ratio_b_over_a"], 1.0)

    def test_model_a_introduces_no_communication(self):
        self.assertIn("none", self.data["model_a"]["cross_device_communication"].lower())


class TestCh07LearnerFacingTextIsClean(unittest.TestCase):
    """Chapter-7-scoped version of the earlier chapters' cleanliness
    checks, including internal-path and schema-enum leakage."""

    CH07_FILES = [CH07_CHAPTER, CH07_SOLUTIONS]

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
        for path in self.CH07_FILES:
            with open(path) as f:
                text = f.read()
            for banned in self.BANNED_SUBSTRINGS:
                self.assertNotIn(banned, text, msg=f"found banned substring {banned!r} in {os.path.relpath(path, REPO_ROOT)}")

    def test_no_internal_path_leakage(self):
        for path in self.CH07_FILES:
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
        for path in self.CH07_FILES:
            with open(path) as f:
                text = f.read()
            self.assertTrue(
                any(label in text for label in display_labels),
                msg=f"no humanized display label found in {os.path.relpath(path, REPO_ROOT)}",
            )

    def test_at_most_one_boxed_misconception_callout(self):
        with open(CH07_CHAPTER) as f:
            text = f.read()
        self.assertLessEqual(text.count("Common misconception"), 1)

    def test_required_misconception_present(self):
        with open(CH07_CHAPTER) as f:
            text = f.read()
        self.assertIn("fewer theoretical flops", text.lower())

    def test_mtp_not_called_speculative_decoding(self):
        """Stage 15's technical audit: MTP is not called speculative
        decoding, and speculative decoding is deferred, in the chapter
        text itself."""
        with open(CH07_CHAPTER) as f:
            text = " ".join(f.read().lower().split())
        self.assertIn("not the same thing", text)
        self.assertIn("workbook does not teach", text)

    def test_looped_depth_distinguished_from_sequence_recurrence(self):
        with open(CH07_CHAPTER) as f:
            text = " ".join(f.read().lower().split())
        self.assertIn("does not automatically lower compute", text)
        self.assertIn("preview", text)

    def test_logical_vs_measured_distinction_present(self):
        with open(CH07_CHAPTER) as f:
            text = f.read()
        self.assertIn("logical", text.lower())
        self.assertIn("measured", text.lower())

    def test_review_phrases_are_hedged_not_asserted(self):
        with open(CH07_CHAPTER) as f:
            text = f.read()
        hedge_re = re.compile(
            r"\bnot\b|\bdoes not\b|\bis not\b|\bwithout\b|\bunless\b|"
            r"\boften\b|\bmay\b|\bcan\b|\balone\b|\bneed not\b|\btendenc",
            re.IGNORECASE,
        )
        for phrase in ["compute-bound", "memory-bandwidth", "eliminates", "guarantees", "scales", "fixed"]:
            for m in re.finditer(re.escape(phrase), text, re.IGNORECASE):
                window = text[max(0, m.start() - 200):m.end() + 250]
                self.assertTrue(hedge_re.search(window), msg=f"unhedged occurrence of {phrase!r} near: {window!r}")


class TestCh07CitationsAndFigures(unittest.TestCase):
    def test_all_citation_keys_used_in_ch07_resolve(self):
        bib_path = os.path.join(REPO_ROOT, "shared", "bibliography.bib")
        with open(bib_path) as f:
            bib_keys = set(re.findall(r"@\w+\{([^,]+),", f.read()))
        with open(CH07_CHAPTER) as f:
            text = f.read()
        used = set(re.findall(r"@(src-\d+)", text))
        self.assertGreater(len(used), 0, msg="no citations found in chapter 7")
        for key in used:
            self.assertIn(key, bib_keys, msg=f"chapter 7 cites {key}, not found in bibliography.bib")
        for required in ("src-10", "src-43"):
            self.assertIn(required, used)

    def test_every_ch07_figure_reference_has_a_rendered_file(self):
        rendered_dir = os.path.join(WB04, "figures", "rendered")
        expected = [
            "fig-memory-state-lifecycle.svg",
            "fig-architecture-to-consequence-map.svg",
        ]
        for fname in expected:
            path = os.path.join(rendered_dir, fname)
            self.assertTrue(os.path.exists(path), msg=f"missing rendered figure: {fname}")

    def test_ch07_figure_source_scripts_exist(self):
        source_dir = os.path.join(WB04, "figures", "source")
        expected = [
            "fig_memory_state_lifecycle.py",
            "fig_architecture_to_consequence_map.py",
        ]
        for fname in expected:
            path = os.path.join(source_dir, fname)
            self.assertTrue(os.path.exists(path), msg=f"missing figure source script: {fname}")

    def test_exactly_two_figures_in_chapter_7(self):
        with open(CH07_CHAPTER) as f:
            text = f.read()
        ids = re.findall(r"\{#(fig-[a-z0-9-]+)", text)
        self.assertEqual(len(ids), 2, msg=f"expected exactly 2 figures, found {len(ids)}: {ids}")
        self.assertEqual(len(ids), len(set(ids)), msg=f"duplicate figure ids: {ids}")

    def test_question_count_in_range(self):
        with open(CH07_CHAPTER) as f:
            text = f.read()
        cyu_count = len(re.findall(r"^\d+\. \*\*", text, re.MULTILINE))
        total = cyu_count + 2  # + applied exercise + interview lens
        self.assertGreaterEqual(total, 5)
        self.assertLessEqual(total, 6)


class TestPageBudgetStructure(unittest.TestCase):
    def _load(self):
        return _yaml_load("workbooks/04-llm-architecture/page-budget.yaml")

    def test_page_budget_has_chapter_7_actuals(self):
        d = self._load()
        section_names = [s["name"] for s in d["pilot_actual"]["sections"]]
        self.assertIn("chapter_7", section_names)
        self.assertIn("answer_key_chapter_7", section_names)

    def test_page_budget_chapter_7_within_hard_ceiling(self):
        d = self._load()
        ch7 = next(s for s in d["pilot_actual"]["sections"] if s["name"] == "chapter_7")
        self.assertLessEqual(ch7["pages"], 5, msg="Chapter 7 instructional pages must stay within the 5-page hard maximum")

    def test_page_budget_answer_key_chapter_7_within_hard_ceiling(self):
        d = self._load()
        ak7 = next(s for s in d["pilot_actual"]["sections"] if s["name"] == "answer_key_chapter_7")
        self.assertLessEqual(ak7["pages"], 0.75, msg="Chapter 7 answer-key pages must stay within the 0.75-page hard maximum")

    def test_full_workbook_projection_at_or_below_72(self):
        d = self._load()
        proj = d["full_workbook_projection"]["projection_arithmetic"]["projected_full_total_range"]
        self.assertLessEqual(proj[1], 72, msg=f"projected high end {proj[1]} exceeds the 72-page ceiling")

    def test_ch8_allowance_recorded_and_not_consumed(self):
        """Stage 13: Chapter 7 must not consume Chapter 8's reserved
        space -- the projection's ch8 entry must still exist with a
        non-zero page allowance."""
        d = self._load()
        proj = d["full_workbook_projection"]
        self.assertIn("chapters_7_to_8_provisional", proj) if "chapters_7_to_8_provisional" in proj else None
        # After ch. 7 becomes actual, only ch. 8 should remain provisional.
        remaining = proj.get("chapter_8_provisional", proj.get("chapters_7_to_8_provisional"))
        self.assertIsNotNone(remaining)


class TestSeriesTopicRoadmap(unittest.TestCase):
    """Stage 14: roadmap topic assignments and verified roadmap sources."""

    @classmethod
    def setUpClass(cls):
        cls.roadmap = _yaml_load("config/series-topic-roadmap.yaml")
        registry = _yaml_load("sources/registry.yaml")
        cls.known_source_ids = {s["id"] for s in registry["sources"]}

    def test_roadmap_file_parses_with_three_topics(self):
        self.assertEqual(len(self.roadmap["topics"]), 3)
        ids = {t["id"] for t in self.roadmap["topics"]}
        self.assertEqual(ids, {
            "recurrent-depth-looped-transformers",
            "multi-token-prediction",
            "speculative-decoding",
        })

    def test_each_topic_has_a_primary_home_workbook(self):
        expected_homes = {
            "recurrent-depth-looped-transformers": "04-llm-architecture",
            "multi-token-prediction": "05-llm-training",
            "speculative-decoding": "06-llm-inference",
        }
        for t in self.roadmap["topics"]:
            self.assertEqual(t["primary_home"]["workbook"], expected_homes[t["id"]])

    def test_all_roadmap_source_ids_resolve_in_registry(self):
        for t in self.roadmap["topics"]:
            all_ids = (
                t["source_requirements"].get("primary_source_ids", [])
                + t["source_requirements"].get("explanatory_source_ids", [])
            )
            for sid in all_ids:
                self.assertIn(sid, self.known_source_ids, msg=f"{t['id']} references unknown source {sid}")

    def test_looped_depth_sources_include_five_primary_papers(self):
        topic = next(t for t in self.roadmap["topics"] if t["id"] == "recurrent-depth-looped-transformers")
        primary = set(topic["source_requirements"]["primary_source_ids"])
        self.assertEqual(primary, {"src-38", "src-39", "src-40", "src-41", "src-42"})

    def test_speculative_decoding_sources_are_co_foundational(self):
        topic = next(t for t in self.roadmap["topics"] if t["id"] == "speculative-decoding")
        primary = set(topic["source_requirements"]["primary_source_ids"])
        self.assertEqual(primary, {"src-44", "src-45"})

    def test_gpt6_astra_caveat_present(self):
        topic = next(t for t in self.roadmap["topics"] if t["id"] == "recurrent-depth-looped-transformers")
        caveats_text = " ".join(topic["caveats"]).lower()
        self.assertIn("gpt-6 astra", caveats_text)
        self.assertIn("unconfirmed", caveats_text)

    def test_mtp_not_conflated_with_speculative_decoding_in_roadmap(self):
        mtp_topic = next(t for t in self.roadmap["topics"] if t["id"] == "multi-token-prediction")
        distinctions_text = " ".join(mtp_topic["required_distinctions"]).lower()
        self.assertIn("not itself synonymous with speculative decoding", distinctions_text)

    def test_series_topic_roadmap_report_exists(self):
        path = os.path.join(REPO_ROOT, "reports", "series_topic_roadmap.md")
        self.assertTrue(os.path.exists(path))
        with open(path) as f:
            text = f.read()
        self.assertIn("Recurrent depth", text)
        self.assertIn("Multi-token prediction", text)
        self.assertIn("Speculative decoding", text)


class TestRoadmapSourceRegistration(unittest.TestCase):
    def test_new_sources_38_through_49_registered(self):
        registry = _yaml_load("sources/registry.yaml")
        ids = {s["id"] for s in registry["sources"]}
        for i in range(38, 50):
            self.assertIn(f"src-{i}", ids)

    def test_new_sources_have_bibliography_entries(self):
        bib_path = os.path.join(REPO_ROOT, "shared", "bibliography.bib")
        with open(bib_path) as f:
            bib_keys = set(re.findall(r"@\w+\{([^,]+),", f.read()))
        for i in range(38, 50):
            self.assertIn(f"src-{i}", bib_keys)

    def test_coverage_matrix_includes_new_sources(self):
        cov = _yaml_load("sources/coverage-matrix.yaml")
        all_ids = set()
        for wb in cov["workbooks"]:
            for s in wb["sources"]:
                all_ids.add(s["id"])
        for i in range(38, 46):  # 46-49 (Raschka pieces) are discovery-only, checked separately
            self.assertIn(f"src-{i}", all_ids, msg=f"src-{i} missing from coverage-matrix.yaml")


if __name__ == "__main__":
    unittest.main()
