"""Chapter 2 figure: three requests' shared prefixes stored once in a radix
tree (one-token pages, as in RadixAttention), compared with full-block
hashing at a toy block size of 4.

What to notice: the tree stores the shared six-token system prefix once and
splits where requests diverge; each node's reference count is the number of
running requests using it, and only an unreferenced leaf (A's "cat") is
evictable, least recently used first. Under full-block hashing the same
requests can reuse only whole matching blocks, so B and C reuse fewer
tokens. Toy word "tokens"; a schematic, not any engine's internal state.

All values come from data/worked-examples/kv_cache_memory.json (radix).

Run: python3 workbooks/06-llm-inference/figures/source/fig_prefix_tree.py
Output: workbooks/06-llm-inference/figures/rendered/fig-prefix-tree.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import SVGCanvas, WIDTH, TEXT, MUTED, colors, line, load_example, out_path  # noqa: E402

FIGURE_ID = "fig-prefix-tree"
HEIGHT = 372
NODE_H = 40
COL_X = [62, 262, 438]       # left edge of each tree depth
COL_W = [180, 158, 158]


def build_model():
    d = load_example("kv_cache_memory.json")["radix"]
    return {"nodes": d["nodes"], "evict_order": d["evict_order"], "requests": d["requests"],
            "radix_matched": d["radix_matched_tokens"], "hash_reusable": d["hash_reusable_tokens"],
            "block": d["toy_block_tokens"]}


def _layout(nodes):
    """y position per node: leaves stacked in order, parents centred on children."""
    ys, next_y = {}, [54]
    kids = {n["id"]: [k["id"] for k in nodes if k["parent"] == n["id"]] for n in nodes}

    def place(nid):
        if not kids[nid]:
            ys[nid] = next_y[0]; next_y[0] += 50
        else:
            for k in kids[nid]:
                place(k)
            ys[nid] = sum(ys[k] for k in kids[nid]) / len(kids[nid])
    for n in nodes:
        if n["parent"] is None:
            place(n["id"])
    return ys


def draw(m):
    col = colors()
    c = SVGCanvas(WIDTH, HEIGHT, title="Radix-tree prefix reuse versus full-block hashing")
    c.add_text(WIDTH / 2, 18, "Shared prefixes stored once: radix tree vs full-block hashing (toy)",
               size=13, weight="bold", color=TEXT, anchor="middle")
    ys = _layout(m["nodes"])
    root_y = ys[0] + NODE_H / 2
    c.add_raw(f'<circle id="radix-root" cx="34" cy="{root_y:.1f}" r="7" fill="{TEXT}"/>')
    c.add_text(34, root_y + 22, "root", size=11, color=MUTED, anchor="middle")
    evictable = set(m["evict_order"])
    by_leaf = {r["tokens"][-1]: f"{r['name']}, {r['state']}" for r in m["requests"]}
    for n in m["nodes"]:
        x, w, y = COL_X[n["depth"]], COL_W[n["depth"]], ys[n["id"]]
        px = 41 if n["parent"] is None else COL_X[n["depth"] - 1] + COL_W[n["depth"] - 1]
        py = root_y if n["parent"] is None else ys[n["parent"]] + NODE_H / 2
        line(c, px, py, x, y + NODE_H / 2, MUTED, 1.3)
        ev = n["id"] in evictable
        stroke = col["flag"] if ev else (col["stored"] if n["ref"] > 1 else TEXT)
        fill = col["stored"] if n["ref"] > 1 else "#ffffff"
        dash = ' stroke-dasharray="4 3"' if ev else ""
        c.add_raw(f'<rect id="node-{n["id"]}" x="{x}" y="{y:.1f}" width="{w}" height="{NODE_H}" rx="5" '
                  f'fill="{fill}" fill-opacity="{0.25 if n["ref"] > 1 else 1}" stroke="{stroke}" '
                  f'stroke-width="1.5"{dash} data-ref="{n["ref"]}" '
                  f'data-evictable="{str(ev).lower()}"/>')
        owner = by_leaf.get(n["tokens"][-1], "") if n["leaf"] else ""
        c.add_text(x + 6, y + 16, " ".join(n["tokens"]) + (f"   ({owner})" if owner else ""),
                   size=11, color=TEXT, mono=True)
        c.add_text(x + 6, y + 32, f"ref {n['ref']}" + (", evictable first" if ev else ""),
                   size=11, color=col["flag"] if ev else MUTED)
    # full-block hashing comparison table
    y0 = 222
    line(c, 20, y0 - 12, WIDTH - 20, y0 - 12, "#d9d9d9", 1)
    c.add_text(20, y0 + 4, f"Same requests under full-block hashing (block = {m['block']} tokens):",
               size=11, weight="bold", color=TEXT)
    blk = m["block"]
    for i, r in enumerate(m["requests"][1:]):
        y = y0 + 22 + i * 62
        toks = r["tokens"]
        c.add_text(20, y + 15, r["name"], size=11, weight="bold", color=TEXT)
        reuse = m["hash_reusable"][r["name"]]
        for b in range(0, len(toks), blk):
            x = 44 + (b // blk) * 214
            hit = b + blk <= reuse
            c.add_raw(f'<rect id="hash-{r["name"]}-{b // blk}" x="{x}" y="{y}" width="206" height="24" rx="4" '
                      f'fill="{col["stored"] if hit else "#ffffff"}" fill-opacity="{0.25 if hit else 1}" '
                      f'stroke="{col["stored"] if hit else MUTED}" stroke-width="1.3" data-hit="{str(hit).lower()}"/>')
            c.add_text(x + 6, y + 16, " ".join(toks[b:b + blk]), size=11, color=TEXT, mono=True)
        c.add_text(44, y + 40, f"reused: {reuse} tokens by hashing vs {m['radix_matched'][r['name']]} in the tree",
                   size=11, color=TEXT)
    return c


def main():
    draw(build_model()).save(out_path(FIGURE_ID))
    print(f"wrote {out_path(FIGURE_ID)}")


if __name__ == "__main__":
    main()
