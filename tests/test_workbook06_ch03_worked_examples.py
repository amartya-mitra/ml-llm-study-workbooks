"""Scheduling invariants and metric arithmetic for Workbook 06, Chapter 3's
worked example (data/worked-examples/serving_schedules.{py,json}).

These tests check the generated schedules against the stated rules rather
than re-running the simulator's own logic: steps never overlap on one
device; no request is processed before it arrives; every step stays
within its token budget and sequence limit; prefills complete exactly
and each request selects exactly its output length; each selected token
after the first is processed by a later step (selection precedes
processing, and the last selected token is never processed); static
batching admits no request mid-batch; disaggregated decode starts only
after KV transfer; metrics and aggregates follow from the timestamps.
"""
import importlib.util
import json
import os
import re
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WB = os.path.join(REPO_ROOT, "workbooks", "06-llm-inference")
EX_DIR = os.path.join(WB, "data", "worked-examples")
EPS = 1e-6


def load_script():
    sys.path.insert(0, EX_DIR)
    spec = importlib.util.spec_from_file_location("wb06_ch03_example", os.path.join(EX_DIR, "serving_schedules.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read(*parts):
    with open(os.path.join(WB, *parts), encoding="utf-8") as f:
        return f.read()


with open(os.path.join(EX_DIR, "serving_schedules.json"), encoding="utf-8") as _f:
    DATA = json.load(_f)
TRACE = {r["id"]: r for r in DATA["trace"]}
CM = DATA["cost_model"]


RUNS = dict(DATA["policies"], exercise_chunked_512=DATA["exercise_chunked_512"])


def step_lists(policy):
    p = RUNS[policy]
    if policy == "disaggregated":
        return {"prefill": p["prefill_steps"], "decode": p["decode_steps"]}
    return {"single": p["steps"]}


class TestScheduleInvariants(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(DATA["labels"]["inputs"], "illustrative")
        self.assertIn("not measured", DATA["labels"]["outputs"])

    def test_steps_do_not_overlap_and_cost_model_holds(self):
        for policy in RUNS:
            for device, steps in step_lists(policy).items():
                for a, b in zip(steps, steps[1:]):
                    self.assertLessEqual(a["end"], b["start"] + EPS, msg=f"{policy}/{device}")
                for s in steps:
                    expected = CM["t0_ms"] + CM["alpha_ms_per_prefill_token"] * s["prefill_tokens"] \
                        + CM["beta_ms_per_decode_token"] * s["decode_tokens"]
                    self.assertAlmostEqual(s["end"] - s["start"], expected, places=6)
                    self.assertEqual(s["prefill_tokens"], sum(w["tokens"] for w in s["work"] if w["kind"] == "prefill"))
                    self.assertEqual(s["decode_tokens"], sum(w["tokens"] for w in s["work"] if w["kind"] == "decode"))
                    if device == "prefill":
                        self.assertEqual(s["decode_tokens"], 0)
                    if device == "decode":
                        self.assertEqual(s["prefill_tokens"], 0)

    def test_no_processing_before_arrival(self):
        for policy in RUNS:
            for steps in step_lists(policy).values():
                for s in steps:
                    for w in s["work"]:
                        self.assertGreaterEqual(s["start"] + EPS, TRACE[w["id"]]["arrival"], msg=f"{policy} {w}")

    def test_budgets_and_sequence_limits(self):
        b = DATA["budgets"]
        limits = {"continuous": b["unchunked"], "chunked": b["chunked"],
                  "exercise_chunked_512": DATA["exercise_chunked_512"]["budget"]}
        for policy, limit in limits.items():
            for s in RUNS[policy]["steps"]:
                self.assertLessEqual(s["prefill_tokens"] + s["decode_tokens"], limit)
                self.assertLessEqual(len({w["id"] for w in s["work"]}), b["max_seqs"])
                self.assertEqual(len({w["id"] for w in s["work"]}), len(s["work"]))  # one work item per request per step
        # without chunking a prompt is processed whole in one step
        for s in DATA["policies"]["continuous"]["steps"]:
            for w in s["work"]:
                if w["kind"] == "prefill":
                    self.assertEqual(w["tokens"], TRACE[w["id"]]["prompt"])
        # with chunking, at least one prompt really is split
        chunks = {}
        for s in DATA["policies"]["chunked"]["steps"]:
            for w in s["work"]:
                if w["kind"] == "prefill":
                    chunks.setdefault(w["id"], []).append(w["tokens"])
        self.assertTrue(any(len(v) > 1 for v in chunks.values()))
        self.assertEqual(len(chunks["C"]), 5)

    def test_completion_counts_and_selection_before_processing(self):
        for policy, p in RUNS.items():
            work = {}
            for steps in step_lists(policy).values():
                for s in steps:
                    for w in s["work"]:
                        work.setdefault(w["id"], []).append((s["start"], s["end"], w["kind"], w["tokens"]))
            for rid, r in TRACE.items():
                items = sorted(work[rid])
                prefill = [x for x in items if x[2] == "prefill"]
                decode = [x for x in items if x[2] == "decode"]
                self.assertEqual(sum(x[3] for x in prefill), r["prompt"], msg=f"{policy} {rid}")
                self.assertEqual(len(decode), r["output"] - 1, msg=f"{policy} {rid}")  # last selected token never processed
                self.assertTrue(all(x[3] == 1 for x in decode))
                self.assertLessEqual(max(x[1] for x in prefill), min(x[0] for x in decode) + EPS)
                m = [q for q in p["requests"] if q["id"] == rid][0]
                self.assertEqual(len(m["selected_at"]), r["output"])
                self.assertEqual(m["processed_outputs"], r["output"] - 1)
                self.assertAlmostEqual(m["selected_at"][0], max(x[1] for x in prefill), places=6)
                # each later token is selected at the end of the step that processed its predecessor,
                # and that step started no earlier than the predecessor was selected
                for k, (start, end, _, _) in enumerate(decode):
                    self.assertGreaterEqual(start + EPS, m["selected_at"][k])
                    self.assertAlmostEqual(end, m["selected_at"][k + 1], places=6)

    def test_iteration_level_fcfs_and_decode_first(self):
        # an earlier arrival has always run at least as many steps as a later one
        # (Orca's iteration-level FCFS), and within a step decodes come before prefills
        for policy in ("continuous", "chunked", "exercise_chunked_512"):
            ran = {rid: 0 for rid in TRACE}
            done_at = {m["id"]: m["arrival"] + m["e2e_ms"] for m in RUNS[policy]["requests"]}
            for s in RUNS[policy]["steps"]:
                for w in s["work"]:
                    ran[w["id"]] += 1
                kinds = [w["kind"] for w in s["work"]]
                self.assertEqual(kinds, sorted(kinds), msg=f"{policy}: decode before prefill")
                for i in TRACE:
                    for j in TRACE:
                        earlier = (TRACE[i]["arrival"], i) < (TRACE[j]["arrival"], j)
                        if earlier and done_at[i] > s["end"] + EPS:
                            self.assertGreaterEqual(ran[i], ran[j], msg=f"{policy} {i} vs {j} at {s['end']}")

    def test_disaggregated_joins_at_first_boundary(self):
        p = DATA["policies"]["disaggregated"]
        bounds = sorted({s["start"] for s in p["decode_steps"]} | {s["end"] for s in p["decode_steps"]})
        for rid, t in p["transfer"].items():
            first = min(s["start"] for s in p["decode_steps"] if any(w["id"] == rid for w in s["work"]))
            later = [b for b in bounds if b >= t["ready_at"] - EPS]
            # it joins at the first step start at or after it is ready (or the device was idle and starts then)
            self.assertAlmostEqual(first, min(later), places=5)

    def test_static_admits_no_request_mid_batch(self):
        steps = DATA["policies"]["static"]["steps"]
        batches, current = [], set()
        for s in steps:
            ids = {w["id"] for w in s["work"]}
            if any(w["kind"] == "prefill" for w in s["work"]):
                batches.append(ids)
                current = ids
            else:
                self.assertTrue(ids <= current)
        self.assertEqual(batches, [{"A", "B"}, {"C", "D"}])
        # the second batch starts only after every first-batch request has finished
        first_done = max(m["arrival"] + m["e2e_ms"] for m in DATA["policies"]["static"]["requests"] if m["id"] in "AB")
        second = [s for s in steps if {w["id"] for w in s["work"]} & {"C", "D"}][0]
        self.assertGreaterEqual(second["start"] + EPS, first_done)

    def test_disaggregated_decode_waits_for_transfer(self):
        p = DATA["policies"]["disaggregated"]
        a = p["transfer_assumptions"]
        for rid, t in p["transfer"].items():
            self.assertEqual(t["bytes"], TRACE[rid]["prompt"] * a["kv_bytes_per_token"])
            self.assertAlmostEqual(t["ms"], a["fixed_overhead_ms"] + t["bytes"] / a["effective_bytes_per_s"] * 1e3, places=5)
            m = [q for q in p["requests"] if q["id"] == rid][0]
            self.assertAlmostEqual(t["ready_at"], m["selected_at"][0] + t["ms"], places=5)
            first_decode = min(s["start"] for s in p["decode_steps"] if any(w["id"] == rid for w in s["work"]))
            self.assertGreaterEqual(first_decode + EPS, t["ready_at"])
        # the transfer is one part of C's first gap, not all of it
        c = [q for q in p["requests"] if q["id"] == "C"][0]
        self.assertGreater(c["gaps_ms"][0], p["transfer"]["C"]["ms"])
        self.assertAlmostEqual(p["transfer"]["C"]["bytes"], 128 * 2 ** 20)


class TestMetrics(unittest.TestCase):
    def test_request_metric_arithmetic(self):
        slo = DATA["slo"]
        for policy, p in RUNS.items():
            for m in p["requests"]:
                sel = m["selected_at"]
                self.assertAlmostEqual(m["ttft_ms"], sel[0] - m["arrival"], places=5)
                self.assertAlmostEqual(m["e2e_ms"], sel[-1] - m["arrival"], places=5)
                gaps = [b - a for a, b in zip(sel, sel[1:])]
                self.assertEqual(len(m["gaps_ms"]), len(gaps))
                self.assertAlmostEqual(m["max_gap_ms"], max(gaps), places=5)
                self.assertAlmostEqual(m["tpot_ms"], (m["e2e_ms"] - m["ttft_ms"]) / (m["output"] - 1), places=5)
                self.assertAlmostEqual(m["tpot_ms"], sum(gaps) / len(gaps), places=5)   # TPOT is the mean gap, not the max
                self.assertGreaterEqual(m["max_gap_ms"] + EPS, m["tpot_ms"])
                self.assertGreaterEqual(m["waiting_ms"], -EPS)
                self.assertLessEqual(m["waiting_ms"], m["ttft_ms"] + EPS)
                self.assertEqual(m["meets_slo"], m["ttft_ms"] <= slo["ttft_ms"] and m["tpot_ms"] <= slo["tpot_ms"])

    def test_aggregates(self):
        for policy, p in DATA["policies"].items():
            a, ms = p["aggregate"], p["requests"]
            end = max(m["arrival"] + m["e2e_ms"] for m in ms)
            self.assertAlmostEqual(a["window_ms"], end - min(m["arrival"] for m in ms), places=5)
            self.assertEqual(a["output_tokens"], sum(TRACE[m["id"]]["output"] for m in ms))
            self.assertAlmostEqual(a["output_tokens_per_s"], a["output_tokens"] / (a["window_ms"] / 1e3), places=3)
            good = [m["id"] for m in ms if m["meets_slo"]]
            self.assertEqual(a["good_requests"], good)
            self.assertAlmostEqual(a["goodput_requests_per_s"], len(good) / (a["window_ms"] / 1e3), places=3)
            self.assertAlmostEqual(a["goodput_per_device"], a["goodput_requests_per_s"] / a["devices"], places=3)
        self.assertEqual(DATA["policies"]["disaggregated"]["aggregate"]["devices"], 2)

    def test_teaching_contrasts(self):
        P = {k: v["aggregate"] for k, v in DATA["policies"].items()}
        R = {k: {m["id"]: m for m in v["requests"]} for k, v in DATA["policies"].items()}
        # continuous batching raises throughput but worsens a latency metric
        self.assertGreater(P["continuous"]["output_tokens_per_s"], P["static"]["output_tokens_per_s"])
        self.assertGreater(R["continuous"]["B"]["tpot_ms"], R["static"]["B"]["tpot_ms"])
        self.assertGreater(P["continuous"]["worst_gap_ms"], P["static"]["worst_gap_ms"])
        # chunking bounds the worst gap but delays the long prompt's first token
        self.assertLess(P["chunked"]["worst_gap_ms"], P["continuous"]["worst_gap_ms"])
        self.assertGreater(R["chunked"]["C"]["ttft_ms"], R["continuous"]["C"]["ttft_ms"])
        # disaggregation: more requests meet the SLO, but goodput per device is lower than continuous
        self.assertGreater(len(P["disaggregated"]["good_requests"]), len(P["continuous"]["good_requests"]))
        self.assertLess(P["disaggregated"]["goodput_per_device"], P["continuous"]["goodput_per_device"])

    def test_chunking_and_preemption_side_calculations(self):
        c = DATA["chunking_overhead"]
        self.assertEqual(c["chunks"], c["prompt"] // c["chunk_tokens"])
        self.assertEqual(c["earlier_chunk_rereads"], c["chunks"] * (c["chunks"] - 1) // 2)
        p = DATA["preemption"]
        r = TRACE[p["request"]]
        self.assertEqual(p["kv_entries_freed"], r["prompt"] + p["after_outputs_selected"] - 1)
        self.assertEqual(p["tokens_in_resume_prefill"], p["kv_entries_freed"] + 1)
        self.assertAlmostEqual(p["resume_step_ms_alone"], CM["t0_ms"] + CM["alpha_ms_per_prefill_token"] * p["tokens_in_resume_prefill"])

    def test_committed_json_matches_a_fresh_run(self):
        mod = load_script()
        for policy in ("static", "continuous", "chunked"):
            reqs, steps = mod.simulate(policy)
            self.assertEqual(json.loads(json.dumps(steps)), DATA["policies"][policy]["steps"])


class TestProse(unittest.TestCase):
    def test_static_gap_wording_matches_data(self):
        ch = read("chapters", "03-serving-and-scheduling.qmd")
        gaps = sorted({g for m in DATA["policies"]["static"]["requests"] for g in m["gaps_ms"]})
        self.assertEqual(gaps, [5.2, 5.4])           # not all gaps are equal
        self.assertNotIn("every gap is 5.4 ms", ch)
        self.assertIn("the worst gap is 5.4 ms (5.4 ms while two requests decode, 5.2 ms with one)", ch)

    def test_numbers_and_layout(self):
        ch = read("chapters", "03-serving-and-scheduling.qmd")
        sol = read("solutions", "03-serving-and-scheduling-solutions.qmd")
        P = {k: v["aggregate"] for k, v in DATA["policies"].items()}
        for s in (f"{P['static']['output_tokens_per_s']:.0f}", f"{P['continuous']['output_tokens_per_s']:.0f}",
                  f"{P['chunked']['output_tokens_per_s']:.0f}", "20.8", "9.2", "58.6", "25.3", "7.37",
                  "41.5", "63.8", "11.4", "14.8", "25.5", "51.0", "516", "517", "12.76"):
            self.assertTrue(s in ch, msg=s)
        qs = re.findall(r"^(\d)\. \*\*([^*]+)\.\*\*", ch, re.M)
        ans = re.findall(r"^\*\*(\d)\. ([^.]+)\.", sol, re.M)
        self.assertEqual(qs, ans)
        self.assertEqual(len(qs), 5)
        self.assertEqual(sol.count("*Answer.*"), 5)
        self.assertEqual(sol.count("*Common trap:*"), 5)
        for n, prompt in re.findall(r"^(\d)\. \*\*[^*]+\.\*\* (.+?) \\$", ch, re.M):
            self.assertIn(prompt.replace("$", ""), sol.replace("$", ""), msg=f"Q{n}")
        self.assertEqual(ch.count("#block(breakable: false)["), 5)
        self.assertEqual(sol.count("#block(sticky: true, width: 100%)["), 6)
        self.assertIsNone(re.search(r"\d'", ch + sol), msg="digit followed by an apostrophe renders as a prime")
        E = DATA["exercise_chunked_512"]
        Em = {m["id"]: m for m in E["requests"]}
        for v in (f"{E['aggregate']['worst_gap_ms']:.2f}", f"{Em['C']['ttft_ms']:.1f}",
                  f"{E['aggregate']['output_tokens_per_s']:.0f}", f"{E['aggregate']['goodput_requests_per_s']:.1f}",
                  f"{Em['C']['waiting_ms']:.2f}", "2.67", "13.46"):
            self.assertTrue(v in sol, msg=v)
        self.assertEqual(E["aggregate"]["good_requests"], ["A", "C", "D"])


if __name__ == "__main__":
    unittest.main()
