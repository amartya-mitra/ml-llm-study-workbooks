"""Chapter 2 figure: pre-norm vs. post-norm vs. sandwich-norm.

What to notice: all three panels contain the exact same two ingredients
(a sublayer and a norm) -- only the norm's POSITION relative to the
sublayer and the residual addition point changes. Sandwich-norm is not
a new operation, it is pre-norm and post-norm's norm placements both
applied to the same sublayer.

Run: python3 figures/source/fig_norm_placement.py
Output: figures/rendered/fig-norm-placement.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-norm-placement"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")


def panel(canvas, x0, title, norm_before, norm_after, colors):
    orange = colors["computation"]
    blue = colors["stored_information"]
    w = 150
    y = 85
    canvas.add_text(x0 + w / 2, y - 30, title, size=11, weight="bold", anchor="middle")

    canvas.add_arrow(x0 + w / 2, y - 14, x0 + w / 2, y, style="solid", color=blue, stroke_width=2.5)

    cur_y = y
    if norm_before:
        canvas.add_rect(x0 + 30, cur_y, w - 60, 22, fill="#ffffff", stroke="#333333", stroke_width=1.5)
        canvas.add_text(x0 + w / 2, cur_y + 15, "norm", size=10, anchor="middle")
        cur_y += 22
        canvas.add_arrow(x0 + w / 2, cur_y, x0 + w / 2, cur_y + 14, style="solid", color="#333333", stroke_width=1.5)
        cur_y += 14

    canvas.add_rect(x0 + 15, cur_y, w - 30, 34, fill=orange, stroke="#333333", stroke_width=2)
    canvas.add_text(x0 + w / 2, cur_y + 22, "sublayer", size=10, color="#ffffff", anchor="middle")
    cur_y += 34
    canvas.add_arrow(x0 + w / 2, cur_y, x0 + w / 2, cur_y + 14, style="solid", color="#333333", stroke_width=1.5)
    cur_y += 14

    if norm_after:
        canvas.add_rect(x0 + 30, cur_y, w - 60, 22, fill="#ffffff", stroke="#333333", stroke_width=1.5)
        canvas.add_text(x0 + w / 2, cur_y + 15, "norm", size=10, anchor="middle")
        cur_y += 22
        canvas.add_arrow(x0 + w / 2, cur_y, x0 + w / 2, cur_y + 14, style="solid", color="#333333", stroke_width=1.5)
        cur_y += 14

    canvas.add_raw(f'<circle cx="{x0 + w/2}" cy="{cur_y + 11}" r="11" fill="#ffffff" stroke="#333333" stroke-width="1.5"/>')
    canvas.add_text(x0 + w / 2, cur_y + 15, "+", size=13, weight="bold", anchor="middle")
    bypass_y = y - 14 + 7
    canvas.add_raw(
        f'<path d="M {x0+5},{bypass_y} L {x0+5},{cur_y+11} L {x0+w/2-11},{cur_y+11}" '
        f'fill="none" stroke="{colors["stored_information"]}" stroke-width="2.5" marker-end="url(#arrow-0072B2)"/>'
    )
    cur_y += 22
    canvas.add_arrow(x0 + w / 2, cur_y, x0 + w / 2, cur_y + 16, style="solid", color=blue, stroke_width=2.5)
    return cur_y + 16


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    canvas = SVGCanvas(width=560, height=1, title="Pre-norm vs. post-norm vs. sandwich-norm")
    canvas._ensure_marker(colors["stored_information"])

    canvas.add_text(20, 25, "Same sublayer, same residual add -- only where \"norm\" sits changes", size=12, weight="bold")

    bottom1 = panel(canvas, 20, "pre-norm", norm_before=True, norm_after=False, colors=colors)
    bottom2 = panel(canvas, 205, "post-norm", norm_before=False, norm_after=True, colors=colors)
    bottom3 = panel(canvas, 390, "sandwich-norm", norm_before=True, norm_after=True, colors=colors)
    bottom = max(bottom1, bottom2, bottom3)

    legend_y = bottom + 20
    canvas.add_text(20, legend_y, "blue = residual stream (bypasses the sublayer at the + point)", size=11, color="#555555")

    canvas.height = legend_y + 25
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
