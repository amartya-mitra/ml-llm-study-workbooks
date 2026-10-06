"""Regression tests for the TSFM addendum's worked examples (W1-W6).

Each worked-example script is the numeric source of truth. These tests run
each script, assert on its JSON output, recompute key values independently
of the script's own helpers, and check that the numbers repeated in the
modules' prose appear in the chapter text.

Evidence labels asserted here: reported (formula or setting taken from a
source), derived (arithmetic), illustrative (chosen for teaching).
"""
import json
import math
import os
import re
import subprocess
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ADD = os.path.join(REPO_ROOT, "workbooks", "addendum-04-05-tsfm")
EX = os.path.join(ADD, "data", "worked-examples")
CH = os.path.join(ADD, "chapters")


def run_script(name):
    path = os.path.join(EX, name + ".py")
    result = subprocess.run([sys.executable, path], capture_output=True, text=True)
    assert result.returncode == 0, f"{name} failed: {result.stderr}"
    with open(os.path.join(EX, name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def chapter_text(prefix):
    for fn in os.listdir(CH):
        if fn.startswith(prefix):
            with open(os.path.join(CH, fn), encoding="utf-8") as f:
                return f.read()
    raise AssertionError("chapter not found: " + prefix)


class TestW1Inputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = run_script("w1_inputs")
        cls.text = chapter_text("01-")

    def test_mean_scaling_matches_independent_computation(self):
        x = self.d["series"]
        scale = sum(abs(v) for v in x) / len(x)
        self.assertAlmostEqual(self.d["mean_abs_scale"], scale)
        self.assertAlmostEqual(scale, 220 / 12)
        self.assertEqual(self.d["scaled"], [v / scale for v in x])

    def test_bin_ids_are_monotone_in_value_and_in_range(self):
        ids = self.d["bin_ids"]
        self.assertEqual(ids, [2, 2, 3, 2, 3, 3, 4, 4, 4, 5, 5, 6])
        for a, b in zip(self.d["scaled"], ids):
            self.assertEqual(b, min(int(a // 0.25), 7))
        self.assertTrue(all(0 <= i < self.d["n_bins"] for i in ids))

    def test_quantization_loses_position_inside_a_bin(self):
        self.assertGreater(self.d["max_abs_reconstruction_error"], 0)
        self.assertAlmostEqual(self.d["max_abs_reconstruction_error"], 2.04, places=2)

    def test_patch_counts(self):
        t, p, s = self.d["t_ctx"], self.d["patch_length"], self.d["stride"]
        self.assertEqual(self.d["n_patches_padded"], (t - p) // s + 2)
        self.assertEqual(self.d["n_patches_padded"], 6)
        self.assertEqual(self.d["n_patches_nonoverlapping"], 3)
        self.assertEqual(len(self.d["patch_windows"]), 6)
        self.assertEqual(self.d["n_padded_positions"], 2)
        # consecutive windows advance by exactly the stride and have length P
        for k, w in enumerate(self.d["patch_windows"]):
            self.assertEqual(len(w), p)
            self.assertEqual(w[0], k * s)

    def test_lag_tokens_need_full_history(self):
        toks = self.d["lag_tokens"]
        self.assertEqual(len(toks), 8)
        for tok in toks:
            self.assertTrue(all(i >= 1 for i in tok["lag_indices"]))
        self.assertEqual(toks[0]["t"], max(self.d["lags"]) + 1)

    def test_large_configuration_arithmetic(self):
        b = self.d["big_config"]
        self.assertEqual(b["n_patches_padded"], (512 - 16) // 8 + 2)
        self.assertEqual(b["n_patches_padded"], 64)
        self.assertEqual(b["n_patches_nonoverlapping"], 32)
        self.assertEqual(b["token_ratio"], 8.0)
        self.assertEqual(b["score_ratio"], 64.0)
        self.assertEqual(b["score_entries_per_head_per_layer_time_steps"], 512 ** 2)

    def test_prose_numbers_appear_in_the_chapter(self):
        for needle in ["18.33", "2.04", "N_p=\\lfloor(12-4)/2\\rfloor+2=6", "8 tokens", "times fewer score entries", "(32 without overlap)"]:
            self.assertIn(needle, self.text, msg=needle)

    def test_settings_are_labeled_illustrative(self):
        self.assertEqual(self.d["labels"]["series"], "illustrative")
        self.assertEqual(self.d["labels"]["big_config"], "illustrative")


class TestW2Shapes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = run_script("w2_shapes")
        cls.text = chapter_text("02-")

    def test_four_by_sixteen_rule(self):
        d = self.d
        self.assertEqual(d["point_values"], 64)
        self.assertEqual(d["future_timestamps"], 16)
        self.assertEqual(d["quantile_numbers"], 4 * 16 * 9)
        self.assertEqual(d["quantile_numbers"], 576)
        self.assertEqual(d["sample_numbers"], 4 * 16 * d["n_samples"])
        self.assertEqual(d["covariate_extra_output_axes"], 0)

    def test_flattening_cost(self):
        d = self.d
        self.assertEqual(d["score_entries_independent"], 1024)
        self.assertEqual(d["score_entries_flattened"], 4096)
        self.assertEqual(d["score_ratio_flattened_over_independent"], 4.0)

    def test_group_id_layouts(self):
        g = self.d["group_layouts"]
        self.assertEqual(len(set(g["independent_series"]["group_ids"])), len(g["independent_series"]["rows"]))
        self.assertEqual(len(set(g["multivariate"]["group_ids"])), 1)
        self.assertEqual(len(set(g["targets_plus_covariates"]["group_ids"])), 1)

    def test_prose_numbers_appear_in_the_chapter(self):
        for needle in ["4\\times16=64", "4\\times16\\times9=576", "4\\times16^2=1024", "64^2=4096"]:
            self.assertIn(needle, self.text, msg=needle)

    def test_axis_orders_are_labeled_by_source(self):
        self.assertIn("horizon x targets x quantiles", self.d["reported_axis_orders"]["chronos_2"])


class TestW3Rollout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = run_script("w3_rollout")
        cls.text = chapter_text("03-")

    def test_pass_counts_equal_ceiling_of_horizon_over_output_patch(self):
        by_p = {r["p_out"]: r["forward_passes"] for r in self.d["rows"] if r["klass"] == "iterative"}
        self.assertEqual(by_p[128], math.ceil(256 / 128))
        self.assertEqual(by_p[32], math.ceil(256 / 32))
        self.assertEqual(by_p[1], 256)
        self.assertEqual((by_p[128], by_p[32], by_p[1]), (2, 8, 256))

    def test_non_iterative_rows_use_one_pass(self):
        for r in self.d["rows"]:
            if r["klass"] in ("placeholder", "direct"):
                self.assertEqual(r["forward_passes"], 1)

    def test_placeholder_patch_count(self):
        ph = [r for r in self.d["rows"] if r["klass"] == "placeholder"][0]
        self.assertEqual(ph["placeholder_patches"] * self.d["p_in"], self.d["horizon"])

    def test_truncation_example(self):
        t = self.d["truncation_example"]
        self.assertEqual((t["forward_passes"], t["generated_steps"], t["truncated_steps"]), (4, 128, 28))

    def test_prose_numbers_appear_in_the_chapter(self):
        for needle in ["\\lceil256/128\\rceil=2", "\\lceil256/32\\rceil=8", "256 passes", "28 are discarded"]:
            self.assertIn(needle, self.text, msg=needle)


class TestW4Losses(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = run_script("w4_losses")
        cls.text = chapter_text("04-")

    def test_pinball_values(self):
        vals = {c["tau"]: c["pinball"] for c in self.d["pinball_cases"]}
        self.assertAlmostEqual(vals[0.1], 0.2)
        self.assertAlmostEqual(vals[0.5], 0.5)
        self.assertAlmostEqual(vals[0.9], 0.3)

    def test_tau_half_is_half_the_absolute_error(self):
        self.assertTrue(self.d["tau_half_equals_half_abs_error"])
        c = [c for c in self.d["pinball_cases"] if c["tau"] == 0.5][0]
        self.assertAlmostEqual(c["pinball"], 0.5 * c["abs_error"])

    def test_pinball_is_asymmetric_at_tau_0_9(self):
        self.assertAlmostEqual(self.d["asymmetry_cases"][0]["pinball"], 2.7)
        self.assertAlmostEqual(self.d["asymmetry_ratio_under_over"], 9.0)

    def test_cross_entropy_is_blind_to_distance(self):
        d = self.d
        self.assertTrue(d["ce_equal"])
        self.assertAlmostEqual(d["ce_near"], -math.log(0.10))
        b = d["bins"]
        self.assertEqual(b["near_miss"][b["target_bin"]], b["far_miss"][b["target_bin"]])
        self.assertAlmostEqual(sum(b["near_miss"]), 1.0)
        self.assertAlmostEqual(sum(b["far_miss"]), 1.0)

    def test_pinball_matches_independent_formula(self):
        for c in self.d["pinball_cases"]:
            z, zh, tau = c["observed"], c["forecast"], c["tau"]
            expected = tau * (z - zh) if z >= zh else (1 - tau) * (zh - z)
            self.assertAlmostEqual(c["pinball"], expected)

    def test_figure_distribution_is_self_consistent(self):
        f = self.d["figure"]
        self.assertLess(f["max_quantile_deviation_fraction"], f["tolerance_fraction_of_10_90_range"])
        self.assertEqual(f["shapes"]["quantile"], [4, f["horizon"], len(f["quantile_levels"])])
        self.assertEqual(f["shapes"]["samples"], [4, f["horizon"], f["n_samples"]])
        # quantiles are non-decreasing in level at every step
        for row in f["quantiles"]:
            self.assertEqual(row, sorted(row))

    def test_prose_numbers_appear_in_the_chapter(self):
        for needle in ["0.1\\times2=0.2", "0.5\\times1=0.5", "0.1\\times3=0.3", "0.9\\times3=2.7", "-\\ln0.10\\approx2.303"]:
            self.assertIn(needle, self.text, msg=needle)


class TestW5MixtureCap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = run_script("w5_mixture_cap")
        cls.text = chapter_text("05-")

    def test_shares_sum_to_one_and_budget_is_exact(self):
        self.assertAlmostEqual(sum(self.d["proportional_shares"].values()), 1.0)
        self.assertAlmostEqual(sum(self.d["capped_shares"].values()), 1.0)
        self.assertEqual(sum(self.d["allocation"].values()), self.d["budget"])

    def test_rule_matches_the_papers_form_independently(self):
        # omega_k = min(|D_k| / sum_i |D_i|, eps); p(D_k) = omega_k / sum_i omega_i
        sizes, eps = self.d["sizes"], self.d["epsilon"]
        total = sum(sizes.values())
        omega = {k: min(v / total, eps) for k, v in sizes.items()}
        norm = sum(omega.values())
        for k in sizes:
            self.assertAlmostEqual(self.d["capped_weights_omega"][k], omega[k])
            self.assertAlmostEqual(self.d["capped_shares"][k], omega[k] / norm)
        self.assertAlmostEqual(norm, 0.6)
        self.assertEqual(self.d["paper_epsilon"], 0.001)

    def test_cap_reduces_the_largest_share(self):
        self.assertAlmostEqual(self.d["largest_share_proportional"], 0.8)
        self.assertAlmostEqual(self.d["largest_share_capped"], 2 / 3)
        self.assertEqual(self.d["allocation"]["dataset A"], 666_666_667)

    def test_toy_values_are_labeled_illustrative_and_rule_form_reported(self):
        self.assertEqual(self.d["labels"]["sizes_epsilon_budget"], "illustrative")
        self.assertIn("reported", self.d["labels"]["rule_form"])
        self.assertNotEqual(self.d["epsilon"], self.d["paper_epsilon"])

    def test_paper_epsilon_would_equalize_a_three_dataset_toy(self):
        # the claim made in the chapter: with epsilon = 0.001 every weight is capped
        omega = {k: min(v / sum(self.d["sizes"].values()), 0.001) for k, v in self.d["sizes"].items()}
        self.assertEqual(len(set(omega.values())), 1)

    def test_timeline_overlaps(self):
        tl = self.d["timeline"]
        self.assertEqual(tl["correct"]["train_eval_overlap"], 0.0)
        self.assertEqual(tl["correct"]["stats_eval_overlap"], 0.0)
        self.assertGreater(tl["leaky"]["train_eval_overlap"], 0.0)
        self.assertGreater(tl["leaky"]["stats_eval_overlap"], 0.0)

    def test_prose_numbers_appear_in_the_chapter(self):
        for needle in ["0.80, 0.15 and 0.05", "0.667$, 0.25 and $0.05/0.60\\approx0.083$", "about 667M, 250M and 83M",
                       "\\epsilon=0.001", "\\epsilon=0.4", "sum to 0.60"]:
            self.assertIn(needle, self.text, msg=needle)


class TestW6ReleaseLabels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = run_script("w6_release_labels")
        cls.text = chapter_text("06-")

    def test_no_statement_is_paper_backed(self):
        self.assertEqual(self.d["paper_backed_count"], 0)
        self.assertEqual(self.d["counts_by_type"], {"vendor claim": 4, "documentation": 4})

    def test_no_reconciliation_attempted(self):
        self.assertFalse(self.d["reconciliation_attempted"])
        pairs = [tuple(u["pair"]) for u in self.d["unresolved"]]
        self.assertIn(("S1", "S2"), pairs)

    def test_discrepancy_numbers_appear_in_the_chapter(self):
        for needle in ["330 million", "20 layers", "1280", "16 heads"]:
            self.assertIn(needle, self.text, msg=needle)

    def test_parameter_discrepancy_is_not_reconciled_in_prose(self):
        # No arithmetic that estimates a parameter count from layers and width.
        self.assertIsNone(re.search(r"12\s*(\\times|\*|x)\s*1280", self.text))
        self.assertIn("attempts no reconciliation", self.text)


if __name__ == "__main__":
    unittest.main()
