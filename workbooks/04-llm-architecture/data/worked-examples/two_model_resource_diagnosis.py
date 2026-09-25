#!/usr/bin/env python3
"""Chapter 7 worked example: the diagnosis exercise comparing Model A
(dense, GQA) against Model B (MoE + MLA), reusing ch. 3's KV-cache
formula and ch. 5's total/active-parameter formulas directly -- no new
formula is derived for this chapter, per that day's drafting task
("reuse verified formulas from earlier chapters... avoid another long
arithmetic derivation").

Both models are hypothetical (illustrative parameter/head counts, not
a real model's published config) and share the same retained context
length and concurrency, so the comparison isolates architecture, not
workload.

Model A: dense, GQA (L=32, H_q=32, H_kv=8, d_head=128), 7B params
(total = active, since it's dense).
Model B: MoE + MLA (L=32, d_c=512, d_rope=64 -- DeepSeek-V2's own
reported ratio, ch. 4 -- 64 routed experts/8 active, p_base=2B),
expert weights distributed across devices.

These are LOGICAL/theoretical minimums (same exclusions as chs. 3-5:
allocator overhead, page metadata, fragmentation, framework buffers) --
not measured GPU memory, and not a latency prediction. See chapter 7's
own text for why latency cannot be concluded from these numbers alone.

Run: python3 workbooks/04-llm-architecture/data/worked-examples/two_model_resource_diagnosis.py
Output: two_model_resource_diagnosis.json (beside this script)
"""
import json
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "two_model_resource_diagnosis.json")

MIB = 2 ** 20
GIB = 2 ** 30


def gqa_cache_bytes(B: int, S: int, L: int, H_kv: int, d_head: int, bytes_per_elem: int) -> int:
    """ch. 3's formula, reused verbatim."""
    return 2 * B * S * L * H_kv * d_head * bytes_per_elem


def mla_cache_bytes(B: int, S: int, L: int, d_c: int, d_rope: int, bytes_per_elem: int) -> int:
    """ch. 4's formula, reused verbatim."""
    return B * S * L * (d_c + d_rope) * bytes_per_elem


def moe_params(p_base: int, E: int, k: int, p_e: int) -> dict:
    """ch. 5's formula, reused verbatim (no shared expert in this example)."""
    return {
        "total": p_base + E * p_e,
        "active": p_base + k * p_e,
    }


def bytes_to_units(n_bytes: int) -> dict:
    return {"bytes": n_bytes, "mib": round(n_bytes / MIB, 4), "gib": round(n_bytes / GIB, 4)}


def main():
    # Shared workload: same retained context and concurrency for both models.
    S = 32768
    concurrency = 64
    bytes_per_elem = 2  # bf16

    # Model A: dense, GQA.
    L_a, H_kv_a, d_head_a = 32, 8, 128
    a_params_total = 7_000_000_000
    a_params_active = a_params_total  # dense: total == active
    a_cache_per_seq = gqa_cache_bytes(1, S, L_a, H_kv_a, d_head_a, bytes_per_elem)
    a_cache_all_seqs = a_cache_per_seq * concurrency

    # Model B: MoE + MLA, expert weights distributed across devices.
    L_b, d_c, d_rope = 32, 512, 64  # d_c = 4*d_head, d_rope = 0.5*d_head, per DeepSeek-V2 (ch. 4)
    E, k, p_e, p_base_b = 64, 8, 100_000_000, 2_000_000_000
    b_params = moe_params(p_base_b, E, k, p_e)
    b_cache_per_seq = mla_cache_bytes(1, S, L_b, d_c, d_rope, bytes_per_elem)
    b_cache_all_seqs = b_cache_per_seq * concurrency

    output = {
        "assumptions": {
            "shared_workload": {"S": S, "concurrency": concurrency, "bytes_per_elem": bytes_per_elem},
            "model_a": {"L": L_a, "H_kv": H_kv_a, "d_head": d_head_a, "params_total": a_params_total},
            "model_b": {"L": L_b, "d_c": d_c, "d_rope": d_rope, "E": E, "k": k, "p_e": p_e, "p_base": p_base_b},
        },
        "model_a": {
            "params_total": a_params_total,
            "params_active": a_params_active,
            "cache_per_sequence": bytes_to_units(a_cache_per_seq),
            "cache_all_sequences": bytes_to_units(a_cache_all_seqs),
            "cross_device_communication": "none (no routed experts to distribute)",
        },
        "model_b": {
            "params_total": b_params["total"],
            "params_active": b_params["active"],
            "cache_per_sequence": bytes_to_units(b_cache_per_seq),
            "cache_all_sequences": bytes_to_units(b_cache_all_seqs),
            "cross_device_communication": "all-to-all dispatch/combine (expert-parallel routed experts, ch. 5)",
        },
        "comparison": {
            "lower_logical_cache": "model_b" if b_cache_per_seq < a_cache_per_seq else "model_a",
            "cache_ratio_b_over_a": round(b_cache_per_seq / a_cache_per_seq, 6),
            "higher_total_weight_storage": "model_b" if b_params["total"] > a_params_total else "model_a",
            "total_params_ratio_b_over_a": round(b_params["total"] / a_params_total, 6),
            "introduces_expert_communication": "model_b",
            "latency_conclusion": "Neither model's latency can be concluded from these logical quantities alone -- batching, kernel implementation, hardware, and the actual routing distribution at serving time all still need to be benchmarked (see ch. 7's own text).",
        },
    }
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"wrote {OUTPUT_PATH}")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
