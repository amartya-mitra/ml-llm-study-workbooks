"""Chapter 2 figure: the multi-token prediction (MTP) training
objective, independent-heads design (Gloeckle et al., [@src-43]).

What to notice: every head reads the SAME shared hidden representation
z_t and predicts a DIFFERENT future offset (t+1, t+2, t+3); no head's
prediction depends on another head's output. This is explicitly a
TRAINING-TIME diagram -- at inference, by default, only the t+1 head
is kept and the others are discarded (stated directly in the figure,
not left implicit), which is why this is not an inference-time
decoding diagram and must not be read as one.

Run: python3 workbooks/05-llm-training/figures/source/fig_mtp_training_objective.py
Output: workbooks/05-llm-training/figures/rendered/fig-mtp-training-objective.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-mtp-training-objective"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

WIDTH = 960
HEIGHT = 610


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    blue = colors["stored_information"]
    orange = colors["computation"]
    green = colors["trainable_component"]
    gray = colors["frozen_or_inactive"]

    c = SVGCanvas(WIDTH, HEIGHT, title="Multi-token prediction training objective (independent heads)")

    # Banner: explicit training-time label, not inference-time.
    c.add_rect(20, 15, WIDTH - 40, 30, fill="#fdecea", stroke="#D55E00", stroke_width=1.5, rx=4)
    c.add_text(WIDTH / 2, 35, "TRAINING-TIME OBJECTIVE  —  not an inference-time decoding diagram", size=14, weight="bold", color="#D55E00", anchor="middle")

    # Context tokens row.
    ctx_tokens = ["x1", "x2", "...", "xt"]
    box_w, box_h, gap = 60, 40, 12
    total_w = len(ctx_tokens) * box_w + (len(ctx_tokens) - 1) * gap
    x0 = (WIDTH - total_w) / 2
    y_ctx = 70
    for i, tok in enumerate(ctx_tokens):
        x = x0 + i * (box_w + gap)
        c.add_rect(x, y_ctx, box_w, box_h, fill=blue, stroke="#333333")
        c.add_text(x + box_w / 2, y_ctx + 26, tok, size=15, color="#ffffff", anchor="middle")
    c.add_text(WIDTH / 2, y_ctx + box_h + 20, "observed context x_t:1", size=13, color="#555555", anchor="middle")

    # Shared trunk box.
    trunk_w, trunk_h = 220, 50
    trunk_x = (WIDTH - trunk_w) / 2
    y_trunk = y_ctx + box_h + 45
    c.add_arrow(WIDTH / 2, y_ctx + box_h + 20 + 8, WIDTH / 2, y_trunk, color="#333333")
    c.add_rect(trunk_x, y_trunk, trunk_w, trunk_h, fill=orange, stroke="#333333")
    c.add_text(WIDTH / 2, y_trunk + 22, "shared trunk f_s", size=15, weight="bold", color="#ffffff", anchor="middle")
    c.add_text(WIDTH / 2, y_trunk + 40, "produces hidden state z_t", size=12, color="#ffffff", anchor="middle")

    # Hidden state z_t.
    z_w, z_h = 140, 40
    z_x = (WIDTH - z_w) / 2
    y_z = y_trunk + trunk_h + 35
    c.add_arrow(WIDTH / 2, y_trunk + trunk_h, WIDTH / 2, y_z, color="#333333")
    c.add_rect(z_x, y_z, z_w, z_h, fill=blue, stroke="#333333")
    c.add_text(WIDTH / 2, y_z + 26, "z_t (shared)", size=14, color="#ffffff", anchor="middle")

    # Three independent heads, each fed the SAME z_t.
    heads = [("Head 1", "predicts x_(t+1)"), ("Head 2", "predicts x_(t+2)"), ("Head 3", "predicts x_(t+3)")]
    head_w, head_h = 190, 50
    head_gap = 40
    total_heads_w = 3 * head_w + 2 * head_gap
    hx0 = (WIDTH - total_heads_w) / 2
    y_heads = y_z + z_h + 55
    head_centers = []
    for i, (name, pred) in enumerate(heads):
        hx = hx0 + i * (head_w + head_gap)
        c.add_arrow(WIDTH / 2, y_z + z_h, hx + head_w / 2, y_heads, color="#888888", stroke_width=1.5)
        c.add_rect(hx, y_heads, head_w, head_h, fill=green, stroke="#333333")
        c.add_text(hx + head_w / 2, y_heads + 22, f"{name}  f_h{i+1}", size=14, weight="bold", color="#ffffff", anchor="middle")
        c.add_text(hx + head_w / 2, y_heads + 40, pred, size=12, color="#ffffff", anchor="middle")
        head_centers.append(hx + head_w / 2)

    # Individual losses, then combine.
    y_loss = y_heads + head_h + 45
    loss_w, loss_h = 150, 38
    for i, hx_center in enumerate(head_centers):
        c.add_arrow(hx_center, y_heads + head_h, hx_center, y_loss, color="#333333")
        c.add_rect(hx_center - loss_w / 2, y_loss, loss_w, loss_h, fill="#ffffff", stroke=orange, stroke_width=1.5)
        c.add_text(hx_center, y_loss + 24, f"loss_{i+1} = -log P(x_(t+{i+1}))", size=11, color="#333333", anchor="middle")

    y_combine = y_loss + loss_h + 45
    combine_w, combine_h = 400, 50
    combine_x = (WIDTH - combine_w) / 2
    for hx_center in head_centers:
        c.add_arrow(hx_center, y_loss + loss_h, combine_x + combine_w / 2, y_combine, color="#888888", stroke_width=1.5)
    c.add_rect(combine_x, y_combine, combine_w, combine_h, fill=gray, stroke="#333333")
    c.add_text(WIDTH / 2, y_combine + 22, "combined objective", size=13, weight="bold", color="#ffffff", anchor="middle")
    c.add_text(WIDTH / 2, y_combine + 40, "L_n = sum of all head losses", size=13, weight="bold", color="#ffffff", anchor="middle")

    c.add_text(WIDTH / 2, y_combine + combine_h + 28, "At inference (not shown): by default, only Head 1's next-token path is kept; Heads 2-3 are discarded.", size=12, color="#555555", anchor="middle")

    c.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
