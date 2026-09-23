#!/usr/bin/env python3
"""Chapter 6 worked example: the two small numeric facts behind the
chapter's hypothetical, unnamed 4th-model reading exercise.

This script is deliberately NOT a large numerical calculation -- per
that day's drafting task, the exercise is about architecture-reading
judgment (what state grows, what is active vs. total, what cannot be
inferred), not another cache-size derivation. The only two numbers
this script computes (GQA group size and the routed-bank active
fraction) back the two numeric claims the chapter's answer key makes;
everything else in the answer key is a qualitative reading judgment,
recorded here as plain strings so the chapter text quotes this file's
values rather than restating hand-typed numbers.

Hypothetical config (not a real model): 32 query heads, 8 KV heads,
alternating local/global attention, 64 routed experts with top-2
routing plus 1 always-active shared expert, and recurrent layers
interleaved between attention layers.

Run: python3 workbooks/04-llm-architecture/data/worked-examples/hypothetical_architecture_reading.py
Output: hypothetical_architecture_reading.json (beside this script)
"""
import json
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "hypothetical_architecture_reading.json")


def main():
    H_q = 32
    H_kv = 8
    E_routed = 64
    k_routed = 2
    has_shared_expert = True

    assert H_q % H_kv == 0, "GQA group size must be a whole number of query heads per KV head"
    gqa_group_size = H_q // H_kv
    routed_bank_active_fraction = k_routed / E_routed

    output = {
        "assumptions": {
            "H_q": H_q,
            "H_kv": H_kv,
            "E_routed": E_routed,
            "k_routed": k_routed,
            "has_shared_expert": has_shared_expert,
            "note": "Hypothetical config, not a real model -- see Chapter 6's worked reading exercise.",
        },
        "gqa_group_size": gqa_group_size,
        "routed_bank_active_fraction": routed_bank_active_fraction,
        "reading_answers": {
            "growing_state": "The attention layers' KV-cache grows with context length (one entry per past token, per attention layer).",
            "fixed_state": "The recurrent layers' state does not grow with context length -- it stays a fixed size per layer, updated in place each token (ch. 6's Mamba reference mechanism).",
            "active_vs_total_experts": f"Only {k_routed} of {E_routed} routed experts are active per token ({routed_bank_active_fraction:.3f} of the routed bank), plus the always-active shared expert; all {E_routed} routed experts are still stored regardless of activation (ch. 5's total-vs-active distinction).",
            "communication_concern": "Expert-parallel deployment of 64 routed experts implies an all-to-all dispatch/combine step, the same architectural consequence ch. 5 and ch. 6's case studies describe for any routed-MoE model -- not a number this config alone determines.",
            "mechanisms_present": "GQA (ch. 3), alternating local/global attention (ch. 4), a routed-MoE feed-forward path with a shared expert (ch. 5), and a recurrent/state-space sequence-mixing layer (ch. 6's Mamba reference) all appear in this one hypothetical config.",
            "not_inferable_from_config_alone": "Quality, wall-clock latency, training data, training recipe, and serving cost cannot be read off this config -- architecture constrains but does not determine any of them.",
        },
    }
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"wrote {OUTPUT_PATH}")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
