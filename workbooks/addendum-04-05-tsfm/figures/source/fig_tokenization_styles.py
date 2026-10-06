"""Module 1 figure: three ways to turn the SAME 12 values into model inputs.

What to notice: a bin id is an index into an embedding table, whereas a
patch is a vector of P values passed through a learned projection with no
table. The counts drawn (6 end-padded overlapping patches; 8 lag tokens)
come from data/worked-examples/w1_inputs.py, not from this script.
All settings (8 bins, P=4, S_p=2, lags 1/2/4) are illustrative.

Run: python3 workbooks/addendum-04-05-tsfm/figures/source/fig_tokenization_styles.py
Output: workbooks/addendum-04-05-tsfm/figures/rendered/fig-tokenization-styles.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import SVGCanvas, WIDTH, TEXT, MUTED, colors, load_example, out_path  # noqa: E402

FIGURE_ID = "fig-tokenization-styles"
HEIGHT = 425
X0, CELL = 118, 33.5   # first column x, column pitch (14 columns incl. 2 padded)


def build_model():
    w1 = load_example("w1_inputs.json")
    t = w1["t_ctx"]
    return {
        "t_ctx": t,
        "bin_ids": w1["bin_ids"],
        "n_bins": w1["n_bins"],
        "patches": w1["patch_windows"],
        "patch_length": w1["patch_length"],
        "stride": w1["stride"],
        "n_padded": w1["n_padded_positions"],
        "lags": w1["lags"],
        "lag_tokens": w1["lag_tokens"],
        "values": w1["series"],
    }


def col_x(i):
    return X0 + i * CELL


def draw(m):
    col = colors()
    c = SVGCanvas(WIDTH, HEIGHT, title="Three ways to tokenize the same 12 values")
    t = m["t_ctx"]

    def header(y, label, sub):
        c.add_text(10, y, label, size=13, weight="bold", color=TEXT)
        c.add_text(10, y + 15, sub, size=11, color=MUTED)

    def value_row(y, with_pad=False):
        for i, v in enumerate(m["values"]):
            c.add_rect(col_x(i), y, CELL - 3, 22, fill="#eaf2fb", stroke=col["observed"], stroke_width=1, rx=3)
            c.add_text(col_x(i) + (CELL - 3) / 2, y + 15, v, size=11, color=TEXT, anchor="middle")
        if with_pad:
            for k in range(m["n_padded"]):
                i = t + k
                c.add_rect(col_x(i), y, CELL - 3, 22, fill="#ffffff", stroke=col["inactive"], stroke_width=1, rx=3, dash="dashed")
                c.add_text(col_x(i) + (CELL - 3) / 2, y + 15, "pad", size=11, color=MUTED, anchor="middle")

    c.add_text(WIDTH / 2, 18, "The same 12 values, three input styles (all settings illustrative)", size=13, weight="bold", color=TEXT, anchor="middle")

    # Row A: bin tokens
    ya = 40
    header(ya + 12, "A. Bin tokens", "scaled, then binned")
    value_row(ya)
    for i, b in enumerate(m["bin_ids"]):
        c.add_rect(col_x(i), ya + 36, CELL - 3, 22, fill=col["forecast"], stroke="#333333", stroke_width=1, rx=3)
        c.add_text(col_x(i) + (CELL - 3) / 2, ya + 51, f"id {b}", size=11, color=TEXT, anchor="middle")
        c.add_arrow(col_x(i) + (CELL - 3) / 2, ya + 23, col_x(i) + (CELL - 3) / 2, ya + 35, color="#555555", stroke_width=1)
    c.add_text(X0, ya + 76, f"each id selects one row of an embedding table ({m['n_bins']} bins here; a table lookup, no arithmetic on the values)", size=11, color=MUTED)

    # Row B: patch tokens
    yb = 140
    header(yb + 12, "B. Patch tokens", f"P = {m['patch_length']}, S_p = {m['stride']}")
    value_row(yb, with_pad=True)
    lane_y = [yb + 32, yb + 50]
    for k, w in enumerate(m["patches"]):
        x1 = col_x(w[0])
        x2 = col_x(w[-1]) + CELL - 3
        y = lane_y[k % 2]
        pad_here = any(i >= m["t_ctx"] for i in w)
        c.add_raw(f'<g id="patch-{k}">')
        c.add_rect(x1, y, x2 - x1, 14, fill=col["trainable"] if not pad_here else "#ffffff", stroke=col["trainable"],
                   stroke_width=1.5, rx=3, dash="dashed" if pad_here else None)
        c.add_text((x1 + x2) / 2, y + 11, f"patch {k + 1}", size=11, color=TEXT if pad_here else "#ffffff", anchor="middle", weight="bold")
        c.add_raw("</g>")
    c.add_text(X0, yb + 90, f"{len(m['patches'])} patches, last one end-padded (dashed). Each patch of P values goes through a learned", size=11, color=MUTED)
    c.add_text(X0, yb + 104, "projection to one d_model vector: no table. Without overlap and padding: 3 patches.", size=11, color=MUTED)

    # Row C: lag tokens
    yc = 262
    header(yc + 12, "C. Lag tokens", f"lags {', '.join(str(x) for x in m['lags'])}")
    value_row(yc)
    for tok in m["lag_tokens"]:
        i = tok["t"] - 1
        cx = col_x(i) + (CELL - 3) / 2
        c.add_raw(f'<g id="lag-token-{tok["t"]}">')
        c.add_rect(col_x(i), yc + 40, CELL - 3, 22, fill=col["trainable"], stroke="#333333", stroke_width=1, rx=3)
        c.add_text(cx, yc + 55, f"t={tok['t']}", size=11, color="#ffffff", anchor="middle", weight="bold")
        c.add_raw("</g>")
    first = m["lag_tokens"][0]["t"]
    for j in range(first - 1):
        cx = col_x(j) + (CELL - 3) / 2
        c.add_text(cx, yc + 55, "–", size=12, color=MUTED, anchor="middle")
    # lag marks for the last token
    last = m["lag_tokens"][-1]
    cx_last = col_x(last["t"] - 1) + (CELL - 3) / 2
    for src in last["lag_indices"]:
        cx_src = col_x(src - 1) + (CELL - 3) / 2
        c.add_arrow(cx_last, yc + 40, cx_src, yc + 24, style="dotted", color=col["observed"], stroke_width=1.2)
    c.add_text(X0, yc + 82, f"one token per time step; needs the largest lag ({max(m['lags'])}) of history, so {len(m['lag_tokens'])} of {t} steps", size=11, color=MUTED)
    c.add_text(X0, yc + 96, "yield a token (dotted arrows: the lags feeding the last token).", size=11, color=MUTED)

    # legend
    ly = 392
    c.add_rect(10, ly, 14, 14, fill="#eaf2fb", stroke=col["observed"], stroke_width=1, rx=3)
    c.add_text(30, ly + 11, "observed value", size=11, color=TEXT)
    c.add_rect(140, ly, 14, 14, fill=col["forecast"], stroke="#333333", stroke_width=1, rx=3)
    c.add_text(160, ly + 11, "discrete token (lookup)", size=11, color=TEXT)
    c.add_rect(310, ly, 14, 14, fill=col["trainable"], stroke="#333333", stroke_width=1, rx=3)
    c.add_text(330, ly + 11, "continuous input (projected)", size=11, color=TEXT)
    c.add_rect(500, ly, 14, 14, fill="#ffffff", stroke=col["inactive"], stroke_width=1, rx=3, dash="dashed")
    c.add_text(520, ly + 11, "padding", size=11, color=TEXT)
    return c


def main():
    m = build_model()
    c = draw(m)
    c.save(out_path(FIGURE_ID))
    print(f"wrote {out_path(FIGURE_ID)}")


if __name__ == "__main__":
    main()
