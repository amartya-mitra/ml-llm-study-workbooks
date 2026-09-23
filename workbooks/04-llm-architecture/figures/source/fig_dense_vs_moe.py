"""Chapter 5 figure: dense feed-forward block vs. sparse MoE block, same
input tokens in both panels.

What to notice: MoE replaces the FEED-FORWARD sublayer, not attention.
The router selects a subset (top-k) of experts per token; unselected
experts are drawn but not highlighted, showing they exist (and are
stored) without being used for this token.

Run: python3 workbooks/04-llm-architecture/figures/source/fig_dense_vs_moe.py
Output: figures/rendered/fig-dense-vs-moe.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-dense-vs-moe"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

# Full-width (6.5in) embed, W=900 -> 1 unit = 6.5*72/900 = 0.52pt.
# Need ~17.3 units for a 9pt essential label.
TITLE_SIZE = 18
LABEL_SIZE = 16
SMALL_SIZE = 14


def token_row(canvas, x0, y, n=3):
    blue = "#0072B2"
    centers = []
    for i in range(n):
        cx = x0 + i * 40
        canvas.add_rect(cx, y, 30, 26, fill=blue, stroke="#333333", stroke_width=1.2, rx=4)
        canvas.add_text(cx + 15, y + 18, f"t{i+1}", size=SMALL_SIZE, color="#ffffff", anchor="middle")
        centers.append(cx + 15)
    return centers


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    orange = colors["computation"]
    blue = colors["stored_information"]
    gray = colors["frozen_or_inactive"]

    W = 900
    canvas = SVGCanvas(width=W, height=1, title="Dense feed-forward block vs. sparse MoE block")

    # Left panel: dense FFN.
    lx0 = 20
    canvas.add_text(lx0 + 130, 24, "Dense FFN", size=TITLE_SIZE, weight="bold", anchor="middle")
    t_centers_l = token_row(canvas, lx0 + 20, 45, n=3)
    ffn_x, ffn_y, ffn_w, ffn_h = lx0 + 40, 110, 180, 44
    for cx in t_centers_l:
        canvas.add_arrow(cx, 45 + 26, ffn_x + ffn_w / 2, ffn_y, style="solid", color="#333333", stroke_width=1.2)
    canvas.add_rect(ffn_x, ffn_y, ffn_w, ffn_h, fill=orange, stroke="#333333", stroke_width=2, rx=6)
    canvas.add_text(ffn_x + ffn_w / 2, ffn_y + ffn_h / 2 + 6, "same FFN, every token", size=LABEL_SIZE, color="#ffffff", anchor="middle")
    out_y = ffn_y + ffn_h + 30
    canvas.add_arrow(ffn_x + ffn_w / 2, ffn_y + ffn_h, ffn_x + ffn_w / 2, out_y, style="solid", color="#333333", stroke_width=1.2)
    canvas.add_text(ffn_x + ffn_w / 2, out_y + 16, "back to residual stream", size=SMALL_SIZE, color="#555555", anchor="middle")

    # Right panel: sparse MoE.
    rx0 = 440
    canvas.add_text(rx0 + 210, 24, "Sparse MoE", size=TITLE_SIZE, weight="bold", anchor="middle")
    t_centers_r = token_row(canvas, rx0 + 160, 45, n=3)
    router_x, router_y, router_w, router_h = rx0 + 140, 110, 140, 40
    for cx in t_centers_r:
        canvas.add_arrow(cx, 45 + 26, router_x + router_w / 2, router_y, style="solid", color="#333333", stroke_width=1.2)
    canvas.add_rect(router_x, router_y, router_w, router_h, fill=orange, stroke="#333333", stroke_width=2, rx=6)
    canvas.add_text(router_x + router_w / 2, router_y + router_h / 2 + 5, "router: top-k", size=LABEL_SIZE, color="#ffffff", anchor="middle")

    expert_y = router_y + router_h + 40
    n_experts = 6
    selected = {1, 4}
    exp_w = 48
    gap = 10
    total_w = n_experts * exp_w + (n_experts - 1) * gap
    ex0 = rx0 + 210 + 70 - total_w / 2
    exp_centers = []
    for i in range(n_experts):
        ex = ex0 + i * (exp_w + gap)
        fill = blue if i in selected else "#e6e6e6"
        stroke = colors["bottleneck_or_failure"] if i in selected else "#999999"
        sw = 2.5 if i in selected else 1
        canvas.add_rect(ex, expert_y, exp_w, 40, fill=fill, stroke=stroke, stroke_width=sw, rx=5)
        label_color = "#ffffff" if i in selected else "#666666"
        canvas.add_text(ex + exp_w / 2, expert_y + 25, f"E{i+1}", size=LABEL_SIZE, color=label_color, anchor="middle")
        exp_centers.append(ex + exp_w / 2)
        style_arrow = "solid" if i in selected else "dotted"
        color_arrow = "#333333" if i in selected else "#aaaaaa"
        canvas.add_arrow(router_x + router_w / 2, router_y + router_h, ex + exp_w / 2, expert_y, style=style_arrow, color=color_arrow, stroke_width=1.2 if i in selected else 0.8)

    combine_y = expert_y + 40 + 35
    combine_x = rx0 + 210 + 70
    for i in selected:
        canvas.add_arrow(exp_centers[i], expert_y + 40, combine_x, combine_y, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_rect(combine_x - 70, combine_y, 140, 34, fill=orange, stroke="#333333", stroke_width=2, rx=6)
    canvas.add_text(combine_x, combine_y + 22, "combine (weighted)", size=SMALL_SIZE, color="#ffffff", anchor="middle")
    out_y2 = combine_y + 34 + 22
    canvas.add_arrow(combine_x, combine_y + 34, combine_x, out_y2, style="solid", color="#333333", stroke_width=1.2)
    canvas.add_text(combine_x, out_y2 + 16, "back to residual stream", size=SMALL_SIZE, color="#555555", anchor="middle")

    legend_y = max(out_y + 35, out_y2 + 35)
    canvas.add_rect(20, legend_y, 16, 16, fill=blue, rx=2)
    canvas.add_text(44, legend_y + 13, "selected expert (active for this token)", size=SMALL_SIZE)
    canvas.add_rect(320, legend_y, 16, 16, fill="#e6e6e6", stroke="#999999", rx=2)
    canvas.add_text(344, legend_y + 13, "unselected expert (stored, inactive)", size=SMALL_SIZE)
    canvas.add_text(20, legend_y + 40, "MoE replaces the feed-forward sublayer only -- attention is unchanged.", size=SMALL_SIZE, color="#555555")

    canvas.height = legend_y + 60
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
