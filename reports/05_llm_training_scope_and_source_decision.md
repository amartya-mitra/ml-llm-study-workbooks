# Workbook 05 — Scope and Source Decision Report

Date: 2026-09-26
Baseline commit SHA: `273afe6`
Scope: Source-gap resolution and chapter-structure reassessment only.
**No chapter content, index.qmd, or scaffolding was created.** This
report is the approval-gate artifact requested; drafting still requires
explicit sign-off after this report.

---

## Headline result

The two previously-blocking source gaps are **resolved**, not worked
around. Both `src-16` and `src-17` were re-fetched this session and are
now **fully verified via full-text extraction** — the earlier "partial
access" status was a fetch-method limitation (WebFetch/`curl` against a
client-side-rendered app shell), not a real property of the source.
Both HuggingFace Spaces are themselves git repositories; each one's
actual article body is a plain, non-LFS file in that repo, fetched
directly. A previously-missing scaling-law primary source is now
registered, having been read in full, not merely titled. **5 of 6
proposed chapters are now source-ready**; the 6th needs only a spot
confirmation of already-verified sources, not new source work.

---

## 1. Verified source table

| Source | Title | Status (before) | Status (now) | How verified |
|---|---|---|---|---|
| `src-16` | The Smol Training Playbook | Partial (HTML shell only) | **Fully verified** | Fetched `app/src/content/article.mdx` directly from the HF Space's underlying repo (plain file, not LFS): 5,807 lines / 67,321 words, full byline (12 named HF authors), published 2025-10-30 |
| `src-17` | The Ultra-Scale Playbook | Partial (HTML shell only) | **Fully verified** | Fetched `ultra_blog.md` directly from the HF Space's underlying repo (plain file, not LFS): 3,927 lines / 31,387 words. Repo also hosts an official PDF export of the same content |
| `src-50` (new) | Kaplan et al., "Scaling Laws for Neural Language Models" | Not registered | **Verified, registered** | Downloaded arXiv PDF (arXiv:2001.08361), `pdftotext` full-text extraction, abstract and framing confirmed directly against the paper's own text |
| `src-51` (new) | Hoffmann et al., "Training Compute-Optimal Large Language Models" (Chinchilla) | Not registered | **Verified, registered** | Downloaded arXiv PDF (arXiv:2203.15556), `pdftotext` full-text extraction, abstract and framing confirmed directly against the paper's own text |
| `src-10` | How To Scale Your Model | Already verified (workbook 04) | Unchanged | Reused, not re-verified this session |
| `src-43` | Gloeckle et al., MTP paper | Already verified | Unchanged | Reused, not re-verified this session |
| `src-33` | DeepSeek-V3 technical report | Already verified | Unchanged | Reused, not re-verified this session |
| `src-32` | The Llama 3 Herd of Models | Already verified | Unchanged | Reused, not re-verified this session — its own `expected_use` field already notes "full pre/post-training recipe described" |

Registry and coverage-matrix changes: `sources/registry.yaml` updated
in place for `src-16`/`src-17` (corrected `access_status`, `last_verified`,
author bylines, `expected_use`); two new entries (`src-50`, `src-51`)
added; `sources/coverage-matrix.yaml`'s `05-llm-training` entry updated
to list both as `primary` coverage. `python3 scripts/validate_registry.py`
passes after every edit.

## 2. Named replacement candidates — status

The task asked me to evaluate GPipe, Megatron-LM, and ZeRO as
parallelism-primary candidates. **Existence and fetchability
confirmed** (all three resolve on arXiv and return HTTP 200 PDFs:
GPipe `arXiv:1811.06965`, Megatron-LM `arXiv:1909.08053`, ZeRO
`arXiv:1910.02054`) — but **not yet read in full text**, so **not yet
registered**, per the instruction not to add sources until actually
verified. `src-17`'s own References section cites the actual academic
originals for each parallelism technique it covers; cross-checking that
list against these three (and registering whichever `src-17` itself
treats as foundational) is recommended **during** Chapter 4/5 drafting,
not as a blocker before it — `src-17` alone already supports
mechanism-level teaching for both chapters today (see readiness table
below).

## 3. Chapter-by-chapter reassessment

| # | Chapter | Learning outcomes | Primary sources | Overlaps WB04? | Source-ready? |
|---|---|---|---|---|---|
| 1 | Pretraining objectives and data | Explain what next-token prediction optimizes; reason about data curation/mixing tradeoffs; describe tokenizer training | `src-16` (now fully verified — covers ablations, dataset/mixing-weight decisions, tokenizer training, model-config case study) | No | **Yes** |
| 2 | Multi-token prediction as a training objective | Distinguish independent-heads vs. causal-chain MTP; explain why the loss is training-only | `src-43`, `src-33` (both already fully verified) | No — WB04 ch.7/ch.8 only cross-reference this by name, per `config/series-topic-roadmap.yaml`'s explicit primary-home assignment | **Yes** (unchanged from before — always ready) |
| 3 | Optimization and scaling laws | Reason about compute-optimal tradeoffs (tokens/params/FLOPs); describe AdamW + LR-schedule practicalities at scale | `src-50` (Kaplan), `src-51` (Hoffmann/Chinchilla) — both now verified and registered; `src-16` covers the AdamW/cosine-schedule practicalities directly | No | **Yes** (previously blocked — now resolved) |
| 4 | Parallelism strategies for distributed training | Name each parallelism strategy, its resource pressure, and its communication pattern — the depth WB04 ch.7 explicitly deferred here | `src-17` (now fully verified — covers data/tensor/context/pipeline/expert parallelism and 5D parallelism at mechanism level, with the authors' own 4,000+-experiment benchmarks) | No — this chapter fulfills WB04 ch.7's own explicit deferral by name | **Yes** (previously blocked — now resolved) |
| 5 | Memory and communication at training scale | Distinguish logical/architectural memory estimates from measured training-run memory, applied to optimizer state/activations/gradients | `src-10` (already verified), `src-17` (now fully verified — covers GPU kernel fusion, mixed precision, and communication overlap) | Connects to but does not repeat WB04 ch.7's architecture-general resource ledger | **Yes** (previously blocked — now resolved) |
| 6 | Reading real pretraining runs | Read a technical report's *training*-configuration facts (batch size, cluster size, training FLOPs) separately from its architecture facts | `src-32` (Llama 3 — already verified, own `expected_use` field confirms "full pre/post-training recipe described"), `src-33` (DeepSeek-V3 — already verified) | Reuses WB04 ch.6's exact source registrations but must cite only training-configuration facts, never re-teaching architecture | **Yes, pending a light spot-check** (not a new fetch — confirm the already-verified full-text extraction actually covered the training-infrastructure section, e.g. Llama 3's cluster-size/GPU-count disclosure, before citing a specific number) |

**Result: 5 of 6 chapters are source-ready today with zero further
fetching required; the 6th needs a spot-check of already-verified
material, not new source work.** This is a substantial change from the
prior planning report, which found only Chapter 2 (MTP) source-ready
and flagged 4 chapters as blocked.

## 4. Explicit boundary with Workbook 04

Unchanged from the prior planning report, restated for this decision:

- **MoE architecture** stays exclusively in WB04 ch.5. If MoE *training*
  dynamics belong anywhere in WB05 (load-balancing loss behavior,
  router training instability, expert-parallel communication during
  training), they belong inside Chapter 4 or 5 above as a
  training-specific angle on an already-taught architecture — never as
  a second architecture chapter.
- **Speculative decoding** stays WB06's primary home.
- **LoRA / PEFT mechanics in depth** and **post-training/alignment**
  stay WB07's domain. This is now sharper than before: `src-16` itself
  contains a substantial post-training section ("Beyond Base
  Models—Post-Training in 2025") that WB05 must explicitly decline to
  cite, even though the same source is WB05's own primary reference for
  its pretraining sections. The registry's `expected_use` field for
  `src-16` states this boundary explicitly.
- **KV-cache serving/inference mechanics** stay WB06's domain; WB05 may
  reuse WB04 ch.3's KV-cache formula by reference, never re-derive it.
- **Chapter 4's parallelism depth is not new scope** — it fulfills a
  promise WB04 ch.7 already made in its own text ("not derived further
  here; see [src-17] and a future training workbook").

## 5. Proposed PDF naming convention — decision

The prior planning report flagged a mismatch: this task's own stated
path is `outputs/05-llm-training-workbook.pdf` (short slug), while
workbook 04's actual precedent is
`outputs/04-modern-llm-architecture-workbook.pdf` (full title embedded).
**Decision: follow this task's explicit instruction for workbook 05**
— `outputs/05-llm-training-workbook.pdf` — since it is stated
unambiguously in this task and in `scripts/workbook_qa.py`'s
`WORKBOOK_REGISTRY` (already implemented this way). This creates a
one-time naming inconsistency between workbook 04 and workbook 05; it
is not resolved retroactively for workbook 04 (out of scope — WB04's
artifact is published and frozen), and future workbooks (06/07/08)
should follow whichever pattern the project maintainer confirms is
canonical going forward. Not re-litigated further here.

## 6. Scaffolding readiness — decision

**Ready for scaffolding, pending your explicit approval of the chapter
list above.** All source gaps that blocked the prior plan are now
resolved. The remaining open items are narrow and do not block
scaffolding:

1. Confirm the 6-chapter list and ordering above (unchanged from the
   prior plan's proposal, now substantially better sourced).
2. Chapter 6's spot-check (re-read the already-fetched Llama 3/
   DeepSeek-V3 full text specifically for training-infrastructure
   numbers) should happen during that chapter's own drafting, not as a
   pre-scaffolding gate.
3. GPipe/Megatron-LM/ZeRO registration (if `src-17`'s own References
   section names them as foundational) should happen during Chapter
   4/5 drafting, not as a pre-scaffolding gate.

**This report does not create `index.qmd`, chapter files, figures,
answer keys, or an RC PDF, and does not install OpenResearch or push
anything**, per this task's explicit stop instruction. The next action
is scaffolding (workbook index/config, `chapters/`, `includes/`,
`solutions/`, `data/`, figure plan, `Makefile`/`build_workbooks.py`
integration — no prose), gated on your explicit sign-off of the chapter
list in Section 3.
