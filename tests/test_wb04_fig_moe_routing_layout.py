"""Layout test for Workbook 04 Figure 17 (fig-moe-routing-parallelism).

No routing connector may cross the "router" label or either "device N"
label. The check parses the rendered SVG, estimates each label's bounding
box from its font size, and tests every <line> connector against it. It
also pins the semantic content (six tokens, expert loads, two-stage
routing, highlight) so a layout fix cannot silently change the figure's
meaning, and proves the checker rejects the previously published geometry.
"""
import os
import unittest
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SVG = os.path.join(REPO_ROOT, "workbooks", "04-llm-architecture", "figures",
                   "rendered", "fig-moe-routing-parallelism.svg")
NS = "{http://www.w3.org/2000/svg}"
MARGIN = 4.0  # clearance required between a connector and a label box

# Connector geometry published before the router-label fix (x1, y1, x2, y2):
# each dispatch arrow ran straight from its token to its expert, so t4->E2
# passed through the router box and its label.
LEGACY_T4_TO_E2 = (450.0, 83.0, 300.0, 212.0)
LEGACY_ROUTER_LABEL = (410.0, 134.0, 16.0, "middle", "router")


def _texts(root):
    return [(float(t.get("x")), float(t.get("y")), float(t.get("font-size")),
             t.get("text-anchor"), (t.text or "")) for t in root.iter(NS + "text")]


def _label_box(x, y, size, anchor, text):
    # Conservative width estimate for a sans-serif label.
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
        cls.texts = _texts(cls.root)

    def _label(self, name):
        found = [t for t in self.texts if t[4] == name]
        self.assertEqual(len(found), 1, msg=f"expected exactly one {name!r} label")
        return found[0]

    def test_router_label_clear_of_all_connectors(self):
        box = _label_box(*self._label("router"))
        for seg in self.lines:
            self.assertFalse(_segment_hits_box(*seg, box, MARGIN),
                             msg=f"connector {seg} intersects router label box {box}")

    def test_no_connector_enters_the_router_box(self):
        rects = [r for r in self.root.iter(NS + "rect") if r.get("fill") != "#ffffff"]
        label = self._label("router")
        # the router rectangle is the one whose x-range contains the label
        router = [r for r in rects
                  if float(r.get("x")) < label[0] < float(r.get("x")) + float(r.get("width"))
                  and float(r.get("y")) < label[1] < float(r.get("y")) + float(r.get("height"))]
        self.assertEqual(len(router), 1)
        rx, ry = float(router[0].get("x")), float(router[0].get("y"))
        rw, rh = float(router[0].get("width")), float(router[0].get("height"))
        inner = (rx + 1, ry + 1, rx + rw - 1, ry + rh - 1)
        for seg in self.lines:
            x1, y1, x2, y2 = seg
            for i in range(0, 401):
                t = i / 400
                px, py = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
                self.assertFalse(inner[0] < px < inner[2] and inner[1] < py < inner[3],
                                 msg=f"connector {seg} passes through the router box")

    def test_device_labels_clear_of_all_connectors(self):
        for name in ("device 1", "device 2"):
            box = _label_box(*self._label(name))
            for seg in self.lines:
                self.assertFalse(_segment_hits_box(*seg, box, MARGIN),
                                 msg=f"connector {seg} intersects {name!r} box {box}")

    def test_device_labels_sit_inside_boundaries_below_experts(self):
        rects = [r for r in self.root.iter(NS + "rect") if r.get("stroke-dasharray")]
        self.assertEqual(len(rects), 2)
        for rect, name in zip(sorted(rects, key=lambda r: float(r.get("x"))), ("device 1", "device 2")):
            rx, ry = float(rect.get("x")), float(rect.get("y"))
            rw, rh = float(rect.get("width")), float(rect.get("height"))
            x, y, size, _, _ = self._label(name)
            self.assertTrue(rx < x < rx + rw)
            self.assertTrue(ry + 80 < y - 0.85 * size and y + 0.25 * size < ry + rh,
                            msg="label must sit between the experts (end 80 below top) and the boundary bottom")

    def test_routing_is_two_stage_and_assignments_unchanged(self):
        # first six connectors: token -> router top edge; last six: router bottom edge -> expert
        up, down = self.lines[:6], self.lines[6:]
        self.assertEqual(len(self.lines), 12)
        self.assertEqual(len({s[2] for s in up}), 6, msg="six distinct anchors on the router top edge")
        self.assertEqual(len({s[1] for s in up}), 1)
        self.assertEqual([s[0] for s in down], [s[2] for s in up],
                         msg="each token leaves the router at the x where it entered")
        # expert x targets: t1,t2,t3 -> E1 ; t4 -> E2 ; t5 -> E3 ; t6 -> E4
        targets = [s[2] for s in down]
        self.assertEqual(targets[0], targets[1])
        self.assertEqual(targets[1], targets[2])
        self.assertEqual(len(set(targets)), 4)
        self.assertEqual(targets, sorted(targets))

    def test_semantic_content_unchanged(self):
        texts = [t[4] for t in self.texts]
        for token in (f"t{i}" for i in range(1, 7)):
            self.assertIn(token, texts)
        for expert in ("E1", "E2", "E3", "E4"):
            self.assertIn(expert, texts)
        load_labels = [t for t in texts if t.endswith("token(s)")]
        self.assertEqual(sorted(load_labels), ["1 token(s)", "1 token(s)", "1 token(s)", "3 token(s)"])
        # E1 carries the 3-token load and the overloaded (red) highlight
        e1 = self._label("E1")
        three = [t for t in self.texts if t[4] == "3 token(s)"][0]
        self.assertAlmostEqual(e1[0], three[0])
        red = [r for r in self.root.iter(NS + "rect") if r.get("stroke") == "#D55E00"]
        self.assertTrue(len(red) >= 1, msg="overloaded expert highlight (red stroke) missing")

    def test_checker_rejects_the_previously_published_geometry(self):
        box = _label_box(*LEGACY_ROUTER_LABEL)
        self.assertTrue(_segment_hits_box(*LEGACY_T4_TO_E2, box, MARGIN),
                        msg="the old t4->E2 connector must be flagged as crossing the router label")


if __name__ == "__main__":
    unittest.main()
