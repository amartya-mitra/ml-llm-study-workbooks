"""Computational verification for workbook 05 Chapter 4's worked
example: a multidimensional (DP x TP x PP x EP) training layout, its
process-group membership, and its global-batch calculation.

Named test_wb05_ch04_* (not test_ch04_*) because tests/test_ch04_worked_examples.py
already belongs to workbook 04's Chapter 4 -- see the identical naming
note in tests/test_wb05_ch03_worked_examples.py.

Per AGENTS.md, prose must never state a number that isn't backed by a
script -- data/worked-examples/parallelism_layout.py is the source of
truth for every number quoted in
chapters/04-distributed-parallelism.qmd's worked example.
"""
import json
import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WB05 = os.path.join(REPO_ROOT, "workbooks", "05-llm-training")
EXAMPLES_DIR = os.path.join(WB05, "data", "worked-examples")
SCRIPT_PATH = os.path.join(EXAMPLES_DIR, "parallelism_layout.py")
JSON_PATH = os.path.join(EXAMPLES_DIR, "parallelism_layout.json")
CHAPTER_PATH = os.path.join(WB05, "chapters", "04-distributed-parallelism.qmd")


class TestChapter4WorkedExample(unittest.TestCase):
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

    def test_world_size_factorization(self):
        layout = self.data["layout"]
        self.assertEqual(
            layout["dp_degree"] * layout["tp_degree"] * layout["pp_degree"] * layout["ep_degree"],
            layout["world_size"],
        )
        self.assertEqual(layout["world_size"], 64)

    def test_devices_per_replica_and_dp_replica_count(self):
        layout = self.data["layout"]
        self.assertEqual(layout["devices_per_model_replica"], 16)
        self.assertEqual(layout["num_dp_replicas"], layout["dp_degree"])

    def test_representative_rank_coordinates(self):
        coords = self.data["layout"]["representative_coords"]
        self.assertEqual(coords, {"dp_idx": 2, "pp_idx": 0, "tp_idx": 2, "ep_idx": 1})

    def test_process_group_membership_sizes(self):
        layout = self.data["layout"]
        self.assertEqual(len(layout["dp_group"]), layout["dp_degree"])
        self.assertEqual(len(layout["tp_group"]), layout["tp_degree"])
        self.assertEqual(len(layout["pp_group"]), layout["pp_degree"])
        self.assertEqual(len(layout["ep_group"]), layout["ep_degree"])

    def test_representative_rank_is_member_of_every_own_group(self):
        layout = self.data["layout"]
        r = layout["representative_rank"]
        for group_name in ("dp_group", "tp_group", "pp_group", "ep_group"):
            self.assertIn(r, layout[group_name], msg=f"rank {r} missing from its own {group_name}")

    def test_global_batch_size_formula(self):
        b = self.data["batch"]
        self.assertEqual(b["micro_batch_size"] * b["grad_acc_steps"] * b["dp_degree"], b["global_batch_size"])
        self.assertEqual(b["global_batch_size"], 64)

    def test_invalid_world_size_factorization_is_rejected(self):
        self.assertTrue(self.data["validation_checks"]["invalid_world_size_factorization_raised"])

    def test_tp_kv_head_divisibility_checks(self):
        checks = self.data["validation_checks"]
        self.assertTrue(checks["valid_tp_kv_head_divisibility_did_not_raise"])
        self.assertTrue(checks["invalid_tp_kv_head_divisibility_raised"])

    def test_worked_example_numbers_appear_in_chapter_text(self):
        layout = self.data["layout"]
        b = self.data["batch"]
        for n in (str(layout["world_size"]), str(layout["dp_degree"]), str(layout["tp_degree"]),
                  str(layout["pp_degree"]), str(layout["ep_degree"]),
                  str(layout["devices_per_model_replica"]), str(b["global_batch_size"])):
            self.assertIn(n, self.chapter_text, msg=f"'{n}' not found in chapter prose")


if __name__ == "__main__":
    unittest.main()
