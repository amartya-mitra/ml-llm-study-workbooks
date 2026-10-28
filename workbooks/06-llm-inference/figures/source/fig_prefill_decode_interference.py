"""Chapter 3 figure: step durations of the synthetic trace without and with
chunked prefill, split into the cost model's three terms.

What to notice: every running sequence waits for the whole step, so a step
that also carries C's 1,024-token prefill lengthens A's and B's gaps to
about 21 ms; with a 256-token budget no step exceeds about 9 ms, but the
prefill now spans several steps. Bars are stacked T0 (fixed per step),
ALPHA x prefill tokens and BETA x decode tokens from the illustrative cost
model; not a measurement.

All values come from data/worked-examples/serving_schedules.json.

Run: python3 workbooks/06-llm-inference/figures/source/fig_prefill_decode_interference.py
Output: workbooks/06-llm-inference/figures/rendered/fig-prefill-decode-interference.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import SVGCanvas, WIDTH, TEXT, MUTED, GRID, LinAxis, colors, line, load_example, out_path  # noqa: E402

FIGURE_ID = "fig-prefill-decode-interference"
X0, X1 = 70, 604
T_MAX = 100.0
MS_MAX = 24.0
PANEL_H = 120
TOP = 44
PANELS = [("continuous", "No chunking: C's whole prefill joins a decode step"),
          ("chunked", "Chunked prefill, 256-token budget")]


def build_model():
    d = load_example("serving_schedules.json")
    cm = d["cost_model"]
    panels = []
    for key, title in PANELS:
        steps = []
        for s in d["policies"][key]["steps"]:
            steps.append({"start": s["start"], "end": s["end"], "t0": cm["t0_ms"],
                          "prefill_ms": cm["alpha_ms_per_prefill_token"] * s["prefill_tokens"],
                          "decode_ms": cm["beta_ms_per_decode_token"] * s["decode_tokens"],
                          "duration": s["end"] - s["start"], "has_decode": s["decode_tokens"] > 0,
                          "has_prefill": s["prefill_tokens"] > 0})
        panels.append({"key": key, "title": title, "steps": steps,
                       "max_mixed": max((s["duration"] for s in steps if s["has_decode"] and s["has_prefill"]), default=0)})
    return {"panels": panels}


def draw(m):
    col = colors()
    height = TOP + PANEL_H * len(m["panels"]) + 38
    c = SVGCanvas(WIDTH, height, title="Prefill-decode interference in step durations")
    c.add_text(WIDTH / 2, 18, "Illustrative step durations: a long prefill stretches co-scheduled decodes",
               size=13, weight="bold", color=TEXT, anchor="middle")
    xa = LinAxis(0, T_MAX, X0, X1)
    for pi, p in enumerate(m["panels"]):
        y0 = TOP + pi * PANEL_H
        ya = LinAxis(0, MS_MAX, y0 + PANEL_H - 26, y0 + 18)
        c.add_text(X0, y0 + 10, p["title"], size=11, weight="bold", color=TEXT)
        for v in (0, 10, 20):
            line(c, X0, ya(v), X1, ya(v), GRID, 0.6)
            c.add_text(X0 - 6, ya(v) + 4, f"{v}", size=11, color=MUTED, anchor="end")
        c.add_raw(f'<g id="panel-{p["key"]}">')
        for i, s in enumerate(p["steps"]):
            x, w = xa(s["start"]) + 0.5, max(xa(s["end"]) - xa(s["start"]) - 1, 0.5)
            yb = ya(0)
            for part, colr, op in (("t0", MUTED, 0.35), ("prefill_ms", col["compute"], 0.8), ("decode_ms", col["stored"], 0.8)):
                h = ya(0) - ya(s[part])
                if h <= 0:
                    continue
                c.add_raw(f'<rect x="{x:.2f}" y="{yb - h:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{colr}" fill-opacity="{op}" '
                          f'data-step="{i}" data-part="{part}" data-ms="{s[part]:.6f}"/>')
                yb -= h
        c.add_raw("</g>")
        c.add_text(X1, y0 + 10, f"longest decode-carrying step {max(s['duration'] for s in p['steps'] if s['has_decode']):.1f} ms",
                   size=11, color=MUTED, anchor="end")
        c.add_raw(f'<text x="18" y="{y0 + PANEL_H / 2}" font-family="sans-serif" font-size="11" fill="{TEXT}" '
                  f'text-anchor="middle" transform="rotate(-90 18 {y0 + PANEL_H / 2})">step (ms)</text>')
    base = TOP + PANEL_H * len(m["panels"])
    for v in range(0, 101, 20):
        c.add_text(xa(v), base - 10, f"{v}", size=11, color=MUTED, anchor="middle")
    c.add_text((X0 + X1) / 2, base + 6, "time (ms)", size=11, color=TEXT, anchor="middle")
    lx = X0
    for colr, op, lab in ((MUTED, 0.35, "fixed per-step cost T0"), (col["compute"], 0.8, "prefill tokens"),
                          (col["stored"], 0.8, "decode tokens")):
        c.add_raw(f'<rect x="{lx}" y="{base + 18}" width="12" height="9" fill="{colr}" fill-opacity="{op}"/>')
        c.add_text(lx + 16, base + 27, lab, size=11, color=TEXT)
        lx += 170
    return c


def main():
    draw(build_model()).save(out_path(FIGURE_ID))
    print(f"wrote {out_path(FIGURE_ID)}")


if __name__ == "__main__":
    main()
