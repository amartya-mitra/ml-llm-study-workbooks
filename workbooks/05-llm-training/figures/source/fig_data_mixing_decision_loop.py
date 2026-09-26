"""Chapter 1 figure: the data-mixing decision loop.

What to notice: candidate datasets are tested at small scale BEFORE any
mixing ratio is chosen for the main run, and the chosen mixture is not
fixed for the whole run -- a later annealing stage can swap in a
different blend. This is a schematic of a PROCESS (which order things
happen in), not a plot of any specific ablation's measured results --
no numeric benchmark scores are shown, since presenting invented
numbers as if measured would violate this project's sourcing policy.
The stage-1 mixing weights (0.7 / 0.2 / 0.1) are the one exception:
they are given as illustrative labels only, copied from the smol
training playbook's own disclosed 1B baseline ablation config [@src-16],
not implied as universal advice.

Run: python3 workbooks/05-llm-training/figures/source/fig_data_mixing_decision_loop.py
Output: workbooks/05-llm-training/figures/rendered/fig-data-mixing-decision-loop.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-data-mixing-decision-loop"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

WIDTH = 960
HEIGHT = 460
BOX_W = 170
BOX_H = 56


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    blue = colors["stored_information"]
    orange = colors["computation"]
    green = colors["trainable_component"]

    c = SVGCanvas(WIDTH, HEIGHT, title="The data-mixing decision loop")

    # Row 1: four candidate dataset domains (data at rest -> blue).
    domains = ["English web\n(FineWeb-Edu, DCLM)", "Multilingual\n(FineWeb2-HQ)", "Code\n(Stack-Edu, The Stack v2)", "Math\n(FineMath, InfiWebMath)"]
    gap = 20
    total_w = 4 * BOX_W + 3 * gap
    x0 = (WIDTH - total_w) / 2
    y1 = 30
    centers = []
    for i, label in enumerate(domains):
        x = x0 + i * (BOX_W + gap)
        c.add_rect(x, y1, BOX_W, BOX_H, fill=blue, stroke="#333333")
        for j, line in enumerate(label.split("\n")):
            c.add_text(x + BOX_W / 2, y1 + 22 + j * 16, line, size=13, color="#ffffff", anchor="middle")
        centers.append(x + BOX_W / 2)

    # Converge down to the ablation-sweep box (a compute process -> orange).
    y2 = y1 + BOX_H + 55
    sweep_x = (WIDTH - BOX_W) / 2
    for cx in centers:
        c.add_arrow(cx, y1 + BOX_H, sweep_x + BOX_W / 2, y2, color="#888888", stroke_width=1.5)
    c.add_rect(sweep_x, y2, BOX_W, BOX_H, fill=orange, stroke="#333333")
    c.add_text(sweep_x + BOX_W / 2, y2 + 22, "Small-scale ablation", size=13, color="#ffffff", anchor="middle")
    c.add_text(sweep_x + BOX_W / 2, y2 + 40, "sweep (test ratios)", size=13, color="#ffffff", anchor="middle")

    # Down to the chosen stage-1 mixture (now the active config -> green).
    y3 = y2 + BOX_H + 55
    mix_x = (WIDTH - BOX_W) / 2
    c.add_arrow(sweep_x + BOX_W / 2, y2 + BOX_H, mix_x + BOX_W / 2, y3, color="#333333")
    c.add_rect(mix_x, y3, BOX_W, BOX_H, fill=green, stroke="#333333")
    c.add_text(mix_x + BOX_W / 2, y3 + 22, "Stage 1 mixture", size=13, color="#ffffff", anchor="middle")
    c.add_text(mix_x + BOX_W / 2, y3 + 40, "(e.g. 0.7 / 0.2 / 0.1)", size=12, color="#ffffff", anchor="middle")

    # Branch: dashed (training-only, mid-run) arrow to an annealing box.
    y4 = y3
    anneal_x = mix_x + BOX_W + 140
    c.add_arrow(mix_x + BOX_W, y3 + BOX_H / 2, anneal_x, y4 + BOX_H / 2, style="dashed", color="#555555")
    c.add_rect(anneal_x, y4, BOX_W, BOX_H, fill=orange, stroke="#333333")
    c.add_text(anneal_x + BOX_W / 2, y4 + 22, "Annealing stage:", size=13, color="#ffffff", anchor="middle")
    c.add_text(anneal_x + BOX_W / 2, y4 + 40, "swap in high-quality data", size=12, color="#ffffff", anchor="middle")

    # Final arrow down to the trained model.
    y5 = y3 + BOX_H + 55
    model_x = (WIDTH - BOX_W) / 2
    c.add_arrow(mix_x + BOX_W / 2, y3 + BOX_H, model_x + BOX_W / 2, y5, color="#333333")
    c.add_arrow(anneal_x + BOX_W / 2, y4 + BOX_H, model_x + BOX_W / 2 + 40, y5, color="#333333")
    c.add_rect(model_x, y5, BOX_W, BOX_H, fill="#444444", stroke="#333333")
    c.add_text(model_x + BOX_W / 2, y5 + 22, "Pretrained model", size=13, color="#ffffff", anchor="middle")
    c.add_text(model_x + BOX_W / 2, y5 + 40, "(after full curriculum)", size=12, color="#ffffff", anchor="middle")

    c.add_text(WIDTH / 2, y5 + BOX_H + 35, "solid = evaluated path   dashed = training-only, mid-run change", size=12, color="#555555", anchor="middle")

    c.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
