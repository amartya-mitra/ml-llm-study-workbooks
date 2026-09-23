"""Chapter 2 figure: annotated modern decoder block.

What to notice: this is the exact same residual-stream skeleton as
Chapter 1's decoder block anatomy figure -- nothing about the SHAPE of
the block changed. What changed is which specific operation fills each
slot: RMSNorm fills the norm slots, RoPE is applied inside the
attention sublayer (not as a separate block), and SwiGLU fills the MLP
slot.

Run: python3 figures/source/fig_annotated_modern_block.py
Output: figures/rendered/fig-annotated-modern-block.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-annotated-modern-block"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    orange = colors["computation"]
    blue = colors["stored_information"]
    green = colors["trainable_component"]

    W = 460
    canvas = SVGCanvas(width=W, height=1, title="Annotated modern decoder block")
    stream_x = W / 2

    top_y = 30
    canvas.add_arrow(stream_x, top_y, stream_x, top_y + 20, style="solid", color=blue, stroke_width=3)

    y = top_y + 20
    canvas.add_rect(stream_x - 60, y, 120, 24, fill="#ffffff", stroke=green, stroke_width=2)
    canvas.add_text(stream_x, y + 16, "RMSNorm", size=10, weight="bold", anchor="middle")
    y += 24
    canvas.add_arrow(stream_x, y, stream_x, y + 16, style="solid", color="#333333", stroke_width=1.5)
    y += 16
    canvas.add_rect(stream_x - 75, y, 150, 52, fill=orange, stroke="#333333", stroke_width=2)
    canvas.add_text(stream_x, y + 20, "attention sublayer", size=10, color="#ffffff", anchor="middle")
    canvas.add_text(stream_x, y + 36, "(RoPE rotates Q, K", size=8, color="#ffffff", anchor="middle")
    canvas.add_text(stream_x, y + 47, "before the dot product)", size=8, color="#ffffff", anchor="middle")
    y += 52
    canvas.add_arrow(stream_x, y, stream_x, y + 16, style="solid", color="#333333", stroke_width=1.5)
    y += 16
    plus1_y = y + 11
    canvas.add_raw(f'<circle cx="{stream_x}" cy="{plus1_y}" r="11" fill="#ffffff" stroke="#333333" stroke-width="1.5"/>')
    canvas.add_text(stream_x, plus1_y + 4, "+", size=13, weight="bold", anchor="middle")
    canvas.add_raw(
        f'<path d="M {stream_x-90},{top_y+34} L {stream_x-90},{plus1_y} L {stream_x-11},{plus1_y}" '
        f'fill="none" stroke="{blue}" stroke-width="3"/>'
    )
    y = plus1_y + 11

    canvas.add_arrow(stream_x, y, stream_x, y + 20, style="solid", color=blue, stroke_width=3)
    y += 20
    canvas.add_rect(stream_x - 60, y, 120, 24, fill="#ffffff", stroke=green, stroke_width=2)
    canvas.add_text(stream_x, y + 16, "RMSNorm", size=10, weight="bold", anchor="middle")
    y += 24
    canvas.add_arrow(stream_x, y, stream_x, y + 16, style="solid", color="#333333", stroke_width=1.5)
    y += 16
    canvas.add_rect(stream_x - 75, y, 150, 40, fill=orange, stroke="#333333", stroke_width=2)
    canvas.add_text(stream_x, y + 24, "SwiGLU MLP", size=11, color="#ffffff", anchor="middle")
    y += 40
    canvas.add_arrow(stream_x, y, stream_x, y + 16, style="solid", color="#333333", stroke_width=1.5)
    y += 16
    plus2_y = y + 11
    canvas.add_raw(f'<circle cx="{stream_x}" cy="{plus2_y}" r="11" fill="#ffffff" stroke="#333333" stroke-width="1.5"/>')
    canvas.add_text(stream_x, plus2_y + 4, "+", size=13, weight="bold", anchor="middle")
    canvas.add_raw(
        f'<path d="M {stream_x-90},{plus1_y+11} L {stream_x-90},{plus2_y} L {stream_x-11},{plus2_y}" '
        f'fill="none" stroke="{blue}" stroke-width="3"/>'
    )
    y = plus2_y + 11
    canvas.add_arrow(stream_x, y, stream_x, y + 20, style="solid", color=blue, stroke_width=3)
    y += 20

    legend_y = y + 20
    canvas.add_rect(20, legend_y, 16, 16, fill=orange)
    canvas.add_text(42, legend_y + 12, "computation (attention / SwiGLU MLP)", size=9)
    canvas.add_rect(20, legend_y + 22, 16, 16, fill="#ffffff", stroke=green, stroke_width=2)
    canvas.add_text(42, legend_y + 34, "RMSNorm (fills the generic \"norm\" slot from ch. 1)", size=9)

    canvas.height = legend_y + 55
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
