"""Tests for figures/rendered/*.svg.

These formalize a check that was previously done ad hoc (by hand, once,
during Stage 6/7 of the original bootstrap): every rendered figure must
be well-formed SVG, and every shape/text element must fit inside the
canvas the figure itself declares. A hardcoded canvas width or height is
a standing clipping risk if a figure script is edited later without
rerunning this check by hand — this test makes that check automatic.

Note this is a *necessary, not sufficient* check: it catches elements
that fall outside the canvas, but it cannot catch elements that overlap
each other while still being individually in-bounds (that class of bug
needs an actual rendered-page visual inspection — see AGENTS.md and
reports/bootstrap_report.md's "Update: rendering toolchain installed"
section for a worked example of five such bugs it would have missed).
"""
import glob
import os
import re
import unittest
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

CANVAS_RE = re.compile(r'width="(\d+(?:\.\d+)?)" height="(\d+(?:\.\d+)?)"')
RECT_RE = re.compile(
    r'<rect x="(-?\d+(?:\.\d+)?)" y="(-?\d+(?:\.\d+)?)" '
    r'width="(-?\d+(?:\.\d+)?)" height="(-?\d+(?:\.\d+)?)"'
)
TEXT_RE = re.compile(r'<text x="(-?\d+(?:\.\d+)?)" y="(-?\d+(?:\.\d+)?)"')


def find_rendered_svgs():
    # Recursive: covers the project-wide figures/rendered/ directory and
    # any per-workbook figures/rendered/ directory (see build_figures.py).
    return sorted(glob.glob(os.path.join(REPO_ROOT, "**", "figures", "rendered", "*.svg"), recursive=True))


class TestFigures(unittest.TestCase):
    def test_at_least_one_figure_exists(self):
        self.assertGreater(len(find_rendered_svgs()), 0, "no rendered figures found under figures/rendered/")

    def test_every_figure_is_well_formed_xml(self):
        for path in find_rendered_svgs():
            with self.subTest(path=path):
                ET.parse(path)  # raises ParseError on malformed XML

    def test_no_shape_or_text_exceeds_the_declared_canvas(self):
        for path in find_rendered_svgs():
            with self.subTest(path=path):
                with open(path, encoding="utf-8") as f:
                    svg = f.read()
                canvas_match = CANVAS_RE.search(svg)
                self.assertIsNotNone(canvas_match, f"{path}: could not find a width/height on the <svg> root")
                width, height = float(canvas_match.group(1)), float(canvas_match.group(2))

                for x, y, w, h in (map(float, m.groups()) for m in RECT_RE.finditer(svg)):
                    self.assertTrue(
                        x >= 0 and y >= 0 and x + w <= width and y + h <= height,
                        msg=f"{path}: <rect> at ({x},{y},{w},{h}) exceeds canvas {width}x{height}",
                    )
                for x, y in (map(float, m.groups()) for m in TEXT_RE.finditer(svg)):
                    self.assertTrue(
                        0 <= x <= width and 0 <= y <= height,
                        msg=f"{path}: <text> at ({x},{y}) exceeds canvas {width}x{height}",
                    )


if __name__ == "__main__":
    unittest.main()
