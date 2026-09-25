#!/usr/bin/env python3
"""Chapter 8 worked example: L_distinct=22, T_passes=2 (looped, so
L_effective=44) vs. a conventional 44-distinct-block stack.

This script is the source of truth for every number quoted in
chapters/08-emerging-directions-and-synthesis.qmd's worked example.
Pure standard library.

Under a SIMPLIFIED equal-per-block-size assumption (every block has
the same parameter count p_per_block, and there is a fixed pool of
non-block parameters -- embeddings, output head, any router --
p_non_block, identical for both models being compared):

    looped block-parameter storage   = L_distinct * p_per_block
    conventional block-parameter storage = L_effective * p_per_block
    block-parameter ratio (looped/conventional) = L_distinct / L_effective = 1 / T_passes

    looped complete-model params     = p_non_block + L_distinct * p_per_block
    conventional complete-model params = p_non_block + L_effective * p_per_block

The block-parameter ratio is EXACTLY 1/T_passes (0.5 here). The
complete-model ratio is NOT exactly 0.5 -- it is always strictly
greater than the block-only ratio whenever p_non_block > 0, since the
non-block parameters add the same absolute mass to both totals. This
script verifies that inequality holds, not just asserts it.

Block applications per token are equal for both models (L_effective in
both cases) -- looping does not reduce how many times a block runs.

This is a LOGICAL parameter-count comparison, not a measured wall-clock
prediction, and not a claim about any specific real model's exact
parameter counts (p_per_block/p_non_block below are illustrative).

Run: python3 workbooks/04-llm-architecture/data/worked-examples/looped_vs_unrolled_depth.py
Output: looped_vs_unrolled_depth.json (beside this script)
"""
import json
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "looped_vs_unrolled_depth.json")


def main():
    L_distinct = 22
    T_passes = 2
    L_effective = L_distinct * T_passes

    # Conventional (unrolled) comparison stack: same effective depth,
    # every block application uses its own distinct weights.
    conventional_L_distinct = L_effective

    p_per_block = 50_000_000       # illustrative, equal-per-block-size assumption
    p_non_block = 500_000_000      # illustrative: embeddings + output head + router, shared assumption for both

    looped_block_params = L_distinct * p_per_block
    conventional_block_params = conventional_L_distinct * p_per_block
    block_param_ratio = looped_block_params / conventional_block_params

    looped_total_params = p_non_block + looped_block_params
    conventional_total_params = p_non_block + conventional_block_params
    complete_model_ratio = looped_total_params / conventional_total_params

    # Block applications per token: equal for both, by construction.
    looped_block_applications = L_effective
    conventional_block_applications = conventional_L_distinct  # every distinct block runs once

    output = {
        "assumptions": {
            "L_distinct": L_distinct,
            "T_passes": T_passes,
            "p_per_block": p_per_block,
            "p_non_block": p_non_block,
            "note": "p_per_block and p_non_block are illustrative, not a specific real model's config -- equal-per-block-size assumption.",
        },
        "L_effective": L_effective,
        "conventional_L_distinct": conventional_L_distinct,
        "block_applications": {
            "looped": looped_block_applications,
            "conventional": conventional_block_applications,
            "equal": looped_block_applications == conventional_block_applications,
        },
        "block_parameter_storage": {
            "looped": looped_block_params,
            "conventional": conventional_block_params,
            "ratio_looped_over_conventional": round(block_param_ratio, 6),
            "matches_one_over_T_passes": abs(block_param_ratio - 1 / T_passes) < 1e-9,
        },
        "complete_model_parameters": {
            "looped": looped_total_params,
            "conventional": conventional_total_params,
            "ratio_looped_over_conventional": round(complete_model_ratio, 6),
            "strictly_greater_than_block_only_ratio": complete_model_ratio > block_param_ratio,
        },
    }
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"wrote {OUTPUT_PATH}")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
