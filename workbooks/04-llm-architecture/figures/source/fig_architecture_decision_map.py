"""Chapter 8 figure: an architecture decision map organizing chapters
1-7's mechanisms (plus looped depth and MTP) by the resource/behavior
each primarily changes.

What to notice: every mechanism sits under exactly one resource/
behavior header -- there is no mechanism that changes two axes at
once in this simplified view. MTP is drawn differently on purpose: it
has two dashed bridge arrows leading OFF the map to two future
workbooks, rather than sitting under a resource-dimension header like
the other six, because MTP's downstream use (as an optional
speculative-decoding draft source) is a separate design choice, not
implied by the training-time objective itself.

Run: python3 workbooks/04-llm-architecture/figures/source/fig_architecture_decision_map.py
Output: figures/rendered/fig-architecture-decision-map.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-architecture-decision-map"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

# Full-width (6.5in) embed, W=1120 -> 1 unit = 6.5*72/1120 = 0.4179pt.
# Need ~21.5 units for a 9pt essential label.
TITLE_SIZE = 17
LABEL_SIZE = 15
SMALL_SIZE = 14
TINY_SIZE = 13


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    blue = colors["stored_information"]
    purple = colors["device_communication"]

    W = 1120
    n = 7
    col_gap = 12
    col_w = (W - 20 - (n - 1) * col_gap) / n
    header_h = 46
    node_h = 50
    top = 40

    canvas = SVGCanvas(width=W, height=1, title="Architecture decision map")
    canvas.add_text(W / 2, 20, "Each mechanism grouped by the ONE resource/behavior it primarily changes", size=SMALL_SIZE, color="#555555", anchor="middle")

    headers = [
        "KV-head\nsharing", "Latent KV\nrepresentation", "Attended\npositions",
        "Conditional FFN\nparameters", "Sequence-state\nmechanism",
        "Depth-wise\nweight reuse", "Future-token\ntraining targets",
    ]
    mechanisms = ["GQA / MQA", "MLA", "Local / sparse\nattention", "MoE", "Hybrid\nrecurrence", "Looped depth", "MTP"]
    fills = [blue] * 6 + [purple]

    x = 10
    centers = []
    for i in range(n):
        canvas.add_rect(x, top, col_w, header_h, fill="#eeeeee", stroke="#333333", stroke_width=1.1, rx=4)
        lines = headers[i].split("\n")
        for li, line in enumerate(lines):
            canvas.add_text(x + col_w / 2, top + 20 + li * 16, line, size=TINY_SIZE, weight="bold", anchor="middle")

        ny = top + header_h + 14
        canvas.add_rect(x, ny, col_w, node_h, fill=fills[i], stroke="#333333", stroke_width=1.3, rx=5)
        mlines = mechanisms[i].split("\n")
        for li, line in enumerate(mlines):
            yoff = ny + node_h / 2 + (li - (len(mlines) - 1) / 2) * 17 + 5
            canvas.add_text(x + col_w / 2, yoff, line, size=SMALL_SIZE, weight="bold", color="#ffffff", anchor="middle")
        centers.append((x + col_w / 2, ny + node_h))
        x += col_w + col_gap

    # MTP bridge arrows (last column) -> two off-map boxes below.
    mtp_cx, mtp_bottom = centers[-1]
    bridge_y = mtp_bottom + 30
    box_w, box_h = 220, 46
    box1_x = W - 20 - 2 * box_w - 20
    box2_x = W - 20 - box_w

    canvas.add_arrow(mtp_cx, mtp_bottom, box1_x + box_w / 2, bridge_y, style="dashed", color="#555555", stroke_width=1.8)
    canvas.add_arrow(mtp_cx, mtp_bottom, box2_x + box_w / 2, bridge_y, style="dashed", color="#555555", stroke_width=1.8)

    canvas.add_rect(box1_x, bridge_y, box_w, box_h, fill="#ffffff", stroke="#555555", stroke_width=1.3, dash="dashed", rx=5)
    canvas.add_text(box1_x + box_w / 2, bridge_y + 20, "Workbook 5:", size=SMALL_SIZE, weight="bold", anchor="middle")
    canvas.add_text(box1_x + box_w / 2, bridge_y + 37, "training objective", size=SMALL_SIZE, anchor="middle")

    canvas.add_rect(box2_x, bridge_y, box_w, box_h, fill="#ffffff", stroke="#555555", stroke_width=1.3, dash="dashed", rx=5)
    canvas.add_text(box2_x + box_w / 2, bridge_y + 20, "Workbook 6:", size=SMALL_SIZE, weight="bold", anchor="middle")
    canvas.add_text(box2_x + box_w / 2, bridge_y + 37, "optional speculative-drafting use", size=TINY_SIZE, anchor="middle")

    note_y = bridge_y + box_h + 26
    canvas.add_text(10, note_y, "MTP is a training-time design choice, not itself a resource-axis mechanism or the speculative-decoding algorithm.", size=SMALL_SIZE, color="#555555")

    legend_y = note_y + 26
    canvas.add_rect(20, legend_y, 16, 16, fill=blue, rx=2)
    canvas.add_text(44, legend_y + 13, "resource/behavior-axis mechanism (ch. 1-7)", size=SMALL_SIZE)
    canvas.add_rect(340, legend_y, 16, 16, fill=purple, rx=2)
    canvas.add_text(364, legend_y + 13, "MTP -- bridges off-map, not a resource-axis mechanism itself", size=SMALL_SIZE)

    canvas.height = legend_y + 40
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
