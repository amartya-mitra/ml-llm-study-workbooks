"""Module 2 figure: which positions can exchange information under three
channel designs, drawn on a variates x time grid.

What to notice: the grid's rows are variates and its columns are time
steps, so the number of sequence positions is rows x columns. Flattening
all variates into one sequence multiplies the positions that every
position can attend to; channel-independent processing keeps each row
separate. This is schematic: it shows who may attend to whom, not a
measured cost. (The output-tensor shape rule is in the worked example,
not repeated here.) Counts come from data/worked-examples/w2_shapes.py.

Run: python3 workbooks/addendum-04-05-tsfm/figures/source/fig_attention_regimes.py
Output: workbooks/addendum-04-05-tsfm/figures/rendered/fig-attention-regimes.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import SVGCanvas, WIDTH, TEXT, MUTED, colors, load_example, out_path  # noqa: E402

FIGURE_ID = "fig-attention-regimes"
HEIGHT = 262
CELL_W, CELL_H = 9.5, 16
PANEL_X = [62, 252, 442]
GRID_Y = 78


def build_model():
    w2 = load_example("w2_shapes.json")
    n_rows, n_cols = w2["n_tgt"], w2["horizon"]
    return {
        "n_rows": n_rows,
        "n_cols": n_cols,
        "row_labels": [f"variate {i + 1}" for i in range(n_rows)],
        "time_axis_label": f"{n_cols} time steps",
        "positions": n_rows * n_cols,
        "panels": [
            {"id": "independent", "title": "Channel-independent", "boxes": [[r, r] for r in range(n_rows)],
             "caption": f"{n_rows} separate sequences of {n_cols}"},
            {"id": "flattened", "title": "Flattened (any-variate)", "boxes": [[0, n_rows - 1]],
             "caption": f"one sequence of {n_rows * n_cols} positions ({n_rows} variates × {n_cols} steps)"},
            {"id": "group", "title": "Group attention", "boxes": [[r, r] for r in range(n_rows)],
             "group_bracket": [0, n_rows - 1],
             "caption": "time attention within a row; group attention across rows with the same group ID"},
        ],
    }


def draw(m):
    col = colors()
    c = SVGCanvas(WIDTH, HEIGHT, title="Three channel designs on a variates by time grid")
    c.add_text(WIDTH / 2, 18, "Who may exchange information: three channel designs (schematic)", size=13, weight="bold", color=TEXT, anchor="middle")
    for p, px in zip(m["panels"], PANEL_X):
        c.add_text(px + m["n_cols"] * CELL_W / 2, 44, p["title"], size=12, weight="bold", color=TEXT, anchor="middle")
        gx = px
        for r in range(m["n_rows"]):
            for k in range(m["n_cols"]):
                c.add_rect(gx + k * CELL_W, GRID_Y + r * CELL_H, CELL_W - 1.2, CELL_H - 2, fill="#eaf2fb", stroke=col["observed"], stroke_width=0.6, rx=1.5)
        for (r0, r1) in p["boxes"]:
            fill_edge = col["forecast"] if p["id"] != "group" else col["trainable"]
            c.add_raw(f'<g id="box-{p["id"]}-{r0}-{r1}">')
            c.add_rect(gx - 2, GRID_Y + r0 * CELL_H - 2, m["n_cols"] * CELL_W + 2, (r1 - r0 + 1) * CELL_H + 0, fill="none", stroke=fill_edge, stroke_width=2, rx=3)
            c.add_raw("</g>")
        if p.get("group_bracket"):
            r0, r1 = p["group_bracket"]
            bx = gx - 8
            c.add_rect(bx - 4, GRID_Y + r0 * CELL_H - 2, 4, (r1 - r0 + 1) * CELL_H, fill=col["flag"], stroke=col["flag"], stroke_width=0.5, rx=1)
            c.add_text(gx + m["n_cols"] * CELL_W / 2, GRID_Y + m["n_rows"] * CELL_H + 46, "group ID 0 (all four rows)", size=11, color=col["flag"], anchor="middle", weight="bold")
        # time axis label (the only place the step count appears as an axis)
        ay = GRID_Y + m["n_rows"] * CELL_H + 12
        c.add_arrow(gx, ay, gx + m["n_cols"] * CELL_W - 2, ay, color="#555555", stroke_width=1)
        c.add_text(gx + m["n_cols"] * CELL_W / 2, ay + 13, m["time_axis_label"] if p["id"] != "group" else "time steps", size=11, color=MUTED, anchor="middle")
    # row axis
    c.add_text(4, GRID_Y + m["n_rows"] * CELL_H / 2 + 4, "variates", size=11, color=MUTED, anchor="start")
    # captions (wrapped manually)
    nr, nc = m["n_rows"], m["n_cols"]
    caps = {
        "independent": [f"{nr} separate sequences of {nc};", "no information crosses rows"],
        "flattened": [f"one sequence of {m['positions']} positions", f"({nr} variates \u00d7 {nc} steps);", "every position sees all"],
        "group": ["time attention inside a row,", "alternating with group attention", "across rows sharing a group ID"],
    }
    for p, px in zip(m["panels"], PANEL_X):
        for i, line in enumerate(caps[p["id"]]):
            c.add_text(px + m["n_cols"] * CELL_W / 2, 208 + i * 14, line, size=11, color=TEXT, anchor="middle")
    return c


def main():
    m = build_model()
    draw(m).save(out_path(FIGURE_ID))
    print(f"wrote {out_path(FIGURE_ID)}")


if __name__ == "__main__":
    main()
