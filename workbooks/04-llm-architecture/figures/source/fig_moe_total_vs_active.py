"""Chapter 5 figure: total vs. active parameters, distinguishing
stored, active-for-this-token, and inactive-for-this-token components.

What to notice: the base/dense parameters and the shared expert are
ALWAYS active; only k of the E routed experts are active for any given
token; all E are stored regardless.

Run: python3 workbooks/04-llm-architecture/figures/source/fig_moe_total_vs_active.py
Output: figures/rendered/fig-moe-total-vs-active.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-moe-total-vs-active"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

# Full-width (6.5in) embed, W=900 -> 1 unit = 0.52pt; need ~17.3 for 9pt.
TITLE_SIZE = 18
LABEL_SIZE = 16
SMALL_SIZE = 14


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    blue = colors["stored_information"]
    green = colors["trainable_component"]
    gray_inactive = "#e6e6e6"

    W = 900
    canvas = SVGCanvas(width=W, height=1, title="Total vs. active parameters for one token")

    canvas.add_text(W / 2, 24, "For one token, top-2 of 8 routed experts selected", size=TITLE_SIZE, weight="bold", anchor="middle")

    row_y = 55
    box_h = 50

    # Base/dense (always active).
    bx, bw = 20, 130
    canvas.add_rect(bx, row_y, bw, box_h, fill=blue, stroke="#333333", stroke_width=2, rx=6)
    canvas.add_text(bx + bw / 2, row_y + 22, "base / dense", size=LABEL_SIZE, color="#ffffff", anchor="middle")
    canvas.add_text(bx + bw / 2, row_y + 40, "(attn, norm, router)", size=SMALL_SIZE, color="#ffffff", anchor="middle")

    # Shared expert (always active).
    sx, sw_ = bx + bw + 20, 100
    canvas.add_rect(sx, row_y, sw_, box_h, fill=blue, stroke="#333333", stroke_width=2, rx=6)
    canvas.add_text(sx + sw_ / 2, row_y + 22, "shared expert", size=LABEL_SIZE, color="#ffffff", anchor="middle")
    canvas.add_text(sx + sw_ / 2, row_y + 40, "(always active)", size=SMALL_SIZE, color="#ffffff", anchor="middle")

    # Routed expert bank: 8 boxes, 2 selected.
    n_experts = 8
    selected = {2, 6}
    exp_w = 62
    gap = 8
    ex0 = sx + sw_ + 30
    exp_centers = []
    for i in range(n_experts):
        ex = ex0 + i * (exp_w + gap)
        active = i in selected
        fill = green if active else gray_inactive
        stroke = colors["bottleneck_or_failure"] if active else "#999999"
        sw_box = 2.5 if active else 1
        canvas.add_rect(ex, row_y, exp_w, box_h, fill=fill, stroke=stroke, stroke_width=sw_box, rx=5)
        label_color = "#ffffff" if active else "#666666"
        canvas.add_text(ex + exp_w / 2, row_y + 22, f"E{i+1}", size=LABEL_SIZE, color=label_color, anchor="middle")
        canvas.add_text(ex + exp_w / 2, row_y + 40, "active" if active else "inactive", size=SMALL_SIZE, color=label_color, anchor="middle")
        exp_centers.append(ex + exp_w / 2)

    bracket_y = row_y + box_h + 20
    canvas.add_arrow(ex0, bracket_y, ex0 + n_experts * (exp_w + gap) - gap, bracket_y, style="solid", color="#555555", stroke_width=1)
    canvas.add_text((ex0 + ex0 + n_experts * (exp_w + gap) - gap) / 2, bracket_y + 20, "routed expert bank: all E stored, only k active per token", size=SMALL_SIZE, color="#555555", anchor="middle")

    legend_y = bracket_y + 55
    canvas.add_rect(20, legend_y, 16, 16, fill=blue, rx=2)
    canvas.add_text(44, legend_y + 13, "always active (base + shared)", size=SMALL_SIZE)
    canvas.add_rect(340, legend_y, 16, 16, fill=green, rx=2)
    canvas.add_text(364, legend_y + 13, "active for this token (selected)", size=SMALL_SIZE)
    canvas.add_rect(20, legend_y + 32, 16, 16, fill=gray_inactive, stroke="#999999", rx=2)
    canvas.add_text(44, legend_y + 45, "stored, not active for this token", size=SMALL_SIZE)

    canvas.height = legend_y + 55
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
