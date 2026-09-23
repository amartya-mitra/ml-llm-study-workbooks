"""Chapter 6 figure: a qualitative tradeoff map placing the three
case-study architectures on two ordinal axes, with marker shape and
color carrying two more qualitative distinctions.

What to notice: positions are ORDINAL (further left/right, further
up/down), not measured numbers -- there is no unit on either axis, and
no coordinate here is a benchmark or a measurement. Marker shape
encodes uniform-vs-hybrid layer pattern; marker color encodes
communication complexity at three qualitative levels (none/low,
present-smaller-scale, present-larger-scale), each traceable to a
documented architectural fact (whether/how many experts are routed),
not a measured runtime number.

Run: python3 workbooks/04-llm-architecture/figures/source/fig_case_study_tradeoff_map.py
Output: figures/rendered/fig-case-study-tradeoff-map.svg
"""
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-case-study-tradeoff-map"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

# Full-width (6.5in) embed, W=1000, H=620 -> 1 unit = 6.5*72/1000 = 0.468pt.
# Need ~19.2 units for a 9pt essential label.
TITLE_SIZE = 19
LABEL_SIZE = 17
SMALL_SIZE = 15
TINY_SIZE = 13


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    blue = colors["stored_information"]
    orange = colors["computation"]
    red = colors["bottleneck_or_failure"]

    W, H = 1000, 560
    canvas = SVGCanvas(width=W, height=H, title="Qualitative architecture tradeoff map")

    canvas.add_text(W / 2, 24, "Ordinal placement only -- no axis is a measured number", size=SMALL_SIZE, color="#555555", anchor="middle")

    # Plot box.
    px0, py0, pw, ph = 220, 70, 640, 380
    canvas.add_rect(px0, py0, pw, ph, fill="#fbfbfb", stroke="#999999", stroke_width=1.5, rx=8)

    # Axis labels.
    canvas.add_text(px0 - 40, py0 + ph + 5, "more full/", size=TINY_SIZE, anchor="end")
    canvas.add_text(px0 - 40, py0 + ph + 22, "growing state", size=TINY_SIZE, anchor="end")
    canvas.add_text(px0 - 40, py0 - 22, "more compressed/", size=TINY_SIZE, anchor="end")
    canvas.add_text(px0 - 40, py0 - 5, "fixed state", size=TINY_SIZE, anchor="end")
    canvas.add_text(px0, py0 + ph + 30, "mostly dense parameters", size=SMALL_SIZE, anchor="start")
    canvas.add_text(px0 + pw, py0 + ph + 30, "mostly sparse/routed parameters", size=SMALL_SIZE, anchor="end")

    canvas.add_arrow(px0, py0 + ph + 15, px0 + pw, py0 + ph + 15, color="#555555", stroke_width=1.5)
    canvas.add_arrow(px0 - 60, py0 + ph, px0 - 60, py0, color="#555555", stroke_width=1.5)

    def place(frac_x, frac_y):
        return px0 + frac_x * pw, py0 + (1 - frac_y) * ph

    # frac_x: 0=dense .. 1=sparse. frac_y: 0=full/growing .. 1=compressed/fixed.
    points = {
        "Llama 3 405B": (0.08, 0.10, "circle", blue, "no MoE all-to-all"),
        "DeepSeek-V3": (0.92, 0.35, "circle", red, "all-to-all, 256-expert scale"),
        "Jamba": (0.55, 0.85, "square", orange, "all-to-all, 16-expert scale"),
    }

    label_offsets = {
        "Llama 3 405B": (22, -18),
        "DeepSeek-V3": (-190, -18),
        "Jamba": (22, 6),
    }

    for name, (fx, fy, shape, color, comm_label) in points.items():
        x, y = place(fx, fy)
        if shape == "circle":
            canvas.add_raw(f'<circle cx="{x}" cy="{y}" r="14" fill="{color}" stroke="#222222" stroke-width="2"/>')
        else:
            canvas.add_rect(x - 13, y - 13, 26, 26, fill=color, stroke="#222222", stroke_width=2, rx=3)
        dx, dy = label_offsets[name]
        canvas.add_text(x + dx, y + dy, name, size=SMALL_SIZE, weight="bold")
        canvas.add_text(x + dx, y + dy + 18, comm_label, size=TINY_SIZE, color="#555555")

    legend_y = py0 + ph + 60
    canvas.add_raw(f'<circle cx="{28}" cy="{legend_y + 8}" r="10" fill="{blue}" stroke="#222222" stroke-width="1.5"/>')
    canvas.add_text(48, legend_y + 13, "circle = uniform layer pattern; square = hybrid layer pattern", size=SMALL_SIZE)
    canvas.add_text(28, legend_y + 40, "marker color = communication complexity (blue: none/low, orange: present, smaller-scale, red: present, larger-scale)", size=TINY_SIZE, color="#555555")

    canvas.height = legend_y + 60
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
