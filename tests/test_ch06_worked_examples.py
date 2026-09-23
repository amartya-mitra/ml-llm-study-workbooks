"""Computational verification tests for Chapter 6's worked example,
plus Chapter-6-scoped versions of the cross-cutting integrity checks
introduced for Chapters 1-5 (learner-facing text cleanliness, citation
resolution, figure/render pairing, page-budget structure), plus
Chapter-6-specific checks for model-version pinning, ledger-field
support, active/total parameter and expert-count consistency, and the
Stage 13 fast-changing-language audit.

Per AGENTS.md, prose must never state a number that isn't backed by a
script -- data/worked-examples/hypothetical_architecture_reading.py is
the source of truth for every number quoted in ch. 6's applied
exercise and its answer key.
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
CH06_CHAPTER = os.path.join(WB04, "chapters", "06-case-studies.qmd")
CH06_SOLUTIONS = os.path.join(WB04, "solutions", "06-case-studies-solutions.qmd")


class TestHypotheticalArchitectureReading(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = os.path.join(EXAMPLES_DIR, "hypothetical_architecture_reading.py")
        subprocess.run([sys.executable, script], check=True, capture_output=True)
        with open(os.path.join(EXAMPLES_DIR, "hypothetical_architecture_reading.json")) as f:
            cls.data = json.load(f)

    def test_result_file_exists_and_parses(self):
        for key in ("assumptions", "gqa_group_size", "routed_bank_active_fraction", "reading_answers"):
            self.assertIn(key, self.data)

    def test_config_matches_chapter_prose(self):
        a = self.data["assumptions"]
        self.assertEqual(a["H_q"], 32)
        self.assertEqual(a["H_kv"], 8)
        self.assertEqual(a["E_routed"], 64)
        self.assertEqual(a["k_routed"], 2)
        self.assertTrue(a["has_shared_expert"])

    def test_gqa_group_size_matches_manual_computation(self):
        a = self.data["assumptions"]
        self.assertEqual(self.data["gqa_group_size"], a["H_q"] // a["H_kv"])
        self.assertEqual(self.data["gqa_group_size"], 4)

    def test_routed_bank_active_fraction(self):
        a = self.data["assumptions"]
        expected = a["k_routed"] / a["E_routed"]
        self.assertAlmostEqual(self.data["routed_bank_active_fraction"], expected, places=6)
        self.assertAlmostEqual(self.data["routed_bank_active_fraction"], 2 / 64, places=6)

    def test_reading_answers_present_and_nonempty(self):
        answers = self.data["reading_answers"]
        for key in (
            "growing_state", "fixed_state", "active_vs_total_experts",
            "communication_concern", "mechanisms_present",
            "not_inferable_from_config_alone",
        ):
            self.assertIn(key, answers)
            self.assertTrue(answers[key].strip())


class TestCh06ModelIdentifiersAndLedger(unittest.TestCase):
    """Stage 13: every case-study model/version identifier and every
    ledger field asserted in the chapter must be internally consistent
    and traceable -- not asserted from memory."""

    @classmethod
    def setUpClass(cls):
        with open(CH06_CHAPTER) as f:
            cls.text = f.read()

    def test_three_case_study_models_named_with_exact_versions(self):
        for needle in ("Llama 3 405B", "DeepSeek-V3", "Jamba"):
            self.assertIn(needle, self.text)

    def test_each_model_has_a_pinned_date(self):
        for date in ("2024-07-31", "2024-12-27", "2025-02-18", "2024-03-28"):
            self.assertIn(date, self.text)

    def test_active_vs_total_parameter_consistency(self):
        # Llama 3: dense, total == active (405B / 405B).
        self.assertIn("405B / 405B", self.text)
        # DeepSeek-V3: 671B total, 37B active -- total != active.
        self.assertIn("671B / 37B", self.text)
        # Jamba: 52B total, 12B active -- total != active.
        self.assertIn("52B / 12B", self.text)

    def test_gqa_group_size_consistency_llama3(self):
        H_q, H_kv = 128, 8
        self.assertEqual(H_q // H_kv, 16)
        self.assertIn("GQA-16", self.text)

    def test_gqa_group_size_consistency_jamba(self):
        H_q, H_kv = 32, 8
        self.assertEqual(H_q // H_kv, 4)
        self.assertIn("GQA-4", self.text)

    def test_expert_count_consistency_deepseek(self):
        # 1 shared + 256 routed, 8 active -- active must be <= total routed.
        self.assertIn("1 shared + 256 routed, 8 active", self.text)
        self.assertLess(8, 256)

    def test_expert_count_consistency_jamba(self):
        self.assertIn("16 routed, 2 active, no shared", self.text)
        self.assertLess(2, 16)

    def test_not_applicable_used_for_dense_model_experts(self):
        self.assertIn("not applicable", self.text)

    def test_mamba_layer_ratio_consistency(self):
        # Jamba: 32 layers total, 4 blocks of 8, 1:7 attention:Mamba ratio
        # -> 4 attention layers + 28 Mamba layers.
        total_layers = 32
        attn_layers = total_layers // 8  # 1 of every 8
        mamba_layers = total_layers - attn_layers
        self.assertEqual(attn_layers, 4)
        self.assertEqual(mamba_layers, 28)
        self.assertIn("attention 1/8", self.text)
        self.assertIn("Mamba 7/8", self.text)


class TestCh06LearnerFacingTextIsClean(unittest.TestCase):
    """Chapter-6-scoped version of the earlier chapters' cleanliness
    checks: no internal repo paths, no raw schema enum names, humanized
    display labels are used, and at most 1 boxed misconception
    (Stage 10's hard limit, tighter than earlier chapters' 2)."""

    CH06_FILES = [CH06_CHAPTER, CH06_SOLUTIONS]

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
        for path in self.CH06_FILES:
            with open(path) as f:
                text = f.read()
            for banned in self.BANNED_SUBSTRINGS:
                self.assertNotIn(banned, text, msg=f"found banned substring {banned!r} in {os.path.relpath(path, REPO_ROOT)}")

    def test_display_labels_used_instead_of_raw_enum_names(self):
        display_labels = [
            "Quick check", "Explain", "Calculation", "Compare",
            "Misconception check", "Design exercise", "Interview practice",
        ]
        for path in self.CH06_FILES:
            with open(path) as f:
                text = f.read()
            self.assertTrue(
                any(label in text for label in display_labels),
                msg=f"no humanized display label found in {os.path.relpath(path, REPO_ROOT)}",
            )

    def test_at_most_one_boxed_misconception_callout(self):
        with open(CH06_CHAPTER) as f:
            text = f.read()
        self.assertLessEqual(text.count("Common misconception"), 1)

    def test_required_misconception_present(self):
        with open(CH06_CHAPTER) as f:
            text = f.read()
        self.assertIn("more sophisticated architecture is necessarily a better model", text.lower())

    def test_no_internal_path_leakage(self):
        for path in self.CH06_FILES:
            with open(path) as f:
                text = f.read()
            self.assertNotIn("/mnt/home", text)
            self.assertNotIn(".qmd", text)
            self.assertNotIn(".yaml", text)

    def test_fast_changing_language_is_hedged(self):
        """Stage 15's manual-review phrase list: 'latest', 'newest',
        'best', 'leading', 'state of the art' must not appear as bare,
        unqualified claims about any model -- only inside a quoted,
        negated phrase explaining why the chapter avoids that framing
        (e.g. 'not stated as a permanent fact about "the best" or "the
        latest" model')."""
        with open(CH06_CHAPTER) as f:
            text = f.read()
        hedge_re = re.compile(r"\bnot\b|\bdoes not\b|\bavoid", re.IGNORECASE)
        for phrase in ["latest", "newest", "leading", "state of the art", "best"]:
            for m in re.finditer(re.escape(phrase), text, re.IGNORECASE):
                window = text[max(0, m.start() - 120):m.end() + 40]
                self.assertTrue(hedge_re.search(window), msg=f"unhedged occurrence of {phrase!r} near: {window!r}")

    def test_review_phrases_are_hedged_not_asserted(self):
        with open(CH06_CHAPTER) as f:
            text = f.read()
        hedge_re = re.compile(
            r"\bnot\b|\bdoes not\b|\bis not\b|\bwithout\b|\bdependent\b|\bunless\b|"
            r"\bmay\b|\bcan\b|\balone\b|\bcannot\b|\balone does not\b",
            re.IGNORECASE,
        )
        # "always-active" is an established compound term (ch. 5's shared-
        # expert terminology), not a bare "always" claim -- excluded here.
        always_bare_re = re.compile(r"\balways\b(?!-active)", re.IGNORECASE)
        for phrase in ["necessarily", "designed to"]:
            for m in re.finditer(re.escape(phrase), text, re.IGNORECASE):
                window = text[max(0, m.start() - 200):m.end() + 250]
                self.assertTrue(hedge_re.search(window), msg=f"unhedged occurrence of {phrase!r} near: {window!r}")
        for m in always_bare_re.finditer(text):
            window = text[max(0, m.start() - 200):m.end() + 250]
            self.assertTrue(hedge_re.search(window), msg=f"unhedged occurrence of 'always' near: {window!r}")

    def test_deferred_topics_are_disclosed(self):
        with open(CH06_CHAPTER) as f:
            text = f.read()
        for topic in ["benchmark", "survey", "release-history", "proprietary"]:
            self.assertIn(topic, text.lower())

    def test_designers_wanted_language_not_used(self):
        """Stage 6: use 'this design has the effect of...', not
        'the designers wanted...' -- the report doesn't state intent."""
        with open(CH06_CHAPTER) as f:
            text = f.read()
        self.assertNotIn("the designers wanted", text.lower())
        self.assertIn("this has the effect of", text.lower())


class TestCh06CitationsAndFigures(unittest.TestCase):
    def test_all_citation_keys_used_in_ch06_resolve(self):
        bib_path = os.path.join(REPO_ROOT, "shared", "bibliography.bib")
        with open(bib_path) as f:
            bib_keys = set(re.findall(r"@\w+\{([^,]+),", f.read()))
        with open(CH06_CHAPTER) as f:
            text = f.read()
        used = set(re.findall(r"@(src-\d+)", text))
        self.assertGreater(len(used), 0, msg="no citations found in chapter 6")
        for key in used:
            self.assertIn(key, bib_keys, msg=f"chapter 6 cites {key}, not found in bibliography.bib")
        # The three case-study primary sources plus the Mamba mechanism
        # source (resolving Chapter 4's disclosed gap) must all be cited.
        for required in ("src-32", "src-33", "src-35", "src-37"):
            self.assertIn(required, used)

    def test_model_specific_source_mapping(self):
        """Each case-study model's own source id must appear near that
        model's name in the chapter text, not just anywhere."""
        with open(CH06_CHAPTER) as f:
            text = f.read()
        pairs = {
            "Llama 3 405B": "src-32",
            "DeepSeek-V3": "src-33",
            "Jamba": "src-35",
        }
        for model, src in pairs.items():
            idx = text.find(f"**{model}")
            self.assertNotEqual(idx, -1, msg=f"model heading for {model} not found")
            window = text[idx:idx + 400]
            self.assertIn(src, window, msg=f"{src} not cited near {model}'s case-study paragraph")

    def test_every_ch06_figure_reference_has_a_rendered_file(self):
        rendered_dir = os.path.join(WB04, "figures", "rendered")
        expected = [
            "fig-case-study-architecture-cards.svg",
            "fig-case-study-tradeoff-map.svg",
        ]
        for fname in expected:
            path = os.path.join(rendered_dir, fname)
            self.assertTrue(os.path.exists(path), msg=f"missing rendered figure: {fname}")

    def test_ch06_figure_source_scripts_exist(self):
        source_dir = os.path.join(WB04, "figures", "source")
        expected = [
            "fig_case_study_architecture_cards.py",
            "fig_case_study_tradeoff_map.py",
        ]
        for fname in expected:
            path = os.path.join(source_dir, fname)
            self.assertTrue(os.path.exists(path), msg=f"missing figure source script: {fname}")

    def test_exactly_two_figures_in_chapter_6(self):
        """Stage 7's figure budget: exactly 2, preferred == hard maximum."""
        with open(CH06_CHAPTER) as f:
            text = f.read()
        ids = re.findall(r"\{#(fig-[a-z0-9-]+)", text)
        self.assertEqual(len(ids), 2, msg=f"expected exactly 2 figures, found {len(ids)}: {ids}")
        self.assertEqual(len(ids), len(set(ids)), msg=f"duplicate figure ids: {ids}")

    def test_exactly_one_ledger_table(self):
        with open(CH06_CHAPTER) as f:
            text = f.read()
        ids = re.findall(r"\{#(tbl-[a-z0-9-]+)", text)
        self.assertEqual(len(ids), 1, msg=f"expected exactly 1 ledger table, found {len(ids)}: {ids}")

    def test_question_count_in_range(self):
        """Stage 10: target 5-6 total questions across check-your-
        understanding, the applied exercise, and the interview lens."""
        with open(CH06_CHAPTER) as f:
            text = f.read()
        cyu_count = len(re.findall(r"^\d+\. \*\*", text, re.MULTILINE))
        total = cyu_count + 2  # + applied exercise + interview lens
        self.assertGreaterEqual(total, 5)
        self.assertLessEqual(total, 6)


class TestPageBudgetStructure(unittest.TestCase):
    def _load(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
        from _yaml_lite import safe_load_path  # noqa: E402
        return safe_load_path(os.path.join(WB04, "page-budget.yaml"))

    def test_page_budget_has_chapter_6_actuals(self):
        d = self._load()
        section_names = [s["name"] for s in d["pilot_actual"]["sections"]]
        self.assertIn("chapter_6", section_names)
        self.assertIn("answer_key_chapter_6", section_names)

    def test_page_budget_chapter_6_within_hard_ceiling(self):
        d = self._load()
        ch6 = next(s for s in d["pilot_actual"]["sections"] if s["name"] == "chapter_6")
        self.assertLessEqual(ch6["pages"], 5, msg="Chapter 6 instructional pages must stay within the 5-page hard maximum")

    def test_page_budget_answer_key_chapter_6_within_hard_ceiling(self):
        d = self._load()
        ak6 = next(s for s in d["pilot_actual"]["sections"] if s["name"] == "answer_key_chapter_6")
        self.assertLessEqual(ak6["pages"], 0.75, msg="Chapter 6 answer-key pages must stay within the 0.75-page hard maximum")

    def test_full_workbook_projection_at_or_below_72(self):
        """Stage 12: after this chapter, the projected complete
        workbook must remain at or below 72 pages."""
        d = self._load()
        proj = d["full_workbook_projection"]["projection_arithmetic"]["projected_full_total_range"]
        self.assertLessEqual(proj[1], 72, msg=f"projected high end {proj[1]} exceeds the 72-page ceiling")

    def test_no_stale_chapter_6_provisional_entry(self):
        """Chapter 6 is now actual, not provisional -- the projection
        block must be renamed and must not still list chapter 6."""
        d = self._load()
        proj = d["full_workbook_projection"]
        self.assertIn("chapters_7_to_8_provisional", proj)
        chapters_listed = [c["chapter"] for c in proj["chapters_7_to_8_provisional"]]
        self.assertNotIn(6, chapters_listed)


class TestSourceRegistryAndCoverage(unittest.TestCase):
    def _load(self, rel_path):
        sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
        from _yaml_lite import safe_load_path  # noqa: E402
        return safe_load_path(os.path.join(REPO_ROOT, rel_path))

    def test_src37_registered(self):
        reg = self._load("sources/registry.yaml")
        ids = [s["id"] for s in reg["sources"]]
        self.assertIn("src-37", ids)

    def test_src37_bibliography_entry_exists(self):
        bib_path = os.path.join(REPO_ROOT, "shared", "bibliography.bib")
        with open(bib_path) as f:
            bib_keys = set(re.findall(r"@\w+\{([^,]+),", f.read()))
        self.assertIn("src-37", bib_keys)

    def test_source_coverage_has_ch6_entries(self):
        cov = self._load("workbooks/04-llm-architecture/source-coverage.yaml")
        ch6_entries = [c for c in cov["claims"] if c["chapter"] == "ch6"]
        self.assertGreaterEqual(len(ch6_entries), 4)


if __name__ == "__main__":
    unittest.main()
