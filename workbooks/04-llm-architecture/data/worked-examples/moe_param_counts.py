#!/usr/bin/env python3
"""Chapter 5 worked example: total vs. active parameters, routed-expert
bank vs. complete model.

This script is the source of truth for every number quoted in
chapters/05-mixture-of-experts.qmd's parameter worked example. Pure
standard library.

Toy config (deliberately simple, not a specific real model):
    E      = 8 routed experts
    k      = 2 selected experts per token
    p_e    = 100,000,000 parameters per expert
    p_s    = 100,000,000 shared-expert parameters (one always-active path)
    p_base = 1,200,000,000 non-expert parameters (attention, embeddings,
             norms, router, etc.)

Formulas (every symbol per notation.yaml):
    routed-expert-bank total  = E * p_e
    routed-expert-bank active = k * p_e
    expert-related total      = E * p_e + p_s
    expert-related active     = k * p_e + p_s
    complete-model total      = p_base + E * p_e + p_s
    complete-model active     = p_base + k * p_e + p_s

The point this script exists to demonstrate: E/k is the routed-expert-
bank's OWN total/active ratio, but it is NOT the complete model's
total/active ratio, because p_base and p_s are active either way.

Run: python3 workbooks/04-llm-architecture/data/worked-examples/moe_param_counts.py
Output: moe_param_counts.json (beside this script)
"""
import json
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "moe_param_counts.json")


def main():
    E = 8
    k = 2
    p_e = 100_000_000
    p_s = 100_000_000
    p_base = 1_200_000_000

    routed_bank_total = E * p_e
    routed_bank_active = k * p_e

    expert_related_total = E * p_e + p_s
    expert_related_active = k * p_e + p_s

    model_total = p_base + E * p_e + p_s
    model_active = p_base + k * p_e + p_s

    result = {
        "assumptions": {
            "E": E, "k": k, "p_e": p_e, "p_s": p_s, "p_base": p_base,
            "note": "Decimal (SI) billions/millions throughout -- no binary units here, since this is a parameter count, not a byte count.",
        },
        "routed_expert_bank": {
            "total": routed_bank_total,
            "active": routed_bank_active,
            "total_active_ratio": round(routed_bank_total / routed_bank_active, 6),
        },
        "expert_related": {
            "total": expert_related_total,
            "active": expert_related_active,
            "total_active_ratio": round(expert_related_total / expert_related_active, 6),
        },
        "complete_model": {
            "total": model_total,
            "active": model_active,
            "total_active_ratio": round(model_total / model_active, 6),
            "total_billions": round(model_total / 1e9, 4),
            "active_billions": round(model_active / 1e9, 4),
        },
        "e_over_k": round(E / k, 6),
        "teaching_point": "E/k (routed-expert-bank ratio) does NOT equal the complete model's total/active ratio, because p_base and p_s are active regardless of routing.",
    }
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {OUTPUT_PATH}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
