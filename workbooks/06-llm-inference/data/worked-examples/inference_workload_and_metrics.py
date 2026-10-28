#!/usr/bin/env python3
"""Workbook 06, Chapter 1 worked example: an idealized cost/roofline model
of prefill and decode, and serving metrics computed from a synthetic
request/token event log.

Every number this script produces is DERIVED from the stated inputs, and
every input is ILLUSTRATIVE: the model configuration resembles an
8B-class dense decoder with grouped-query attention but is not a claim
about any named model, and the accelerator numbers are round values, not
a specification of any real device. Nothing here is a measurement.

Accounting conventions (stated once, used everywhere):
  * Precision: weights and KV cache in a 2-byte format (bf16).
  * FLOPs: one multiply-add = 2 FLOPs. Linear layers cost 2 x (weights
    used) x (tokens in the step). Attention cost counts only the two
    attention matmuls (scores Q.K and the weighted sum with V); softmax,
    normalization and other element-wise work are ignored.
  * "Linear" weights are the matrices multiplied in every step: attention
    projections (Q, K, V, O), the gated MLP (three matrices) and the
    output (unembedding) matrix. The input embedding is a row lookup, so
    it is stored but not counted as matmul work or as bytes read per step.
  * Logical bytes: the minimum bytes that must move from device memory if
    every weight element read in the step is read exactly once and every
    needed KV element is read exactly once. Activation traffic is ignored
    (small when tokens per step << model width). Real traffic is at least
    this and usually more; it is not modelled.
  * Roofline: attainable FLOP/s = min(peak FLOP/s, bandwidth x intensity).
    Two idealized step-time numbers are reported: a global lower bound,
    max(total FLOPs / peak, total bytes / bandwidth), which assumes perfect
    overlap of everything; and a per-operation estimate that sums
    max(FLOPs/peak, bytes/bandwidth) for the linear part and the attention
    part separately, which assumes the two parts run back to back. Neither
    is a measured runtime.
  * Decode steps: every sequence in the batch adds one token (T_q = 1) and
    all sequences have the same retained context length S (a
    simplification); decode attention bytes are the cache read only (the
    new token's K/V write, 1/S of the read, and Q/O traffic are ignored).
    Prefill: one prompt, causal attention over unmasked pairs, unembedding
    applied at the last position only (inference, not training).

Run: python3 inference_workload_and_metrics.py  (writes inference_workload_and_metrics.json)
"""
import json
import os

# ---- illustrative inputs ------------------------------------------------
MODEL = {
    "n_layers": 32, "d_model": 4096, "n_q_heads": 32, "n_kv_heads": 8, "d_head": 128,
    "d_ff": 14336, "vocab": 128000, "bytes_per_weight": 2, "bytes_per_kv": 2,
}
HARDWARE = {  # round illustrative numbers, not a real device
    "peak_flops_per_s": 1.0e15,
    "mem_bandwidth_bytes_per_s": 3.0e12,
    "mem_capacity_bytes": 80e9,
}
DECODE_CONTEXTS = [512, 4096]
DECODE_BATCHES = [1, 16, 64, 256, 512]
PREFILL_PROMPT_TOKENS = 2048
MHA_COMPARISON_KV_HEADS = 32  # same model with one KV head per query head


def linear_params(m):
    d, hq, hkv, dh = m["d_model"], m["n_q_heads"], m["n_kv_heads"], m["d_head"]
    attn = d * hq * dh + 2 * d * hkv * dh + hq * dh * d
    mlp = 3 * d * m["d_ff"]
    per_layer = attn + mlp
    unembed = d * m["vocab"]
    return {"attention_per_layer": attn, "mlp_per_layer": mlp, "per_layer": per_layer,
            "unembedding": unembed, "linear_total": per_layer * m["n_layers"] + unembed,
            "input_embedding_stored_not_read": d * m["vocab"]}


def kv_bytes_per_token(m, n_kv_heads=None):
    hkv = m["n_kv_heads"] if n_kv_heads is None else n_kv_heads
    return 2 * m["n_layers"] * hkv * m["d_head"] * m["bytes_per_kv"]


def attention_flops_per_query_token(m, context):
    # Q.K scores and weights.V, each 2 x context x d_head per query head per layer
    return 4 * context * m["n_layers"] * m["n_q_heads"] * m["d_head"]


def decode_step(m, hw, batch, context):
    p = linear_params(m)["linear_total"]
    f_lin = 2 * p * batch
    b_lin = p * m["bytes_per_weight"]
    f_att = batch * attention_flops_per_query_token(m, context)
    b_att = batch * context * kv_bytes_per_token(m)
    C, W = hw["peak_flops_per_s"], hw["mem_bandwidth_bytes_per_s"]
    t_lin = max(f_lin / C, b_lin / W)
    t_att = max(f_att / C, b_att / W)
    t_global = max((f_lin + f_att) / C, (b_lin + b_att) / W)
    t_est = t_lin + t_att
    resident = b_lin + linear_params(m)["input_embedding_stored_not_read"] * m["bytes_per_weight"] + b_att
    return {
        "batch": batch, "context": context, "tokens_per_step": batch,
        "linear_flops": f_lin, "linear_bytes": b_lin, "linear_intensity": f_lin / b_lin,
        "linear_bound": "compute" if f_lin / C > b_lin / W else "bandwidth",
        "attention_flops": f_att, "attention_bytes": b_att, "attention_intensity": f_att / b_att,
        "attention_bound": "compute" if f_att / C > b_att / W else "bandwidth",
        "step_time_lower_bound_s": t_global, "step_time_per_op_estimate_s": t_est,
        "tokens_per_s_at_per_op_estimate": batch / t_est,
        "logical_resident_bytes": resident,
        "fits_illustrative_capacity": resident <= hw["mem_capacity_bytes"],
    }


def prefill(m, hw, prompt):
    lp = linear_params(m)
    p = lp["linear_total"]
    # inference prefill needs logits only at the last prompt position (to
    # sample the first output token); training computes them at every position
    f_lin = 2 * (p - lp["unembedding"]) * prompt + 2 * lp["unembedding"]
    b_lin = p * m["bytes_per_weight"]
    # causal, counting only unmasked query-key pairs (a block-skipping kernel);
    # a dense masked kernel would do about twice this: query i (1-based) attends to i keys
    f_att = 4 * m["n_layers"] * m["n_q_heads"] * m["d_head"] * prompt * (prompt + 1) // 2
    # logical attention bytes: read Q once, read K and V once, write O once;
    # the cache write of K and V is reported separately (kv_written_bytes)
    q_bytes = prompt * m["n_q_heads"] * m["d_head"] * m["bytes_per_kv"] * m["n_layers"]
    kv_bytes = prompt * kv_bytes_per_token(m)
    b_att = 2 * q_bytes + kv_bytes
    C, W = hw["peak_flops_per_s"], hw["mem_bandwidth_bytes_per_s"]
    t_lin = max(f_lin / C, b_lin / W)
    t_att = max(f_att / C, b_att / W)
    return {
        "prompt_tokens": prompt, "linear_flops": f_lin, "linear_bytes": b_lin,
        "linear_intensity": f_lin / b_lin,
        "linear_bound": "compute" if f_lin / C > b_lin / W else "bandwidth",
        "attention_flops": f_att, "attention_logical_bytes": b_att, "attention_intensity": f_att / b_att,
        "kv_written_bytes": kv_bytes,
        "step_time_lower_bound_s": max((f_lin + f_att) / C, (b_lin + b_att) / W),
        "step_time_per_op_estimate_s": t_lin + t_att,
    }


# ---- synthetic event log ------------------------------------------------
# Times in seconds on one shared clock. Client events: send, each streamed
# content chunk (with the number of output tokens it carries), and the
# end-of-stream marker. Server events: arrival, first scheduled, and the
# time each output token is emitted. r3 has a single output token; r2's
# third chunk carries two tokens (as happens when tokens are bundled).
EVENTS = [
    {"id": "r1", "client_send": 0.000, "server_arrival": 0.010, "first_scheduled": 0.010,
     "server_token_times": [0.200, 0.240, 0.280, 0.320, 0.360],
     "client_chunks": [[0.215, 1], [0.255, 1], [0.295, 1], [0.335, 1], [0.375, 1]], "client_done": 0.380},
    {"id": "r2", "client_send": 0.050, "server_arrival": 0.060, "first_scheduled": 0.300,
     "server_token_times": [0.520, 0.570, 0.610, 0.620, 0.660],
     "client_chunks": [[0.535, 1], [0.585, 1], [0.640, 2], [0.675, 1]], "client_done": 0.680},
    {"id": "r3", "client_send": 0.100, "server_arrival": 0.110, "first_scheduled": 0.110,
     "server_token_times": [0.400],
     "client_chunks": [[0.415, 1]], "client_done": 0.420},
    {"id": "r4", "client_send": 0.150, "server_arrival": 0.160, "first_scheduled": 0.600,
     "server_token_times": [0.900, 0.960, 1.020],
     "client_chunks": [[0.915, 1], [0.975, 1], [1.035, 1]], "client_done": 1.040},
]
SLO = {"ttft_s": 0.5, "tpot_s": 0.05}


def request_metrics(e):
    chunks = e["client_chunks"]
    n_out = sum(n for _, n in chunks)
    assert n_out == len(e["server_token_times"]), e["id"]
    first, last = chunks[0][0], chunks[-1][0]
    ttft_client = first - e["client_send"]
    e2e_client = last - e["client_send"]
    itl = [round(chunks[i][0] - chunks[i - 1][0], 6) for i in range(1, len(chunks))]
    tpot = (e2e_client - ttft_client) / (n_out - 1) if n_out > 1 else None
    server_ttft_incl_queue = e["server_token_times"][0] - e["server_arrival"]
    server_queue = e["first_scheduled"] - e["server_arrival"]
    gaps = [round(b - a, 6) for a, b in zip(e["server_token_times"], e["server_token_times"][1:])]
    return {
        "id": e["id"], "output_tokens": n_out,
        "ttft_client_s": round(ttft_client, 6), "e2e_client_s": round(e2e_client, 6),
        "itl_client_s": itl, "tpot_s": None if tpot is None else round(tpot, 6),
        "server_ttft_incl_queue_s": round(server_ttft_incl_queue, 6),
        "server_queue_s": round(server_queue, 6),
        "server_ttft_excl_queue_s": round(server_ttft_incl_queue - server_queue, 6),
        "server_token_gaps_s": gaps,
        "client_overhead_on_ttft_s": round(ttft_client - server_ttft_incl_queue, 6),
    }


def aggregate(per_req, events):
    window_start = min(e["client_send"] for e in events)
    # like vLLM v0.32.0's benchmark duration, the window ends when the last
    # stream has finished (its end-of-stream marker), not at its last content chunk
    window_end = max(e["client_done"] for e in events)
    window = window_end - window_start
    total_out = sum(r["output_tokens"] for r in per_req)
    itl_all = [g for r in per_req for g in r["itl_client_s"]]
    tpots = [r["tpot_s"] for r in per_req if r["tpot_s"] is not None]

    def good(r, one_token_rule):
        ok_ttft = r["ttft_client_s"] <= SLO["ttft_s"]
        if r["tpot_s"] is None:
            ok_tpot = one_token_rule == "vacuous"
        else:
            ok_tpot = r["tpot_s"] <= SLO["tpot_s"]
        return ok_ttft and ok_tpot

    good_vacuous = [r["id"] for r in per_req if good(r, "vacuous")]
    good_strict = [r["id"] for r in per_req if good(r, "strict")]
    return {
        "window_start_s": window_start, "window_end_s": window_end, "window_s": round(window, 6),
        "completed_requests": len(per_req), "output_tokens": total_out,
        "request_throughput_per_s": round(len(per_req) / window, 6),
        "output_token_throughput_per_s": round(total_out / window, 6),
        "mean_itl_s": round(sum(itl_all) / len(itl_all), 6), "itl_gap_count": len(itl_all),
        "mean_tpot_s_excluding_one_token": round(sum(tpots) / len(tpots), 6), "tpot_count": len(tpots),
        "mean_tpot_s_if_one_token_counted_as_zero": round(sum(tpots) / (len(tpots) + 1), 6),
        "slo": SLO,
        "good_requests_one_token_tpot_vacuous": good_vacuous,
        "good_requests_one_token_tpot_strict": good_strict,
        "goodput_per_s_vacuous": round(len(good_vacuous) / window, 6),
        "goodput_per_s_strict": round(len(good_strict) / window, 6),
    }


def sampling_transforms(probs, top_p, top_k):
    """Truncate-and-renormalize a small next-token distribution (probabilities
    sorted in descending order), as defined for top-p and top-k sampling."""
    order = sorted(range(len(probs)), key=lambda i: -probs[i])
    kept, mass = [], 0.0
    for i in order:  # smallest set whose mass reaches top_p
        kept.append(i)
        mass += probs[i]
        if mass >= top_p - 1e-12:
            break
    top_p_dist = {i: probs[i] / mass for i in kept}
    k_set = order[:top_k]
    k_mass = sum(probs[i] for i in k_set)
    top_k_dist = {i: probs[i] / k_mass for i in k_set}
    return {"probs": probs, "top_p": top_p, "top_p_set": kept, "top_p_mass": mass,
            "top_p_renormalized": {str(i): round(v, 6) for i, v in top_p_dist.items()},
            "top_k": top_k, "top_k_set": k_set,
            "top_k_renormalized": {str(i): round(v, 6) for i, v in top_k_dist.items()}}


def questions(m, hw):
    """Numbers used by the chapter's questions and answer key."""
    q1 = decode_step(m, hw, 8, 4096)
    # Q5: largest decode batch at S = 4096 whose per-op step estimate is <= 10 ms
    best = max(b for b in range(1, 1025) if decode_step(m, hw, b, 4096)["step_time_per_op_estimate_s"] <= 0.010)
    q5 = decode_step(m, hw, best, 4096)
    q3_chunks = [[0.30, 1], [0.36, 2], [0.40, 1]]
    q3 = request_metrics({"id": "q3", "client_send": 0.0, "server_arrival": 0.0, "first_scheduled": 0.0,
                          "server_token_times": [0.29, 0.34, 0.35, 0.39], "client_chunks": q3_chunks,
                          "client_done": 0.41})
    m_mha = dict(m, n_kv_heads=MHA_COMPARISON_KV_HEADS)
    # the MHA variant also has larger K/V projections, so its weights differ too
    params_mha = linear_params(m_mha)
    stored = (params_mha["linear_total"] + params_mha["input_embedding_stored_not_read"]) * m["bytes_per_weight"]
    mha_step = decode_step(m_mha, hw, 16, 4096)
    gqa_step = decode_step(m, hw, 16, 4096)
    mha = {"kv_bytes_per_token": kv_bytes_per_token(m, MHA_COMPARISON_KV_HEADS),
           "kv_bytes_per_sequence_4096": 4096 * kv_bytes_per_token(m, MHA_COMPARISON_KV_HEADS),
           "attention_intensity": attention_flops_per_query_token(m, 1) / kv_bytes_per_token(m, MHA_COMPARISON_KV_HEADS),
           "max_batch_fitting_4096": int((hw["mem_capacity_bytes"] - stored)
                                         // (4096 * kv_bytes_per_token(m, MHA_COMPARISON_KV_HEADS))),
           "step_time_B16_S4096_s": mha_step["step_time_per_op_estimate_s"],
           "tokens_per_s_B16_S4096": mha_step["tokens_per_s_at_per_op_estimate"],
           "weight_bytes_read_per_step": params_mha["linear_total"] * m["bytes_per_weight"],
           "weight_bytes_stored": stored,
           "gqa_step_time_B16_S4096_s": gqa_step["step_time_per_op_estimate_s"],
           "gqa_tokens_per_s_B16_S4096": gqa_step["tokens_per_s_at_per_op_estimate"]}
    return {
        "q1_decode_B8_S4096": {"bytes": q1["linear_bytes"] + q1["attention_bytes"],
                               "step_time_s": q1["step_time_per_op_estimate_s"],
                               "tokens_per_s": q1["tokens_per_s_at_per_op_estimate"],
                               "flops": q1["linear_flops"] + q1["attention_flops"]},
        "q2_integer_crossover_tokens": min(n for n in range(1, 2000) if 2 * n / m["bytes_per_weight"]
                                           >= hw["peak_flops_per_s"] / hw["mem_bandwidth_bytes_per_s"]),
        "q3_request": q3,
        "q4_sampling": sampling_transforms([0.5, 0.2, 0.15, 0.1, 0.05], 0.8, 2),
        "q5_max_batch_10ms_S4096": {"batch": best, "step_time_s": q5["step_time_per_op_estimate_s"],
                                    "tokens_per_s": q5["tokens_per_s_at_per_op_estimate"]},
        "exercise_mha": mha,
    }


def main():
    m, hw = MODEL, HARDWARE
    params = linear_params(m)
    ridge = hw["peak_flops_per_s"] / hw["mem_bandwidth_bytes_per_s"]
    decode = {str(S): [decode_step(m, hw, B, S) for B in DECODE_BATCHES] for S in DECODE_CONTEXTS}
    gqa_att_intensity = attention_flops_per_query_token(m, 1) / kv_bytes_per_token(m)
    mha_att_intensity = attention_flops_per_query_token(m, 1) / kv_bytes_per_token(m, MHA_COMPARISON_KV_HEADS)
    max_batch_fit = {str(S): int((hw["mem_capacity_bytes"]
                                  - (params["linear_total"] + params["input_embedding_stored_not_read"]) * m["bytes_per_weight"])
                                 // (S * kv_bytes_per_token(m))) for S in DECODE_CONTEXTS}
    per_req = [request_metrics(e) for e in EVENTS]
    result = {
        "labels": {"inputs": "illustrative", "outputs": "derived (idealized, not measured)"},
        "model": m, "hardware": hw, "params": params,
        "weight_bytes_read_per_step": params["linear_total"] * m["bytes_per_weight"],
        "weight_bytes_stored": (params["linear_total"] + params["input_embedding_stored_not_read"]) * m["bytes_per_weight"],
        "kv_bytes_per_token": kv_bytes_per_token(m),
        "kv_bytes_per_sequence": {str(S): S * kv_bytes_per_token(m) for S in DECODE_CONTEXTS},
        "ridge_flops_per_byte": ridge,
        "linear_crossover_tokens_per_step": ridge * m["bytes_per_weight"] / 2,
        "decode_attention_intensity_gqa": gqa_att_intensity,
        "decode_attention_intensity_mha": mha_att_intensity,
        "max_batch_fitting_capacity": max_batch_fit,
        "decode": decode,
        "prefill": prefill(m, hw, PREFILL_PROMPT_TOKENS),
        "events": EVENTS, "requests": per_req, "aggregate": aggregate(per_req, EVENTS),
        "questions": questions(m, hw),
    }
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inference_workload_and_metrics.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
