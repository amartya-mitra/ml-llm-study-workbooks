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


def branch(canvas, stream_x, y0, y1, label_norm, label_sublayer, fill, colors, side=1):
    """Draw one residual branch: stream -> norm -> sublayer -> back to stream."""
    branch_x = stream_x + side * 130
    canvas.add_arrow(stream_x + side * 6, y0 + 14, branch_x - 45 if side > 0 else branch_x + 45, y0 + 14,
                      style="solid", color="#333333", stroke_width=1.5)
    norm_w, norm_h = 70, 28
    norm_x = branch_x - norm_w / 2
    canvas.add_rect(norm_x, y0, norm_w, norm_h, fill="#ffffff", stroke="#333333", stroke_width=1.5)
    canvas.add_text(branch_x, y0 + norm_h / 2 + 4, label_norm, size=10, anchor="middle")

    canvas.add_arrow(branch_x, y0 + norm_h, branch_x, y0 + norm_h + 22, style="solid", color="#333333", stroke_width=1.5)

    sub_y = y0 + norm_h + 22
    sub_w, sub_h = 130, 44
    sub_x = branch_x - sub_w / 2
    canvas.add_rect(sub_x, sub_y, sub_w, sub_h, fill=fill, stroke="#333333", stroke_width=2)
    canvas.add_text(branch_x, sub_y + sub_h / 2 + 4, label_sublayer, size=11, color="#ffffff", anchor="middle")

    plus_y = sub_y + sub_h + 26
    canvas.add_arrow(branch_x, sub_y + sub_h, branch_x, plus_y - 10, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_raw(f'<circle cx="{branch_x}" cy="{plus_y}" r="11" fill="#ffffff" stroke="#333333" stroke-width="1.5"/>')
    canvas.add_text(branch_x, plus_y + 4, "+", size=14, weight="bold", anchor="middle")
    canvas.add_arrow(branch_x - side * 45 if side > 0 else branch_x + 45, plus_y, stream_x + side * 6, plus_y,
                      style="solid", color="#333333", stroke_width=1.5)
    return plus_y


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    blue = colors["stored_information"]
    orange = colors["computation"]

    W = 560
    canvas = SVGCanvas(width=W, height=1, title="Decoder block anatomy: residual stream with two sublayers")

    stream_x = W / 2
    top_y = 30
    bottom_y = 430

    canvas.add_text(stream_x, top_y - 10, "residual stream (in)", size=10, color="#555555", anchor="middle")
    canvas.add_arrow(stream_x, top_y, stream_x, top_y + 20, style="solid", color=blue, stroke_width=3)

    y1 = branch(canvas, stream_x, top_y + 30, None, "norm", "attention sublayer", orange, colors, side=1)
    canvas.add_arrow(stream_x, top_y + 30 - 10, stream_x, y1 - 11, style="solid", color=blue, stroke_width=3)

    y2 = branch(canvas, stream_x, y1 + 30, None, "norm", "MLP sublayer", orange, colors, side=1)
    canvas.add_arrow(stream_x, y1, stream_x, y2 + 30 - 20, style="solid", color=blue, stroke_width=3)

    canvas.add_arrow(stream_x, y2, stream_x, y2 + 40, style="solid", color=blue, stroke_width=3)
    canvas.add_text(stream_x, y2 + 55, "residual stream (out) -- same width as (in)", size=10, color="#555555", anchor="middle")

    canvas.add_text(30, top_y - 10, "each box below reads a normalized COPY", size=9, color="#777777")
    canvas.add_text(30, top_y + 4, "of the stream but adds its result back", size=9, color="#777777")
    canvas.add_text(30, top_y + 18, "onto the ORIGINAL stream value at +", size=9, color="#777777")

    legend_y = y2 + 85
    canvas.add_rect(30, legend_y, 16, 4, fill=blue)
    canvas.add_text(52, legend_y + 8, "residual stream (stored state, constant width)", size=9)
    canvas.add_rect(300, legend_y - 6, 16, 16, fill=orange)
    canvas.add_text(322, legend_y + 8, "computation (a sublayer)", size=9)

    canvas.height = legend_y + 30
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
