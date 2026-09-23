"""Chapter 1 figure: one decoder block and its residual stream.

What to notice: the residual stream (the vertical bar) is never replaced
end to end -- each sublayer reads a normalized copy of it, computes an
update, and adds that update back onto the *original, un-normalized*
stream. The stream's width never changes across the block.

Run: python3 figures/source/fig_decoder_block_anatomy.py
Output: figures/rendered/fig-decoder-block-anatomy.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-decoder-block-anatomy"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")


# Box/font sizes below target >= 8pt printed at this figure's actual
# embed width (48% of the 6.5in text column -> 1 SVG unit = 0.48*6.5*72/W
# points). That ratio is much smaller than a 100%-embed figure's, so
# essential labels need much larger SVG-unit sizes than they would at
# full width -- see the review notes behind scripts/build_ch01_02_review.py.
NORM_W, NORM_H = 90, 32
SUB_W, SUB_H = 220, 46
PLUS_R = 15
BRANCH_DX = 160
LABEL_SIZE = 20  # ~8.0pt at final size -- essential (names each sublayer/norm)


def branch(canvas, stream_x, y0, label_norm, label_sublayer, fill, colors, side=1):
    """Draw one residual branch: stream -> norm -> sublayer -> back to stream."""
    branch_x = stream_x + side * BRANCH_DX
    canvas.add_arrow(stream_x + side * 6, y0 + 16, branch_x - side * (NORM_W / 2), y0 + 16,
                      style="solid", color="#333333", stroke_width=1.5)
    norm_x = branch_x - NORM_W / 2
    canvas.add_rect(norm_x, y0, NORM_W, NORM_H, fill="#ffffff", stroke="#333333", stroke_width=1.5)
    canvas.add_text(branch_x, y0 + NORM_H / 2 + 6, label_norm, size=LABEL_SIZE, anchor="middle")

    canvas.add_arrow(branch_x, y0 + NORM_H, branch_x, y0 + NORM_H + 22, style="solid", color="#333333", stroke_width=1.5)

    sub_y = y0 + NORM_H + 22
    sub_x = branch_x - SUB_W / 2
    canvas.add_rect(sub_x, sub_y, SUB_W, SUB_H, fill=fill, stroke="#333333", stroke_width=2)
    canvas.add_text(branch_x, sub_y + SUB_H / 2 + 6, label_sublayer, size=LABEL_SIZE, color="#ffffff", anchor="middle")

    plus_y = sub_y + SUB_H + 30
    canvas.add_arrow(branch_x, sub_y + SUB_H, branch_x, plus_y - PLUS_R - 1, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_raw(f'<circle cx="{branch_x}" cy="{plus_y}" r="{PLUS_R}" fill="#ffffff" stroke="#333333" stroke-width="1.5"/>')
    canvas.add_text(branch_x, plus_y + 6, "+", size=20, weight="bold", anchor="middle")
    canvas.add_arrow(branch_x - side * (NORM_W / 2), plus_y, stream_x + side * 6, plus_y,
                      style="solid", color="#333333", stroke_width=1.5)
    return plus_y


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    blue = colors["stored_information"]
    orange = colors["computation"]

    W = 560
    canvas = SVGCanvas(width=W, height=1, title="Decoder block anatomy: residual stream with two sublayers")

    # Stream sits left-of-center (not dead center) so the branch column has
    # enough width for the wider, more-legible boxes below without pushing
    # past the canvas edge.
    stream_x = 170
    top_y = 30

    canvas.add_text(stream_x, top_y - 12, "residual stream (in)", size=20, color="#555555", anchor="middle")
    canvas.add_arrow(stream_x, top_y, stream_x, top_y + 20, style="solid", color=blue, stroke_width=3)

    y1 = branch(canvas, stream_x, top_y + 30, "norm", "attention sublayer", orange, colors, side=1)
    canvas.add_arrow(stream_x, top_y + 30 - 10, stream_x, y1 - 11, style="solid", color=blue, stroke_width=3)

    y2 = branch(canvas, stream_x, y1 + 30, "norm", "MLP sublayer", orange, colors, side=1)
    canvas.add_arrow(stream_x, y1, stream_x, y2 + 30 - 20, style="solid", color=blue, stroke_width=3)

    canvas.add_arrow(stream_x, y2, stream_x, y2 + 40, style="solid", color=blue, stroke_width=3)
    canvas.add_text(stream_x, y2 + 60, "residual stream (out)", size=20, color="#555555", anchor="middle")

    # An earlier version repeated, inside the figure, the same "reads a
    # normalized copy, adds back onto the original" explanation that is
    # already in the surrounding prose and this figure's own caption
    # (see @eq-residual-update's discussion in the chapter text) -- at
    # this figure's 48%-embed size that explanatory text could not be
    # enlarged to a legible point size without overflowing the branch
    # column, and removing it loses no information the reader doesn't
    # already have from the prose/caption.

    legend_y = y2 + 95
    canvas.add_rect(30, legend_y, 16, 4, fill=blue)
    canvas.add_text(54, legend_y + 7, "residual stream (constant width)", size=20)
    canvas.add_rect(30, legend_y + 32, 16, 16, fill=orange)
    canvas.add_text(54, legend_y + 45, "computation (a sublayer)", size=20)

    canvas.height = legend_y + 70
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
