"""Layout test for Workbook 04 Figure 17 (fig-moe-routing-parallelism).

The "device 1" / "device 2" labels must not be crossed by any routing arrow.
The check parses the rendered SVG, estimates each label's bounding box from
its font size, and tests every <line> arrow segment against it. It also pins
the semantic content (six tokens, routing assignment, expert loads) so the
layout fix cannot silently change the figure's meaning.
"""
import os
import re
import unittest
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SVG = os.path.join(REPO_ROOT, "workbooks", "04-llm-architecture", "figures",
                   "rendered", "fig-moe-routing-parallelism.svg")
NS = "{http://www.w3.org/2000/svg}"
MARGIN = 4.0  # clearance required between an arrow and a label box


def _texts(root):
    return [(float(t.get("x")), float(t.get("y")), float(t.get("font-size")),
             t.get("text-anchor"), (t.text or "")) for t in root.iter(NS + "text")]


def _label_box(x, y, size, anchor, text):
    # Conservative width estimate for a bold sans-serif label.
    width = 0.62 * size * len(text)
    left = x - width / 2 if anchor == "middle" else x
    return (left, y - 0.85 * size, left + width, y + 0.25 * size)


def _segment_hits_box(x1, y1, x2, y2, box, pad):
    bx0, by0, bx1, by1 = box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad
    steps = 400
    for i in range(steps + 1):
        t = i / steps
        px, py = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
        if bx0 <= px <= bx1 and by0 <= py <= by1:
            return True
    return False


class Figure17LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ET.parse(SVG).getroot()
        cls.lines = [tuple(float(l.get(k)) for k in ("x1", "y1", "x2", "y2"))
                     for l in cls.root.iter(NS + "line")]

    def test_device_labels_clear_of_all_arrows(self):
        labels = [t for t in _texts(self.root) if re.fullmatch(r"device [12]", t[4])]
        self.assertEqual(sorted(t[4] for t in labels), ["device 1", "device 2"])
        for x, y, size, anchor, text in labels:
            box = _label_box(x, y, size, anchor, text)
            for seg in self.lines:
                self.assertFalse(_segment_hits_box(*seg, box, MARGIN),
                                 msg=f"arrow {seg} intersects label {text!r} box {box}")

    def test_labels_sit_inside_dashed_boundaries_above_experts(self):
        rects = [r for r in self.root.iter(NS + "rect") if r.get("stroke-dasharray")]
        self.assertEqual(len(rects), 2)
        labels = {t[4]: t for t in _texts(self.root) if t[4] in ("device 1", "device 2")}
        for rect, name in zip(sorted(rects, key=lambda r: float(r.get("x"))), ("device 1", "device 2")):
            rx, ry, rw = float(rect.get("x")), float(rect.get("y")), float(rect.get("width"))
            x, y, size, _, _ = labels[name]
            self.assertTrue(rx < x < rx + rw)
            self.assertTrue(ry < y - 0.85 * size and y + 0.25 * size < ry + 30,
                            msg="label must sit between the boundary top and the expert row")

    def test_semantic_content_unchanged(self):
        texts = [t[4] for t in _texts(self.root)]
        for token in (f"t{i}" for i in range(1, 7)):
            self.assertIn(token, texts)
        for expert in ("E1", "E2", "E3", "E4"):
            self.assertIn(expert, texts)
        self.assertEqual(sorted(t for t in texts if t.endswith("token(s)")),
                         ["1 token(s)", "1 token(s)", "1 token(s)", "3 token(s)"])
        # six token->router arrows, six dispatch arrows
        self.assertEqual(len(self.lines), 12)
        red = [r for r in self.root.iter(NS + "rect") if r.get("stroke") == "#D55E00"]
        self.assertTrue(len(red) >= 1, msg="overloaded expert highlight (red stroke) missing")


if __name__ == "__main__":
    unittest.main()
