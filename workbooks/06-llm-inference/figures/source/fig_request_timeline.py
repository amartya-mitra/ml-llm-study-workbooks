"""Chapter 1 figure: the synthetic event log drawn as one lane per request,
with the timestamps the serving metrics are computed from.

What to notice: server-side queueing (grey) and the client-to-server
boundary both sit inside a client-measured time to first token; a
streamed chunk can carry more than one token, so chunk gaps (ITL) are not
the same as the request-average time per output token; a request with a
single output token has a time to first token but no token gaps at all.
The log is synthetic and schematic: it is not produced by the chapter's
cost model and is not a measurement.

All times come from data/worked-examples/inference_workload_and_metrics.json.

Run: python3 workbooks/06-llm-inference/figures/source/fig_request_timeline.py
Output: workbooks/06-llm-inference/figures/rendered/fig-request-timeline.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import SVGCanvas, WIDTH, TEXT, MUTED, GRID, LinAxis, circle, colors, line, load_example, out_path  # noqa: E402

FIGURE_ID = "fig-request-timeline"
LANE_H = 52
TOP = 64
X0, X1 = 58, 600
T_MAX = 1.1


def build_model():
    d = load_example("inference_workload_and_metrics.json")
    metrics = {r["id"]: r for r in d["requests"]}
    lanes = []
    for e in d["events"]:
        lanes.append({
            "id": e["id"], "send": e["client_send"], "arrival": e["server_arrival"],
            "scheduled": e["first_scheduled"], "server_tokens": e["server_token_times"],
            "chunks": e["client_chunks"], "ttft_client": metrics[e["id"]]["ttft_client_s"],
            "output_tokens": metrics[e["id"]]["output_tokens"],
        })
    return {"lanes": lanes}


def draw(m):
    col = colors()
    height = TOP + LANE_H * len(m["lanes"]) + 74
    c = SVGCanvas(WIDTH, height, title="Synthetic request and token events")
    xa = LinAxis(0, T_MAX, X0, X1)
    c.add_text(WIDTH / 2, 18, "Four requests on one clock (synthetic, schematic event log)", size=13, weight="bold", color=TEXT, anchor="middle")
    base = TOP + LANE_H * len(m["lanes"])
    for v in (0, 0.2, 0.4, 0.6, 0.8, 1.0):
        line(c, xa(v), TOP - 14, xa(v), base, GRID, 0.8)
        c.add_text(xa(v), base + 14, f"{v:.1f}", size=11, color=MUTED, anchor="middle")
    c.add_text((X0 + X1) / 2, base + 30, "time (s)", size=11, color=TEXT, anchor="middle")
    for i, ln in enumerate(m["lanes"]):
        y = TOP + i * LANE_H + 18
        c.add_text(10, y + 4, ln["id"], size=12, weight="bold", color=TEXT)
        c.add_raw(f'<g id="lane-{ln["id"]}">')
        # client view: send -> first chunk (TTFT bracket)
        line(c, xa(ln["send"]), y - 14, xa(ln["chunks"][0][0]), y - 14, col["green"], 2, ident=f"ttft-{ln['id']}")
        line(c, xa(ln["send"]), y - 18, xa(ln["send"]), y - 10, col["green"], 2)
        c.add_text(xa(ln["send"]) + 3, y - 18, f"TTFT {ln['ttft_client'] * 1000:.0f} ms", size=11, color=col["green"])
        # server: queue then running
        c.add_raw(f'<rect id="queue-{ln["id"]}" x="{xa(ln["arrival"]):.2f}" y="{y - 6}" '
                  f'width="{max(xa(ln["scheduled"]) - xa(ln["arrival"]), 0.5):.2f}" height="12" fill="{col["inactive"]}" opacity="0.6"/>')
        end = ln["server_tokens"][-1]
        c.add_raw(f'<rect id="run-{ln["id"]}" x="{xa(ln["scheduled"]):.2f}" y="{y - 6}" '
                  f'width="{xa(end) - xa(ln["scheduled"]):.2f}" height="12" fill="{col["compute"]}" opacity="0.35"/>')
        for t in ln["server_tokens"]:
            line(c, xa(t), y - 6, xa(t), y + 6, col["compute"], 2)
        # client chunk receipts
        for t, n in ln["chunks"]:
            circle(c, xa(t), y + 14, 4, col["stored"], "#ffffff", data={"tokens": n})
            if n > 1:
                c.add_text(xa(t), y + 31, f"chunk with {n} tokens", size=11, color=col["stored"], anchor="middle")
        if ln["output_tokens"] == 1:
            c.add_text(xa(ln["chunks"][0][0]) + 8, y + 18, "1 output token: no gaps", size=11, color=col["stored"])
        c.add_raw("</g>")
    items = ((col["inactive"], "server queue"), (col["compute"], "running on the server; ticks = token emitted"),
             (col["stored"], "streamed chunk received by the client"), (col["green"], "client-side time to first token"))
    for k, (colr, lab) in enumerate(items):
        x = X0 + (k % 2) * 270
        ly = base + 48 + (k // 2) * 16
        c.add_raw(f'<rect x="{x}" y="{ly - 9}" width="12" height="10" fill="{colr}" opacity="0.8"/>')
        c.add_text(x + 16, ly, lab, size=11, color=TEXT)
    return c


def main():
    draw(build_model()).save(out_path(FIGURE_ID))
    print(f"wrote {out_path(FIGURE_ID)}")


if __name__ == "__main__":
    main()
