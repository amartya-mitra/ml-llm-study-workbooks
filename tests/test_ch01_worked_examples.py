"""Computational verification for workbook 05 Chapter 1's worked
example and applied exercise.

Per AGENTS.md, prose must never state a number that isn't backed by a
script -- data/worked-examples/data_mixing_allocation.py is the source
of truth for every number quoted in
chapters/01-pretraining-objectives-and-data.qmd's worked example and
applied exercise.
"""
import json
import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WB05 = os.path.join(REPO_ROOT, "workbooks", "05-llm-training")
EXAMPLES_DIR = os.path.join(WB05, "data", "worked-examples")
SCRIPT_PATH = os.path.join(EXAMPLES_DIR, "data_mixing_allocation.py")
JSON_PATH = os.path.join(EXAMPLES_DIR, "data_mixing_allocation.json")
CHAPTER_PATH = os.path.join(WB05, "chapters", "01-pretraining-objectives-and-data.qmd")


class TestChapter1WorkedExample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = subprocess.run([sys.executable, SCRIPT_PATH], capture_output=True, text=True)
        cls.assertEqual_ = result.returncode
        with open(JSON_PATH, encoding="utf-8") as f:
            cls.data = json.load(f)
        with open(CHAPTER_PATH, encoding="utf-8") as f:
            cls.chapter_text = f.read()

    def test_script_runs_cleanly(self):
        result = subprocess.run([sys.executable, SCRIPT_PATH], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=f"worked-example script failed: {result.stderr}")

    def test_worked_example_mixture_weights_sum_to_one(self):
        weights = self.data["worked_example"]["mixture_weights"]
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=9)

    def test_worked_example_token_allocations_match_chapter_text(self):
        allocation = self.data["worked_example"]["tokens_per_source"]
        self.assertEqual(allocation["fineweb-edu"], 21_000_000_000)
        self.assertEqual(allocation["stack-edu-python"], 6_000_000_000)
        self.assertEqual(allocation["finemath-3plus"], 3_000_000_000)
        self.assertEqual(sum(allocation.values()), 30_000_000_000)
        # Cross-check the same three numbers actually appear in the
        # chapter's own worked-example table, not just in the script.
        self.assertIn("21\\text{B}", self.chapter_text)
        self.assertIn("6\\text{B}", self.chapter_text)
        self.assertIn("3\\text{B}", self.chapter_text)

    def test_applied_exercise_mixture_weights_sum_to_one(self):
        weights = self.data["applied_exercise"]["mixture_weights"]
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=9)

    def test_applied_exercise_domain_split_matches_chapter_text(self):
        weights = self.data["applied_exercise"]["mixture_weights"]
        self.assertEqual(weights["english-web"], 0.75)
        self.assertEqual(weights["multilingual-web"], 0.12)
        self.assertEqual(weights["code"], 0.10)
        self.assertEqual(weights["math"], 0.03)
        self.assertIn("75%", self.chapter_text)
        self.assertIn("12%", self.chapter_text)
        self.assertIn("10%", self.chapter_text)
        self.assertIn("3%", self.chapter_text)

    def test_applied_exercise_allocations_sum_to_total_budget(self):
        allocation = self.data["applied_exercise"]["tokens_per_source"]
        self.assertEqual(sum(allocation.values()), 200_000_000_000)


if __name__ == "__main__":
    unittest.main()
