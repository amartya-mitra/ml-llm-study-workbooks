#!/usr/bin/env python3
"""Chapter 1 worked example: token allocation across a data mixture.

This script is the source of truth for every number quoted in
chapters/01-pretraining-objectives-and-data.qmd's worked example.
Pure standard library -- this calculation needs no NumPy.

Mixing weights and total token budget (0.7 / 0.2 / 0.1, 30B tokens) are
copied directly from one disclosed 1B-parameter baseline ablation
config [@src-16] -- not invented. The per-source token allocation
(tokens_i = w_i * T) is this script's own arithmetic.

Run: python3 workbooks/05-llm-training/data/worked-examples/data_mixing_allocation.py
Output: data_mixing_allocation.json (beside this script)
"""
import json
import os

TOTAL_TOKENS = 30_000_000_000  # 30B, per the disclosed 1B-baseline ablation config [@src-16]

MIXTURE = {
    "fineweb-edu": 0.7,
    "stack-edu-python": 0.2,
    "finemath-3plus": 0.1,
}

# Second worked example (the applied exercise): a 200B-token budget
# split 75/12/10/3 across four domains, per SmolLM3's own disclosed
# stage-1 domain split [@src-16].
APPLIED_EXERCISE_TOTAL_TOKENS = 200_000_000_000  # 200B
APPLIED_EXERCISE_MIXTURE = {
    "english-web": 0.75,
    "multilingual-web": 0.12,
    "code": 0.10,
    "math": 0.03,
}


def allocate(total_tokens, mixture):
    weight_sum = sum(mixture.values())
    assert abs(weight_sum - 1.0) < 1e-9, f"mixing weights must sum to 1.0, got {weight_sum}"
    allocation = {source: int(round(weight * total_tokens)) for source, weight in mixture.items()}
    assert sum(allocation.values()) == total_tokens, "allocated tokens must sum to exactly the total budget"
    return allocation


def main():
    worked_example = allocate(TOTAL_TOKENS, MIXTURE)
    applied_exercise = allocate(APPLIED_EXERCISE_TOTAL_TOKENS, APPLIED_EXERCISE_MIXTURE)

    result = {
        "worked_example": {
            "total_tokens": TOTAL_TOKENS,
            "mixture_weights": MIXTURE,
            "tokens_per_source": worked_example,
            "sum_check": sum(worked_example.values()),
        },
        "applied_exercise": {
            "total_tokens": APPLIED_EXERCISE_TOTAL_TOKENS,
            "mixture_weights": APPLIED_EXERCISE_MIXTURE,
            "tokens_per_source": applied_exercise,
            "sum_check": sum(applied_exercise.values()),
        },
        "source": "Mixing weights and totals copied from [@src-16]'s own disclosed configs, not invented. Per-source allocation is this script's own arithmetic (tokens_i = w_i * T).",
    }

    out_path = os.path.join(os.path.dirname(__file__), "data_mixing_allocation.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out_path}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
