"""Chapter 1 figure: causal attention visibility.

What to notice: a query at position i can attend to every key at
position <= i, including itself, and nothing after it. The allowed
region is a solid lower-triangular block, not a single-step lookback --
this directly corrects the "only attends to the immediately previous
token" misconception.

Tokens match the chapter's worked example (prompt "The cat sat on",
decoded token "the") so this figure and the worked example are the same
concrete case, not two different toy examples.

Run: python3 figures/source/fig_causal_attention_mask.py
Output: figures/rendered/fig-causal-attention-mask.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-causal-attention-mask"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

TOKENS = ["The", "cat", "sat", "on", "the"]


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    blue = colors["stored_information"]
    gray = colors["frozen_or_inactive"]

    n = len(TOKENS)
    cell = 46
    grid_x0 = 130
    grid_y0 = 70

    W = grid_x0 + n * cell + 40
    canvas = SVGCanvas(width=W, height=1, title="Causal attention visibility")

    canvas.add_text(20, 30, "Which positions may each query attend to?", size=12, weight="bold")

    for j, tok in enumerate(TOKENS):
        cx = grid_x0 + j * cell + cell / 2
        canvas.add_text(cx, grid_y0 - 10, tok, size=10, anchor="middle")
    canvas.add_text(grid_x0 + n * cell / 2, grid_y0 - 28, "key position (attended TO)", size=9, color="#555555", anchor="middle")

    for i, tok in enumerate(TOKENS):
        cy = grid_y0 + i * cell + cell / 2
        canvas.add_text(grid_x0 - 14, cy + 4, tok, size=10, anchor="end")

    canvas.add_raw(
        f'<text x="20" y="{grid_y0 + n*cell/2}" font-size="9" fill="#555555" '
        f'transform="rotate(-90 20 {grid_y0 + n*cell/2})" text-anchor="middle">query position (attending FROM)</text>'
    )

    for i in range(n):
        for j in range(n):
            x = grid_x0 + j * cell
            y = grid_y0 + i * cell
            allowed = j <= i
            fill = blue if allowed else "#eeeeee"
            stroke = "#333333" if allowed else "#cccccc"
            canvas.add_rect(x, y, cell - 3, cell - 3, fill=fill, stroke=stroke, stroke_width=1.2, rx=3)
            if allowed:
                canvas.add_raw(
                    f'<rect x="{x}" y="{y}" width="{cell-3}" height="{cell-3}" rx="3" '
                    f'fill="none" stroke="#333333" stroke-width="0" />'
                )
                mark = "self" if j == i else "OK"
                canvas.add_text(x + (cell - 3) / 2, y + (cell - 3) / 2 + 4, mark, size=8,
                                 color="#ffffff", anchor="middle")
            else:
                canvas.add_text(x + (cell - 3) / 2, y + (cell - 3) / 2 + 4, "x", size=10,
                                 color="#aaaaaa", anchor="middle")

    legend_y = grid_y0 + n * cell + 30
    canvas.add_rect(grid_x0, legend_y, 16, 16, fill=blue)
    canvas.add_text(grid_x0 + 22, legend_y + 12, "allowed (key position <= query position)", size=9)
    canvas.add_rect(grid_x0, legend_y + 22, 16, 16, fill="#eeeeee", stroke="#cccccc")
    canvas.add_text(grid_x0 + 22, legend_y + 34, "blocked (key is in the future)", size=9)

    canvas.add_text(20, legend_y + 60, "Note: row 5 (the decoded token \"the\") can see all 5 columns -- prompt tokens",
                     size=9, color="#555555")
    canvas.add_text(20, legend_y + 75, "plus itself. No row can see anything to the right of its own position.",
                     size=9, color="#555555")

    canvas.height = legend_y + 95
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
