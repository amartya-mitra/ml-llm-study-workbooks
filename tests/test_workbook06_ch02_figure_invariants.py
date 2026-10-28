"""Figure invariants for Workbook 06, Chapter 2 (block table, prefix tree).

Each figure's build_model() is checked against the worked-example JSON and
the block-sharing rules, and each committed SVG is checked to be exactly
what its script draws today, with the semantic elements present and every
label at or above the 11 px minimum.
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

with open(os.path.join(WB, "data", "worked-examples", "kv_cache_memory.json"), encoding="utf-8") as _f:
    DATA = json.load(_f)


def load(name):
    sys.modules.pop("_common", None)   # other workbooks also have a figures/source/_common.py
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

    def test_labelled_toy(self):
        self.assertIn("toy", self.text)


class TestBlockTable(Common, unittest.TestCase):
    MODULE = "fig_block_table"

    def test_refs_equal_table_references(self):
        refs = {}
        for t in self.model["tables"].values():
            for b in t:
                refs[b] = refs.get(b, 0) + 1
        for p in self.model["physical"]:
            self.assertEqual(p["ref"], refs.get(p["id"], 0))
            m = re.search(rf'<rect id="phys-{p["id"]}"[^>]*data-ref="(\d+)" data-filled="(\d+)" data-state="(\w+)"', self.text)
            self.assertIsNotNone(m)
            self.assertEqual((int(m.group(1)), int(m.group(2)), m.group(3)), (p["ref"], p["filled"], p["state"]))

    def test_shared_prefix_and_private_tails(self):
        t = self.model["tables"]
        self.assertEqual(t["R1"][:2], t["R2"][:2])
        self.assertNotEqual(t["R1"][-1], t["R2"][-1])
        shared = {p["id"] for p in self.model["physical"] if p["state"] == "shared"}
        self.assertEqual(shared, set(t["R1"][:2]))
        for p in self.model["physical"]:
            self.assertLessEqual(p["filled"], self.model["block_tokens"])
            if p["state"] == "free":
                self.assertEqual(p["filled"], 0)

    def test_counts_match_snapshot(self):
        snap = DATA["lifecycle"]["snapshots"][0]
        for k, v in self.model["counts"].items():
            self.assertEqual(v, snap[k])
        self.assertIn(f"logical references {snap['logical_references']}", self.text)
        self.assertIn(f"live tokens across both requests {snap['live_tokens']}", self.text)
        for req, table in self.model["tables"].items():
            for li, pb in enumerate(table):
                self.assertIn(f'id="log-{req}-{li}"', self.text)
                self.assertIn(f'data-physical="{pb}"', self.text)


class TestPrefixTree(Common, unittest.TestCase):
    MODULE = "fig_prefix_tree"

    def test_nodes_and_evictable(self):
        ev = set(self.model["evict_order"])
        for n in self.model["nodes"]:
            m = re.search(rf'<rect id="node-{n["id"]}"[^>]*data-ref="(\d+)" data-evictable="(\w+)"', self.text)
            self.assertIsNotNone(m)
            self.assertEqual(int(m.group(1)), n["ref"])
            self.assertEqual(m.group(2) == "true", n["id"] in ev)
            self.assertEqual(n["id"] in ev, n["leaf"] and n["ref"] == 0)

    def test_hash_rows_mark_only_reusable_full_blocks(self):
        blk = self.model["block"]
        for r in self.model["requests"][1:]:
            reuse = self.model["hash_reusable"][r["name"]]
            for b in range(0, len(r["tokens"]), blk):
                m = re.search(rf'<rect id="hash-{r["name"]}-{b // blk}"[^>]*data-hit="(\w+)"', self.text)
                self.assertIsNotNone(m)
                self.assertEqual(m.group(1) == "true", b + blk <= reuse)
            self.assertIn(f"reused: {reuse} tokens by hashing vs {self.model['radix_matched'][r['name']]} in the tree",
                          self.text)


if __name__ == "__main__":
    unittest.main()
