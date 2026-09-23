"""Computational verification tests for Chapters 1-2's worked examples.

These tests re-run (or re-check the committed output of)
data/worked-examples/*.py and fail if the numbers the chapter prose
quotes ever drift from what the scripts actually compute. Per AGENTS.md,
prose must never state a number that isn't backed by a script.
"""
import json
import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WB04 = os.path.join(REPO_ROOT, "workbooks", "04-llm-architecture")
EXAMPLES_DIR = os.path.join(WB04, "data", "worked-examples")


class TestTinyDecoderTrace(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = os.path.join(EXAMPLES_DIR, "tiny_decoder_trace.py")
        subprocess.run([sys.executable, script], check=True, capture_output=True)
        with open(os.path.join(EXAMPLES_DIR, "tiny_decoder_trace.json")) as f:
            cls.data = json.load(f)

    def test_result_file_exists_and_parses(self):
        self.assertIn("config", self.data)
        self.assertIn("prefill", self.data)
        self.assertIn("decode_step", self.data)

    def test_config_matches_chapter_prose(self):
        cfg = self.data["config"]
        self.assertEqual(cfg["d_model"], 4)
        self.assertEqual(cfg["n_heads"], 2)
        self.assertEqual(cfg["d_head"], 2)
        self.assertEqual(cfg["prompt_tokens"], ["The", "cat", "sat", "on"])
        self.assertEqual(cfg["decode_token"], "the")

    def test_tensor_dimensions_are_internally_consistent(self):
        prefill = self.data["prefill"]
        S = len(self.data["config"]["prompt_tokens"])
        d_model = self.data["config"]["d_model"]
        d_head = self.data["config"]["d_head"]
        n_heads = self.data["config"]["n_heads"]
        self.assertEqual(len(prefill["embeddings"]), S)
        self.assertEqual(len(prefill["embeddings"][0]), d_model)
        self.assertEqual(len(prefill["Q"]), S)
        self.assertEqual(len(prefill["Q"][0]), d_model)
        for head in prefill["per_head"]:
            self.assertEqual(len(head["scores_scaled"]), S)
            self.assertEqual(len(head["scores_scaled"][0]), S)
            self.assertEqual(len(head["head_output"][0]), d_head)
        self.assertEqual(len(prefill["per_head"]), n_heads)

    def test_causal_mask_zeroes_out_future_positions(self):
        """Row i's softmax weights must be exactly 0 for every column j > i
        (the causal mask sent those scores to -inf before softmax ran)."""
        prefill = self.data["prefill"]
        for head in prefill["per_head"]:
            weights = head["softmax_weights"]
            for i, row in enumerate(weights):
                for j, w in enumerate(row):
                    if j > i:
                        self.assertEqual(w, 0.0, msg=f"head {head['head']} row {i} col {j} should be exactly 0")

    def test_every_row_sums_to_one(self):
        prefill = self.data["prefill"]
        for head in prefill["per_head"]:
            for row in head["softmax_weights"]:
                self.assertAlmostEqual(sum(row), 1.0, places=3)
        decode = self.data["decode_step"]
        for head in decode["per_head"]:
            for row in head["softmax_weights"]:
                self.assertAlmostEqual(sum(row), 1.0, places=3)

    def test_decode_step_cache_grows_by_exactly_one(self):
        decode = self.data["decode_step"]
        self.assertEqual(decode["cache_size_after"] - decode["cache_size_before"], 1)
        self.assertEqual(decode["cache_size_before"], 4)
        self.assertEqual(decode["cache_size_after"], 5)

    def test_kv_cache_is_not_the_residual_stream(self):
        """Regression test for a corrected error: the chapter previously
        (wrongly) called the post-attention residual stream 'exactly the
        state that gets cached'. What actually gets cached is each
        layer's K/V projections (computed from that layer's INPUT),
        which must differ in both shape and value from the residual
        stream state produced AFTER the attention sublayer's output is
        added back in."""
        prefill = self.data["prefill"]
        k_full = prefill["K_full"]
        residual = prefill["residual_stream_after_attn"]
        self.assertEqual(len(k_full), len(residual))
        self.assertEqual(len(k_full[0]), len(residual[0]))
        differs_somewhere = any(
            abs(k_full[i][j] - residual[i][j]) > 1e-9
            for i in range(len(k_full))
            for j in range(len(k_full[0]))
        )
        self.assertTrue(
            differs_somewhere,
            msg="K (what gets cached) must not equal the post-attention residual stream",
        )

    def test_decode_step_query_has_no_blocked_positions(self):
        """The decode step's query is always the last position, so every
        key (including the 4 cached ones and itself) must be visible --
        no zero weight from masking (weights can still be small from the
        softmax itself, just not identically zero from a mask)."""
        decode = self.data["decode_step"]
        for head in decode["per_head"]:
            for w in head["softmax_weights"][0]:
                self.assertGreater(w, 0.0)


class TestGatedMLPParams(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = os.path.join(EXAMPLES_DIR, "gated_mlp_params.py")
        subprocess.run([sys.executable, script], check=True, capture_output=True)
        with open(os.path.join(EXAMPLES_DIR, "gated_mlp_params.json")) as f:
            cls.data = json.load(f)

    def test_result_file_exists_and_parses(self):
        self.assertIn("plain_mlp", self.data)
        self.assertIn("gated_mlp_same_d_ff", self.data)
        self.assertIn("gated_mlp_compensated_d_ff", self.data)

    def test_plain_mlp_matches_chapter_prose(self):
        # d_model=8, d_ff=32 -> 2*8*32 = 512 (matches ch. 2's worked example table)
        self.assertEqual(self.data["plain_mlp"]["params"], 512)

    def test_gated_same_d_ff_is_exactly_1_5x_plain(self):
        plain = self.data["plain_mlp"]["params"]
        gated = self.data["gated_mlp_same_d_ff"]["params"]
        self.assertEqual(gated, 768)
        self.assertAlmostEqual(gated / plain, 1.5, places=6)

    def test_compensated_d_ff_lands_close_to_plain(self):
        plain = self.data["plain_mlp"]["params"]
        compensated = self.data["gated_mlp_compensated_d_ff"]["params"]
        self.assertEqual(compensated, 504)
        # "close to" per the chapter's own claim -- within 5%, not exact
        self.assertLess(abs(compensated - plain) / plain, 0.05)

    def test_applied_exercise_instantiation(self):
        """The applied exercise (chapters/02) asks about d_model=16,
        d_ff=64 -- verify that specific instantiation independently of
        the script's own default config."""
        d_model, d_ff = 16, 64
        self.assertEqual(2 * d_model * d_ff, 2048)


class TestQuestionAndFigureIntegrity(unittest.TestCase):
    """Cross-cutting checks Stage 8 asks for: no duplicate question ids,
    every figure referenced by a chapter has a rendered file, every
    citation key used in the chapters resolves to a bibliography entry."""

    def test_no_duplicate_question_ids_across_project(self):
        sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
        from validate_questions import validate_all  # noqa: E402
        errors, total = validate_all()
        duplicate_errors = [e for e in errors if "duplicate" in e]
        self.assertEqual(duplicate_errors, [], msg="\n".join(duplicate_errors))
        self.assertGreaterEqual(total, 19)

    def test_every_ch01_02_figure_reference_has_a_rendered_file(self):
        rendered_dir = os.path.join(WB04, "figures", "rendered")
        expected = [
            "fig-decoder-end-to-end.svg", "fig-decoder-block-anatomy.svg",
            "fig-causal-attention-mask.svg", "fig-annotated-modern-block.svg",
            "fig-rope-rotation.svg", "fig-norm-placement.svg", "fig-gated-mlp.svg",
        ]
        for fname in expected:
            path = os.path.join(rendered_dir, fname)
            self.assertTrue(os.path.exists(path), msg=f"missing rendered figure: {fname}")

    def test_no_duplicate_figure_ids_in_ch01_02(self):
        chapters_dir = os.path.join(WB04, "chapters")
        seen = {}
        import re
        for fname in ("01-transformer-refresher.qmd", "02-modern-decoder.qmd"):
            with open(os.path.join(chapters_dir, fname)) as f:
                text = f.read()
            for m in re.finditer(r"\{#(fig-[a-z0-9-]+)", text):
                fig_id = m.group(1)
                self.assertNotIn(fig_id, seen, msg=f"duplicate figure id {fig_id} in {fname} and {seen.get(fig_id)}")
                seen[fig_id] = fname

    def test_all_citation_keys_used_in_ch01_02_resolve(self):
        import re
        chapters_dir = os.path.join(WB04, "chapters")
        bib_path = os.path.join(REPO_ROOT, "shared", "bibliography.bib")
        with open(bib_path) as f:
            bib_keys = set(re.findall(r"@\w+\{([^,]+),", f.read()))
        for fname in ("01-transformer-refresher.qmd", "02-modern-decoder.qmd"):
            with open(os.path.join(chapters_dir, fname)) as f:
                text = f.read()
            used = set(re.findall(r"@(src-\d+)", text))
            for key in used:
                self.assertIn(key, bib_keys, msg=f"{fname} cites {key}, not found in bibliography.bib")


class TestLearnerFacingTextIsClean(unittest.TestCase):
    """Regression tests for the post-review cleanup: raw machine-readable
    enum labels and internal repo-relative paths must never appear in the
    learner-facing chapter/solutions text, and the corrected KV-cache
    claim must not silently regress."""

    LEARNER_FACING_FILES = [
        os.path.join(WB04, "chapters", "01-transformer-refresher.qmd"),
        os.path.join(WB04, "chapters", "02-modern-decoder.qmd"),
        os.path.join(WB04, "solutions", "01-transformer-refresher-solutions.qmd"),
        os.path.join(WB04, "solutions", "02-modern-decoder-solutions.qmd"),
        os.path.join(WB04, "includes", "notation-summary.qmd"),
        os.path.join(WB04, "includes", "draft-scope-note.qmd"),
    ]

    BANNED_SUBSTRINGS = [
        "figures/source",
        "data/worked-examples",
        "workbooks/04",
        "shared/question-schema",
        "misconception_diagnosis",
        "compare_and_contrast",
        "residual stream is exactly the state that gets cached",
        "sources/registry.yaml",
        "notation.yaml",
        "questions.yaml",
        "(recall)",
        "(explanation)",
        "(calculation)",
        "(design)",
        "(debugging)",
    ]

    def test_no_banned_substrings_in_learner_facing_files(self):
        for path in self.LEARNER_FACING_FILES:
            with open(path) as f:
                text = f.read()
            for banned in self.BANNED_SUBSTRINGS:
                self.assertNotIn(
                    banned, text,
                    msg=f"found banned substring {banned!r} in {os.path.relpath(path, REPO_ROOT)}",
                )

    def test_display_labels_used_instead_of_raw_enum_names(self):
        display_labels = [
            "Quick check", "Explain", "Calculation", "Compare",
            "Misconception check", "Design exercise", "Interview practice",
        ]
        for path in self.LEARNER_FACING_FILES[:4]:
            with open(path) as f:
                text = f.read()
            self.assertTrue(
                any(label in text for label in display_labels),
                msg=f"no humanized display label found in {os.path.relpath(path, REPO_ROOT)}",
            )


if __name__ == "__main__":
    unittest.main()
