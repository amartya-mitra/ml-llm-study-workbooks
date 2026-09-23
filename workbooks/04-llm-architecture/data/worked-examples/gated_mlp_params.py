#!/usr/bin/env python3
"""Chapter 2 worked example: parameter counts for a plain MLP vs. a
gated (SwiGLU-style) MLP.

This script is the source of truth for every number quoted in
chapters/02-modern-decoder.qmd's parameter-count worked example. Pure
standard library -- this calculation needs no NumPy.

Convention (matches the workbook's notation.yaml style: state every
assumption explicitly):
    - no biases counted (matches most current open decoder implementations)
    - "plain MLP" = two weight matrices: d_model -> d_ff -> d_model
    - "gated MLP" = three weight matrices: two d_model -> d_ff projections
      (the gate and the value branch) plus one d_ff -> d_model output
      projection

Run: python3 workbooks/04-llm-architecture/data/worked-examples/gated_mlp_params.py
Output: gated_mlp_params.json (beside this script)
"""
import json
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "gated_mlp_params.json")


def plain_mlp_params(d_model: int, d_ff: int) -> int:
    w1 = d_model * d_ff
    w2 = d_ff * d_model
    return w1 + w2


def gated_mlp_params(d_model: int, d_ff: int) -> int:
    w1 = d_model * d_ff  # gate branch
    w3 = d_model * d_ff  # value branch
    w2 = d_ff * d_model  # output projection
    return w1 + w3 + w2


def main():
    d_model = 8
    d_ff_plain = 32  # a common 4x expansion ratio for a plain MLP

    plain_params = plain_mlp_params(d_model, d_ff_plain)
    gated_same_dff_params = gated_mlp_params(d_model, d_ff_plain)

    # Many real gated-MLP models shrink d_ff instead of accepting the 1.5x
    # increase -- solve for the d_ff that makes gated_mlp_params roughly
    # match plain_params at the SAME d_model, so the two designs cost
    # about the same total parameters.
    # gated_params(d_ff') = 3 * d_model * d_ff' ~= plain_params = 2 * d_model * d_ff_plain
    # => d_ff' ~= (2/3) * d_ff_plain
    d_ff_compensated = round((2 / 3) * d_ff_plain)
    gated_compensated_params = gated_mlp_params(d_model, d_ff_compensated)

    result = {
        "assumptions": {
            "d_model": d_model,
            "d_ff_plain": d_ff_plain,
            "biases_counted": False,
            "note": "d_ff_compensated is rounded to the nearest integer from (2/3) * d_ff_plain",
        },
        "plain_mlp": {
            "d_ff": d_ff_plain,
            "params": plain_params,
            "formula": "2 * d_model * d_ff",
        },
        "gated_mlp_same_d_ff": {
            "d_ff": d_ff_plain,
            "params": gated_same_dff_params,
            "formula": "3 * d_model * d_ff",
            "ratio_vs_plain": round(gated_same_dff_params / plain_params, 4),
        },
        "gated_mlp_compensated_d_ff": {
            "d_ff": d_ff_compensated,
            "params": gated_compensated_params,
            "formula": "3 * d_model * d_ff_compensated",
            "ratio_vs_plain": round(gated_compensated_params / plain_params, 4),
        },
    }
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {OUTPUT_PATH}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
