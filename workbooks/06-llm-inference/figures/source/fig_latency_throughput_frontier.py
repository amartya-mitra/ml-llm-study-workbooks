"""Chapter 1 figure: idealized decode step time versus throughput as the
batch grows, for two retained context lengths.

What to notice: a larger batch raises tokens per second but also raises
each step's time, which is every sequence's gap between tokens; at long
context the extra KV reads make throughput flatten early. Hollow points
need more memory than the illustrative device holds, so they are
analytical extrapolations, not configurations that could run there.
Values are the per-operation step-time estimates from
data/worked-examples/inference_workload_and_metrics.json; they are
idealized bounds, not measurements.

Run: python3 workbooks/06-llm-inference/figures/source/fig_latency_throughput_frontier.py
Output: workbooks/06-llm-inference/figures/rendered/fig-latency-throughput-frontier.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (SVGCanvas, WIDTH, TEXT, MUTED, GRID, LinAxis, LogAxis, circle, colors, line,  # noqa: E402
                     load_example, out_path)

FIGURE_ID = "fig-latency-throughput-frontier"
HEIGHT = 340
X0, X1, Y0, Y1 = 70, 590, 290, 46
T_LO, T_HI = 100, 50000
MS_LO, MS_HI = 0, 110


def build_model():
    d = load_example("inference_workload_and_metrics.json")
    series = []
    for S, rows in d["decode"].items():
        series.append({"context": int(S), "points": [
            {"batch": r["batch"], "tokens_per_s": r["tokens_per_s_at_per_op_estimate"],
             "step_ms": r["step_time_per_op_estimate_s"] * 1e3, "fits": r["fits_illustrative_capacity"]}
            for r in rows]})
    return {"series": series}


def draw(m):
    col = colors()
    c = SVGCanvas(WIDTH, HEIGHT, title="Decode step time versus throughput")
    xa, ya = LogAxis(T_LO, T_HI, X0, X1), LinAxis(MS_LO, MS_HI, Y0, Y1)
    c.add_text(WIDTH / 2, 18, "Batch size trades step time for throughput (idealized decode)",
               size=13, weight="bold", color=TEXT, anchor="middle")
    for v in (100, 1000, 10000):
        line(c, xa(v), Y0, xa(v), Y1, GRID, 0.8)
        c.add_text(xa(v), Y0 + 16, f"{v:,}", size=11, color=MUTED, anchor="middle")
    for v in (0, 25, 50, 75, 100):
        line(c, X0, ya(v), X1, ya(v), GRID, 0.8)
        c.add_text(X0 - 6, ya(v) + 4, f"{v}", size=11, color=MUTED, anchor="end")
    line(c, X0, Y0, X1, Y0, MUTED, 1.2)
    line(c, X0, Y0, X0, Y1, MUTED, 1.2)
    c.add_text((X0 + X1) / 2, Y0 + 34, "output tokens per second across the batch (log scale)", size=11, color=TEXT, anchor="middle")
    c.add_raw(f'<text x="18" y="{(Y0 + Y1) / 2}" font-family="sans-serif" font-size="11" fill="{TEXT}" '
              f'text-anchor="middle" transform="rotate(-90 18 {(Y0 + Y1) / 2})">step time = per-sequence token gap (ms)</text>')
    colours = {512: col["stored"], 4096: col["flag"]}
    for s in m["series"]:
        colr = colours[s["context"]]
        pts = s["points"]
        for a, b in zip(pts, pts[1:]):
            line(c, xa(a["tokens_per_s"]), ya(a["step_ms"]), xa(b["tokens_per_s"]), ya(b["step_ms"]), colr, 1.6,
                 dash=None if b["fits"] else "4 3")
        for p in pts:
            ident = f"pt-S{s['context']}-B{p['batch']}"
            circle(c, xa(p["tokens_per_s"]), ya(p["step_ms"]), 5, colr if p["fits"] else "#ffffff", colr,
                   ident=ident, data={"fits": str(p["fits"]).lower()})
            if s["context"] == 512 and p["batch"] == 1:
                continue  # coincides with the 4,096-token B=1 point, labelled there
            dx, anchor = (-8, "end") if s["context"] == 4096 and p["batch"] != 1 else (7, "start")
            text = "B=1 (both)" if p["batch"] == 1 else f"B={p['batch']}"
            dy = 17 if (s["context"] == 512 and p["batch"] == 256) else -9
            c.add_text(xa(p["tokens_per_s"]) + dx, ya(p["step_ms"]) + dy, text, size=11, color=colr, anchor=anchor)
    lx, ly = X0 + 14, Y1 + 8
    for i, (S, lab) in enumerate(((512, "context 512 tokens"), (4096, "context 4,096 tokens"))):
        circle(c, lx, ly + i * 16 - 4, 5, colours[S], colours[S])
        c.add_text(lx + 10, ly + i * 16, lab, size=11, color=TEXT)
    circle(c, lx, ly + 32 - 4, 5, "#ffffff", MUTED)
    c.add_text(lx + 10, ly + 32, "exceeds illustrative memory capacity", size=11, color=TEXT)
    return c


def main():
    draw(build_model()).save(out_path(FIGURE_ID))
    print(f"wrote {out_path(FIGURE_ID)}")


if __name__ == "__main__":
    main()
