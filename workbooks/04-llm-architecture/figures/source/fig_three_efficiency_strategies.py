"""Chapter 4 figure: three different efficiency strategies, shown as
three independent axes rather than one continuum.

What to notice: panel 1 changes WHICH positions are scored (still full
per-head K/V, just fewer pairs); panel 2 changes WHAT is stored per
retained position (a compressed joint latent instead of full K/V);
panel 3 replaces the growing history entirely with a fixed-size state.
These are different mechanisms solving different problems, not three
strengths of the same knob -- panel 3 is a taxonomy label only, not a
mechanism diagram (no SSM/recurrence math is shown).

Run: python3 workbooks/04-llm-architecture/figures/source/fig_three_efficiency_strategies.py
Output: figures/rendered/fig-three-efficiency-strategies.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-three-efficiency-strategies"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

# Full-width (6.5in) embed, W=960 -> 1 unit = 6.5*72/960 = 0.4875pt.
# Need ~18.5 units for a 9pt essential label.
TITLE_SIZE = 19
LABEL_SIZE = 17
SMALL_SIZE = 15


def panel_title(canvas, x0, panel_w, title):
    canvas.add_text(x0 + panel_w / 2, 24, title, size=TITLE_SIZE, weight="bold", anchor="middle")


def panel1_connectivity(canvas, x0, panel_w, colors):
    """Full vs. local/sparse connectivity: two small grids."""
    blue = colors["stored_information"]
    n = 6
    cell = 20
    gap_between = 30

    def grid(gx, allowed_fn, label):
        for i in range(n):
            for j in range(n):
                x, y = gx + j * cell, 60 + i * cell
                fill = blue if allowed_fn(i, j) else "#eeeeee"
                canvas.add_rect(x, y, cell - 2, cell - 2, fill=fill, stroke="#999999", stroke_width=0.75, rx=1)
        canvas.add_text(gx + (n * cell) / 2, 60 + n * cell + 20, label, size=SMALL_SIZE, anchor="middle")

    gx1 = x0 + 10
    grid(gx1, lambda i, j: j <= i, "full")
    gx2 = x0 + 10 + n * cell + 30
    grid(gx2, lambda i, j: j <= i and (i - j) < 3, "local/sparse")

    canvas.add_text(x0 + panel_w / 2, 60 + n * cell + 45, "same # heads scored, fewer pairs", size=SMALL_SIZE, color="#555555", anchor="middle")


def panel2_representation(canvas, x0, panel_w, colors):
    """Full K/V heads vs. a compressed latent, per retained token."""
    blue = colors["stored_information"]
    orange = colors["computation"]
    cx = x0 + panel_w / 2

    canvas.add_text(cx, 60, "one retained token", size=SMALL_SIZE, anchor="middle", color="#555555")

    # Full K/V: 4 small boxes.
    fx = x0 + 20
    for i in range(4):
        canvas.add_rect(fx + i * 26, 80, 22, 22, fill=blue, stroke="#333333", stroke_width=1.2, rx=3)
    canvas.add_text(fx + 2 * 26 - 13, 122, "full: K/V per head", size=SMALL_SIZE, anchor="middle")

    # Compressed latent: one box.
    lx = x0 + panel_w - 20 - 40
    canvas.add_rect(lx, 80, 40, 22, fill=orange, stroke="#333333", stroke_width=1.5, rx=5)
    canvas.add_text(lx + 20, 122, "MLA: one latent", size=SMALL_SIZE, anchor="middle")

    canvas.add_text(cx, 150, "different WHAT is stored, not fewer pairs scored", size=SMALL_SIZE, color="#555555", anchor="middle")


def panel3_state(canvas, x0, panel_w, colors):
    """Growing token history vs. fixed-size/recurrent state."""
    blue = colors["stored_information"]
    gray = colors["frozen_or_inactive"]
    cx = x0 + panel_w / 2

    # Growing history: increasing bars.
    gx = x0 + 25
    for i, h in enumerate([14, 22, 30, 38]):
        canvas.add_rect(gx + i * 22, 130 - h, 16, h, fill=blue, stroke="#333333", stroke_width=1)
    canvas.add_text(gx + 1.5 * 22, 150, "cache grows with S", size=SMALL_SIZE, anchor="middle")

    # Fixed-size state: constant box repeated.
    fx = x0 + panel_w - 25 - 4 * 22
    for i in range(4):
        canvas.add_rect(fx + i * 22, 130 - 22, 16, 22, fill=gray, stroke="#333333", stroke_width=1)
    canvas.add_text(fx + 1.5 * 22, 150, "state stays fixed size", size=SMALL_SIZE, anchor="middle")

    canvas.add_text(cx, 178, "taxonomy only -- mechanism not shown", size=SMALL_SIZE, color="#555555", anchor="middle")


def main():
    style = load_visual_style()
    colors = palette_hex(style)

    W = 960
    canvas = SVGCanvas(width=W, height=1, title="Three efficiency strategies: different axes, not one continuum")

    panel_w = W / 3 - 10
    gap = 15

    panel_title(canvas, 0, panel_w, "1. Fewer positions")
    panel1_connectivity(canvas, 0, panel_w, colors)

    panel_title(canvas, panel_w + gap, panel_w, "2. Smaller per-token state")
    panel2_representation(canvas, panel_w + gap, panel_w, colors)

    panel_title(canvas, 2 * (panel_w + gap), panel_w, "3. Replace growing state")
    panel3_state(canvas, 2 * (panel_w + gap), panel_w, colors)

    legend_y = 250
    blue = colors["stored_information"]
    orange = colors["computation"]
    gray = colors["frozen_or_inactive"]
    canvas.add_rect(20, legend_y, 16, 16, fill=blue, rx=2)
    canvas.add_text(44, legend_y + 13, "scored / stored per-head", size=SMALL_SIZE)
    canvas.add_rect(300, legend_y, 16, 16, fill=orange, rx=2)
    canvas.add_text(324, legend_y + 13, "compressed / computed", size=SMALL_SIZE)
    canvas.add_rect(560, legend_y, 16, 16, fill=gray, rx=2)
    canvas.add_text(584, legend_y + 13, "fixed-size / inactive-growth", size=SMALL_SIZE)

    canvas.height = legend_y + 40
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
