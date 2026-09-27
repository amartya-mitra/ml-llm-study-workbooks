"""Chapter 4 figure: a schematic one-forward-one-backward (1F1B)
pipeline-parallelism timeline for p=4 stages and m=6 microbatches,
showing the fill, steady-state, and drain phases and the idle "bubble"
slots between them.

The 1F1B schedule itself is computed programmatically below (not hand-
drawn), following the standard algorithm [@src-17] and [@src-52]
(GPipe) both describe: stage s (0-indexed, 0=first stage) performs
(p-1-s) warmup forward passes, then alternates one backward + one new
forward per step during steady state, then drains its remaining
backward passes once no new forwards remain. Each stage's local
operation sequence is shown starting at global time slot (stage index
+ local step) -- the same simplifying stagger used in the Ultra-Scale
Playbook's own pipeline diagrams -- so this figure is schematic
(illustrating the SHAPE of fill/steady-state/drain and where bubbles
fall), not a claim about exact wall-clock timing, which is Chapter 5's
subject.

Run: python3 workbooks/05-llm-training/figures/source/fig_pipeline_timeline.py
Output: workbooks/05-llm-training/figures/rendered/fig-pipeline-timeline.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-pipeline-timeline"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

P_STAGES = 4
M_MICROBATCHES = 6


def build_1f1b_schedule(p, m):
    """Return {stage: [(global_time_slot, label), ...]} for a standard
    1F1B schedule, one entry per stage."""
    schedule = {}
    max_slot = 0
    for s in range(p):
        warmup = p - 1 - s
        ops = []
        fwd_done = 0
        bwd_done = 0
        for _ in range(warmup):
            fwd_done += 1
            ops.append(f"F{fwd_done}")
        while fwd_done < m:
            bwd_done += 1
            ops.append(f"B{bwd_done}")
            fwd_done += 1
            ops.append(f"F{fwd_done}")
        while bwd_done < m:
            bwd_done += 1
            ops.append(f"B{bwd_done}")
        timed = [(s + i, label) for i, label in enumerate(ops)]
        schedule[s] = timed
        max_slot = max(max_slot, timed[-1][0])
    return schedule, max_slot


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    fwd_color = colors["computation"]
    bwd_color = colors["trainable_component"]
    bubble_color = "#e0e0e0"

    schedule, max_slot = build_1f1b_schedule(P_STAGES, M_MICROBATCHES)
    n_cols = max_slot + 1

    cell_w, cell_h = 58, 56
    label_w = 90
    top_margin = 90
    left_margin = 30

    width = left_margin + label_w + n_cols * cell_w + 30
    height = top_margin + P_STAGES * cell_h + 130

    c = SVGCanvas(int(width), int(height), title="1F1B pipeline schedule: fill, steady state, and drain phases (p=4 stages, m=6 microbatches)")

    c.add_rect(20, 15, width - 40, 32, fill="#f2f2f2", stroke="#666666", stroke_width=1.2, rx=4)
    c.add_text(width / 2, 36, "SCHEMATIC SCHEDULE — illustrates phase shape, not measured wall-clock timing", size=13, weight="bold", color="#333333", anchor="middle")

    grid_x0 = left_margin + label_w
    grid_y0 = top_margin

    for s in range(P_STAGES):
        y = grid_y0 + s * cell_h
        c.add_text(left_margin + label_w - 12, y + cell_h / 2 + 5, f"Stage {s + 1}", size=13, weight="bold", color="#111111", anchor="end")
        occupied = {slot: label for slot, label in schedule[s]}
        for col in range(n_cols):
            x = grid_x0 + col * cell_w
            if col in occupied:
                label = occupied[col]
                fill = fwd_color if label.startswith("F") else bwd_color
                c.add_rect(x + 2, y + 2, cell_w - 4, cell_h - 4, fill=fill, stroke="#333333", stroke_width=1)
                c.add_text(x + cell_w / 2, y + cell_h / 2 + 5, label, size=12, weight="bold", color="#ffffff", anchor="middle")
            else:
                c.add_rect(x + 2, y + 2, cell_w - 4, cell_h - 4, fill=bubble_color, stroke="#999999", stroke_width=1, dash="dashed")

    c.add_text(grid_x0 + n_cols * cell_w / 2, grid_y0 - 20, "time →", size=12, color="#555555", anchor="middle")

    # Phase brackets: fill = cols 0..P_STAGES-2 (warmup ramp), drain = last P_STAGES-1 cols, steady-state = middle
    phase_y = grid_y0 + P_STAGES * cell_h + 30
    fill_end = P_STAGES - 1
    drain_start = n_cols - (P_STAGES - 1)

    def bracket(x1, x2, label, color):
        c.add_raw(f'<line x1="{x1}" y1="{phase_y}" x2="{x2}" y2="{phase_y}" stroke="{color}" stroke-width="3"/>')
        c.add_raw(f'<line x1="{x1}" y1="{phase_y - 8}" x2="{x1}" y2="{phase_y + 8}" stroke="{color}" stroke-width="3"/>')
        c.add_raw(f'<line x1="{x2}" y1="{phase_y - 8}" x2="{x2}" y2="{phase_y + 8}" stroke="{color}" stroke-width="3"/>')
        c.add_text((x1 + x2) / 2, phase_y + 24, label, size=12, weight="bold", color=color, anchor="middle")

    bracket(grid_x0, grid_x0 + fill_end * cell_w, "fill", "#D55E00")
    bracket(grid_x0 + fill_end * cell_w, grid_x0 + drain_start * cell_w, "steady state (1F1B)", "#0072B2")
    bracket(grid_x0 + drain_start * cell_w, grid_x0 + n_cols * cell_w, "drain", "#D55E00")

    legend_y = phase_y + 55
    c.add_rect(grid_x0, legend_y - 14, 30, 16, fill=fwd_color, stroke="#333333")
    c.add_text(grid_x0 + 38, legend_y - 2, "Forward pass", size=12, color="#333333", anchor="start")
    c.add_rect(grid_x0 + 190, legend_y - 14, 30, 16, fill=bwd_color, stroke="#333333")
    c.add_text(grid_x0 + 228, legend_y - 2, "Backward pass", size=12, color="#333333", anchor="start")
    c.add_rect(grid_x0 + 390, legend_y - 14, 30, 16, fill=bubble_color, stroke="#999999", dash="dashed")
    c.add_text(grid_x0 + 428, legend_y - 2, "Bubble (idle)", size=12, color="#333333", anchor="start")

    c.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
