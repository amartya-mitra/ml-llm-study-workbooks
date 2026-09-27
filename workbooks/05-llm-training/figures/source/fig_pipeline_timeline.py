"""Chapter 4 figure: a schematic one-forward-one-backward (1F1B)
pipeline-parallelism timeline for p=4 stages and m=6 microbatches,
showing the fill, steady-state, and drain phases and the idle "bubble"
slots between them.

The schedule is produced by a discrete-event, dependency-respecting
simulation (build_1f1b_schedule below), not a closed-form per-stage
offset -- an earlier version of this figure used a closed-form warmup
count (p-1-s) that gave the LAST stage zero warmup forwards, which is
causally impossible: a stage's first backward pass always needs that
same stage's own matching forward pass to have already run (the
backward reads the forward's saved activation), and the last stage
has no upstream neighbor to wait on, so it is the one stage most prone
to this exact bug if warmup is computed without simulating real
dependencies.

At each discrete time step, every stage independently checks two
candidate operations against the true dependencies described in
[@src-52] (GPipe) and [@src-17]:

    - Backward B(s, i) is ready only once F(s, i) (this stage's own
      matching forward) has completed at a strictly earlier time step,
      AND (for every stage except the last) B(s+1, i) has also
      completed at a strictly earlier time step -- the gradient must
      arrive from downstream first.
    - Forward F(s, i) is ready only once F(s-1, i) has completed at a
      strictly earlier time step (trivially true for the first stage).

A stage that has both candidates ready prefers the backward -- that
preference is the defining property of "1F1B" as opposed to
all-forward-all-backward. This directly enforces, by construction,
every one of: F(s,i) before B(s,i); F(s,i) after F(s-1,i); B(s,i)
after B(s+1,i); no backward before its forward exists; and no stage
ever executes two operations in the same time slot (each stage does
at most one action per simulated time step). See
tests/test_wb05_ch04_pipeline_schedule.py for the automated checks.

This figure is schematic (illustrating the SHAPE of fill/steady-state/
drain and where bubbles fall), not a claim about exact wall-clock
timing, which is Chapter 5's subject.

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
    """Discrete-event simulation of a standard 1F1B pipeline schedule.
    Returns ({stage: [(time_slot, label), ...]}, max_time_slot).

    Each stage does at most one operation per time step, chosen by
    checking real cross-stage/same-stage dependencies rather than any
    closed-form offset (see module docstring)."""
    fwd_done_time = {}
    bwd_done_time = {}
    next_fwd = [1] * p
    next_bwd = [1] * p
    schedule = {s: [] for s in range(p)}
    total_ops = 2 * p * m
    done_ops = 0
    t = 0
    while done_ops < total_ops:
        for s in range(p):
            bwd_ready = False
            i = next_bwd[s]
            if i <= m and (s, i) in fwd_done_time and fwd_done_time[(s, i)] < t:
                if s == p - 1:
                    bwd_ready = True
                elif (s + 1, i) in bwd_done_time and bwd_done_time[(s + 1, i)] < t:
                    bwd_ready = True
            if bwd_ready:
                bwd_done_time[(s, i)] = t
                schedule[s].append((t, f"B{i}"))
                next_bwd[s] += 1
                done_ops += 1
                continue
            fj = next_fwd[s]
            fwd_ready = False
            if fj <= m:
                if s == 0:
                    fwd_ready = True
                elif (s - 1, fj) in fwd_done_time and fwd_done_time[(s - 1, fj)] < t:
                    fwd_ready = True
            if fwd_ready:
                fwd_done_time[(s, fj)] = t
                schedule[s].append((t, f"F{fj}"))
                next_fwd[s] += 1
                done_ops += 1
        t += 1
        if t > 20 * m * p:
            raise RuntimeError("1F1B schedule simulation did not converge")
    max_slot = t - 1
    return schedule, max_slot


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    fwd_color = colors["computation"]
    bwd_color = colors["trainable_component"]
    bubble_color = "#e0e0e0"

    schedule, max_slot = build_1f1b_schedule(P_STAGES, M_MICROBATCHES)
    n_cols = max_slot + 1

    cell_w, cell_h = 54, 56
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

    all_first_bwd_slots = []
    all_last_fwd_slots = []
    for s in range(P_STAGES):
        y = grid_y0 + s * cell_h
        c.add_text(left_margin + label_w - 12, y + cell_h / 2 + 5, f"Stage {s + 1}", size=13, weight="bold", color="#111111", anchor="end")
        occupied = {slot: label for slot, label in schedule[s]}
        fwd_slots = [slot for slot, label in schedule[s] if label.startswith("F")]
        bwd_slots = [slot for slot, label in schedule[s] if label.startswith("B")]
        all_first_bwd_slots.append(min(bwd_slots))
        all_last_fwd_slots.append(max(fwd_slots))
        for col in range(n_cols):
            x = grid_x0 + col * cell_w
            if col in occupied:
                label = occupied[col]
                fill = fwd_color if label.startswith("F") else bwd_color
                c.add_rect(x + 2, y + 2, cell_w - 4, cell_h - 4, fill=fill, stroke="#333333", stroke_width=1)
                c.add_text(x + cell_w / 2, y + cell_h / 2 + 5, label, size=11, weight="bold", color="#ffffff", anchor="middle")
            else:
                c.add_rect(x + 2, y + 2, cell_w - 4, cell_h - 4, fill=bubble_color, stroke="#999999", stroke_width=1, dash="dashed")

    c.add_text(grid_x0 + n_cols * cell_w / 2, grid_y0 - 20, "time →", size=12, color="#555555", anchor="middle")

    # Phase boundaries derived from the actual schedule, not assumed:
    # fill ends at the first backward that occurs anywhere; drain
    # begins right after the last forward that occurs anywhere.
    phase_y = grid_y0 + P_STAGES * cell_h + 30
    fill_end = min(all_first_bwd_slots)
    drain_start = max(all_last_fwd_slots) + 1

    def bracket(x1, x2, label, color):
        if x2 <= x1:
            return
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
