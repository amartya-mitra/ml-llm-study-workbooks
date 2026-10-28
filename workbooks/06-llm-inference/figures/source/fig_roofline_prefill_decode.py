"""Chapter 1 figure: an idealized roofline for the illustrative accelerator,
with the chapter's prefill and decode operations placed on it.

What to notice: the roof is min(peak FLOP/s, bandwidth x intensity), so an
operation left of the ridge point is limited by memory traffic and one to
the right by compute. Decode linear layers move right as more tokens share
each weight read (intensity = tokens per step for 2-byte weights); decode
attention stays at a fixed, low intensity set by the KV-head grouping,
whatever the batch size; prefill sits far to the right. Every point is an
idealized bound computed from logical bytes, not a measurement.

All numbers come from data/worked-examples/inference_workload_and_metrics.json.

Run: python3 workbooks/06-llm-inference/figures/source/fig_roofline_prefill_decode.py
Output: workbooks/06-llm-inference/figures/rendered/fig-roofline-prefill-decode.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (SVGCanvas, WIDTH, TEXT, MUTED, GRID, LogAxis, circle, colors, line,  # noqa: E402
                     load_example, out_path)

FIGURE_ID = "fig-roofline-prefill-decode"
HEIGHT = 380
X0, X1, Y0, Y1 = 78, 590, 330, 40  # plot box (y grows downward)
I_LO, I_HI = 0.5, 8192.0
P_LO, P_HI = 1e11, 3e15


def roof(peak, bw, intensity):
    return min(peak, bw * intensity)


def build_model():
    d = load_example("inference_workload_and_metrics.json")
    peak = d["hardware"]["peak_flops_per_s"]
    bw = d["hardware"]["mem_bandwidth_bytes_per_s"]
    pts = []
    for r in d["decode"]["4096"]:
        pts.append({"id": f"decode-linear-B{r['batch']}", "group": "decode-linear",
                    "intensity": r["linear_intensity"], "label": f"B={r['batch']}"})
    pts.append({"id": "decode-attention-gqa", "group": "decode-attention",
                "intensity": d["decode_attention_intensity_gqa"], "label": "decode attention, 8 KV heads"})
    pts.append({"id": "decode-attention-mha", "group": "decode-attention",
                "intensity": d["decode_attention_intensity_mha"], "label": "decode attention, 32 KV heads"})
    pts.append({"id": "prefill-linear", "group": "prefill",
                "intensity": d["prefill"]["linear_intensity"], "label": "prefill linear (2048 tokens)"})
    pts.append({"id": "prefill-attention", "group": "prefill",
                "intensity": d["prefill"]["attention_intensity"], "label": "prefill attention"})
    for p in pts:
        p["attainable"] = roof(peak, bw, p["intensity"])
        p["bound"] = "compute" if bw * p["intensity"] >= peak else "bandwidth"
    return {"peak": peak, "bandwidth": bw, "ridge": peak / bw, "points": pts}


def draw(m):
    col = colors()
    c = SVGCanvas(WIDTH, HEIGHT, title="Idealized roofline with prefill and decode operations")
    xa, ya = LogAxis(I_LO, I_HI, X0, X1), LogAxis(P_LO, P_HI, Y0, Y1)
    c.add_text(WIDTH / 2, 18, "Idealized roofline (illustrative accelerator; bounds, not measurements)",
               size=13, weight="bold", color=TEXT, anchor="middle")
    # grid and axes
    for v in (1, 10, 100, 1000):
        line(c, xa(v), Y0, xa(v), Y1, GRID, 0.8)
        c.add_text(xa(v), Y0 + 16, f"{v:g}", size=11, color=MUTED, anchor="middle")
    for v, lab in ((1e12, "1 T"), (1e13, "10 T"), (1e14, "100 T"), (1e15, "1000 T")):
        line(c, X0, ya(v), X1, ya(v), GRID, 0.8)
        c.add_text(X0 - 6, ya(v) + 4, lab, size=11, color=MUTED, anchor="end")
    line(c, X0, Y0, X1, Y0, MUTED, 1.2)
    line(c, X0, Y0, X0, Y1, MUTED, 1.2)
    c.add_text((X0 + X1) / 2, Y0 + 34, "operational intensity (FLOP per byte of memory traffic, log scale)",
               size=11, color=TEXT, anchor="middle")
    c.add_raw(f'<text x="18" y="{(Y0 + Y1) / 2}" font-family="sans-serif" font-size="11" fill="{TEXT}" '
              f'text-anchor="middle" transform="rotate(-90 18 {(Y0 + Y1) / 2})">attainable FLOP/s (log scale)</text>')
    # roof: bandwidth slope then flat compute ceiling
    ridge = m["ridge"]
    line(c, xa(I_LO), ya(m["bandwidth"] * I_LO), xa(ridge), ya(m["peak"]), TEXT, 2.2, ident="roof-bandwidth")
    line(c, xa(ridge), ya(m["peak"]), xa(I_HI), ya(m["peak"]), TEXT, 2.2, ident="roof-compute")
    line(c, xa(ridge), ya(m["peak"]), xa(ridge), Y0, MUTED, 1, dash="4 3", ident="ridge")
    c.add_text(xa(ridge) + 4, Y0 - 8, f"ridge ≈ {ridge:.0f} FLOP/byte", size=11, color=MUTED)
    c.add_text(xa(40), ya(m["bandwidth"] * 40) + 56, "bandwidth-bound", size=11, color=MUTED, anchor="start")
    # sits a row above the prefill-attention label so the two never touch
    c.add_text(xa(4000), ya(m["peak"]) - 26, "compute-bound", size=11, color=MUTED, anchor="middle")
    # points
    style = {"decode-linear": col["stored"], "decode-attention": col["flag"], "prefill": col["compute"]}
    for p in m["points"]:
        x, y = xa(p["intensity"]), ya(p["attainable"])
        circle(c, x, y, 5, style[p["group"]], "#ffffff", ident=f"pt-{p['id']}",
               data={"intensity": f"{p['intensity']:g}", "bound": p["bound"]})
    lab = {p["id"]: p for p in m["points"]}
    # decode linear labels sit above-left of the rising roof; attention labels below-right
    for B in ("1", "16", "64", "256"):
        p = lab[f"decode-linear-B{B}"]
        c.add_text(xa(p["intensity"]) - 8, ya(p["attainable"]) - 7, p["label"], size=11, color=col["stored"], anchor="end")
    p512 = lab["decode-linear-B512"]
    c.add_text(xa(p512["intensity"]), ya(p512["attainable"]) + 20, "B=512", size=11, color=col["stored"], anchor="middle")
    g, h = lab["decode-attention-gqa"], lab["decode-attention-mha"]
    c.add_text(xa(h["intensity"]) + 8, ya(h["attainable"]) + 17, "attention, 32 KV heads (same point as B=1)",
               size=11, color=col["flag"], anchor="start")
    c.add_text(xa(g["intensity"]) + 8, ya(g["attainable"]) + 17, "attention, 8 KV heads", size=11, color=col["flag"], anchor="start")
    pl, pa = lab["prefill-linear"], lab["prefill-attention"]
    c.add_text(xa(pa["intensity"]), ya(pa["attainable"]) - 10, "prefill attention", size=11, color=col["compute"], anchor="middle")
    c.add_text(xa(pl["intensity"]), ya(pl["attainable"]) + 20, "prefill linear", size=11, color=col["compute"], anchor="middle")
    # legend
    lx, ly = X0 + 14, Y1 + 18
    # white backing so gridlines do not strike through the legend text
    c.add_raw(f'<rect x="{lx - 8}" y="{ly - 14}" width="232" height="52" fill="#ffffff" opacity="0.92"/>')
    for i, (name, key) in enumerate((("decode linear layers (B sequences)", "stored"),
                                     ("decode attention (any batch)", "flag"),
                                     ("prefill, one 2048-token prompt", "compute"))):
        circle(c, lx, ly + i * 16 - 4, 5, col[key], "#ffffff")
        c.add_text(lx + 10, ly + i * 16, name, size=11, color=TEXT)
    return c


def main():
    draw(build_model()).save(out_path(FIGURE_ID))
    print(f"wrote {out_path(FIGURE_ID)}")


if __name__ == "__main__":
    main()
