"""Chapter 4 figure: MLA's cache pathway, from hidden state to
attention-compatible use during decode.

What to notice: only the compressed latent and the decoupled rotary
component are cached -- not full per-head K/V. Reconstructing full K/V
from the latent (left path) is always a CONCEPTUALLY valid derivation,
but an optimized implementation may instead take the dashed path
(matrix absorption), which never materializes full K/V at all. Neither
path is drawn as mandatory; the figure marks the absorption path as
optional/implementation-dependent.

Run: python3 workbooks/04-llm-architecture/figures/source/fig_mla_cache_pathway.py
Output: figures/rendered/fig-mla-cache-pathway.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-mla-cache-pathway"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

# Full-width (6.5in) embed, W=700 -> 1 unit = 6.5*72/700 = 0.6686pt.
# Need ~13.5 units for a 9pt essential label; use 15-16 for headroom.
LABEL_SIZE = 15
SMALL_SIZE = 13


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    blue = colors["stored_information"]
    orange = colors["computation"]

    W = 700
    canvas = SVGCanvas(width=W, height=1, title="MLA cache pathway: compression, cached latent, and decode-time use")

    cx = W / 2

    # Hidden state.
    hs_w, hs_h = 200, 40
    canvas.add_rect(cx - hs_w / 2, 20, hs_w, hs_h, fill="#ffffff", stroke="#333333", stroke_width=1.5, rx=6)
    canvas.add_text(cx, 20 + hs_h / 2 + 5, "hidden state h_t", size=LABEL_SIZE, anchor="middle")

    canvas.add_arrow(cx, 20 + hs_h, cx, 20 + hs_h + 24, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_text(cx + 10, 20 + hs_h + 18, "compress (down-projection)", size=SMALL_SIZE, color="#555555")

    # Cached row: latent + rope component.
    cache_y = 20 + hs_h + 30
    lat_w, lat_h = 220, 44
    rope_w = 160
    gap = 30
    total_w = lat_w + gap + rope_w
    lx = cx - total_w / 2
    canvas.add_rect(lx, cache_y, lat_w, lat_h, fill=blue, stroke="#333333", stroke_width=2, rx=6)
    canvas.add_text(lx + lat_w / 2, cache_y + lat_h / 2 + 5, "latent c_t^KV (d_c)", size=LABEL_SIZE, color="#ffffff", anchor="middle")
    rx = lx + lat_w + gap
    canvas.add_rect(rx, cache_y, rope_w, lat_h, fill=blue, stroke="#333333", stroke_width=2, rx=6)
    canvas.add_text(rx + rope_w / 2, cache_y + lat_h / 2 - 2, "rope key k_t^R", size=LABEL_SIZE, color="#ffffff", anchor="middle")
    canvas.add_text(rx + rope_w / 2, cache_y + lat_h / 2 + 16, "(d_rope)", size=SMALL_SIZE, color="#ffffff", anchor="middle")

    text_y1 = cache_y + lat_h + 22
    text_y2 = cache_y + lat_h + 40
    canvas.add_text(cx, text_y1, "cached during inference (per token, per layer)", size=SMALL_SIZE, color="#555555", anchor="middle")
    canvas.add_text(cx, text_y2, "separate component needed: RoPE applied to the latent would break matrix absorption",
                     size=SMALL_SIZE, color="#555555", anchor="middle")

    arrow_start_y = text_y2 + 25
    branch_y = arrow_start_y + 55
    left_x = cx - 170
    right_x = cx + 170

    canvas.add_arrow(cx - 30, arrow_start_y, left_x, branch_y - 30, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_arrow(cx + 30, arrow_start_y, right_x, branch_y - 30, style="dashed", color="#333333", stroke_width=1.5)

    # Left path: conceptual reconstruction.
    rec_w, rec_h = 220, 46
    canvas.add_text(left_x, branch_y - 8, "conceptual derivation", size=SMALL_SIZE, weight="bold", anchor="middle")
    canvas.add_rect(left_x - rec_w / 2, branch_y, rec_w, rec_h, fill="#ffffff", stroke="#333333", stroke_width=1.5, rx=6)
    canvas.add_text(left_x, branch_y + rec_h / 2 - 2, "reconstruct per-head K/V", size=SMALL_SIZE, anchor="middle")
    canvas.add_text(left_x, branch_y + rec_h / 2 + 14, "(up-projection; not cached)", size=SMALL_SIZE, color="#555555", anchor="middle")

    # Right path: optional matrix absorption.
    canvas.add_text(right_x, branch_y - 8, "optional: matrix absorption", size=SMALL_SIZE, weight="bold", anchor="middle")
    canvas.add_rect(right_x - rec_w / 2, branch_y, rec_w, rec_h, fill="#ffffff", stroke=colors["bottleneck_or_failure"], stroke_width=1.5, dash="dashed", rx=6)
    canvas.add_text(right_x, branch_y + rec_h / 2 - 8, "W^UK folded into W^Q,", size=SMALL_SIZE, anchor="middle")
    canvas.add_text(right_x, branch_y + rec_h / 2 + 6, "W^UV folded into W^O", size=SMALL_SIZE, anchor="middle")
    canvas.add_text(right_x, branch_y + rec_h / 2 + 20, "(implementation-dependent)", size=SMALL_SIZE, color="#555555", anchor="middle")

    out_y = branch_y + rec_h + 30
    canvas.add_arrow(left_x, branch_y + rec_h, cx, out_y, style="solid", color="#333333", stroke_width=1.5)
    canvas.add_arrow(right_x, branch_y + rec_h, cx, out_y, style="dashed", color="#333333", stroke_width=1.5)
    out_w, out_h = 220, 40
    canvas.add_rect(cx - out_w / 2, out_y, out_w, out_h, fill=orange, stroke="#333333", stroke_width=2, rx=6)
    canvas.add_text(cx, out_y + out_h / 2 + 5, "attention score / output", size=LABEL_SIZE, color="#ffffff", anchor="middle")

    canvas.height = out_y + out_h + 25
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
