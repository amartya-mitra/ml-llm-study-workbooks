"""Chapter 2 figure: two requests' block tables mapping logical KV blocks to
physical blocks, with a shared, reference-counted prefix.

What to notice: R1 and R2 begin with the same eight-token prefix, so their
first two logical blocks map to the same physical blocks (reference count
2); each request's last block is private and only partly filled (the empty
slots are internal fragmentation, bounded by one block per request); and
the counts at the bottom keep unique physical blocks, logical references,
allocated slots and live tokens apart. Toy block size of 4 word "tokens";
a schematic of the mechanism, not any engine's internal state.

All values come from data/worked-examples/kv_cache_memory.json
(lifecycle.snapshots[0]).

Run: python3 workbooks/06-llm-inference/figures/source/fig_block_table.py
Output: workbooks/06-llm-inference/figures/rendered/fig-block-table.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import SVGCanvas, WIDTH, TEXT, MUTED, colors, line, load_example, out_path  # noqa: E402

FIGURE_ID = "fig-block-table"
HEIGHT = 392
BOX_W, BOX_H, GAP = 66, 76, 6
X_POOL = 30
Y_R1, Y_POOL, Y_R2 = 58, 160, 284


def build_model():
    d = load_example("kv_cache_memory.json")
    snap = d["lifecycle"]["snapshots"][0]
    nblocks = d["lifecycle"]["pool_blocks"]
    tok = d["lifecycle"]["block_tokens"]
    physical = []
    for b in range(nblocks):
        ref = snap["ref"].get(str(b), 0)
        toks = snap["block_tokens"].get(str(b), [])
        physical.append({"id": b, "ref": ref, "tokens": toks, "filled": len(toks),
                         "state": "free" if ref == 0 else ("shared" if ref > 1 else "private")})
    tables = {r: list(t) for r, t in snap["tables"].items()}
    counts = {k: snap[k] for k in ("unique_physical_blocks", "logical_references",
                                   "allocated_slots", "live_tokens", "unique_stored_tokens")}
    return {"block_tokens": tok, "physical": physical, "tables": tables, "counts": counts,
            "lengths": snap["lengths"]}


def _x(b):
    return X_POOL + b * (BOX_W + GAP)


def _rect(c, x, y, w, h, fill, stroke, opacity=1.0, dash=None, ident=None, data=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    i = f' id="{ident}"' if ident else ""
    extra = "".join(f' data-{k}="{v}"' for k, v in (data or {}).items())
    c.add_raw(f'<rect{i} x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="4" fill="{fill}" '
              f'fill-opacity="{opacity}" stroke="{stroke}" stroke-width="1.3"{d}{extra}/>')


def draw(m):
    col = colors()
    c = SVGCanvas(WIDTH, HEIGHT, title="Block tables mapping logical KV blocks to physical blocks")
    c.add_text(WIDTH / 2, 18, "Two block tables over one physical block pool (toy block size 4)",
               size=13, weight="bold", color=TEXT, anchor="middle")
    fills = {"shared": (col["stored"], 0.30), "private": (col["compute"], 0.22), "free": ("#ffffff", 1.0)}
    tok = m["block_tokens"]
    c.add_text(_x(4) + 2, Y_POOL - 8, "physical blocks (pool of 8)", size=11, color=MUTED)
    for p in m["physical"]:
        x, y = _x(p["id"]), Y_POOL
        f, op = fills[p["state"]]
        _rect(c, x, y, BOX_W, BOX_H, f, col["stored"] if p["state"] == "shared" else
              (col["compute"] if p["state"] == "private" else MUTED), op,
              dash="4 3" if p["state"] == "free" else None, ident=f"phys-{p['id']}",
              data={"ref": p["ref"], "filled": p["filled"], "state": p["state"]})
        head = f"P{p['id']}" + (f"  ref {p['ref']}" if p["ref"] else "  free")
        c.add_text(x + 5, y + 15, head, size=11, weight="bold", color=TEXT)
        words = p["tokens"]
        # wrap to lines of at most 10 characters so a short trailing token stays on its line
        lines, cur = [], ""
        for w in words:
            cand = (cur + " " + w).strip()
            if len(cand) > 10 and cur:
                lines.append(cur); cur = w
            else:
                cur = cand
        if cur:
            lines.append(cur)
        for k, ln in enumerate(lines):
            c.add_text(x + 5, y + 31 + 13 * k, ln, size=11, color=TEXT, mono=True)
        for s in range(tok):                 # slot bar: filled vs empty slots
            sx = x + 5 + s * ((BOX_W - 10) / tok)
            filled = s < p["filled"]
            c.add_raw(f'<rect x="{sx:.1f}" y="{y + BOX_H - 13}" width="{(BOX_W - 10) / tok - 2:.1f}" height="8" '
                      f'fill="{TEXT if filled else "#ffffff"}" fill-opacity="{0.55 if filled else 1}" '
                      f'stroke="{MUTED}" stroke-width="0.8"/>')
    for req, y, below in (("R1", Y_R1, True), ("R2", Y_R2, False)):
        table = m["tables"][req]
        c.add_text(X_POOL - 4, y - 8 if below else y + 52, f"{req} block table ({m['lengths'][req]} tokens)",
                   size=11, weight="bold", color=TEXT)
        for li, pb in enumerate(table):
            x = _x(pb)
            _rect(c, x + 6, y, BOX_W - 12, 34, "#ffffff", TEXT, ident=f"log-{req}-{li}",
                  data={"physical": pb})
            c.add_text(x + BOX_W / 2, y + 15, f"logical {li}", size=11, color=TEXT, anchor="middle")
            c.add_text(x + BOX_W / 2, y + 28, f"to P{pb}", size=11, color=MUTED, anchor="middle")
            if below:
                c.add_arrow(x + BOX_W / 2, y + 34, x + BOX_W / 2, Y_POOL - 2, color=TEXT, stroke_width=1.4)
            else:
                c.add_arrow(x + BOX_W / 2, y, x + BOX_W / 2, Y_POOL + BOX_H + 2, color=TEXT, stroke_width=1.4)
    k = m["counts"]
    c.add_text(X_POOL - 4, HEIGHT - 30,
               f"unique physical blocks {k['unique_physical_blocks']} · logical references {k['logical_references']}"
               f" · allocated slots {k['allocated_slots']}", size=11, color=TEXT)
    c.add_text(X_POOL - 4, HEIGHT - 14,
               f"stored tokens {k['unique_stored_tokens']} · live tokens across both requests {k['live_tokens']}"
               "  (filled bar cells = written slots)", size=11, color=TEXT)
    return c


def main():
    draw(build_model()).save(out_path(FIGURE_ID))
    print(f"wrote {out_path(FIGURE_ID)}")


if __name__ == "__main__":
    main()
