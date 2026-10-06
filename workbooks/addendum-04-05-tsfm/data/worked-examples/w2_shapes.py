#!/usr/bin/env python3
"""Module 2 worked example: output-tensor shapes, attention score-entry
counts for independent versus flattened channels, and group-ID layouts.

Evidence labels:
  - DERIVED: all shape products and score-entry counts below.
  - ILLUSTRATIVE: n_tgt=4, F=16, n_q=9, n_samples=1000, the series counts in
    the group-ID layouts. (Chronos-2 uses 21 quantile levels; TiRex,
    Moirai 2.0 and the TimesFM documentation use 9; 9 is used here only
    because it is a common documented choice.)
  - REPORTED (qualitative): group IDs define univariate, multivariate and
    covariate-informed tasks in the Chronos-2 report; flattening all
    variates into one sequence is the Moirai (original) design.

Pure standard library. Run: python3 w2_shapes.py   (writes w2_shapes.json)
"""
import json
import os

N_TGT, HORIZON, N_Q, N_SAMPLES = 4, 16, 9, 1000


def group_layouts():
    """Illustrative group-ID assignments (one ID per series/row)."""
    return {
        "independent_series": {"rows": ["target A", "target B", "target C"], "group_ids": [0, 1, 2]},
        "multivariate": {"rows": ["target A", "target B", "target C", "target D"], "group_ids": [0, 0, 0, 0]},
        "targets_plus_covariates": {"rows": ["target", "covariate 1", "covariate 2"], "group_ids": [0, 0, 0]},
    }


def main():
    result = {
        "labels": {"shapes": "derived", "settings": "illustrative"},
        "n_tgt": N_TGT, "horizon": HORIZON, "n_q": N_Q, "n_samples": N_SAMPLES,
        "point_values": N_TGT * HORIZON,
        "future_timestamps": HORIZON,
        "quantile_numbers": N_TGT * HORIZON * N_Q,
        "sample_numbers": N_TGT * HORIZON * N_SAMPLES,
        "covariate_extra_output_axes": 0,
        "positions_flattened": N_TGT * HORIZON,
        "score_entries_independent": N_TGT * HORIZON ** 2,
        "score_entries_flattened": (N_TGT * HORIZON) ** 2,
        "score_ratio_flattened_over_independent": ((N_TGT * HORIZON) ** 2) / (N_TGT * HORIZON ** 2),
        "group_layouts": group_layouts(),
        "reported_axis_orders": {
            "chronos_2": "horizon x targets x quantiles",
            "tirex_2": "targets x quantiles x patches x steps-per-patch",
            "timesfm_readme_example": "point (12,); quantiles (12, 9)",
        },
        "note": "Score-entry counts are logical (counted), per head per layer, for the future positions only; not measured.",
    }
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "w2_shapes.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
