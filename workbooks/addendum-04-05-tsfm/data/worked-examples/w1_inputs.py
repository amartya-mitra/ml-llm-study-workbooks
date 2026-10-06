#!/usr/bin/env python3
"""Module 1 worked example: scaling, binning, patch counting and lag
tokens for one 12-value toy series.

Evidence labels (see the addendum's front matter):
  - DERIVED: arithmetic from the definitions below (mean scaling, uniform
    binning, patch-count formulas, score-matrix entry counts).
  - ILLUSTRATIVE: the series values, the 8-bin range, P=4, S_p=2, the lag
    set {1, 2, 4} and the L=512 / P=16 / S_p=8 configuration are chosen for
    teaching. They are NOT settings of any named model.
  - REPORTED (formulas only): mean scaling divides by the mean absolute
    context value [Chronos paper]; the end-padded overlapping patch count
    N_p = floor((T_ctx - P)/S_p) + 2 and the non-overlapping count
    floor(T_ctx/P) follow the patching description in the PatchTST paper.

Pure standard library. Run: python3 w1_inputs.py   (writes w1_inputs.json)
"""
import json
import math
import os

SERIES = [10, 12, 14, 13, 15, 18, 20, 19, 22, 25, 24, 28]  # illustrative
N_BINS = 8                      # illustrative (the Chronos paper uses a 4096-entry vocabulary)
BIN_LOW, BIN_HIGH = 0.0, 2.0    # illustrative range in scaled units
PATCH_LEN = 4                   # P (illustrative)
STRIDE = 2                      # S_p (illustrative)
LAGS = [1, 2, 4]                # illustrative lag indices
BIG_T, BIG_P, BIG_S = 512, 16, 8  # illustrative configuration for the arithmetic line


def mean_scale(x):
    scale = sum(abs(v) for v in x) / len(x)
    return scale, [v / scale for v in x]


def bin_id(v, n_bins=N_BINS, lo=BIN_LOW, hi=BIN_HIGH):
    width = (hi - lo) / n_bins
    return min(max(int((v - lo) // width), 0), n_bins - 1)


def bin_center(i, n_bins=N_BINS, lo=BIN_LOW, hi=BIN_HIGH):
    width = (hi - lo) / n_bins
    return lo + (i + 0.5) * width


def n_patches_padded(t_ctx, p, s):
    return (t_ctx - p) // s + 2


def n_patches_plain(t_ctx, p):
    return t_ctx // p


def patch_windows(t_ctx, p, s):
    """Index windows of the end-padded overlapping patches; indices >= t_ctx are padding."""
    n = n_patches_padded(t_ctx, p, s)
    return [list(range(k * s, k * s + p)) for k in range(n)]


def lag_tokens(t_ctx, lags):
    """1-based time indices whose lagged values are ALL available inside the series."""
    first = max(lags) + 1
    return [{"t": t, "lag_indices": [t - l for l in lags]} for t in range(first, t_ctx + 1)]


def main():
    t_ctx = len(SERIES)
    scale, scaled = mean_scale(SERIES)
    ids = [bin_id(v) for v in scaled]
    recon = [bin_center(i) * scale for i in ids]
    err = [abs(a - b) for a, b in zip(SERIES, recon)]
    windows = patch_windows(t_ctx, PATCH_LEN, STRIDE)
    result = {
        "labels": {
            "series": "illustrative", "scale": "derived", "bin_ids": "derived",
            "patch_counts": "derived", "big_config": "illustrative",
        },
        "series": SERIES,
        "t_ctx": t_ctx,
        "mean_abs_scale": scale,
        "scaled": scaled,
        "n_bins": N_BINS,
        "bin_range_scaled": [BIN_LOW, BIN_HIGH],
        "bin_ids": ids,
        "bin_center_reconstruction": recon,
        "max_abs_reconstruction_error": max(err),
        "patch_length": PATCH_LEN,
        "stride": STRIDE,
        "n_patches_padded": n_patches_padded(t_ctx, PATCH_LEN, STRIDE),
        "n_padded_positions": max(max(w) for w in windows) + 1 - t_ctx,
        "patch_windows": windows,
        "n_patches_nonoverlapping": n_patches_plain(t_ctx, PATCH_LEN),
        "lags": LAGS,
        "lag_tokens": lag_tokens(t_ctx, LAGS),
        "big_config": {
            "t_ctx": BIG_T, "patch_length": BIG_P, "stride": BIG_S,
            "n_patches_padded": n_patches_padded(BIG_T, BIG_P, BIG_S),
            "n_patches_nonoverlapping": n_patches_plain(BIG_T, BIG_P),
            "score_entries_per_head_per_layer_time_steps": BIG_T ** 2,
            "score_entries_per_head_per_layer_padded_patches": n_patches_padded(BIG_T, BIG_P, BIG_S) ** 2,
            "score_ratio": BIG_T ** 2 / n_patches_padded(BIG_T, BIG_P, BIG_S) ** 2,
            "token_ratio": BIG_T / n_patches_padded(BIG_T, BIG_P, BIG_S),
        },
        "note": "Score-matrix entry counts are logical (counted), not measured memory or runtime.",
    }
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "w1_inputs.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
