#!/usr/bin/env python3
"""Chapter 4 worked example: sliding-window receptive field across
stacked layers.

This script is the source of truth for the receptive-field numbers
quoted in chapters/04-reducing-attention-cost.qmd. Pure standard
library.

Informal but quantitative growth rule (reused from the project's
outline.yaml, ch4 required_equations): after L stacked windowed layers
of window width W, the effective (indirect) receptive field is L * W.
This is a stacking argument, not a claim about any specific real
model's measured effective context -- real models may recover more or
less depending on exact attention-pattern and positional-encoding
details.

Run: python3 workbooks/04-llm-architecture/data/worked-examples/sliding_window_receptive_field.py
Output: sliding_window_receptive_field.json (beside this script)
"""
import json
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "sliding_window_receptive_field.json")


def effective_receptive_field(window_w: int, num_layers: int) -> int:
    return window_w * num_layers


def main():
    window_w = 4
    layer_counts = [1, 2, 3]

    results = {
        str(L): {
            "window_w": window_w,
            "num_layers": L,
            "direct_receptive_field": window_w,
            "effective_receptive_field": effective_receptive_field(window_w, L),
        }
        for L in layer_counts
    }

    # Mistral 7B reference point ([@src-25]): window=4096, reported ~8x
    # cache reduction at 32K context vs. full attention -- a real,
    # dated, model-specific data point, not recomputed here (Chapter 4
    # cites it, does not re-derive it).
    output = {
        "toy_example": results,
        "note": "L * W is a stacking argument (informal, not a proof of exact effective context); Mistral 7B's own reported window=4096 / ~8x cache reduction at 32K context (Chapter 4's citation) is a separate, real, dated data point, not derived from this toy formula.",
    }
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"wrote {OUTPUT_PATH}")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
