"""Computational verification tests for Chapter 3's worked examples,
plus Chapter-3-scoped versions of the cross-cutting integrity checks
introduced for Chapters 1-2 (learner-facing text cleanliness, citation
resolution, figure/render pairing, page-budget structure).

Per AGENTS.md, prose must never state a number that isn't backed by a
script -- data/worked-examples/attention_head_variants.py is the
source of truth for every number quoted in
chapters/03-attention-head-structure.qmd.
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

MIB = 2 ** 20
GIB = 2 ** 30


class TestAttentionHeadVariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = os.path.join(EXAMPLES_DIR, "attention_head_variants.py")
        subprocess.run([sys.executable, script], check=True, capture_output=True)
        with open(os.path.join(EXAMPLES_DIR, "attention_head_variants.json")) as f:
            cls.data = json.load(f)

    def test_result_file_exists_and_parses(self):
        self.assertIn("assumptions", self.data)
        self.assertIn("variants", self.data)
        for name in ("mha", "gqa", "mqa"):
            self.assertIn(name, self.data["variants"])

    def test_config_matches_chapter_prose(self):
        a = self.data["assumptions"]
        self.assertEqual(a["L"], 32)
        self.assertEqual(a["H_q"], 32)
        self.assertEqual(a["d_head"], 128)
        self.assertEqual(a["d_model"], 4096)
        self.assertEqual(a["S"], 8192)
        self.assertEqual(a["B_base"], 1)
        self.assertEqual(a["bytes_per_elem"], 2)

    def test_h_kv_values_for_each_variant(self):
        v = self.data["variants"]
        self.assertEqual(v["mha"]["H_kv"], 32)
        self.assertEqual(v["gqa"]["H_kv"], 8)
        self.assertEqual(v["mqa"]["H_kv"], 1)

    def test_group_size_divides_evenly(self):
        """Stage 3's simple equal-group presentation requires H_kv to
        divide H_q evenly for every variant in this chapter."""
        H_q = self.data["assumptions"]["H_q"]
        for name, v in self.data["variants"].items():
            with self.subTest(variant=name):
                self.assertEqual(H_q % v["H_kv"], 0, msg=f"{name}: H_q={H_q} not divisible by H_kv={v['H_kv']}")

    def test_kv_cache_formula_matches_manual_computation(self):
        """Independently recompute KV_bytes = 2*B*S*L*H_kv*d_head*bytes_per_elem
        for every variant, without trusting the script's own arithmetic."""
        a = self.data["assumptions"]
        for name, v in self.data["variants"].items():
            with self.subTest(variant=name):
                expected = 2 * a["B_base"] * a["S"] * a["L"] * v["H_kv"] * a["d_head"] * a["bytes_per_elem"]
                self.assertEqual(v["kv_cache_B1"]["bytes"], expected)

    def test_kv_cache_exact_values(self):
        v = self.data["variants"]
        self.assertEqual(v["mha"]["kv_cache_B1"]["bytes"], 4294967296)
        self.assertEqual(v["gqa"]["kv_cache_B1"]["bytes"], 1073741824)
        self.assertEqual(v["mqa"]["kv_cache_B1"]["bytes"], 134217728)

    def test_binary_unit_conversions(self):
        """1 MiB = 2^20 bytes, 1 GiB = 2^30 bytes -- verify the script's
        own unit conversions, not just trust its rounding."""
        v = self.data["variants"]
        self.assertAlmostEqual(v["mha"]["kv_cache_B1"]["bytes"] / MIB, v["mha"]["kv_cache_B1"]["mib"], places=3)
        self.assertAlmostEqual(v["mha"]["kv_cache_B1"]["bytes"] / GIB, v["mha"]["kv_cache_B1"]["gib"], places=3)
        self.assertEqual(v["mha"]["kv_cache_B1"]["gib"], 4.0)
        self.assertEqual(v["gqa"]["kv_cache_B1"]["gib"], 1.0)
        self.assertEqual(v["mqa"]["kv_cache_B1"]["mib"], 128.0)

    def test_cache_reduction_factors(self):
        v = self.data["variants"]
        self.assertAlmostEqual(v["mha"]["cache_reduction_vs_mha"], 1.0, places=6)
        self.assertAlmostEqual(v["gqa"]["cache_reduction_vs_mha"], 0.25, places=6)
        self.assertAlmostEqual(v["mqa"]["cache_reduction_vs_mha"], 1 / 32, places=6)

    def test_b16_concurrency_extension_scales_linearly(self):
        """The B=16 extension must be exactly 16x the B=1 result for
        every variant -- cache size is linear in B."""
        v = self.data["variants"]
        for name in ("mha", "gqa", "mqa"):
            with self.subTest(variant=name):
                self.assertEqual(v[name]["kv_cache_B16"]["bytes"], v[name]["kv_cache_B1"]["bytes"] * 16)

    def test_projection_parameter_formulas(self):
        """Independently recompute P_Q, P_K, P_V, P_O per @eq-attn-proj-params."""
        a = self.data["assumptions"]
        d_model, H_q, d_head = a["d_model"], a["H_q"], a["d_head"]
        for name, v in self.data["variants"].items():
            with self.subTest(variant=name):
                H_kv = v["H_kv"]
                self.assertEqual(v["P_Q"], d_model * H_q * d_head)
                self.assertEqual(v["P_K"], d_model * H_kv * d_head)
                self.assertEqual(v["P_V"], d_model * H_kv * d_head)
                self.assertEqual(v["P_O"], H_q * d_head * d_model)

    def test_q_and_o_projections_are_identical_across_variants(self):
        """P_Q and P_O must NOT depend on H_kv -- this is the chapter's
        central teaching point, checked as a hard invariant."""
        v = self.data["variants"]
        self.assertEqual(v["mha"]["P_Q"], v["gqa"]["P_Q"])
        self.assertEqual(v["mha"]["P_Q"], v["mqa"]["P_Q"])
        self.assertEqual(v["mha"]["P_O"], v["gqa"]["P_O"])
        self.assertEqual(v["mha"]["P_O"], v["mqa"]["P_O"])

    def test_kv_param_reduction_matches_cache_reduction(self):
        """K/V params and cache bytes both scale linearly in H_kv ONLY,
        so their reduction ratios vs. MHA must be identical."""
        v = self.data["variants"]
        for name in ("gqa", "mqa"):
            with self.subTest(variant=name):
                self.assertAlmostEqual(
                    v[name]["kv_param_reduction_vs_mha"], v[name]["cache_reduction_vs_mha"], places=6
                )

    def test_total_attn_param_reduction_is_less_extreme_than_kv_reduction(self):
        """The chapter's headline point: total attention-block params
        (Q+K+V+O) shrink by LESS than K/V alone, because P_Q/P_O don't
        change. This must hold strictly for both GQA and MQA."""
        v = self.data["variants"]
        for name in ("gqa", "mqa"):
            with self.subTest(variant=name):
                self.assertGreater(
                    v[name]["total_attn_param_reduction_vs_mha"],
                    v[name]["kv_param_reduction_vs_mha"],
                )

    def test_projection_parameter_exact_values(self):
        v = self.data["variants"]
        self.assertEqual(v["mha"]["total_attn_params_per_layer"], 67108864)
        self.assertEqual(v["gqa"]["total_attn_params_per_layer"], 41943040)
        self.assertEqual(v["mqa"]["total_attn_params_per_layer"], 34603008)

    def test_check_your_understanding_q7_instantiation(self):
        """Chapter 3's check-your-understanding Q7 (and answer-key Q7)
        asks about L=24, H_q=16 (MHA), d_head=128, S=4096, B=1, bf16 --
        verify that specific instantiation independently of the
        script's own default config."""
        B, S, L, H_kv, d_head, bytes_per_elem = 1, 4096, 24, 16, 128, 2
        result = 2 * B * S * L * H_kv * d_head * bytes_per_elem
        self.assertEqual(result, 805306368)
        self.assertAlmostEqual(result / MIB, 768.0, places=3)


class TestCh03LearnerFacingTextIsClean(unittest.TestCase):
    """Chapter-3-scoped version of the Chapters 1-2 cleanliness checks:
    no internal repo paths, no raw schema enum names, and humanized
    display labels are actually used."""

    CH03_FILES = [
        os.path.join(WB04, "chapters", "03-attention-head-structure.qmd"),
        os.path.join(WB04, "solutions", "03-attention-head-structure-solutions.qmd"),
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

    # Stage 14's specific unqualified-claim phrases to watch for; these
    # are substrings that would misrepresent the chapter's own careful
    # hedging if they appeared verbatim.
    UNQUALIFIED_CLAIM_PATTERNS = [
        r"\bexactly \d+x? times faster\b",
        r"\bexact GPU memory\b",
        r"\balways better\b",
        r"\bno quality loss\b",
        r"\buniversally (?:best|superior|better)\b(?!.*[Nn]ot)",
    ]

    def test_no_banned_substrings(self):
        for path in self.CH03_FILES:
            with open(path) as f:
                text = f.read()
            for banned in self.BANNED_SUBSTRINGS:
                self.assertNotIn(banned, text, msg=f"found banned substring {banned!r} in {os.path.relpath(path, REPO_ROOT)}")

    def test_display_labels_used_instead_of_raw_enum_names(self):
        display_labels = [
            "Quick check", "Explain", "Calculation", "Compare",
            "Misconception check", "Design exercise", "Interview practice",
        ]
        for path in self.CH03_FILES:
            with open(path) as f:
                text = f.read()
            self.assertTrue(
                any(label in text for label in display_labels),
                msg=f"no humanized display label found in {os.path.relpath(path, REPO_ROOT)}",
            )

    def test_no_unqualified_superiority_claims_in_chapter_prose(self):
        chapter_path = os.path.join(WB04, "chapters", "03-attention-head-structure.qmd")
        with open(chapter_path) as f:
            text = f.read()
        # "MQA is universally superior" appears only inside the
        # misconception callout that REJECTS the claim -- check the
        # sentence immediately following each hit states a correction
        # (contains "not" or "does not" nearby) rather than asserting it.
        for m in re.finditer(r"universally (?:best|superior|better)", text, re.IGNORECASE):
            window = text[max(0, m.start() - 200):m.end() + 300]
            self.assertTrue(
                re.search(r"\bnot\b|\bfalse\b|\bwithout claiming\b|\bnone (?:is|of)\b|\bno .{0,15} is\b", window, re.IGNORECASE),
                msg=f"unqualified superiority claim near: {window!r}",
            )

    def test_mla_not_substantially_taught_in_chapter_3(self):
        """Chapter 3 defers MLA per outline.yaml's ch3.drafting_note --
        MLA may be named as a forward reference but must not appear
        with its defining equation/mechanism keyword 'latent' more than
        a couple of times (a hard substantive-teaching proxy check)."""
        chapter_path = os.path.join(WB04, "chapters", "03-attention-head-structure.qmd")
        with open(chapter_path) as f:
            text = f.read()
        self.assertNotIn("MLA", text)
        self.assertNotIn("multi-head latent attention", text.lower())


class TestCh03CitationsAndFigures(unittest.TestCase):
    def test_all_citation_keys_used_in_ch03_resolve(self):
        bib_path = os.path.join(REPO_ROOT, "shared", "bibliography.bib")
        with open(bib_path) as f:
            bib_keys = set(re.findall(r"@\w+\{([^,]+),", f.read()))
        for fname in ("03-attention-head-structure.qmd",):
            path = os.path.join(WB04, "chapters", fname)
            with open(path) as f:
                text = f.read()
            used = set(re.findall(r"@(src-\d+)", text))
            self.assertGreater(len(used), 0, msg=f"{fname}: no citations found")
            for key in used:
                self.assertIn(key, bib_keys, msg=f"{fname} cites {key}, not found in bibliography.bib")

    def test_every_ch03_figure_reference_has_a_rendered_file(self):
        rendered_dir = os.path.join(WB04, "figures", "rendered")
        expected = [
            "fig-mha-mqa-gqa-head-sharing.svg",
            "fig-tensor-shape-gqa.svg",
            "fig-kv-cache-scaling.svg",
        ]
        for fname in expected:
            path = os.path.join(rendered_dir, fname)
            self.assertTrue(os.path.exists(path), msg=f"missing rendered figure: {fname}")

    def test_ch03_figure_source_scripts_exist(self):
        source_dir = os.path.join(WB04, "figures", "source")
        expected = [
            "fig_mha_mqa_gqa_head_sharing.py",
            "fig_tensor_shape_gqa.py",
            "fig_kv_cache_scaling.py",
        ]
        for fname in expected:
            path = os.path.join(source_dir, fname)
            self.assertTrue(os.path.exists(path), msg=f"missing figure source script: {fname}")

    def test_no_duplicate_figure_ids_in_ch03(self):
        chapters_dir = os.path.join(WB04, "chapters")
        path = os.path.join(chapters_dir, "03-attention-head-structure.qmd")
        with open(path) as f:
            text = f.read()
        ids = re.findall(r"\{#(fig-[a-z0-9-]+)", text)
        self.assertEqual(len(ids), len(set(ids)), msg=f"duplicate figure ids in {path}: {ids}")


class TestPageBudgetStructure(unittest.TestCase):
    def _load(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
        from _yaml_lite import safe_load_path  # noqa: E402
        return safe_load_path(os.path.join(WB04, "page-budget.yaml"))

    def test_page_budget_has_chapter_3_actuals(self):
        d = self._load()
        self.assertIn("pilot_actual", d)
        section_names = [s["name"] for s in d["pilot_actual"]["sections"]]
        self.assertIn("chapter_3", section_names)

    def test_page_budget_chapter_3_within_hard_ceiling(self):
        d = self._load()
        ch3 = next(s for s in d["pilot_actual"]["sections"] if s["name"] == "chapter_3")
        self.assertLessEqual(ch3["pages"], 8, msg="Chapter 3 instructional pages must stay within the 8-page hard maximum")

    def test_page_budget_total_pages_is_positive_int(self):
        d = self._load()
        self.assertIsInstance(d["pilot_actual"]["total_pages"], int)
        self.assertGreater(d["pilot_actual"]["total_pages"], 0)


if __name__ == "__main__":
    unittest.main()
