"""Computational verification tests for Chapter 4's worked examples,
plus Chapter-4-scoped versions of the cross-cutting integrity checks
introduced for Chapters 1-3 (learner-facing text cleanliness, citation
resolution, figure/render pairing, page-budget structure).

Per AGENTS.md, prose must never state a number that isn't backed by a
script -- data/worked-examples/gqa_vs_mla_cache.py and
sliding_window_receptive_field.py are the source of truth for every
number quoted in chapters/04-reducing-attention-cost.qmd.
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


class TestGqaVsMlaCache(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = os.path.join(EXAMPLES_DIR, "gqa_vs_mla_cache.py")
        subprocess.run([sys.executable, script], check=True, capture_output=True)
        with open(os.path.join(EXAMPLES_DIR, "gqa_vs_mla_cache.json")) as f:
            cls.data = json.load(f)

    def test_result_file_exists_and_parses(self):
        for key in ("assumptions", "gqa", "mha_reference", "mla", "ratios", "caveats"):
            self.assertIn(key, self.data)

    def test_config_matches_chapter_3_base_config(self):
        a = self.data["assumptions"]
        self.assertEqual(a["L"], 32)
        self.assertEqual(a["H_q"], 32)
        self.assertEqual(a["d_head"], 128)
        self.assertEqual(a["d_model"], 4096)
        self.assertEqual(a["S"], 8192)
        self.assertEqual(a["B"], 1)
        self.assertEqual(a["bytes_per_elem"], 2)

    def test_gqa_cache_matches_chapter_3(self):
        """GQA at H_kv=8 on this config must reproduce Chapter 3's own
        1 GiB result exactly -- this is a continuity check, not just an
        internal consistency check."""
        self.assertEqual(self.data["gqa"]["H_kv"], 8)
        self.assertEqual(self.data["gqa"]["cache_per_sequence"]["bytes"], 1073741824)
        self.assertEqual(self.data["gqa"]["cache_per_sequence"]["gib"], 1.0)

    def test_mha_reference_matches_chapter_3(self):
        self.assertEqual(self.data["mha_reference"]["cache_per_sequence"]["bytes"], 4294967296)
        self.assertEqual(self.data["mha_reference"]["cache_per_sequence"]["gib"], 4.0)

    def test_mla_dimensions_follow_deepseek_v2_ratio(self):
        """Per [@src-27] Table 1's caption: d_c = 4*d_head, d_rope = 0.5*d_head."""
        d_head = self.data["assumptions"]["d_head"]
        self.assertEqual(self.data["mla"]["d_c"], 4 * d_head)
        self.assertEqual(self.data["mla"]["d_rope"], round(0.5 * d_head))

    def test_mla_cache_formula_matches_manual_computation(self):
        a = self.data["assumptions"]
        mla = self.data["mla"]
        expected = a["B"] * a["S"] * a["L"] * (mla["d_c"] + mla["d_rope"]) * a["bytes_per_elem"]
        self.assertEqual(mla["cache_per_sequence"]["bytes"], expected)

    def test_mla_cache_exact_value(self):
        self.assertEqual(self.data["mla"]["cache_per_sequence"]["bytes"], 301989888)
        self.assertEqual(self.data["mla"]["cache_per_sequence"]["mib"], 288.0)

    def test_mla_equals_gqa_at_2_25_groups(self):
        """[@src-27]'s own stated equivalence for its reported ratio,
        checked as a hard invariant: (d_c+d_rope) == 2 * 2.25 * d_head."""
        self.assertAlmostEqual(self.data["mla"]["equivalent_gqa_groups"], 2.25, places=4)
        d_head = self.data["assumptions"]["d_head"]
        mla = self.data["mla"]
        self.assertAlmostEqual((mla["d_c"] + mla["d_rope"]) / (2 * d_head), 2.25, places=6)

    def test_binary_unit_conversions(self):
        mla_bytes = self.data["mla"]["cache_per_sequence"]["bytes"]
        self.assertAlmostEqual(mla_bytes / MIB, self.data["mla"]["cache_per_sequence"]["mib"], places=3)

    def test_ratios(self):
        r = self.data["ratios"]
        self.assertAlmostEqual(r["mla_vs_gqa"], 301989888 / 1073741824, places=4)
        self.assertAlmostEqual(r["mla_vs_mha"], 301989888 / 4294967296, places=4)
        self.assertAlmostEqual(r["gqa_vs_mha"], 0.25, places=6)

    def test_caveats_present(self):
        text = " ".join(self.data["caveats"]).lower()
        self.assertIn("latency", text)
        self.assertIn("quality", text)
        self.assertIn("overhead", text)

    def test_check_your_understanding_q6_instantiation(self):
        """Chapter 4's check-your-understanding Q6 (and answer-key Q6)
        asks about L=24, H_q=16, d_head=128, GQA H_kv=4 -- verify that
        specific instantiation independently of the script's default
        config."""
        L, d_head = 24, 128
        d_c, d_rope = 4 * d_head, round(0.5 * d_head)
        mla_elems = (d_c + d_rope) * L
        H_kv = 4
        gqa_elems = 2 * H_kv * d_head * L
        self.assertEqual(mla_elems, 13824)
        self.assertEqual(gqa_elems, 24576)
        self.assertAlmostEqual(mla_elems / gqa_elems, 0.5625, places=4)


class TestSlidingWindowReceptiveField(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = os.path.join(EXAMPLES_DIR, "sliding_window_receptive_field.py")
        subprocess.run([sys.executable, script], check=True, capture_output=True)
        with open(os.path.join(EXAMPLES_DIR, "sliding_window_receptive_field.json")) as f:
            cls.data = json.load(f)

    def test_result_file_exists_and_parses(self):
        self.assertIn("toy_example", self.data)

    def test_receptive_field_values(self):
        t = self.data["toy_example"]
        self.assertEqual(t["1"]["effective_receptive_field"], 4)
        self.assertEqual(t["2"]["effective_receptive_field"], 8)
        self.assertEqual(t["3"]["effective_receptive_field"], 12)

    def test_formula_matches_manual_computation(self):
        t = self.data["toy_example"]
        for key, entry in t.items():
            with self.subTest(layers=key):
                self.assertEqual(entry["effective_receptive_field"], entry["window_w"] * entry["num_layers"])


class TestCh04LearnerFacingTextIsClean(unittest.TestCase):
    """Chapter-4-scoped version of the earlier chapters' cleanliness
    checks: no internal repo paths, no raw schema enum names, and
    humanized display labels are actually used."""

    CH04_FILES = [
        os.path.join(WB04, "chapters", "04-reducing-attention-cost.qmd"),
        os.path.join(WB04, "solutions", "04-reducing-attention-cost-solutions.qmd"),
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
        for path in self.CH04_FILES:
            with open(path) as f:
                text = f.read()
            for banned in self.BANNED_SUBSTRINGS:
                self.assertNotIn(banned, text, msg=f"found banned substring {banned!r} in {os.path.relpath(path, REPO_ROOT)}")

    def test_display_labels_used_instead_of_raw_enum_names(self):
        display_labels = [
            "Quick check", "Explain", "Calculation", "Compare",
            "Misconception check", "Design exercise", "Interview practice",
        ]
        for path in self.CH04_FILES:
            with open(path) as f:
                text = f.read()
            self.assertTrue(
                any(label in text for label in display_labels),
                msg=f"no humanized display label found in {os.path.relpath(path, REPO_ROOT)}",
            )

    def test_at_most_two_boxed_misconception_callouts(self):
        chapter_path = os.path.join(WB04, "chapters", "04-reducing-attention-cost.qmd")
        with open(chapter_path) as f:
            text = f.read()
        self.assertLessEqual(text.count("Common misconception"), 2)

    def test_review_phrases_are_hedged_not_asserted(self):
        """Stage 14's manual-review phrase list: each occurrence in the
        chapter must appear inside a negation/hedge, not as a bare
        unqualified claim."""
        chapter_path = os.path.join(WB04, "chapters", "04-reducing-attention-cost.qmd")
        with open(chapter_path) as f:
            text = f.read()
        hedge_re = re.compile(r"\bnot\b|\bdoes not\b|\bis not\b|\bwithout\b|\bmay\b|\bpattern-dependent\b|\bavailable\b|\bimplementation-dependent\b", re.IGNORECASE)
        for phrase in ["guarantees", "no quality loss", "reconstructs full k/v", "cannot access older tokens"]:
            for m in re.finditer(re.escape(phrase), text, re.IGNORECASE):
                window = text[max(0, m.start() - 250):m.end() + 250]
                self.assertTrue(hedge_re.search(window), msg=f"unhedged occurrence of {phrase!r} near: {window!r}")

    def test_mla_is_taught_here_unlike_chapter_3(self):
        chapter_path = os.path.join(WB04, "chapters", "04-reducing-attention-cost.qmd")
        with open(chapter_path) as f:
            text = f.read()
        self.assertIn("MLA", text)
        self.assertIn("latent", text.lower())

    def test_recurrent_family_kept_taxonomic(self):
        """Chapter 4 must name recurrent/SSM/linear-attention as a
        family without teaching mechanics -- no equation ids for it
        and an explicit disclosed sourcing gap statement."""
        chapter_path = os.path.join(WB04, "chapters", "04-reducing-attention-cost.qmd")
        with open(chapter_path) as f:
            text = f.read()
        self.assertIn("without a primary source for its mechanics", text.lower())


class TestCh04CitationsAndFigures(unittest.TestCase):
    def test_all_citation_keys_used_in_ch04_resolve(self):
        bib_path = os.path.join(REPO_ROOT, "shared", "bibliography.bib")
        with open(bib_path) as f:
            bib_keys = set(re.findall(r"@\w+\{([^,]+),", f.read()))
        path = os.path.join(WB04, "chapters", "04-reducing-attention-cost.qmd")
        with open(path) as f:
            text = f.read()
        used = set(re.findall(r"@(src-\d+)", text))
        self.assertGreater(len(used), 0, msg="no citations found in chapter 4")
        for key in used:
            self.assertIn(key, bib_keys, msg=f"chapter 4 cites {key}, not found in bibliography.bib")
        # src-27 (DeepSeek-V2/MLA) must be cited, per Stage 12.
        self.assertIn("src-27", used)

    def test_every_ch04_figure_reference_has_a_rendered_file(self):
        rendered_dir = os.path.join(WB04, "figures", "rendered")
        expected = [
            "fig-three-efficiency-strategies.svg",
            "fig-sliding-window-receptive-field.svg",
            "fig-mla-cache-pathway.svg",
        ]
        for fname in expected:
            path = os.path.join(rendered_dir, fname)
            self.assertTrue(os.path.exists(path), msg=f"missing rendered figure: {fname}")

    def test_ch04_figure_source_scripts_exist(self):
        source_dir = os.path.join(WB04, "figures", "source")
        expected = [
            "fig_three_efficiency_strategies.py",
            "fig_sliding_window_receptive_field.py",
            "fig_mla_cache_pathway.py",
        ]
        for fname in expected:
            path = os.path.join(source_dir, fname)
            self.assertTrue(os.path.exists(path), msg=f"missing figure source script: {fname}")

    def test_exactly_three_figures_in_chapter_4(self):
        """Stage 9's figure budget: exactly 3, hard maximum 3."""
        chapter_path = os.path.join(WB04, "chapters", "04-reducing-attention-cost.qmd")
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

    def test_page_budget_has_chapter_4_actuals(self):
        d = self._load()
        section_names = [s["name"] for s in d["pilot_actual"]["sections"]]
        self.assertIn("chapter_4", section_names)

    def test_page_budget_chapter_4_within_hard_ceiling(self):
        d = self._load()
        ch4 = next(s for s in d["pilot_actual"]["sections"] if s["name"] == "chapter_4")
        self.assertLessEqual(ch4["pages"], 7, msg="Chapter 4 instructional pages must stay within the 7-page hard maximum")

    def test_full_workbook_projection_at_or_below_72(self):
        """Stage 13: after this chapter, the projected complete
        workbook must remain at or below 72 pages."""
        d = self._load()
        proj = d["full_workbook_projection"]["projection_arithmetic"]["projected_full_total_range"]
        self.assertLessEqual(proj[1], 72, msg=f"projected high end {proj[1]} exceeds the 72-page ceiling")


if __name__ == "__main__":
    unittest.main()
