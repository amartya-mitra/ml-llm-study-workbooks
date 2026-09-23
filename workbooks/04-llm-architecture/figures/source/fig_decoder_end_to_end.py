"""Chapter 1 figure: end-to-end decoder data flow.

What to notice: tokens become vectors, the vectors pass through the same
stacked block N times, and only at the very end does the model turn a
vector back into a probability distribution over the vocabulary. Nothing
"decides" the next token until that last softmax step.

Run: python3 figures/source/fig_decoder_end_to_end.py
Output: figures/rendered/fig-decoder-end-to-end.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-decoder-end-to-end"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    blue = colors["stored_information"]
    orange = colors["computation"]
    gray = colors["frozen_or_inactive"]

    # Font sizes below are chosen so essential labels print at >= 8pt at
    # final embed size: this figure embeds at 100% of the 6.5in text
    # column, so 1 SVG unit = 6.5*72/W points and a label of size S prints
    # at S * 6.5 * 72 / W points (see AGENTS.md-adjacent build note /
    # scripts/build_ch01_02_review.py review pass for the derivation).
    W = 960
    canvas = SVGCanvas(width=W, height=1, title="End-to-end decoder data flow")

    stage_y = 60
    stage_h = 78
    stage_w = 125
    gap = 22
    stage_label_size = 17  # ~8.3pt at final size -- essential (names the stage)
    line_step = 20
    stages = ["tokens", "embeddings", "N x decoder\nblock", "final norm", "output head", "logits"]
    x = 20
    centers = []
    for i, label in enumerate(stages):
        fill = blue if label in ("tokens", "embeddings") else orange
        canvas.add_rect(x, stage_y, stage_w, stage_h, fill=fill, stroke="#333333", stroke_width=2)
        lines = label.split("\n")
        for li, line in enumerate(lines):
            canvas.add_text(x + stage_w / 2, stage_y + stage_h / 2 + 4 + (li - (len(lines) - 1) / 2) * line_step,
                             line, size=stage_label_size, color="#ffffff", anchor="middle")
        centers.append((x, x + stage_w))
        x += stage_w + gap

    for i in range(len(stages) - 1):
        x1 = centers[i][1]
        x2 = centers[i + 1][0]
        canvas.add_arrow(x1, stage_y + stage_h / 2, x2, stage_y + stage_h / 2, style="solid", color="#333333", stroke_width=1.5)

    loop_y0 = stage_y - 22
    loop_x1, loop_x2 = centers[2]
    canvas.add_raw(
        f'<path d="M {loop_x1},{loop_y0} L {loop_x1},{stage_y-4} M {loop_x2},{loop_y0} L {loop_x2},{stage_y-4}" '
        f'stroke="#333333" stroke-width="1" fill="none"/>'
    )
    canvas.add_raw(
        f'<line x1="{loop_x1}" y1="{loop_y0}" x2="{loop_x2}" y2="{loop_y0}" stroke="#333333" stroke-width="1"/>'
    )
    canvas.add_text((loop_x1 + loop_x2) / 2, loop_y0 - 6, "same block, applied N times, each with its own weights", size=15, color="#555555", anchor="middle")

    softmax_y = stage_y + stage_h + 55
    logits_cx = (centers[5][0] + centers[5][1]) / 2
    canvas.add_arrow(logits_cx, stage_y + stage_h, logits_cx, softmax_y - 4, style="solid", color="#333333", stroke_width=1.5)
    softmax_w, softmax_h = 170, 55
    softmax_x = logits_cx - softmax_w / 2
    canvas.add_rect(softmax_x, softmax_y, softmax_w, softmax_h, fill=orange, stroke="#333333", stroke_width=2)
    canvas.add_text(logits_cx, softmax_y + softmax_h / 2 + 4, "softmax", size=17, color="#ffffff", anchor="middle")

    dist_y = softmax_y + softmax_h + 40
    canvas.add_arrow(logits_cx, softmax_y + softmax_h, logits_cx, dist_y - 4, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_text(20, dist_y, "next-token probability distribution over the whole vocabulary:", size=18, weight="bold")
    bar_y = dist_y + 34
    bar_h_max = 60
    probs = [0.05, 0.62, 0.10, 0.18, 0.03, 0.02]
    tok_labels = ["the", "cat", "dog", "sat", "runs", "..."]
    bar_w = 54
    bar_gap = 20
    bx = 20
    for p, lab in zip(probs, tok_labels):
        h = p * bar_h_max / max(probs)
        canvas.add_rect(bx, bar_y + (bar_h_max - h), bar_w, h, fill=blue if lab != "cat" else colors["bottleneck_or_failure"],
                         stroke="#333333", stroke_width=1.5)
        canvas.add_text(bx + bar_w / 2, bar_y + bar_h_max + 22, lab, size=16, anchor="middle")
        canvas.add_text(bx + bar_w / 2, bar_y + (bar_h_max - h) - 8, f"{p:.2f}", size=16, anchor="middle", color="#333333")
        bx += bar_w + bar_gap

    canvas.add_text(bx + 10, bar_y + bar_h_max / 2, "one token is sampled/chosen from this distribution", size=13, color="#555555")

    legend_y = bar_y + bar_h_max + 70
    canvas.add_rect(20, legend_y, 16, 16, fill=blue)
    canvas.add_text(42, legend_y + 13, "stored (tokens / embeddings / vocabulary scores)", size=16)
    canvas.add_rect(20, legend_y + 30, 16, 16, fill=orange)
    canvas.add_text(42, legend_y + 43, "computation (a stage that transforms the vector)", size=16)

    canvas.height = legend_y + 65
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
