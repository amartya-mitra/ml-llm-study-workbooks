"""Module 3 figure: the attention layout of one Decoupled Horizon
Forecasting (DHF) block, as implemented in Timestral's public inference
code, and the role firewall of its variate attention.

What to notice: forecast tokens are extra query tokens appended after the
context patches; they read every context patch and the earlier forecast
tokens of the same block, while no context patch ever reads a forecast
token. So the observed history is never replaced by a mask. The right
panel shows which roles may read which in variate attention: covariates
never read targets, and known-future rows read only known-future rows.
Both grids are generated from data/worked-examples/w7_timestral.py, which
transcribes the rules from the pinned inference code. It shows inference
code, not the (unreleased) training code.

Run: python3 workbooks/addendum-04-05-tsfm/figures/source/fig_dhf_layout.py
Output: workbooks/addendum-04-05-tsfm/figures/rendered/fig-dhf-layout.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import SVGCanvas, WIDTH, TEXT, MUTED, colors, load_example, out_path  # noqa: E402

FIGURE_ID = "fig-dhf-layout"
HEIGHT = 312
CELL = 22
LEFT_X, LEFT_Y = 120, 78
RIGHT_X, RIGHT_Y = 410, 86
RCELL = 56
ROLE_SHORT = {"target": "target", "past-only": "past-only", "known-future": "known-fut."}


def build_model():
    w7 = load_example("w7_timestral.json")
    mx = w7["mask_example"]
    n_ctx, n_dec = mx["n_ctx"], mx["n_dec"]
    labels = [f"c{i + 1}" for i in range(n_ctx)] + [f"f{i + 1}" for i in range(n_dec)]
    roles = list(w7["role_visibility"])
    return {
        "n_ctx": n_ctx,
        "n_dec": n_dec,
        "labels": labels,
        "mask": mx["mask"],
        "roles": roles,
        "visibility": [[w7["role_visibility"][q][k] for k in roles] for q in roles],
    }


def draw(m):
    col = colors()
    c = SVGCanvas(WIDTH, HEIGHT, title="Attention layout of one DHF block and the role firewall")
    c.add_text(WIDTH / 2, 18, "One DHF block: who may read whom (inference code, schematic)", size=13, weight="bold", color=TEXT, anchor="middle")

    # ---- left: time mask over [context patches ; forecast tokens] ----
    n = m["n_ctx"] + m["n_dec"]
    c.add_text(LEFT_X + n * CELL / 2, 44, "Time attention", size=12, weight="bold", color=TEXT, anchor="middle")
    c.add_text(LEFT_X + n * CELL / 2, 60, "key (read)", size=11, color=MUTED, anchor="middle")
    for k, lab in enumerate(m["labels"]):
        c.add_text(LEFT_X + k * CELL + CELL / 2, LEFT_Y - 4, lab, size=11, color=TEXT, anchor="middle")
    for q, lab in enumerate(m["labels"]):
        c.add_text(LEFT_X - 6, LEFT_Y + q * CELL + CELL / 2 + 4, lab, size=11, color=TEXT, anchor="end")
        for k in range(n):
            allowed = m["mask"][q][k] == 1
            key_is_dec = k >= m["n_ctx"]
            fill = (col["forecast"] if key_is_dec else col["observed"]) if allowed else "#f4f4f4"
            c.add_raw(f'<g id="cell-{q}-{k}" data-allowed="{int(allowed)}">')
            c.add_rect(LEFT_X + k * CELL, LEFT_Y + q * CELL, CELL - 2, CELL - 2, fill=fill, stroke="#bbbbbb", stroke_width=0.6, rx=2)
            c.add_raw("</g>")
    # divider between context and forecast tokens
    dx = LEFT_X + m["n_ctx"] * CELL - 1
    c.add_raw(f'<line x1="{dx}" y1="{LEFT_Y - 2}" x2="{dx}" y2="{LEFT_Y + n * CELL}" stroke="{TEXT}" stroke-width="1.4"/>')
    dy = LEFT_Y + m["n_ctx"] * CELL - 1
    c.add_raw(f'<line x1="{LEFT_X - 2}" y1="{dy}" x2="{LEFT_X + n * CELL}" y2="{dy}" stroke="{TEXT}" stroke-width="1.4"/>')
    c.add_text(LEFT_X - 6, LEFT_Y - 4, "query", size=11, color=MUTED, anchor="end")
    c.add_text(LEFT_X - 34, LEFT_Y + m["n_ctx"] * CELL / 2 + 4, "context", size=11, color=col["observed"], anchor="end", weight="bold")
    c.add_text(LEFT_X - 34, LEFT_Y + m["n_ctx"] * CELL + m["n_dec"] * CELL / 2 + 4, "forecast", size=11, color=col["forecast"], anchor="end", weight="bold")
    ly = LEFT_Y + n * CELL + 18
    for i, line in enumerate([
        "c = encoded context patch; f = learned forecast token",
        "no context row reads a forecast column (top right empty)",
        "forecast tokens read the valid context, themselves",
        "and earlier forecast tokens in their block",
    ]):
        c.add_text(LEFT_X - 98, ly + i * 14, line, size=11, color=TEXT, anchor="start")

    # ---- right: role firewall of variate attention ----
    r = len(m["roles"])
    c.add_text(RIGHT_X + r * RCELL / 2, 44, "Variate attention by role", size=12, weight="bold", color=TEXT, anchor="middle")
    c.add_text(RIGHT_X + r * RCELL / 2, 60, "key (read)", size=11, color=MUTED, anchor="middle")
    for k, role in enumerate(m["roles"]):
        c.add_text(RIGHT_X + k * RCELL + RCELL / 2, RIGHT_Y - 6, ROLE_SHORT[role], size=11, color=TEXT, anchor="middle")
    c.add_text(RIGHT_X - 6, RIGHT_Y - 6, "query", size=11, color=MUTED, anchor="end")
    for q, role in enumerate(m["roles"]):
        c.add_text(RIGHT_X - 6, RIGHT_Y + q * RCELL + RCELL / 2 + 4, ROLE_SHORT[role], size=11, color=TEXT, anchor="end")
        for k in range(r):
            allowed = bool(m["visibility"][q][k])
            c.add_raw(f'<g id="role-{q}-{k}" data-allowed="{int(allowed)}">')
            c.add_rect(RIGHT_X + k * RCELL, RIGHT_Y + q * RCELL, RCELL - 3, RCELL - 3,
                       fill=col["trainable"] if allowed else "#f4f4f4", stroke="#bbbbbb", stroke_width=0.6, rx=3)
            c.add_text(RIGHT_X + k * RCELL + (RCELL - 3) / 2, RIGHT_Y + q * RCELL + RCELL / 2 + 2,
                       "yes" if allowed else "no", size=11, color="#ffffff" if allowed else MUTED, anchor="middle")
            c.add_raw("</g>")
    ry = RIGHT_Y + r * RCELL + 18
    for i, line in enumerate([
        "rows of one series only;",
        "covariates never read targets;",
        "known-future rows read only known-future rows",
    ]):
        c.add_text(RIGHT_X - 60, ry + i * 14, line, size=11, color=TEXT, anchor="start")
    return c


def main():
    m = build_model()
    draw(m).save(out_path(FIGURE_ID))
    print(f"wrote {out_path(FIGURE_ID)}")


if __name__ == "__main__":
    main()
