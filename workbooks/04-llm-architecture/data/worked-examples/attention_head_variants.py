#!/usr/bin/env python3
"""Chapter 3 worked example: KV-cache memory and attention projection
parameters under MHA, GQA, and MQA, for one shared base config.

This script is the source of truth for every number quoted in
chapters/03-attention-head-structure.qmd's worked examples. Pure
standard library -- this calculation needs no NumPy.

Base config (a plausible ~7B-dense-model-scale shape, not a specific
real model): L=32 layers, H_q=32 query heads, d_head=128
(so d_model = H_q * d_head = 4096), S=8192 retained tokens, B=1
sequence, bytes_per_elem=2 (bf16). MHA/GQA/MQA share every symbol
except H_kv.

Formulas (every symbol per notation.yaml):
    KV_bytes  = 2 * B * S * L * H_kv * d_head * bytes_per_elem
    P_Q       = d_model * H_q  * d_head
    P_K       = d_model * H_kv * d_head
    P_V       = d_model * H_kv * d_head
    P_O       = H_q * d_head * d_model

These are LOGICAL/theoretical minimums: they exclude allocator
overhead, page/block metadata, fragmentation, attention workspaces,
framework buffers, sharding-specific layouts, prefix-sharing effects,
and any cache quantization not reflected in bytes_per_elem. They are
not the same number a profiler or nvidia-smi would report.

Run: python3 workbooks/04-llm-architecture/data/worked-examples/attention_head_variants.py
Output: attention_head_variants.json (beside this script)
"""
import json
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "attention_head_variants.json")

MIB = 2 ** 20
GIB = 2 ** 30


def kv_cache_bytes(B: int, S: int, L: int, H_kv: int, d_head: int, bytes_per_elem: int) -> int:
    return 2 * B * S * L * H_kv * d_head * bytes_per_elem


def proj_params(d_model: int, H_q: int, H_kv: int, d_head: int) -> dict:
    p_q = d_model * H_q * d_head
    p_k = d_model * H_kv * d_head
    p_v = d_model * H_kv * d_head
    p_o = H_q * d_head * d_model
    return {
        "P_Q": p_q, "P_K": p_k, "P_V": p_v, "P_O": p_o,
        "kv_only_params_per_layer": p_k + p_v,
        "total_attn_params_per_layer": p_q + p_k + p_v + p_o,
    }


def bytes_to_units(n_bytes: int) -> dict:
    return {
        "bytes": n_bytes,
        "mib": round(n_bytes / MIB, 4),
        "gib": round(n_bytes / GIB, 4),
    }


def main():
    L = 32
    H_q = 32
    d_head = 128
    d_model = H_q * d_head  # 4096; standard config where d_model = H_q * d_head
    S = 8192
    B = 1
    bytes_per_elem = 2  # bf16

    variants = {
        "mha": {"H_kv": 32},
        "gqa": {"H_kv": 8},
        "mqa": {"H_kv": 1},
    }

    results = {}
    for name, v in variants.items():
        H_kv = v["H_kv"]
        cache_b1 = kv_cache_bytes(B, S, L, H_kv, d_head, bytes_per_elem)
        cache_b16 = kv_cache_bytes(16, S, L, H_kv, d_head, bytes_per_elem)
        params = proj_params(d_model, H_q, H_kv, d_head)
        results[name] = {
            "H_kv": H_kv,
            "kv_cache_B1": bytes_to_units(cache_b1),
            "kv_cache_B16": bytes_to_units(cache_b16),
            **params,
        }

    mha_cache_bytes = results["mha"]["kv_cache_B1"]["bytes"]
    mha_kv_params = results["mha"]["kv_only_params_per_layer"]
    mha_total_attn_params = results["mha"]["total_attn_params_per_layer"]
    for name in variants:
        results[name]["cache_reduction_vs_mha"] = round(
            results[name]["kv_cache_B1"]["bytes"] / mha_cache_bytes, 6
        )
        results[name]["kv_param_reduction_vs_mha"] = round(
            results[name]["kv_only_params_per_layer"] / mha_kv_params, 6
        )
        results[name]["total_attn_param_reduction_vs_mha"] = round(
            results[name]["total_attn_params_per_layer"] / mha_total_attn_params, 6
        )

    output = {
        "assumptions": {
            "L": L, "H_q": H_q, "d_head": d_head, "d_model": d_model,
            "S": S, "B_base": B, "B_extension": 16, "bytes_per_elem": bytes_per_elem,
            "numeric_format": "bf16",
            "note": "H_q, d_head, and d_model are identical across all three variants; only H_kv changes.",
        },
        "variants": results,
    }
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"wrote {OUTPUT_PATH}")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
