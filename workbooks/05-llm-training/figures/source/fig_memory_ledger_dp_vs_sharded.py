"""Chapter 5 figure (optional second figure): a per-device memory
ledger comparing replicated data parallelism with a ZeRO-3/FSDP
sharded configuration, for this chapter's own worked example.

Reads directly from data/worked-examples/memory_and_communication_budget.py's
own JSON output -- the four stacked segments (bf16 params, bf16
gradients, fp32 master weights, fp32 Adam states) and their heights
are not reinvented here. The semantic invariant this figure must
satisfy (see tests/test_wb05_ch05_figure_invariants.py): each bar's
stacked-segment heights must sum to that configuration's own total,
and the sharded bar's total must equal the replicated bar's total
divided by the worked example's own DP degree.

Run: python3 workbooks/05-llm-training/figures/source/fig_memory_ledger_dp_vs_sharded.py
Output: workbooks/05-llm-training/figures/rendered/fig-memory-ledger-dp-vs-sharded.svg
"""
import json
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-memory-ledger-dp-vs-sharded"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")
DATA_PATH = os.path.join(os.path.dirname(_THIS_DIR), "..", "data", "worked-examples",
                         "memory_and_communication_budget.json")

WIDTH = 860
HEIGHT = 620

SEGMENT_ORDER = ["m_params_bf16", "m_grad_bf16", "m_params_fp32_master", "m_opt_fp32_adam"]
SEGMENT_LABELS = {
    "m_params_bf16": "Params (bf16)",
    "m_grad_bf16": "Gradients (bf16)",
    "m_params_fp32_master": "Master weights (fp32)",
    "m_opt_fp32_adam": "Adam states (fp32)",
}


def load_worked_example_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    segment_colors = {
        "m_params_bf16": colors["stored_information"],
        "m_grad_bf16": colors["computation"],
        "m_params_fp32_master": colors["trainable_component"],
        "m_opt_fp32_adam": colors["frozen_or_inactive"],
    }

    data = load_worked_example_data()
    dp = data["toy_config"]["dp_degree"]
    replicated = data["model_state_memory"]["replicated_per_rank_bytes"]
    sharded = data["model_state_memory"]["zero3_sharded_per_rank_bytes"]
    replicated_gib = data["model_state_memory"]["replicated_per_rank_GiB"]
    sharded_gib = data["model_state_memory"]["zero3_sharded_per_rank_GiB"]

    c = SVGCanvas(WIDTH, HEIGHT, title="Per-device model-state memory: replicated DP vs. ZeRO-3/FSDP sharded")

    c.add_rect(20, 15, WIDTH - 40, 32, fill="#f2f2f2", stroke="#666666", stroke_width=1.2, rx=4)
    c.add_text(WIDTH / 2, 36, "PER-DEVICE MODEL-STATE MEMORY — this chapter's own worked example, not a measured allocation", size=12, weight="bold", color="#333333", anchor="middle")

    plot_top = 80
    plot_bottom = 470
    plot_h = plot_bottom - plot_top
    max_gib = replicated_gib * 1.15
    px_per_gib = plot_h / max_gib

    bar_w = 180
    gap = 160
    x0 = (WIDTH - (2 * bar_w + gap)) / 2
    x_replicated = x0
    x_sharded = x0 + bar_w + gap

    def draw_bar(x, components_bytes, total_gib, label, sub_label):
        y = plot_bottom
        for key in SEGMENT_ORDER:
            seg_gib = (components_bytes[key] / 2**30)
            h = seg_gib * px_per_gib
            y -= h
            c.add_rect(x, y, bar_w, h, fill=segment_colors[key], stroke="#333333", stroke_width=1)
            if h > 18:
                c.add_text(x + bar_w / 2, y + h / 2 + 4, f"{seg_gib:.1f}", size=11, color="#ffffff", anchor="middle")
        c.add_text(x + bar_w / 2, plot_bottom + 24, label, size=14, weight="bold", color="#111111", anchor="middle")
        c.add_text(x + bar_w / 2, plot_bottom + 44, sub_label, size=12, color="#555555", anchor="middle")
        c.add_text(x + bar_w / 2, y - 12, f"{total_gib:.1f} GiB total", size=13, weight="bold", color="#111111", anchor="middle")

    draw_bar(x_replicated, replicated, replicated_gib, "Replicated DP", "every rank stores the full total")
    draw_bar(x_sharded, sharded, sharded_gib, "ZeRO-3 / FSDP sharded", f"every rank stores total ÷ DP={dp}")

    # y-axis
    c.add_raw(f'<line x1="{x0 - 20}" y1="{plot_top}" x2="{x0 - 20}" y2="{plot_bottom}" stroke="#666666" stroke-width="1.5"/>')
    c.add_text(x0 - 30, plot_top + 10, "GiB per device", size=12, color="#555555", anchor="end")

    legend_y = 550
    lx = x0
    for i, key in enumerate(SEGMENT_ORDER):
        c.add_rect(lx, legend_y - 14, 24, 14, fill=segment_colors[key], stroke="#333333")
        c.add_text(lx + 30, legend_y - 3, SEGMENT_LABELS[key], size=11, color="#333333", anchor="start")
        lx += 185

    c.add_text(WIDTH / 2, legend_y + 35,
               "Same four model-state objects in both bars — sharding changes residency (divides each by DP), not which objects exist.",
               size=12, color="#555555", anchor="middle")

    c.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
