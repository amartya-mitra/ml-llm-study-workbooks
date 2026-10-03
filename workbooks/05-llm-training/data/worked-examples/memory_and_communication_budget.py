#!/usr/bin/env python3
"""Chapter 5 worked example: model-state memory before/after sharding,
one activation-memory estimate, one collective's communication
payload/time, exposed communication after a declared overlap
fraction, and the resulting illustrative step-time impact.

This script is the source of truth for every number quoted in
chapters/05-training-memory-and-communication.qmd's worked example,
and for figures/source/fig_training_step_timeline.py and
fig_memory_ledger_dp_vs_sharded.py, which both read this script's own
JSON output rather than re-deriving or duplicating any number.

Every quantity below is one of exactly two kinds, and each is labeled
as such in its own dict key:
    - "sourced_*"   : a formula or constant taken directly from a
                       verified source ([@src-17], [@src-52], [@src-54]),
                       cited in this docstring and in the chapter prose.
    - toy/illustrative inputs (TOY_* constants below) : deliberately
                       chosen numbers for this worked example, NOT a
                       claim about any real model, cluster, or
                       measured run.
Anything computed FROM a toy input using a sourced formula is a
"computed_by_script" estimate, not a measurement -- see the chapter's
own "logical/estimated vs measured" distinction.

Sourced formulas used (re-verified by full-text extraction this
session, not from the registry summary):
    - Parameter count: N = h*v + L*(12*h^2 + 13*h) + 2*h  [@src-17]
    - Mixed-precision (BF16 compute, FP32 master weights + Adam
      moments, no FP32 grad accumulation) model-state memory:
      m_params=2N, m_grad=2N, m_params_fp32=4N, m_opt=8N bytes;
      total 16N bytes replicated per rank under vanilla DP  [@src-17]
    - ZeRO-3/FSDP shards all four of the above across the DP group:
      total model-state memory becomes 16N/DP bytes per rank; ZeRO's
      own notation calls the combined master-weight+optimizer term
      "k*Psi" with k=12 for mixed-precision Adam (4N+8N=12N here)
      [@src-54;@src-17]
    - Activation memory (mixed precision):
      m_act = L*seq*bs*h*(34 + 5*n_heads*seq/h) bytes  [@src-17]
    - ZeRO-3 per-transformer-block forward-pass parameter all-gather:
      16*h^2 elements total, 16*h^2/DP elements/rank  [@src-17]
    - Communication volume of one all-gather equals its message size
      (one "Psi" of data moved per the collective's own definition)
      [@src-54]

Run: python3 workbooks/05-llm-training/data/worked-examples/memory_and_communication_budget.py
Output: memory_and_communication_budget.json (beside this script)
"""
import json
import os


class InvalidTrainingConfig(ValueError):
    pass


BYTES_PER_ELEM_BF16 = 2
BYTES_PER_ELEM_FP32 = 4


def parameter_count(h, v, L):
    """N = h*v + L*(12*h^2 + 13*h) + 2*h -- [@src-17]'s own formula,
    excluding fixed positional embeddings."""
    return h * v + L * (12 * h ** 2 + 13 * h) + 2 * h


def model_state_memory_bytes(N):
    """16N bytes total: 2N (bf16 params) + 2N (bf16 grad) + 4N (fp32
    master weights) + 8N (fp32 Adam momentum+variance) -- [@src-17]."""
    m_params = 2 * N
    m_grad = 2 * N
    m_params_fp32 = 4 * N
    m_opt = 8 * N
    return {
        "m_params_bf16": m_params,
        "m_grad_bf16": m_grad,
        "m_params_fp32_master": m_params_fp32,
        "m_opt_fp32_adam": m_opt,
        "total": m_params + m_grad + m_params_fp32 + m_opt,
    }


def validate_dp_degree(dp, world_size):
    if world_size % dp != 0:
        raise InvalidTrainingConfig(f"dp={dp} does not evenly divide world_size={world_size}")


def shard_model_state(per_rank_replicated, dp):
    """ZeRO-3/FSDP: every component of model-state memory is divided
    by the DP degree -- [@src-54;@src-17]."""
    if dp <= 0:
        raise InvalidTrainingConfig(f"dp must be positive, got {dp}")
    return {k: v / dp for k, v in per_rank_replicated.items()}


def activation_memory_bytes(L, seq, bs, h, n_heads):
    """m_act = L*seq*bs*h*(34 + 5*n_heads*seq/h) -- [@src-17]'s own
    mixed-precision activation-memory formula."""
    if h % n_heads != 0:
        raise InvalidTrainingConfig(f"hidden size {h} is not divisible by n_heads={n_heads}")
    return L * seq * bs * h * (34 + 5 * n_heads * seq / h)


def boundary_only_activation_estimate_bytes(L, seq, bs, h):
    """Illustrative, script-computed estimate of full activation
    recomputation's memory floor: apply [@src-17]'s own stated
    PRINCIPLE ("during the forward pass, each accelerator only stores
    output activations at partition boundaries") to the toy config,
    storing one bf16 hidden-state tensor per layer boundary. This is
    NOT a formula given directly by any source for this specific
    reduced case -- it is this chapter's own illustrative application
    of the stated principle, explicitly NOT a claim about measured
    recomputation memory for any real model."""
    bytes_per_boundary = seq * bs * h * BYTES_PER_ELEM_BF16
    return L * bytes_per_boundary


def zero3_forward_allgather_payload_bytes(h, dp):
    """16*h^2 elements per transformer block (total across the
    collective); 16*h^2/dp elements/rank -- [@src-17]'s own ZeRO-3
    communication-volume analysis. Converted to bytes at bf16 width."""
    elements_per_rank = (16 * h ** 2) / dp
    return elements_per_rank * BYTES_PER_ELEM_BF16


def estimate_communication_time_seconds(bytes_moved, effective_bandwidth_bytes_per_s, alpha_seconds, num_messages=1):
    """T_comm ~= alpha * num_messages + bytes_moved / effective_bandwidth.
    alpha and effective_bandwidth are DECLARED, illustrative assumptions
    for this worked example -- not a measurement of any real
    interconnect. effective_bandwidth is explicitly NOT the same as a
    link's nominal/peak bandwidth; see chapter prose."""
    if effective_bandwidth_bytes_per_s <= 0:
        raise InvalidTrainingConfig("effective_bandwidth_bytes_per_s must be positive")
    if bytes_moved < 0:
        raise InvalidTrainingConfig("bytes_moved must be non-negative")
    return alpha_seconds * num_messages + bytes_moved / effective_bandwidth_bytes_per_s


def exposed_communication_seconds(total_comm_seconds, overlap_fraction):
    if not (0.0 <= overlap_fraction <= 1.0):
        raise InvalidTrainingConfig(f"overlap_fraction must be in [0,1], got {overlap_fraction}")
    hidden = total_comm_seconds * overlap_fraction
    exposed = total_comm_seconds - hidden
    return hidden, exposed


def main():
    # ---- TOY / ILLUSTRATIVE inputs -- not a real model or cluster ----
    TOY_HIDDEN = 4096
    TOY_VOCAB = 32000
    TOY_LAYERS = 24
    TOY_N_HEADS = 32
    TOY_SEQ_LEN = 2048
    TOY_MICROBATCH = 2
    TOY_WORLD_SIZE = 8
    TOY_DP_DEGREE = 8
    TOY_EFFECTIVE_BANDWIDTH_GBPS = 200.0  # illustrative, NOT a measured link speed
    TOY_ALPHA_SECONDS = 10e-6             # illustrative fixed per-message latency
    TOY_OVERLAP_FRACTION = 0.7            # illustrative fraction of comm hidden behind compute
    TOY_COMPUTE_TIME_SECONDS = 0.120      # illustrative forward-pass compute time for this toy config

    validate_dp_degree(TOY_DP_DEGREE, TOY_WORLD_SIZE)

    N = parameter_count(TOY_HIDDEN, TOY_VOCAB, TOY_LAYERS)
    replicated = model_state_memory_bytes(N)
    sharded = shard_model_state(replicated, TOY_DP_DEGREE)

    act_bytes_no_recompute = activation_memory_bytes(
        TOY_LAYERS, TOY_SEQ_LEN, TOY_MICROBATCH, TOY_HIDDEN, TOY_N_HEADS,
    )
    act_bytes_boundary_only = boundary_only_activation_estimate_bytes(
        TOY_LAYERS, TOY_SEQ_LEN, TOY_MICROBATCH, TOY_HIDDEN,
    )

    payload_bytes_per_rank = zero3_forward_allgather_payload_bytes(TOY_HIDDEN, TOY_DP_DEGREE)
    payload_bytes_all_blocks = payload_bytes_per_rank * TOY_LAYERS

    effective_bw_bytes_per_s = TOY_EFFECTIVE_BANDWIDTH_GBPS * 1e9
    comm_time_per_block = estimate_communication_time_seconds(
        payload_bytes_per_rank, effective_bw_bytes_per_s, TOY_ALPHA_SECONDS,
    )
    total_comm_time_all_blocks = comm_time_per_block * TOY_LAYERS

    hidden_s, exposed_s = exposed_communication_seconds(total_comm_time_all_blocks, TOY_OVERLAP_FRACTION)

    step_time_with_overlap = TOY_COMPUTE_TIME_SECONDS + exposed_s
    step_time_fully_exposed = TOY_COMPUTE_TIME_SECONDS + total_comm_time_all_blocks
    overlap_benefit_fraction = (step_time_fully_exposed - step_time_with_overlap) / step_time_fully_exposed

    # ---- invalid-configuration checks (must raise) ----
    checks = {}
    try:
        validate_dp_degree(dp=3, world_size=8)
        checks["invalid_dp_not_dividing_world_size_raised"] = False
    except InvalidTrainingConfig:
        checks["invalid_dp_not_dividing_world_size_raised"] = True

    try:
        exposed_communication_seconds(1.0, overlap_fraction=1.5)
        checks["invalid_overlap_fraction_raised"] = False
    except InvalidTrainingConfig:
        checks["invalid_overlap_fraction_raised"] = True

    try:
        estimate_communication_time_seconds(1.0, effective_bandwidth_bytes_per_s=0, alpha_seconds=1e-6)
        checks["invalid_zero_bandwidth_raised"] = False
    except InvalidTrainingConfig:
        checks["invalid_zero_bandwidth_raised"] = True

    try:
        activation_memory_bytes(TOY_LAYERS, TOY_SEQ_LEN, TOY_MICROBATCH, TOY_HIDDEN, n_heads=30)
        checks["invalid_n_heads_not_dividing_hidden_raised"] = False
    except InvalidTrainingConfig:
        checks["invalid_n_heads_not_dividing_hidden_raised"] = True

    result = {
        "toy_config": {
            "hidden": TOY_HIDDEN, "vocab": TOY_VOCAB, "layers": TOY_LAYERS,
            "n_heads": TOY_N_HEADS, "seq_len": TOY_SEQ_LEN, "microbatch": TOY_MICROBATCH,
            "world_size": TOY_WORLD_SIZE, "dp_degree": TOY_DP_DEGREE,
            "effective_bandwidth_GBps": TOY_EFFECTIVE_BANDWIDTH_GBPS,
            "alpha_seconds": TOY_ALPHA_SECONDS,
            "overlap_fraction": TOY_OVERLAP_FRACTION,
            "illustrative_compute_time_seconds": TOY_COMPUTE_TIME_SECONDS,
        },
        "parameter_count_N": N,
        "parameter_count_N_billions": N / 1e9,
        "model_state_memory": {
            "replicated_per_rank_bytes": replicated,
            "replicated_per_rank_GiB": replicated["total"] / 2**30,
            "zero3_sharded_per_rank_bytes": sharded,
            "zero3_sharded_per_rank_GiB": sharded["total"] / 2**30,
        },
        "activation_memory": {
            "no_recompute_bytes": act_bytes_no_recompute,
            "no_recompute_GiB": act_bytes_no_recompute / 2**30,
            "boundary_only_estimate_bytes": act_bytes_boundary_only,
            "boundary_only_estimate_GiB": act_bytes_boundary_only / 2**30,
        },
        "communication": {
            "zero3_allgather_payload_per_rank_per_block_bytes": payload_bytes_per_rank,
            "zero3_allgather_payload_per_rank_per_block_MiB": payload_bytes_per_rank / 2**20,
            "zero3_allgather_payload_all_blocks_bytes": payload_bytes_all_blocks,
            "comm_time_per_block_seconds": comm_time_per_block,
            "total_comm_time_all_blocks_seconds": total_comm_time_all_blocks,
            "total_comm_time_all_blocks_ms": total_comm_time_all_blocks * 1000,
            "hidden_comm_time_seconds": hidden_s,
            "exposed_comm_time_seconds": exposed_s,
            "exposed_comm_time_ms": exposed_s * 1000,
        },
        "step_time": {
            "compute_time_seconds": TOY_COMPUTE_TIME_SECONDS,
            "step_time_with_overlap_seconds": step_time_with_overlap,
            "step_time_with_overlap_ms": step_time_with_overlap * 1000,
            "step_time_fully_exposed_seconds": step_time_fully_exposed,
            "step_time_fully_exposed_ms": step_time_fully_exposed * 1000,
            "overlap_benefit_fraction": overlap_benefit_fraction,
            "overlap_benefit_percent": overlap_benefit_fraction * 100,
        },
        "invalid_configuration_checks": checks,
    }
    out_path = os.path.join(os.path.dirname(__file__), "memory_and_communication_budget.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out_path}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
