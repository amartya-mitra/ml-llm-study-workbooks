"""Stage 6 demonstration figure: prefill, KV-cache creation, and one
autoregressive decode step that extends the cache.

What to notice: the prefill pass builds the *entire* KV-cache in one shot
from the prompt tokens (orange compute, once), while each decode step
afterwards is a *small, incremental* computation that reads the whole
existing cache but only ever appends one new blue slot to it — the cache
grows by exactly one K/V pair per generated token, it is never
recomputed from scratch.

This figure is original, generated from this script, and uses only the
semantic palette defined in config/visual-style.yaml (no colors are
hardcoded here).

Run: python3 figures/source/kv_cache_demo.py
Output: figures/rendered/kv_cache_demo.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "kv_cache_demo"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_PATH = os.path.join(REPO_ROOT, "figures", "rendered", f"{FIGURE_ID}.svg")

PROMPT_TOKENS = ["The", "cat", "sat", "on"]
NEW_TOKEN = "the"


def token_row(canvas, tokens, x0, y0, box_w, box_h, gap, fill, text_color="#ffffff", highlight_idx=None, stroke=None, size=16):
    xs = []
    for i, tok in enumerate(tokens):
        x = x0 + i * (box_w + gap)
        box_fill = fill
        box_stroke = stroke or "#333333"
        canvas.add_rect(x, y0, box_w, box_h, fill=box_fill, stroke=box_stroke, stroke_width=2)
        canvas.add_text(x + box_w / 2, y0 + box_h / 2 + 5, tok, size=size, color=text_color, anchor="middle")
        xs.append(x + box_w / 2)
    return xs


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    blue = colors["stored_information"]
    orange = colors["computation"]
    gray = colors["frozen_or_inactive"]

    # This figure embeds at 100% of the 6.5in text column, so 1 SVG unit =
    # 6.5*72/W points at final size. Sizes below target >= 8-9pt for
    # essential labels (box/section names) and >= 7pt for secondary
    # annotations (see the review notes behind scripts/build_ch01_02_review.py).
    # height is a placeholder; the real height is derived from content and
    # set on `canvas` just before save() (see the legend_y block below).
    W = 920
    canvas = SVGCanvas(width=W, height=1, title="KV-cache: prefill then one decode step")

    canvas.add_text(20, 32, "Prefill: build the whole KV-cache from the prompt in one pass", size=18, weight="bold")

    tok_x0, tok_y0, box_w, box_h, gap = 20, 58, 60, 40, 12
    tok_centers = token_row(canvas, PROMPT_TOKENS, tok_x0, tok_y0, box_w, box_h, gap, fill=blue)

    compute_x, compute_y, compute_w, compute_h = 20, 142, 340, 72
    canvas.add_rect(compute_x, compute_y, compute_w, compute_h, fill=orange, stroke="#333333", stroke_width=2)
    canvas.add_text(compute_x + compute_w / 2, compute_y + compute_h / 2 - 4, "Prefill forward pass",
                     size=15, color="#ffffff", anchor="middle")
    canvas.add_text(compute_x + compute_w / 2, compute_y + compute_h / 2 + 18, "(attention + MLP, all 4 tokens at once)",
                     size=15, color="#ffffff", anchor="middle")

    for cx in tok_centers:
        canvas.add_arrow(cx, tok_y0 + box_h, cx, compute_y, style="solid", color="#333333", stroke_width=1.5)

    # Layout note: the connecting arrow and the section label below it must
    # not share a y-band, or the arrow draws straight through the label
    # text (found via visual inspection of the rendered PDF). The label
    # sits immediately under the compute box; the arrow only starts once
    # the label's text has fully cleared.
    label1_y = compute_y + compute_h + 20
    arrow1_y0 = label1_y + 10
    cache_y0 = arrow1_y0 + 22
    cache_box_w, cache_box_h = box_w, 34
    canvas.add_text(20, label1_y, "KV-cache after prefill (one slot per prompt token)", size=16, weight="bold")
    cache_x0 = tok_x0
    cache_centers = []
    for i, tok in enumerate(PROMPT_TOKENS):
        x = cache_x0 + i * (box_w + gap)
        canvas.add_rect(x, cache_y0, cache_box_w, cache_box_h, fill=blue, stroke="#333333", stroke_width=1.5)
        canvas.add_text(x + cache_box_w / 2, cache_y0 + cache_box_h / 2 + 5, f"K/V[{i}]", size=14, color="#ffffff", anchor="middle")
        cache_centers.append(x + cache_box_w / 2)
    canvas.add_arrow(compute_x + compute_w / 2, arrow1_y0, compute_x + compute_w / 2, cache_y0 - 4,
                      style="solid", color="#333333", stroke_width=1.5)

    canvas.add_raw(f'<line x1="20" y1="{cache_y0+59}" x2="{W-20}" y2="{cache_y0+59}" stroke="#cccccc" stroke-width="1"/>')

    row2_y = cache_y0 + 84
    canvas.add_text(20, row2_y, "Decode step: one new token reuses the whole cache, then extends it by one slot", size=18, weight="bold")

    # The section-2 title sits between the first cache row and the decode
    # box, directly in the path of the "decode reads the cache" dotted
    # lines below. A tight gap here (an earlier version used +20/-10) left
    # no room for those lines and they were drawn straight through the
    # title text (caught by visual inspection). Widen the gap and break
    # each dotted line into two segments that skip over the title's text.
    new_tok_x, new_tok_y = 20, row2_y + 58
    canvas.add_rect(new_tok_x, new_tok_y, box_w, box_h, fill=blue, stroke="#333333", stroke_width=2)
    canvas.add_text(new_tok_x + box_w / 2, new_tok_y + box_h / 2 + 5, NEW_TOKEN, size=16, color="#ffffff", anchor="middle")
    # Placed below the box (not above, as an earlier version had it) so it
    # cannot sit in the same y-band as the dotted "decode reads the cache"
    # line's arrowhead just above the box -- at this label's larger,
    # legible font size that arrowhead was drawn straight through the text
    # (caught by visual inspection).
    canvas.add_text(new_tok_x, new_tok_y + box_h + 16, "new token", size=13, color="#555555")

    decode_x, decode_y, decode_w, decode_h = 160, new_tok_y - 10, 420, 72
    canvas.add_rect(decode_x, decode_y, decode_w, decode_h, fill=orange, stroke="#333333", stroke_width=2)
    canvas.add_text(decode_x + decode_w / 2, decode_y + decode_h / 2 - 4, "Decode forward pass",
                     size=15, color="#ffffff", anchor="middle")
    canvas.add_text(decode_x + decode_w / 2, decode_y + decode_h / 2 + 18, "(1 new token attends to all cached K/V)",
                     size=15, color="#ffffff", anchor="middle")

    canvas.add_arrow(new_tok_x + box_w, new_tok_y + box_h / 2, decode_x, decode_y + decode_h / 2, style="solid", color="#333333", stroke_width=1.5)

    # These dotted lines show "decode reads the whole existing cache".
    # Segment A runs from the cache boxes down to just above the title;
    # segment B resumes just below the title (with the arrowhead) and
    # stops at the decode box's top edge, never tunneling through either.
    title_clear_above = row2_y - 12
    title_clear_below = row2_y + 10
    for cx in cache_centers:
        canvas.add_raw(
            f'<line x1="{cx}" y1="{cache_y0 + cache_box_h}" x2="{cx}" y2="{title_clear_above}" '
            f'stroke="{gray}" stroke-width="1.2" stroke-dasharray="2,3"/>'
        )
        canvas.add_arrow(cx, title_clear_below, cx, decode_y - 2, style="dotted", color=gray, stroke_width=1.2)

    label2_y = decode_y + decode_h + 20
    arrow2_y0 = label2_y + 10
    new_cache_y = arrow2_y0 + 22
    canvas.add_text(20, label2_y, "KV-cache after this decode step (cache grew by exactly one slot)", size=16, weight="bold")
    all_tokens = PROMPT_TOKENS + [NEW_TOKEN]
    for i, tok in enumerate(all_tokens):
        x = cache_x0 + i * (box_w + gap)
        is_new = i == len(all_tokens) - 1
        fill = orange if is_new else blue
        canvas.add_rect(x, new_cache_y, cache_box_w, cache_box_h, fill=fill, stroke="#333333", stroke_width=2 if is_new else 1.5)
        canvas.add_text(x + cache_box_w / 2, new_cache_y + cache_box_h / 2 + 5, f"K/V[{i}]", size=14, color="#ffffff", anchor="middle")

    canvas.add_arrow(decode_x + decode_w / 2, arrow2_y0, decode_x + decode_w / 2, new_cache_y - 4,
                      style="solid", color="#333333", stroke_width=1.5)
    canvas.add_text(decode_x + decode_w / 2 + 8, arrow2_y0 + 15, "+1 new K/V pair appended", size=13, color="#333333")

    loop_y = new_cache_y + cache_box_h + 34
    canvas.add_text(20, loop_y, "Repeated once per generated token until a stop condition (dotted = conditional, not always taken):", size=13, color="#555555")
    # A straight diagonal line back to the decode box would cut through the
    # label2/arrow2 band and the cache boxes themselves (caught by visual
    # inspection of an earlier version). Route it along the right margin
    # instead, where nothing else is drawn, so it never crosses other ink.
    gray_marker_id = canvas._ensure_marker(gray)
    loop_start_x = cache_x0 + (len(all_tokens) - 1) * (box_w + gap) + cache_box_w
    loop_start_y = new_cache_y + cache_box_h / 2
    margin_x = W - 40
    decode_mid_y = decode_y + decode_h / 2
    decode_right_x = decode_x + decode_w
    loop_path = (
        f"M {loop_start_x},{loop_start_y} "
        f"L {margin_x},{loop_start_y} "
        f"L {margin_x},{decode_mid_y} "
        f"L {decode_right_x},{decode_mid_y}"
    )
    canvas.add_raw(
        f'<path d="{loop_path}" fill="none" stroke="{gray}" stroke-width="1.5" '
        f'stroke-dasharray="2,3" marker-end="url(#{gray_marker_id})"/>'
    )

    # Canvas height is derived from the last content placed, not a fixed
    # constant — a fixed height previously let the "repeat" caption drift
    # down into the legend row once an earlier layout fix added vertical
    # space upstream (caught by visual inspection: pdftotext showed the two
    # rows' text interleaved). Deriving it here makes that class of bug
    # impossible: the legend always sits a fixed gap below whatever content
    # ends up above it.
    # Stacked (not side-by-side) so each legend line can use a legible
    # size=15 (~7.6pt at final size) without one entry's text running into
    # the next entry's swatch -- an earlier side-by-side layout could not
    # be enlarged this way without that collision.
    legend_y = loop_y + 30
    canvas.add_rect(20, legend_y, 16, 16, fill=blue)
    canvas.add_text(42, legend_y + 13, "stored (tokens / cache)", size=15)
    canvas.add_rect(20, legend_y + 28, 16, 16, fill=orange)
    canvas.add_text(42, legend_y + 28 + 13, "computation (forward pass)", size=15)
    canvas.add_rect(20, legend_y + 56, 16, 16, fill=gray)
    canvas.add_text(42, legend_y + 56 + 13, "dotted = conditional / not-always-taken flow", size=15)

    canvas.height = legend_y + 90
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
