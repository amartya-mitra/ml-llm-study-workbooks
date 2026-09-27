#!/usr/bin/env python3
"""Chapter 2 worked example: target shifting and loss construction for
multi-token prediction (MTP), under both verified designs.

This script is the source of truth for every position/target number
quoted in chapters/02-multi-token-prediction.qmd's worked example.
Pure standard library.

Design 1 -- independent parallel heads (Gloeckle et al., [@src-43]):
    L_n = -sum_t sum_{i=1}^{n} log P_theta(x_{t+i} | z_t) ,  z_t from
    a SHARED trunk; each head i predicts offset t+i directly from the
    same z_t, independent of the other heads' predictions.
    (Their Eq. 1-2 and the factorization on p.1 of the paper.)

Design 2 -- sequential causal chain (DeepSeek-V3, [@src-33], Sec. 2.2):
    At depth k, the input combines the PREVIOUS depth's hidden state
    h_i^{k-1} with the embedding of the actual ground-truth token
    t_{i+k} -- so depth k's module sees teacher-forced information the
    parallel design's head k never sees. Only the transformer block
    and projection matrix differ per depth; the embedding layer and
    output head are shared across all depths AND with the main model
    (their own explicit "shared with the main model" statement).

Both designs, by default, discard every auxiliary head/module at
inference and keep only the ordinary next-token path -- this script
also records that as a structural fact, not a benchmark claim.

Run: python3 workbooks/05-llm-training/data/worked-examples/mtp_target_alignment.py
Output: mtp_target_alignment.json (beside this script)
"""
import json
import os

# A short, six-token toy sequence -- illustrative only, not from any
# source's own dataset.
TOKENS = ["The", "cat", "sat", "on", "the", "mat"]
T = len(TOKENS)  # 6
N_HEADS = 3  # predict up to 3 tokens ahead


def independent_heads_targets(tokens, n):
    """Design 1 (Gloeckle et al.): for each valid position t (1-indexed
    into `tokens`), head i (i=1..n) targets tokens[t+i-1] (0-indexed).
    A position t is valid only if t+n <= T, i.e. every head has a real
    target token to predict -- positions within n-1 of the sequence
    end are dropped, exactly as the paper's own sum over t implies."""
    total = len(tokens)
    rows = []
    for t in range(1, total - n + 1):  # 1-indexed t, t+n <= T
        targets = {f"head_{i}": tokens[t + i - 1] for i in range(1, n + 1)}
        rows.append({"position_t": t, "context_up_to": tokens[:t], "targets": targets})
    return rows


def sequential_chain_targets(tokens, depth):
    """Design 2 (DeepSeek-V3): for each valid position i and each depth
    k (1..depth), the k-th module's target is tokens[i+k-1] (0-indexed),
    and its INPUT combines depth (k-1)'s hidden state with the actual
    embedding of that same target token -- i.e. teacher forcing, unlike
    design 1 where head i sees only the shared trunk's output."""
    total = len(tokens)
    rows = []
    for i in range(1, total - depth + 1):
        depths = {}
        for k in range(1, depth + 1):
            depths[f"depth_{k}"] = {
                "input_combines": f"h_{i}^{k-1}" if k > 1 else f"main_model_hidden_state(pos={i})",
                "plus_embedding_of_target": tokens[i + k - 1],
                "predicts_target": tokens[i + k - 1],
            }
        rows.append({"position_i": i, "depths": depths})
    return rows


def main():
    design1 = independent_heads_targets(TOKENS, N_HEADS)
    design2 = sequential_chain_targets(TOKENS, N_HEADS)

    total_loss_terms_design1 = len(design1) * N_HEADS
    total_loss_terms_design2 = sum(len(row["depths"]) for row in design2)

    result = {
        "toy_sequence": TOKENS,
        "sequence_length_T": T,
        "n_heads_or_depth": N_HEADS,
        "design_1_independent_heads": {
            "source": "src-43",
            "rows": design1,
            "valid_positions_t": len(design1),
            "total_individual_loss_terms": total_loss_terms_design1,
            "note": "valid t satisfies t + n <= T; positions within n-1 of the sequence end have no complete n-token target and are excluded, per the paper's own summation over t.",
        },
        "design_2_sequential_chain": {
            "source": "src-33",
            "rows": design2,
            "valid_positions_i": len(design2),
            "total_individual_loss_terms": total_loss_terms_design2,
            "note": "each depth k's module input includes the ACTUAL embedding of its own target token (teacher forcing) combined with the previous depth's hidden state -- a structural difference from design 1, where every head sees only the shared trunk's output and nothing about the other heads' targets.",
        },
        "combined_objective_structure": {
            "design_1": "L_n = sum over valid t, sum over i=1..n of -log P(target_{t,i} | shared_trunk_output(t)) -- one flat sum, all terms weighted equally, no depth-specific weighting factor in the base formulation.",
            "design_2": "L_MTP = (lambda / D) * sum_{k=1}^{D} L_MTP^k, where each L_MTP^k averages its own depth's individual token losses, and lambda is a single scalar weighting the AVERAGED MTP loss relative to the main next-token loss.",
        },
        "inference_time_default": "Both designs discard every auxiliary head/module by default at inference, keeping only the ordinary next-token path -- this is a structural default in both papers, not a benchmark result.",
    }

    out_path = os.path.join(os.path.dirname(__file__), "mtp_target_alignment.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out_path}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
