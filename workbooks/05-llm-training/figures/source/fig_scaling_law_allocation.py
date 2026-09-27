"""Chapter 3 figure: compute-optimal model/data allocation, contrasting
Kaplan et al.'s fitted exponents ([@src-50]) against Hoffmann et al.'s
(Chinchilla, [@src-51]) fitted exponents, for the SAME toy 10x
fixed-compute increase used in the chapter's worked example.

What to notice: both bars represent the SAME compute budget increase
(10x) -- the figure is a schematic comparison of a FITTED allocation
split, not a plot of measured training-run datapoints. Growth factors
shown (5.37x/1.86x for Kaplan, 3.16x/3.16x for Chinchilla) are computed
by data/worked-examples/scaling_law_allocation.py, not invented here.

Run: python3 workbooks/05-llm-training/figures/source/fig_scaling_law_allocation.py
Output: workbooks/05-llm-training/figures/rendered/fig-scaling-law-allocation.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-scaling-law-allocation"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

WIDTH = 960
HEIGHT = 560

# Growth factors for a 10x fixed-compute increase, from
# scaling_law_allocation.py's own computed output (part_a_toy_allocation).
KAPLAN_MODEL_GROWTH = 5.37
KAPLAN_DATA_GROWTH = 1.86
CHINCHILLA_MODEL_GROWTH = 3.16
CHINCHILLA_DATA_GROWTH = 3.16
MAX_GROWTH = 6.0  # bar-height scale ceiling, chosen to fit the largest bar (5.37) with headroom


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    model_color = colors["computation"]
    data_color = colors["stored_information"]
    frame_color = colors["frozen_or_inactive"]

    c = SVGCanvas(WIDTH, HEIGHT, title="Compute-optimal allocation: Kaplan et al. vs. Chinchilla, for a 10x fixed-compute increase")

    c.add_rect(20, 15, WIDTH - 40, 34, fill="#eaf2fb", stroke="#0072B2", stroke_width=1.5, rx=4)
    c.add_text(WIDTH / 2, 37, "FITTED ALLOCATION SPLIT for the SAME 10x compute increase — not measured training-run datapoints", size=13, weight="bold", color="#0072B2", anchor="middle")

    panel_w = (WIDTH - 100) / 2
    panel_gap = 40
    panel_y = 90
    panel_h = 380
    baseline_y = panel_y + panel_h

    bar_w = 90
    bar_gap = 50
    scale = panel_h / MAX_GROWTH

    def draw_panel(px, title, model_growth, data_growth, source_label):
        c.add_text(px + panel_w / 2, panel_y - 20, title, size=16, weight="bold", color="#111111", anchor="middle")
        c.add_rect(px, panel_y, panel_w, panel_h, fill="#ffffff", stroke=frame_color, stroke_width=1.5, rx=6)

        group_center = px + panel_w / 2
        model_x = group_center - bar_gap / 2 - bar_w
        data_x = group_center + bar_gap / 2

        model_h = model_growth * scale
        c.add_rect(model_x, baseline_y - model_h, bar_w, model_h, fill=model_color, stroke="#333333")
        c.add_text(model_x + bar_w / 2, baseline_y - model_h - 10, f"{model_growth:.2f}x", size=14, weight="bold", color="#111111", anchor="middle")
        c.add_text(model_x + bar_w / 2, baseline_y + 22, "model size N", size=12, color="#333333", anchor="middle")

        data_h = data_growth * scale
        c.add_rect(data_x, baseline_y - data_h, bar_w, data_h, fill=data_color, stroke="#333333")
        c.add_text(data_x + bar_w / 2, baseline_y - data_h - 10, f"{data_growth:.2f}x", size=14, weight="bold", color="#111111", anchor="middle")
        c.add_text(data_x + bar_w / 2, baseline_y + 22, "data size D", size=12, color="#333333", anchor="middle")

        c.add_text(px + panel_w / 2, baseline_y + 46, source_label, size=11, color="#555555", anchor="middle")

    draw_panel(50, "Kaplan et al. (2020)", KAPLAN_MODEL_GROWTH, KAPLAN_DATA_GROWTH, "exponents a=0.73, b=0.27 — model-heavy")
    draw_panel(50 + panel_w + panel_gap, "Chinchilla (Hoffmann et al., 2022)", CHINCHILLA_MODEL_GROWTH, CHINCHILLA_DATA_GROWTH, "exponents a=0.50, b=0.50 — equal split")

    c.add_text(WIDTH / 2, baseline_y + 75, "Both allocations satisfy the same fixed-compute constraint C ≈ 6ND; they differ only in HOW that compute is split between N and D.", size=12, color="#555555", anchor="middle")

    c.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
