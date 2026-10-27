#!/usr/bin/env python3
"""Timestral worked examples (Modules 1, 2, 3 and 6): patch padding, the
Decoupled Horizon Forecasting attention layout, role visibility, block
rollout counts, and a parameter count checked against the documentation.

Evidence labels:
  - REPORTED (documentation): the four checkpoint configurations below are
    restated from each Hugging Face config.json, and the fp32 weight sizes
    from the repository README (as of October 2026).
  - CODE-VERIFIED: the padding rule, the mask rules, the role firewall, the
    block-by-block rollout and every parameter-shape formula are transcribed
    from the public inference code at commit
    a534bdbd244d64f3d9d743f46c7bf6fc330ed4ff. They describe what the
    released inference code does, not how the model was trained.
  - DERIVED: every count below is arithmetic on those inputs. Parameter
    counts are LOGICAL estimates from shapes, not a count of loaded weights
    (no weights were downloaded).
  - ILLUSTRATIVE: the 2,000-step context, the 4 + 3 patch mask example and
    the 2,500-step horizon are teaching choices.

Pure standard library. Run: python3 w7_timestral.py  (writes w7_timestral.json)
"""
import json
import math
import os

PINNED_COMMIT = "a534bdbd244d64f3d9d743f46c7bf6fc330ed4ff"
PATCH = 32          # config.json patch_size (all four checkpoints)
BLOCK = 32          # config.json block_size: patches decoded per block
CONTEXT_MAX = 32768  # config.json context_length
QUANTILES = [0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5,
             0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.99]

# Reported (config.json): width, MLP hidden width, heads, and the layer
# schedule as (time-only layers, time_variate layers).
CHECKPOINTS = {
    "5M": {"d": 192, "h": 512, "heads": 3, "time": 6, "time_variate": 2, "fp32_mb_doc": 21},
    "28M": {"d": 384, "h": 1024, "heads": 6, "time": 9, "time_variate": 3, "fp32_mb_doc": 111},
    "123M": {"d": 640, "h": 1712, "heads": 10, "time": 15, "time_variate": 5, "fp32_mb_doc": 490},
    "209M": {"d": 768, "h": 2048, "heads": 12, "time": 18, "time_variate": 6, "fp32_mb_doc": 837},
}


def padded_patches(t, patch=PATCH, cap=CONTEXT_MAX):
    """Keep the most recent `cap` steps, then left-pad to a multiple of the patch."""
    t = min(t, cap)
    pad = (-t) % patch
    return {"steps": t, "left_pad": pad, "patches": (t + pad) // patch}


def time_mask(n_ctx, n_dec):
    """Allowed (query -> key) pairs over [Enc ; Dec] for one block, no covariates.

    Enc -> Enc causal; Enc -> Dec never; Dec -> Enc every (valid) context
    patch; Dec -> Dec causal inside the block. 1 = may attend.
    """
    n = n_ctx + n_dec
    m = [[0] * n for _ in range(n)]
    for q in range(n):
        for k in range(n):
            if q < n_ctx:
                m[q][k] = int(k < n_ctx and k <= q)
            else:
                m[q][k] = int(k < n_ctx or (k >= n_ctx and k <= q))
    return m


ROLES = ["target", "past-only", "known-future"]


def role_may_read(query, key):
    """Variate-attention firewall: covariates never read targets; known-future
    rows read only known-future rows. Every row reads itself."""
    if query == key:
        return True
    if query != "target" and key == "target":
        return False
    if query == "known-future" and key != "known-future":
        return False
    return True


def rollout(horizon, patch=PATCH, block=BLOCK, symmetric_averaging=True):
    patches = math.ceil(horizon / patch)
    blocks = []
    left = patches
    while left > 0:
        b = min(block, left)
        blocks.append(b)
        left -= b
    produced = patches * patch
    passes = len(blocks) * (2 if symmetric_averaging else 1)
    return {"horizon": horizon, "patches": patches, "blocks": blocks, "steps_produced": produced,
            "steps_discarded": produced - horizon, "block_calls_with_symmetric_averaging": passes,
            "max_steps_per_block": block * patch}


def parameter_count(cfg, patch=PATCH, n_q=len(QUANTILES)):
    """Logical count from the module shapes in model.py / layers.py."""
    d, h = cfg["d"], cfg["h"]
    attn_count = cfg["time"] + 2 * cfg["time_variate"]
    layers = cfg["time"] + cfg["time_variate"]
    parts = {
        # ResidualBlock(2*patch, 4d, d, bias) + forecast-query vector
        "patch_embedding": (2 * patch * 4 * d + 4 * d) + (4 * d * d + d) + (2 * patch * d + d) + d,
        # per attention: fused QKV (3d^2) + output (d^2) + sigmoid gate (d^2) + its RMSNorm (d)
        "attention": attn_count * (5 * d * d + d),
        # per layer: SwiGLU (d*2h + h*d) + its RMSNorm (d)
        "mlp": layers * (3 * d * h + d),
        "final_norm": d,
        # ResidualBlock(d, 4d, patch*Q), no bias
        "quantile_head": d * 4 * d + 4 * d * patch * n_q + d * patch * n_q,
    }
    total = sum(parts.values())
    return {"parts": parts, "total": total, "layers": layers, "attention_sublayers": attn_count,
            "fp32_mb_logical": round(total * 4 / 1e6, 1)}


def main():
    pad_example = padded_patches(2000)
    pad_question = padded_patches(1000)
    full = padded_patches(CONTEXT_MAX)
    mask = time_mask(4, 3)
    visibility = {q: {k: role_may_read(q, k) for k in ROLES} for q in ROLES}
    roll = rollout(2500)
    roll_question = rollout(1500)
    params = {name: parameter_count(cfg) for name, cfg in CHECKPOINTS.items()}
    for name, cfg in CHECKPOINTS.items():
        params[name]["fp32_mb_doc"] = cfg["fp32_mb_doc"]
    result = {
        "labels": {"configs_and_sizes": "reported (documentation)", "rules": f"code-verified at {PINNED_COMMIT}",
                   "counts": "derived (logical)", "settings": "illustrative"},
        "patch": PATCH, "block": BLOCK, "context_max": CONTEXT_MAX,
        "n_quantiles": len(QUANTILES), "quantile_levels": QUANTILES,
        "padding_example": pad_example, "padding_question": pad_question, "full_context": full,
        "mask_example": {"n_ctx": 4, "n_dec": 3, "mask": mask,
                         "enc_to_dec_allowed": sum(mask[q][k] for q in range(4) for k in range(4, 7)),
                         "allowed_total": sum(map(sum, mask))},
        "role_visibility": visibility,
        "rollout_example": roll,
        "rollout_question": roll_question,
        "parameters": params,
    }
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "w7_timestral.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
