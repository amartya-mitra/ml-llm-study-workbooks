#!/usr/bin/env python3
"""Module 4 worked example: pinball loss, MAE/MSE, categorical cross-entropy
over bins, and the illustrative predictive distribution behind Figure 4.

Evidence labels:
  - REPORTED (form): pinball loss rho_tau(z, zhat) = tau*max(z-zhat,0) +
    (1-tau)*max(zhat-z,0), as printed in the Chronos-2 and TiRex papers
    (written here with tau). Cross-entropy over bins is not distance-aware
    (the Chronos paper says so).
  - DERIVED: every loss value below, and the tau=0.5 relation (half the
    absolute error).
  - ILLUSTRATIVE: the observed value, the forecasts, the 6-bin
    probabilities, and the two-component mixture used for the figure.

Pure standard library. Run: python3 w4_losses.py   (writes w4_losses.json)
"""
import json
import math
import os
import random
from statistics import NormalDist

OBSERVED = 10.0
PINBALL_CASES = [  # (tau, forecast) -- illustrative
    (0.1, 8.0), (0.5, 11.0), (0.9, 13.0),
]
ASYMMETRY_CASES = [(0.9, 7.0), (0.9, 13.0)]  # under- vs over-forecast by 3 at tau = 0.9

N_Q_LEVELS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]  # 9 levels
HORIZON = 16
N_SAMPLES = 1000
SEED = 7
TOL_FRAC = 0.10  # empirical-vs-analytic quantile tolerance, as a fraction of that step's 10%-90% range


def pinball(tau, z, zhat):
    return tau * max(z - zhat, 0.0) + (1 - tau) * max(zhat - z, 0.0)


def mixture_params(t):
    """Illustrative per-step two-component normal mixture (weights, means, sds)."""
    centre = 20.0 + 0.6 * t
    spread = 1.0 + 0.18 * t
    return [(0.7, centre, spread), (0.3, centre + 3.0 + 0.2 * t, 1.6 * spread)]


def mix_cdf(params, x):
    return sum(w * NormalDist(m, s).cdf(x) for w, m, s in params)


def mix_ppf(params, u, lo=-50.0, hi=150.0):
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if mix_cdf(params, mid) < u:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def build_forecast():
    quantiles = [[mix_ppf(mixture_params(t), q) for q in N_Q_LEVELS] for t in range(HORIZON)]
    rng = random.Random(SEED)
    nd = NormalDist()
    phi = 0.8
    paths = []
    for _ in range(N_SAMPLES):
        z = rng.gauss(0, 1)
        path = []
        for t in range(HORIZON):
            if t > 0:
                z = phi * z + math.sqrt(1 - phi ** 2) * rng.gauss(0, 1)
            u = min(max(nd.cdf(z), 1e-6), 1 - 1e-6)
            path.append(mix_ppf(mixture_params(t), u))
        paths.append(path)
    return quantiles, paths


def empirical_quantile(vals, q):
    s = sorted(vals)
    pos = q * (len(s) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (pos - lo) * (s[hi] - s[lo])


def main():
    pin = [{"tau": tau, "forecast": zh, "observed": OBSERVED, "pinball": pinball(tau, OBSERVED, zh),
            "abs_error": abs(OBSERVED - zh), "squared_error": (OBSERVED - zh) ** 2} for tau, zh in PINBALL_CASES]
    asym = [{"tau": tau, "forecast": zh, "pinball": pinball(tau, OBSERVED, zh)} for tau, zh in ASYMMETRY_CASES]

    # Six-bin strip: target is bin 2 (0-based). Two models, same probability on the target bin.
    target_bin = 2
    near = [0.05, 0.10, 0.10, 0.70, 0.03, 0.02]   # remaining mass next to the target
    far = [0.70, 0.10, 0.10, 0.05, 0.03, 0.02]    # remaining mass far from the target
    assert abs(sum(near) - 1) < 1e-9 and abs(sum(far) - 1) < 1e-9
    ce_near, ce_far = -math.log(near[target_bin]), -math.log(far[target_bin])
    bin_distance = {"near_mass_bin": 3, "far_mass_bin": 0, "target_bin": target_bin}

    quantiles, paths = build_forecast()
    emp = [[empirical_quantile([p[t] for p in paths], q) for q in N_Q_LEVELS] for t in range(HORIZON)]
    max_dev = max(abs(a - b) / (ra[-1] - ra[0]) for ra, rb in zip(quantiles, emp) for a, b in zip(ra, rb))
    medians = [row[N_Q_LEVELS.index(0.5)] for row in quantiles]

    result = {
        "labels": {"pinball": "derived", "settings": "illustrative", "figure_distribution": "illustrative"},
        "pinball_cases": pin,
        "tau_half_equals_half_abs_error": all(
            abs(c["pinball"] - 0.5 * c["abs_error"]) < 1e-12 for c in pin if c["tau"] == 0.5),
        "asymmetry_cases": asym,
        "asymmetry_ratio_under_over": asym[0]["pinball"] / asym[1]["pinball"],
        "bins": {"near_miss": near, "far_miss": far, **bin_distance},
        "ce_near": ce_near, "ce_far": ce_far,
        "ce_equal": abs(ce_near - ce_far) < 1e-12,
        "figure": {
            "horizon": HORIZON, "n_samples": N_SAMPLES, "quantile_levels": N_Q_LEVELS,
            "tolerance_fraction_of_10_90_range": TOL_FRAC, "seed": SEED,
            "mixture_params_last_step": mixture_params(HORIZON - 1),
            "quantiles": quantiles, "empirical_quantiles": emp,
            "max_quantile_deviation_fraction": max_dev,
            "point_median": medians,
            "sample_paths_first_12": paths[:12],
            "shapes": {"point": [4, HORIZON], "quantile": [4, HORIZON, len(N_Q_LEVELS)],
                       "samples": [4, HORIZON, N_SAMPLES]},
        },
        "note": "All numbers are illustrative or derived; none is a measurement of any model.",
    }
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "w4_losses.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
