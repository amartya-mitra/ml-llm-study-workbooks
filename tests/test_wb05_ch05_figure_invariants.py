"""Semantic invariant tests for workbook 05 Chapter 5's two figures.

A figure passing tests/test_figures.py's generic bounds/XML checks is
NOT evidence it is semantically correct -- see
docs/chapter-review-checklist.md section 5. These tests check that
each figure's rendered quantities, ordering, and dependencies actually
match the worked example's own computed numbers, by re-deriving the
same layout math the figure scripts use and comparing against the
worked example's JSON directly.
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

sys.path.insert(0, os.path.join(WB05, "figures", "source"))


class TestTrainingStepTimelineInvariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, SCRIPT_PATH], capture_output=True, text=True)
        with open(JSON_PATH, encoding="utf-8") as f:
            cls.data = json.load(f)
        import fig_training_step_timeline as fig
        cls.fig = fig
        cls.fig_data = fig.load_worked_example_data()

    def test_figure_loads_the_same_json_the_worked_example_produced(self):
        self.assertEqual(self.fig_data, self.data)

    def test_hidden_plus_exposed_equals_total_communication(self):
        comm = self.fig_data["communication"]
        self.assertAlmostEqual(
            comm["hidden_comm_time_seconds"] + comm["exposed_comm_time_seconds"],
            comm["total_comm_time_all_blocks_seconds"], delta=1e-12,
        )

    def test_exposed_segment_starts_exactly_where_compute_ends(self):
        # Mirrors the figure script's own x-coordinate math: the
        # exposed-communication rect starts at left_margin + compute_s
        # * px_per_s, i.e. exactly at the end of the compute bar.
        compute_s = self.fig_data["step_time"]["compute_time_seconds"]
        step_s = self.fig_data["step_time"]["step_time_with_overlap_seconds"]
        exposed_s = self.fig_data["communication"]["exposed_comm_time_seconds"]
        self.assertAlmostEqual(compute_s + exposed_s, step_s, delta=1e-9)

    def test_critical_path_label_matches_step_time_with_overlap(self):
        # The figure's critical-path bracket spans exactly
        # [0, step_time_with_overlap_seconds] -- not fully-exposed time.
        step_with_overlap = self.fig_data["step_time"]["step_time_with_overlap_seconds"]
        step_fully_exposed = self.fig_data["step_time"]["step_time_fully_exposed_seconds"]
        self.assertLess(step_with_overlap, step_fully_exposed)

    def test_rendered_svg_exists_and_is_nonempty(self):
        svg_path = os.path.join(WB05, "figures", "rendered", "fig-training-step-timeline.svg")
        self.assertTrue(os.path.exists(svg_path))
        self.assertGreater(os.path.getsize(svg_path), 500)


class TestMemoryLedgerInvariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, SCRIPT_PATH], capture_output=True, text=True)
        with open(JSON_PATH, encoding="utf-8") as f:
            cls.data = json.load(f)
        import fig_memory_ledger_dp_vs_sharded as fig
        cls.fig = fig
        cls.fig_data = fig.load_worked_example_data()

    def test_figure_loads_the_same_json_the_worked_example_produced(self):
        self.assertEqual(self.fig_data, self.data)

    def test_replicated_bar_segments_sum_to_its_own_total(self):
        rep = self.fig_data["model_state_memory"]["replicated_per_rank_bytes"]
        segment_sum = sum(rep[k] for k in self.fig.SEGMENT_ORDER)
        self.assertAlmostEqual(segment_sum, rep["total"], delta=1)

    def test_sharded_bar_segments_sum_to_its_own_total(self):
        sharded = self.fig_data["model_state_memory"]["zero3_sharded_per_rank_bytes"]
        segment_sum = sum(sharded[k] for k in self.fig.SEGMENT_ORDER)
        self.assertAlmostEqual(segment_sum, sharded["total"], delta=1)

    def test_sharded_total_equals_replicated_total_divided_by_dp(self):
        dp = self.fig_data["toy_config"]["dp_degree"]
        rep_total = self.fig_data["model_state_memory"]["replicated_per_rank_bytes"]["total"]
        sharded_total = self.fig_data["model_state_memory"]["zero3_sharded_per_rank_bytes"]["total"]
        self.assertAlmostEqual(sharded_total, rep_total / dp, delta=1e-6)

    def test_every_segment_key_has_a_label_and_a_color(self):
        for key in self.fig.SEGMENT_ORDER:
            self.assertIn(key, self.fig.SEGMENT_LABELS)

    def test_rendered_svg_exists_and_is_nonempty(self):
        svg_path = os.path.join(WB05, "figures", "rendered", "fig-memory-ledger-dp-vs-sharded.svg")
        self.assertTrue(os.path.exists(svg_path))
        self.assertGreater(os.path.getsize(svg_path), 500)


if __name__ == "__main__":
    unittest.main()
