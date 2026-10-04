"""Chapter 6 figure: the evidence-to-diagnosis pipeline for reading a
real (or, here, synthetic) pretraining run's telemetry.

Six stages, top to bottom: configuration -> training telemetry ->
derived metrics -> comparability controls -> bottleneck/failure
hypothesis -> measurement needed to confirm. This figure reads every
number it displays directly from
data/worked-examples/pretraining_run_telemetry.py's own JSON output
(specifically, the loss-spike event at the JSON's own
diagnoses.loss_spike_event.step) -- it does not hardcode or re-derive
tokens/step, the observed step-18 values, the derived throughput or
anomaly-deviation numbers, the comparability-control flags, or the two
competing diagnoses and their distinguishing measurement.

Color semantics reuse config/visual-style.yaml's existing palette
instead of inventing new ones:
    - OBSERVED values (what the log itself reports) -> "stored_information"
      (blue) -- the palette's own meaning, "stored information or state."
    - DERIVED values (computed by the worked example's script from
      observed fields) -> "computation" (orange) -- "computation."
    - ASSUMPTIONS / controls that must hold for a comparison to be valid
      -> "frozen_or_inactive" (gray) -- repurposed here as "not itself
      the thing being measured, held fixed as a background condition."
    - DIAGNOSTIC CONCLUSIONS (the competing hypotheses) -> "bottleneck_or_failure"
      (red) -- the palette's own meaning, "bottleneck, failure, or high
      cost; the thing to notice as a problem," which is exactly what a
      diagnosis names.
    - The final "measurement needed to confirm" stage reuses the same
      diagnostic red but with a DASHED border -- explicitly meaning
      "not yet measured," a distinct visual signal from the solid-border
      diagnosis boxes above it, and explained as such in the figure's
      own on-canvas caption (not left for the reader to infer).

Semantic invariant this figure must satisfy (see
tests/test_wb05_ch06_figure_invariants.py): every number and every
diagnosis/measurement string drawn must equal the corresponding value
in the worked example's own JSON output for the loss-spike event.

Run: python3 workbooks/05-llm-training/figures/source/fig_run_diagnosis_pipeline.py
Output: workbooks/05-llm-training/figures/rendered/fig-run-diagnosis-pipeline.svg
"""
import json
import os
import sys

_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "figures", "source"))
from _svg_helpers import SVGCanvas, load_visual_style, palette_hex  # noqa: E402

FIGURE_ID = "fig-run-diagnosis-pipeline"
OUTPUT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "rendered", f"{FIGURE_ID}.svg")
DATA_PATH = os.path.join(os.path.dirname(_THIS_DIR), "..", "data", "worked-examples",
                         "pretraining_run_telemetry.json")

WIDTH = 1000
BOX_X = 60
BOX_W = WIDTH - 2 * BOX_X
LINE_H = 20
BOX_PAD_TOP = 34
BOX_PAD_BOTTOM = 14
GAP = 46


def load_worked_example_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def wrap_text(text, max_width_px, font_size, avg_char_width_factor=0.56):
    """Greedy word-wrap using an approximate average character width
    (Helvetica/Arial at this font size) -- there is no real text-layout
    engine available in this environment (see figures/source/_svg_helpers.py's
    own docstring), so this is a deliberately conservative estimate.
    Raises if a single word alone cannot fit, rather than silently
    emitting a line that will overflow the box -- the exact class of bug
    Chapter 5's fig_training_step_timeline.py guarded against for
    narrow bars, applied here to wrapped paragraph text instead."""
    max_chars = max(4, int(max_width_px / (font_size * avg_char_width_factor)))
    words = text.split(" ")
    for w in words:
        if len(w) > max_chars:
            raise ValueError(f"word {w!r} alone exceeds max_chars={max_chars} at font_size={font_size}")
    lines = []
    current = ""
    for w in words:
        candidate = (current + " " + w).strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def main():
    style = load_visual_style()
    colors = palette_hex(style)
    observed_color = colors["stored_information"]
    derived_color = colors["computation"]
    assumption_color = colors["frozen_or_inactive"]
    diagnosis_color = colors["bottleneck_or_failure"]

    data = load_worked_example_data()
    event = data["diagnoses"]["loss_spike_event"]
    step = event["step"]
    by_step = {e["step"]: e for e in data["per_step_log"]}
    entry = by_step[step]
    obs = entry["observed"]
    der = entry["derived"]
    cfg = data["synthetic_run_config"]
    controls = data["comparability_controls"]
    diag_a, diag_b = event["competing_diagnoses"]
    measurement = event["distinguishing_measurement_not_logged"]

    stages = [
        {
            "title": "1. Configuration (observed / declared)",
            "color": observed_color,
            "dashed": False,
            "lines": [
                f"global_batch_size = {cfg['global_batch_size_sequences']} sequences, "
                f"seq_len = {cfg['seq_len_tokens']} tokens, devices = {cfg['device_count']}",
                f"-> tokens per optimizer step = {data['tokens_per_step']:,} "
                "(= global_batch_size x seq_len x grad_accum_steps)",
            ],
        },
        {
            "title": f"2. Training telemetry logged at step {step} (observed)",
            "color": observed_color,
            "dashed": False,
            "lines": [
                f"train_loss = {obs['train_loss']:.3f}, grad_norm = {obs['grad_norm']:.3f}, "
                f"step_time = {obs['step_time_seconds']:.3f} s, "
                f"learning_rate = {obs['learning_rate']:.2e}",
            ],
        },
        {
            "title": "3. Derived metrics (computed from the telemetry above)",
            "color": derived_color,
            "dashed": False,
            "lines": [
                f"consumed_tokens = {der['consumed_tokens']:,}, "
                f"global_throughput = {der['global_throughput_tokens_per_s']:,.0f} tok/s, "
                f"achieved/nominal FLOPs = {der['achieved_fraction_of_nominal']:.1%}",
                f"loss vs. trailing-{cfg['trailing_window_size']}-step average: "
                f"{der['loss_relative_deviation']:.1%} deviation -> "
                f"anomaly flagged = {der['loss_anomaly_flagged']}",
            ],
        },
        {
            "title": "4. Comparability controls (must hold for this comparison to be valid)",
            "color": assumption_color,
            "dashed": False,
            "lines": [
                "device count, global batch size, sequence length, and gradient-accumulation "
                f"steps unchanged within the trailing window: "
                f"{all(controls.values())} -- a within-run comparison against recent "
                "history, not a cross-run comparison.",
            ],
        },
        {
            "title": "5. Bottleneck / failure hypothesis (two diagnoses, same observed evidence)",
            "color": diagnosis_color,
            "dashed": False,
            "lines": [
                f"(A) {diag_a['name'].replace('_', ' ')}: {diag_a['description']}",
                f"(B) {diag_b['name'].replace('_', ' ')}: {diag_b['description']}",
            ],
        },
        {
            "title": "6. Measurement needed to confirm (not yet taken)",
            "color": diagnosis_color,
            "dashed": True,
            "lines": [measurement],
        },
    ]

    inner_w = BOX_W - 48
    y = 70
    box_geoms = []
    for s in stages:
        wrapped = []
        for line in s["lines"]:
            wrapped.extend(wrap_text(line, inner_w, 12.5))
        box_h = BOX_PAD_TOP + len(wrapped) * LINE_H + BOX_PAD_BOTTOM
        box_geoms.append((y, box_h, s, wrapped))
        y += box_h + GAP

    content_bottom = y - GAP
    legend_item_count = 4
    legend_top = content_bottom + 40
    total_height = legend_top + legend_item_count * 22 + 20

    c = SVGCanvas(WIDTH, total_height,
                  title="Evidence-to-diagnosis pipeline for reading a pretraining run's telemetry")

    c.add_rect(20, 15, WIDTH - 40, 36, fill="#f2f2f2", stroke="#666666", stroke_width=1.2, rx=4)
    c.add_text(WIDTH / 2, 38,
               "RUN-DIAGNOSIS PIPELINE — this chapter's own synthetic worked example, not a measured dashboard",
               size=13, weight="bold", color="#333333", anchor="middle")

    for i, (by, bh, s, wrapped) in enumerate(box_geoms):
        c.add_rect(BOX_X, by, BOX_W, bh, fill="#ffffff", stroke=s["color"], stroke_width=3,
                   rx=8, dash="dashed" if s["dashed"] else None)
        c.add_rect(BOX_X, by, 14, bh, fill=s["color"], stroke=s["color"], stroke_width=1, rx=4)
        c.add_text(BOX_X + 26, by + 22, s["title"], size=13, weight="bold", color="#111111", anchor="start")
        ty = by + BOX_PAD_TOP + LINE_H - 6
        for line in wrapped:
            c.add_text(BOX_X + 26, ty, line, size=12.5, color="#222222", anchor="start")
            ty += LINE_H
        if i < len(box_geoms) - 1:
            next_by = box_geoms[i + 1][0]
            cx = BOX_X + BOX_W / 2
            c.add_arrow(cx, by + bh + 2, cx, next_by - 4, color="#333333", stroke_width=2.5)

    legend_items = [
        (observed_color, "Observed (logged)"),
        (derived_color, "Derived (computed from observed fields)"),
        (assumption_color, "Assumption / control (must hold for the comparison to be valid)"),
        (diagnosis_color, "Diagnostic conclusion (solid border = hypothesis; dashed border = still unconfirmed)"),
    ]
    ly = legend_top + 22
    for color, label in legend_items:
        c.add_rect(BOX_X, ly - 12, 22, 14, fill=color, stroke="#333333")
        c.add_text(BOX_X + 30, ly - 1, label, size=11.5, color="#333333", anchor="start")
        ly += 22

    c.save(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
