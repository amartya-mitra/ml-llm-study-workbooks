"""Computational verification for workbook 05 Chapter 5's worked
example: model-state memory before/after ZeRO-3 sharding, an
activation-memory estimate, one collective's communication payload
and time, exposed communication after a declared overlap fraction,
and the resulting illustrative step-time impact.

Named test_wb05_ch05_* (not test_ch05_*) because tests/test_ch05_worked_examples.py
already belongs to a different workbook's own Chapter 5 -- see the
identical naming note in tests/test_wb05_ch03_worked_examples.py and
tests/test_wb05_ch04_worked_examples.py.

Per AGENTS.md, prose must never state a number that isn't backed by a
script -- data/worked-examples/memory_and_communication_budget.py is
the source of truth for every number quoted in
chapters/05-training-memory-and-communication.qmd's worked example.
"""
import json
import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WB05 = os.path.join(REPO_ROOT, "workbooks", "05-llm-training")
EXAMPLES_DIR = os.path.join(WB05, "data", "worked-examples")
SCRIPT_PATH = os.path.join(EXAMPLES_DIR, "memory_and_communication_budget.py")
JSON_PATH = os.path.join(EXAMPLES_DIR, "memory_and_communication_budget.json")
CHAPTER_PATH = os.path.join(WB05, "chapters", "05-training-memory-and-communication.qmd")


class TestChapter5WorkedExample(unittest.TestCase):
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

    def test_parameter_count(self):
        self.assertEqual(self.data["parameter_count_N"], 4964196352)

    def test_model_state_memory_components_sum_to_total(self):
        rep = self.data["model_state_memory"]["replicated_per_rank_bytes"]
        components = rep["m_params_bf16"] + rep["m_grad_bf16"] + rep["m_params_fp32_master"] + rep["m_opt_fp32_adam"]
        self.assertAlmostEqual(components, rep["total"], delta=1)

    def test_model_state_memory_is_16_times_N(self):
        N = self.data["parameter_count_N"]
        total = self.data["model_state_memory"]["replicated_per_rank_bytes"]["total"]
        self.assertAlmostEqual(total, 16 * N, delta=1)

    def test_zero3_sharding_divides_every_component_by_dp_degree(self):
        dp = self.data["toy_config"]["dp_degree"]
        rep = self.data["model_state_memory"]["replicated_per_rank_bytes"]
        sharded = self.data["model_state_memory"]["zero3_sharded_per_rank_bytes"]
        for key in rep:
            self.assertAlmostEqual(sharded[key], rep[key] / dp, delta=1e-6)

    def test_activation_memory_exceeds_boundary_only_estimate(self):
        act = self.data["activation_memory"]
        self.assertGreater(act["no_recompute_bytes"], act["boundary_only_estimate_bytes"])
        # the no-recompute estimate must be dramatically larger -- this
        # is the "activation explosion" the chapter prose describes
        self.assertGreater(act["no_recompute_bytes"] / act["boundary_only_estimate_bytes"], 10)

    def test_communication_payload_matches_declared_formula(self):
        h = self.data["toy_config"]["hidden"]
        dp = self.data["toy_config"]["dp_degree"]
        expected_elements_per_rank = (16 * h ** 2) / dp
        expected_bytes = expected_elements_per_rank * 2  # bf16
        self.assertAlmostEqual(
            self.data["communication"]["zero3_allgather_payload_per_rank_per_block_bytes"],
            expected_bytes, delta=1,
        )

    def test_exposed_plus_hidden_equals_total_communication_time(self):
        comm = self.data["communication"]
        self.assertAlmostEqual(
            comm["hidden_comm_time_seconds"] + comm["exposed_comm_time_seconds"],
            comm["total_comm_time_all_blocks_seconds"], delta=1e-12,
        )

    def test_step_time_with_overlap_is_less_than_fully_exposed(self):
        st = self.data["step_time"]
        self.assertLess(st["step_time_with_overlap_seconds"], st["step_time_fully_exposed_seconds"])
        self.assertAlmostEqual(
            st["step_time_with_overlap_seconds"],
            st["compute_time_seconds"] + self.data["communication"]["exposed_comm_time_seconds"],
            delta=1e-9,
        )

    def test_overlap_never_makes_step_time_faster_than_pure_compute(self):
        # Overlap can hide communication, but it cannot make the step
        # faster than compute alone -- exposed time is >= 0.
        st = self.data["step_time"]
        self.assertGreaterEqual(st["step_time_with_overlap_seconds"], st["compute_time_seconds"])

    def test_all_four_invalid_configuration_checks_raised(self):
        checks = self.data["invalid_configuration_checks"]
        for name, raised in checks.items():
            self.assertTrue(raised, msg=f"{name} did not raise as expected")

    def test_worked_example_numbers_appear_in_chapter_text(self):
        mm = self.data["model_state_memory"]
        act = self.data["activation_memory"]
        comm = self.data["communication"]
        st = self.data["step_time"]
        # Spot-check a representative, distinctive subset of numbers
        # (avoids asserting on every float's exact string rendering,
        # which is fragile to formatting choices in prose).
        self.assertIn("4.96", self.chapter_text)  # parameter_count_N_billions
        self.assertIn(f"{mm['replicated_per_rank_GiB']:.1f}", self.chapter_text)
        self.assertIn(f"{mm['zero3_sharded_per_rank_GiB']:.1f}", self.chapter_text)
        self.assertIn(f"{act['no_recompute_GiB']:.2f}", self.chapter_text)
        self.assertIn(f"{act['boundary_only_estimate_GiB']:.2f}", self.chapter_text)
        self.assertIn(f"{comm['zero3_allgather_payload_per_rank_per_block_MiB']:.0f}", self.chapter_text)
        self.assertIn(f"{st['overlap_benefit_percent']:.1f}", self.chapter_text)


if __name__ == "__main__":
    unittest.main()
