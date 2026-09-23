#!/usr/bin/env python3
"""Chapter 1 worked example: trace a tiny causal decoder over a short
token sequence.

This script IS the source of truth for every number quoted in
chapters/01-transformer-refresher.qmd's worked example. The prose
should never restate a number that doesn't come from re-running this
script. Run it and diff the JSON if you ever change a chapter number.

Toy config (deliberately tiny, not representative of a real model):
    d_model = 4, n_heads = 2, d_head = 2, n_layers = 1 (for this trace)
    prompt tokens: ["The", "cat", "sat", "on"]  (prefill, 4 positions)
    decoded token: "the"                          (1 decode step, position 5)

Uses NumPy (already available in this environment) for exact,
reproducible matrix arithmetic -- no hand arithmetic is trusted.

Run: python3 workbooks/04-llm-architecture/data/worked-examples/tiny_decoder_trace.py
Output: tiny_decoder_trace.json (beside this script)
"""
import json
import math
import os

import numpy as np

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "tiny_decoder_trace.json")

D_MODEL = 4
N_HEADS = 2
D_HEAD = D_MODEL // N_HEADS  # 2

PROMPT_TOKENS = ["The", "cat", "sat", "on"]
DECODE_TOKEN = "the"
ALL_TOKENS = PROMPT_TOKENS + [DECODE_TOKEN]

# Toy embeddings: hand-picked small 0/1 integer vectors, one per token,
# chosen only for arithmetic clarity -- not learned, not meaningful.
EMBEDDINGS = {
    "The": [1, 0, 1, 0],
    "cat": [0, 1, 0, 1],
    "sat": [1, 1, 0, 0],
    "on": [0, 0, 1, 1],
    "the": [1, 0, 0, 1],
}

# Toy projection matrices (also hand-picked 0/1 integers, fixed and
# untrained -- real models learn these). Shape (d_model, d_model).
W_Q = np.array([[1, 0, 0, 1], [0, 1, 1, 0], [1, 0, 1, 0], [0, 1, 0, 1]], dtype=float)
W_K = np.array([[0, 1, 0, 1], [1, 0, 1, 0], [0, 0, 1, 1], [1, 1, 0, 0]], dtype=float)
W_V = np.array([[1, 1, 0, 0], [0, 0, 1, 1], [1, 0, 0, 1], [0, 1, 1, 0]], dtype=float)
W_O = np.array([[1, 0, 1, 1], [0, 1, 0, 1], [1, 1, 0, 0], [0, 0, 1, 1]], dtype=float)


def split_heads(mat: np.ndarray) -> np.ndarray:
    """(seq, d_model) -> (n_heads, seq, d_head)."""
    seq = mat.shape[0]
    return mat.reshape(seq, N_HEADS, D_HEAD).transpose(1, 0, 2)


def softmax_rows(mat: np.ndarray) -> np.ndarray:
    shifted = mat - mat.max(axis=-1, keepdims=True)
    ex = np.exp(shifted)
    return ex / ex.sum(axis=-1, keepdims=True)


def causal_mask(n: int) -> np.ndarray:
    """Additive mask: 0 where allowed (j <= i), -inf where blocked (j > i)."""
    m = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if j > i:
                m[i, j] = -np.inf
    return m


def attention(q_h, k_h, v_h, mask):
    """One head's causal self-attention. q_h/k_h/v_h: (seq, d_head)."""
    scores = (q_h @ k_h.T) / math.sqrt(D_HEAD)
    scores = scores + mask
    weights = softmax_rows(scores)
    out = weights @ v_h
    return scores, weights, out


def run_prefill():
    x = np.array([EMBEDDINGS[t] for t in PROMPT_TOKENS], dtype=float)  # (4, 4)
    q = x @ W_Q
    k = x @ W_K
    v = x @ W_V
    q_heads = split_heads(q)
    k_heads = split_heads(k)
    v_heads = split_heads(v)
    mask = causal_mask(len(PROMPT_TOKENS))

    per_head = []
    head_outputs = []
    for h in range(N_HEADS):
        scores, weights, out = attention(q_heads[h], k_heads[h], v_heads[h], mask)
        per_head.append({
            "head": h,
            "scores_scaled": scores.tolist(),
            "softmax_weights": np.round(weights, 4).tolist(),
            "head_output": np.round(out, 4).tolist(),
        })
        head_outputs.append(out)

    concat = np.concatenate(head_outputs, axis=-1)  # (4, d_model)
    attn_out = concat @ W_O
    residual_after_attn = x + attn_out

    return {
        "embeddings": x.tolist(),
        "Q": q.tolist(), "K": k.tolist(), "V": v.tolist(),
        "per_head": per_head,
        "concat_heads": np.round(concat, 4).tolist(),
        "attn_sublayer_output": np.round(attn_out, 4).tolist(),
        "residual_stream_after_attn": np.round(residual_after_attn, 4).tolist(),
        "K_full": k.tolist(), "V_full": v.tolist(),  # what gets cached
    }


def run_decode_step(prefill_result):
    """Position 5 ('the') attends to its own new K/V plus the 4 cached K/V
    from prefill -- nothing from positions 1-4 is recomputed."""
    x_new = np.array(EMBEDDINGS[DECODE_TOKEN], dtype=float).reshape(1, D_MODEL)
    q_new = x_new @ W_Q
    k_new = x_new @ W_K
    v_new = x_new @ W_V

    k_cached = np.array(prefill_result["K_full"])
    v_cached = np.array(prefill_result["V_full"])
    k_all = np.concatenate([k_cached, k_new], axis=0)  # (5, d_model)
    v_all = np.concatenate([v_cached, v_new], axis=0)

    q_heads = split_heads(q_new)          # (n_heads, 1, d_head)
    k_heads = split_heads(k_all)          # (n_heads, 5, d_head)
    v_heads = split_heads(v_all)

    per_head = []
    head_outputs = []
    for h in range(N_HEADS):
        scores = (q_heads[h] @ k_heads[h].T) / math.sqrt(D_HEAD)  # (1, 5), no mask needed: query is the last position
        weights = softmax_rows(scores)
        out = weights @ v_heads[h]
        per_head.append({
            "head": h,
            "scores_scaled": np.round(scores, 4).tolist(),
            "softmax_weights": np.round(weights, 4).tolist(),
            "head_output": np.round(out, 4).tolist(),
        })
        head_outputs.append(out)

    concat = np.concatenate(head_outputs, axis=-1)
    attn_out = concat @ W_O
    residual_after_attn = x_new + attn_out

    return {
        "new_token_embedding": x_new.tolist()[0],
        "Q_new": q_new.tolist()[0], "K_new": k_new.tolist()[0], "V_new": v_new.tolist()[0],
        "cache_size_before": k_cached.shape[0],
        "cache_size_after": k_all.shape[0],
        "per_head": per_head,
        "attn_sublayer_output": np.round(attn_out, 4).tolist()[0],
        "residual_stream_after_attn": np.round(residual_after_attn, 4).tolist()[0],
    }


def main():
    prefill = run_prefill()
    decode = run_decode_step(prefill)
    result = {
        "config": {"d_model": D_MODEL, "n_heads": N_HEADS, "d_head": D_HEAD,
                    "prompt_tokens": PROMPT_TOKENS, "decode_token": DECODE_TOKEN},
        "prefill": prefill,
        "decode_step": decode,
    }
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {OUTPUT_PATH}")

    # Human-readable spot-check printed to stdout for anyone drafting prose
    # from this script's output.
    print("\n--- spot-check values for prose ---")
    print("Head 0 softmax weights, row for 'sat' (query position 3, 0-indexed 2):")
    print(prefill["per_head"][0]["softmax_weights"][2])
    print("Decode step head 0 softmax weights (query = 'the', over all 5 cached keys):")
    print(decode["per_head"][0]["softmax_weights"])
    print("Cache size before/after decode step:", decode["cache_size_before"], "->", decode["cache_size_after"])


if __name__ == "__main__":
    main()
