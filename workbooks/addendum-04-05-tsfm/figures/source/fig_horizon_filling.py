"""Module 3 figure: how a 256-step horizon gets filled, on one shared timeline.

What to notice: context and horizon are different stretches of the same
time axis, and the number of forward passes depends on the strategy and on
the output-patch length, not on the horizon alone. The pass counts
(2, 8, 256, 1, 1) come from data/worked-examples/w3_rollout.py
(ceil(F / P_out) for the iterative rows). The settings follow the TimesFM
paper's own example (context 256, horizon 256, input patch 32, output patch
128); the placeholder row is an illustrative counting device. Nothing here
describes the internals of a release that has no paper.

Run: python3 workbooks/addendum-04-05-tsfm/figures/source/fig_horizon_filling.py
Output: workbooks/addendum-04-05-tsfm/figures/rendered/fig-horizon-filling.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import SVGCanvas, WIDTH, TEXT, MUTED, colors, load_example, out_path  # noqa: E402

FIGURE_ID = "fig-horizon-filling"
HEIGHT = 330
X0, X1 = 168, 540   # timeline pixel span for 0 .. t_ctx + horizon
ROW_Y0, ROW_H = 74, 36


def build_model():
    w3 = load_example("w3_rollout.json")
    rows = []
    for r in w3["rows"]:
        rows.append({"label": r["strategy"], "klass": r["klass"], "passes": r["forward_passes"], "p_out": r["p_out"],
                     "placeholder_patches": r.get("placeholder_patches")})
    return {"t_ctx": w3["t_ctx"], "horizon": w3["horizon"], "p_in": w3["p_in"], "p_out": w3["p_out"], "rows": rows}


def draw(m):
    col = colors()
    total = m["t_ctx"] + m["horizon"]

    def sx(step):
        return X0 + (X1 - X0) * step / total

    c = SVGCanvas(WIDTH, HEIGHT, title="Horizon filling strategies on one shared timeline")
    c.add_text(WIDTH / 2, 18, "Filling a 256-step horizon: passes depend on the strategy (illustrative setting)", size=13, weight="bold", color=TEXT, anchor="middle")
    # axis band
    c.add_rect(sx(0), 30, sx(m["t_ctx"]) - sx(0), 22, fill="#eaf2fb", stroke=col["observed"], stroke_width=1.2, rx=3)
    c.add_text((sx(0) + sx(m["t_ctx"])) / 2, 45, f"context  T_ctx = {m['t_ctx']}", size=11, color=TEXT, anchor="middle", weight="bold")
    c.add_rect(sx(m["t_ctx"]), 30, sx(total) - sx(m["t_ctx"]), 22, fill="#fdf1d6", stroke=col["forecast"], stroke_width=1.2, rx=3)
    c.add_text((sx(m["t_ctx"]) + sx(total)) / 2, 45, f"horizon  F = {m['horizon']}", size=11, color=TEXT, anchor="middle", weight="bold")
    c.add_text(sx(0), 64, "time step 0", size=11, color=MUTED, anchor="start")
    c.add_text(sx(total), 64, f"{total}", size=11, color=MUTED, anchor="end")

    for i, r in enumerate(m["rows"]):
        y = ROW_Y0 + i * ROW_H
        c.add_text(10, y + 13, ["iterative, P_out = 128", "iterative, P_out = 32", "iterative, 1 value per pass", "one pass, placeholders", "direct head"][i], size=11, weight="bold", color=TEXT)
        sub = ["output patch longer than input", "output patch = input patch", "one token or value at a time", "no feedback loop", "one head over the whole horizon"][i]
        c.add_text(10, y + 27, sub, size=11, color=MUTED)
        # context shading
        c.add_rect(sx(0), y, sx(m["t_ctx"]) - sx(0), 22, fill="#eaf2fb", stroke=col["observed"], stroke_width=0.8, rx=2)
        if r["klass"] == "iterative":
            n = r["passes"]
            blocks = min(n, 8)
            if n <= 8:
                step = m["horizon"] / n
                for k in range(n):
                    a, b = m["t_ctx"] + k * step, m["t_ctx"] + (k + 1) * step
                    c.add_raw(f'<g id="pass-{i}-{k}">')
                    c.add_rect(sx(a), y, sx(b) - sx(a), 22, fill=col["forecast"], stroke="#333333", stroke_width=0.8, rx=2)
                    c.add_text((sx(a) + sx(b)) / 2, y + 15, str(k + 1), size=11, color=TEXT, anchor="middle")
                    c.add_raw("</g>")
            else:  # too many to label: a dense run
                c.add_rect(sx(m["t_ctx"]), y, sx(total) - sx(m["t_ctx"]), 22, fill=col["forecast"], stroke="#333333", stroke_width=0.8, rx=2)
                c.add_raw(f'<g id="pass-{i}-dense"></g>')
                c.add_text((sx(m["t_ctx"]) + sx(total)) / 2, y + 15, "1 … 256", size=11, color=TEXT, anchor="middle")
        elif r["klass"] == "placeholder":
            n = r["placeholder_patches"]
            step = m["horizon"] / n
            for k in range(n):
                a, b = m["t_ctx"] + k * step, m["t_ctx"] + (k + 1) * step
                c.add_raw(f'<g id="placeholder-{k}">')
                c.add_rect(sx(a), y, sx(b) - sx(a), 22, fill="#ffffff", stroke=col["inactive"], stroke_width=1, rx=2, dash="dashed")
                c.add_text((sx(a) + sx(b)) / 2, y + 15, "?", size=11, color=MUTED, anchor="middle")
                c.add_raw("</g>")
        else:
            c.add_raw(f'<g id="direct-{i}">')
            c.add_rect(sx(m["t_ctx"]), y, sx(total) - sx(m["t_ctx"]), 22, fill=col["forecast"], stroke="#333333", stroke_width=0.8, rx=2)
            c.add_text((sx(m["t_ctx"]) + sx(total)) / 2, y + 15, "whole horizon at once", size=11, color=TEXT, anchor="middle")
            c.add_raw("</g>")
        label = f"{r['passes']} pass" + ("es" if r["passes"] != 1 else "")
        c.add_text(X1 + 8, y + 15, label, size=12, weight="bold", color=TEXT)

    yb = ROW_Y0 + len(m["rows"]) * ROW_H + 10
    c.add_rect(10, yb, 292, 54, fill="#ffffff", stroke=col["inactive"], stroke_width=1.4, rx=4, dash="dashed")
    c.add_text(18, yb + 17, "Training only", size=12, weight="bold", color=TEXT)
    c.add_text(18, yb + 32, "patch masking, contiguous patch masking,", size=11, color=MUTED)
    c.add_text(18, yb + 46, "extra future-patch targets", size=11, color=MUTED)
    c.add_rect(318, yb, 292, 54, fill="#ffffff", stroke="#333333", stroke_width=1.4, rx=4)
    c.add_text(326, yb + 17, "Inference only", size=12, weight="bold", color=TEXT)
    c.add_text(326, yb + 32, "rollout (own output fed back) or one pass", size=11, color=MUTED)
    c.add_text(326, yb + 46, "over placeholders; feedback errors need a rollout", size=11, color=MUTED)
    return c


def main():
    m = build_model()
    draw(m).save(out_path(FIGURE_ID))
    print(f"wrote {out_path(FIGURE_ID)}")


if __name__ == "__main__":
    main()
