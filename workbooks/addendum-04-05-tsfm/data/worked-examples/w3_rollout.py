#!/usr/bin/env python3
"""Module 3 worked example: forward-pass counts for horizon-filling strategies.

Evidence labels:
  - REPORTED: the TimesFM paper's own example uses an input patch of 32, an
    output patch of 128, a 256-step context and a 256-step forecast, giving
    2 autoregressive steps (versus 8 if the output patch were also 32).
  - DERIVED: pass counts ceil(F / P_out) and the two contrasting cases.
  - ILLUSTRATIVE: the single-pass placeholder row assumes placeholder
    patches of the same length as the input patch (32); it is a counting
    device, not a statement about any named model.

Pure standard library. Run: python3 w3_rollout.py   (writes w3_rollout.json)
"""
import json
import math
import os

T_CTX, HORIZON, P_IN, P_OUT = 256, 256, 32, 128


def passes(horizon, p_out):
    return math.ceil(horizon / p_out)


def main():
    rows = [
        {"strategy": "iterative, output patch 128 (TimesFM-paper example)", "klass": "iterative", "p_out": 128,
         "forward_passes": passes(HORIZON, 128), "label": "reported example; count derived"},
        {"strategy": "iterative, output patch 32 (same as input patch)", "klass": "iterative", "p_out": 32,
         "forward_passes": passes(HORIZON, 32), "label": "derived"},
        {"strategy": "iterative, one value per pass", "klass": "iterative", "p_out": 1,
         "forward_passes": passes(HORIZON, 1), "label": "derived"},
        {"strategy": "single pass over placeholder patches", "klass": "placeholder", "p_out": None,
         "forward_passes": 1, "placeholder_patches": HORIZON // P_IN, "label": "illustrative counting device"},
        {"strategy": "direct head over the whole horizon", "klass": "direct", "p_out": HORIZON,
         "forward_passes": 1, "label": "derived"},
    ]
    result = {
        "t_ctx": T_CTX, "horizon": HORIZON, "p_in": P_IN, "p_out": P_OUT,
        "rows": rows,
        "truncation_example": {"horizon": 100, "p_out": 32, "forward_passes": passes(100, 32),
                               "generated_steps": passes(100, 32) * 32, "truncated_steps": passes(100, 32) * 32 - 100},
        "note": "Forward-pass counts are logical counts. A recurrent backbone can still be sequential inside one pass; passes are not wall-clock time.",
    }
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "w3_rollout.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
