#!/usr/bin/env python3
"""Chapter 4 worked example: conventional GQA cache vs. a simplified
MLA-style latent cache, on the same base config used in Chapter 3.

This script is the source of truth for every number quoted in
chapters/04-reducing-attention-cost.qmd's worked example. Pure standard
library -- this calculation needs no NumPy.

Base config (identical to Chapter 3's worked example, for continuity):
L=32 layers, H_q=32 query heads, d_head=128 (so d_model=4096), S=8192
retained tokens, B=1 sequence, bytes_per_elem=2 (bf16).

GQA cache formula (Chapter 3): KV_bytes = 2*B*S*L*H_kv*d_head*bytes_per_elem
MLA cache formula (this chapter, per [@src-27] Section 2.1.2-2.1.4):
    M_MLA = B*S*L*(d_c + d_rope)*bytes_per_elem
DeepSeek-V2's own reported ratio ([@src-27] Table 1 and its caption):
    d_c = 4 * d_head, d_rope = 0.5 * d_head
    (their own stated consequence: MLA's cache is then equal to GQA's
    cache at 2.25 groups -- verified as a hard invariant below.)

These are LOGICAL/theoretical minimums (same exclusions as Chapter 3:
allocator overhead, page metadata, fragmentation, workspaces, framework
buffers, sharding layouts, prefix-sharing, unstated quantization).
GQA and MLA cache DIFFERENT representations (per-head K/V copies vs. a
shared joint latent) -- this script computes both so the chapter can
show a size comparison, not to claim the two numbers are otherwise
equivalent.

Run: python3 workbooks/04-llm-architecture/data/worked-examples/gqa_vs_mla_cache.py
Output: gqa_vs_mla_cache.json (beside this script)
"""
import json
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "gqa_vs_mla_cache.json")

MIB = 2 ** 20
GIB = 2 ** 30


def gqa_cache_bytes(B: int, S: int, L: int, H_kv: int, d_head: int, bytes_per_elem: int) -> int:
    return 2 * B * S * L * H_kv * d_head * bytes_per_elem


def mla_cache_bytes(B: int, S: int, L: int, d_c: int, d_rope: int, bytes_per_elem: int) -> int:
    return B * S * L * (d_c + d_rope) * bytes_per_elem


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
    d_model = H_q * d_head  # 4096, identical to Chapter 3's base config
    S = 8192
    B = 1
    bytes_per_elem = 2  # bf16

    H_kv_gqa = 8  # same GQA config Chapter 3 used

    # DeepSeek-V2's own reported ratio ([@src-27] Table 1 caption).
    d_c = 4 * d_head       # 512
    d_rope = round(0.5 * d_head)  # 64

    gqa_bytes = gqa_cache_bytes(B, S, L, H_kv_gqa, d_head, bytes_per_elem)
    mla_bytes = mla_cache_bytes(B, S, L, d_c, d_rope, bytes_per_elem)

    # MHA reference number, restated (not recomputed independently here)
    # from Chapter 3's own script, for the chapter's cross-reference only.
    mha_bytes = gqa_cache_bytes(B, S, L, H_q, d_head, bytes_per_elem)

    # DeepSeek-V2's own stated consequence ([@src-27] Table 1 caption):
    # MLA's cache should equal a GQA config with 2.25 groups, i.e.
    # (d_c + d_rope) == 2 * 2.25 * d_head.
    equivalent_gqa_groups = (d_c + d_rope) / (2 * d_head)

    output = {
        "assumptions": {
            "L": L, "H_q": H_q, "d_head": d_head, "d_model": d_model,
            "S": S, "B": B, "bytes_per_elem": bytes_per_elem,
            "numeric_format": "bf16",
            "note": "Base config identical to Chapter 3's worked example. d_c and d_rope follow DeepSeek-V2's own reported ratio (d_c = 4*d_head, d_rope = 0.5*d_head), not an invented toy.",
        },
        "gqa": {
            "H_kv": H_kv_gqa,
            "cache_per_sequence": bytes_to_units(gqa_bytes),
        },
        "mha_reference": {
            "H_kv": H_q,
            "cache_per_sequence": bytes_to_units(mha_bytes),
        },
        "mla": {
            "d_c": d_c,
            "d_rope": d_rope,
            "cache_per_sequence": bytes_to_units(mla_bytes),
            "equivalent_gqa_groups": round(equivalent_gqa_groups, 4),
        },
        "ratios": {
            "mla_vs_gqa": round(mla_bytes / gqa_bytes, 4),
            "mla_vs_mha": round(mla_bytes / mha_bytes, 4),
            "gqa_vs_mha": round(gqa_bytes / mha_bytes, 4),
        },
        "caveats": [
            "Logical/theoretical minimums only -- exclude allocator overhead, page metadata, fragmentation, attention workspaces, framework buffers.",
            "Cache compression is not the same as end-to-end latency improvement.",
            "Model quality and training behavior are outside this arithmetic.",
            "GQA and MLA cache different representations (per-head K/V copies vs. a shared joint latent) -- this ratio is a size comparison, not a claim of equivalence.",
        ],
    }
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"wrote {OUTPUT_PATH}")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
