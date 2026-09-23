"""Chapter 2 figure: RoPE rotation intuition.

What to notice: in both panels the key vector is rotated exactly one
position-step further than the query vector. Even though the panels use
different absolute positions, the ANGLE BETWEEN the two rotated vectors
is identical in both -- that invariant angle, not the absolute
positions, is what the attention dot product ends up depending on.

Simplified model: real RoPE rotates many 2D subspaces of the head
dimension at different frequencies at once; this figure shows a single
2D subspace at one frequency to make the geometry checkable by eye.

Run: python3 figures/source/fig_rope_rotation.py
Output: figures/rendered/fig-rope-rotation.svg
"""
import math
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-rope-rotation"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

THETA_DEG = 25  # one position-step of rotation, in degrees, for this illustration only


def draw_panel(canvas, cx, cy, r, q_pos, k_pos, colors, label):
    canvas.add_raw(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#dddddd" stroke-width="1"/>')
    canvas.add_raw(f'<line x1="{cx-r-10}" y1="{cy}" x2="{cx+r+10}" y2="{cy}" stroke="#eeeeee" stroke-width="1"/>')
    canvas.add_raw(f'<line x1="{cx}" y1="{cy-r-10}" x2="{cx}" y2="{cy+r+10}" stroke="#eeeeee" stroke-width="1"/>')

    q_angle = -q_pos * THETA_DEG
    k_angle = -k_pos * THETA_DEG
    qx = cx + r * math.cos(math.radians(q_angle))
    qy = cy + r * math.sin(math.radians(q_angle))
    kx = cx + r * math.cos(math.radians(k_angle))
    ky = cy + r * math.sin(math.radians(k_angle))

    blue = colors["stored_information"]
    orange = colors["computation"]
    canvas.add_arrow(cx, cy, qx, qy, style="solid", color=blue, stroke_width=2.5)
    canvas.add_arrow(cx, cy, kx, ky, style="solid", color=orange, stroke_width=2.5)
    canvas.add_text(qx + (8 if qx >= cx else -8), qy - 6, f"q (pos {q_pos})", size=10, color=blue,
                     anchor="start" if qx >= cx else "end")
    canvas.add_text(kx + (8 if kx >= cx else -8), ky + 14, f"k (pos {k_pos})", size=10, color=orange,
                     anchor="start" if kx >= cx else "end")

    arc_r = r * 0.4
    a0, a1 = min(q_angle, k_angle), max(q_angle, k_angle)
    steps = 12
    pts = []
    for s in range(steps + 1):
        a = a0 + (a1 - a0) * s / steps
        pts.append((cx + arc_r * math.cos(math.radians(a)), cy + arc_r * math.sin(math.radians(a))))
    path = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    canvas.add_raw(f'<path d="{path}" fill="none" stroke="#333333" stroke-width="1.5"/>')

    canvas.add_text(cx, cy + r + 30, label, size=11, weight="bold", anchor="middle")
    canvas.add_text(cx, cy + r + 46, f"relative offset = {abs(q_pos - k_pos)} position(s)", size=9, color="#555555", anchor="middle")


def main():
    style = load_visual_style()
    colors = palette_hex(style)

    W = 700
    canvas = SVGCanvas(width=W, height=1, title="RoPE: relative angle is invariant to absolute position")

    canvas.add_text(20, 30, "Same relative offset, different absolute positions -> same angle between q and k", size=12, weight="bold")

    r = 90
    draw_panel(canvas, 190, 170, r, q_pos=1, k_pos=0, colors=colors, label="positions (1, 0)")
    draw_panel(canvas, 510, 170, r, q_pos=3, k_pos=2, colors=colors, label="positions (3, 2)")

    legend_y = 170 + r + 75
    canvas.add_text(20, legend_y, "Both panels: the angle traced between q and k is identical, because each vector", size=10, color="#555555")
    canvas.add_text(20, legend_y + 15, "is rotated by its OWN position, so only the difference in position survives.", size=10, color="#555555")
    canvas.add_text(20, legend_y + 38, "Simplified model: real RoPE rotates several 2D subspaces at different frequencies", size=9, color="#888888")
    canvas.add_text(20, legend_y + 52, "at once; this figure shows one subspace at one frequency to keep the geometry checkable by eye.", size=9, color="#888888")

    canvas.height = legend_y + 75
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
