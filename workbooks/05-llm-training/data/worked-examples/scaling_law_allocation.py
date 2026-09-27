#!/usr/bin/env python3
"""Chapter 3 worked example: compute-optimal model/data allocation
under a fixed compute budget, comparing Kaplan et al.'s fitted
exponents against Hoffmann et al.'s (Chinchilla) fitted exponents, and
checking two real production choices against a Chinchilla-optimal
estimate. This script is the source of truth for every number quoted
in chapters/03-optimization-and-scaling-laws.qmd's worked example.
Pure standard library.

Part A -- TOY fixed-compute allocation comparison.
    Both papers assume compute is estimated as C ~= 6*N*D (Kaplan et
    al.'s own definition, Sec. 1.3: "C ~= 6*N*B*S", and D = B*S, so
    C ~= 6*N*D; Hoffmann et al. use the identical approximation,
    "FLOPs(N,D) ~= 6*N*D", Sec. 3.3). Given a toy anchor (N0, D0) that
    respects this relation, and a compute multiplier m, each paper's
    fitted exponents predict a different (N, D) split for the new
    compute budget m*C0:
        Kaplan (Sec. 6, Eq. 1.7-1.8):     N ~ C^0.73,  D ~ C^0.27
        Chinchilla (Table 2, Approach 1): N ~ C^0.50,  D ~ C^0.50
    Because both exponent pairs sum to 1.0, both allocations respect
    the SAME compute constraint C = 6*N*D exactly -- this script
    verifies that mechanically rather than asserting it.
    N0 and D0 below are a DELIBERATELY CHOSEN toy anchor, not a real
    published model -- picked so the anchor does not coincide with any
    row of Hoffmann et al.'s own Table 3 (see Part B).

Part B -- REAL values quoted directly from Hoffmann et al.'s Table 3
    and their Chinchilla model itself (Sec. 4.1), used to show that the
    fitted frontier's projection for a given size and the actual model
    the paper trained are close but not identical numbers.

Part C -- REAL production deviation from a Chinchilla-optimal estimate,
    using the Smol Training Playbook's own reported SmolLM3 configuration
    (3B parameters, 11T tokens), compared against a Chinchilla-optimal
    token estimate for a 3B model obtained by interpolating Table 3's
    own tokens-per-parameter ratio (NOT re-fit from scratch -- an
    explicitly approximate interpolation of already-reported numbers).

Run: python3 workbooks/05-llm-training/data/worked-examples/scaling_law_allocation.py
Output: scaling_law_allocation.json (beside this script)
"""
import json
import os

# --------------------------------------------------------------------
# Part A: toy fixed-compute allocation comparison.
# --------------------------------------------------------------------
TOY_N0 = 5.0e8    # 500M parameters -- illustrative toy anchor, not a real model
TOY_D0 = 1.0e10   # 10B tokens -- illustrative toy anchor, not a real model
COMPUTE_MULTIPLIER = 10.0

KAPLAN_A, KAPLAN_B = 0.73, 0.27          # Kaplan et al., Eq. 1.7-1.8 / Hoffmann et al. Table 2 last row
CHINCHILLA_A, CHINCHILLA_B = 0.50, 0.50  # Hoffmann et al., Table 2, Approach 1


def flops(n, d):
    return 6.0 * n * d


def allocate(n0, d0, multiplier, a, b):
    return n0 * (multiplier ** a), d0 * (multiplier ** b)


def part_a():
    c0 = flops(TOY_N0, TOY_D0)
    n_kaplan, d_kaplan = allocate(TOY_N0, TOY_D0, COMPUTE_MULTIPLIER, KAPLAN_A, KAPLAN_B)
    n_chinchilla, d_chinchilla = allocate(TOY_N0, TOY_D0, COMPUTE_MULTIPLIER, CHINCHILLA_A, CHINCHILLA_B)
    c_kaplan = flops(n_kaplan, d_kaplan)
    c_chinchilla = flops(n_chinchilla, d_chinchilla)
    return {
        "toy_anchor": {"N0": TOY_N0, "D0": TOY_D0, "C0_flops": c0},
        "compute_multiplier": COMPUTE_MULTIPLIER,
        "kaplan": {
            "exponent_a_model": KAPLAN_A, "exponent_b_data": KAPLAN_B,
            "N_new": n_kaplan, "D_new": d_kaplan,
            "model_growth_factor": n_kaplan / TOY_N0, "data_growth_factor": d_kaplan / TOY_D0,
            "C_new_flops": c_kaplan, "C_new_over_C0": c_kaplan / c0,
        },
        "chinchilla": {
            "exponent_a_model": CHINCHILLA_A, "exponent_b_data": CHINCHILLA_B,
            "N_new": n_chinchilla, "D_new": d_chinchilla,
            "model_growth_factor": n_chinchilla / TOY_N0, "data_growth_factor": d_chinchilla / TOY_D0,
            "C_new_flops": c_chinchilla, "C_new_over_C0": c_chinchilla / c0,
        },
    }


# --------------------------------------------------------------------
# Part B: real values quoted from Hoffmann et al.
# --------------------------------------------------------------------
# Table 3 (Approach 1 projections) -- quoted directly, not recomputed.
TABLE_3_REAL = [
    {"params": 4.0e8, "tokens": 8.0e9},
    {"params": 1.0e9, "tokens": 20.2e9},
    {"params": 1.0e10, "tokens": 205.1e9},
    {"params": 6.7e10, "tokens": 1.5e12},
    {"params": 1.75e11, "tokens": 3.7e12},
    {"params": 2.8e11, "tokens": 5.9e12},
    {"params": 5.2e11, "tokens": 11.0e12},
    {"params": 1.0e12, "tokens": 21.2e12},
    {"params": 1.0e13, "tokens": 216.2e12},
]

# The Chinchilla model itself (Sec. 4.1 / Table 1 / abstract) -- the
# model actually trained, chosen as "the larger end" of a predicted
# 40-70B range, not read mechanically off the fitted frontier.
CHINCHILLA_ACTUAL = {"params": 7.0e10, "tokens": 1.4e12}
CHINCHILLA_PREDICTED_RANGE_PARAMS = (4.0e10, 7.0e10)


def part_b():
    rows = []
    for row in TABLE_3_REAL:
        ratio = row["tokens"] / row["params"]
        rows.append({**row, "tokens_per_param": ratio})
    ratios = [r["tokens_per_param"] for r in rows]
    table3_67b_row = next(r for r in rows if r["params"] == 6.7e10)
    actual_ratio = CHINCHILLA_ACTUAL["tokens"] / CHINCHILLA_ACTUAL["params"]
    return {
        "table_3_rows": rows,
        "tokens_per_param_min": min(ratios),
        "tokens_per_param_max": max(ratios),
        "table3_67B_row_predicted_tokens": table3_67b_row["tokens"],
        "chinchilla_actual": CHINCHILLA_ACTUAL,
        "chinchilla_actual_tokens_per_param": actual_ratio,
        "chinchilla_predicted_range_params": CHINCHILLA_PREDICTED_RANGE_PARAMS,
        "predicted_vs_actual_token_difference": CHINCHILLA_ACTUAL["tokens"] - table3_67b_row["tokens"],
    }


# --------------------------------------------------------------------
# Part C: real production deviation (SmolLM3, src-16).
# --------------------------------------------------------------------
SMOLLM3_PARAMS = 3.0e9
SMOLLM3_TOKENS = 11.0e12


def interpolate_ratio_for(params, table3_rows):
    """Linear interpolation (in log-log space) of Table 3's own
    tokens-per-param ratio between the two nearest bracketing rows.
    An explicit approximation of an already-approximate table -- not a
    refit -- used only to sanity-check SmolLM3's token budget against
    Table 3's own numbers, since 3B is not itself a Table 3 row."""
    import math
    sorted_rows = sorted(table3_rows, key=lambda r: r["params"])
    lower = max((r for r in sorted_rows if r["params"] <= params), key=lambda r: r["params"], default=sorted_rows[0])
    upper = min((r for r in sorted_rows if r["params"] >= params), key=lambda r: r["params"], default=sorted_rows[-1])
    if lower["params"] == upper["params"]:
        return lower["tokens"] / lower["params"]
    log_p, log_pl, log_pu = math.log10(params), math.log10(lower["params"]), math.log10(upper["params"])
    log_tl, log_tu = math.log10(lower["tokens"]), math.log10(upper["tokens"])
    frac = (log_p - log_pl) / (log_pu - log_pl)
    log_t = log_tl + frac * (log_tu - log_tl)
    interpolated_tokens = 10 ** log_t
    return interpolated_tokens / params


def part_c(table3_rows):
    ratio = interpolate_ratio_for(SMOLLM3_PARAMS, table3_rows)
    predicted_tokens = ratio * SMOLLM3_PARAMS
    overtraining_factor = SMOLLM3_TOKENS / predicted_tokens
    return {
        "smollm3_params": SMOLLM3_PARAMS,
        "smollm3_actual_tokens": SMOLLM3_TOKENS,
        "interpolated_chinchilla_optimal_tokens_per_param": ratio,
        "interpolated_chinchilla_optimal_tokens": predicted_tokens,
        "overtraining_factor_vs_interpolated_estimate": overtraining_factor,
    }


def main():
    result_a = part_a()
    result_b = part_b()
    result_c = part_c(result_b["table_3_rows"])
    result = {"part_a_toy_allocation": result_a, "part_b_real_table3_and_chinchilla": result_b, "part_c_smollm3_vs_estimate": result_c}
    out_path = os.path.join(os.path.dirname(__file__), "scaling_law_allocation.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out_path}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
