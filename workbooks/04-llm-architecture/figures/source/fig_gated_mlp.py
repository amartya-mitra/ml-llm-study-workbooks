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

    W = 760
    canvas = SVGCanvas(width=W, height=1, title="Plain MLP vs. gated MLP")

    canvas.add_text(20, 25, "Plain MLP (two matrices)", size=12, weight="bold")
    x0 = 20
    y0 = 50
    canvas.add_rect(x0, y0, 90, 30, fill=blue, stroke="#333333", stroke_width=2)
    canvas.add_text(x0 + 45, y0 + 20, "input x", size=10, color="#ffffff", anchor="middle")
    canvas.add_arrow(x0 + 45, y0 + 30, x0 + 45, y0 + 50, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_rect(x0, y0 + 50, 90, 34, fill=orange, stroke="#333333", stroke_width=2)
    canvas.add_text(x0 + 45, y0 + 72, "W1, activation", size=9, color="#ffffff", anchor="middle")
    canvas.add_arrow(x0 + 45, y0 + 84, x0 + 45, y0 + 104, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_rect(x0, y0 + 104, 90, 30, fill=orange, stroke="#333333", stroke_width=2)
    canvas.add_text(x0 + 45, y0 + 124, "W2", size=10, color="#ffffff", anchor="middle")
    canvas.add_arrow(x0 + 45, y0 + 134, x0 + 45, y0 + 154, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_rect(x0, y0 + 154, 90, 30, fill=blue, stroke="#333333", stroke_width=2)
    canvas.add_text(x0 + 45, y0 + 174, "output", size=10, color="#ffffff", anchor="middle")
    canvas.add_text(x0 - 5, y0 + 210, "one path, two weight matrices (W1, W2)", size=9, color="#555555")

    gx0 = 320
    canvas.add_text(gx0, 25, "Gated MLP / SwiGLU (three matrices)", size=12, weight="bold")
    canvas.add_rect(gx0 + 90, y0, 90, 30, fill=blue, stroke="#333333", stroke_width=2)
    canvas.add_text(gx0 + 135, y0 + 20, "input x", size=10, color="#ffffff", anchor="middle")

    left_x = gx0 + 20
    right_x = gx0 + 250
    canvas.add_arrow(gx0 + 100, y0 + 30, left_x + 45, y0 + 50, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_arrow(gx0 + 170, y0 + 30, right_x + 45, y0 + 50, style="solid", color="#333333", stroke_width=1.5)

    canvas.add_rect(left_x, y0 + 50, 90, 34, fill=orange, stroke="#333333", stroke_width=2)
    canvas.add_text(left_x + 45, y0 + 68, "W1", size=10, color="#ffffff", anchor="middle")
    canvas.add_text(left_x + 45, y0 + 80, "(gate, activated)", size=8, color="#ffffff", anchor="middle")

    canvas.add_rect(right_x, y0 + 50, 90, 34, fill=orange, stroke="#333333", stroke_width=2)
    canvas.add_text(right_x + 45, y0 + 68, "W3", size=10, color="#ffffff", anchor="middle")
    canvas.add_text(right_x + 45, y0 + 80, "(value, linear)", size=8, color="#ffffff", anchor="middle")

    mult_y = y0 + 84 + 30
    mult_x = (left_x + 45 + right_x + 45) / 2
    canvas.add_arrow(left_x + 45, y0 + 84, mult_x - 10, mult_y - 10, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_arrow(right_x + 45, y0 + 84, mult_x + 10, mult_y - 10, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_raw(f'<circle cx="{mult_x}" cy="{mult_y}" r="13" fill="#ffffff" stroke="#333333" stroke-width="1.5"/>')
    canvas.add_text(mult_x, mult_y + 4, "x", size=13, weight="bold", anchor="middle")
    canvas.add_text(mult_x, mult_y + 22, "elementwise multiply", size=8, color="#555555", anchor="middle")

    canvas.add_arrow(mult_x, mult_y + 13, mult_x, mult_y + 38, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_rect(mult_x - 45, mult_y + 38, 90, 30, fill=orange, stroke="#333333", stroke_width=2)
    canvas.add_text(mult_x, mult_y + 58, "W2", size=10, color="#ffffff", anchor="middle")
    canvas.add_arrow(mult_x, mult_y + 68, mult_x, mult_y + 88, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_rect(mult_x - 45, mult_y + 88, 90, 30, fill=blue, stroke="#333333", stroke_width=2)
    canvas.add_text(mult_x, mult_y + 108, "output", size=10, color="#ffffff", anchor="middle")

    note_y = mult_y + 88 + 30 + 20
    canvas.add_text(gx0 - 20, note_y, "two parallel paths (W1, W3) meet at a multiply before the shared W2 -- three weight matrices total", size=9, color="#555555")

    canvas.height = note_y + 25
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
