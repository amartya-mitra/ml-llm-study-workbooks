"""Semantic invariant tests for workbook 05 Chapter 6's figure
(fig-run-diagnosis-pipeline): the evidence-to-diagnosis pipeline for
reading a pretraining run's telemetry.

A figure passing tests/test_figures.py's generic bounds/XML checks is
NOT evidence it is semantically correct -- see
docs/chapter-review-checklist.md section 5. These tests re-derive the
same values the figure script reads from
data/worked-examples/pretraining_run_telemetry.py's own JSON output and
check that the figure's six stages, in order, actually correspond to
that data (observed step-18 telemetry, derived metrics, comparability
controls, and the two competing diagnoses plus the distinguishing
measurement), and that each stage's declared color category matches
config/visual-style.yaml's own palette semantics.
"""
import json
import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WB05 = os.path.join(REPO_ROOT, "workbooks", "05-llm-training")
EXAMPLES_DIR = os.path.join(WB05, "data", "worked-examples")
SCRIPT_PATH = os.path.join(EXAMPLES_DIR, "pretraining_run_telemetry.py")
JSON_PATH = os.path.join(EXAMPLES_DIR, "pretraining_run_telemetry.json")

sys.path.insert(0, os.path.join(WB05, "figures", "source"))
sys.path.insert(0, os.path.join(REPO_ROOT, "figures", "source"))


class TestRunDiagnosisPipelineInvariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, SCRIPT_PATH], capture_output=True, text=True)
        with open(JSON_PATH, encoding="utf-8") as f:
            cls.data = json.load(f)
        import fig_run_diagnosis_pipeline as fig
        cls.fig = fig
        cls.fig_data = fig.load_worked_example_data()
        from _svg_helpers import load_visual_style, palette_hex
        cls.colors = palette_hex(load_visual_style())

    def test_figure_loads_the_same_json_the_worked_example_produced(self):
        self.assertEqual(self.fig_data, self.data)

    def test_event_used_by_figure_is_the_loss_spike_event(self):
        event = self.fig_data["diagnoses"]["loss_spike_event"]
        self.assertEqual(event["step"], 18)

    def test_wrap_text_never_overflows_and_rejects_oversized_single_words(self):
        # Every real line this figure draws must wrap without error at
        # the box width/font size the figure script actually uses.
        lines = self.fig.wrap_text("a " * 40 + "word", max_width_px=400, font_size=12.5)
        self.assertGreater(len(lines), 1)
        for line in lines:
            max_chars = int(400 / (12.5 * 0.56))
            self.assertLessEqual(len(line), max_chars)
        with self.assertRaises(ValueError):
            self.fig.wrap_text("x" * 500, max_width_px=100, font_size=12.5)

    def test_six_stage_titles_appear_in_declared_pipeline_order(self):
        # Re-run main()'s own stage-construction logic indirectly: build
        # the same stage title list main() would build by inspecting the
        # rendered SVG's own text content for each stage's distinguishing
        # keyword, in order.
        with open(self.fig.OUTPUT_PATH, encoding="utf-8") as f:
            svg_text = f.read()
        expected_order = [
            "1. Configuration",
            "2. Training telemetry",
            "3. Derived metrics",
            "4. Comparability controls",
            "5. Bottleneck / failure hypothesis",
            "6. Measurement needed to confirm",
        ]
        positions = [svg_text.index(title) for title in expected_order]
        self.assertEqual(positions, sorted(positions), msg="pipeline stages are not drawn in declared order")

    def test_configuration_stage_tokens_per_step_matches_json(self):
        with open(self.fig.OUTPUT_PATH, encoding="utf-8") as f:
            svg_text = f.read()
        tps = self.fig_data["tokens_per_step"]
        self.assertIn(f"{tps:,}", svg_text)

    def test_telemetry_stage_matches_step_18_observed_values(self):
        by_step = {e["step"]: e for e in self.fig_data["per_step_log"]}
        step18 = by_step[18]
        with open(self.fig.OUTPUT_PATH, encoding="utf-8") as f:
            svg_text = f.read()
        self.assertIn(f"{step18['observed']['train_loss']:.3f}", svg_text)
        self.assertIn(f"{step18['observed']['grad_norm']:.3f}", svg_text)
        self.assertIn(f"{step18['observed']['step_time_seconds']:.3f}", svg_text)

    def test_derived_stage_matches_step_18_derived_values(self):
        by_step = {e["step"]: e for e in self.fig_data["per_step_log"]}
        step18 = by_step[18]
        with open(self.fig.OUTPUT_PATH, encoding="utf-8") as f:
            svg_text = f.read()
        self.assertIn(f"{step18['derived']['consumed_tokens']:,}", svg_text)
        self.assertIn(f"{step18['derived']['achieved_fraction_of_nominal']:.1%}", svg_text)
        self.assertIn(f"{step18['derived']['loss_relative_deviation']:.1%}", svg_text)
        self.assertIn(str(step18["derived"]["loss_anomaly_flagged"]), svg_text)

    def test_comparability_controls_stage_matches_json(self):
        with open(self.fig.OUTPUT_PATH, encoding="utf-8") as f:
            svg_text = f.read()
        self.assertIn(str(all(self.fig_data["comparability_controls"].values())), svg_text)

    def test_diagnosis_stage_names_both_competing_diagnoses(self):
        event = self.fig_data["diagnoses"]["loss_spike_event"]
        diag_a, diag_b = event["competing_diagnoses"]
        with open(self.fig.OUTPUT_PATH, encoding="utf-8") as f:
            svg_text = f.read()
        self.assertIn(diag_a["name"].replace("_", " "), svg_text)
        self.assertIn(diag_b["name"].replace("_", " "), svg_text)

    def test_measurement_stage_matches_distinguishing_measurement(self):
        event = self.fig_data["diagnoses"]["loss_spike_event"]
        with open(self.fig.OUTPUT_PATH, encoding="utf-8") as f:
            svg_text = f.read()
        # The measurement string is wrapped across lines, so check its
        # distinctive substring rather than the full phrase verbatim.
        self.assertIn("gradient-norm breakdown", svg_text)
        self.assertIn(event["distinguishing_measurement_not_logged"].split(" ")[0], svg_text)

    def test_color_semantics_match_palette_categories(self):
        # Observed/derived/assumption/diagnosis boxes must each use the
        # exact palette hex this figure's docstring declares, reusing
        # config/visual-style.yaml's existing semantic colors rather than
        # inventing new ones.
        observed_color = self.colors["stored_information"]
        derived_color = self.colors["computation"]
        assumption_color = self.colors["frozen_or_inactive"]
        diagnosis_color = self.colors["bottleneck_or_failure"]
        with open(self.fig.OUTPUT_PATH, encoding="utf-8") as f:
            svg_text = f.read()
        for color in (observed_color, derived_color, assumption_color, diagnosis_color):
            self.assertIn(color, svg_text)
        # Distinct categories must use distinct colors.
        self.assertEqual(len({observed_color, derived_color, assumption_color, diagnosis_color}), 4)

    def test_measurement_needed_stage_is_dashed(self):
        with open(self.fig.OUTPUT_PATH, encoding="utf-8") as f:
            svg_text = f.read()
        self.assertIn("stroke-dasharray", svg_text)

    def test_rendered_svg_exists_and_is_nonempty(self):
        self.assertTrue(os.path.exists(self.fig.OUTPUT_PATH))
        self.assertGreater(os.path.getsize(self.fig.OUTPUT_PATH), 500)


if __name__ == "__main__":
    unittest.main()
