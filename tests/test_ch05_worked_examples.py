"""Computational verification tests for Chapter 5's worked examples,
plus Chapter-5-scoped versions of the cross-cutting integrity checks
introduced for Chapters 1-4 (learner-facing text cleanliness, citation
resolution, figure/render pairing, page-budget structure).

Per AGENTS.md, prose must never state a number that isn't backed by a
script -- data/worked-examples/moe_param_counts.py and
moe_routing_imbalance.py are the source of truth for every number
quoted in chapters/05-mixture-of-experts.qmd.
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


class TestMoeParamCounts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = os.path.join(EXAMPLES_DIR, "moe_param_counts.py")
        subprocess.run([sys.executable, script], check=True, capture_output=True)
        with open(os.path.join(EXAMPLES_DIR, "moe_param_counts.json")) as f:
            cls.data = json.load(f)

    def test_result_file_exists_and_parses(self):
        for key in ("assumptions", "routed_expert_bank", "expert_related", "complete_model"):
            self.assertIn(key, self.data)

    def test_config_matches_chapter_prose(self):
        a = self.data["assumptions"]
        self.assertEqual(a["E"], 8)
        self.assertEqual(a["k"], 2)
        self.assertEqual(a["p_e"], 100_000_000)
        self.assertEqual(a["p_s"], 100_000_000)
        self.assertEqual(a["p_base"], 1_200_000_000)

    def test_routed_bank_formula_matches_manual_computation(self):
        a = self.data["assumptions"]
        bank = self.data["routed_expert_bank"]
        self.assertEqual(bank["total"], a["E"] * a["p_e"])
        self.assertEqual(bank["active"], a["k"] * a["p_e"])

    def test_complete_model_formula_matches_manual_computation(self):
        a = self.data["assumptions"]
        model = self.data["complete_model"]
        expected_total = a["p_base"] + a["E"] * a["p_e"] + a["p_s"]
        expected_active = a["p_base"] + a["k"] * a["p_e"] + a["p_s"]
        self.assertEqual(model["total"], expected_total)
        self.assertEqual(model["active"], expected_active)

    def test_exact_values(self):
        bank = self.data["routed_expert_bank"]
        model = self.data["complete_model"]
        self.assertEqual(bank["total"], 800_000_000)
        self.assertEqual(bank["active"], 200_000_000)
        self.assertEqual(model["total"], 2_100_000_000)
        self.assertEqual(model["active"], 1_500_000_000)

    def test_e_over_k_is_not_the_model_ratio(self):
        """The chapter's central invariant: E/k (bank ratio) must NOT
        equal the complete model's total/active ratio."""
        e_over_k = self.data["e_over_k"]
        bank_ratio = self.data["routed_expert_bank"]["total_active_ratio"]
        model_ratio = self.data["complete_model"]["total_active_ratio"]
        self.assertAlmostEqual(e_over_k, 4.0, places=6)
        self.assertAlmostEqual(bank_ratio, e_over_k, places=6)
        self.assertNotAlmostEqual(model_ratio, e_over_k, places=2)
        self.assertAlmostEqual(model_ratio, 1.4, places=6)

    def test_check_your_understanding_q6_instantiation(self):
        """Chapter 5's check-your-understanding Q6 (and answer-key Q6)
        asks about E=16, k=4, p_e=50M, no shared expert, p_base=2B --
        verify that specific instantiation independently of the
        script's default config."""
        E, k, p_e, p_s, p_base = 16, 4, 50_000_000, 0, 2_000_000_000
        bank_total = E * p_e
        bank_active = k * p_e
        model_total = p_base + E * p_e + p_s
        model_active = p_base + k * p_e + p_s
        self.assertEqual(bank_total, 800_000_000)
        self.assertEqual(bank_active, 200_000_000)
        self.assertEqual(model_total, 2_800_000_000)
        self.assertEqual(model_active, 2_200_000_000)
        self.assertAlmostEqual(bank_total / bank_active, 4.0, places=6)
        self.assertAlmostEqual(model_total / model_active, 2800 / 2200, places=6)


class TestMoeRoutingImbalance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = os.path.join(EXAMPLES_DIR, "moe_routing_imbalance.py")
        subprocess.run([sys.executable, script], check=True, capture_output=True)
        with open(os.path.join(EXAMPLES_DIR, "moe_routing_imbalance.json")) as f:
            cls.data = json.load(f)

    def test_result_file_exists_and_parses(self):
        for key in ("counts_per_expert", "nominal_balanced_load", "capacity_per_expert", "overflow_per_expert"):
            self.assertIn(key, self.data)

    def test_matches_figure_assignment(self):
        """Must match fig_moe_routing_parallelism.py's hand-chosen
        assignment exactly, so the figure and the worked example
        describe the same concrete scenario."""
        self.assertEqual(self.data["assumptions"]["num_tokens"], 6)
        self.assertEqual(self.data["assumptions"]["num_experts"], 4)
        self.assertEqual(self.data["counts_per_expert"], {"0": 3, "1": 1, "2": 1, "3": 1})

    def test_counts_sum_to_num_tokens(self):
        total = sum(self.data["counts_per_expert"].values())
        self.assertEqual(total, self.data["assumptions"]["num_tokens"])

    def test_nominal_balanced_load(self):
        expected = self.data["assumptions"]["num_tokens"] / self.data["assumptions"]["num_experts"]
        self.assertAlmostEqual(self.data["nominal_balanced_load"], expected, places=6)

    def test_capacity_and_overflow_matches_manual_computation(self):
        import math
        nominal = self.data["nominal_balanced_load"]
        cf = self.data["assumptions"]["capacity_factor"]
        expected_capacity = math.ceil(nominal * cf)
        self.assertEqual(self.data["capacity_per_expert"], expected_capacity)
        for e, count in self.data["counts_per_expert"].items():
            expected_overflow = max(0, count - expected_capacity)
            self.assertEqual(self.data["overflow_per_expert"][e], expected_overflow)

    def test_exact_overflow_value(self):
        self.assertEqual(self.data["overflow_per_expert"]["0"], 1)
        self.assertEqual(self.data["total_overflow_tokens"], 1)


class TestCh05LearnerFacingTextIsClean(unittest.TestCase):
    """Chapter-5-scoped version of the earlier chapters' cleanliness
    checks: no internal repo paths, no raw schema enum names, humanized
    display labels are used, and at most 2 boxed misconceptions."""

    CH05_FILES = [
        os.path.join(WB04, "chapters", "05-mixture-of-experts.qmd"),
        os.path.join(WB04, "solutions", "05-mixture-of-experts-solutions.qmd"),
    ]

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
        "(recall)",
        "(explanation)",
        "(calculation)",
        "(design)",
        "(debugging)",
    ]

    def test_no_banned_substrings(self):
        for path in self.CH05_FILES:
            with open(path) as f:
                text = f.read()
            for banned in self.BANNED_SUBSTRINGS:
                self.assertNotIn(banned, text, msg=f"found banned substring {banned!r} in {os.path.relpath(path, REPO_ROOT)}")

    def test_display_labels_used_instead_of_raw_enum_names(self):
        display_labels = [
            "Quick check", "Explain", "Calculation", "Compare",
            "Misconception check", "Design exercise", "Interview practice",
        ]
        for path in self.CH05_FILES:
            with open(path) as f:
                text = f.read()
            self.assertTrue(
                any(label in text for label in display_labels),
                msg=f"no humanized display label found in {os.path.relpath(path, REPO_ROOT)}",
            )

    def test_at_most_two_boxed_misconception_callouts(self):
        chapter_path = os.path.join(WB04, "chapters", "05-mixture-of-experts.qmd")
        with open(chapter_path) as f:
            text = f.read()
        self.assertLessEqual(text.count("Common misconception"), 2)

    def test_required_misconceptions_present(self):
        chapter_path = os.path.join(WB04, "chapters", "05-mixture-of-experts.qmd")
        with open(chapter_path) as f:
            text = f.read()
        self.assertIn("2/64", text)
        self.assertIn("Inactive experts consume no memory", text)

    def test_review_phrases_are_hedged_not_asserted(self):
        """Stage 15's manual-review phrase list: each occurrence in the
        chapter must appear inside a negation/hedge or a quoted
        misconception being corrected, not as a bare unqualified claim."""
        chapter_path = os.path.join(WB04, "chapters", "05-mixture-of-experts.qmd")
        with open(chapter_path) as f:
            text = f.read()
        hedge_re = re.compile(
            r"\bnot\b|\bdoes not\b|\bis not\b|\bwithout\b|\bdependent\b|\bunless\b|"
            r"\bencourages?\b|\bmay\b|\bcan\b|\bimplementation-dependent\b|\bcloser to\b",
            re.IGNORECASE,
        )
        for phrase in ["always", "guarantee", "no memory", "no compute"]:
            for m in re.finditer(re.escape(phrase), text, re.IGNORECASE):
                window = text[max(0, m.start() - 200):m.end() + 250]
                self.assertTrue(hedge_re.search(window), msg=f"unhedged occurrence of {phrase!r} near: {window!r}")

    def test_deferred_systems_topics_are_disclosed(self):
        chapter_path = os.path.join(WB04, "chapters", "05-mixture-of-experts.qmd")
        with open(chapter_path) as f:
            text = f.read()
        for topic in ["collective-communication", "kernel", "quantization", "post-training"]:
            self.assertIn(topic, text.lower())


class TestCh05CitationsAndFigures(unittest.TestCase):
    def test_all_citation_keys_used_in_ch05_resolve(self):
        bib_path = os.path.join(REPO_ROOT, "shared", "bibliography.bib")
        with open(bib_path) as f:
            bib_keys = set(re.findall(r"@\w+\{([^,]+),", f.read()))
        path = os.path.join(WB04, "chapters", "05-mixture-of-experts.qmd")
        with open(path) as f:
            text = f.read()
        used = set(re.findall(r"@(src-\d+)", text))
        self.assertGreater(len(used), 0, msg="no citations found in chapter 5")
        for key in used:
            self.assertIn(key, bib_keys, msg=f"chapter 5 cites {key}, not found in bibliography.bib")
        # src-36 (DeepSeekMoE) must be cited for the shared-experts claim, per Stage 13.
        self.assertIn("src-36", used)

    def test_every_ch05_figure_reference_has_a_rendered_file(self):
        rendered_dir = os.path.join(WB04, "figures", "rendered")
        expected = [
            "fig-dense-vs-moe.svg",
            "fig-moe-total-vs-active.svg",
            "fig-moe-routing-parallelism.svg",
        ]
        for fname in expected:
            path = os.path.join(rendered_dir, fname)
            self.assertTrue(os.path.exists(path), msg=f"missing rendered figure: {fname}")

    def test_ch05_figure_source_scripts_exist(self):
        source_dir = os.path.join(WB04, "figures", "source")
        expected = [
            "fig_dense_vs_moe.py",
            "fig_moe_total_vs_active.py",
            "fig_moe_routing_parallelism.py",
        ]
        for fname in expected:
            path = os.path.join(source_dir, fname)
            self.assertTrue(os.path.exists(path), msg=f"missing figure source script: {fname}")

    def test_exactly_three_figures_in_chapter_5(self):
        """Stage 10's figure budget: exactly 3, hard maximum 3."""
        chapter_path = os.path.join(WB04, "chapters", "05-mixture-of-experts.qmd")
        with open(chapter_path) as f:
            text = f.read()
        ids = re.findall(r"\{#(fig-[a-z0-9-]+)", text)
        self.assertEqual(len(ids), 3, msg=f"expected exactly 3 figures, found {len(ids)}: {ids}")
        self.assertEqual(len(ids), len(set(ids)), msg=f"duplicate figure ids: {ids}")


class TestPageBudgetStructure(unittest.TestCase):
    def _load(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
        from _yaml_lite import safe_load_path  # noqa: E402
        return safe_load_path(os.path.join(WB04, "page-budget.yaml"))

    def test_page_budget_has_chapter_5_actuals(self):
        d = self._load()
        section_names = [s["name"] for s in d["pilot_actual"]["sections"]]
        self.assertIn("chapter_5", section_names)

    def test_page_budget_chapter_5_within_hard_ceiling(self):
        d = self._load()
        ch5 = next(s for s in d["pilot_actual"]["sections"] if s["name"] == "chapter_5")
        self.assertLessEqual(ch5["pages"], 6, msg="Chapter 5 instructional pages must stay within the 6-page hard maximum")

    def test_full_workbook_projection_at_or_below_72(self):
        """Stage 14: after this chapter, the projected complete
        workbook must remain at or below 72 pages."""
        d = self._load()
        proj = d["full_workbook_projection"]["projection_arithmetic"]["projected_full_total_range"]
        self.assertLessEqual(proj[1], 72, msg=f"projected high end {proj[1]} exceeds the 72-page ceiling")


if __name__ == "__main__":
    unittest.main()
