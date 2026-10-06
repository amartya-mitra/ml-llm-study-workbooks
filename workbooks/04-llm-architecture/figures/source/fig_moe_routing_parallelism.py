"""Chapter 5 figure: routing and expert parallelism, combined into one
figure (not a detailed networking diagram).

What to notice: tokens dispatch to whichever device holds their
selected expert, and results return to the token's originating
position -- and routing can be imbalanced, putting more tokens (and
more dispatch traffic) on one device than another.

Run: python3 workbooks/04-llm-architecture/figures/source/fig_moe_routing_parallelism.py
Output: figures/rendered/fig-moe-routing-parallelism.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-moe-routing-parallelism"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

# Full-width (6.5in) embed, W=820 -> 1 unit = 0.57pt; need ~15.8 for 9pt.
TITLE_SIZE = 18
LABEL_SIZE = 16
SMALL_SIZE = 14
# Baseline of the "device N" labels, measured down from the top edge of
# each dashed device boundary (experts start 30 units below that edge).
DEVICE_LABEL_DY = 22
# The "device 1" label is nudged right of the box centre so it sits in the
# corridor between the t3->E1 and t4->E2 dispatch arrows (>= 20 units of
# clearance each side); "device 2" has a clear centre and is not nudged.
DEVICE1_LABEL_DX = 15


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    blue = colors["stored_information"]
    orange = colors["computation"]
    purple = colors["device_communication"]
    red = colors["bottleneck_or_failure"]

    W = 820
    canvas = SVGCanvas(width=W, height=1, title="Token routing across devices, with one imbalanced pattern")

    canvas.add_text(W / 2, 24, "6 tokens, top-1 routing, 4 experts split across 2 devices", size=TITLE_SIZE, weight="bold", anchor="middle")

    # Tokens.
    n_tok = 6
    tok_w, gap = 60, 20
    total_tok_w = n_tok * tok_w + (n_tok - 1) * gap
    tx0 = (W - total_tok_w) / 2
    tok_centers = []
    for i in range(n_tok):
        tx = tx0 + i * (tok_w + gap)
        canvas.add_rect(tx, 45, tok_w, 30, fill=blue, stroke="#333333", stroke_width=1.2, rx=4)
        canvas.add_text(tx + tok_w / 2, 65, f"t{i+1}", size=SMALL_SIZE, color="#ffffff", anchor="middle")
        tok_centers.append(tx + tok_w / 2)

    router_y = 110
    router_w, router_h = 160, 36
    router_x = W / 2 - router_w / 2
    for cx in tok_centers:
        canvas.add_arrow(cx, 75, router_x + router_w / 2, router_y, style="solid", color="#333333", stroke_width=1)
    canvas.add_rect(router_x, router_y, router_w, router_h, fill=orange, stroke="#333333", stroke_width=2, rx=6)
    canvas.add_text(router_x + router_w / 2, router_y + 24, "router", size=LABEL_SIZE, color="#ffffff", anchor="middle")

    # Two devices, each a dashed boundary containing 2 experts.
    dev_y, dev_h = router_y + router_h + 40, 110
    dev_w = 340
    dev1_x = W / 2 - dev_w - 20
    dev2_x = W / 2 + 20
    # Device labels sit just inside the top edge of each dashed boundary
    # (above the experts), not above the boundary: the dispatch arrows
    # from t2/t3 and t4 pass through the strip above the boundary and
    # crossed/crowded the "device 1" label there. Inside the boundary the
    # arrows are clear of the label's horizontal extent.
    canvas.add_rect(dev1_x, dev_y, dev_w, dev_h, fill="#ffffff", stroke=purple, stroke_width=2, dash="dashed", rx=8)
    canvas.add_text(dev1_x + dev_w / 2 + DEVICE1_LABEL_DX, dev_y + DEVICE_LABEL_DY, "device 1", size=LABEL_SIZE, weight="bold", anchor="middle")
    canvas.add_rect(dev2_x, dev_y, dev_w, dev_h, fill="#ffffff", stroke=purple, stroke_width=2, dash="dashed", rx=8)
    canvas.add_text(dev2_x + dev_w / 2, dev_y + DEVICE_LABEL_DY, "device 2", size=LABEL_SIZE, weight="bold", anchor="middle")

    # Experts within devices: E1,E2 on device1; E3,E4 on device2.
    exp_w, exp_h = 100, 50
    exp_y = dev_y + 30
    e1_x = dev1_x + 40
    e2_x = dev1_x + dev_w - 40 - exp_w
    e3_x = dev2_x + 40
    e4_x = dev2_x + dev_w - 40 - exp_w
    exp_positions = {1: e1_x, 2: e2_x, 3: e3_x, 4: e4_x}
    # Imbalanced assignment: t1,t2,t3 -> E1; t4 -> E2; t5 -> E3; t6 -> E4.
    assignment = {1: 1, 2: 1, 3: 1, 4: 2, 5: 3, 6: 4}
    load = {1: 3, 2: 1, 3: 1, 4: 1}
    for e, ex in exp_positions.items():
        overloaded = load[e] >= 3
        stroke = red if overloaded else "#333333"
        sw = 2.5 if overloaded else 1.5
        canvas.add_rect(ex, exp_y, exp_w, exp_h, fill=blue, stroke=stroke, stroke_width=sw, rx=6)
        canvas.add_text(ex + exp_w / 2, exp_y + 22, f"E{e}", size=LABEL_SIZE, color="#ffffff", anchor="middle")
        canvas.add_text(ex + exp_w / 2, exp_y + 40, f"{load[e]} token(s)", size=SMALL_SIZE, color="#ffffff", anchor="middle")

    for tok_idx, e in assignment.items():
        tx = tok_centers[tok_idx - 1]
        ex = exp_positions[e] + exp_w / 2
        color = red if load[e] >= 3 else "#333333"
        canvas.add_arrow(tx, 75 + 8, ex, exp_y - 4, style="solid", color=color, stroke_width=1)

    note_y = dev_y + dev_h + 30
    canvas.add_text(20, note_y, "Dispatch (router -> expert) and return (expert -> token) both cross the device boundary --",
                     size=SMALL_SIZE, color="#555555")
    canvas.add_text(20, note_y + 18, "\"all-to-all\": every device may need to send tokens to, and receive results from, every other device.",
                     size=SMALL_SIZE, color="#555555")

    legend_y = note_y + 45
    canvas.add_rect(20, legend_y, 16, 16, fill=blue, rx=2)
    canvas.add_text(44, legend_y + 13, "expert (stored on one device)", size=SMALL_SIZE)
    canvas.add_rect(320, legend_y, 16, 16, fill=blue, stroke=red, stroke_width=2.5, rx=2)
    canvas.add_text(344, legend_y + 13, "overloaded expert (this batch)", size=SMALL_SIZE)

    canvas.height = legend_y + 40
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
