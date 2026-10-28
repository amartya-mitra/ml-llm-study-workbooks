#!/usr/bin/env python3
"""Workbook 06, Chapter 2 worked example: a KV-cache capacity plan, block
rounding and fragmentation, and toy simulations of paged block sharing,
copy-on-write, prefix reuse and eviction.

Every input is ILLUSTRATIVE and every output is DERIVED (analytical or
simulated from the stated rules); nothing here is a measurement. The model
and device are Chapter 1's illustrative ones, imported read-only from that
chapter's worked example so the two chapters agree numerically.

Conventions (stated once, used everywhere):
  * Retained length S of a sequence = prompt tokens + output tokens whose
    keys and values have been written. The token processed in the current
    step writes its own K/V in that step, so a step needs a slot for it.
  * Logical KV bytes = S x per-token KV bytes (Workbook 04's M_KV for one
    sequence): no allocator overhead, padding or metadata.
  * Allocated slots = blocks x block size; a block is the unit the
    allocator hands out. Unique physical blocks, logical references
    (block-table entries), allocated slots and live tokens are counted
    separately.
  * GB = 1e9 bytes; GiB = 2**30 bytes. Both are reported where it matters.
  * The KV budget follows the shape vLLM v0.32.0 uses (requested =
    ceil(total x gpu_memory_utilization); KV = requested - non-KV memory),
    but the non-KV term here is weights plus an ILLUSTRATIVE runtime
    headroom, not a profiled value.
  * Toy lifecycle and radix-tree traces use a block size of 4 tokens and
    word "tokens" so a figure can show them; they illustrate mechanisms,
    not any engine's exact internal state.

Run: python3 kv_cache_memory.py  (writes kv_cache_memory.json)
"""
import hashlib
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inference_workload_and_metrics import HARDWARE, MODEL, kv_bytes_per_token, linear_params  # noqa: E402

GIB = 2 ** 30
GB = 1e9

# ---- illustrative inputs -------------------------------------------------
GPU_MEMORY_UTILIZATION = 0.92          # vLLM v0.32.0's default value, used here as an illustrative input
RUNTIME_HEADROOM_BYTES = 4 * GIB       # illustrative: activations, workspaces, graph buffers (not profiled)
BLOCK_TOKENS = 16                      # vLLM's default block size (paper Sec. 7.2; v0.32.0 config)
MAX_MODEL_LEN = 4096                   # per-request maximum for the reservation comparison
# snapshot of eight running requests: (current retained length, final length)
RESERVATION_WORKLOAD = [(312, 400), (1800, 2300), (4000, 4096), (97, 120),
                        (640, 900), (2049, 2049), (16, 64), (1203, 1500)]
ROUNDING_LENGTHS = [1, 15, 16, 17, 33, 4096, 4097]
# prefix sharing at scale (applied exercise)
SHARED_PREFIX_TOKENS = 1024
UNIQUE_TOKENS_PER_REQUEST = 1024       # unique prompt suffix + output, per request
SHARING_REQUESTS = 32
LOOPED_PASSES = 2                      # looped-depth variant: each pass keeps its own cache
SLIDING_WINDOW = 4096                  # sliding-window variant (an architectural property)
LONG_CONTEXT = 32768


def ceil_div(a, b):
    return -(-a // b)


# ---- A. capacity and allocation -------------------------------------------
def capacity():
    p = linear_params(MODEL)
    weights = (p["linear_total"] + p["input_embedding_stored_not_read"]) * MODEL["bytes_per_weight"]
    total = HARDWARE["mem_capacity_bytes"]
    requested = math.ceil(total * GPU_MEMORY_UTILIZATION)
    kv_budget = requested - weights - RUNTIME_HEADROOM_BYTES
    per_token = kv_bytes_per_token(MODEL)
    block_bytes = BLOCK_TOKENS * per_token
    num_blocks = kv_budget // block_bytes
    blocks_per_full_seq = ceil_div(MAX_MODEL_LEN, BLOCK_TOKENS)
    full_seqs = num_blocks // blocks_per_full_seq
    rem_blocks = num_blocks - full_seqs * blocks_per_full_seq
    return {
        "device_bytes": total, "gpu_memory_utilization": GPU_MEMORY_UTILIZATION,
        "requested_bytes": requested, "weights_stored_bytes": weights,
        "runtime_headroom_bytes": RUNTIME_HEADROOM_BYTES, "kv_budget_bytes": kv_budget,
        "kv_budget_gb": kv_budget / GB, "kv_budget_gib": kv_budget / GIB,
        "kv_bytes_per_token": per_token, "block_tokens": BLOCK_TOKENS, "block_bytes": block_bytes,
        "num_blocks": num_blocks, "unusable_tail_bytes": kv_budget - num_blocks * block_bytes,
        "blocks_per_full_sequence": blocks_per_full_seq,
        "max_full_length_sequences": full_seqs, "remaining_blocks": rem_blocks,
        # exact fit: one more sequence of exactly rem_blocks x 16 tokens fits; one token more does not
        "exact_fit_extra_tokens": rem_blocks * BLOCK_TOKENS,
        "one_over_extra_tokens": rem_blocks * BLOCK_TOKENS + 1,
        "one_over_blocks_needed": ceil_div(rem_blocks * BLOCK_TOKENS + 1, BLOCK_TOKENS),
        "logical_only_full_seqs": kv_budget // (MAX_MODEL_LEN * per_token),
    }


def rounding():
    rows = []
    for n in ROUNDING_LENGTHS:
        blocks = ceil_div(n, BLOCK_TOKENS)
        rows.append({"tokens": n, "blocks": blocks, "slots": blocks * BLOCK_TOKENS,
                     "empty_slots": blocks * BLOCK_TOKENS - n})
    return rows


def reservation_vs_paged():
    per_token = kv_bytes_per_token(MODEL)
    rows, tot = [], {"used": 0, "reserved_future": 0, "internal": 0, "paged_slots": 0}
    for cur, final in RESERVATION_WORKLOAD:
        used, future, internal = cur, final - cur, MAX_MODEL_LEN - final
        paged = ceil_div(cur, BLOCK_TOKENS) * BLOCK_TOKENS
        rows.append({"current": cur, "final": final, "used": used, "reserved_future": future,
                     "internal_fragmentation": internal, "paged_slots": paged,
                     "paged_empty_slots": paged - cur})
        tot["used"] += used; tot["reserved_future"] += future
        tot["internal"] += internal; tot["paged_slots"] += paged
    reserved_total = MAX_MODEL_LEN * len(RESERVATION_WORKLOAD)
    return {
        "requests": rows, "reserved_slots_total": reserved_total, "used_slots": tot["used"],
        "reserved_for_future_slots": tot["reserved_future"], "internal_fragmentation_slots": tot["internal"],
        "reservation_used_fraction": tot["used"] / reserved_total,
        "paged_allocated_slots": tot["paged_slots"], "paged_empty_slots": tot["paged_slots"] - tot["used"],
        "paged_used_fraction": tot["used"] / tot["paged_slots"],
        "reserved_bytes": reserved_total * per_token, "paged_bytes": tot["paged_slots"] * per_token,
        "used_bytes": tot["used"] * per_token,
    }


def external_fragmentation():
    """Toy contiguous arena of 16 units (one unit = 256 MiB of KV). Requests
    reserve contiguous runs; after some finish, free memory is scattered."""
    unit = 256 * 2 ** 20
    arena = [None] * 16
    allocs = [("a", 3), ("b", 2), ("c", 4), ("d", 2), ("e", 3), ("f", 2)]
    pos = 0
    for name, size in allocs:
        for i in range(pos, pos + size):
            arena[i] = name
        pos += size
    for name in ("b", "d", "f"):           # three requests finish
        arena = [None if x == name else x for x in arena]
    runs, run = [], 0
    for x in arena:
        if x is None:
            run += 1
        else:
            if run:
                runs.append(run)
            run = 0
    if run:
        runs.append(run)
    need = 3
    return {"unit_bytes": unit, "arena": arena, "free_units": arena.count(None),
            "free_runs": runs, "largest_free_run": max(runs), "request_units": need,
            "fits_contiguous": max(runs) >= need, "fits_paged": arena.count(None) >= need}


# ---- B. sharing and lifecycle (toy block size 4) --------------------------
TOY_BLOCK = 4


class ToyBlockPool:
    """A tiny model of vLLM-style prefix caching: chained hashes of full
    blocks, per-block reference counts, a free queue whose head is reused
    first (evicting any cached content), and requests freed in reverse
    block order. Partial blocks are never cached. Not an engine."""

    def __init__(self, n_blocks):
        self.free = list(range(n_blocks))
        self.ref = [0] * n_blocks
        self.tokens = [[] for _ in range(n_blocks)]
        self.hash_of = [None] * n_blocks
        self.cached = {}                    # hash -> block id
        self.tables = {}                    # request -> list of block ids
        self.lengths = {}
        self.events = []

    @staticmethod
    def _hash(parent, toks):
        return hashlib.sha256(repr((parent, tuple(toks))).encode()).hexdigest()[:12]

    def _pop_free(self):
        b = self.free.pop(0)
        assert self.ref[b] == 0, "a referenced block must never be handed out"
        if self.hash_of[b] is not None:     # reusing a cached block evicts it
            self.events.append(("evict", b, self.hash_of[b]))
            del self.cached[self.hash_of[b]]
            self.hash_of[b] = None
        self.tokens[b] = []
        return b

    def _maybe_cache(self, req, idx):
        b = self.tables[req][idx]
        if len(self.tokens[b]) == TOY_BLOCK and self.hash_of[b] is None:
            parent = self.hash_of[self.tables[req][idx - 1]] if idx else None
            h = self._hash(parent, self.tokens[b])
            if h not in self.cached:
                self.cached[h] = b
                self.hash_of[b] = h

    def arrive(self, req, prompt):
        hits, parent = [], None
        max_hit = len(prompt) - 1           # the last prompt token is always recomputed for its logits
        for i in range(max_hit // TOY_BLOCK):
            h = self._hash(parent, prompt[i * TOY_BLOCK:(i + 1) * TOY_BLOCK])
            if h not in self.cached:
                break
            hits.append(self.cached[h]); parent = h
        for b in hits:                      # touch: take a reference, leave the free queue
            if self.ref[b] == 0:
                self.free.remove(b)
            self.ref[b] += 1
        self.tables[req] = list(hits)
        self.lengths[req] = len(hits) * TOY_BLOCK
        self.events.append(("arrive", req, len(hits) * TOY_BLOCK))
        self.append(req, prompt[len(hits) * TOY_BLOCK:])
        return len(hits) * TOY_BLOCK

    def append(self, req, toks):
        for t in toks:
            if self.lengths[req] % TOY_BLOCK == 0:
                b = self._pop_free()
                self.ref[b] = 1
                self.tables[req].append(b)
            b = self.tables[req][-1]
            assert self.ref[b] == 1, "writes go only to a block this request owns alone"
            self.tokens[b].append(t)
            self.lengths[req] += 1
            self._maybe_cache(req, len(self.tables[req]) - 1)

    def finish(self, req):
        for b in reversed(self.tables[req]):
            self.ref[b] -= 1
            assert self.ref[b] >= 0
            if self.ref[b] == 0:
                self.free.append(b)
        del self.tables[req], self.lengths[req]
        self.events.append(("finish", req))

    def snapshot(self, label):
        in_use = sorted({b for t in self.tables.values() for b in t})
        return {
            "label": label,
            "tables": {r: list(t) for r, t in self.tables.items()},
            "lengths": dict(self.lengths),
            "ref": {b: self.ref[b] for b in range(len(self.ref)) if self.ref[b] or self.hash_of[b]},
            "cached_blocks": sorted(self.cached.values()),
            "free_queue": list(self.free),
            "unique_physical_blocks": len(in_use),
            "logical_references": sum(len(t) for t in self.tables.values()),
            "allocated_slots": len(in_use) * TOY_BLOCK,
            "live_tokens": sum(self.lengths.values()),
            "unique_stored_tokens": sum(len(self.tokens[b]) for b in in_use),
            "block_tokens": {b: list(self.tokens[b]) for b in in_use},
        }


SYS = ["<s>", "You", "are", "a", "helpful", "bot", ":", "Q"]   # 8 tokens = two full toy blocks


def lifecycle():
    pool = ToyBlockPool(8)
    snaps = []
    hit1 = pool.arrive("R1", SYS + ["cat", "?"])
    hit2 = pool.arrive("R2", SYS + ["dog", "food", "?"])
    snaps.append(pool.snapshot("R1 and R2 running, sharing two prefix blocks"))
    pool.append("R1", ["A", "1", "."])
    pool.finish("R1")
    snaps.append(pool.snapshot("R1 finished; shared blocks still held by R2"))
    pool.finish("R2")
    snaps.append(pool.snapshot("both finished; cached blocks idle in the free queue"))
    hit3 = pool.arrive("R3", SYS + ["cat", "?"])
    snaps.append(pool.snapshot("R3 reuses the idle cached prefix"))
    pool.arrive("R4", ["x%d" % i for i in range(19)])
    snaps.append(pool.snapshot("R4 needs five new blocks; taking cached P2 evicts it"))
    return {"block_tokens": TOY_BLOCK, "pool_blocks": 8, "hits": {"R1": hit1, "R2": hit2, "R3": hit3},
            "snapshots": snaps, "events": [list(e) for e in pool.events]}


def copy_on_write():
    """PagedAttention paper Sec. 4.4 mechanism (parallel sampling): two
    samples share a prompt whose last block is partly filled."""
    ref = {0: 2, 1: 2}
    tables = {"A1": [0, 1], "A2": [0, 1]}
    fill = {0: 4, 1: 2}
    steps = [{"step": "fork", "tables": {k: list(v) for k, v in tables.items()}, "ref": dict(ref)}]
    next_free, copies = 2, 0
    for sample in ("A1", "A2"):
        last = tables[sample][-1]
        if ref[last] > 1:                   # shared partial block: copy before writing
            new = next_free; next_free += 1
            ref[last] -= 1; ref[new] = 1; fill[new] = fill[last]
            tables[sample][-1] = new
            copies += 1
            action = f"copy block {last} to {new}"
        else:
            action = f"write in place to block {last}"
        fill[tables[sample][-1]] += 1
        steps.append({"step": f"{sample} writes", "action": action,
                      "tables": {k: list(v) for k, v in tables.items()}, "ref": dict(ref)})
    return {"block_tokens": TOY_BLOCK, "prompt_tokens": 6, "steps": steps, "copies": copies}


class RadixNode:
    def __init__(self, label):
        self.label, self.children, self.ref, self.last = label, {}, 0, 0


def radix():
    """Toy radix tree with one-token pages (SGLang's RadixAttention):
    edges carry token runs, nodes carry reference counts, and an LRU policy
    evicts unreferenced leaves first."""
    requests = [("A", SYS[:6] + ["Translate", "cat"], 1, "finished"),
                ("B", SYS[:6] + ["Translate", "dog"], 2, "running"),
                ("C", SYS[:6] + ["Summarize", "this"], 3, "running")]
    root = RadixNode([])

    def insert(seq, t, running):
        node, i, matched = root, 0, 0
        path = []
        while i < len(seq):
            child = node.children.get(seq[i])
            if child is None:
                new = RadixNode(seq[i:]); node.children[seq[i]] = new; node = new; path.append(node)
                break
            k = 0
            while k < len(child.label) and i + k < len(seq) and child.label[k] == seq[i + k]:
                k += 1
            if k < len(child.label):        # split the edge
                mid = RadixNode(child.label[:k]); mid.ref, mid.last = child.ref, child.last
                child.label = child.label[k:]; mid.children[child.label[0]] = child
                node.children[seq[i]] = mid; child = mid
            matched += k; i += k; node = child; path.append(node)
        for n in path:
            n.last = t
            if running:
                n.ref += 1
        return matched

    matched = {}
    for name, seq, t, state in requests:
        matched[name] = insert(seq, t, state == "running")

    nodes, evict_order = [], []

    def walk(node, depth, parent_id):
        for key in sorted(node.children):
            child = node.children[key]
            nid = len(nodes)
            nodes.append({"id": nid, "parent": parent_id, "tokens": child.label, "ref": child.ref,
                          "last_access": child.last, "leaf": not child.children, "depth": depth})
            walk(child, depth + 1, nid)
    walk(root, 0, None)
    evictable = sorted([n for n in nodes if n["leaf"] and n["ref"] == 0], key=lambda n: n["last_access"])
    evict_order = [n["id"] for n in evictable]
    # full-block hashing (toy block 4) on the same requests: reusable prefix = full blocks
    # matching an earlier request, capped at prompt length - 1
    hash_reuse = {}
    seen = []
    for name, seq, _, _ in requests:
        best = 0
        for prev in seen:
            k = 0
            while k < min(len(prev), len(seq)) and prev[k] == seq[k]:
                k += 1
            best = max(best, k)
        hash_reuse[name] = min((best // TOY_BLOCK) * TOY_BLOCK, (len(seq) - 1) // TOY_BLOCK * TOY_BLOCK)
        seen.append(seq)
    return {"nodes": nodes, "evict_order": evict_order, "radix_matched_tokens": matched,
            "hash_reusable_tokens": hash_reuse, "toy_block_tokens": TOY_BLOCK,
            "requests": [{"name": n, "tokens": s, "state": st} for n, s, _, st in requests]}


# ---- C. sharing at scale, looped depth, sliding window -----------------------
def sharing_at_scale(cap):
    per_token = kv_bytes_per_token(MODEL)
    total_len = SHARED_PREFIX_TOKENS + UNIQUE_TOKENS_PER_REQUEST
    blocks_each = ceil_div(total_len, BLOCK_TOKENS)
    shared_blocks = SHARED_PREFIX_TOKENS // BLOCK_TOKENS
    unique_blocks = ceil_div(UNIQUE_TOKENS_PER_REQUEST, BLOCK_TOKENS)
    no_share_blocks = SHARING_REQUESTS * blocks_each
    share_blocks = shared_blocks + SHARING_REQUESTS * unique_blocks
    return {
        "requests": SHARING_REQUESTS, "shared_prefix_tokens": SHARED_PREFIX_TOKENS,
        "unique_tokens_per_request": UNIQUE_TOKENS_PER_REQUEST,
        "blocks_without_sharing": no_share_blocks, "blocks_with_sharing": share_blocks,
        "bytes_without_sharing": no_share_blocks * cap["block_bytes"],
        "bytes_with_sharing": share_blocks * cap["block_bytes"],
        "logical_references_with_sharing": no_share_blocks,
        # every request's attention still reads its whole retained history each decode step
        "decode_read_bytes_per_step": SHARING_REQUESTS * total_len * per_token,
        "max_requests_without_sharing": cap["num_blocks"] // blocks_each,
        "max_requests_with_sharing": (cap["num_blocks"] - shared_blocks) // unique_blocks,
        "prefill_tokens_skipped_per_hit": SHARED_PREFIX_TOKENS,
    }


def architecture_variants():
    per_token = kv_bytes_per_token(MODEL)
    return {
        "looped_passes": LOOPED_PASSES,
        "looped_kv_bytes_per_token_if_per_pass_cache": LOOPED_PASSES * per_token,
        "sliding_window": SLIDING_WINDOW, "long_context": LONG_CONTEXT,
        "full_attention_bytes_at_long_context": LONG_CONTEXT * per_token,
        "sliding_window_bytes_at_long_context": min(LONG_CONTEXT, SLIDING_WINDOW) * per_token,
        "sliding_window_reduction": LONG_CONTEXT / min(LONG_CONTEXT, SLIDING_WINDOW),
    }


def questions(cap):
    per_token = kv_bytes_per_token(MODEL)
    q1_len = 2048
    q1_blocks = ceil_div(q1_len, BLOCK_TOKENS)
    budget_8 = cap["requested_bytes"] - cap["weights_stored_bytes"] - 8 * GIB
    blocks_8 = budget_8 // cap["block_bytes"]
    return {
        "q1_concurrency_2048": {"blocks_per_sequence": q1_blocks, "max_sequences": cap["num_blocks"] // q1_blocks,
                                "logical_bytes_per_sequence": q1_len * per_token,
                                "headroom_8gib_budget_bytes": budget_8, "headroom_8gib_blocks": blocks_8,
                                "headroom_8gib_max_sequences": blocks_8 // q1_blocks},
        "q2_rounding": [{"tokens": n, "blocks": ceil_div(n, BLOCK_TOKENS),
                         "empty_slots": ceil_div(n, BLOCK_TOKENS) * BLOCK_TOKENS - n} for n in (48, 49, 63)],
    }


def main():
    cap = capacity()
    result = {
        "labels": {"inputs": "illustrative", "outputs": "derived (analytical or simulated), not measured"},
        "capacity": cap, "rounding": rounding(), "reservation_vs_paged": reservation_vs_paged(),
        "external_fragmentation": external_fragmentation(), "lifecycle": lifecycle(),
        "copy_on_write": copy_on_write(), "radix": radix(), "sharing_at_scale": sharing_at_scale(cap),
        "architecture_variants": architecture_variants(), "questions": questions(cap),
    }
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kv_cache_memory.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
