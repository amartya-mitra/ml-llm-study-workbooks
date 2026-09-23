"""Chapter 3 figure: MHA vs. GQA vs. MQA as one head-sharing axis.

What to notice: the number of QUERY heads (H_q = 8) is identical in all
three panels -- nothing removes a query head. What changes is how many
KEY/VALUE heads those query heads fan into: 8 (no sharing, MHA), 2
(groups of 4 share a K/V head, GQA), or 1 (every query head shares the
same K/V head, MQA).

Run: python3 workbooks/04-llm-architecture/figures/source/fig_mha_mqa_gqa_head_sharing.py
Output: figures/rendered/fig-mha-mqa-gqa-head-sharing.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-mha-mqa-gqa-head-sharing"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

# Full-width (6.5in) embed -> 1 unit = 6.5*72/W points. W=900 needs
# ~17.3 units for a 9pt essential label; used 18 for headroom.
LABEL_SIZE = 18       # ~9.4pt at final size -- essential (panel titles, H_kv values)
SMALL_LABEL = 15      # ~7.8pt -- secondary (per-box "q" labels)
Q_BOX = 26
KV_BOX_W, KV_BOX_H = 70, 34
H_Q = 8


def panel(canvas, x0, y0, panel_w, title, h_kv, colors, group_size=None):
    blue = colors["stored_information"]
    orange = colors["computation"]

    canvas.add_text(x0 + panel_w / 2, y0, title, size=LABEL_SIZE, weight="bold", anchor="middle")
    canvas.add_text(x0 + panel_w / 2, y0 + 22, f"H_q = {H_Q}, H_kv = {h_kv}", size=SMALL_LABEL, color="#555555", anchor="middle")

    q_y = y0 + 45
    q_gap = (panel_w - H_Q * Q_BOX) / (H_Q + 1)
    q_centers = []
    for i in range(H_Q):
        qx = x0 + q_gap + i * (Q_BOX + q_gap)
        canvas.add_rect(qx, q_y, Q_BOX, Q_BOX, fill=blue, stroke="#333333", stroke_width=1.5, rx=3)
        canvas.add_text(qx + Q_BOX / 2, q_y + Q_BOX / 2 + 5, "q", size=SMALL_LABEL, color="#ffffff", anchor="middle")
        q_centers.append(qx + Q_BOX / 2)

    kv_y = q_y + Q_BOX + 55
    kv_box_w = min(KV_BOX_W, max(Q_BOX, panel_w / h_kv - 8))
    kv_gap = panel_w / (h_kv + 1)
    kv_centers = []
    for j in range(h_kv):
        kvx = x0 + kv_gap * (j + 1) - kv_box_w / 2
        canvas.add_rect(kvx, kv_y, kv_box_w, KV_BOX_H, fill=orange, stroke="#333333", stroke_width=2, rx=5)
        label = "K/V" if kv_box_w >= 40 else ""
        if label:
            canvas.add_text(kvx + kv_box_w / 2, kv_y + KV_BOX_H / 2 + 5, label, size=SMALL_LABEL, color="#ffffff", anchor="middle")
        kv_centers.append(kvx + kv_box_w / 2)

    # Fan-in arrows: query head i shares KV head (i // group_size).
    gs = H_Q // h_kv
    for i, qx in enumerate(q_centers):
        kv_idx = i // gs
        canvas.add_arrow(qx, q_y + Q_BOX, kv_centers[kv_idx], kv_y, style="solid", color="#333333", stroke_width=1.2)

    note_y = kv_y + KV_BOX_H + 26
    if h_kv == H_Q:
        note_lines = ["no sharing", "(1 : 1)"]
    elif h_kv == 1:
        note_lines = ["maximum sharing", "(all : 1)"]
    else:
        note_lines = [f"groups of {gs} share", "one K/V head"]
    for i, line in enumerate(note_lines):
        canvas.add_text(x0 + panel_w / 2, note_y + i * 18, line, size=SMALL_LABEL, color="#555555", anchor="middle")
    return note_y + (len(note_lines) - 1) * 18


def main():
    style = load_visual_style()
    colors = palette_hex(style)

    W = 900
    canvas = SVGCanvas(width=W, height=1, title="MHA vs. MQA vs. GQA head-sharing")

    panel_w = W / 3 - 10
    gap = 15
    last_y = 0
    last_y = max(last_y, panel(canvas, 0, 25, panel_w, "MHA", H_Q, colors))
    last_y = max(last_y, panel(canvas, panel_w + gap, 25, panel_w, "GQA", 2, colors))
    last_y = max(last_y, panel(canvas, 2 * (panel_w + gap), 25, panel_w, "MQA", 1, colors))

    legend_y = last_y + 40
    blue = colors["stored_information"]
    orange = colors["computation"]
    canvas.add_rect(20, legend_y, 18, 18, fill=blue, rx=3)
    canvas.add_text(46, legend_y + 14, "query head", size=SMALL_LABEL)
    canvas.add_rect(260, legend_y, 18, 18, fill=orange, rx=5)
    canvas.add_text(286, legend_y + 14, "key/value head (cached)", size=SMALL_LABEL)

    canvas.height = legend_y + 40
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
