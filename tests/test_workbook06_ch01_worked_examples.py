"""Numerical and semantic tests for Workbook 06, Chapter 1's worked example
(data/worked-examples/inference_workload_and_metrics.{py,json}).

They recompute the cost model and the event-log metrics independently of
the script, check units and edge cases (one-output-token requests,
multi-token chunks, the vacuous versus strict TPOT convention for
goodput), confirm the committed JSON matches a fresh run, and check that
the numbers quoted in the chapter and answer key are the derived ones.
"""
import importlib.util
import json
import math
import os
import re
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WB = os.path.join(REPO_ROOT, "workbooks", "06-llm-inference")
EX_DIR = os.path.join(WB, "data", "worked-examples")


def load_script():
    spec = importlib.util.spec_from_file_location("wb06_ch01_example", os.path.join(EX_DIR, "inference_workload_and_metrics.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read(*parts):
    with open(os.path.join(WB, *parts), encoding="utf-8") as f:
        return f.read()


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_script()
        with open(os.path.join(EX_DIR, "inference_workload_and_metrics.json"), encoding="utf-8") as f:
            cls.d = json.load(f)
        cls.m, cls.hw = cls.mod.MODEL, cls.mod.HARDWARE


class TestCostModel(Base):
    def test_inputs_are_labelled_illustrative(self):
        self.assertEqual(self.d["labels"]["inputs"], "illustrative")
        self.assertIn("not measured", self.d["labels"]["outputs"])

    def test_linear_parameter_count_by_hand(self):
        d, L = 4096, 32
        attn = d * 32 * 128 + 2 * d * 8 * 128 + 32 * 128 * d
        mlp = 3 * d * 14336
        total = L * (attn + mlp) + d * 128000
        self.assertEqual(self.d["params"]["linear_total"], total)
        self.assertEqual(total, 7_503_609_856)
        self.assertEqual(self.d["weight_bytes_read_per_step"], 2 * total)
        self.assertEqual(self.d["weight_bytes_stored"], 2 * (total + d * 128000))

    def test_kv_bytes_units(self):
        self.assertEqual(self.d["kv_bytes_per_token"], 2 * 32 * 8 * 128 * 2)
        self.assertEqual(self.d["kv_bytes_per_token"], 128 * 1024)  # 128 KiB
        self.assertEqual(self.d["kv_bytes_per_sequence"]["512"], 64 * 2**20)
        self.assertEqual(self.d["kv_bytes_per_sequence"]["4096"], 512 * 2**20)

    def test_ridge_crossover_and_attention_intensity(self):
        self.assertAlmostEqual(self.d["ridge_flops_per_byte"], 1e15 / 3e12)
        self.assertAlmostEqual(self.d["linear_crossover_tokens_per_step"], 1e15 / 3e12)  # 2-byte weights
        self.assertAlmostEqual(self.d["decode_attention_intensity_gqa"], 2 * 32 / (8 * 2))
        self.assertAlmostEqual(self.d["decode_attention_intensity_mha"], 1.0)

    def test_decode_rows_recomputed(self):
        P = self.d["params"]["linear_total"]
        for S, rows in self.d["decode"].items():
            S = int(S)
            for r in rows:
                B = r["batch"]
                f_lin, b_lin = 2 * P * B, 2 * P
                f_att = 4 * B * S * 32 * 32 * 128
                b_att = B * S * self.d["kv_bytes_per_token"]
                self.assertEqual((r["linear_flops"], r["linear_bytes"], r["attention_flops"], r["attention_bytes"]),
                                 (f_lin, b_lin, f_att, b_att))
                self.assertAlmostEqual(r["linear_intensity"], B)  # 2N_tok / b_w with b_w = 2
                self.assertAlmostEqual(r["attention_intensity"], 4.0)  # independent of B and S
                est = max(f_lin / 1e15, b_lin / 3e12) + max(f_att / 1e15, b_att / 3e12)
                lb = max((f_lin + f_att) / 1e15, (b_lin + b_att) / 3e12)
                self.assertAlmostEqual(r["step_time_per_op_estimate_s"], est)
                self.assertAlmostEqual(r["step_time_lower_bound_s"], lb)
                self.assertLessEqual(lb, est + 1e-15)  # the global bound never exceeds the per-op sum
                self.assertAlmostEqual(r["tokens_per_s_at_per_op_estimate"], B / est)
                self.assertEqual(r["attention_bound"], "bandwidth")
                self.assertEqual(r["linear_bound"], "compute" if B > 1e15 / 3e12 else "bandwidth")
                resident = self.d["weight_bytes_stored"] + b_att
                self.assertEqual(r["fits_illustrative_capacity"], resident <= 80e9)

    def test_batch_trade_off_is_monotone(self):
        for rows in self.d["decode"].values():
            t = [r["step_time_per_op_estimate_s"] for r in rows]
            x = [r["tokens_per_s_at_per_op_estimate"] for r in rows]
            self.assertEqual(t, sorted(t))
            self.assertEqual(x, sorted(x))

    def test_max_batch_fitting(self):
        stored = self.d["weight_bytes_stored"]
        for S, n in self.d["max_batch_fitting_capacity"].items():
            per = int(S) * self.d["kv_bytes_per_token"]
            self.assertLessEqual(stored + n * per, 80e9)
            self.assertGreater(stored + (n + 1) * per, 80e9)
        self.assertEqual(self.d["max_batch_fitting_capacity"], {"512": 952, "4096": 119})

    def test_prefill(self):
        p = self.d["prefill"]
        P = self.d["params"]["linear_total"]
        U = self.d["params"]["unembedding"]
        # inference prefill: logits only at the last prompt position
        self.assertEqual(p["linear_flops"], 2 * (P - U) * 2048 + 2 * U)
        self.assertLess(p["linear_flops"], 2 * P * 2048)
        self.assertAlmostEqual(p["linear_intensity"], p["linear_flops"] / (2 * P))
        self.assertAlmostEqual(p["step_time_lower_bound_s"], (p["linear_flops"] + p["attention_flops"]) / 1e15)
        self.assertEqual(p["attention_flops"], 4 * 32 * 32 * 128 * 2048 * 2049 // 2)
        ridge = self.d["ridge_flops_per_byte"]
        self.assertGreater(p["linear_intensity"], ridge)
        self.assertGreater(p["attention_intensity"], ridge)

    def test_committed_json_matches_a_fresh_run(self):
        m, hw = self.m, self.hw
        fresh = {str(S): [self.mod.decode_step(m, hw, B, S) for B in self.mod.DECODE_BATCHES] for S in self.mod.DECODE_CONTEXTS}
        self.assertEqual(json.loads(json.dumps(fresh)), self.d["decode"])
        self.assertEqual(json.loads(json.dumps(self.mod.questions(m, hw))), self.d["questions"])
        self.assertEqual(json.loads(json.dumps(self.mod.prefill(m, hw, 2048))), self.d["prefill"])


class TestMetrics(Base):
    def test_request_metrics_from_timestamps(self):
        by = {r["id"]: r for r in self.d["requests"]}
        for e in self.d["events"]:
            r = by[e["id"]]
            chunks = e["client_chunks"]
            self.assertEqual(r["output_tokens"], sum(n for _, n in chunks))
            self.assertAlmostEqual(r["ttft_client_s"], chunks[0][0] - e["client_send"])
            self.assertAlmostEqual(r["e2e_client_s"], chunks[-1][0] - e["client_send"])  # last content chunk, not done
            self.assertEqual(len(r["itl_client_s"]), len(chunks) - 1)
            if r["output_tokens"] == 1:
                self.assertIsNone(r["tpot_s"])
                self.assertEqual(r["itl_client_s"], [])
            else:
                tpot = (r["e2e_client_s"] - r["ttft_client_s"]) / (r["output_tokens"] - 1)
                self.assertAlmostEqual(r["tpot_s"], tpot, places=6)
                # E2E = TTFT + TPOT (n_out - 1) exactly under these definitions
                self.assertAlmostEqual(r["ttft_client_s"] + r["tpot_s"] * (r["output_tokens"] - 1), r["e2e_client_s"], places=5)
            self.assertAlmostEqual(r["server_queue_s"], e["first_scheduled"] - e["server_arrival"])

    def test_multi_token_chunk_separates_itl_from_tpot(self):
        r2 = [r for r in self.d["requests"] if r["id"] == "r2"][0]
        self.assertAlmostEqual(sum(r2["itl_client_s"]) / len(r2["itl_client_s"]), 0.14 / 3, places=6)
        self.assertAlmostEqual(r2["tpot_s"], 0.035, places=6)

    def test_aggregate_window_and_conventions(self):
        a = self.d["aggregate"]
        ev = self.d["events"]
        # ends when the last stream finishes (end-of-stream marker), as vLLM's duration does
        window = max(e["client_done"] for e in ev) - min(e["client_send"] for e in ev)
        self.assertAlmostEqual(a["window_s"], window)
        self.assertAlmostEqual(a["window_s"], 1.04)
        self.assertGreater(a["window_s"], max(e["client_chunks"][-1][0] for e in ev))
        self.assertEqual(a["completed_requests"], 4)
        self.assertEqual(a["output_tokens"], 14)
        self.assertAlmostEqual(a["request_throughput_per_s"], 4 / 1.04, places=5)
        self.assertAlmostEqual(a["output_token_throughput_per_s"], 14 / 1.04, places=4)
        self.assertEqual(a["itl_gap_count"], 9)
        self.assertAlmostEqual(a["mean_itl_s"], 0.42 / 9, places=6)
        self.assertEqual(a["tpot_count"], 3)
        self.assertAlmostEqual(a["mean_tpot_s_excluding_one_token"], 0.045, places=6)
        self.assertEqual(a["good_requests_one_token_tpot_vacuous"], ["r1", "r2", "r3"])
        self.assertEqual(a["good_requests_one_token_tpot_strict"], ["r1", "r2"])
        self.assertAlmostEqual(a["goodput_per_s_vacuous"], 3 / 1.04, places=5)
        self.assertAlmostEqual(a["goodput_per_s_strict"], 2 / 1.04, places=5)


class TestQuestionsAndProse(Base):
    def test_question_numbers(self):
        q = self.d["questions"]
        self.assertEqual(q["q1_decode_B8_S4096"]["bytes"], 15_007_219_712 + 8 * 536_870_912)
        self.assertAlmostEqual(q["q1_decode_B8_S4096"]["step_time_s"], 0.006434, places=6)
        q3 = q["q3_request"]
        self.assertEqual(q3["output_tokens"], 4)
        self.assertAlmostEqual(q3["tpot_s"], 0.1 / 3, places=6)
        self.assertEqual(len(q3["itl_client_s"]), 2)
        s = q["q4_sampling"]
        self.assertEqual(s["top_p_set"], [0, 1, 2])
        self.assertAlmostEqual(sum(s["top_p_renormalized"].values()), 1.0, places=5)
        self.assertAlmostEqual(sum(s["top_k_renormalized"].values()), 1.0, places=5)
        self.assertGreaterEqual(s["top_p_mass"], s["top_p"])
        self.assertEqual(q["q2_integer_crossover_tokens"], 334)
        self.assertEqual(self.mod.decode_step(self.m, self.hw, 333, 512)["linear_bound"], "bandwidth")
        self.assertEqual(self.mod.decode_step(self.m, self.hw, 334, 512)["linear_bound"], "compute")
        q5 = q["q5_max_batch_10ms_S4096"]
        self.assertEqual(q5["batch"], 27)
        self.assertLessEqual(q5["step_time_s"], 0.010)
        self.assertGreater(self.mod.decode_step(self.m, self.hw, 28, 4096)["step_time_per_op_estimate_s"], 0.010)
        x = q["exercise_mha"]
        self.assertEqual(x["kv_bytes_per_token"], 4 * self.d["kv_bytes_per_token"])
        self.assertEqual(x["max_batch_fitting_4096"], 29)
        self.assertAlmostEqual(x["attention_intensity"], 1.0)
        self.assertGreater(x["step_time_B16_S4096_s"], x["gqa_step_time_B16_S4096_s"])

    def test_prose_quotes_the_derived_numbers(self):
        ch = read("chapters", "01-inference-workload.qmd")
        sol = read("solutions", "01-inference-workload-solutions.qmd")
        for s in ("7,503,609,856", "15.01 GB", "16.06 GB", "131,072", "128 KiB", "64 MiB", "512 MiB",
                  "333", "334", "B = 119", "153.5 GB", "5.18", "16.46", "about 20-fold", "19.14", "28.6 TFLOP", "1,900",
                  "29.7 ms", "1.04 s", "3.85", "46.7 ms", "45.0 ms", "33.8 ms", "2.88", "1.92", "114,000", "16.62 GB", "17.67 GB"):
            self.assertTrue(s in ch, msg=s)
        for s in ("19,302,187,008", "6.43", "1,243", "33.3", "0.588", "0.235", "0.176", "0.714", "0.286",
                  "B = 27", "9.83", "10.01", "2,746", "29", "16.99", "7.87", "2,034", "334", "1.92", "2.88"):
            self.assertTrue(s in sol, msg=s)

    def test_decode_table_matches_json(self):
        ch = read("chapters", "01-inference-workload.qmd")
        rows = re.findall(r"^\| ([\d,]+) \| (\d+) \| (\w+) \| ([\d.]+) \| ([\d,]+) \|", ch, re.MULTILINE)
        self.assertEqual(len(rows), 7)
        for S, B, bound, ms, tps in rows:
            r = [x for x in self.d["decode"][S.replace(",", "")] if x["batch"] == int(B)][0]
            self.assertEqual(bound, r["linear_bound"])
            self.assertEqual(ms, f"{r['step_time_per_op_estimate_s'] * 1e3:.2f}")
            self.assertEqual(int(tps.replace(",", "")), round(r["tokens_per_s_at_per_op_estimate"]))

    def test_request_table_matches_json(self):
        ch = read("chapters", "01-inference-workload.qmd")
        for r in self.d["requests"]:
            row = re.search(rf"^\| {r['id']} \| (\d+) \| (\d+) \|", ch, re.MULTILINE)
            self.assertIsNotNone(row, r["id"])
            self.assertEqual(int(row.group(1)), r["output_tokens"])
            self.assertEqual(int(row.group(2)), round(r["ttft_client_s"] * 1000))

    def test_answer_key_covers_every_question(self):
        ch = read("chapters", "01-inference-workload.qmd")
        sol = read("solutions", "01-inference-workload-solutions.qmd")
        qs = re.findall(r"^(\d)\. \*\*([^*]+)\.\*\*", ch, re.MULTILINE)
        ans = re.findall(r"^\*\*(\d)\. ([^.]+)\.", sol, re.MULTILINE)
        self.assertEqual(qs, ans)
        self.assertEqual(len(qs), 5)
        self.assertEqual(sol.count("*Answer.*"), 5)
        self.assertEqual(sol.count("*Common trap:*"), 5)

    def test_one_token_tpot_is_never_reported_as_a_number(self):
        r3 = [r for r in self.d["requests"] if r["id"] == "r3"][0]
        self.assertIsNone(r3["tpot_s"])
        self.assertTrue(math.isfinite(r3["ttft_client_s"]))


if __name__ == "__main__":
    unittest.main()
