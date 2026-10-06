"""Semantic-invariant tests for the TSFM addendum's figures (F1-F5).

Each figure script exposes build_model() (the machine-readable layout the
drawing is made from) and draw(). These tests check the invariant each
figure teaches against the worked-example JSON, and check the rendered SVG
for the matching elements, bounds and legible font sizes.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ADD = os.path.join(REPO_ROOT, "workbooks", "addendum-04-05-tsfm")
SRC = os.path.join(ADD, "figures", "source")
REND = os.path.join(ADD, "figures", "rendered")
EX = os.path.join(ADD, "data", "worked-examples")


def load_fig(module_name):
    sys.path.insert(0, SRC)
    spec = importlib.util.spec_from_file_location(module_name, os.path.join(SRC, module_name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def example(name):
    with open(os.path.join(EX, name), encoding="utf-8") as f:
        return json.load(f)


def svg_text(figure_id):
    with open(os.path.join(REND, figure_id + ".svg"), encoding="utf-8") as f:
        return f.read()


class TestGenericSvgHygiene(unittest.TestCase):
    FIGS = ["fig-tokenization-styles", "fig-attention-regimes", "fig-horizon-filling", "fig-output-types", "fig-leakage-timeline"]

    def test_well_formed_and_within_bounds_and_legible(self):
        for fid in self.FIGS:
            root = ET.fromstring(svg_text(fid))
            ns = "{http://www.w3.org/2000/svg}"
            w, h = float(root.get("width")), float(root.get("height"))
            self.assertEqual(w, 620.0, msg=fid)
            for el in root.iter(ns + "text"):
                self.assertGreaterEqual(float(el.get("font-size")), 11.0, msg=f"{fid}: small font")
                x, y = float(el.get("x")), float(el.get("y"))
                self.assertTrue(0 <= x <= w and 0 <= y <= h, msg=f"{fid}: text anchor outside canvas")

    def test_every_rendered_figure_has_a_source_script(self):
        for fid in self.FIGS:
            self.assertTrue(os.path.exists(os.path.join(SRC, fid.replace("-", "_") + ".py")), msg=fid)

    def test_no_internal_names_drawn_into_images(self):
        for fid in self.FIGS:
            text = svg_text(fid)
            self.assertIsNone(re.search(r"src-\d+|\.py\b|\.qmd\b|/mnt/", text), msg=fid)


class TestTokenizationFigure(unittest.TestCase):
    def test_drawn_patch_count_equals_computed_n_p_with_padded_patch(self):
        mod = load_fig("fig_tokenization_styles")
        m = mod.build_model()
        w1 = example("w1_inputs.json")
        self.assertEqual(len(m["patches"]), w1["n_patches_padded"])
        svg = svg_text("fig-tokenization-styles")
        self.assertEqual(len(re.findall(r'<g id="patch-\d+">', svg)), w1["n_patches_padded"])
        # the last patch reaches into padding, the others do not
        pads = [any(i >= m["t_ctx"] for i in w) for w in m["patches"]]
        self.assertEqual(pads, [False] * (len(pads) - 1) + [True])

    def test_bin_ids_drawn_match_worked_example(self):
        w1 = example("w1_inputs.json")
        svg = svg_text("fig-tokenization-styles")
        drawn = [int(x) for x in re.findall(r">id (\d+)<", svg)]
        self.assertEqual(drawn, w1["bin_ids"])

    def test_only_fully_available_lag_tokens_are_drawn(self):
        mod = load_fig("fig_tokenization_styles")
        m = mod.build_model()
        svg = svg_text("fig-tokenization-styles")
        drawn = [int(x) for x in re.findall(r'<g id="lag-token-(\d+)">', svg)]
        self.assertEqual(drawn, [t["t"] for t in m["lag_tokens"]])
        self.assertTrue(all(t - max(m["lags"]) >= 1 for t in drawn))
        self.assertEqual(len(drawn), 8)

    def test_discrete_versus_continuous_contrast_is_stated(self):
        svg = svg_text("fig-tokenization-styles")
        self.assertIn("embedding table", svg)
        self.assertIn("no table", svg)


class TestAttentionRegimesFigure(unittest.TestCase):
    def test_axes_are_generated_from_shape_parameters(self):
        mod = load_fig("fig_attention_regimes")
        m = mod.build_model()
        w2 = example("w2_shapes.json")
        self.assertEqual((m["n_rows"], m["n_cols"]), (w2["n_tgt"], w2["horizon"]))
        self.assertEqual(m["positions"], w2["positions_flattened"])
        svg = svg_text("fig-attention-regimes")
        self.assertEqual(svg.count("16 time steps"), 2)  # time axis labels of the two non-group panels
        self.assertIn(f"{m['positions']} positions", svg)

    def test_flattened_box_spans_all_rows_and_independent_boxes_one_row_each(self):
        mod = load_fig("fig_attention_regimes")
        m = mod.build_model()
        by_id = {p["id"]: p for p in m["panels"]}
        self.assertEqual(by_id["flattened"]["boxes"], [[0, m["n_rows"] - 1]])
        self.assertEqual(by_id["independent"]["boxes"], [[r, r] for r in range(m["n_rows"])])

    def test_output_box_is_not_repeated_here(self):
        svg = svg_text("fig-attention-regimes")
        self.assertNotIn("4 × 16 output", svg)
        self.assertNotIn("64 timestamps", svg)
        # "16 time steps" appears only as an axis label (never inside a caption sentence)
        self.assertEqual(len(re.findall(r">[^<]*16 time steps[^<]*<", svg)), 2)


class TestHorizonFillingFigure(unittest.TestCase):
    def test_pass_blocks_equal_ceiling_of_horizon_over_output_patch(self):
        mod = load_fig("fig_horizon_filling")
        m = mod.build_model()
        svg = svg_text("fig-horizon-filling")
        iterative = [r for r in m["rows"] if r["klass"] == "iterative"]
        for i, r in enumerate(m["rows"]):
            if r["klass"] == "iterative" and r["passes"] <= 8:
                self.assertEqual(len(re.findall(rf'<g id="pass-{i}-\d+">', svg)), r["passes"])
        self.assertEqual([r["passes"] for r in m["rows"]], [2, 8, 256, 1, 1])
        self.assertEqual(iterative[0]["passes"], -(-m["horizon"] // m["p_out"]))

    def test_labeled_pass_counts_are_drawn(self):
        svg = svg_text("fig-horizon-filling")
        for label in ["2 passes", "8 passes", "256 passes"]:
            self.assertIn(f">{label}<", svg)
        self.assertEqual(svg.count(">1 pass<"), 2)

    def test_context_and_horizon_are_adjacent_not_overlapping(self):
        mod = load_fig("fig_horizon_filling")
        m = mod.build_model()
        self.assertEqual(m["t_ctx"] + m["horizon"], 512)
        svg = svg_text("fig-horizon-filling")
        self.assertIn("context  T_ctx = 256", svg)
        self.assertIn("horizon  F = 256", svg)

    def test_placeholder_row_has_no_feedback_and_training_strip_present(self):
        svg = svg_text("fig-horizon-filling")
        self.assertEqual(len(re.findall(r'<g id="placeholder-\d+">', svg)), 8)
        self.assertIn("Training only", svg)
        self.assertIn("Inference only", svg)


class TestOutputTypesFigure(unittest.TestCase):
    def test_shape_labels_match_the_tensor_shapes(self):
        w4 = example("w4_losses.json")["figure"]
        svg = svg_text("fig-output-types")
        self.assertIn(f"shape 4 × {w4['horizon']} × {len(w4['quantile_levels'])}", svg)
        self.assertIn(f"shape 4 × {w4['horizon']} × {w4['n_samples']}", svg)
        self.assertIn(f"n_q = {len(w4['quantile_levels'])}", svg)

    def test_empirical_quantiles_of_sample_paths_match_the_fan(self):
        f = example("w4_losses.json")["figure"]
        for ra, rb in zip(f["quantiles"], f["empirical_quantiles"]):
            spread = ra[-1] - ra[0]
            for a, b in zip(ra, rb):
                self.assertLessEqual(abs(a - b), f["tolerance_fraction_of_10_90_range"] * spread)

    def test_point_panel_is_the_median_and_labeled_so(self):
        f = example("w4_losses.json")["figure"]
        i = f["quantile_levels"].index(0.5)
        self.assertEqual(f["point_median"], [row[i] for row in f["quantiles"]])
        self.assertIn("median of the example", svg_text("fig-output-types"))

    def test_four_panels_drawn_and_no_output_box_repeated(self):
        svg = svg_text("fig-output-types")
        for pid in ["panel-point", "panel-fan", "panel-mixture", "panel-samples"]:
            self.assertIn(f'id="{pid}"', svg)
        self.assertNotIn("64 values", svg)


class TestLeakageTimelineFigure(unittest.TestCase):
    def test_correct_panel_has_no_overlap_and_leaky_panel_does(self):
        mod = load_fig("fig_leakage_timeline")
        m = mod.build_model()
        panels = {p["id"]: p for p in m["panels"]}

        def overlap(a, b):
            return max(0.0, min(a[1], b[1]) - max(a[0], b[0]))

        c, l = panels["correct"], panels["leaky"]
        self.assertEqual(overlap(c["train"], c["eval"]), 0.0)
        self.assertEqual(overlap(c["stats"], c["eval"]), 0.0)
        self.assertGreater(overlap(l["train"], l["eval"]), 0.0)
        self.assertGreater(overlap(l["stats"], l["eval"]), 0.0)

    def test_overlap_highlights_are_drawn_exactly_where_windows_overlap(self):
        svg = svg_text("fig-leakage-timeline")
        self.assertIn('id="leaky-overlap-train"', svg)
        self.assertIn('id="leaky-overlap-stats"', svg)
        self.assertNotIn('id="correct-overlap', svg)

    def test_windows_match_the_worked_example(self):
        w5 = example("w5_mixture_cap.json")["timeline"]
        mod = load_fig("fig_leakage_timeline")
        m = mod.build_model()
        for p in m["panels"]:
            for key in ("train", "stats", "eval"):
                self.assertEqual(p[key], w5[p["id"]][key])


class TestFiguresAreReproducible(unittest.TestCase):
    def test_regeneration_reproduces_the_committed_svg(self):
        for name in ["fig_tokenization_styles", "fig_attention_regimes", "fig_horizon_filling", "fig_output_types", "fig_leakage_timeline"]:
            fid = name.replace("_", "-")
            before = svg_text(fid)
            r = subprocess.run([sys.executable, os.path.join(SRC, name + ".py")], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            self.assertEqual(before, svg_text(fid), msg=f"{fid} changed on regeneration")


if __name__ == "__main__":
    unittest.main()
