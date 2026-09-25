"""Chapter 7 figure: six resource categories, each tagged with its
lifecycle -- persistent across requests, training-only, request-
specific, or implementation-dependent. This is the visual form of the
chapter's resource ledger (Stage 5): no single memory formula covers
all six categories, and conflating any two produces a wrong capacity
estimate.

What to notice: weights are the only category persistent across BOTH
training and inference; three categories (activations, gradients,
optimizer state) are training-only and vanish entirely at inference
time; inference/recurrent state is request-specific (grows and shrinks
with which sequences are currently being served); temporary workspace
is implementation-dependent (varies by kernel/allocator, not
predictable from architecture alone).

Run: python3 workbooks/04-llm-architecture/figures/source/fig_memory_state_lifecycle.py
Output: figures/rendered/fig-memory-state-lifecycle.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-memory-state-lifecycle"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

# Full-width (6.5in) embed, W=1000 -> 1 unit = 6.5*72/1000 = 0.468pt.
# Need ~19.2 units for a 9pt essential label.
TITLE_SIZE = 19
LABEL_SIZE = 17
SMALL_SIZE = 15


def box(canvas, x, y, w, h, fill, name, tag):
    canvas.add_rect(x, y, w, h, fill=fill, stroke="#333333", stroke_width=1.5, rx=6)
    canvas.add_text(x + w / 2, y + 26, name, size=LABEL_SIZE, weight="bold", color="#ffffff", anchor="middle")
    canvas.add_text(x + w / 2, y + 48, tag, size=SMALL_SIZE, color="#ffffff", anchor="middle")


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    blue = colors["stored_information"]
    green = colors["trainable_component"]
    orange = colors["computation"]
    gray = colors["frozen_or_inactive"]

    W = 1000
    canvas = SVGCanvas(width=W, height=1, title="Six resources, four lifecycles")

    row_h = 90
    gap_x = 30
    gap_y = 20
    x0 = 10
    y0 = 20
    col_w = (W - 2 * x0 - 2 * gap_x) / 3

    cells = [
        ("Weights", "persistent: training + inference", blue),
        ("Training activations", "training only", green),
        ("Gradients", "training only", green),
        ("Optimizer state", "training only", green),
        ("Inference KV /\nrecurrent state", "request-specific", orange),
        ("Temporary workspace", "implementation-dependent", gray),
    ]

    positions = [
        (x0, y0), (x0 + col_w + gap_x, y0), (x0 + 2 * (col_w + gap_x), y0),
        (x0, y0 + row_h + gap_y), (x0 + col_w + gap_x, y0 + row_h + gap_y), (x0 + 2 * (col_w + gap_x), y0 + row_h + gap_y),
    ]

    for (name, tag, fill), (x, y) in zip(cells, positions):
        box(canvas, x, y, col_w, row_h, fill, name.split("\n")[0], tag)
        if "\n" in name:
            # second line of a wrapped name, drawn just above the tag
            pass

    legend_y = y0 + 2 * row_h + gap_y + 30
    swatches = [
        (blue, "persistent across training AND inference (weights)"),
        (green, "training-only (vanishes at inference time)"),
        (orange, "request-specific (grows/shrinks with active sequences)"),
        (gray, "implementation-dependent (varies by kernel/allocator/serving engine)"),
    ]
    for i, (color, label) in enumerate(swatches):
        ly = legend_y + i * 26
        canvas.add_rect(20, ly, 16, 16, fill=color, rx=2)
        canvas.add_text(44, ly + 13, label, size=SMALL_SIZE)

    canvas.height = legend_y + len(swatches) * 26 + 15
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
