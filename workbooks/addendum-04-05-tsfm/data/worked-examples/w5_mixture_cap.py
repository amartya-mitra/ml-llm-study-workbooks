#!/usr/bin/env python3
"""Module 5 worked example: a capped sub-dataset sampling rule applied to
three TOY sub-datasets, plus the leakage-timeline windows used by Figure 5.

Evidence labels:
  - REPORTED (rule form): the original Moirai paper samples a sub-dataset
    first and, instead of sampling proportionally to size, caps each
    sub-dataset's proportional weight and renormalizes:
        omega_k = min(|D_k| / sum_i |D_i|, epsilon),
        p(D_k)  = omega_k / sum_i omega_i,
    with |D_k| the number of observations in sub-dataset k and, in the
    paper, epsilon = 0.001 (data-distribution paragraph of its
    pre-training section).
  - ILLUSTRATIVE: the three sub-dataset sizes, the epsilon used here (0.4,
    chosen so that the cap binds with only three sub-datasets; the paper's
    0.001 would equalize every weight of a three-dataset toy), and the
    training budget. None of these values comes from the paper.
  - DERIVED: the shares and the allocated observation counts.
  - The timeline windows are an original explanatory illustration.

Pure standard library. Run: python3 w5_mixture_cap.py   (writes w5_mixture_cap.json)
"""
import json
import os

SIZES = {"dataset A": 8_000_000, "dataset B": 1_500_000, "dataset C": 500_000}  # observations (illustrative)
EPSILON = 0.4            # illustrative cap on the proportional weight (the paper's value is 0.001)
PAPER_EPSILON = 0.001    # reported by the original Moirai paper
BUDGET = 1_000_000_000   # training observations (illustrative)

# Figure 5 windows on a normalized 0..1 time axis of one series (illustrative).
TIMELINE = {
    "correct": {"train": [0.00, 0.60], "stats": [0.00, 0.60], "eval": [0.80, 1.00]},
    "leaky": {"train": [0.00, 0.90], "stats": [0.00, 1.00], "eval": [0.80, 1.00]},
}


def proportional_shares(sizes):
    total = sum(sizes.values())
    return {k: v / total for k, v in sizes.items()}


def capped_shares(sizes, epsilon):
    """omega_k = min(proportional share, epsilon); then renormalize."""
    prop = proportional_shares(sizes)
    omega = {k: min(w, epsilon) for k, w in prop.items()}
    total = sum(omega.values())
    return omega, {k: w / total for k, w in omega.items()}


def overlap(a, b):
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0]))


def main():
    prop = proportional_shares(SIZES)
    omega, capped = capped_shares(SIZES, EPSILON)
    alloc = {k: round(w * BUDGET) for k, w in capped.items()}
    assert sum(alloc.values()) == BUDGET
    tl = {}
    for name, w in TIMELINE.items():
        tl[name] = {**w, "train_eval_overlap": overlap(w["train"], w["eval"]),
                    "stats_eval_overlap": overlap(w["stats"], w["eval"])}
    result = {
        "labels": {"sizes_epsilon_budget": "illustrative", "shares_allocation": "derived",
                   "rule_form": "reported (original Moirai paper); epsilon here is illustrative"},
        "paper_epsilon": PAPER_EPSILON,
        "sizes": SIZES, "epsilon": EPSILON, "budget": BUDGET,
        "proportional_shares": prop, "capped_weights_omega": omega,
        "capped_shares": capped, "allocation": alloc,
        "largest_share_proportional": max(prop.values()), "largest_share_capped": max(capped.values()),
        "timeline": tl,
        "note": "The rule's form follows the original Moirai paper; every number here is illustrative or derived.",
    }
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "w5_mixture_cap.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
