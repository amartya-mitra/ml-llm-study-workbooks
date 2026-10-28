"""Figure invariants for Workbook 06, Chapter 1.

Each figure's build_model() is checked against the worked-example JSON
(the numeric source of truth) and against the chapter's claims, and each
committed SVG is checked to be exactly what its script draws today, with
the semantic elements (roof lines, points, lanes, chunks) present and
every label at or above the 11 px minimum.
"""
import importlib.util
import json
import os
import re
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WB = os.path.join(REPO_ROOT, "workbooks", "06-llm-inference")
SRC = os.path.join(WB, "figures", "source")
RENDERED = os.path.join(WB, "figures", "rendered")


def load(name):
    # other workbooks also have a figures/source/_common.py; drop any cached one
    sys.modules.pop("_common", None)
    spec = importlib.util.spec_from_file_location(name, os.path.join(SRC, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def svg(fig_id):
    with open(os.path.join(RENDERED, fig_id + ".svg"), encoding="utf-8") as f:
        return f.read()


with open(os.path.join(WB, "data", "worked-examples", "inference_workload_and_metrics.json"), encoding="utf-8") as _f:
    DATA = json.load(_f)


class Common:
    MODULE = None

    @classmethod
    def setUpClass(cls):
        cls.mod = load(cls.MODULE)
        cls.model = cls.mod.build_model()
        cls.text = svg(cls.mod.FIGURE_ID)

    def test_committed_svg_is_current(self):
        self.assertEqual(self.mod.draw(self.model).to_string(), self.text)

    def test_minimum_font_size(self):
        sizes = [float(s) for s in re.findall(r'font-size="([\d.]+)"', self.text)]
        self.assertTrue(sizes)
        self.assertGreaterEqual(min(sizes), 11)

    def test_labelled_schematic_or_idealized(self):
        self.assertRegex(self.text, r"(?i)idealized|synthetic|schematic")


class TestRoofline(Common, unittest.TestCase):
    MODULE = "fig_roofline_prefill_decode"

    def test_roof_and_ridge(self):
        m = self.model
        self.assertEqual(m["peak"], DATA["hardware"]["peak_flops_per_s"])
        self.assertAlmostEqual(m["ridge"], DATA["ridge_flops_per_byte"])
        for ident in ("roof-bandwidth", "roof-compute", "ridge"):
            self.assertIn(f'id="{ident}"', self.text)

    def test_points_lie_on_the_roof_and_classify_correctly(self):
        m = self.model
        for p in m["points"]:
            self.assertAlmostEqual(p["attainable"], min(m["peak"], m["bandwidth"] * p["intensity"]))
            self.assertEqual(p["bound"], "compute" if p["intensity"] >= m["ridge"] else "bandwidth")
            self.assertIn(f'id="pt-{p["id"]}"', self.text)

    def test_decode_linear_moves_right_with_batch(self):
        lin = [p for p in self.model["points"] if p["group"] == "decode-linear"]
        batches = [int(p["id"].split("B")[-1]) for p in lin]
        self.assertEqual([p["intensity"] for p in lin], [float(b) for b in batches])  # = tokens per step
        self.assertEqual(batches, sorted(batches))
        self.assertEqual({p["bound"] for p in lin if int(p["id"].split("B")[-1]) < DATA["ridge_flops_per_byte"]},
                         {"bandwidth"})
        self.assertEqual([p["bound"] for p in lin if p["id"].endswith("B512")], ["compute"])

    def test_decode_attention_fixed_and_left_of_ridge(self):
        att = {p["id"]: p for p in self.model["points"] if p["group"] == "decode-attention"}
        self.assertAlmostEqual(att["decode-attention-gqa"]["intensity"], 4.0)
        self.assertAlmostEqual(att["decode-attention-mha"]["intensity"], 1.0)
        self.assertTrue(all(p["bound"] == "bandwidth" for p in att.values()))
        for rows in DATA["decode"].values():  # same intensity for every batch and context
            self.assertTrue(all(abs(r["attention_intensity"] - 4.0) < 1e-12 for r in rows))

    def test_prefill_right_of_ridge(self):
        pre = [p for p in self.model["points"] if p["group"] == "prefill"]
        self.assertEqual(len(pre), 2)
        self.assertTrue(all(p["bound"] == "compute" for p in pre))


class TestFrontier(Common, unittest.TestCase):
    MODULE = "fig_latency_throughput_frontier"

    def test_points_match_json(self):
        for s in self.model["series"]:
            rows = DATA["decode"][str(s["context"])]
            self.assertEqual(len(s["points"]), len(rows))
            for p, r in zip(s["points"], rows):
                self.assertAlmostEqual(p["step_ms"], r["step_time_per_op_estimate_s"] * 1e3)
                self.assertAlmostEqual(p["tokens_per_s"], r["tokens_per_s_at_per_op_estimate"])
                self.assertEqual(p["fits"], r["fits_illustrative_capacity"])
                m = re.search(rf'<circle id="pt-S{s["context"]}-B{p["batch"]}"[^>]*fill="([^"]+)"[^>]*data-fits="(\w+)"', self.text)
                self.assertIsNotNone(m)
                self.assertEqual(m.group(2), str(p["fits"]).lower())
                self.assertEqual(m.group(1) == "#ffffff", not p["fits"])  # hollow iff it does not fit

    def test_trade_off_monotone_and_chapter_ratio(self):
        for s in self.model["series"]:
            self.assertEqual([p["step_ms"] for p in s["points"]], sorted(p["step_ms"] for p in s["points"]))
            self.assertEqual([p["tokens_per_s"] for p in s["points"]], sorted(p["tokens_per_s"] for p in s["points"]))
        long = {p["batch"]: p for p in [s for s in self.model["series"] if s["context"] == 4096][0]["points"]}
        self.assertEqual(round(long[64]["tokens_per_s"] / long[1]["tokens_per_s"]), 20)  # "about 20-fold"


class TestTimeline(Common, unittest.TestCase):
    MODULE = "fig_request_timeline"

    def test_lanes_and_brackets_match_json(self):
        metrics = {r["id"]: r for r in DATA["requests"]}
        self.assertEqual([l["id"] for l in self.model["lanes"]], [e["id"] for e in DATA["events"]])
        for ln in self.model["lanes"]:
            r = metrics[ln["id"]]
            self.assertAlmostEqual(ln["chunks"][0][0] - ln["send"], r["ttft_client_s"])
            self.assertEqual(sum(n for _, n in ln["chunks"]), r["output_tokens"])
            self.assertEqual(len(ln["server_tokens"]), r["output_tokens"])
            self.assertLessEqual(ln["arrival"], ln["scheduled"])
            self.assertLessEqual(ln["scheduled"], ln["server_tokens"][0])
            for ident in ("lane", "ttft", "queue", "run"):
                self.assertIn(f'id="{ident}-{ln["id"]}"', self.text)

    def test_chunk_token_counts_and_one_token_lane(self):
        lanes = re.findall(r'<g id="lane-(r\d)">(.*?)</g>', self.text, re.DOTALL)
        self.assertEqual(len(lanes), 4)
        by = {e["id"]: e for e in DATA["events"]}
        for rid, body in lanes:
            tokens = [int(t) for t in re.findall(r'data-tokens="(\d+)"', body)]
            self.assertEqual(tokens, [n for _, n in by[rid]["client_chunks"]])
        self.assertIn("chunk with 2 tokens", self.text)
        self.assertIn("1 output token: no gaps", self.text)


if __name__ == "__main__":
    unittest.main()
