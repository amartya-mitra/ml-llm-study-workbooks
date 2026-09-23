"""Chapter 3 figure: logical Q/K/V tensor shapes, MHA vs. GQA.

What to notice: the Q shape's H_q axis is identical in both rows. Only
the K/V shape's head axis shrinks from H_q to H_kv -- that is the one
change GQA makes to the tensor shapes established in chapter 1.

Run: python3 workbooks/04-llm-architecture/figures/source/fig_tensor_shape_gqa.py
Output: figures/rendered/fig-tensor-shape-gqa.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-tensor-shape-gqa"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

# Full-width (6.5in) embed, W=800 -> ~15.4 units needed for 9pt; use 16.
LABEL_SIZE = 16    # ~9.4pt at final size -- essential (shape labels)
ROW_LABEL_SIZE = 18
BOX_W, BOX_H = 210, 60


def shape_box(canvas, x, y, lines, fill, colors, highlight=False):
    stroke = colors["bottleneck_or_failure"] if highlight else "#333333"
    sw = 3 if highlight else 1.5
    canvas.add_rect(x, y, BOX_W, BOX_H, fill=fill, stroke=stroke, stroke_width=sw, rx=6)
    n = len(lines)
    for i, line in enumerate(lines):
        ly = y + BOX_H / 2 - (n - 1) * 11 + i * 22 + 5
        color = "#ffffff" if fill != "#ffffff" else "#111111"
        canvas.add_text(x + BOX_W / 2, ly, line, size=LABEL_SIZE, color=color, anchor="middle", mono=True)


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    blue = colors["stored_information"]

    W = 800
    canvas = SVGCanvas(width=W, height=1, title="Tensor shapes: MHA vs. GQA (Q unchanged, K/V's head axis shrinks)")

    x_q, x_kv, x_v = 40, 300, 560
    gap_row = 150

    canvas.add_text(20, 40, "MHA", size=ROW_LABEL_SIZE, weight="bold", anchor="start")
    y_mha = 55
    shape_box(canvas, x_q, y_mha, ["Q:", "(B, T_q, H_q, d_head)"], "#ffffff", colors)
    shape_box(canvas, x_kv, y_mha, ["K:", "(B, S, H_kv, d_head)", "H_kv = H_q"], blue, colors)
    shape_box(canvas, x_v, y_mha, ["V:", "(B, S, H_kv, d_head)", "H_kv = H_q"], blue, colors)

    y_gqa = y_mha + gap_row
    canvas.add_text(20, y_gqa - 15, "GQA", size=ROW_LABEL_SIZE, weight="bold", anchor="start")
    shape_box(canvas, x_q, y_gqa, ["Q:", "(B, T_q, H_q, d_head)"], "#ffffff", colors)
    shape_box(canvas, x_kv, y_gqa, ["K:", "(B, S, H_kv, d_head)", "H_kv < H_q"], blue, colors, highlight=True)
    shape_box(canvas, x_v, y_gqa, ["V:", "(B, S, H_kv, d_head)", "H_kv < H_q"], blue, colors, highlight=True)

    note_y = y_gqa + BOX_H + 40
    canvas.add_text(40, note_y, "Q's shape never changes between MHA and GQA -- only K/V's head axis (outlined in red) shrinks.",
                     size=LABEL_SIZE, color="#555555")
    canvas.add_text(40, note_y + 26, "Group size = H_q / H_kv (e.g. H_q=8, H_kv=2 -> each K/V head serves a group of 4 query heads).",
                     size=LABEL_SIZE, color="#555555")

    canvas.height = note_y + 55
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
