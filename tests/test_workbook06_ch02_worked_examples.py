"""Numerical, lifecycle and prose-consistency tests for Workbook 06,
Chapter 2's worked example (data/worked-examples/kv_cache_memory.{py,json}).

They recompute the capacity plan and block rounding by hand, check the
reservation and fragmentation accounting, replay the toy block pool to
enforce lifecycle invariants (reference counts equal block-table
references, a referenced block is never on the free queue or handed out,
a shared block is not released while any request holds it, copy-on-write
happens exactly once), check the radix-versus-hash comparison, and confirm
that the numbers quoted in the chapter and answer key are the derived ones.
"""
import importlib.util
import json
import math
import os
import re
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WB = os.path.join(REPO_ROOT, "workbooks", "06-llm-inference")
EX_DIR = os.path.join(WB, "data", "worked-examples")
GIB = 2 ** 30


def load_script():
    sys.path.insert(0, EX_DIR)
    spec = importlib.util.spec_from_file_location("wb06_ch02_example", os.path.join(EX_DIR, "kv_cache_memory.py"))
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
        with open(os.path.join(EX_DIR, "kv_cache_memory.json"), encoding="utf-8") as f:
            cls.d = json.load(f)
        cls.cap = cls.d["capacity"]


class TestCapacity(Base):
    def test_labels(self):
        self.assertEqual(self.d["labels"]["inputs"], "illustrative")
        self.assertIn("not measured", self.d["labels"]["outputs"])

    def test_budget_by_hand(self):
        c = self.cap
        self.assertEqual(c["requested_bytes"], math.ceil(80e9 * 0.92))
        self.assertEqual(c["weights_stored_bytes"], 16_055_795_712)   # Chapter 1's stored weights
        self.assertEqual(c["runtime_headroom_bytes"], 4 * GIB)
        self.assertEqual(c["kv_budget_bytes"], 73_600_000_000 - 16_055_795_712 - 4 * GIB)
        self.assertAlmostEqual(c["kv_budget_gib"], c["kv_budget_bytes"] / GIB)
        self.assertEqual(c["kv_bytes_per_token"], 131_072)
        self.assertEqual(c["block_bytes"], 16 * 131_072)
        self.assertEqual(c["num_blocks"], c["kv_budget_bytes"] // c["block_bytes"])
        self.assertEqual(c["num_blocks"], 25_391)
        self.assertLess(c["unusable_tail_bytes"], c["block_bytes"])

    def test_concurrency_and_exact_fit(self):
        c = self.cap
        self.assertEqual(c["blocks_per_full_sequence"], 256)
        self.assertEqual(c["max_full_length_sequences"], 99)
        self.assertEqual(c["remaining_blocks"], c["num_blocks"] - 99 * 256)
        # exact fit: rem x 16 tokens fits in the remaining blocks, one more token does not
        self.assertEqual(math.ceil(c["exact_fit_extra_tokens"] / 16), c["remaining_blocks"])
        self.assertEqual(c["one_over_blocks_needed"], c["remaining_blocks"] + 1)
        self.assertGreater(c["one_over_blocks_needed"], c["remaining_blocks"])

    def test_rounding(self):
        for r in self.d["rounding"]:
            self.assertEqual(r["blocks"], math.ceil(r["tokens"] / 16))
            self.assertEqual(r["empty_slots"], r["blocks"] * 16 - r["tokens"])
            self.assertLessEqual(r["empty_slots"], 15)

    def test_reservation_accounting(self):
        r = self.d["reservation_vs_paged"]
        self.assertEqual(r["reserved_slots_total"], 8 * 4096)
        self.assertEqual(r["used_slots"] + r["reserved_for_future_slots"] + r["internal_fragmentation_slots"],
                         r["reserved_slots_total"])
        self.assertEqual(r["paged_allocated_slots"],
                         sum(math.ceil(q["current"] / 16) * 16 for q in r["requests"]))
        self.assertLessEqual(r["paged_empty_slots"], 15 * len(r["requests"]))
        # paging never changes the logical bytes of the live tokens
        self.assertEqual(r["used_bytes"], r["used_slots"] * 131_072)

    def test_external_fragmentation(self):
        e = self.d["external_fragmentation"]
        self.assertEqual(e["free_units"], sum(e["free_runs"]))
        self.assertFalse(e["fits_contiguous"])
        self.assertTrue(e["fits_paged"])
        self.assertGreaterEqual(e["free_units"], e["request_units"])

    def test_sharing_at_scale(self):
        s = self.d["sharing_at_scale"]
        self.assertEqual(s["blocks_without_sharing"], 32 * 128)
        self.assertEqual(s["blocks_with_sharing"], 64 + 32 * 64)
        self.assertEqual(s["bytes_with_sharing"], 2112 * 2 * 2 ** 20)
        self.assertEqual(s["max_requests_without_sharing"], self.cap["num_blocks"] // 128)
        self.assertEqual(s["max_requests_with_sharing"], (self.cap["num_blocks"] - 64) // 64)
        # storage falls, per-step reads do not
        self.assertEqual(s["decode_read_bytes_per_step"], s["bytes_without_sharing"])
        self.assertLess(s["bytes_with_sharing"], s["decode_read_bytes_per_step"])

    def test_architecture_variants(self):
        v = self.d["architecture_variants"]
        self.assertEqual(v["looped_kv_bytes_per_token_if_per_pass_cache"], 2 * 131_072)
        self.assertEqual(v["sliding_window_bytes_at_long_context"], 4096 * 131_072)
        self.assertEqual(v["sliding_window_reduction"], 8.0)


class TestLifecycle(Base):
    def replay(self):
        """Re-run the trace with invariant checks after every operation."""
        m = self.mod
        pool = m.ToyBlockPool(8)
        SYS = m.SYS

        def check():
            refs = [0] * 8
            for t in pool.tables.values():
                for b in t:
                    refs[b] += 1
            self.assertEqual(refs, pool.ref)           # ref count == number of table references
            for b in pool.free:
                self.assertEqual(pool.ref[b], 0)       # nothing referenced is on the free queue
            self.assertEqual(len(set(pool.free)), len(pool.free))
            in_use = {b for t in pool.tables.values() for b in t}
            self.assertEqual(in_use & set(pool.free), set())
            self.assertEqual(len(in_use) + len(pool.free), 8)
        pool.arrive("R1", SYS + ["cat", "?"]); check()
        pool.arrive("R2", SYS + ["dog", "food", "?"]); check()
        pool.append("R1", ["A", "1", "."]); check()
        shared = pool.tables["R2"][:2]
        pool.finish("R1"); check()
        for b in shared:                                 # still held by R2: not released
            self.assertNotIn(b, pool.free)
            self.assertEqual(pool.ref[b], 1)
        pool.finish("R2"); check()
        pool.arrive("R3", SYS + ["cat", "?"]); check()
        pool.arrive("R4", ["x%d" % i for i in range(19)]); check()
        return pool

    def test_invariants_hold_through_the_trace(self):
        pool = self.replay()
        self.assertEqual([e for e in pool.events if e[0] == "evict"][0][1], 2)

    def test_handing_out_a_referenced_block_is_impossible(self):
        m = self.mod
        pool = m.ToyBlockPool(4)
        pool.arrive("R1", m.SYS + ["cat", "?"])
        pool.free.insert(0, pool.tables["R1"][0])      # simulate a premature release bug
        with self.assertRaises(AssertionError):
            pool._pop_free()

    def test_last_prompt_token_is_never_a_cache_hit(self):
        m = self.mod
        pool = m.ToyBlockPool(8)
        pool.arrive("R1", m.SYS + ["cat", "?"])
        pool.finish("R1")
        # a block-aligned 8-token prompt matches two cached blocks, but only 4 tokens may hit
        self.assertEqual(pool.arrive("R5", list(m.SYS)), 4)

    def test_snapshots_match_replay_and_counts_are_distinct(self):
        L = self.d["lifecycle"]
        self.assertEqual(L["hits"], {"R1": 0, "R2": 8, "R3": 8})
        s0 = L["snapshots"][0]
        self.assertEqual(s0["tables"], {"R1": [0, 1, 2], "R2": [0, 1, 3]})
        self.assertEqual((s0["unique_physical_blocks"], s0["logical_references"], s0["allocated_slots"],
                          s0["live_tokens"], s0["unique_stored_tokens"]), (4, 6, 16, 21, 13))
        self.assertEqual(L["snapshots"][1]["free_queue"], [5, 6, 7, 4, 2])
        self.assertEqual(L["snapshots"][2]["free_queue"], [5, 6, 7, 4, 2, 3, 1, 0])
        self.assertEqual(L["snapshots"][2]["cached_blocks"], [0, 1, 2])   # idle but still cached
        self.assertEqual(L["snapshots"][3]["tables"], {"R3": [0, 1, 5]})
        self.assertEqual(L["snapshots"][4]["tables"]["R4"], [6, 7, 4, 2, 3])

    def test_copy_on_write_once(self):
        c = self.d["copy_on_write"]
        steps = c["steps"]
        self.assertEqual(c["copies"], 1)
        self.assertEqual(steps[0]["ref"], {"0": 2, "1": 2})
        self.assertEqual(steps[1]["action"], "copy block 1 to 2")
        self.assertEqual(steps[2]["action"], "write in place to block 1")
        self.assertEqual(steps[2]["tables"], {"A1": [0, 2], "A2": [0, 1]})
        self.assertEqual(steps[2]["ref"], {"0": 2, "1": 1, "2": 1})   # full shared block never copied

    def test_radix_versus_hash(self):
        r = self.d["radix"]
        self.assertEqual(r["radix_matched_tokens"], {"A": 0, "B": 7, "C": 6})
        self.assertEqual(r["hash_reusable_tokens"], {"A": 0, "B": 4, "C": 4})
        for name in ("B", "C"):
            self.assertEqual(r["hash_reusable_tokens"][name] % r["toy_block_tokens"], 0)
            self.assertLessEqual(r["hash_reusable_tokens"][name], r["radix_matched_tokens"][name])
        evictable = [n for n in r["nodes"] if n["leaf"] and n["ref"] == 0]
        self.assertEqual([n["id"] for n in evictable], r["evict_order"])
        self.assertEqual([n["tokens"] for n in evictable], [["cat"]])
        for n in r["nodes"]:                            # a parent's ref covers its children's
            kids = [k for k in r["nodes"] if k["parent"] == n["id"]]
            if kids:
                self.assertGreaterEqual(n["ref"], max(k["ref"] for k in kids))

    def test_committed_json_matches_a_fresh_run(self):
        m = self.mod
        cap = m.capacity()
        self.assertEqual(cap, self.cap)
        self.assertEqual(json.loads(json.dumps(m.lifecycle())), self.d["lifecycle"])
        self.assertEqual(json.loads(json.dumps(m.radix())), self.d["radix"])
        self.assertEqual(json.loads(json.dumps(m.questions(cap))), self.d["questions"])


class TestProse(Base):
    def test_chapter_quotes_derived_numbers(self):
        ch = read("chapters", "02-kv-cache-memory.qmd")
        for s in ("128 KiB", "512 MiB", "73.6", "16.06 GB", "4.29 GB", "53.25 GB", "49.59 GiB", "25,391",
                  "450,560", "99 such sequences", "119", "47 blocks", "752 tokens", "753 tokens",
                  "32,768", "10,117", "30.9%", "1,312", "21,339", "10,176", "59 are empty", "99.4%",
                  "1.5 GiB", "768 MiB", "4,096 blocks", "8 GiB", "2,112 blocks", "4.125 GiB", "395", "198",
                  "256 KiB", "20.4–38.2%", "96.3%"):
            self.assertTrue(s in ch, msg=s)

    def test_rounding_table_matches_json(self):
        ch = read("chapters", "02-kv-cache-memory.qmd")
        toks = re.search(r"^\| Retained tokens \|(.+)\|$", ch, re.M).group(1)
        blocks = re.search(r"^\| Blocks \|(.+)\|$", ch, re.M).group(1)
        empty = re.search(r"^\| Empty slots \|(.+)\|$", ch, re.M).group(1)
        cells = lambda s: [int(x.strip().replace(",", "")) for x in s.split("|")]
        self.assertEqual(cells(toks), [r["tokens"] for r in self.d["rounding"]])
        self.assertEqual(cells(blocks), [r["blocks"] for r in self.d["rounding"]])
        self.assertEqual(cells(empty), [r["empty_slots"] for r in self.d["rounding"]])

    def test_answer_key_numbers_and_coverage(self):
        ch = read("chapters", "02-kv-cache-memory.qmd")
        sol = read("solutions", "02-kv-cache-memory-solutions.qmd")
        q = self.d["questions"]
        self.assertEqual(q["q1_concurrency_2048"]["max_sequences"], 198)
        self.assertEqual(q["q1_concurrency_2048"]["headroom_8gib_blocks"], 23_343)
        self.assertEqual(q["q1_concurrency_2048"]["headroom_8gib_max_sequences"], 182)
        self.assertEqual([(r["tokens"], r["blocks"], r["empty_slots"]) for r in q["q2_rounding"]],
                         [(48, 3, 0), (49, 4, 15), (63, 4, 1)])
        for s in ("198", "23,343", "182", "48.95 GB", "15 empty slots", "P2 and P4", "2,112", "395",
                  "4.125 GiB"):
            self.assertTrue(s in sol, msg=s)
        qs = re.findall(r"^(\d)\. \*\*([^*]+)\.\*\*", ch, re.M)
        ans = re.findall(r"^\*\*(\d)\. ([^.]+)\.", sol, re.M)
        self.assertEqual(qs, ans)
        self.assertEqual(len(qs), 5)
        self.assertEqual(sol.count("*Answer.*"), 5)
        self.assertEqual(sol.count("*Common trap:*"), 5)
        # every chapter question prompt is repeated verbatim (bar markup) in the key
        for n, prompt in re.findall(r"^(\d)\. \*\*[^*]+\.\*\* (.+?) \\$", ch, re.M):
            self.assertIn(prompt.replace("$", ""), sol.replace("$", ""), msg=f"Q{n}")

    def test_question2_separates_selection_from_cache_write(self):
        ch = read("chapters", "02-kv-cache-memory.qmd")
        sol = read("solutions", "02-kv-cache-memory-solutions.qmd")
        prompt = ("A sequence has KV entries for exactly 48 processed tokens. Its next token has been "
                  "selected, but no block is free. Can it process that token and append its KV entries?")
        self.assertIn(prompt, ch)
        self.assertIn(prompt, sol)
        self.assertNotIn("can it generate its next token", ch + sol)
        ans = sol[sol.index("**2. Calculation."):sol.index("**3. Debugging.")]
        for phrase in ("logits from which token 49 was selected", "Selecting token 49 stores nothing",
                       "logits for token 50", "fourth block", "must wait"):
            self.assertIn(phrase, ans, msg=phrase)
        # the block arithmetic behind the answer: 48 processed tokens fill 3 blocks; the 49th needs a 4th
        self.assertEqual(self.mod.ceil_div(48, 16), 3)
        self.assertEqual(self.mod.ceil_div(49, 16), 4)
        sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
        from _yaml_lite import safe_load_path
        rec = [q for q in safe_load_path(os.path.join(WB, "questions.yaml"))["questions"]
               if q["id"] == "q-06-kv-cache-memory-002"][0]
        self.assertTrue(rec["prompt"].endswith(prompt))
        self.assertIn("selecting it stores nothing", rec["expected_answer"])

    def test_layout_guards_present(self):
        ch = read("chapters", "02-kv-cache-memory.qmd")
        sol = read("solutions", "02-kv-cache-memory-solutions.qmd")
        self.assertEqual(ch.count("#block(breakable: false)["), 5)
        self.assertEqual(sol.count("#block(sticky: true, width: 100%)["), 6)
        self.assertIsNone(re.search(r"\d'", ch + sol), msg="digit followed by an apostrophe renders as a prime")


if __name__ == "__main__":
    unittest.main()
