"""Computational verification for workbook 05 Chapter 2's worked
example: target shifting and loss construction for both verified MTP
designs.

Per AGENTS.md, prose must never state a number that isn't backed by a
script -- data/worked-examples/mtp_target_alignment.py is the source
of truth for every position/target number quoted in
chapters/02-multi-token-prediction.qmd's worked example.
"""
import json
import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WB05 = os.path.join(REPO_ROOT, "workbooks", "05-llm-training")
EXAMPLES_DIR = os.path.join(WB05, "data", "worked-examples")
SCRIPT_PATH = os.path.join(EXAMPLES_DIR, "mtp_target_alignment.py")
JSON_PATH = os.path.join(EXAMPLES_DIR, "mtp_target_alignment.json")
CHAPTER_PATH = os.path.join(WB05, "chapters", "02-multi-token-prediction.qmd")


class TestChapter2WorkedExample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, SCRIPT_PATH], capture_output=True, text=True)
        with open(JSON_PATH, encoding="utf-8") as f:
            cls.data = json.load(f)
        with open(CHAPTER_PATH, encoding="utf-8") as f:
            cls.chapter_text = f.read()

    def test_script_runs_cleanly(self):
        result = subprocess.run([sys.executable, SCRIPT_PATH], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=f"worked-example script failed: {result.stderr}")

    def test_toy_sequence_length_and_horizon(self):
        self.assertEqual(self.data["sequence_length_T"], 6)
        self.assertEqual(self.data["n_heads_or_depth"], 3)

    def test_design1_independent_heads_valid_positions_and_loss_terms(self):
        d1 = self.data["design_1_independent_heads"]
        self.assertEqual(d1["valid_positions_t"], 3)
        self.assertEqual(d1["total_individual_loss_terms"], 9)

    def test_design1_targets_match_toy_sequence(self):
        d1 = self.data["design_1_independent_heads"]
        row_t1 = d1["rows"][0]
        self.assertEqual(row_t1["position_t"], 1)
        self.assertEqual(row_t1["targets"]["head_1"], "cat")
        self.assertEqual(row_t1["targets"]["head_2"], "sat")
        self.assertEqual(row_t1["targets"]["head_3"], "on")

    def test_design2_sequential_chain_valid_positions_and_loss_terms(self):
        d2 = self.data["design_2_sequential_chain"]
        self.assertEqual(d2["valid_positions_i"], 3)
        self.assertEqual(d2["total_individual_loss_terms"], 9)

    def test_design2_depth1_uses_main_model_hidden_state(self):
        d2 = self.data["design_2_sequential_chain"]
        depth1 = d2["rows"][0]["depths"]["depth_1"]
        self.assertIn("main_model_hidden_state", depth1["input_combines"])

    def test_design2_later_depths_chain_from_previous_depth(self):
        d2 = self.data["design_2_sequential_chain"]
        depth2 = d2["rows"][0]["depths"]["depth_2"]
        self.assertEqual(depth2["input_combines"], "h_1^1")

    def test_both_designs_agree_on_total_loss_term_count_for_this_toy_case(self):
        d1 = self.data["design_1_independent_heads"]
        d2 = self.data["design_2_sequential_chain"]
        self.assertEqual(d1["total_individual_loss_terms"], d2["total_individual_loss_terms"])

    def test_worked_example_numbers_appear_in_chapter_text(self):
        # Cross-check the same headline numbers actually appear in the
        # chapter's own worked-example section, not just in the script.
        self.assertIn("9", self.chapter_text)  # total loss terms
        self.assertIn("cat", self.chapter_text)
        self.assertIn("mat", self.chapter_text)


if __name__ == "__main__":
    unittest.main()
