"""Shared helpers for the addendum's figure generators.

Not a figure itself (leading underscore: scripts/build_figures.py skips it).
Every figure loads its numbers from data/worked-examples/*.json (the
worked-example scripts are the numeric source of truth) and its colors
from config/visual-style.yaml.
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
WB_DIR = os.path.abspath(os.path.join(_HERE, "..", ".."))
REPO_ROOT = os.path.abspath(os.path.join(WB_DIR, "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402,F401

RENDERED_DIR = os.path.join(WB_DIR, "figures", "rendered")
EXAMPLES_DIR = os.path.join(WB_DIR, "data", "worked-examples")

WIDTH = 620  # px; 620 px = 465 pt, which fits the 6.5 in text block at 0.75 pt/px
MIN_FONT = 11  # px; = 8.25 pt at final size (config/visual-style.yaml asks for >= 8 pt)

TEXT = "#111111"
MUTED = "#444444"


def load_example(name):
    with open(os.path.join(EXAMPLES_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def colors():
    c = palette_hex(load_visual_style())
    return {
        "observed": c["stored_information"],      # blue: observed / context values
        "forecast": c["computation"],              # orange: forecast / horizon
        "trainable": c["trainable_component"],     # green: learned projection
        "flag": c["bottleneck_or_failure"],        # red: problem / overlap
        "inactive": c["frozen_or_inactive"],       # gray: placeholder / inactive
    }


def out_path(figure_id):
    return os.path.join(RENDERED_DIR, f"{figure_id}.svg")
