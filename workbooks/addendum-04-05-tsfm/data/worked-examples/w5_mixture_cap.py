#!/usr/bin/env python3
"""Module 5 worked example: a TOY capped-proportional allocation across
three sub-datasets, plus the leakage-timeline windows used by Figure 5.

Evidence labels:
  - ILLUSTRATIVE: sub-dataset sizes, the cap, the training budget, and the
    allocation rule itself. The rule (share proportional to
    min(size, cap)) is invented here to show why a per-sub-dataset cap
    matters. It is NOT the rule used by any named model: the sampling-cap
    formula of the Moirai pretraining archive could not be verified, so no
    source formula is attributed.
  - DERIVED: the shares and the allocated observation counts.
  - The timeline windows are an original explanatory illustration.

Pure standard library. Run: python3 w5_mixture_cap.py   (writes w5_mixture_cap.json)
"""
import json
import os

SIZES = {"dataset A": 8_000_000, "dataset B": 1_500_000, "dataset C": 500_000}  # observations (illustrative)
CAP = 2_000_000
BUDGET = 1_000_000_000  # training observations (illustrative)

# Figure 5 windows on a normalized 0..1 time axis of one series (illustrative).
TIMELINE = {
    "correct": {"train": [0.00, 0.60], "stats": [0.00, 0.60], "eval": [0.80, 1.00]},
    "leaky": {"train": [0.00, 0.90], "stats": [0.00, 1.00], "eval": [0.80, 1.00]},
}


def shares(sizes, cap=None):
    eff = {k: (min(v, cap) if cap is not None else v) for k, v in sizes.items()}
    total = sum(eff.values())
    return {k: v / total for k, v in eff.items()}


def overlap(a, b):
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0]))


def main():
    unc, cap = shares(SIZES), shares(SIZES, CAP)
    alloc = {k: round(w * BUDGET) for k, w in cap.items()}
    assert sum(alloc.values()) == BUDGET
    tl = {}
    for name, w in TIMELINE.items():
        tl[name] = {**w, "train_eval_overlap": overlap(w["train"], w["eval"]),
                    "stats_eval_overlap": overlap(w["stats"], w["eval"])}
    result = {
        "labels": {"sizes_cap_budget": "illustrative", "shares_allocation": "derived", "rule": "illustrative (invented)"},
        "sizes": SIZES, "cap": CAP, "budget": BUDGET,
        "uncapped_shares": unc, "capped_shares": cap, "allocation": alloc,
        "largest_share_uncapped": max(unc.values()), "largest_share_capped": max(cap.values()),
        "timeline": tl,
        "note": "The allocation rule is a toy; it is not a claim about any model's data pipeline.",
    }
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "w5_mixture_cap.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
