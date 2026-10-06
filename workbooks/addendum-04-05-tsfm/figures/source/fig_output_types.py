"""Module 4 figure: one illustrative predictive distribution shown as four
output types.

What to notice: the same forecast can be handed over as a point, a set of
quantiles, a density, or sample paths, and each carries different
information. The fan shows marginal per-step quantiles; the sample paths
are joint (each path is one coherent scenario). Every panel is derived from
the same illustrative per-step two-component mixture in
data/worked-examples/w4_losses.py; none is a measurement of any model.
The point panel is labeled as the median of the example distribution: a
point-forecast model is trained directly with a squared-error loss, not
derived from a distribution.

Run: python3 workbooks/addendum-04-05-tsfm/figures/source/fig_output_types.py
Output: workbooks/addendum-04-05-tsfm/figures/rendered/fig-output-types.svg
"""
import math
import os
import sys
from statistics import NormalDist

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import SVGCanvas, WIDTH, TEXT, MUTED, colors, load_example, out_path  # noqa: E402

FIGURE_ID = "fig-output-types"
HEIGHT = 394
PW, PH = 258, 118        # plot area of each panel
ORIGINS = [(52, 54), (352, 54), (52, 232), (352, 232)]


def build_model():
    w4 = load_example("w4_losses.json")
    f = w4["figure"]
    return {
        "horizon": f["horizon"],
        "levels": f["quantile_levels"],
        "quantiles": f["quantiles"],
        "median": f["point_median"],
        "paths": f["sample_paths_first_12"],
        "n_samples": f["n_samples"],
        "mixture_last": f["mixture_params_last_step"],
        "shapes": f["shapes"],
    }


def mixture_pdf(params, x):
    return sum(w * NormalDist(mu, s).pdf(x) for w, mu, s in params)


def draw(m):
    col = colors()
    H = m["horizon"]
    lo = min(min(r) for r in m["quantiles"]) - 1.5
    hi = max(max(r) for r in m["quantiles"]) + 1.5
    allp = [v for p in m["paths"] for v in p]
    lo, hi = min(lo, min(allp)), max(hi, max(allp))

    def px(ox, t):
        return ox + PW * t / (H - 1)

    def py(oy, v):
        return oy + PH - PH * (v - lo) / (hi - lo)

    c = SVGCanvas(WIDTH, HEIGHT, title="One illustrative forecast as four output types")
    c.add_text(WIDTH / 2, 18, "One illustrative predictive distribution, four output types (not a measurement)", size=13, weight="bold", color=TEXT, anchor="middle")
    titles = ["(a) Point: median of the example", f"(b) Quantile fan, n_q = {len(m['levels'])}", "(c) Mixture density at the last step", f"(d) Sample paths ({len(m['paths'])} of {m['n_samples']})"]
    shapes = [
        f"shape 4 × {H} (first target shown)",
        f"shape 4 × {H} × {len(m['levels'])}",
        "mixture parameters per step (dashed, dotted: components)",
        f"shape 4 × {H} × {m['n_samples']}",
    ]
    for (ox, oy), title, shape in zip(ORIGINS, titles, shapes):
        c.add_text(ox, oy - 12, title, size=12, weight="bold", color=TEXT)
        c.add_rect(ox, oy, PW, PH, fill="#ffffff", stroke=col["inactive"], stroke_width=1, rx=2)
        c.add_text(ox, oy + PH + 15, shape, size=11, color=MUTED)

    # (a) point
    ox, oy = ORIGINS[0]
    pts = " ".join(f"{px(ox, t):.1f},{py(oy, v):.1f}" for t, v in enumerate(m["median"]))
    c.add_raw(f'<g id="panel-point"><polyline points="{pts}" fill="none" stroke="{col["forecast"]}" stroke-width="2.5"/></g>')
    # (b) fan: 10-90, 30-70 bands and median
    ox, oy = ORIGINS[1]
    li = {q: i for i, q in enumerate(m["levels"])}

    def band(qa, qb, color, op):
        up = [f"{px(ox, t):.1f},{py(oy, m['quantiles'][t][li[qb]]):.1f}" for t in range(H)]
        dn = [f"{px(ox, t):.1f},{py(oy, m['quantiles'][t][li[qa]]):.1f}" for t in reversed(range(H))]
        c.add_raw(f'<polygon points="{" ".join(up + dn)}" fill="{color}" fill-opacity="{op}" stroke="none"/>')

    c.add_raw('<g id="panel-fan">')
    band(0.1, 0.9, col["forecast"], 0.28)
    band(0.3, 0.7, col["forecast"], 0.5)
    pts = " ".join(f"{px(ox, t):.1f},{py(oy, m['quantiles'][t][li[0.5]]):.1f}" for t in range(H))
    c.add_raw(f'<polyline points="{pts}" fill="none" stroke="#7a4f00" stroke-width="2"/></g>')
    c.add_text(ox + PW - 4, oy + 14, "10–90% and 30–70% bands", size=11, color=MUTED, anchor="end")
    # (c) mixture density at the last step (x = value, y = density)
    ox, oy = ORIGINS[2]
    params = m["mixture_last"]
    xs = [lo + (hi - lo) * k / 160 for k in range(161)]
    dens = [mixture_pdf(params, x) for x in xs]
    dmax = max(dens) * 1.08
    pts = " ".join(f"{ox + PW * (x - lo) / (hi - lo):.1f},{oy + PH - PH * d / dmax:.1f}" for x, d in zip(xs, dens))
    c.add_raw(f'<g id="panel-mixture"><polyline points="{pts}" fill="none" stroke="{col["forecast"]}" stroke-width="2.5"/>')
    for (w, mu, s), dash in zip(params, ["6,4", "2,3"]):
        comp = " ".join(f"{ox + PW * (x - lo) / (hi - lo):.1f},{oy + PH - PH * w * NormalDist(mu, s).pdf(x) / dmax:.1f}" for x in xs)
        c.add_raw(f'<polyline points="{comp}" fill="none" stroke="#555555" stroke-width="1.2" stroke-dasharray="{dash}"/>')
    c.add_raw("</g>")
    c.add_text(ox + PW / 2, oy + PH + 28, "value at the last horizon step →", size=11, color=MUTED, anchor="middle")
    # (d) sample paths
    ox, oy = ORIGINS[3]
    c.add_raw('<g id="panel-samples">')
    for p in m["paths"]:
        pts = " ".join(f"{px(ox, t):.1f},{py(oy, v):.1f}" for t, v in enumerate(p))
        c.add_raw(f'<polyline points="{pts}" fill="none" stroke="{col["forecast"]}" stroke-width="1" stroke-opacity="0.7"/>')
    c.add_raw("</g>")
    for (ox, oy) in (ORIGINS[0], ORIGINS[1], ORIGINS[3]):
        c.add_text(ox + PW / 2, oy + PH + 28, "horizon step →", size=11, color=MUTED, anchor="middle")
    return c


def main():
    m = build_model()
    draw(m).save(out_path(FIGURE_ID))
    print(f"wrote {out_path(FIGURE_ID)}")


if __name__ == "__main__":
    main()
