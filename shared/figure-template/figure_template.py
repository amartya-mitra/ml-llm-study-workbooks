"""Template for a new figure script.

Copy this file to figures/source/<figure_id>.py, rename FIGURE_ID, and
fill in the drawing calls. Run it directly to (re)generate the SVG:

    python3 figures/source/<figure_id>.py

What to notice (fill in): one sentence describing the specific thing this
figure should make visually obvious to the reader. This line should also
appear as the figure's caption in the .qmd chapter that embeds it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "figure_template"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_PATH = os.path.join(REPO_ROOT, "figures", "rendered", f"{FIGURE_ID}.svg")


def main():
    style = load_visual_style()
    colors = palette_hex(style)

    canvas = SVGCanvas(width=600, height=300, title=FIGURE_ID)
    canvas.add_rect(20, 20, 160, 60, fill=colors["stored_information"], stroke="#333333")
    canvas.add_text(100, 55, "example box", size=12, color="#ffffff", anchor="middle")
    canvas.add_arrow(180, 50, 260, 50, style="solid", color="#333333")

    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
