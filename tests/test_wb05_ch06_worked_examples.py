"""Computational verification for workbook 05 Chapter 6's worked
example: a synthetic, illustrative 30-step pretraining-run log, the
tokens/throughput/FLOPs-utilization quantities derived from it, and
the two detected behavior-change events (a loss-and-gradient-norm
spike at step 18, and a sustained throughput drop across steps 24-27)
each with two competing diagnoses and a stated distinguishing
measurement the log does not contain.

Named test_wb05_ch06_* (not test_ch06_*) because test_ch06_*.py already
belongs to a different workbook's own Chapter 6 -- see the identical
naming note in tests/test_wb05_ch05_worked_examples.py and
docs/chapter-review-checklist.md.

Per AGENTS.md, prose must never state a number that isn't backed by a
script -- data/worked-examples/pretraining_run_telemetry.py is the
source of truth for every number quoted in
chapters/06-reading-real-pretraining-runs.qmd's worked example, its
figure, its questions, and its answer key.
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
CHAPTER_PATH = os.path.join(WB05, "chapters", "06-reading-real-pretraining-runs.qmd")
SOLUTIONS_PATH = os.path.join(WB05, "solutions", "06-reading-real-pretraining-runs-solutions.qmd")


class TestChapter6WorkedExample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, SCRIPT_PATH], capture_output=True, text=True)
        with open(JSON_PATH, encoding="utf-8") as f:
            cls.data = json.load(f)
        with open(CHAPTER_PATH, encoding="utf-8") as f:
            cls.chapter_text = f.read()
        with open(SOLUTIONS_PATH, encoding="utf-8") as f:
            cls.solutions_text = f.read()
        cls.by_step = {e["step"]: e for e in cls.data["per_step_log"]}

    def test_script_runs_cleanly(self):
        result = subprocess.run([sys.executable, SCRIPT_PATH], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=f"worked-example script failed: {result.stderr}")

    def test_mentions_synthetic_not_real(self):
        # This workbook's sourcing discipline requires a synthetic log to
        # be repeatedly, unmistakably labeled as such wherever it is quoted.
        self.assertIn("synthetic", self.chapter_text.lower())
        self.assertGreaterEqual(self.chapter_text.lower().count("synthetic"), 3)

    def test_tokens_per_step(self):
        cfg = self.data["synthetic_run_config"]
        expected = cfg["global_batch_size_sequences"] * cfg["seq_len_tokens"] * cfg["gradient_accumulation_steps"]
        self.assertEqual(self.data["tokens_per_step"], expected)
        self.assertEqual(self.data["tokens_per_step"], 1_048_576)

    def test_consumed_tokens_equals_step_times_tokens_per_step(self):
        tps = self.data["tokens_per_step"]
        for step, entry in self.by_step.items():
            self.assertEqual(entry["derived"]["consumed_tokens"], step * tps)

    def test_consumed_sequences_equals_step_times_batch_size(self):
        batch = self.data["synthetic_run_config"]["global_batch_size_sequences"]
        for step, entry in self.by_step.items():
            self.assertEqual(entry["derived"]["consumed_sequences"], step * batch)

    def test_global_and_per_device_throughput_relationship(self):
        device_count = self.data["synthetic_run_config"]["device_count"]
        for entry in self.data["per_step_log"]:
            global_tp = entry["derived"]["global_throughput_tokens_per_s"]
            per_device_tp = entry["derived"]["per_device_throughput_tokens_per_s"]
            self.assertAlmostEqual(per_device_tp * device_count, global_tp, delta=1e-6)

    def test_loss_spike_event_detected_exactly_at_step_18(self):
        self.assertEqual(self.data["detected_loss_anomaly_steps"], [18])
        step18 = self.by_step[18]
        self.assertEqual(step18["observed"]["train_loss"], 4.350)
        self.assertEqual(step18["observed"]["grad_norm"], 3.950)
        # step_time stays at baseline during the loss event -- not a
        # throughput event.
        self.assertAlmostEqual(step18["observed"]["step_time_seconds"], 1.800, delta=1e-9)
        self.assertTrue(step18["derived"]["loss_anomaly_flagged"])

    def test_throughput_drop_event_steps_and_flags(self):
        cfg = self.data["synthetic_run_config"]
        for step in (24, 25, 26, 27):
            entry = self.by_step[step]
            self.assertAlmostEqual(entry["observed"]["step_time_seconds"], 2.880, delta=1e-9)
        # The trailing-window check (window=4, threshold=20%) flags 24-26
        # but NOT 27, because by step 27 the trailing window itself has
        # filled with slow steps -- the exact "averaged metric lags"
        # demonstration the chapter's misconception callout relies on.
        self.assertEqual(self.data["detected_throughput_anomaly_steps"], [24, 25, 26])
        self.assertNotIn(27, self.data["detected_throughput_anomaly_steps"])
        self.assertLess(self.by_step[27]["derived"]["step_time_relative_deviation"], cfg["anomaly_relative_threshold"])
        self.assertGreater(self.by_step[27]["derived"]["step_time_relative_deviation"], 0)

    def test_throughput_drop_does_not_disturb_loss_or_grad_norm(self):
        for step in (24, 25, 26, 27):
            entry = self.by_step[step]
            self.assertFalse(entry["derived"]["loss_anomaly_flagged"])

    def test_loss_spike_does_not_disturb_step_time(self):
        self.assertFalse(self.by_step[18]["derived"]["throughput_anomaly_flagged"])

    def test_achieved_fraction_of_nominal_is_strictly_between_zero_and_one(self):
        for entry in self.data["per_step_log"]:
            frac = entry["derived"]["achieved_fraction_of_nominal"]
            self.assertGreater(frac, 0.0)
            self.assertLess(frac, 1.0)

    def test_achieved_fraction_drops_during_throughput_event(self):
        baseline_frac = self.by_step[20]["derived"]["achieved_fraction_of_nominal"]
        event_frac = self.by_step[25]["derived"]["achieved_fraction_of_nominal"]
        self.assertLess(event_frac, baseline_frac)

    def test_eval_loss_only_logged_at_checkpoint_steps(self):
        checkpoint_steps = set(self.data["synthetic_run_config"]["checkpoint_steps"])
        for step, entry in self.by_step.items():
            if step in checkpoint_steps:
                self.assertIsNotNone(entry["observed"]["eval_loss"])
            else:
                self.assertIsNone(entry["observed"]["eval_loss"])

    def test_checkpoint_at_step_20_does_not_reveal_the_step_18_spike(self):
        # The chapter's own point: a sparse checkpoint record can miss a
        # transient event the full per-step log shows clearly.
        step20 = self.by_step[20]
        gap = step20["observed"]["eval_loss"] - step20["observed"]["train_loss"]
        self.assertGreater(gap, 0)
        self.assertLess(gap, 0.5)  # an ordinary generalization gap, not a spike-sized jump

    def test_two_competing_diagnoses_for_each_event(self):
        diagnoses = self.data["diagnoses"]
        for event_key in ("loss_spike_event", "throughput_drop_event"):
            event = diagnoses[event_key]
            self.assertEqual(len(event["competing_diagnoses"]), 2)
            self.assertTrue(event["distinguishing_measurement_not_logged"])

    def test_invalid_configuration_checks_all_pass(self):
        checks = self.data["invalid_configuration_checks"]
        self.assertGreaterEqual(len(checks), 5)
        for name, ok in checks.items():
            self.assertTrue(ok, msg=f"{name} did not hold as expected")

    def test_comparability_controls_all_true_for_this_within_run_comparison(self):
        self.assertTrue(all(self.data["comparability_controls"].values()))

    def test_worked_example_numbers_appear_in_chapter_text(self):
        step18 = self.by_step[18]
        self.assertIn("1{,}048{,}576", self.chapter_text)
        self.assertIn("18{,}874{,}368", self.chapter_text)
        self.assertIn(f"+{step18['derived']['loss_relative_deviation'] * 100:.1f}%", self.chapter_text)
        self.assertIn("582{,}542", self.chapter_text)
        self.assertIn("18{,}204", self.chapter_text)
        self.assertIn("364{,}089", self.chapter_text)
        self.assertIn("11{,}378", self.chapter_text)
        self.assertIn(f"{self.by_step[20]['derived']['achieved_fraction_of_nominal'] * 100:.1f}%", self.chapter_text)
        self.assertIn(f"{self.by_step[25]['derived']['achieved_fraction_of_nominal'] * 100:.1f}%", self.chapter_text)
        self.assertIn("per-parameter-group", self.chapter_text)
        self.assertIn("per-device (per-rank) step-time", self.chapter_text)

    def test_worked_example_numbers_appear_in_solutions_text(self):
        self.assertIn("25{,}165{,}824", self.solutions_text)
        self.assertIn("364{,}088.9", self.solutions_text)
        self.assertIn("11{,}377.8", self.solutions_text)
        self.assertIn("Step 18", self.solutions_text)


if __name__ == "__main__":
    unittest.main()
