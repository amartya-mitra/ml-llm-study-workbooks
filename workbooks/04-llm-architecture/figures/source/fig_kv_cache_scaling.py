"""Chapter 3 figure: logical KV-cache memory, MHA vs. GQA vs. MQA.

What to notice: same base config (L=32, H_q=32, d_head=128, S=8192,
B=1, bf16), only H_kv changes -- and the logical cache size drops from
4 GiB (MHA) to 1 GiB (GQA, 4x smaller) to 128 MiB (MQA, 32x smaller).
Bar height is log2-scaled (labeled explicitly) so the smallest bar
stays visible; the byte/GiB/MiB values printed on each bar are the
actual linear numbers, not scaled.

These are LOGICAL/theoretical minimums (see notation.yaml's
formula_assumption_checklist) -- not a measured nvidia-smi/profiler
number.

Run: python3 workbooks/04-llm-architecture/figures/source/fig_kv_cache_scaling.py
Output: figures/rendered/fig-kv-cache-scaling.svg
"""
import math
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-kv-cache-scaling"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")

# Full-width (6.5in) embed, W=650 -> ~12.5 units needed for 9pt; use 14.
LABEL_SIZE = 14     # ~10.1pt at final size -- essential (bar values, axis title)
TITLE_SIZE = 16

BARS = [
    ("MHA", 32, 4294967296, "4 GiB"),
    ("GQA", 8, 1073741824, "1 GiB"),
    ("MQA", 1, 134217728, "128 MiB"),
]
BASELINE_LOG2 = 20  # 1 MiB; bars measure height above this, not from 0 bytes
PX_PER_LOG2_UNIT = 13


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    blue = colors["stored_information"]

    W = 650
    canvas = SVGCanvas(width=W, height=1, title="Logical KV-cache memory: MHA vs. GQA vs. MQA")

    canvas.add_text(20, 26, "Logical KV-cache size per sequence (L=32, H_q=32, d_head=128, S=8192, B=1, bf16)",
                     size=TITLE_SIZE, weight="bold")
    canvas.add_text(20, 46, "bar height is log2-scaled for visibility -- printed values are the actual linear byte counts",
                     size=LABEL_SIZE, color="#555555")

    base_y = 300
    bar_w = 110
    gap = 70
    x0 = 60

    max_h = (math.log2(BARS[0][2]) - BASELINE_LOG2) * PX_PER_LOG2_UNIT

    for i, (name, h_kv, n_bytes, label) in enumerate(BARS):
        h = (math.log2(n_bytes) - BASELINE_LOG2) * PX_PER_LOG2_UNIT
        x = x0 + i * (bar_w + gap)
        y = base_y - h
        canvas.add_rect(x, y, bar_w, h, fill=blue, stroke="#333333", stroke_width=1.5)
        canvas.add_text(x + bar_w / 2, y - 12, label, size=LABEL_SIZE, weight="bold", anchor="middle")
        canvas.add_text(x + bar_w / 2, base_y + 24, name, size=LABEL_SIZE, weight="bold", anchor="middle")
        canvas.add_text(x + bar_w / 2, base_y + 44, f"H_kv = {h_kv}", size=LABEL_SIZE, color="#555555", anchor="middle")

    canvas.add_arrow(x0 - 20, base_y, x0 - 20, base_y - max_h - 20, style="solid", color="#888888", stroke_width=1)
    canvas.add_text(x0 - 26, base_y - max_h - 24, "larger", size=LABEL_SIZE, color="#888888", anchor="end")

    note_y = base_y + 75
    canvas.add_text(20, note_y, "Logical minimum only -- excludes allocator overhead, page metadata, fragmentation,",
                     size=LABEL_SIZE, color="#555555")
    canvas.add_text(20, note_y + 20, "attention workspaces, and framework buffers. Not a measured GPU-memory number.",
                     size=LABEL_SIZE, color="#555555")

    canvas.height = note_y + 45
    canvas.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
