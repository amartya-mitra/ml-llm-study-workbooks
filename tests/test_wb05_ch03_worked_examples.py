"""Computational verification for workbook 05 Chapter 3's worked
example: fixed-compute model/data allocation under Kaplan et al.'s and
Hoffmann et al.'s (Chinchilla) fitted exponents, plus two real
production-choice comparisons.

Named test_wb05_ch03_* (not test_ch03_*) because tests/test_ch03_worked_examples.py
already belongs to workbook 04's Chapter 3 (attention head structure)
-- workbook 05's own chapters 1-2 tests happened to reuse the
now-freed test_ch01_worked_examples.py / test_ch02_worked_examples.py
names (workbook 04's chapters 1-2 tests were consolidated into
test_ch01_02_worked_examples.py), but workbook 04's chapter 3 test was
never consolidated, so that name is still taken.

Per AGENTS.md, prose must never state a number that isn't backed by a
script -- data/worked-examples/scaling_law_allocation.py is the source
of truth for every number quoted in
chapters/03-optimization-and-scaling-laws.qmd's worked example.
"""
import json
import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WB05 = os.path.join(REPO_ROOT, "workbooks", "05-llm-training")
EXAMPLES_DIR = os.path.join(WB05, "data", "worked-examples")
SCRIPT_PATH = os.path.join(EXAMPLES_DIR, "scaling_law_allocation.py")
JSON_PATH = os.path.join(EXAMPLES_DIR, "scaling_law_allocation.json")
CHAPTER_PATH = os.path.join(WB05, "chapters", "03-optimization-and-scaling-laws.qmd")


class TestChapter3WorkedExample(unittest.TestCase):
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

    def test_toy_anchor_respects_the_six_n_d_compute_relation(self):
        a = self.data["part_a_toy_allocation"]
        n0, d0, c0 = a["toy_anchor"]["N0"], a["toy_anchor"]["D0"], a["toy_anchor"]["C0_flops"]
        self.assertAlmostEqual(6 * n0 * d0, c0, delta=1.0)

    def test_kaplan_allocation_growth_factors(self):
        kaplan = self.data["part_a_toy_allocation"]["kaplan"]
        self.assertAlmostEqual(kaplan["model_growth_factor"], 5.37, places=2)
        self.assertAlmostEqual(kaplan["data_growth_factor"], 1.86, places=2)

    def test_chinchilla_allocation_growth_factors(self):
        chinchilla = self.data["part_a_toy_allocation"]["chinchilla"]
        self.assertAlmostEqual(chinchilla["model_growth_factor"], 3.16, places=2)
        self.assertAlmostEqual(chinchilla["data_growth_factor"], 3.16, places=2)

    def test_both_allocations_respect_the_same_ten_x_compute_budget(self):
        a = self.data["part_a_toy_allocation"]
        self.assertAlmostEqual(a["kaplan"]["C_new_over_C0"], 10.0, places=6)
        self.assertAlmostEqual(a["chinchilla"]["C_new_over_C0"], 10.0, places=6)

    def test_table3_tokens_per_param_ratio_range(self):
        b = self.data["part_b_real_table3_and_chinchilla"]
        self.assertAlmostEqual(b["tokens_per_param_min"], 20.0, places=2)
        self.assertAlmostEqual(b["tokens_per_param_max"], 22.39, places=2)

    def test_table3_67b_row_matches_quoted_source_value(self):
        b = self.data["part_b_real_table3_and_chinchilla"]
        self.assertEqual(b["table3_67B_row_predicted_tokens"], 1.5e12)

    def test_chinchilla_actual_model_differs_from_table3_67b_row(self):
        b = self.data["part_b_real_table3_and_chinchilla"]
        self.assertEqual(b["chinchilla_actual"]["params"], 7.0e10)
        self.assertEqual(b["chinchilla_actual"]["tokens"], 1.4e12)
        self.assertNotEqual(b["chinchilla_actual"]["params"], 6.7e10)

    def test_smollm3_overtraining_factor(self):
        c = self.data["part_c_smollm3_vs_estimate"]
        self.assertAlmostEqual(c["overtraining_factor_vs_interpolated_estimate"], 180.2, places=1)

    def test_worked_example_numbers_appear_in_chapter_text(self):
        a = self.data["part_a_toy_allocation"]
        c = self.data["part_c_smollm3_vs_estimate"]
        self.assertIn("5.37", self.chapter_text)
        self.assertIn("3.16", self.chapter_text)
        self.assertIn("180", self.chapter_text)
        self.assertIn(f"{a['kaplan']['data_growth_factor']:.2f}", self.chapter_text)


if __name__ == "__main__":
    unittest.main()
