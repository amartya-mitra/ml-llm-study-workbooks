#!/usr/bin/env python3
"""Chapter 5 worked example: a tiny top-1 routing batch, showing load
imbalance against a nominal balanced load and a stated capacity factor.

This script is the source of truth for the routing numbers quoted in
chapters/05-mixture-of-experts.qmd. Pure standard library. Top-1
routing is used (not top-2) to keep the toy example small enough to
follow visually, per Stage 7 of the drafting task.

Toy batch: 6 tokens, E=4 experts, a deliberately skewed top-1
assignment (not derived from an actual router -- chosen by hand to
demonstrate imbalance clearly, and matching
figures/source/fig_moe_routing_parallelism.py's assignment exactly, so
the chapter's figure and its worked-example numbers describe the same
concrete example).

Capacity factor and token-dropping/overflow handling are both
IMPLEMENTATION-DEPENDENT in real systems; this script computes one
concrete instantiation (capacity_factor=1.5) to make the concept
checkable, not to claim this is how any specific real system behaves.

Run: python3 workbooks/04-llm-architecture/data/worked-examples/moe_routing_imbalance.py
Output: moe_routing_imbalance.json (beside this script)
"""
import json
import math
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "moe_routing_imbalance.json")


def main():
    num_experts = 4
    # Token index -> assigned expert (top-1), chosen by hand to be skewed.
    # Matches fig_moe_routing_parallelism.py: t1,t2,t3 -> E1 (index 0);
    # t4 -> E2 (index 1); t5 -> E3 (index 2); t6 -> E4 (index 3).
    assignments = [0, 0, 0, 1, 2, 3]
    num_tokens = len(assignments)

    counts = {e: 0 for e in range(num_experts)}
    for e in assignments:
        counts[e] += 1

    nominal_balanced_load = num_tokens / num_experts

    capacity_factor = 1.2
    capacity = math.ceil(nominal_balanced_load * capacity_factor)

    overflow = {e: max(0, counts[e] - capacity) for e in range(num_experts)}
    total_overflow_tokens = sum(overflow.values())

    result = {
        "assumptions": {
            "num_tokens": num_tokens,
            "num_experts": num_experts,
            "routing_style": "top-1",
            "assignments": assignments,
            "capacity_factor": capacity_factor,
        },
        "counts_per_expert": counts,
        "nominal_balanced_load": nominal_balanced_load,
        "capacity_per_expert": capacity,
        "overflow_per_expert": overflow,
        "total_overflow_tokens": total_overflow_tokens,
        "most_loaded_expert": max(counts, key=lambda e: counts[e]),
        "most_loaded_expert_count": max(counts.values()),
        "load_ratio_vs_nominal": {
            e: round(counts[e] / nominal_balanced_load, 4) for e in range(num_experts)
        },
        "note": "Capacity factor and overflow handling (drop vs. reroute) are implementation-dependent in real systems; this is one concrete, checkable instantiation, not a claim about any specific real serving system.",
    }
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {OUTPUT_PATH}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
