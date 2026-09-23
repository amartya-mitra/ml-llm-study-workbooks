"""Chapter 4 figure: sliding-window receptive field across stacked
layers.

What to notice: at the top (output) layer, the target position's
DIRECT window is narrow (width W). Tracing back down through earlier
layers, the region of original input positions that can INDIRECTLY
influence that same output position widens by W at each layer -- by
the input layer, the effective reach is L * W, wider than any single
layer's direct window, but this is indirect, multi-layer influence,
not unrestricted global attention.

Run: python3 workbooks/04-llm-architecture/figures/source/fig_sliding_window_receptive_field.py
Output: figures/rendered/fig-sliding-window-receptive-field.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-sliding-window-receptive-field"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

# Full-width (6.5in) embed, W=760 -> 1 unit = 6.5*72/760 = 0.6158pt.
# Need ~14.6 units for a 9pt essential label.
LABEL_SIZE = 16
TITLE_SIZE = 18

N_POS = 16
CELL = 38
WINDOW_W = 4
TARGET_COL = 12  # 0-indexed


def row(canvas, y, direct_lo, direct_hi, reach_lo, reach_hi, fill, dash, row_label):
    for c in range(N_POS):
        x = 40 + c * CELL
        in_reach = reach_lo <= c <= reach_hi
        in_direct = direct_lo is not None and direct_lo <= c <= direct_hi
        if in_direct:
            canvas.add_rect(x, y, CELL - 4, CELL - 4, fill=fill, stroke="#333333", stroke_width=2, rx=3)
        elif in_reach:
            canvas.add_rect(x, y, CELL - 4, CELL - 4, fill=fill, stroke="#333333", stroke_width=1.5, dash=dash, rx=3)
        else:
            canvas.add_rect(x, y, CELL - 4, CELL - 4, fill="#f0f0f0", stroke="#cccccc", stroke_width=1, rx=3)
    canvas.add_text(40 + N_POS * CELL + 20, y + (CELL - 4) / 2 + 6, row_label, size=LABEL_SIZE, anchor="start")


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    blue = colors["stored_information"]

    W = 40 + N_POS * CELL + 260
    canvas = SVGCanvas(width=W, height=1, title="Sliding-window receptive field across stacked layers")

    canvas.add_text(20, 26, "Target position's receptive field, by layer (window W = 4)", size=TITLE_SIZE, weight="bold")

    y_l3 = 50
    y_l2 = y_l3 + CELL + 30
    y_l1 = y_l2 + CELL + 30

    t = TARGET_COL
    # Layer 3 (output/top): direct window only, width W.
    row(canvas, y_l3, t - WINDOW_W + 1, t, t - WINDOW_W + 1, t, blue, None, "layer 3: direct window (W)")
    # Layer 2: indirect reach widens to 2W.
    row(canvas, y_l2, None, None, t - 2 * WINDOW_W + 1, t, blue, "dashed", "layer 2: indirect reach (2W)")
    # Layer 1 (input): indirect reach widens to 3W.
    row(canvas, y_l1, None, None, t - 3 * WINDOW_W + 1, t, blue, "dotted", "layer 1: indirect reach (3W)")

    # Target marker: vertical line through the target column across all rows.
    tx = 40 + t * CELL + (CELL - 4) / 2
    canvas.add_arrow(tx, y_l1 + CELL, tx, y_l3 - 8, style="dashed", color="#888888", stroke_width=1)
    canvas.add_text(tx, y_l3 - 12, "target position", size=LABEL_SIZE - 2, color="#555555", anchor="middle")

    legend_y = y_l1 + CELL + 40
    canvas.add_rect(40, legend_y, 30, 22, fill=blue, stroke="#333333", stroke_width=2, rx=3)
    canvas.add_text(80, legend_y + 16, "direct window (this layer's own attention)", size=LABEL_SIZE)
    canvas.add_rect(40, legend_y + 32, 30, 22, fill=blue, stroke="#333333", stroke_width=1.5, dash="dashed", rx=3)
    canvas.add_text(80, legend_y + 48, "indirect (reached only via an earlier layer)", size=LABEL_SIZE)
    canvas.add_text(40, legend_y + 80, "Stacking layers widens indirect reach; this is not the same as unrestricted global attention.",
                     size=LABEL_SIZE, color="#555555")

    canvas.height = legend_y + 110
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
