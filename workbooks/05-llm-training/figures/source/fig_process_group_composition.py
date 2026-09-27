"""Chapter 4 figure: a multidimensional (DP x PP x TP) process-group
diagram, showing how the SAME eight devices participate in three
different logical groups depending on which axis is varied.

This is a smaller, 8-device illustration (DP=2, PP=2, TP=2) of the
same grouping logic used in the chapter's own 64-device worked
example -- drawn small enough to keep every label legible at print
scale, not a claim that real deployments use exactly 8 devices.

What to notice: rank 0 belongs to a DIFFERENT set of co-workers
depending on which axis you ask about -- its TP group (rank 1), its
PP group (rank 2), and its DP group (rank 4) are three disjoint pairs.
These are LOGICAL process groups (which ranks all-reduce/all-gather
together for a given axis) -- they say nothing about physical rack or
network topology, which is a separate, unillustrated concern.

Run: python3 workbooks/05-llm-training/figures/source/fig_process_group_composition.py
Output: workbooks/05-llm-training/figures/rendered/fig-process-group-composition.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-process-group-composition"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

WIDTH = 980
HEIGHT = 620

# rank = dp_idx*4 + pp_idx*2 + tp_idx, for dp_idx,pp_idx,tp_idx in {0,1}
DEVICES = {}
for dp_idx in (0, 1):
    for pp_idx in (0, 1):
        for tp_idx in (0, 1):
            rank = dp_idx * 4 + pp_idx * 2 + tp_idx
            DEVICES[rank] = {"dp": dp_idx, "pp": pp_idx, "tp": tp_idx}

# grid column = dp_idx*2 + tp_idx (0..3), grid row = pp_idx (0..1)
COLUMNS = [(dp, tp) for dp in (0, 1) for tp in (0, 1)]  # (dp,tp) -> col index 0..3


def rank_of(dp, pp, tp):
    return dp * 4 + pp * 2 + tp


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    tp_color = "#0072B2"   # blue, solid
    pp_color = "#009E73"   # green, dotted
    dp_color = "#D55E00"   # orange, dashed

    c = SVGCanvas(WIDTH, HEIGHT, title="Multidimensional process-group composition (DP x PP x TP), 8-device illustration")

    c.add_rect(20, 15, WIDTH - 40, 32, fill="#f2f2f2", stroke="#666666", stroke_width=1.2, rx=4)
    c.add_text(WIDTH / 2, 36, "LOGICAL PROCESS GROUPS — not a physical rack or network diagram", size=13, weight="bold", color="#333333", anchor="middle")

    box_w, box_h = 150, 90
    col_gap, row_gap = 40, 60
    grid_w = 4 * box_w + 3 * col_gap
    x0 = (WIDTH - grid_w) / 2
    y0 = 110

    box_xy = {}
    for col, (dp, tp) in enumerate(COLUMNS):
        x = x0 + col * (box_w + col_gap)
        for pp in (0, 1):
            y = y0 + pp * (box_h + row_gap)
            rank = rank_of(dp, pp, tp)
            box_xy[rank] = (x, y)
            c.add_rect(x, y, box_w, box_h, fill="#ffffff", stroke="#333333", stroke_width=1.5, rx=6)
            c.add_text(x + box_w / 2, y + 28, f"rank {rank}", size=15, weight="bold", color="#111111", anchor="middle")
            c.add_text(x + box_w / 2, y + 52, f"dp={dp}  pp={pp}  tp={tp}", size=11, color="#555555", anchor="middle")

    # TP group example: rank 0 and rank 1 (top row, col 0) -- solid blue box
    r0x, r0y = box_xy[0]
    r1x, r1y = box_xy[1]
    tp_left = min(r0x, r1x) - 8
    tp_right = max(r0x + box_w, r1x + box_w) + 8
    c.add_rect(tp_left, r0y - 8, tp_right - tp_left, box_h + 16, fill="none", stroke=tp_color, stroke_width=3, rx=10, dash="solid")

    # PP group example: rank 0 and rank 2 (col 0, both rows) -- dotted green box
    r2x, r2y = box_xy[2]
    pp_top = min(r0y, r2y) - 8
    pp_bottom = max(r0y + box_h, r2y + box_h) + 8
    c.add_rect(r0x - 8, pp_top, box_w + 16, pp_bottom - pp_top, fill="none", stroke=pp_color, stroke_width=3, rx=10, dash="dotted")

    # DP group example: rank 0 and rank 4 (same row, 2 columns apart) -- dashed
    # orange halo, with the connector routed ABOVE the row (not through
    # rank 1's box, which sits directly between rank 0 and rank 4).
    r4x, r4y = box_xy[4]
    c.add_rect(r0x - 8, r0y - 8, box_w + 16, box_h + 16, fill="none", stroke=dp_color, stroke_width=3, rx=10, dash="dashed")
    c.add_rect(r4x - 8, r4y - 8, box_w + 16, box_h + 16, fill="none", stroke=dp_color, stroke_width=3, rx=10, dash="dashed")
    conn_y = r0y - 34
    r0_top_cx = r0x + box_w / 2
    r4_top_cx = r4x + box_w / 2
    c.add_raw(
        f'<line x1="{r0_top_cx}" y1="{r0y - 8}" x2="{r0_top_cx}" y2="{conn_y}" '
        f'stroke="{dp_color}" stroke-width="3" stroke-dasharray="6,4"/>'
    )
    c.add_raw(
        f'<line x1="{r0_top_cx}" y1="{conn_y}" x2="{r4_top_cx}" y2="{conn_y}" '
        f'stroke="{dp_color}" stroke-width="3" stroke-dasharray="6,4"/>'
    )
    c.add_raw(
        f'<line x1="{r4_top_cx}" y1="{conn_y}" x2="{r4_top_cx}" y2="{r4y - 8}" '
        f'stroke="{dp_color}" stroke-width="3" stroke-dasharray="6,4"/>'
    )
    c.add_text((r0_top_cx + r4_top_cx) / 2, conn_y - 8, "same DP group — not grid-adjacent", size=11, color=dp_color, anchor="middle")

    legend_y = y0 + 2 * box_h + row_gap + 55
    c.add_text(x0, legend_y, "Legend:", size=13, weight="bold", color="#111111", anchor="start")
    c.add_rect(x0 + 90, legend_y - 14, 40, 16, fill="none", stroke=tp_color, stroke_width=3, rx=3, dash="solid")
    c.add_text(x0 + 140, legend_y - 2, "TP group (rank 0, rank 1) — shares dp, pp; varies tp", size=12, color="#333333", anchor="start")
    c.add_rect(x0 + 90, legend_y + 14, 40, 16, fill="none", stroke=pp_color, stroke_width=3, rx=3, dash="dotted")
    c.add_text(x0 + 140, legend_y + 26, "PP group (rank 0, rank 2) — shares dp, tp; varies pp", size=12, color="#333333", anchor="start")
    c.add_rect(x0 + 90, legend_y + 42, 40, 16, fill="none", stroke=dp_color, stroke_width=3, rx=3, dash="dashed")
    c.add_text(x0 + 140, legend_y + 54, "DP group (rank 0, rank 4) — shares pp, tp; varies dp", size=12, color="#333333", anchor="start")

    c.add_text(WIDTH / 2, legend_y + 90, "Rank 0 is a member of all three groups above at once — the same 8 devices, sliced along three different axes.", size=12, color="#555555", anchor="middle")

    c.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
