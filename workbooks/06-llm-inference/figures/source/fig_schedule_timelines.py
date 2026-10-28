"""Chapter 3 figure: the synthetic four-request trace under four schedules,
one panel per policy, one row per request.

What to notice: static batching makes C and D wait for the whole first
batch; continuous batching admits them at the next step but C's whole
prefill shares a step with A's and B's decodes; chunked prefill spreads
C's prefill over several bounded steps, delaying C's first token; under
disaggregation prefill and decode run on separate devices, joined by a
KV transfer. Bars are steps in which a request's tokens are processed
(orange: prefill tokens; blue: one decode token); dots mark output tokens
being selected. Synthetic, illustrative cost model; not a measurement.

All values come from data/worked-examples/serving_schedules.json.

Run: python3 workbooks/06-llm-inference/figures/source/fig_schedule_timelines.py
Output: workbooks/06-llm-inference/figures/rendered/fig-schedule-timelines.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import SVGCanvas, WIDTH, TEXT, MUTED, GRID, LinAxis, circle, colors, line, load_example, out_path  # noqa: E402

FIGURE_ID = "fig-schedule-timelines"
X0, X1 = 92, 604
T_MAX = 110.0
ROW_H = 15
PANEL_H = 4 * ROW_H + 30
TOP = 40
POLICIES = [("static", "Static (request-level) batching"),
            ("continuous", "Continuous batching, no chunking"),
            ("chunked", "Continuous batching, chunked prefill (256-token budget)"),
            ("disaggregated", "Disaggregated: prefill device + decode device")]


def build_model():
    d = load_example("serving_schedules.json")
    ids = [r["id"] for r in d["trace"]]
    arrivals = {r["id"]: r["arrival"] for r in d["trace"]}
    panels = []
    for key, title in POLICIES:
        p = d["policies"][key]
        segs = []
        for group in ("steps", "prefill_steps", "decode_steps"):
            for s in p.get(group, []):
                for w in s["work"]:
                    segs.append({"id": w["id"], "kind": w["kind"], "start": s["start"], "end": s["end"],
                                 "device": "decode" if group == "decode_steps" else ("prefill" if group == "prefill_steps" else "single")})
        selects = {m["id"]: m["selected_at"] for m in p["requests"]}
        transfers = {k: (min(t for t in selects[k][:1]), v["ready_at"]) for k, v in p.get("transfer", {}).items()}
        panels.append({"key": key, "title": title, "segments": segs, "selected": selects, "transfers": transfers,
                       "aggregate": p["aggregate"]})
    return {"ids": ids, "arrivals": arrivals, "panels": panels}


def draw(m):
    col = colors()
    height = TOP + PANEL_H * len(m["panels"]) + 58
    c = SVGCanvas(WIDTH, height, title="Four schedules of one synthetic trace")
    c.add_text(WIDTH / 2, 18, "One synthetic trace, four schedules (illustrative cost model)",
               size=13, weight="bold", color=TEXT, anchor="middle")
    xa = LinAxis(0, T_MAX, X0, X1)
    for pi, p in enumerate(m["panels"]):
        y0 = TOP + pi * PANEL_H
        c.add_text(X0, y0 + 10, p["title"], size=11, weight="bold", color=TEXT)
        c.add_raw(f'<g id="panel-{p["key"]}">')
        for ri, rid in enumerate(m["ids"]):
            y = y0 + 18 + ri * ROW_H
            c.add_text(X0 - 8, y + 10, rid, size=11, weight="bold", color=TEXT, anchor="end")
            line(c, X0, y + ROW_H - 2, X1, y + ROW_H - 2, GRID, 0.6)
            ax = xa(m["arrivals"][rid])
            c.add_raw(f'<line id="arr-{p["key"]}-{rid}" x1="{ax:.1f}" y1="{y}" x2="{ax:.1f}" y2="{y + ROW_H - 2}" '
                      f'stroke="{TEXT}" stroke-width="1.6" data-arrival="{m["arrivals"][rid]}"/>')
            for s in [s for s in p["segments"] if s["id"] == rid]:
                fill = col["compute"] if s["kind"] == "prefill" else col["stored"]
                c.add_raw(f'<rect x="{xa(s["start"]) + 0.4:.2f}" y="{y + 2}" width="{max(xa(s["end"]) - xa(s["start"]) - 0.8, 0.5):.2f}" '
                          f'height="{ROW_H - 6}" fill="{fill}" fill-opacity="0.75" data-kind="{s["kind"]}" '
                          f'data-start="{s["start"]}" data-end="{s["end"]}" data-req="{rid}"/>')
            if rid in p["transfers"]:
                a, b = p["transfers"][rid]
                c.add_raw(f'<line id="xfer-{rid}" x1="{xa(a):.2f}" y1="{y + ROW_H / 2 - 1}" x2="{xa(b):.2f}" y2="{y + ROW_H / 2 - 1}" '
                          f'stroke="{col["flag"]}" stroke-width="2" stroke-dasharray="3 2"/>')
            for t in p["selected"][rid]:
                circle(c, xa(t), y + ROW_H / 2 - 1, 2.6, TEXT, TEXT, data={"t": t})
        a = p["aggregate"]
        c.add_text(X1, y0 + 10, f"{a['output_tokens_per_s']:.0f} tok/s · worst gap {a['worst_gap_ms']:.1f} ms",
                   size=11, color=MUTED, anchor="end")
        c.add_raw("</g>")
    base = TOP + PANEL_H * len(m["panels"])
    for v in range(0, 111, 20):
        line(c, xa(v), TOP + 14, xa(v), base - 10, GRID, 0.6)
        c.add_text(xa(v), base + 2, f"{v}", size=11, color=MUTED, anchor="middle")
    c.add_text((X0 + X1) / 2, base + 16, "time (ms)", size=11, color=TEXT, anchor="middle")
    ly = base + 34
    c.add_raw(f'<rect x="{X0}" y="{ly - 9}" width="12" height="9" fill="{col["compute"]}" fill-opacity="0.75"/>')
    c.add_text(X0 + 16, ly, "prefill tokens processed", size=11, color=TEXT)
    c.add_raw(f'<rect x="{X0 + 160}" y="{ly - 9}" width="12" height="9" fill="{col["stored"]}" fill-opacity="0.75"/>')
    c.add_text(X0 + 176, ly, "decode token processed", size=11, color=TEXT)
    circle(c, X0 + 4, ly + 12, 2.6, TEXT, TEXT)
    c.add_text(X0 + 16, ly + 16, "token selected", size=11, color=TEXT)
    c.add_raw(f'<line x1="{X0 + 160}" y1="{ly + 7}" x2="{X0 + 160}" y2="{ly + 18}" stroke="{TEXT}" stroke-width="1.6"/>')
    c.add_text(X0 + 176, ly + 16, "arrival", size=11, color=TEXT)
    c.add_raw(f'<line x1="{X0 + 300}" y1="{ly + 12}" x2="{X0 + 316}" y2="{ly + 12}" stroke="{col["flag"]}" stroke-width="2" stroke-dasharray="3 2"/>')
    c.add_text(X0 + 322, ly + 16, "KV transfer (disaggregated)", size=11, color=TEXT)
    return c


def main():
    draw(build_model()).save(out_path(FIGURE_ID))
    print(f"wrote {out_path(FIGURE_ID)}")


if __name__ == "__main__":
    main()
