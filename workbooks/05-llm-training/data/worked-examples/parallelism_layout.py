#!/usr/bin/env python3
"""Chapter 4 worked example: a multidimensional (DP x TP x PP x EP)
training layout, and its global-batch calculation. This script is the
source of truth for every number quoted in
chapters/04-distributed-parallelism.qmd's worked example.

Illustrative, toy configuration -- NOT a claim about the fastest or
most memory-efficient layout for any real model (see [@src-17]'s own
caution that none of these techniques is a "silver bullet").

Rank decomposition convention (must be fixed and stated explicitly,
since [@src-17] itself never gives one worked numeric example): axes
are nested from outermost to innermost as DP > PP > TP > EP, matching
the common convention that the data-parallel axis is the outermost/
coarsest split. For a given global rank r:

    ep_idx = r % EP
    tp_idx = (r // EP) % TP
    pp_idx = (r // (EP * TP)) % PP
    dp_idx = r // (EP * TP * PP)

    r = dp_idx*(PP*TP*EP) + pp_idx*(TP*EP) + tp_idx*EP + ep_idx

A rank's DP group = all ranks sharing (pp_idx, tp_idx, ep_idx), varying
dp_idx. Its TP group = all ranks sharing (dp_idx, pp_idx, ep_idx),
varying tp_idx. Its PP group = all ranks sharing (dp_idx, tp_idx,
ep_idx), varying pp_idx. Its EP group = all ranks sharing (dp_idx,
pp_idx, tp_idx), varying ep_idx. This is the same "process group"
concept [@src-17] describes for DP's all-reduce group, generalized to
every axis.

Global batch size formula gbs = mbs * grad_acc * dp is [@src-17]'s own
stated formula (its "Revisit global batch size" section).

Run: python3 workbooks/05-llm-training/data/worked-examples/parallelism_layout.py
Output: parallelism_layout.json (beside this script)
"""
import json
import os


class InvalidParallelismConfig(ValueError):
    pass


def validate_world_size(world_size, dp, tp, pp, ep):
    product = dp * tp * pp * ep
    if product != world_size:
        raise InvalidParallelismConfig(
            f"DP({dp}) x TP({tp}) x PP({pp}) x EP({ep}) = {product}, "
            f"which does not equal world_size ({world_size})"
        )


def validate_tp_divides_kv_heads(tp, num_kv_heads):
    """Megatron-LM/[@src-17]'s own constraint: TP degree must not exceed,
    and should evenly divide, the number of K/V heads, or attention
    heads must be split unevenly / duplicated across TP ranks."""
    if num_kv_heads % tp != 0:
        raise InvalidParallelismConfig(
            f"TP degree ({tp}) does not evenly divide num_kv_heads ({num_kv_heads})"
        )


def decode_rank(r, dp, tp, pp, ep):
    ep_idx = r % ep
    tp_idx = (r // ep) % tp
    pp_idx = (r // (ep * tp)) % pp
    dp_idx = r // (ep * tp * pp)
    return {"dp_idx": dp_idx, "pp_idx": pp_idx, "tp_idx": tp_idx, "ep_idx": ep_idx}


def encode_rank(dp_idx, pp_idx, tp_idx, ep_idx, dp, tp, pp, ep):
    return dp_idx * (pp * tp * ep) + pp_idx * (tp * ep) + tp_idx * ep + ep_idx


def group_members(coords, dp, tp, pp, ep, varying_axis):
    """All ranks sharing every coordinate except `varying_axis`."""
    members = []
    sizes = {"dp": dp, "tp": tp, "pp": pp, "ep": ep}
    for i in range(sizes[varying_axis]):
        c = dict(coords)
        c[f"{varying_axis}_idx"] = i
        members.append(encode_rank(c["dp_idx"], c["pp_idx"], c["tp_idx"], c["ep_idx"], dp, tp, pp, ep))
    return sorted(members)


def build_layout(world_size, dp, tp, pp, ep, representative_rank):
    validate_world_size(world_size, dp, tp, pp, ep)
    coords = decode_rank(representative_rank, dp, tp, pp, ep)
    devices_per_replica = world_size // dp
    num_dp_replicas = dp
    return {
        "world_size": world_size,
        "dp_degree": dp,
        "tp_degree": tp,
        "pp_degree": pp,
        "ep_degree": ep,
        "devices_per_model_replica": devices_per_replica,
        "num_dp_replicas": num_dp_replicas,
        "representative_rank": representative_rank,
        "representative_coords": coords,
        "dp_group": group_members(coords, dp, tp, pp, ep, "dp"),
        "tp_group": group_members(coords, dp, tp, pp, ep, "tp"),
        "pp_group": group_members(coords, dp, tp, pp, ep, "pp"),
        "ep_group": group_members(coords, dp, tp, pp, ep, "ep"),
    }


def global_batch_size(micro_batch_size, grad_acc_steps, dp_degree):
    """gbs = mbs * grad_acc * dp -- [@src-17]'s own formula."""
    return micro_batch_size * grad_acc_steps * dp_degree


def main():
    # --- Part A: the representative multidimensional layout ---
    WORLD_SIZE = 64
    DP, TP, PP, EP = 4, 4, 2, 2
    REPRESENTATIVE_RANK = 37
    layout = build_layout(WORLD_SIZE, DP, TP, PP, EP, REPRESENTATIVE_RANK)

    # --- Part B: global batch size for this layout ---
    MICRO_BATCH_SIZE = 2
    GRAD_ACC_STEPS = 8
    gbs = global_batch_size(MICRO_BATCH_SIZE, GRAD_ACC_STEPS, layout["dp_degree"])

    # --- Part C: invalid-configuration checks (must raise) ---
    invalid_world_size_raised = False
    try:
        validate_world_size(64, dp=3, tp=4, pp=2, ep=2)  # 3*4*2*2=48 != 64
    except InvalidParallelismConfig:
        invalid_world_size_raised = True

    valid_tp_kv_raised = False
    try:
        validate_tp_divides_kv_heads(tp=4, num_kv_heads=8)  # 8 % 4 == 0, must NOT raise
    except InvalidParallelismConfig:
        valid_tp_kv_raised = True

    invalid_tp_kv_raised = False
    try:
        validate_tp_divides_kv_heads(tp=3, num_kv_heads=8)  # 8 % 3 != 0, must raise
    except InvalidParallelismConfig:
        invalid_tp_kv_raised = True

    result = {
        "layout": layout,
        "batch": {
            "micro_batch_size": MICRO_BATCH_SIZE,
            "grad_acc_steps": GRAD_ACC_STEPS,
            "dp_degree": layout["dp_degree"],
            "global_batch_size": gbs,
        },
        "validation_checks": {
            "invalid_world_size_factorization_raised": invalid_world_size_raised,
            "valid_tp_kv_head_divisibility_did_not_raise": not valid_tp_kv_raised,
            "invalid_tp_kv_head_divisibility_raised": invalid_tp_kv_raised,
        },
    }
    out_path = os.path.join(os.path.dirname(__file__), "parallelism_layout.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out_path}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
