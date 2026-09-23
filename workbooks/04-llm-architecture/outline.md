# Workbook 04 — Modern LLM Architecture: Refined Outline

Working title: **Modern LLM Architecture: A Visual Guide to Attention,
Memory, Sparsity, and Hybrid Models**

Target reader: a technically experienced ML practitioner or researcher —
comfortable with deep learning and linear algebra, familiar with the
standard Transformer, but not necessarily fluent in the efficiency
mechanisms that separate a 2017 Transformer from a 2025-2026 production
LLM. Not written for a complete beginner. Familiarity with the original
Transformer does **not** imply familiarity with GQA, MLA, MoE routing,
or hybrid attention stacks — the workbook treats those as the actual
subject matter, not a footnote.

This file is the human-readable rationale behind
`workbooks/04-llm-architecture/outline.yaml` (the machine-checked,
per-chapter structured version of the same plan). If the two ever
disagree, `outline.yaml` is authoritative for build tooling; this file
explains *why* the structure looks the way it does.

## What changed from the provisional 9-chapter outline, and why

The provisional outline (see the Stage 3 task prompt) is a reasonable
first pass, but a close read turns up one real structural problem and
one real scope risk:

1. **Multi-head latent attention (MLA) was listed in two chapters** —
   once under "Reducing attention cost" (old ch. 4) and again under "KV
   cache as an architectural constraint" (old ch. 6, "effects of MHA,
   MQA, GQA, and MLA"). Teaching MLA twice either duplicates content or
   forces an artificial split between "what MLA is" and "what MLA costs"
   that doesn't match how any real source (e.g. DeepSeek-V2/V3's own
   technical reports) presents it — MLA's whole point *is* its cache
   cost, so the mechanism and its cache-size consequence belong in the
   same place.
2. **Old chapter 4 ("Reducing attention cost") mixed three genuinely
   different axes of variation**: (a) how K/V heads are shared across
   query heads (MQA/GQA/MLA — a *head-structure* axis), (b) which token
   positions are allowed to attend to which others (sliding-window,
   sparse patterns — a *connectivity-pattern* axis), and (c) replacing
   softmax attention with a different sequence-mixing primitive entirely
   (linear attention, SSM-style recurrence, hybrids — an
   *architecture-family* axis). Bundling all three into one chapter
   either forces shallow coverage of all three or a chapter that quietly
   balloons past its page budget.

**The fix:** move the head-structure axis (MHA → MQA → GQA → MLA) into
its own chapter that builds the KV-cache-size formula incrementally as
each variant is introduced (so the formula is derived once, per
mechanism, in the place that motivates it — not re-derived in a later
chapter). This absorbs old chapter 6's "effects of MHA/MQA/GQA/MLA on
cache size" into the chapter that already needs that math to make its
point, and leaves old chapter 6 with a smaller, sharper job: the
architecture-vs-runtime distinction (what quantization/paging/batching
do *not* change about the architecture) plus context-length/concurrency
framing. That remaining job is naturally a short opening section of the
architecture-to-systems chapter, not a standalone chapter — merging it
there removes a chapter that would otherwise be mostly a coda to the
attention-variants chapter.

Net effect: **9 chapters become 8.** No topic from the provisional
outline was dropped; three were relocated to remove duplication and one
thin chapter was folded into a natural neighbor. This directly follows
the Stage 3 instruction not to add chapters merely to increase apparent
coverage — the corollary is not to *keep* a chapter that's mostly
duplication either.

The linear-attention / recurrent / hybrid material stays scoped
deliberately narrow: this workbook explains *why* a team would mix
sliding-window, global, and linear/recurrent layers (receptive field vs.
memory/compute tradeoff) and what a real hybrid model's layer pattern
looks like — it does **not** derive SSM recurrence equations or
selective-state-space math from scratch. That level of depth belongs to
a dedicated architecture paper or a future workbook, and including it
here would blow the page budget and the "don't drift into a full
[adjacent] textbook" review gate (Stage 10).

## Refined chapter list

| # | Title | Purpose in one line | Est. pages |
|---|---|---|---|
| 1 | Transformer refresher | Fast, shared vocabulary — not a tutorial | 4 |
| 2 | Anatomy of a modern decoder | RoPE, RMSNorm, SwiGLU, norm placement, tied embeddings — convention vs. requirement | 7 |
| 3 | Attention head structure and cache-efficient variants | MHA → MQA → GQA → MLA, with the KV-cache-size formula built up mechanism by mechanism | 9 |
| 4 | Restricting attention's reach | Sliding-window/local-global, sparse patterns, linear/recurrent & hybrid alternatives | 7 |
| 5 | Mixture-of-experts models | Routing, active vs. total params, load balancing, expert parallelism | 8 |
| 6 | Modern architecture case studies | Real dense / MoE / MLA / hybrid models, compared on architecture not benchmark marketing | 8 |
| 7 | From architecture to systems consequences | Architecture-vs-runtime distinction, training communication, inference memory bandwidth, latency vs. throughput, why FLOPs ≠ wall-clock | 7 |
| 8 | Synthesis and practice | Worksheet, worked calculations, design scenarios, misconception diagnosis, interview questions, compact visual reference | 6 |

**Total estimated pages: 56** (ceiling is 65; ~9 pages of margin
reserved for front matter, a table of contents, and drafting overrun —
deliberately not spent in advance, per "the length is a ceiling, not a
target to inflate").

## Recommended drafting order (conceptual dependency, not chapter number)

1. **Ch. 1** (refresher) — establishes shared notation everything else
   depends on; must exist before anything else is checked for
   consistency.
2. **Ch. 2** (modern decoder anatomy) — RoPE/RMSNorm/SwiGLU are
   prerequisites for reading any real model's architecture, including
   the ones used as running examples in ch. 3-6.
3. **Ch. 3** (attention variants + cache math) — the single most
   load-bearing chapter; ch. 4, 6, and 7 all reference its cache-size
   formula rather than re-deriving it.
4. **Ch. 5** (MoE) — independent of ch. 3/4's attention content
   (orthogonal axis: which *parameters* activate, not attention
   structure), can be drafted in parallel with ch. 4 once ch. 1-2 exist.
5. **Ch. 4** (restricting attention's reach) — depends on ch. 3's
   head-structure vocabulary (e.g. explaining sliding-window GQA
   requires GQA to already be defined).
6. **Ch. 6** (case studies) — depends on ch. 2, 3, 4, and 5 all being
   done, since it exercises every mechanism taught so far against real
   models.
7. **Ch. 7** (architecture → systems) — depends on ch. 3's cache math
   and ch. 5's active/total parameter distinction being in place.
8. **Ch. 8** (synthesis) — must be last; it is explicitly a worksheet
   over the preceding seven chapters and cannot be written first.

## Drafting-time adjustment: MLA deferred out of chapter 3 (2026-09-23)

The chapter-3 drafting task explicitly scoped chapter 3 to MHA, MQA,
and GQA only, and explicitly excluded substantially teaching MLA in
that pass ("do not substantially teach: MLA..."), with a tighter
instructional-page budget (7 preferred / 8 hard maximum) than this
outline's own estimate (9 pages) assumed. This is a real conflict with
this file's and `outline.yaml`'s original chapter-3 scope (MHA → MQA →
GQA → MLA as one progression). Per the drafting task's own instruction
to preserve intended learning goals while documenting the adjustment
rather than silently relocating material, the resolution taken was:

- Chapter 3, as actually drafted, covers MHA/MQA/GQA and the KV-cache
  formula they share, ending with one brief, unnamed-mechanism forward
  reference to a further latent-compression technique "chapter 6's
  case studies will name" — not a taught mechanism.
- MLA's full mechanism (low-rank latent compression, its own cache
  formula, its own worked example and figure) is **not yet placed** in
  a specific future chapter. The most natural homes are a short
  addition to chapter 3 in a later revision (so the KV-cache-formula
  chapter still owns every head-structure/compression mechanism) or a
  dedicated slice of chapter 6's case studies (since DeepSeek-V2/V3 are
  already chapter 6's case-study source for MLA). This decision is
  deliberately left open rather than guessed at now — see
  `reports/04_ch03_draft_report.md` for the full rationale — and must
  be made explicitly before chapter 6 is drafted, not defaulted by
  omission.
- This also resolves the estimated-page mismatch: chapter 3's estimate
  above (9 pages) assumed MLA content that is no longer in chapter 3 as
  drafted; the actual chapter is ~7-8 pages, consistent with dropping
  roughly a figure, a worked example, and a table row's worth of MLA
  material relative to the original estimate.

## Explicit non-goals (scope fences, checked again at Stage 10)

- Not a full inference-serving/inference-engineering textbook (that is
  workbook 06's job) — ch. 7 stops at *why* architecture constrains
  systems behavior, not *how* to build a serving stack.
- Not a full distributed-training textbook (that is workbook 05's job)
  — ch. 7's training-communication section stays at the level of "why
  does this architecture choice create more/less cross-device traffic,"
  not a parallelism-strategy deep dive.
- Not a from-scratch derivation of state-space-model recurrence — ch. 4
  treats linear/recurrent/hybrid attention at the intuition-and-tradeoff
  level, not the differential-equation level.
- Model-specific numbers (parameter counts, reported benchmarks) are
  treated as **time-sensitive and dated explicitly** in prose (e.g. "as
  of the model's technical report, dated ..."), never stated as timeless
  fact, per AGENTS.md.
