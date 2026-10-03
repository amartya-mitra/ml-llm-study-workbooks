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
    - ZeRO-3 per-transformer-block parameter all-gather: a full block
      has 16*h^2 elements; this chapter declares the collective
      algorithm explicitly as a RING all-gather over the DP group of
      size P, and reports exactly one convention throughout: the
      one-direction (send) volume moved BY one rank, which for a ring
      all-gather is ((P-1)/P) of the full tensor -- NOT the local
      shard size (which is only 1/P of the full tensor, the amount one
      rank *starts with and ends up with locally*, not the amount it
      *communicates*). The receive volume per rank is equal to the
      send volume by the same ring symmetry. This (P-1)/P factor is
      the standard collective-communication-volume result for a ring
      algorithm (every rank forwards P-1 chunks around the ring and
      receives P-1 chunks); it is consistent with -- not a
      contradiction of -- ZeRO's own Section 7.2 Psi-based accounting
      [@src-54], which states collective volumes using the large-P
      asymptotic approximation (P-1)/P ~= 1 and drops the factor
      entirely. This worked example's P=8 is small enough that
      dropping that factor materially changes the numbers, so it is
      kept explicit here rather than approximated away. The latency
      term in the cost model below also uses P-1 (one message per ring
      round), not a single message, for the same reason.
    - Communication volume of one all-gather or reduce-scatter, in
      ZeRO's own large-P asymptotic notation, is one "Psi" of data per
      rank [@src-54] -- this worked example's exact (P-1)/P*Psi
      accounting (above) specializes that asymptotic notation for a
      concrete, small P.

SCOPE of the communication/step-time numbers below: this worked
example models only the FORWARD-PASS ZeRO-3 parameter all-gather
across all 24 transformer blocks. It explicitly excludes backward-pass
parameter all-gathers and gradient reduce-scatters -- see the
"scope" field in the JSON output and the chapter prose, which both
label every downstream number "forward-pass parameter all-gather
communication," never "total step communication."

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


def zero3_block_full_tensor_bytes(h):
    """16*h^2 elements for one full transformer block's ZeRO-3-sharded
    parameters -- [@src-17]'s own per-block element count. Converted
    to bytes at bf16 width. This is the FULL tensor size S, not any
    one rank's share of it."""
    return (16 * h ** 2) * BYTES_PER_ELEM_BF16


def zero3_ring_allgather_volumes_bytes(full_tensor_bytes, dp):
    """For a full tensor of S bytes ring-all-gathered over a DP group
    of P=dp ranks: local shard size = S/P (what one rank stores, NOT
    what it communicates); ring all-gather SEND volume per rank =
    ((P-1)/P)*S; RECEIVE volume per rank = ((P-1)/P)*S also, by ring
    symmetry. Returns all three, explicitly distinguishing the local
    shard from the communicated payload -- see this module's docstring
    and the chapter prose for why conflating the two was a numerical
    bug in an earlier draft."""
    if dp <= 0:
        raise InvalidTrainingConfig(f"dp must be positive, got {dp}")
    local_shard_bytes = full_tensor_bytes / dp
    one_direction_volume_bytes = ((dp - 1) / dp) * full_tensor_bytes
    return {
        "local_shard_bytes": local_shard_bytes,
        "send_volume_per_rank_bytes": one_direction_volume_bytes,
        "receive_volume_per_rank_bytes": one_direction_volume_bytes,
    }


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

    # Ring all-gather over the DP group (P = TOY_DP_DEGREE ranks, no TP
    # active in this toy config). We report ONE convention throughout
    # this chapter: the one-direction (send) volume per rank, which
    # equals the receive volume per rank by ring symmetry -- see this
    # module's docstring. This is explicitly NOT the local shard size.
    full_block_bytes = zero3_block_full_tensor_bytes(TOY_HIDDEN)
    ring_volumes = zero3_ring_allgather_volumes_bytes(full_block_bytes, TOY_DP_DEGREE)
    send_volume_per_rank_bytes = ring_volumes["send_volume_per_rank_bytes"]
    local_shard_bytes = ring_volumes["local_shard_bytes"]
    ring_rounds = TOY_DP_DEGREE - 1  # one ring all-gather round per remaining rank

    reported_payload_bytes_per_rank = send_volume_per_rank_bytes
    payload_bytes_all_blocks = reported_payload_bytes_per_rank * TOY_LAYERS

    effective_bw_bytes_per_s = TOY_EFFECTIVE_BANDWIDTH_GBPS * 1e9
    comm_time_per_block = estimate_communication_time_seconds(
        reported_payload_bytes_per_rank, effective_bw_bytes_per_s, TOY_ALPHA_SECONDS,
        num_messages=ring_rounds,
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

    # Regression check for the local-shard-as-payload bug: the
    # reported communication payload must be the ring all-gather's
    # (P-1)/P send volume, NOT the 1/P local shard size. This would
    # have caught the earlier draft's error, which quoted the local
    # shard (64 MiB) as if it were the per-rank communication volume.
    checks["reported_payload_is_not_local_shard_size"] = (
        reported_payload_bytes_per_rank != local_shard_bytes
    )
    checks["reported_payload_equals_ring_allgather_formula"] = (
        abs(reported_payload_bytes_per_rank - ((TOY_DP_DEGREE - 1) / TOY_DP_DEGREE) * full_block_bytes) < 1e-6
    )
    # Sanity bound (item 2): hidden communication time must never
    # exceed the compute interval it is overlapping with -- otherwise
    # "hidden" is not a physically meaningful label for this toy step.
    checks["hidden_comm_time_does_not_exceed_compute_time"] = (
        hidden_s <= TOY_COMPUTE_TIME_SECONDS
    )

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
            "scope": "forward-pass ZeRO-3 parameter all-gather only (excludes backward-pass parameter all-gathers and gradient reduce-scatters)",
            "collective_algorithm": "ring all-gather",
            "volume_convention": "one-direction (send) volume per rank; receive volume per rank is equal by ring symmetry",
            "ring_rounds": ring_rounds,
            "full_block_tensor_bytes": full_block_bytes,
            "full_block_tensor_MiB": full_block_bytes / 2**20,
            "local_shard_per_rank_per_block_bytes": local_shard_bytes,
            "local_shard_per_rank_per_block_MiB": local_shard_bytes / 2**20,
            "ring_allgather_send_volume_per_rank_per_block_bytes": send_volume_per_rank_bytes,
            "ring_allgather_send_volume_per_rank_per_block_MiB": send_volume_per_rank_bytes / 2**20,
            "ring_allgather_receive_volume_per_rank_per_block_bytes": send_volume_per_rank_bytes,
            "ring_allgather_receive_volume_per_rank_per_block_MiB": send_volume_per_rank_bytes / 2**20,
            "reported_payload_per_rank_per_block_bytes": reported_payload_bytes_per_rank,
            "reported_payload_per_rank_per_block_MiB": reported_payload_bytes_per_rank / 2**20,
            "reported_payload_all_blocks_bytes": payload_bytes_all_blocks,
            "reported_payload_all_blocks_GiB": payload_bytes_all_blocks / 2**30,
            "comm_time_per_block_seconds": comm_time_per_block,
            "comm_time_per_block_ms": comm_time_per_block * 1000,
            "total_comm_time_all_blocks_seconds": total_comm_time_all_blocks,
            "total_comm_time_all_blocks_ms": total_comm_time_all_blocks * 1000,
            "hidden_comm_time_seconds": hidden_s,
            "hidden_comm_time_ms": hidden_s * 1000,
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
