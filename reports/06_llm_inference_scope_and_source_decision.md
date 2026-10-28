# Workbook 06 — LLM Inference Engineering: Scope and Source Decision

Date: 2026-10-28
Baseline commit: `857d103a0f388b6a62edbc95039e153e22d9ae15` (= `origin/main`)
Scope: repository discovery, chapter-structure decision and source
verification only. **No chapter prose, `index.qmd`, scaffold, figure,
PDF, RC or canonical artifact was created.** This report is the
approval gate; scaffolding starts only after the chapter list below is
approved.

---

## 1. Starting state (observed, not inferred)

| Item | Observed |
|---|---|
| Branch / HEAD / tree | `main` at `857d103`, equal to `origin/main`; working tree clean |
| Protection | `safetyctl self-check` → `PROTECTED` |
| `workbooks/06-llm-inference/` | only an empty `.gitkeep` (Sep 22): no index, chapters, contracts, data or figures |
| `config/project.yaml` | `06-llm-inference`, "LLM Inference Engineering", status `not started` |
| `config/chapter-status-registry.yaml` | no `workbooks:` or `publications:` entry for 06 |
| README | 06 listed as "not started (empty directory)" |
| `scripts/workbook_qa.py` `WORKBOOK_REGISTRY` | entries for 04 and 05 only |
| Roadmap (`config/series-topic-roadmap.yaml`) | 06 is the **primary home of speculative decoding** (13 required concepts; src-44/45 co-foundational; vendor docs only as implementation companions); brief 06 treatment of MTP as a draft source and of looped-depth cache **and latency** consequences |
| Coverage matrix (before) | 06: src-11 (primary), src-10, src-12, src-44 and src-45 (primary), src-49 |
| Published artifacts | WB04 v1.0.0, WB05 v1.0.0, TSFM addendum v1.0.0 and v1.1.0 — untouched |

Source IDs: the registry ended at src-72; this task adds src-73 – src-95
(23 entries) and updates reused entries (§6).

## 2. Recommended identity

| Field | Recommendation |
|---|---|
| Title | **LLM Inference Engineering** (as in `config/project.yaml`) |
| Source location | `workbooks/06-llm-inference/` |
| Canonical PDF | **`outputs/06-llm-inference-workbook.pdf`** — the WB05 short-slug pattern (`outputs/05-llm-training-workbook.pdf`) adopted as the forward convention in the WB05 scope report |
| Future release | tag `workbook-06-v1.0.0`, asset `06-llm-inference-workbook.pdf` |
| Page budget | **target 72, hard ceiling 78** (see §5.3; needs approval) |

## 3. Coverage bridge to Workbooks 04–05

Mapped from the frozen chapter text; every file:line below was
spot-checked.

**Already taught — 06 recaps, never re-derives:**

| Topic | Where (frozen) | What 06 reuses |
|---|---|---|
| KV-cache size | WB04 ch3:122-125 `@eq-kv-cache` | `M_KV = 2·B·S·L·H_kv·d_head·bytes_per_elem`, total across layers, a **logical minimum** with an explicit exclusion list (allocator, paging, fragmentation, workspaces, padding, sharding, prefix sharing, cache quantization) — the list 06 ch2 fills in |
| MQA / GQA / MLA | WB04 ch3, ch4 (`@eq-mla-cache`, no factor 2) | cache sizes; fewer KV heads cut memory and bandwidth, not query FLOPs |
| Sliding window | WB04 ch4:75-103 | bounded cache only under strict eviction; rolling-buffer mechanics not taught |
| Prefill vs decode | WB04 ch1, ch7:57-68 | qualitative ("often compute-heavy" / "often memory-bandwidth-sensitive"; "tendencies, not laws"; larger batches shift decode toward compute-bound, ch7:64-66) |
| Arithmetic intensity, MFU | WB05 ch5:325-359 | training definitions; roofline named, never drawn |
| FlashAttention | WB05 ch5:198-213 | training framing: avoids materializing S/P via tiling |
| TP / PP / EP | WB05 ch4 | training mechanisms and communication only |
| MoE | WB04 ch5 | total vs active parameters; serving configuration out of scope (ch5:253) |
| MTP | WB05 ch2:167-200 | both designs; heads discarded at inference by default |
| Looped depth | WB04 ch8 | cache may scale with effective block applications unless reuse is designed in |
| Memory kinds | WB05 ch5:82-115 | logical tensor bytes, analytical estimate, `max_memory_allocated`, `max_memory_reserved`, sampled `nvidia-smi` |
| Report reading | WB05 ch6 | configured / observed / derived; comparability controls; competing diagnoses |

**Explicit deferrals to 06:** speculative decoding (WB04 ch7:83-89,
ch8:119-125; WB05 ch2:184-185); MTP as a draft source; looped-depth
serving; chunked prefill (forward reference, WB04 ch3:143-145);
serving-engine implementation and inference-engine configuration (WB04
ch7:182-184, ch5:253).

**Gaps neither workbook covers (06's content):** serving metrics and
SLOs; decode as a *weight-read* bandwidth problem (WB04 frames decode
only as KV re-reads); a drawn roofline; inference memory and concurrency
planning; paging, continuous batching, chunked prefill, prefix caching,
preemption, disaggregation; online softmax and split-KV decode kernels;
quantization; sampling transforms; inference-time parallelism;
speculative decoding.

**Statements 06 must reconcile explicitly (without editing frozen text):**
1. WB04 ch1:350-353 ("A 50-token response requires at least 50 forward
   passes") and ch1:403 ("at least N forward passes") — true for
   one-token-per-pass decoding; speculative decoding verifies several
   drafted tokens per target pass (ch6 states when).
2. WB04 ch1:355-357 (decode cost "almost independently" of prompt
   length) vs ch4:64-66 (per-step cost grows with S) — ch1 separates
   weight reads (constant in S) from KV reads (linear in S).
3. "Goodput" appears only as a WB04 ch7 learning objective — ch1 defines
   it, with its competing definitions (§4).
4. MFU: WB05 ch5:327-330 counts forward **and** backward FLOPs for
   training; src-78 defines inference MFU on forward FLOPs against peak.

**Notation:** WB04's symbols (`B, S, L, H_q, H_kv, d_head, d_model, T_q,
bytes_per_elem, d_c, d_rope`), with the mapping to WB05's (`bs, seq, h,
n_heads, N`) stated once. GiB/MiB for memory, GB/s for bandwidth. Avoid
two WB04 slips (ch7 "five" vs caption "six" resources; ch7:52 cites a
nonexistent recurrent-state formula).

**Number labels (one vocabulary, applied per number):** *reported* (a
source states it, with its conditions), *derived* (computed in the
workbook from stated definitions, including analytical estimates), and
*illustrative* (chosen for teaching). Measured values from a source are
"reported"; the workbook measures nothing.

## 4. Technical contracts

| Distinction | Owner | Contract (source) |
|---|---|---|
| TTFT / inter-token latency / E2E / throughput | ch1 defines; ch7 measures | Definitions differ and are stated per use. **TTFT:** from request arrival incl. queueing (src-75); prefill duration with queueing noted separately (src-76); client send → first streamed chunk (src-82, vLLM v0.32.0); MLPerf: "latency of the first token" (src-81). **Inter-token:** TBT per gap evaluated at P99 (src-75); TPOT per-request average excluding the first token (src-76; src-82 computes `(latency − TTFT)/(output_tokens − 1)`); MLPerf TPOT "the average interval between all the tokens generated" (src-81, as written); ITL per streamed chunk (src-82), which the vLLM docs say exceeds TPOT under speculative decoding (several tokens per chunk). **E2E:** E2E = TTFT + TPOT·(N_out − 1) under the src-76/src-82 convention. |
| req/s, tok/s, concurrency, batch size | ch1; applied in ch3, ch7 | Throughput as req/s, output tok/s, total tok/s (src-82). Goodput: max rate meeting an SLO-attainment target (src-76), "capacity" (src-75), per-run good requests/s (src-82), MLPerf Server QPS (src-80/81). Concurrency (requests in flight) ≠ per-iteration batch, counted in tokens or sequences (`max_num_batched_tokens`, `max_num_seqs`, src-82). |
| Logical vs allocated/reserved vs observed memory | ch2 | WB05's five kinds. WB04 `M_KV` is logical; vLLM's KV budget = `gpu_memory_utilization` × total − **profiled** non-KV memory, measured at startup (src-82); `nvidia-smi` is device-level observation. |
| Prefill vs decode cost and its assumptions | ch1 | Roofline: attainable = min(peak compute, peak bandwidth × operational intensity) (src-79). **Linear layers:** compute-bound iff the per-step *token* batch (B·T_q) exceeds B_crit ≈ C/W_hbm × (bits/param ÷ bits/activation) (src-10, derived); so decode linear layers are bandwidth-bound only while B·T_q < B_crit, and the bound ignores KV bytes, so long-context steps can stay bandwidth-bound beyond it. **Attention:** intensity ST/(S+T) per KV head in src-10's MHA analysis, ≈ 1 at decode; with GQA each KV head serves H_q/H_kv query heads, so decode attention intensity is ≈ H_q/H_kv (≈ 4 for H_q = 32, H_kv = 8) and higher for MLA — still independent of batch, because KV is not shared across sequences. Weights dominate decode traffic at small batch, KV at long context and large batch (src-78). All such numbers are derived and carry hardware/workload assumptions. |
| Exact acceleration vs numerics/quality-changing | ch4, ch5, ch6 | **Same mathematics, different IO or schedule:** FlashAttention-1/2, FA-3 FP16, Flash-Decoding (src-55, 83, 85), paging and prefix reuse (src-73, 77). "Exact" means mathematically equivalent, **not bit-identical**: reduction order, batch shape and chunking change floating-point results; vLLM v0.32.0 docs note that batch-size changes may vary logprobs (src-82, speculative_decoding/README.md:220), and prefix-cached KV was computed under a different batch/chunk shape. **Changes numerics or quality:** all quantization (src-86–92), FA-3 FP8 (src-84), Medusa typical acceptance (src-93). |
| Speculative decoding: correctness vs speedup | ch6 | **Notation first:** 06 adopts src-44's letters (p = target, q = draft); src-45 writes the target as q and the draft as p. **Correctness:** accept a drafted token with probability min(1, p(x)/q(x)), else resample from norm(max(0, p − q)) (src-44 §2.3, Alg. 1, App. A.1), where p and q are the distributions *after* the sampling transform — src-44 §2.2 casts argmax, top-k, nucleus and temperature as "standard sampling from an adjusted probability distribution", and src-45 applies the transforms before rejection; the guarantee holds "within hardware numerics" (src-45 Thm 1); vLLM v0.32.0: "theoretically lossless up to the precision limits of hardware numerics" (src-82). **Speedup:** E[tokens/iteration] = (1 − α^{γ+1})/(1 − α) assuming i.i.d. acceptance; walltime factor (1 − α^{γ+1})/((1 − α)(γc + 1)) assuming γ+1 parallel target evaluations cost no extra walltime (src-44 Eq. 1, Thm 3.8); useful when bandwidth-bound with spare compute (src-44 §1, §6); reported gains are batch-1 (src-44, src-45) and shrink as batch grows (src-94 §4.4). **Exactness belongs to the verification rule, not the draft source.** |
| Kernel efficiency vs end-to-end serving | ch4, ch7 | Kernel results (FA-2 % of peak; FA-3 TFLOP/s; Flash-Decoding 50× attention micro-benchmark; KVQuant 1.2–1.7× matvec) are not end-to-end; inference MFU is defined against peak with no memory or communication overhead (src-78). |
| Reported vs derived vs illustrative | all; ch7 owns | §3 label vocabulary; vendor speed claims stay attributed with their (possibly missing) conditions, e.g. DeepSeek-V3's 1.8× TPS (src-33 §5.4.3). |

No optimization is presented as universally faster or more accurate;
each chapter carries a "when it helps / when it does not" table.

## 5. Chapter structure (recommended)

### 5.1 Comparison with the proposed outline

Keep **seven chapters**, with these changes:

1. **Ch1 owns the metric contract and the roofline**; ch7 measures what
   ch1 defines, and ch3 applies SLOs and goodput.
2. **A short sampling primer in ch1** (logits → transformed distribution),
   needed by ch6's correctness condition; no frozen chapter teaches it.
3. **Ch4 renamed and bounded** to "Efficient execution: attention kernels
   and inference parallelism"; "device placement" folds into the
   parallelism section. Ch4 covers layouts *within one deployment*; ch3
   covers separate prefill and decode pools.
4. **Disaggregation and preemption policy in ch3** (scheduling decisions);
   ch2 explains the memory mechanics of preemption and cross-references ch3.
5. **MoE and long-context serving are sections**, not chapters (EP in ch4;
   context ceilings in ch2; split-KV in ch4).
6. **Order follows an exactness axis:** ch2–4 mathematically equivalent
   methods, ch5 numerics-changing methods, ch6 distribution-preserving
   under stated conditions, ch7 measurement. FA-3 FP8 appears in ch4 only
   as a pointer to ch5; no ch4 question depends on FP8 numerics.
7. **Looped depth** (roadmap brief): cache consequence in ch2's technical
   core, latency consequence (decode cost does not shrink with fewer
   distinct parameters) as one paragraph in ch1.

**Out of scope (front matter):** structured/constrained decoding and
SGLang's frontend language; LoRA/multi-adapter serving (WB07); multimodal
serving; framework surveys (one representative engine, vLLM v0.32.0,
pinned); CUDA programming; hardware purchasing; QAT and FP8 training;
FP4/MX formats and EAGLE-2/3 (not registered; mention only if registered
at drafting time).

### 5.2 Chapters

Skeleton per chapter, as the WB05 contracts require: Learning objectives
→ Why this matters → **Mental model or analogy** → **Visual overview** →
Technical core → Worked example → Compare and contrast → Check your
understanding (**5 questions**, as WB05) → Applied exercise → Interview
lens → Chapter recap → Sources and further reading → Answer Key. Every
worked example is computed by a small deterministic script under
`data/worked-examples/`; every figure is generated from data by a script
beside its rendered SVG.

**Ch1 — The inference workload: prefill, decode, roofline and the
latency–throughput trade-off** (≈11 pp)
- Outcomes: classify linear and attention work at prefill and decode;
  place steps on a roofline; compute a step-time lower bound; define
  TTFT/TBT/TPOT/ITL/E2E, throughput and goodput with their source
  variants; explain batch size as a latency–throughput knob; state why
  looped depth does not cut decode cost.
- Recap: WB04 ch1/ch7 prefill–decode; WB05 ch5 intensity and MFU.
- Boundaries: scheduling → ch3; kernels → ch4.
- Worked example: illustrative 8B-class GQA model (WB04 base config,
  H_q = 32, H_kv = 8) on an illustrative accelerator (round numbers,
  labelled) at fixed S: weight bytes, per-sequence KV, B_crit, and
  step time ≥ max(FLOPs/C, (weight bytes + B·KV bytes)/W) at B = 1, 16,
  256 (derived, src-10 form).
- Figures: roofline with prefill/decode points; one-request timeline
  (queue → prefill → decode) with TTFT/TPOT marked; analytical
  latency–throughput frontier over batch size.
- Sources: src-78, src-79, src-10, src-75, src-76, src-81, src-82,
  src-44 §2.2 (sampling as an adjusted distribution).

**Ch2 — KV-cache memory: capacity, paging, prefix reuse and eviction**
(≈9 pp)
- Outcomes: plan max concurrency from a memory budget; explain
  reservation, internal and external fragmentation; trace block tables
  and copy-on-write; compare full-block hashing with radix-tree prefix
  reuse; explain swap vs recompute preemption and version drift; state
  the looped-depth cache consequence.
- Recap: WB04 `@eq-kv-cache`, MQA/GQA/MLA, sliding windows (ch4) and
  looped depth (ch8); WB05 memory kinds.
- Boundaries: KV quantization → ch5; cross-machine transfer and
  preemption policy → ch3.
- Worked example: concurrency = (budget − weights − profiled non-KV
  memory) / per-sequence KV; block-size-16 waste for a few lengths;
  prefix hit-rate savings (derived/illustrative, per number).
- Figures: logical → physical block table; prefix tree with shared
  blocks.
- Questions include prefix-cache correctness conditions: identical tokens
  *and* extra keys (LoRA, multimodal inputs, cache salt; src-82), and why
  reuse is mathematically but not bitwise identical.
- Sources: src-73, src-77, src-82, src-10.

**Ch3 — Serving and scheduling: continuous batching, chunked prefill and
disaggregation** (≈9 pp)
- Outcomes: contrast request-level vs iteration-level batching; explain
  selective batching; diagnose generation stalls; weigh chunked prefill
  against disaggregation and state where the sources disagree; apply SLO
  attainment and goodput; place preemption policy.
- Recap: ch1 metrics; ch2 paging and preemption mechanics.
- Boundaries: no queueing theory; no autoscaling.
- Worked example: hand-scheduled toy trace (4 requests) under static,
  iteration-level, chunked-prefill and disaggregated policies, with a
  stated illustrative KV-transfer time; TTFT, TBT and SLO attainment
  computed per policy.
- Figures (both from the toy-trace data): four schedule timelines;
  prefill–decode interference view.
- Sources: src-74, src-75, src-76, src-73, src-82, src-10.

**Ch4 — Efficient execution: attention kernels and inference
parallelism** (≈11 pp)
- Outcomes: explain online-softmax tiling and why it is mathematically
  exact; explain why query length 1 starves batch×head parallelism and how
  split-KV fixes it; keep kernel and end-to-end claims apart; choose
  replicas vs TP (and EP for MoE) for latency or throughput; explain why
  MQA's saving is lost when the KV head is replicated under head sharding.
- Recap: WB05 ch5 FlashAttention, ch4 parallelism (training); WB04 ch5 MoE.
- Boundaries: no CUDA programming; FP8 → ch5 (pointer only); inference
  pipeline parallelism only briefly (no primary source, §7).
- Worked example: per-token TP decode — weight bytes per device and two
  all-reduces per layer (src-53 structure; the decode application is
  derived) vs replicas; Flash-Decoding split count when B×H is below the
  SM count (illustrative).
- Figures: split-KV compute-and-reduce; replicas-vs-TP per-device bytes
  and communication (from the worked example). Pope's layout diagram is
  omitted unless space allows.
- Sources: src-55, src-83, src-84 (hardware dependence), src-85 (authors'
  blog, labelled), src-78, src-53, src-33 §3.4, src-10.

**Ch5 — Quantization: weights, activations and KV caches** (≈10 pp)
- Outcomes: separate formats (INT8/INT4, FP8 E4M3/E5M2) from granularity
  (tensor/channel/token/group) and from methods; explain why weight-only
  quantization helps bandwidth-bound decode but not compute; read a
  quantization quality or speed claim against its conditions.
- Depth: **one method per category in depth** — GPTQ (weight-only error
  compensation), SmoothQuant (W8A8), KIVI (KV cache); LLM.int8(), AWQ,
  KVQuant and the FP8 paper's results in one comparison table.
- Recap: ch1 B_crit; ch2 per-sequence KV accounting.
- Boundaries: no QAT, no FP8 training, no FP4/MX.
- Worked example: an 8B model at bf16 vs INT4 with group size 128 and an
  FP16 scale plus FP16 zero point per group (+32/128 = 0.25 bit per
  weight → 4.25 bits, derived); the B_crit change under weight-only INT4
  assuming bf16 compute and ignoring dequantization cost (stated);
  SmoothQuant's s_j for a two-channel toy.
- Figures: granularity grid; exact transform → approximate quantization
  pipeline.
- Sources: src-88, src-87, src-90 (in depth); src-86, src-89, src-91,
  src-92, src-84, src-10.
- Disagreements to preserve: LLM.int8() speed per GPTQ vs its own App. D;
  AWQ's view of GPTQ calibration; KIVI vs KVQuant; the FP8 paper's int8
  baseline without outlier handling.

**Ch6 — Speculative decoding: proposal, verification and correctness**
(≈9 pp)
- Outcomes (covering all 13 roadmap concepts): run accept/resample by
  hand and recover the target distribution; state correctness conditions
  separately from speedup conditions; compute expected tokens and the
  walltime factor; classify **draft sources** (independent model, MTP
  heads, Medusa heads, EAGLE features, layer-skip self-speculation) by
  cost and acceptance rate, and **verification rules** (rejection
  sampling, greedy match, typical acceptance) by exactness; explain
  batch-size effects and the latency-vs-throughput trade-off; explain
  hardware and serving-engine dependence; reconcile WB04 ch1:350-353/403.
- Recap: WB05 ch2 MTP; ch1 sampling primer and bandwidth-bound decode;
  ch3 iteration-level batching.
- Worked example: 3-token vocabulary — acceptance plus residual returns
  the target distribution exactly (fractions, script-checked); α = 0.8,
  γ = 4, c = 0.05 → E[tokens] = 3.36, walltime factor ≈ 2.80 (derived
  from src-44's closed forms).
- Figures: propose → verify → accept/resample timeline; walltime factor
  vs γ for several α (closed form).
- Sources: src-44, src-45, src-93, src-94, src-95, src-43, src-33 §2.2 /
  §5.4.3 (vendor-reported, conditions unstated), src-82 (docs caveats;
  hardware and engine dependence), src-84 (hardware dependence), src-49.

**Ch7 — Reading and benchmarking an inference deployment** (≈8 pp)
- Outcomes: specify a benchmark (model, hardware, precision, length
  distributions, arrival process, concurrency, warm-up, percentiles); map
  a reported metric to its definition; separate kernel, engine and
  end-to-end claims; read a deployment description (DeepSeek-V3 §3.4).
- Recap: WB05 ch6 configured/observed/derived; ch1 metric contract; ch3
  SLO attainment; ch4 kernel vs end-to-end.
- Boundaries: the workbook runs no benchmark. Warm-up and open- vs
  closed-loop load are the workbook's own methodology guidance
  (MLPerf scenarios, src-80/81, support only the scenario part).
- Worked example: a seeded, script-generated trace of ~30 requests →
  TTFT, ITL, TPOT, E2E with P50/P99; ITL vs TPOT when chunks carry
  several tokens; two "reports" with mismatched conditions
  (illustrative).
- Figures: P50/P99 latency vs offered load from the seeded trace; the
  benchmark-specification checklist is a table, not a figure.
- Sources: src-80, src-81, src-82, src-76, src-75, src-33 §3.4, src-78.

### 5.3 Page estimate

| Front matter | Ch1 | Ch2 | Ch3 | Ch4 | Ch5 | Ch6 | Ch7 | Build note + bibliography (~30 sources) | **Total** |
|---|---|---|---|---|---|---|---|---|---|
| 3 | 11 | 9 | 9 | 11 | 10 | 9 | 8 | 4 | **74** |

Chapter figures include questions and answer keys. WB05 densities
(about 6–12 instructional pages per chapter plus about 1.3 pp of answers;
2 pp for a 12-entry bibliography) put this outline at about 74 pages.
**Recommendation: target 72, hard ceiling 78** (requires approval),
reached by content cuts, never by dropping required sections or
qualifications. Cut order: (1) Pope weight-gathered/stationary layout
detail (ch4); (2) inference pipeline parallelism (ch4); (3) per-method
detail beyond the comparison table (ch5); (4) Medusa/EAGLE detail beyond
the draft-source table (ch6). If cuts are rejected and pages still
overrun, split ch4 into kernels and parallelism (eight chapters) rather
than shrink typography.

## 6. Source-reading records

All new entries were read from the document's own text (pdftotext of the
PDF, raw documentation, or code at a pinned tag). **No paper was read
cover to cover**; depth per entry is in `sources/registry.yaml`.

| ID | Source | Version / pin | Depth | Kind |
|---|---|---|---|---|
| src-73 | PagedAttention / vLLM (SOSP'23) | arXiv 2309.06180v1 | §1, 3, 4.1-4.6, 6.2-6.3, 7.2-7.3 | paper |
| src-74 | Orca (OSDI'22) | USENIX PDF | abstract, §1, 3, 4.2, part §6 | paper |
| src-75 | Sarathi-Serve (OSDI'24) | arXiv 2403.02310v3 | §1, 2, 3.2, 4.1-4.3, 5 | paper |
| src-76 | DistServe (OSDI'24) | arXiv 2401.09670v3 | §1, 2.2-2.3, 3, 4 | paper |
| src-77 | SGLang / RadixAttention (NeurIPS'24) | arXiv 2312.07104v2 | §1, 3 | paper |
| src-78 | Pope et al. (MLSys'23) | arXiv 2211.05102v1 | §2-2.2, 3.2, 3.3 | paper |
| src-79 | Roofline (CACM'09) | Berkeley TR EECS-2008-134 | TR §2-4 (CACM PDF: HTTP 403) | paper (TR text) |
| src-80 | MLPerf Inference (ISCA'20) | arXiv 1911.02549v2 | §III-C, III-D, Table III | paper |
| src-81 | MLPerf inference rules | commit d3eba2f (2026-08-20) | scenario table, LLM rows, footnote | documentation |
| src-82 | vLLM docs and code | tag v0.32.0 = `5df63a72…` | named files with file:line | documentation / code |
| src-83 | FlashAttention-2 | arXiv 2307.08691v1 | §1, 3.1-3.3, 4.1, 5 | paper |
| src-84 | FlashAttention-3 | arXiv 2407.08608v2 | §1, 2.2, 3.1-3.3, 4.3, 5 | paper |
| src-85 | Flash-Decoding | CRFM blog, 2023-10-12 | full post | authors' blog |
| src-86 | LLM.int8() (NeurIPS'22) | arXiv 2208.07339v2 | §1, 3.1-3.2, 6, App. D | paper |
| src-87 | SmoothQuant (ICML'23) | arXiv 2211.10438v7 | §1, 3, 4, 5.1, 5.3 | paper |
| src-88 | GPTQ (ICLR'23) | arXiv 2210.17323v2 | §1, 3, 4, 5 | paper |
| src-89 | AWQ (MLSys'24) | arXiv 2306.00978v6 | §1, 3.1-3.2, Tables 1-2 | paper |
| src-90 | KIVI (ICML'24) | arXiv 2402.02750v2 | §1-3, Table 3 | paper |
| src-91 | KVQuant (NeurIPS'24) | arXiv 2401.18079v6 | §1, 3.1-3.5, 4.1, 4.4 | paper |
| src-92 | FP8 Formats | arXiv 2209.05433v2 | §2-3, Tables 1, 5 | paper |
| src-93 | Medusa | arXiv 2401.10774v3 | §1-3, App. A.2, B | paper |
| src-94 | EAGLE | arXiv 2401.15077v3 | §1-3, 4.1, 4.4 | paper |
| src-95 | Draft & Verify | arXiv 2309.08168v2 | §1, 3, 4.1-4.2, App. B, K | paper |

**Reused entries:**
- Re-read on 2026-10-28 (last_verified updated, passages recorded in
  `access_status` / `expected_use`): src-44 (§1-6, App. A, incl. §2.2),
  src-45 (whole paper incl. proof), src-10 ("Inference" chapter, targeted;
  analytical), src-33 (§2.2, §3.4, §5.4.3, §6), src-43 (§3.2-3.3, App. A),
  src-55 (§1, §3.1, §5, App. E.5).
- Reused **without re-reading**: src-53 (Megatron-LM §3, full-text
  verified 2026-09-27 for Workbook 05); its 06 use (decode-time TP
  communication) is recorded as the workbook's derivation.
- src-11, src-12: vendor guides, title/table-of-contents level only;
  coverage set to `discovery`, never cited for mechanisms.

**Read but not registered:** OCP Microscaling v1.0 (FP4/MX), LayerSkip
(arXiv 2404.16710v4), EAGLE-2 and EAGLE-3 (abstract/introduction only).
None is used by the plan.

**Delegated reading and spot-checks.** Four bounded read-only agents
gathered the coverage map and three topic groups of source records. The
main session re-checked against the frozen files or downloaded text:
WB04 `@eq-kv-cache`, ch1:350-353 and :403, ch7:182-184, "goodput"
occurrence; WB05 ch5 required sections and question counts; src-44
naming, §2.2 and Thm 3.8; src-45 Algorithm 2 naming and "within hardware
numerics"; DeepSeek-V3 85-90% / 1.8×; FP8 E4M3 max 448; GPTQ
calibration; SmoothQuant α = 0.5; KIVI per-channel keys; vLLM v0.32.0
tag commit, TPOT formula (`serve.py:625-628`), `gpu_memory_utilization`
0.92, prefix caching default, README:197/:220, cli.md:127,
prefix_caching.md:87.

## 7. Remaining evidence gaps (none blocks scaffolding)

| Gap | Affects | Disposition |
|---|---|---|
| CACM Roofline text inaccessible (403) | ch1 | cite the Berkeley TR for wording; CACM metadata via Crossref |
| No hardware datasheet registered | ch1, ch4 | labelled illustrative numbers; register a vendor spec only if a real device is named |
| No primary source for inference pipeline parallelism | ch4 | keep brief and derived, or register one during ch4 drafting |
| Nucleus/top-p original paper not registered | ch1 | definitional use via src-44 §2.2; register Holtzman et al. if cited by name |
| No queueing-theory source | ch3, ch7 | arrival effects qualitative; ch7's load curve is an illustrative simulation |
| MLPerf percentile for TTFT/TPOT unconfirmed | ch7 | state rules as written |
| DeepSeek-V3 MTP speedup conditions unstated | ch6 | vendor-reported, under-specified |
| Flash-Decoding end-to-end hardware unstated; not peer-reviewed | ch4 | label as the authors' blog |
| vLLM `synthetic`/`block` rejection options unverified | ch6 | not described |
| src-25 (Mistral 7B) and src-31 (DeepSpeed-MoE) web-search-verified only | ch2, ch4 | re-read before any mechanism claim |
| FA-1/2/3 and FP8 venues | bibliography | cite as arXiv |
| Pre-existing bib/registry mismatches: src-11/src-12 bib titles; src-10 bib note "accessed date not yet confirmed" | bibliography | left unchanged: editing shared bib entries would alter frozen WB04/WB05 rebuilds; fix only in a scoped maintenance task |
| Version drift (vLLM preemption, defaults) | ch2, ch3, ch7 | always "vLLM v0.32.0"; re-pin at drafting time if a newer release changes behaviour |

## 8. Audit dispositions

Three bounded read-only audits reviewed the first draft of this plan
(source coverage; technical correctness and boundaries; pedagogy, figures
and page budget). Every substantiated finding was resolved in this
version; findings were checked against the files before acting.

| # | Finding (audit) | Disposition |
|---|---|---|
| T1 | Decode stated flatly as bandwidth-bound (technical, must-fix) | **Fixed** §4: linear layers vs attention separated; B_crit stated in tokens per step |
| T2 | ST/(S+T) ≈ 1 holds only for MHA (technical, must-fix) | **Fixed** §4: GQA decode intensity ≈ H_q/H_kv; MLA higher |
| T3-T6 | E2E count; src-81 TPOT wording; ITL > TPOT condition; acceptance rule before notation | **Fixed** §4 |
| T7 | Exactness attributed to draft sources | **Fixed** §4, ch6: drafts by cost/acceptance, verification rules by exactness |
| T8 | MFU training vs inference | **Fixed** §3 reconcile item 4 |
| T9 | Prefix reuse "exact" but not bitwise identical | **Fixed** §4, ch2 question |
| T10-T13 | B_crit/KV caveats; step-time form; boundaries (preemption, looped latency, layouts vs pools); WB04 ch1:350-353 | **Fixed** §3, §4, §5.1, ch1, ch2 |
| S1-S2 | src-33/43/53/55 records lacked 06 passages; overstated "read today" for src-53 | **Fixed** registry (passages, dates); src-53 recorded as reused without re-reading |
| S3-S6 | vLLM logprob, "theoretically lossless", ITL/TPOT locators; src-44 §2.2 | **Fixed** registry src-82, src-44 and §4 |
| S7 | No inference-PP primary source | **Recorded** §7; ch4 keeps PP brief |
| S8 | OCP MX, EAGLE-2/3 "mentioned" but unregistered | **Fixed** §5.1: out of scope unless registered |
| S9-S10 | src-10/11/12 06 roles | **Fixed** registry expected_use; src-11/12 coverage → discovery |
| S11-S12 | registry comment range; src-45 notes speedup | **Fixed** |
| S13-S15 | extra keys locator; looped-depth source; warm-up/open-closed source | **Fixed** (src-82 note; WB04 ch8 recap; labelled workbook methodology) |
| S16 | src-10 bib note stale | **Not changed** (§7: shared bib affects frozen rebuilds) |
| P1-P3 | bibliography/page budget/cut order unrealistic | **Fixed** §5.3: 74-page estimate, target 72 / ceiling 78 for approval, content-only cut order |
| P4 | skeleton omitted required sections | **Fixed** §5.2 |
| P5 | looped depth only in a question | **Fixed** ch2 technical core, ch1 latency paragraph |
| P6 | duplicate timeline; no latency–throughput figure | **Fixed** ch1 frontier figure; ch7 P50/P99-vs-load |
| P7 | two roadmap concepts implicit | **Fixed** ch6 outcomes |
| P8-P9 | goodput defined twice; missing recap dependencies | **Fixed** ch3 "apply"; recaps updated |
| P10-P14 | FA-3 pointer; label vocabulary; INT4 convention; ch5 breadth; question counts | **Fixed** §3 labels, §5.1, ch5, §5.2 (5 per chapter) |
| P15-P19 | script feasibility; seeded trace; data-driven figures; Pope figure fallback; ch4 split option | **Adopted** in ch3, ch4, ch7, §5.3 |

## 9. Unresolved decisions for approval

1. Page budget: target 72 / ceiling 78 (vs the default habit of ~68), or
   an eight-chapter split of ch4.
2. Canonical filename `outputs/06-llm-inference-workbook.pdf`.
3. Single representative engine (vLLM v0.32.0) vs adding pinned SGLang or
   TensorRT-LLM documentation (not recommended: framework-encyclopedia
   risk).

## 10. Exact next task after approval

**Scaffold Workbook 06 (no prose):** in `workbooks/06-llm-inference/`
create `index.qmd` (title, front-matter include, chapter and solution
includes), an `includes/front-matter.qmd` stub, seven
`chapter-contracts/chNN.yaml` (status `scaffold_only`, required source
IDs and sections from §5.2, `question_count: 5`), empty `chapters/` and
`solutions/` files, `claim-ledger.yaml` and `questions.yaml` skeletons,
`figure-plan.yaml` with the §5.2 figures, `page-budget.yaml` (as
approved), and `data/worked-examples/`; register `06-llm-inference` in
`config/chapter-status-registry.yaml` (`workbooks:` at `scaffold_only`;
`publications:` record at `planned`, README catalog synchronized) and in
`scripts/workbook_qa.py` `WORKBOOK_REGISTRY` (canonical
`06-llm-inference-workbook.pdf`); add a scaffold test mirroring
`tests/test_workbook05_scaffold.py`. Then draft Chapter 1 through
`.claude/skills/draft-workbook-chapter/`.
