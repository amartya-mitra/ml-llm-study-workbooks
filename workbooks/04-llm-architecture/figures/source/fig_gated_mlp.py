"""Chapter 2 figure: plain MLP vs. gated (SwiGLU-style) MLP.

What to notice: the gated MLP does not add a third sequential layer --
it adds a second PARALLEL branch (W3) that elementwise-multiplies
against the first branch's activated output before the final
projection (W2). That elementwise multiply is the entire difference.

Run: python3 figures/source/fig_gated_mlp.py
Output: figures/rendered/fig-gated-mlp.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-gated-mlp"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    orange = colors["computation"]
    blue = colors["stored_information"]

    # This figure embeds at 100% of the 6.5in text column, so 1 SVG unit =
    # 6.5*72/W points at final size. Sizes below target >= 8-9pt for
    # essential labels (box names) and >= 7pt for secondary annotations
    # (see the review notes behind scripts/build_ch01_02_review.py; this
    # figure was explicitly flagged for being unreadable at print size).
    W = 760
    canvas = SVGCanvas(width=W, height=1, title="Plain MLP vs. gated MLP")

    BOX_W = 130
    BOX_H = 34
    LABEL_SIZE = 15  # ~9.2pt at final size -- essential (names each weight matrix)
    SUB_LABEL_SIZE = 12  # ~7.4pt -- secondary parenthetical clarification

    canvas.add_text(20, 28, "Plain MLP (two matrices)", size=LABEL_SIZE, weight="bold")
    x0 = 20
    y0 = 50
    canvas.add_rect(x0, y0, BOX_W, BOX_H, fill=blue, stroke="#333333", stroke_width=2)
    canvas.add_text(x0 + BOX_W / 2, y0 + 22, "input x", size=LABEL_SIZE, color="#ffffff", anchor="middle")
    canvas.add_arrow(x0 + BOX_W / 2, y0 + BOX_H, x0 + BOX_W / 2, y0 + BOX_H + 20, style="solid", color="#333333", stroke_width=1.5)
    y1 = y0 + BOX_H + 20
    canvas.add_rect(x0, y1, BOX_W, BOX_H, fill=orange, stroke="#333333", stroke_width=2)
    canvas.add_text(x0 + BOX_W / 2, y1 + 22, "W1, activation", size=LABEL_SIZE, color="#ffffff", anchor="middle")
    canvas.add_arrow(x0 + BOX_W / 2, y1 + BOX_H, x0 + BOX_W / 2, y1 + BOX_H + 20, style="solid", color="#333333", stroke_width=1.5)
    y2 = y1 + BOX_H + 20
    canvas.add_rect(x0, y2, BOX_W, BOX_H, fill=orange, stroke="#333333", stroke_width=2)
    canvas.add_text(x0 + BOX_W / 2, y2 + 22, "W2", size=LABEL_SIZE, color="#ffffff", anchor="middle")
    canvas.add_arrow(x0 + BOX_W / 2, y2 + BOX_H, x0 + BOX_W / 2, y2 + BOX_H + 20, style="solid", color="#333333", stroke_width=1.5)
    y3 = y2 + BOX_H + 20
    canvas.add_rect(x0, y3, BOX_W, BOX_H, fill=blue, stroke="#333333", stroke_width=2)
    canvas.add_text(x0 + BOX_W / 2, y3 + 22, "output", size=LABEL_SIZE, color="#ffffff", anchor="middle")
    canvas.add_text(x0, y3 + BOX_H + 26, "one path, two weight matrices (W1, W2)", size=SUB_LABEL_SIZE, color="#555555")

    gx0 = 300
    canvas.add_text(gx0, 28, "Gated MLP / SwiGLU (three matrices)", size=LABEL_SIZE, weight="bold")

    left_x = gx0 + 20
    right_x = gx0 + 280
    left_c = left_x + BOX_W / 2
    right_c = right_x + BOX_W / 2
    mult_x = (left_c + right_c) / 2
    input_x = mult_x - BOX_W / 2

    canvas.add_rect(input_x, y0, BOX_W, BOX_H, fill=blue, stroke="#333333", stroke_width=2)
    canvas.add_text(mult_x, y0 + 22, "input x", size=LABEL_SIZE, color="#ffffff", anchor="middle")

    canvas.add_arrow(input_x + 25, y0 + BOX_H, left_c, y1, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_arrow(input_x + BOX_W - 25, y0 + BOX_H, right_c, y1, style="solid", color="#333333", stroke_width=1.5)

    two_line_h = BOX_H + 12
    canvas.add_rect(left_x, y1, BOX_W, two_line_h, fill=orange, stroke="#333333", stroke_width=2)
    canvas.add_text(left_c, y1 + 20, "W1", size=LABEL_SIZE, color="#ffffff", anchor="middle")
    canvas.add_text(left_c, y1 + 38, "(gate, activated)", size=SUB_LABEL_SIZE, color="#ffffff", anchor="middle")

    canvas.add_rect(right_x, y1, BOX_W, two_line_h, fill=orange, stroke="#333333", stroke_width=2)
    canvas.add_text(right_c, y1 + 20, "W3", size=LABEL_SIZE, color="#ffffff", anchor="middle")
    canvas.add_text(right_c, y1 + 38, "(value, linear)", size=SUB_LABEL_SIZE, color="#ffffff", anchor="middle")

    mult_r = 14
    mult_y = y1 + two_line_h + 40
    canvas.add_arrow(left_c, y1 + two_line_h, mult_x - 12, mult_y - 12, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_arrow(right_c, y1 + two_line_h, mult_x + 12, mult_y - 12, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_raw(f'<circle cx="{mult_x}" cy="{mult_y}" r="{mult_r}" fill="#ffffff" stroke="#333333" stroke-width="1.5"/>')
    canvas.add_text(mult_x, mult_y + 5, "x", size=16, weight="bold", anchor="middle")
    canvas.add_text(mult_x, mult_y + mult_r + 16, "elementwise multiply", size=SUB_LABEL_SIZE, color="#555555", anchor="middle")

    y4 = mult_y + mult_r + 32
    canvas.add_arrow(mult_x, mult_y + mult_r, mult_x, y4, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_rect(mult_x - BOX_W / 2, y4, BOX_W, BOX_H, fill=orange, stroke="#333333", stroke_width=2)
    canvas.add_text(mult_x, y4 + 22, "W2", size=LABEL_SIZE, color="#ffffff", anchor="middle")
    y5 = y4 + BOX_H + 20
    canvas.add_arrow(mult_x, y4 + BOX_H, mult_x, y5, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_rect(mult_x - BOX_W / 2, y5, BOX_W, BOX_H, fill=blue, stroke="#333333", stroke_width=2)
    canvas.add_text(mult_x, y5 + 22, "output", size=LABEL_SIZE, color="#ffffff", anchor="middle")

    note_y = y5 + BOX_H + 26
    canvas.add_text(20, note_y, "two parallel paths (W1, W3) meet at a multiply before the shared W2 -- three weight matrices total", size=SUB_LABEL_SIZE, color="#555555")

    canvas.height = max(y3 + BOX_H + 45, note_y + 25)
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
