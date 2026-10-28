#!/usr/bin/env python3
"""Workbook 06, Chapter 3 worked example: one synthetic four-request trace
scheduled under static (request-level) batching, continuous
(iteration-level) batching without chunking, continuous batching with
chunked prefill, and prefill/decode disaggregation.

Every input is ILLUSTRATIVE and every output is DERIVED by this
deterministic simulator; nothing here is a measured engine benchmark.

Conventions (stated once, used everywhere):
  * Time is in milliseconds on one server-side clock (no client or
    network time; Chapter 1's client boundary is out of scope here).
  * A step (iteration) processes a set of tokens. Processing a token runs
    the forward pass over it and writes its keys and values. The step that
    processes a request's LAST prompt token yields logits from which the
    first output token is SELECTED at the end of that step. Every later
    step for the request processes the most recently selected token and
    selects the next one. A request with n output tokens therefore needs
    its prefill plus n - 1 decode steps, and its last selected token is
    never processed.
  * Illustrative step-cost model: t_step = T0 + ALPHA * (prefill tokens in
    the step) + BETA * (decode tokens in the step), with T0 standing for
    the per-step weight read. Not fitted to any engine or device.
  * A request becomes schedulable at the first step boundary at or after
    its arrival. Policies are FCFS among requests.
  * Metrics (Chapter 1 vocabulary, server side): waiting = first step that
    processes any of its tokens starts - arrival; TTFT = time token 1 is
    selected - arrival; gaps = times between consecutive selected tokens;
    TPOT = (E2E - TTFT) / (n - 1); E2E = time token n is selected -
    arrival. Throughput and goodput use the window from the first arrival
    to the last completion.

Run: python3 serving_schedules.py  (writes serving_schedules.json)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inference_workload_and_metrics import MODEL, kv_bytes_per_token  # noqa: E402

# ---- illustrative inputs -------------------------------------------------
T0, ALPHA, BETA = 5.0, 0.015, 0.2          # ms, ms per prefill token, ms per decode token
TRACE = [  # id, arrival (ms), prompt tokens, output tokens
    {"id": "A", "arrival": 0.0, "prompt": 512, "output": 8},
    {"id": "B", "arrival": 0.0, "prompt": 256, "output": 4},
    {"id": "C", "arrival": 12.0, "prompt": 1024, "output": 4},
    {"id": "D", "arrival": 30.0, "prompt": 128, "output": 6},
]
TOKEN_BUDGET_UNCHUNKED = 2048               # tokens per step (large enough for any whole prompt here)
TOKEN_BUDGET_CHUNKED = 256                  # tokens per step for chunked prefill
EXERCISE_CHUNK_BUDGET = 512                 # applied-exercise variant
MAX_SEQS = 4                                # active-sequence limit
SLO = {"ttft_ms": 40.0, "tpot_ms": 10.0}   # both must hold (Chapter 1 form); worst gap reported separately
# disaggregation: KV transfer from the prefill device to the decode device
TRANSFER_EFFECTIVE_BYTES_PER_S = 25e9        # illustrative effective bandwidth (not a link peak)
TRANSFER_FIXED_OVERHEAD_MS = 2.0             # illustrative per-request setup/handshake


def step_cost(prefill_tokens, decode_tokens):
    return T0 + ALPHA * prefill_tokens + BETA * decode_tokens


class Req:
    def __init__(self, r):
        self.id, self.arrival, self.prompt, self.output = r["id"], r["arrival"], r["prompt"], r["output"]
        self.prefilled = 0          # prompt tokens processed
        self.selected = []          # times at which output tokens were selected
        self.processed_outputs = 0  # output tokens whose KV has been written
        self.first_start = None

    @property
    def done(self):
        return len(self.selected) == self.output

    @property
    def in_decode(self):
        return self.prefilled == self.prompt and not self.done


def finish_step(steps, t, work, reqs_by_id):
    """work: list of (req_id, kind, tokens). Records the step, advances state."""
    p = sum(n for _, k, n in work if k == "prefill")
    d = sum(n for _, k, n in work if k == "decode")
    dur = step_cost(p, d)
    end = t + dur
    for rid, kind, n in work:
        r = reqs_by_id[rid]
        if r.first_start is None:
            r.first_start = t
        if kind == "prefill":
            r.prefilled += n
            if r.prefilled == r.prompt:
                r.selected.append(end)          # token 1 selected from the last prompt token's logits
        else:
            r.processed_outputs += 1            # the previously selected token's KV is written
            r.selected.append(end)              # and the next token is selected
    steps.append({"start": round(t, 6), "end": round(end, 6), "prefill_tokens": p, "decode_tokens": d,
                  "work": [{"id": rid, "kind": k, "tokens": n} for rid, k, n in work]})
    return end


def simulate(policy, chunk_budget=None):
    reqs = [Req(r) for r in TRACE]
    by_id = {r.id: r for r in reqs}
    steps, t = [], 0.0
    batch = []                                   # static policy: current fixed batch
    while not all(r.done for r in reqs):
        arrived = [r for r in reqs if r.arrival <= t + 1e-9 and not r.done]
        work = []
        if policy == "static":
            if not batch or all(r.done for r in batch):
                batch = [r for r in arrived if r.first_start is None][:MAX_SEQS]
            if batch:
                pending = [r for r in batch if r.prefilled < r.prompt]
                if pending:                       # one step prefills the whole batch
                    work = [(r.id, "prefill", r.prompt) for r in pending]
                else:
                    work = [(r.id, "decode", 1) for r in batch if not r.done]
        else:
            budget = (chunk_budget or TOKEN_BUDGET_CHUNKED) if policy == "chunked" else TOKEN_BUDGET_UNCHUNKED
            running = [r for r in arrived if r.first_start is not None]
            for r in running:                     # running decodes first, one token each
                if r.in_decode and budget > 0:
                    work.append((r.id, "decode", 1)); budget -= 1
            active = len(running)
            # then partial prefills, then new requests, FCFS, within the budget and sequence limit
            for r in sorted(arrived, key=lambda r: (r.first_start is None, r.arrival, r.id)):
                if r.prefilled == r.prompt or budget <= 0:
                    continue
                is_new = r.first_start is None
                if is_new and active >= MAX_SEQS:
                    break
                need = r.prompt - r.prefilled
                if policy == "continuous" and need > budget:
                    break                         # no chunking: a prompt runs whole or waits
                n = min(need, budget)
                work.append((r.id, "prefill", n)); budget -= n
                if is_new:
                    active += 1
        if not work:                              # idle until the next arrival
            t = min(r.arrival for r in reqs if not r.done and r.arrival > t)
            continue
        t = finish_step(steps, t, work, by_id)
    return reqs, steps


def simulate_disaggregated():
    """Prefill device: FCFS prefill-only steps (whole prompts within the
    unchunked budget). Decode device: continuous decode-only steps; a request
    joins at the first step boundary after its KV transfer completes."""
    reqs = [Req(r) for r in TRACE]
    by_id = {r.id: r for r in reqs}
    psteps, t = [], 0.0
    while any(r.prefilled < r.prompt for r in reqs):
        ready = [r for r in reqs if r.arrival <= t + 1e-9 and r.prefilled < r.prompt]
        if not ready:
            t = min(r.arrival for r in reqs if r.prefilled < r.prompt and r.arrival > t)
            continue
        work, budget = [], TOKEN_BUDGET_UNCHUNKED
        for r in ready:
            if r.prompt <= budget:
                work.append((r.id, "prefill", r.prompt)); budget -= r.prompt
        t = finish_step(psteps, t, work, by_id)
    transfer = {}
    for r in reqs:
        nbytes = r.prompt * kv_bytes_per_token(MODEL)
        ms = TRANSFER_FIXED_OVERHEAD_MS + nbytes / TRANSFER_EFFECTIVE_BYTES_PER_S * 1e3
        transfer[r.id] = {"bytes": nbytes, "ms": round(ms, 6), "ready_at": round(r.selected[0] + ms, 6)}
    dsteps, t = [], 0.0
    while not all(r.done for r in reqs):
        ready = [r for r in reqs if transfer[r.id]["ready_at"] <= t + 1e-9 and not r.done]
        if not ready:
            t = min(transfer[r.id]["ready_at"] for r in reqs if not r.done and transfer[r.id]["ready_at"] > t)
            continue
        t = finish_step(dsteps, t, [(r.id, "decode", 1) for r in ready[:MAX_SEQS]], by_id)
    return reqs, psteps, dsteps, transfer


def request_metrics(r):
    gaps = [round(b - a, 6) for a, b in zip(r.selected, r.selected[1:])]
    ttft = r.selected[0] - r.arrival
    e2e = r.selected[-1] - r.arrival
    tpot = (e2e - ttft) / (r.output - 1) if r.output > 1 else None
    return {"id": r.id, "arrival": r.arrival, "prompt": r.prompt, "output": r.output,
            "waiting_ms": round(r.first_start - r.arrival, 6), "ttft_ms": round(ttft, 6),
            "gaps_ms": gaps, "max_gap_ms": max(gaps) if gaps else None,
            "tpot_ms": round(tpot, 6) if tpot is not None else None, "e2e_ms": round(e2e, 6),
            "selected_at": [round(x, 6) for x in r.selected], "processed_outputs": r.processed_outputs,
            "meets_slo": ttft <= SLO["ttft_ms"] and (tpot is None or tpot <= SLO["tpot_ms"])}


def aggregate(metrics, devices=1):
    start = min(m["arrival"] for m in metrics)
    end = max(m["arrival"] + m["e2e_ms"] for m in metrics)
    window_s = (end - start) / 1e3
    good = [m["id"] for m in metrics if m["meets_slo"]]
    out = sum(m["output"] for m in metrics)
    return {"window_ms": round(end - start, 6), "output_tokens": out,
            "output_tokens_per_s": round(out / window_s, 6),
            "requests_per_s": round(len(metrics) / window_s, 6),
            "good_requests": good, "goodput_requests_per_s": round(len(good) / window_s, 6),
            "devices": devices, "goodput_per_device": round(len(good) / window_s / devices, 6),
            "mean_ttft_ms": round(sum(m["ttft_ms"] for m in metrics) / len(metrics), 6),
            "worst_gap_ms": max(m["max_gap_ms"] for m in metrics if m["max_gap_ms"] is not None)}


def chunk_reread_blocks(n_chunks):
    """Times earlier chunks' KV is re-read when a prefill is split into
    n_chunks equal chunks (each chunk attends to all earlier chunks)."""
    return sum(range(n_chunks))


def preemption_recompute(prompt, outputs_selected):
    """vLLM v0.32.0-style recomputation after a request has selected
    `outputs_selected` tokens. Its cache held the prompt and every selected
    token except the last (never processed): prompt + outputs_selected - 1
    KV entries, all freed. Resuming prefills those again together with the
    last selected token, which would have been processed by the next decode
    step anyway, so the resume pass processes prompt + outputs_selected
    tokens and selects the next one."""
    lost = prompt + outputs_selected - 1
    tokens = prompt + outputs_selected
    return {"kv_entries_freed": lost, "tokens_in_resume_prefill": tokens,
            "tokens_recomputed_beyond_normal_decode": lost,
            "resume_step_ms_alone": round(step_cost(tokens, 0), 6),
            "normal_decode_step_ms_alone": round(step_cost(0, 1), 6)}


def main():
    result = {"labels": {"inputs": "illustrative", "outputs": "derived by a deterministic simulator, not measured"},
              "cost_model": {"t0_ms": T0, "alpha_ms_per_prefill_token": ALPHA, "beta_ms_per_decode_token": BETA},
              "trace": TRACE, "slo": SLO,
              "budgets": {"unchunked": TOKEN_BUDGET_UNCHUNKED, "chunked": TOKEN_BUDGET_CHUNKED, "max_seqs": MAX_SEQS},
              "policies": {}}
    for policy in ("static", "continuous", "chunked"):
        reqs, steps = simulate(policy)
        ms = [request_metrics(r) for r in reqs]
        result["policies"][policy] = {"steps": steps, "requests": ms, "aggregate": aggregate(ms)}
    reqs, psteps, dsteps, transfer = simulate_disaggregated()
    ms = [request_metrics(r) for r in reqs]
    result["policies"]["disaggregated"] = {"prefill_steps": psteps, "decode_steps": dsteps, "transfer": transfer,
                                           "requests": ms, "aggregate": aggregate(ms, devices=2),
                                           "transfer_assumptions": {"effective_bytes_per_s": TRANSFER_EFFECTIVE_BYTES_PER_S,
                                                                    "fixed_overhead_ms": TRANSFER_FIXED_OVERHEAD_MS,
                                                                    "kv_bytes_per_token": kv_bytes_per_token(MODEL)}}
    reqs, steps = simulate("chunked", chunk_budget=EXERCISE_CHUNK_BUDGET)
    ms = [request_metrics(r) for r in reqs]
    result["exercise_chunked_512"] = {"budget": EXERCISE_CHUNK_BUDGET, "steps": steps, "requests": ms,
                                      "aggregate": aggregate(ms)}
    result["chunking_overhead"] = {"prompt": 1024, "chunk_tokens": 256, "chunks": 4,
                                   "earlier_chunk_rereads": chunk_reread_blocks(4)}
    result["preemption"] = {"request": "A", "after_outputs_selected": 5, **preemption_recompute(512, 5)}
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "serving_schedules.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
