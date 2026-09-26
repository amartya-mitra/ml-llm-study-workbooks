# Project Plan — Workbook 05 (LLM Pretraining and Distributed Training)

Date: 2026-09-26
Baseline commit SHA: `6ebdcc1`
Scope: Phase 1 discovery + Phase 2 planning only. **No chapter prose,
no scaffolding directories, no release candidate.** Per this task's own
gating instructions, drafting does not begin until the chapter list
below is confirmed and the source gaps flagged in this report are
resolved.

---

## Confirmed facts

- **Workbook title:** "LLM Pretraining and Distributed Training"
  (confirmed identically in `README.md` and `config/project.yaml`;
  workbook id `05-llm-training`, number 5).
- **Confirmed source directory:** `workbooks/05-llm-training/` — exists
  today containing only a placeholder `.gitkeep`. No chapter sources,
  index/config, data, figures, question bank, answer keys, build
  scripts, or prior release candidates exist yet for this workbook.
- **`config/project.yaml` status field** still reads `"not started"`
  for workbook 05, and (separately, noted for completeness) still
  reads `"pilot in planning"` for workbook 04 even though workbook 04
  is complete and published — a stale field outside this task's scope,
  flagged but not corrected here.
- **Shared infrastructure already workbook-agnostic and ready:**
  `shared/question-schema.yaml`'s `workbook` field already allows
  `"05-llm-training"`; `shared/glossary.yaml` already has three terms
  tagged for it (`Mixture of experts (MoE)` — shared with 04, `3D
  parallelism` — 05-only, `LoRA` — shared with 07);
  `sources/coverage-matrix.yaml` already has a `05-llm-training` entry
  with 6 pre-registered sources (below). No shared-infra changes are
  needed to begin scaffolding once the chapter list is approved.
- **`.gitignore`'s `outputs/_development/` and `outputs/_releases/`
  rules are already generic** (not scoped to `04-llm-architecture`),
  so `outputs/_development/05-llm-training/` and
  `outputs/_releases/05-llm-training/` will be ignored automatically
  with zero `.gitignore` changes required.

## Only one topic has a confirmed, decided scope assignment

`config/series-topic-roadmap.yaml` (a cross-workbook decision record,
not a drafting plan) assigns exactly one topic to workbook 05 as its
**primary home**:

- **Multi-token prediction (MTP)** — "a pretraining-objectives chapter
  (not yet planned in chapter-level detail)," full training-time
  mechanism treatment. Required concepts: predicting multiple future
  offsets; auxiliary heads/modules; loss construction; independent
  (Gloeckle et al., `src-43`) versus causal-chain (DeepSeek-V3, `src-33`)
  MTP designs; training-only use; parameter/compute implications.
  Required distinction: MTP is a training-time design choice, not
  itself speculative decoding (workbook 06's primary home) — an MTP
  module *can* become a draft source but doesn't have to.

Everything else about workbook 05's scope — pretraining data curation,
optimization at scale, scaling laws, parallelism strategies, memory/
communication at training scale — is implied only by the workbook's
own title and by which sources are pre-registered against it. **No
prior planning document defines a full chapter list for workbook 05.**
The chapter list below is therefore a new proposal from this session,
not a confirmed pre-existing plan, and needs your sign-off before any
drafting starts.

## Pre-registered sources for workbook 05

From `sources/coverage-matrix.yaml`'s `05-llm-training` entry:

| Source | Role | Coverage | Status |
|---|---|---|---|
| `src-16` "The Smol Training Playbook" (HF) | primary — pretraining practicalities, data curation, training recipes | primary | **Access partial** — client-rendered app; only HTML shell/meta fetched, body not retrieved (confirmed both at initial registration 2026-09-22 and again during workbook 04's blueprint session) |
| `src-17` "The Ultra-Scale Playbook" (Nanotron) | primary — distributed training, 3D parallelism, GPU clusters, expert parallelism | primary | **Access partial** — same client-rendering issue as `src-16` |
| `src-10` "How To Scale Your Model" | supporting — scaling laws, rooflines, distributed-training math (already used in workbook 04 ch. 3/ch. 7 for KV-cache/FLOPs framing) | supporting | Fully accessible, already verified |
| `src-18` "LoRA Without Regret" (HF TRL docs) | supporting — cross-reference only; LoRA's primary home is workbook 07 | supporting | Not yet fetched (`last_verified: null`) |
| `src-43` Gloeckle et al., MTP paper | **primary** for MTP's independent-heads design | primary | Fully verified (full-text extraction) |
| `src-33` DeepSeek-V3 technical report | supporting — MTP's causal-chain design (already deeply verified for workbook 04 ch. 6) | supporting | Fully verified |

**Load-bearing gap:** the two sources meant to carry the bulk of
workbook 05's *own* new material — pretraining practicalities
(`src-16`) and distributed-training parallelism (`src-17`) — are both
only partially accessible. This is not a new problem introduced by
this session; it was already flagged during workbook 04's blueprint
work and never resolved. It blocks writing any chapter that depends on
either source as its primary citation until one of the following
happens (see "Unresolved questions," below).

## Proposed chapter list (draft — needs confirmation)

Rationale for ordering: pretraining objectives/data first (what the
model is trained *to do*), then MTP (the one topic with a confirmed,
required placement), then optimization and scaling laws (what governs
*how well* a training run converges), then distributed-training
mechanics (*how* a run is executed across hardware), then a synthesis
chapter reading real training reports through this workbook's lens —
mirroring workbook 04's own closing-synthesis pattern (ch. 8).

| # | Chapter | Purpose | Primary sources (pending gaps) |
|---|---|---|---|
| 1 | Pretraining objectives and data | What next-token prediction actually optimizes at scale; data curation, filtering, deduplication, and quality tradeoffs; tokenizer training (as distinct from tokenizer *use*, already assumed in workbook 04). Establishes vocabulary this workbook needs before MTP. | `src-16` (gap) |
| 2 | Multi-token prediction as a training objective | **Required by the cross-workbook roadmap.** Full mechanism treatment of both the independent-heads (Gloeckle et al.) and causal-chain (DeepSeek-V3) MTP designs; loss construction; why only the next-token head survives to inference; parameter/compute cost of the auxiliary heads. Explicit boundary: does NOT teach speculative decoding (workbook 06). | `src-43`, `src-33` (both fully verified — **this chapter's sourcing is ready today**) |
| 3 | Optimization and scaling laws | AdamW at scale, learning-rate schedules (warmup/decay), gradient clipping, mixed-precision/numerical-stability practicalities; compute-optimal scaling tradeoffs (tokens vs. parameters vs. FLOPs). | `src-10` (partial fit — supporting only); **no primary scaling-law source registered** (gap — see below) |
| 4 | Parallelism strategies for distributed training | Full depth on data/tensor/pipeline/sequence/expert parallelism and memory-sharding (ZeRO/FSDP-style approaches) — the topic workbook 04 ch. 7's parallelism table *explicitly deferred here* ("not derived further here; see [src-17] and a future training workbook"). This chapter is workbook 05's clearest, most load-bearing obligation to workbook 04's own text. | `src-17` (gap — this chapter cannot be responsibly drafted until `src-17` is resolved) |
| 5 | Memory and communication at training scale | Activation memory, optimizer-state memory (Adam's two extra tensors), gradient synchronization/all-reduce cost, communication-computation overlap. Connects to, but does not repeat, workbook 04 ch. 7's resource-ledger framing — that chapter's ledger is architecture-general; this one is training-specific and quantitative. | `src-10`, `src-17` (gap) |
| 6 | Reading real pretraining runs | Synthesis chapter (mirrors workbook 04 ch. 8's pattern): reads the *training-configuration* facts (batch size, LR schedule, cluster size, reported training FLOPs) already disclosed in technical reports workbook 04 ch. 6 already cited for architecture — Llama 3 405B, DeepSeek-V3 — strictly from the training lens, not re-teaching their architecture. | `src-33` and workbook 04's existing Llama 3/Jamba source registrations (re-used, not re-verified) |

**Explicitly excluded from workbook 05** (per your instruction and per
the existing cross-workbook roadmap):

- Mixture-of-experts **architecture** (router, top-k selection, expert
  structure) — workbook 04 ch. 5's primary home; not repeated here.
  If MoE *training* dynamics (load-balancing loss behavior, router
  training instability, expert-parallel communication during training)
  belong anywhere in workbook 05, they belong in Chapter 4 or 5 above
  as a training-specific angle on an already-taught architecture, never
  as a second architecture chapter.
- Speculative decoding — workbook 06's primary home (per the roadmap).
- LoRA / parameter-efficient fine-tuning mechanics in depth — workbook
  07's primary home (`src-18` is registered as a workbook-05
  cross-reference only, not primary content).
- Post-training/alignment (RLHF, DPO, instruction tuning) — workbook
  07's domain entirely; workbook 05 is pretraining only, per its own
  title.
- Inference-time serving, batching, or KV-cache serving mechanics —
  workbook 06's domain; workbook 05 may reference the KV-cache formula
  workbook 04 ch. 3 already built, but does not re-derive it.

## Relationship to Workbook 04

Workbook 04 already:
- Built the KV-cache/FLOPs math (`src-10`) that workbook 05's Chapter 5
  will reuse rather than re-derive.
- Cited `src-17` at a conceptual, table-only level for its five
  parallelism types (ch. 7's "Parallelism, briefly" section), with an
  explicit line stating the topic is "not derived further here" and
  pointing at "a future training workbook" — i.e., workbook 05's
  Chapter 4 above is the text workbook 04 itself promised exists.
- Deferred MTP's full training treatment here by name, in both ch. 7's
  text and `config/series-topic-roadmap.yaml`.
- Already taught MoE architecture in full (ch. 5) and three
  architecture case studies including their MoE/parallelism-relevant
  configs (ch. 6) — workbook 05 may cite these configs' *training*
  facts but must not re-teach the architecture itself.

## Proposed learner outcomes

By the end of workbook 05, a learner should be able to:
1. Explain what a pretraining objective optimizes and why data quality/
   curation choices measurably affect it (not just model architecture).
2. Distinguish MTP's two known implementations (independent-heads vs.
   causal-chain) and state why an MTP loss is training-only.
3. Reason about compute-optimal scaling tradeoffs at a back-of-envelope
   level (tokens vs. parameters vs. FLOPs), citing an appropriate
   primary source once one is registered.
4. Name each of the standard parallelism strategies, what resource
   pressure each addresses, and what communication pattern each
   introduces — the depth workbook 04 ch. 7 promised but deferred.
5. Distinguish logical/architectural memory estimates from measured
   training-run memory, consistent with workbook 04's own established
   distinction (ch. 7), now applied to training-specific state
   (optimizer state, activations, gradients).
6. Read a real model's technical report and identify its *training*
   configuration facts, separately from its architecture facts already
   covered in workbook 04.

## Planned figures and worked examples (draft, pending chapter approval)

- MTP loss-construction diagram (independent-heads vs. causal-chain,
  side by side) — new figure, not reusable from workbook 04.
- A 3D-parallelism diagram (data/tensor/pipeline dimensions on one
  cube or three orthogonal panels) — new figure; workbook 04 ch. 7's
  parallelism table has no figure today, so this is not a duplicate.
- Worked example: given a stated auxiliary-head count and shared-trunk
  parameter count, compute MTP's added parameter/compute cost at
  training time vs. the next-token-only inference cost — mirrors
  workbook 04's own "verified programmatically, not hand-derived"
  worked-example convention (`data/worked-examples/`, checked by
  `tests/test_chNN_worked_examples.py`-style tests).
- Worked example: compute-optimal tradeoff calculation (tokens vs.
  params vs. FLOPs) once a primary scaling-law source is registered.
- Worked example: communication-volume estimate for one parallelism
  strategy at a stated cluster size — deferred until `src-17` is
  resolved, since the exact formula should come from a primary source,
  not be invented.

## Source-verification plan

Before Chapter 1, 3, 4, or 5 can be drafted responsibly:

1. **Retry `src-16` and `src-17` access.** Both are HuggingFace Spaces
   (client-side-rendered apps) that WebFetch and raw `curl` could not
   retrieve past the HTML shell, in two separate sessions now. Retry
   options: a headless-browser-capable fetch tool if one becomes
   available, or locating the same content republished as a static
   page/PDF/GitHub README (both playbooks are open-source projects and
   may have a markdown source in their own repos).
2. **If retries fail again, register named, independently-verifiable
   replacement primary sources** rather than leaving Chapters 1/3/4/5
   under-sourced. Concrete, real candidates to verify and register
   (not yet in `sources/registry.yaml` — confirmed by grep):
   - Scaling laws: Kaplan et al. 2020 ("Scaling Laws for Neural
     Language Models") and/or Hoffmann et al. 2022 ("Training
     Compute-Optimal Large Language Models," the Chinchilla paper).
   - Parallelism: Shoeybi et al. ("Megatron-LM"), Rajbhandari et al.
     ("ZeRO: Memory Optimizations Toward Training Trillion Parameter
     Models"), and/or Huang et al. ("GPipe") as primary,
     independently-fetchable alternatives or companions to `src-17`.
3. Chapter 2 (MTP) needs no further source work — both `src-43` and
   `src-33` are already fully verified.
4. Chapter 6 reuses workbook 04's existing Llama 3/DeepSeek-V3/Jamba
   source registrations; confirm each entry's `access_status` still
   covers the specific training-configuration facts (batch size,
   cluster size, training FLOPs) this chapter would cite, not only the
   architecture facts workbook 04 already used them for.

## Validation and visual-QA plan

Reuse workbook 04's established pattern exactly, since it is already
workbook-agnostic infrastructure:

- `scripts/validate_registry.py` / `scripts/validate_questions.py` —
  already pass today with zero workbook-05 content; will validate new
  `questions.yaml` records against `shared/question-schema.yaml` once
  written (schema already accepts `"05-llm-training"`).
- Per-chapter worked-example tests under `tests/`, following the
  `test_chNN_worked_examples.py` naming/verification pattern — each
  worked-example number must be computed by a version-controlled
  script under `workbooks/05-llm-training/data/worked-examples/`, not
  hand-derived, exactly as workbook 04's build-version-note discloses.
- `git diff --check` before every commit.
- Visual QA: render → `pdftoppm` at 170dpi → visually inspect chapter
  openings, exactly as workbook 04's release-candidate cycle did —
  page renders land under `outputs/_development/05-llm-training/`, per
  this task's own output convention, never committed.
- A dedicated `tests/test_workbook05_blueprint.py` (mirroring
  `test_workbook04_blueprint.py`) should assert the eventual outline's
  page-budget ceiling, once a chapter list is confirmed and a page
  estimate exists — not created yet, since no outline exists to test.

## Expected output paths

- **Canonical PDF:** `outputs/05-llm-training-workbook.pdf` (per this
  task's own stated convention — note this differs slightly from
  workbook 04's canonical filename pattern,
  `04-modern-llm-architecture-workbook.pdf`, which embeds the full
  title rather than the short workbook slug; flagged under "Unresolved
  questions" below since the task text and workbook 04's precedent
  disagree on the naming pattern).
- **RC PDFs:** `outputs/_releases/05-llm-training/` (e.g.
  `05-llm-training-workbook-rc1.pdf`, mirroring workbook 04's
  `rcN` suffix convention once RCs begin).
- **Development artifacts:** `outputs/_development/05-llm-training/`
  (page renders, review PDFs, review bundles — all already covered by
  the existing generic `.gitignore` rules with zero changes needed).

## Unresolved questions / missing inputs

1. **`src-16` and `src-17` access.** Both of workbook 05's own primary
   sources for pretraining practicalities and distributed-training
   parallelism are only partially fetchable (confirmed twice, across
   two sessions). This blocks four of the six proposed chapters.
   Decision needed: retry access, or approve the named replacement
   candidates above.
2. **No scaling-law primary source is registered at all** (Kaplan/
   Chinchilla or equivalent) — a genuine gap, not just an access
   problem. Needs explicit approval to register one before Chapter 3
   can be drafted.
3. **Canonical PDF filename convention mismatch.** This task specifies
   `outputs/05-llm-training-workbook.pdf`; workbook 04's actual
   precedent is `outputs/04-modern-llm-architecture-workbook.pdf` (full
   title embedded, not the short slug). Confirm which pattern workbook
   05 (and, implicitly, workbooks 06-08) should follow going forward.
4. **Chapter list itself is a new proposal, not a pre-existing
   decision** (except for MTP's placement). Needs your explicit
   sign-off — including chapter count, ordering, and the MoE-training-
   dynamics boundary described above — before any scaffolding or
   drafting begins.
5. **Whether Chapter 6 (reading real pretraining runs) duplicates
   workbook 04 ch. 6's case studies too closely** in spirit (both read
   real technical reports) is a judgment call worth confirming; the
   proposed boundary (training-configuration facts only, no
   architecture) is this session's best attempt to keep them distinct.
6. **Stale `config/project.yaml` status fields** (workbook 04 still
   marked "pilot in planning," workbook 05 still "not started" even
   after this planning pass) — flagged, not corrected, since updating
   project-wide config is outside this task's explicit scope.

## Recommended next step

Do not scaffold or draft yet. The chapter list above needs your
sign-off (or edits), and unresolved question 1-2 need a decision before
Chapters 1, 3, 4, and 5's source requirements are "identified" in the
sense this task's own Phase 4 gate requires. Once both are resolved,
the minimum next action is scaffolding only (workbook index/config,
`chapters/`, `includes/`, `solutions/`, `data/`, a figure plan, and
`Makefile`/`scripts/build_workbooks.py` integration — no prose), then
a source-audit pass matching `reports/04_source_audit.md`'s rigor
before Chapter 2 (MTP) becomes the first chapter actually drafted,
since it is the only one with zero outstanding source gaps today.
