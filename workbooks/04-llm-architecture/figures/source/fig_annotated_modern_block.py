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

    # This figure embeds at 48% of the 6.5in text column, so 1 SVG unit =
    # 0.48*6.5*72/W points at final size -- a much smaller ratio than a
    # full-width figure gets, so labels need large SVG-unit sizes and wide
    # boxes to clear 8pt (see the review notes behind
    # scripts/build_ch01_02_review.py; this figure was explicitly flagged
    # for being unreadable at print size).
    W = 480
    canvas = SVGCanvas(width=W, height=1, title="Annotated modern decoder block")
    stream_x = W / 2

    NORM_W, NORM_H = 130, 32
    SUB_W = 230
    R = 13
    LABEL_SIZE = 19  # ~8.9pt at final size -- essential (names each component)
    SUB_LABEL_SIZE = 14  # ~6.5pt -- secondary clarification, kept well above the 6pt floor
    BYPASS_DX = SUB_W / 2 + 15

    top_y = 30
    canvas.add_arrow(stream_x, top_y, stream_x, top_y + 20, style="solid", color=blue, stroke_width=3)

    y = top_y + 20
    canvas.add_rect(stream_x - NORM_W / 2, y, NORM_W, NORM_H, fill="#ffffff", stroke=green, stroke_width=2)
    canvas.add_text(stream_x, y + NORM_H / 2 + 6, "RMSNorm", size=LABEL_SIZE, weight="bold", anchor="middle")
    y += NORM_H
    canvas.add_arrow(stream_x, y, stream_x, y + 16, style="solid", color="#333333", stroke_width=1.5)
    y += 16
    attn_h = 72
    canvas.add_rect(stream_x - SUB_W / 2, y, SUB_W, attn_h, fill=orange, stroke="#333333", stroke_width=2)
    canvas.add_text(stream_x, y + 24, "attention sublayer", size=LABEL_SIZE, color="#ffffff", anchor="middle")
    canvas.add_text(stream_x, y + 44, "(RoPE rotates Q, K", size=SUB_LABEL_SIZE, color="#ffffff", anchor="middle")
    canvas.add_text(stream_x, y + 60, "before the dot product)", size=SUB_LABEL_SIZE, color="#ffffff", anchor="middle")
    y += attn_h
    canvas.add_arrow(stream_x, y, stream_x, y + 16, style="solid", color="#333333", stroke_width=1.5)
    y += 16
    plus1_y = y + R
    canvas.add_raw(f'<circle cx="{stream_x}" cy="{plus1_y}" r="{R}" fill="#ffffff" stroke="#333333" stroke-width="1.5"/>')
    canvas.add_text(stream_x, plus1_y + 6, "+", size=18, weight="bold", anchor="middle")
    canvas.add_raw(
        f'<path d="M {stream_x-BYPASS_DX},{top_y+20} L {stream_x-BYPASS_DX},{plus1_y} L {stream_x-R},{plus1_y}" '
        f'fill="none" stroke="{blue}" stroke-width="3"/>'
    )
    y = plus1_y + R

    canvas.add_arrow(stream_x, y, stream_x, y + 20, style="solid", color=blue, stroke_width=3)
    y += 20
    canvas.add_rect(stream_x - NORM_W / 2, y, NORM_W, NORM_H, fill="#ffffff", stroke=green, stroke_width=2)
    canvas.add_text(stream_x, y + NORM_H / 2 + 6, "RMSNorm", size=LABEL_SIZE, weight="bold", anchor="middle")
    y += NORM_H
    canvas.add_arrow(stream_x, y, stream_x, y + 16, style="solid", color="#333333", stroke_width=1.5)
    y += 16
    mlp_h = 46
    canvas.add_rect(stream_x - SUB_W / 2, y, SUB_W, mlp_h, fill=orange, stroke="#333333", stroke_width=2)
    canvas.add_text(stream_x, y + mlp_h / 2 + 6, "SwiGLU MLP", size=LABEL_SIZE, color="#ffffff", anchor="middle")
    y += mlp_h
    canvas.add_arrow(stream_x, y, stream_x, y + 16, style="solid", color="#333333", stroke_width=1.5)
    y += 16
    plus2_y = y + R
    canvas.add_raw(f'<circle cx="{stream_x}" cy="{plus2_y}" r="{R}" fill="#ffffff" stroke="#333333" stroke-width="1.5"/>')
    canvas.add_text(stream_x, plus2_y + 6, "+", size=18, weight="bold", anchor="middle")
    canvas.add_raw(
        f'<path d="M {stream_x-BYPASS_DX},{plus1_y+R} L {stream_x-BYPASS_DX},{plus2_y} L {stream_x-R},{plus2_y}" '
        f'fill="none" stroke="{blue}" stroke-width="3"/>'
    )
    y = plus2_y + R
    canvas.add_arrow(stream_x, y, stream_x, y + 20, style="solid", color=blue, stroke_width=3)
    y += 20

    legend_y = y + 20
    canvas.add_rect(20, legend_y, 16, 16, fill=orange)
    canvas.add_text(42, legend_y + 13, "computation (attention / SwiGLU MLP)", size=18)
    canvas.add_rect(20, legend_y + 26, 16, 16, fill="#ffffff", stroke=green, stroke_width=2)
    canvas.add_text(42, legend_y + 26 + 13, "RMSNorm (fills the norm slot from ch. 1)", size=18)

    canvas.height = legend_y + 26 + 16 + 24
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
