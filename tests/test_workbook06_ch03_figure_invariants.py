"""Figure invariants for Workbook 06, Chapter 3 (schedule timelines,
prefill-decode interference).

Each figure's build_model() is checked against the worked-example JSON and
the scheduling rules, and each committed SVG is checked to be exactly what
its script draws today, with semantic elements present and every label at
or above the 11 px minimum.
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

with open(os.path.join(WB, "data", "worked-examples", "serving_schedules.json"), encoding="utf-8") as _f:
    DATA = json.load(_f)


def load(name):
    sys.modules.pop("_common", None)
    spec = importlib.util.spec_from_file_location(name, os.path.join(SRC, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Common:
    MODULE = None

    @classmethod
    def setUpClass(cls):
        cls.mod = load(cls.MODULE)
        cls.model = cls.mod.build_model()
        with open(os.path.join(RENDERED, cls.mod.FIGURE_ID + ".svg"), encoding="utf-8") as f:
            cls.text = f.read()

    def test_committed_svg_is_current(self):
        self.assertEqual(self.mod.draw(self.model).to_string(), self.text)

    def test_minimum_font_size(self):
        sizes = [float(s) for s in re.findall(r'font-size="([\d.]+)"', self.text)]
        self.assertTrue(sizes)
        self.assertGreaterEqual(min(sizes), 11)

    def test_labelled_illustrative(self):
        self.assertRegex(self.text, r"(?i)illustrative|synthetic")


class TestTimelines(Common, unittest.TestCase):
    MODULE = "fig_schedule_timelines"

    def test_every_processed_token_group_is_drawn(self):
        for p in self.model["panels"]:
            body = re.search(rf'<g id="panel-{p["key"]}">(.*?)</g>', self.text, re.S).group(1)
            bars = re.findall(r'data-kind="(\w+)" data-start="([\d.]+)" data-end="([\d.]+)" data-req="(\w)"', body)
            pol = DATA["policies"][p["key"]]
            expected = []
            for group in ("steps", "prefill_steps", "decode_steps"):
                for s in pol.get(group, []):
                    for w in s["work"]:
                        expected.append((w["kind"], s["start"], s["end"], w["id"]))
            self.assertEqual(sorted((k, float(a), float(b), r) for k, a, b, r in bars),
                             sorted((k, float(a), float(b), r) for k, a, b, r in expected))
            dots = re.findall(r'data-t="([\d.]+)"', body)
            self.assertEqual(len(dots), sum(m["output"] for m in pol["requests"]))

    def test_arrivals_precede_bars_and_transfers_only_when_disaggregated(self):
        for p in self.model["panels"]:
            for s in p["segments"]:
                self.assertGreaterEqual(s["start"] + 1e-6, self.model["arrivals"][s["id"]])
            self.assertEqual(bool(p["transfers"]), p["key"] == "disaggregated")
        self.assertEqual(len(re.findall(r'id="xfer-', self.text)), 4)
        self.assertEqual(len(re.findall(r'id="arr-', self.text)), 16)


class TestInterference(Common, unittest.TestCase):
    MODULE = "fig_prefill_decode_interference"

    def test_stacks_sum_to_step_duration(self):
        for p in self.model["panels"]:
            for s in p["steps"]:
                self.assertAlmostEqual(s["t0"] + s["prefill_ms"] + s["decode_ms"], s["duration"], places=6)
            body = re.search(rf'<g id="panel-{p["key"]}">(.*?)</g>', self.text, re.S).group(1)
            parts = re.findall(r'data-step="(\d+)" data-part="(\w+)" data-ms="([\d.]+)"', body)
            per_step = {}
            for i, _, ms in parts:
                per_step[int(i)] = per_step.get(int(i), 0) + float(ms)
            for i, s in enumerate(p["steps"]):
                self.assertAlmostEqual(per_step[i], s["duration"], places=4)

    def test_chunking_lowers_the_longest_decode_carrying_step(self):
        longest = {p["key"]: max(s["duration"] for s in p["steps"] if s["has_decode"]) for p in self.model["panels"]}
        self.assertLess(longest["chunked"], longest["continuous"])
        self.assertAlmostEqual(longest["continuous"], DATA["policies"]["continuous"]["aggregate"]["worst_gap_ms"], places=5)


if __name__ == "__main__":
    unittest.main()
