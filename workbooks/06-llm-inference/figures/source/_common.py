"""Shared helpers for Workbook 06 figure scripts (not a figure itself:
the leading underscore keeps scripts/build_figures.py from running it).

Every figure loads its numbers from data/worked-examples/*.json (the
worked-example scripts are the numeric source of truth) and its colours
from config/visual-style.yaml. Canvas width 620 px renders at the text
width (6.5 in = 465 pt, 0.75 pt/px), so the 11 px minimum label size is
about 8.25 pt at final size (the style guide asks for at least 8 pt).
"""
import json
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
WB_DIR = os.path.abspath(os.path.join(_HERE, "..", ".."))
REPO_ROOT = os.path.abspath(os.path.join(WB_DIR, "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402,F401

RENDERED_DIR = os.path.join(WB_DIR, "figures", "rendered")
EXAMPLES_DIR = os.path.join(WB_DIR, "data", "worked-examples")
WIDTH = 620
MIN_FONT = 11
TEXT = "#111111"
MUTED = "#444444"
GRID = "#d9d9d9"


def load_example(name):
    with open(os.path.join(EXAMPLES_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def colors():
    c = palette_hex(load_visual_style())
    return {
        "stored": c["stored_information"],   # blue: memory traffic / stored state
        "compute": c["computation"],          # orange: compute
        "green": c["trainable_component"],
        "flag": c["bottleneck_or_failure"],
        "inactive": c["frozen_or_inactive"],
    }


def out_path(figure_id):
    return os.path.join(RENDERED_DIR, f"{figure_id}.svg")


class LogAxis:
    """Map a value on a log10 scale to a pixel coordinate."""

    def __init__(self, lo, hi, p0, p1):
        self.lo, self.hi, self.p0, self.p1 = math.log10(lo), math.log10(hi), p0, p1

    def __call__(self, v):
        return self.p0 + (math.log10(v) - self.lo) / (self.hi - self.lo) * (self.p1 - self.p0)


class LinAxis:
    def __init__(self, lo, hi, p0, p1):
        self.lo, self.hi, self.p0, self.p1 = lo, hi, p0, p1

    def __call__(self, v):
        return self.p0 + (v - self.lo) / (self.hi - self.lo) * (self.p1 - self.p0)


def line(c, x1, y1, x2, y2, color, width=1.0, dash=None, ident=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    i = f' id="{ident}"' if ident else ""
    c.add_raw(f'<line{i} x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{width}"{d}/>')


def circle(c, x, y, r, fill, stroke, ident=None, data=None):
    i = f' id="{ident}"' if ident else ""
    extra = "".join(f' data-{k}="{v}"' for k, v in (data or {}).items())
    c.add_raw(f'<circle{i} cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.2"{extra}/>')
