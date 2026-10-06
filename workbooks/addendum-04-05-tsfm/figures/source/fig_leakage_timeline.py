"""Module 5 figure: where leakage can enter along one series' timeline.

What to notice: in the "no overlap" design the training region and the
normalization-statistics window both end before the evaluation window
starts; in the leaky design, either one reaches into it. This is an
ORIGINAL explanatory illustration: the windows are illustrative numbers
(data/worked-examples/w5_mixture_cap.py), not a description of any named
benchmark's protocol or any model's pipeline.

Run: python3 workbooks/addendum-04-05-tsfm/figures/source/fig_leakage_timeline.py
Output: workbooks/addendum-04-05-tsfm/figures/rendered/fig-leakage-timeline.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import SVGCanvas, WIDTH, TEXT, MUTED, colors, load_example, out_path  # noqa: E402

FIGURE_ID = "fig-leakage-timeline"
HEIGHT = 322
AX0, AX1 = 140, 590
BAR_H = 18


def build_model():
    w5 = load_example("w5_mixture_cap.json")
    return {"panels": [
        {"id": "correct", "title": "No overlap", **w5["timeline"]["correct"]},
        {"id": "leaky", "title": "Leaky", **w5["timeline"]["leaky"]},
    ]}


def draw(m):
    col = colors()

    def sx(v):
        return AX0 + (AX1 - AX0) * v

    c = SVGCanvas(WIDTH, HEIGHT, title="Leakage timeline: training region, normalization window, evaluation window")
    c.add_text(WIDTH / 2, 18, "Where leakage can enter along one series (illustrative windows)", size=13, weight="bold", color=TEXT, anchor="middle")
    for k, p in enumerate(m["panels"]):
        ty = 34 + k * 138
        y0 = ty + 12
        c.add_text(10, ty, p["title"], size=13, weight="bold", color=col["flag"] if p["id"] == "leaky" else TEXT)
        rows = [("training region", p["train"], col["observed"]), ("statistics window", p["stats"], col["trainable"]), ("evaluation window", p["eval"], col["forecast"])]
        for i, (label, (a, b), color) in enumerate(rows):
            y = y0 + 4 + i * 24
            c.add_text(AX0 - 6, y + 13, label, size=11, color=TEXT, anchor="end")
            c.add_raw(f'<g id="{p["id"]}-{label.split()[0]}">')
            c.add_rect(sx(a), y, sx(b) - sx(a), BAR_H, fill=color, stroke="#333333", stroke_width=1, rx=2)
            c.add_raw("</g>")
        # eval start marker
        ea = p["eval"][0]
        c.add_arrow(sx(ea), y0 + 80, sx(ea), y0 + 76, color="#333333", stroke_width=1)
        # overlap highlights
        for nm, (a, b), y in [("train", p["train"], y0 + 4), ("stats", p["stats"], y0 + 28)]:
            ov0, ov1 = max(a, ea), min(b, p["eval"][1])
            if ov1 > ov0:
                c.add_raw(f'<g id="{p["id"]}-overlap-{nm}">')
                c.add_rect(sx(ov0), y - 2, sx(ov1) - sx(ov0), BAR_H + 4, fill="none", stroke=col["flag"], stroke_width=3, rx=2)
                c.add_raw("</g>")
        msg = "both end before the evaluation window starts" if p["id"] == "correct" else \
            f"training reaches {p['train_eval_overlap']:.2f} into evaluation; statistics reach {p['stats_eval_overlap']:.2f} in"
        c.add_text(AX0, y0 + 98, msg, size=11, color=col["flag"] if p["id"] == "leaky" else MUTED, weight="bold" if p["id"] == "leaky" else "normal")
        c.add_arrow(AX0, y0 + 108, AX1, y0 + 108, color="#555555", stroke_width=1)
    c.add_text(AX0, 314, "time along the series (normalized 0 to 1)", size=11, color=MUTED)
    return c


def main():
    m = build_model()
    draw(m).save(out_path(FIGURE_ID))
    print(f"wrote {out_path(FIGURE_ID)}")


if __name__ == "__main__":
    main()
