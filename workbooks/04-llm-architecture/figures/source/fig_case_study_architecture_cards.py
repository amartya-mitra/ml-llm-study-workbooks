"""Chapter 6 figure: three case-study models redrawn in one consistent
visual grammar (an "architecture card" per model), so their mechanism
differences are directly comparable by position rather than only by
table lookup.

What to notice: all three stack repeated blocks (schematic -- the true
repeat counts are given in each panel's caption, not drawn N times).
The load-bearing difference is the cache-state icon at the bottom of
each panel: Llama 3's grows every layer; DeepSeek-V3's grows but at a
compressed per-token size; Jamba's is mostly a fixed-size box (its
Mamba layers) with a small growing component (its few attention
layers) -- this is the ONE distinction Chapter 6 wants a reader to
notice at a glance.

Run: python3 workbooks/04-llm-architecture/figures/source/fig_case_study_architecture_cards.py
Output: figures/rendered/fig-case-study-architecture-cards.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-case-study-architecture-cards"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

# Full-width (6.5in) embed, W=1020 -> 1 unit = 6.5*72/1020 = 0.4588pt.
# Need ~19.6 units for a 9pt essential label.
TITLE_SIZE = 19
LABEL_SIZE = 17
SMALL_SIZE = 15
TINY_SIZE = 13


def panel_header(canvas, x0, panel_w, name, version):
    cx = x0 + panel_w / 2
    canvas.add_text(cx, 24, name, size=TITLE_SIZE, weight="bold", anchor="middle")
    canvas.add_text(cx, 44, version, size=TINY_SIZE, color="#555555", anchor="middle")


def growing_bars(canvas, x0, y0, blue):
    heights = [12, 19, 26, 33]
    for i, h in enumerate(heights):
        canvas.add_rect(x0 + i * 20, y0 + (33 - h), 15, h, fill=blue, stroke="#333333", stroke_width=1)


def fixed_box(canvas, x0, y0, gray):
    canvas.add_rect(x0, y0, 40, 33, fill=gray, stroke="#333333", stroke_width=1)


def panel_llama(canvas, x0, panel_w, colors):
    blue = colors["stored_information"]
    bx, bw = x0 + 18, panel_w - 36
    by = 48
    bh = 26
    canvas.add_rect(bx, by, bw, bh, fill=blue, stroke="#333333", stroke_width=1.5, rx=5)
    canvas.add_text(bx + bw / 2, by + 18, "Attn: full causal, GQA (8 KV heads)", size=TINY_SIZE, color="#ffffff", anchor="middle")
    by2 = by + bh + 8
    canvas.add_rect(bx, by2, bw, bh, fill=blue, stroke="#333333", stroke_width=1.5, rx=5)
    canvas.add_text(bx + bw / 2, by2 + 18, "FFN: dense (SwiGLU)", size=TINY_SIZE, color="#ffffff", anchor="middle")
    canvas.add_text(x0 + panel_w / 2, by2 + bh + 18, "block repeated x126 (schematic)", size=SMALL_SIZE, color="#555555", anchor="middle")

    cache_y = by2 + bh + 32
    growing_bars(canvas, bx + 10, cache_y, blue)
    canvas.add_text(x0 + panel_w / 2, cache_y + 48, "cache state: full K/V,", size=SMALL_SIZE, anchor="middle")
    canvas.add_text(x0 + panel_w / 2, cache_y + 64, "grows every layer/token", size=SMALL_SIZE, anchor="middle")
    return cache_y + 64


def panel_deepseek(canvas, x0, panel_w, colors):
    blue = colors["stored_information"]
    orange = colors["computation"]
    gray_inactive = "#e6e6e6"
    bx, bw = x0 + 18, panel_w - 36
    by = 48
    bh = 26
    canvas.add_rect(bx, by, bw, bh, fill=orange, stroke="#333333", stroke_width=1.5, rx=5)
    canvas.add_text(bx + bw / 2, by + 18, "Attn: MLA (compressed latent)", size=TINY_SIZE, color="#ffffff", anchor="middle")
    by2 = by + bh + 8
    canvas.add_rect(bx, by2, bw, bh, fill=blue, stroke="#333333", stroke_width=1.5, rx=5)
    canvas.add_text(bx + bw / 2, by2 + 18, "FFN: 1 shared + 256 routed (8 active)", size=TINY_SIZE, color="#ffffff", anchor="middle")
    canvas.add_text(x0 + panel_w / 2, by2 + bh + 18, "block repeated x58 of 61 (schematic)", size=SMALL_SIZE, color="#555555", anchor="middle")

    # Expert row: schematic 8 squares, 1 highlighted (shared, always active)
    # plus 7 "active" of a much larger routed bank (not drawn to scale).
    row_y = by2 + bh + 22
    n = 8
    sq = 16
    gap = 4
    ex0 = x0 + panel_w / 2 - (n * (sq + gap) - gap) / 2
    for i in range(n):
        ex = ex0 + i * (sq + gap)
        fill = orange if i < 7 else blue
        canvas.add_rect(ex, row_y, sq, sq, fill=fill, stroke="#333333", stroke_width=1, rx=2)
    canvas.add_text(x0 + panel_w / 2, row_y + sq + 12, "8 of 256 routed active + 1 shared (schematic, not to scale)", size=TINY_SIZE, color="#555555", anchor="middle")

    cache_y = row_y + sq + 18
    growing_bars(canvas, bx + 10, cache_y, blue)
    canvas.add_text(x0 + panel_w / 2, cache_y + 48, "cache state: compressed latent,", size=SMALL_SIZE, anchor="middle")
    canvas.add_text(x0 + panel_w / 2, cache_y + 64, "grows every layer, smaller per token", size=SMALL_SIZE, anchor="middle")
    return cache_y + 64


def panel_jamba(canvas, x0, panel_w, colors):
    blue = colors["stored_information"]
    orange = colors["computation"]
    gray = colors["frozen_or_inactive"]
    bx, bw = x0 + 18, panel_w - 36
    by = 48
    bh = 26
    canvas.add_rect(bx, by, bw, bh, fill=gray, stroke="#333333", stroke_width=1.5, rx=5)
    canvas.add_text(bx + bw / 2, by + 18, "Mostly: Mamba (selective SSM)", size=TINY_SIZE, color="#ffffff", anchor="middle")
    by2 = by + bh + 8
    canvas.add_rect(bx, by2, bw, bh, fill=blue, stroke="#333333", stroke_width=1.5, rx=5)
    canvas.add_text(bx + bw / 2, by2 + 18, "Occasionally: Attn, GQA (32/8 heads)", size=TINY_SIZE, color="#ffffff", anchor="middle")
    canvas.add_text(x0 + panel_w / 2, by2 + bh + 18, "1 attn : 7 Mamba layers x4 blocks (schematic)", size=SMALL_SIZE, color="#555555", anchor="middle")

    row_y = by2 + bh + 22
    n = 8
    sq = 16
    gap = 4
    ex0 = x0 + panel_w / 2 - (n * (sq + gap) - gap) / 2
    for i in range(n):
        ex = ex0 + i * (sq + gap)
        fill = orange if i < 2 else "#e6e6e6"
        canvas.add_rect(ex, row_y, sq, sq, fill=fill, stroke="#333333", stroke_width=1, rx=2)
    canvas.add_text(x0 + panel_w / 2, row_y + sq + 12, "2 of 16 routed active, no shared expert (schematic)", size=TINY_SIZE, color="#555555", anchor="middle")

    cache_y = row_y + sq + 18
    fixed_box(canvas, bx + 10, cache_y, gray)
    growing_bars(canvas, bx + 60, cache_y, blue)
    canvas.add_text(x0 + panel_w / 2, cache_y + 48, "cache state: mostly fixed size,", size=SMALL_SIZE, anchor="middle")
    canvas.add_text(x0 + panel_w / 2, cache_y + 64, "small growing part (attn layers only)", size=SMALL_SIZE, anchor="middle")
    return cache_y + 64


def main():
    style = load_visual_style()
    colors = palette_hex(style)

    W = 1020
    canvas = SVGCanvas(width=W, height=1, title="Three case-study architectures in one visual grammar")

    panel_w = W / 3 - 10
    gap = 15

    x_positions = [0, panel_w + gap, 2 * (panel_w + gap)]

    panel_header(canvas, x_positions[0], panel_w, "Llama 3 405B", "dense, Meta, 2024-07-31")
    bottom1 = panel_llama(canvas, x_positions[0], panel_w, colors)

    panel_header(canvas, x_positions[1], panel_w, "DeepSeek-V3", "MoE + MLA, 2024-12-27")
    bottom2 = panel_deepseek(canvas, x_positions[1], panel_w, colors)

    panel_header(canvas, x_positions[2], panel_w, "Jamba", "hybrid, AI21, 2024-03-28")
    bottom3 = panel_jamba(canvas, x_positions[2], panel_w, colors)

    legend_y = max(bottom1, bottom2, bottom3) + 30
    blue = colors["stored_information"]
    orange = colors["computation"]
    gray = colors["frozen_or_inactive"]
    canvas.add_rect(20, legend_y, 16, 16, fill=blue, rx=2)
    canvas.add_text(44, legend_y + 13, "stored/active state or dense path", size=SMALL_SIZE)
    canvas.add_rect(20, legend_y + 26, 16, 16, fill=orange, rx=2)
    canvas.add_text(44, legend_y + 39, "computed/compressed or MoE-active path", size=SMALL_SIZE)
    canvas.add_rect(20, legend_y + 52, 16, 16, fill=gray, rx=2)
    canvas.add_text(44, legend_y + 65, "fixed-size/recurrent or inactive", size=SMALL_SIZE)

    canvas.height = legend_y + 90
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
