"""Chapter 5 figure: a training-step resource timeline showing
compute, communication, overlap, and exposed communication on the
critical path.

This figure reads its numbers directly from
data/worked-examples/memory_and_communication_budget.py's own JSON
output -- it does not hardcode or re-derive compute time, total
communication time, or the overlap fraction. The semantic invariant
this figure must satisfy (see
tests/test_wb05_ch05_figure_invariants.py): the exposed-communication
segment must start exactly where compute ends and end exactly at the
worked example's own step_time_with_overlap value, and
hidden+exposed communication must sum to the worked example's own
total communication time.

What to notice: communication is split into a HIDDEN portion (drawn
overlapping the compute bar, since it executes concurrently and does
not extend the critical path) and an EXPOSED portion (drawn after
compute ends, since nothing hides it and it does extend the critical
path). Overlap can shrink the exposed portion; it cannot shrink it to
a claim that communication was free -- the hidden portion is time
communication still occupies, concurrently.

Run: python3 workbooks/05-llm-training/figures/source/fig_training_step_timeline.py
Output: workbooks/05-llm-training/figures/rendered/fig-training-step-timeline.svg
"""
import json
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-training-step-timeline"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")
DATA_PATH = os.path.join(os.path.dirname(_THIS_DIR), "..", "data", "worked-examples",
                         "memory_and_communication_budget.json")

WIDTH = 980
HEIGHT = 420


def load_worked_example_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    compute_color = colors["computation"]
    hidden_comm_color = colors["frozen_or_inactive"]
    exposed_comm_color = "#D55E00"

    data = load_worked_example_data()
    compute_s = data["step_time"]["compute_time_seconds"]
    hidden_s = data["communication"]["hidden_comm_time_seconds"]
    exposed_s = data["communication"]["exposed_comm_time_seconds"]
    total_comm_s = data["communication"]["total_comm_time_all_blocks_seconds"]
    step_with_overlap_s = data["step_time"]["step_time_with_overlap_seconds"]

    c = SVGCanvas(WIDTH, HEIGHT, title="Training-step resource timeline: compute, hidden communication, and exposed communication")

    c.add_rect(20, 15, WIDTH - 40, 32, fill="#f2f2f2", stroke="#666666", stroke_width=1.2, rx=4)
    c.add_text(WIDTH / 2, 36, "CRITICAL-PATH TIMELINE — from this chapter's own worked example, not a measured trace", size=13, weight="bold", color="#333333", anchor="middle")

    left_margin = 160
    right_margin = 40
    timeline_w = WIDTH - left_margin - right_margin
    px_per_s = timeline_w / step_with_overlap_s

    row_h = 70
    row_gap = 40
    y_compute = 110
    y_comm = y_compute + row_h + row_gap

    c.add_text(left_margin - 15, y_compute + row_h / 2 + 5, "Compute", size=14, weight="bold", color="#111111", anchor="end")
    c.add_rect(left_margin, y_compute, compute_s * px_per_s, row_h, fill=compute_color, stroke="#333333", stroke_width=1.5)
    c.add_text(left_margin + (compute_s * px_per_s) / 2, y_compute + row_h / 2 + 5,
               f"{compute_s * 1000:.0f} ms", size=13, weight="bold", color="#ffffff", anchor="middle")

    c.add_text(left_margin - 15, y_comm + row_h / 2 + 5, "Communication", size=14, weight="bold", color="#111111", anchor="end")
    hidden_w = hidden_s * px_per_s
    exposed_w = exposed_s * px_per_s
    MIN_LABEL_WIDTH = 70  # below this bar width, an inside-centered label would overflow its own bar

    def label_segment(bar_x, bar_w, text, text_color, grow_left):
        """Centers `text` inside the bar if it is wide enough; otherwise
        places it above the bar (anchored so it grows away from the
        bar's nearest canvas edge, never past WIDTH) with a leader line
        down to the bar -- the exact fix for a bar narrow enough that a
        centered label would overflow both the bar and, near the right
        margin, the canvas itself."""
        if bar_w > MIN_LABEL_WIDTH:
            c.add_text(bar_x + bar_w / 2, y_comm + row_h / 2 + 5, text, size=12, weight="bold", color="#ffffff", anchor="middle")
            return
        label_y = y_comm - 14
        anchor = "end" if grow_left else "start"
        label_x = bar_x + bar_w if grow_left else bar_x
        bar_cx = bar_x + bar_w / 2
        c.add_raw(f'<line x1="{bar_cx}" y1="{label_y + 4}" x2="{bar_cx}" y2="{y_comm}" stroke="{text_color}" stroke-width="1.5"/>')
        c.add_text(label_x, label_y, text, size=12, weight="bold", color=text_color, anchor=anchor)

    c.add_rect(left_margin, y_comm, hidden_w, row_h, fill=hidden_comm_color, stroke="#333333", stroke_width=1.5, dash="dashed")
    label_segment(left_margin, hidden_w, "hidden", "#555555", grow_left=False)
    exposed_x = left_margin + compute_s * px_per_s
    c.add_rect(exposed_x, y_comm, exposed_w, row_h, fill=exposed_comm_color, stroke="#333333", stroke_width=1.5)
    label_segment(exposed_x, exposed_w, "exposed", exposed_comm_color, grow_left=True)

    # Critical-path bracket spanning compute + exposed communication.
    bracket_y = y_comm + row_h + 35
    x0, x1 = left_margin, left_margin + step_with_overlap_s * px_per_s
    c.add_raw(f'<line x1="{x0}" y1="{bracket_y}" x2="{x1}" y2="{bracket_y}" stroke="#333333" stroke-width="2.5"/>')
    c.add_raw(f'<line x1="{x0}" y1="{bracket_y - 8}" x2="{x0}" y2="{bracket_y + 8}" stroke="#333333" stroke-width="2.5"/>')
    c.add_raw(f'<line x1="{x1}" y1="{bracket_y - 8}" x2="{x1}" y2="{bracket_y + 8}" stroke="#333333" stroke-width="2.5"/>')
    c.add_text((x0 + x1) / 2, bracket_y + 24, f"critical path / step time ≈ {step_with_overlap_s * 1000:.1f} ms", size=13, weight="bold", color="#333333", anchor="middle")

    # Dashed vertical guide at end of compute, where exposed comm begins.
    guide_x = left_margin + compute_s * px_per_s
    c.add_raw(f'<line x1="{guide_x}" y1="{y_compute}" x2="{guide_x}" y2="{y_comm + row_h}" stroke="#999999" stroke-width="1" stroke-dasharray="3,3"/>')

    legend_y = bracket_y + 60
    c.add_rect(left_margin, legend_y - 14, 30, 16, fill=compute_color, stroke="#333333")
    c.add_text(left_margin + 38, legend_y - 2, "Compute", size=12, color="#333333", anchor="start")
    c.add_rect(left_margin + 170, legend_y - 14, 30, 16, fill=hidden_comm_color, stroke="#333333", dash="dashed")
    c.add_text(left_margin + 208, legend_y - 2, "Hidden communication (overlapped)", size=12, color="#333333", anchor="start")
    c.add_rect(left_margin + 460, legend_y - 14, 30, 16, fill=exposed_comm_color, stroke="#333333")
    c.add_text(left_margin + 498, legend_y - 2, "Exposed communication (on critical path)", size=12, color="#333333", anchor="start")

    c.add_text(WIDTH / 2, legend_y + 35,
              f"Total forward-pass parameter all-gather communication this step: {total_comm_s * 1000:.1f} ms — hidden + exposed must sum to this total. "
              "Excludes backward-pass all-gathers and gradient reduce-scatters.",
              size=12, color="#555555", anchor="middle")

    c.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
