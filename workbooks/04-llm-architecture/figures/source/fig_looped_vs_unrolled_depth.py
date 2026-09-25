"""Chapter 8 figure: looped vs. unrolled depth, three panels.

What to notice: panel 1 and panel 2 use the SAME 22 distinct blocks
(same color/pattern) -- panel 2 just runs them twice. Panel 3's
unrolled view shows 44 block applications, but applications 1-22 and
23-44 share the same underlying weight identity (same color) --
distinct parameters (22) and block applications (44) are different
counts. The small cache icon under each application in panel 3 is
schematic: it does NOT assert that panel 3's applications share one
cache -- see the chapter text for the caveat that pass-specific K/V
may still be required.

Run: python3 workbooks/04-llm-architecture/figures/source/fig_looped_vs_unrolled_depth.py
Output: figures/rendered/fig-looped-vs-unrolled-depth.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-looped-vs-unrolled-depth"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

# Full-width (6.5in) embed, W=1080 -> 1 unit = 6.5*72/1080 = 0.4333pt.
# Need ~20.8 units for a 9pt essential label.
TITLE_SIZE = 18
LABEL_SIZE = 16
SMALL_SIZE = 15
TINY_SIZE = 13


def block_stack(canvas, x0, y0, n, box_w, box_h, gap, fill):
    for i in range(n):
        canvas.add_rect(x0, y0 + i * (box_h + gap), box_w, box_h, fill=fill, stroke="#333333", stroke_width=1.3, rx=4)
    return y0 + n * (box_h + gap) - gap


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    blue = colors["stored_information"]
    orange = colors["computation"]

    W = 1080
    panel_w = W / 3 - 10
    canvas = SVGCanvas(width=W, height=1, title="Looped vs. unrolled depth")

    n_shown = 4  # schematic stand-in for 22 distinct blocks
    box_w, box_h, gap = 110, 18, 5

    # Panel 1: single pass.
    x0 = 30
    canvas.add_text(x0 + panel_w / 2 - 20, 22, "22 distinct blocks,", size=TITLE_SIZE, weight="bold", anchor="middle")
    canvas.add_text(x0 + panel_w / 2 - 20, 40, "single pass", size=TITLE_SIZE, weight="bold", anchor="middle")
    bottom1 = block_stack(canvas, x0, 55, n_shown, box_w, box_h, gap, blue)
    canvas.add_text(x0 + box_w / 2, bottom1 + 18, "x22 distinct blocks", size=SMALL_SIZE, color="#555555", anchor="middle")
    canvas.add_text(x0 + box_w / 2, bottom1 + 36, "22 block applications", size=SMALL_SIZE, anchor="middle")

    # Panel 2: looped, 2 passes.
    x1 = x0 + panel_w + 20
    canvas.add_text(x1 + panel_w / 2 - 20, 22, "Same 22 blocks,", size=TITLE_SIZE, weight="bold", anchor="middle")
    canvas.add_text(x1 + panel_w / 2 - 20, 40, "looped (2 passes)", size=TITLE_SIZE, weight="bold", anchor="middle")
    bottom2 = block_stack(canvas, x1, 55, n_shown, box_w, box_h, gap, blue)
    # Return arrow from bottom back to top.
    arrow_x = x1 + box_w + 25
    canvas.add_arrow(arrow_x, bottom2, arrow_x, 55, color="#555555", stroke_width=2)
    canvas.add_raw(f'<line x1="{x1+box_w}" y1="{bottom2}" x2="{arrow_x}" y2="{bottom2}" stroke="#555555" stroke-width="2"/>')
    canvas.add_raw(f'<line x1="{x1+box_w}" y1="55" x2="{arrow_x}" y2="55" stroke="#555555" stroke-width="2"/>')
    canvas.add_text(arrow_x + 10, (bottom2 + 55) / 2 + 5, "pass 2:", size=TINY_SIZE, color="#555555")
    canvas.add_text(arrow_x + 10, (bottom2 + 55) / 2 + 20, "same weights,", size=TINY_SIZE, color="#555555")
    canvas.add_text(arrow_x + 10, (bottom2 + 55) / 2 + 35, "hidden state evolves", size=TINY_SIZE, color="#555555")
    canvas.add_text(x1 + box_w / 2, bottom2 + 18, "x22 distinct blocks", size=SMALL_SIZE, color="#555555", anchor="middle")
    canvas.add_text(x1 + box_w / 2, bottom2 + 36, "44 block applications", size=SMALL_SIZE, anchor="middle")

    # Panel 3: unrolled view.
    x2 = x1 + panel_w + 40
    canvas.add_text(x2 + panel_w / 2 - 10, 22, "Unrolled view:", size=TITLE_SIZE, weight="bold", anchor="middle")
    canvas.add_text(x2 + panel_w / 2 - 10, 40, "44 block applications", size=TITLE_SIZE, weight="bold", anchor="middle")
    small_box_w = 70
    row_y1 = 55
    for i in range(n_shown):
        y = row_y1 + i * (box_h + gap)
        canvas.add_rect(x2, y, small_box_w, box_h, fill=blue, stroke="#333333", stroke_width=1.3, rx=4)
        canvas.add_rect(x2 + small_box_w + 8, y, 14, box_h, fill=orange, stroke="#333333", stroke_width=1, rx=2)
    canvas.add_text(x2 + small_box_w / 2, row_y1 + n_shown * (box_h + gap) + 12, "pass 1 (x22)", size=TINY_SIZE, color="#555555", anchor="middle")

    row2_top = row_y1 + n_shown * (box_h + gap) + 24
    for i in range(n_shown):
        y = row2_top + i * (box_h + gap)
        canvas.add_rect(x2, y, small_box_w, box_h, fill=blue, stroke="#333333", stroke_width=1.3, rx=4)
        canvas.add_rect(x2 + small_box_w + 8, y, 14, box_h, fill=orange, stroke="#333333", stroke_width=1, rx=2)
    canvas.add_text(x2 + small_box_w / 2, row2_top + n_shown * (box_h + gap) + 12, "pass 2 (x22, same weights)", size=TINY_SIZE, color="#555555", anchor="middle")

    bottom3 = row2_top + n_shown * (box_h + gap) + 24

    legend_y = max(bottom1 + 50, bottom2 + 90, bottom3) + 10
    canvas.add_rect(20, legend_y, 16, 16, fill=blue, rx=2)
    canvas.add_text(44, legend_y + 13, "distinct weight identity (same shade = same weights)", size=SMALL_SIZE)
    canvas.add_rect(20, legend_y + 26, 16, 16, fill=orange, rx=2)
    canvas.add_text(44, legend_y + 39, "pass-specific cache/state icon (schematic -- not asserted shared)", size=SMALL_SIZE)

    canvas.height = legend_y + 60
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
