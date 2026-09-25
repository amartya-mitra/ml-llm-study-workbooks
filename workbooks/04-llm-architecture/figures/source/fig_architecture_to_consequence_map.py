"""Chapter 7 figure: an architecture-to-systems consequence map, drawn
as a comparison matrix (six mechanisms x five resource dimensions)
with qualitative markers only -- no fabricated numeric measurement.

What to notice: no mechanism improves every column. Each one trades a
specific resource dimension for a specific complication (MoE trades
weight memory for new cross-device communication; MLA trades cache
memory for extra reconstruction compute; looped depth trades distinct
parameter count for NOTHING on the compute or cache axes -- the
repeated block applications still cost compute, and the cache is not
automatically reduced). The looped-depth row is a systems-oriented
PREVIEW only; its full explanation is deferred to chapter 8.

Run: python3 workbooks/04-llm-architecture/figures/source/fig_architecture_to_consequence_map.py
Output: figures/rendered/fig-architecture-to-consequence-map.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-architecture-to-consequence-map"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

# Full-width (6.5in) embed, W=1080 -> 1 unit = 6.5*72/1080 = 0.4333pt.
# Need ~20.8 units for a 9pt essential label.
TITLE_SIZE = 18
LABEL_SIZE = 16
SMALL_SIZE = 15
TINY_SIZE = 14


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    blue = colors["stored_information"]

    W = 1080
    row_label_w = 210
    col_w = (W - row_label_w - 20) / 5
    header_h = 60
    row_h = 58
    n_rows = 6

    H = 40 + header_h + n_rows * row_h + 30 + 60 + 20
    canvas = SVGCanvas(width=W, height=H, title="Architecture-to-systems consequence map")

    canvas.add_text(W / 2, 24, "Qualitative markers only -- no cell is a measurement", size=SMALL_SIZE, color="#555555", anchor="middle")

    columns = ["Weight\nmemory", "Cache/state\nmemory", "Compute", "Communi-\ncation", "Impl.\ncomplexity"]
    top = 40

    # Header row.
    canvas.add_rect(10, top, row_label_w, header_h, fill="#eeeeee", stroke="#333333", stroke_width=1.2, rx=4)
    canvas.add_text(10 + row_label_w / 2, top + header_h / 2 + 5, "Mechanism", size=LABEL_SIZE, weight="bold", anchor="middle")
    for j, col in enumerate(columns):
        x = 10 + row_label_w + j * col_w
        canvas.add_rect(x, top, col_w - 4, header_h, fill="#eeeeee", stroke="#333333", stroke_width=1.2, rx=4)
        lines = col.split("\n")
        for li, line in enumerate(lines):
            canvas.add_text(x + (col_w - 4) / 2, top + 24 + li * 18, line, size=SMALL_SIZE, weight="bold", anchor="middle")

    rows = [
        ("GQA / MQA", ["same", "lower", "~same", "none new", "low"]),
        ("MLA", ["similar", "much lower", "higher", "none new", "higher"]),
        ("Sliding / local attn.", ["same", "bounded", "lower", "none new", "moderate"]),
        ("MoE", ["much higher", "same", "lower (active)", "new (all-to-all)", "higher"]),
        ("Hybrid recurrent layers", ["same/lower", "much lower", "~comparable", "none new", "higher"]),
        ("Looped depth (preview -- ch. 8)", ["lower", "not auto-reduced", "NOT reduced", "none new", "preview only"]),
    ]

    y = top + header_h
    for i, (name, cells) in enumerate(rows):
        row_fill = "#f7f7f7" if i % 2 == 0 else "#ffffff"
        canvas.add_rect(10, y, row_label_w, row_h, fill=row_fill, stroke="#333333", stroke_width=1, rx=3)
        # Wrap the row label across up to two lines by splitting on spaces if long.
        words = name.split(" ")
        line1, line2 = name, ""
        if len(name) > 22:
            mid = len(words) // 2
            line1 = " ".join(words[:mid])
            line2 = " ".join(words[mid:])
        if line2:
            canvas.add_text(10 + row_label_w / 2, y + row_h / 2 - 6, line1, size=TINY_SIZE, weight="bold", anchor="middle")
            canvas.add_text(10 + row_label_w / 2, y + row_h / 2 + 14, line2, size=TINY_SIZE, weight="bold", anchor="middle")
        else:
            canvas.add_text(10 + row_label_w / 2, y + row_h / 2 + 5, line1, size=TINY_SIZE, weight="bold", anchor="middle")

        for j, cell in enumerate(cells):
            x = 10 + row_label_w + j * col_w
            canvas.add_rect(x, y, col_w - 4, row_h, fill=row_fill, stroke="#333333", stroke_width=1, rx=3)
            canvas.add_text(x + (col_w - 4) / 2, y + row_h / 2 + 5, cell, size=TINY_SIZE, anchor="middle")
        y += row_h

    note_y = y + 25
    canvas.add_text(10, note_y, "Looped depth's row previews only -- see chapter 8 for the full mechanism.", size=SMALL_SIZE, color="#555555")
    canvas.add_text(10, note_y + 22, "MTP/speculative decoding are cross-referenced in the text, not shown as a row here (not a main architecture change).", size=SMALL_SIZE, color="#555555")

    canvas.height = note_y + 45
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
