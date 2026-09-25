# Release Candidate Report — Workbook 04, Complete Content Draft (RC1)

Date: 2026-09-25
Status: **Complete content draft — pending whole-book editorial and
visual QA.** This is a release candidate, not the final edition. Do
not distribute this as a finished book without the editorial/visual
pass described in Section 8 below.

PDF: `outputs/04-modern-llm-architecture-workbook-rc1.pdf`
Build command: `make release-candidate-v1`
(`scripts/build_release_candidate_v1.py`)

## 1. What this artifact is

All eight chapters of *Modern LLM Architecture: A Visual Guide to
Attention, Memory, Sparsity, and Hybrid Models* (workbook 04), plus a
complete answer key, references, and a build/version note, rendered
into one PDF for the first time. Each chapter was drafted, illustrated,
and validated individually across several sessions (see
`reports/04_ch03_draft_report.md` through `reports/04_ch08_draft_report.md`);
this report records the first whole-book assembly and its own
validation pass, not a re-draft of any chapter's content.

## 2. Complete-workbook statistics

| Metric | Value |
|---|---|
| Total PDF pages | **68** (within the 70-page release-candidate ceiling and the general 72-page project ceiling; at the top of the 60-68 preferred range) |
| Total word count (rendered) | **33,415** |
| Chapters | 8 of 8 (complete) |
| Distinct figures (anchored, `{#fig-...}`) | **20** |
| Distinct tables (anchored, `{#tbl-...}`) | **16** |
| Registered sources | **49** (`src-01` through `src-49`) |
| Quick/check-your-understanding questions | 30 (3+4+4+3+4+4+4+4 across ch. 1-8) |
| Boxed misconceptions | 13 |
| Applied exercises | 8 (one per chapter) |
| Cumulative review questions | 12 |
| Interview-style questions | 9 |

## 3. Chapter 8 (the chapter drafted this session)

| Metric | Value |
|---|---|
| Instructional pages | **5** (hard maximum, disclosed miss vs. 4-page preferred) |
| Answer-key pages | **~0.65** (within 0.75 hard maximum, disclosed miss vs. 0.5 preferred) |
| Chapter word count (qmd source) | 1,527 |
| Solutions word count (qmd source) | 363 |
| Figures | 2 (looped-vs-unrolled depth; architecture decision map) |
| Tables | 1 (fixed-vs-adaptive computation) + 1 worked-example table |
| Questions | 6 (4 check-your-understanding + 1 applied exercise + 1 interview lens) |

Full detail in `reports/04_ch08_draft_report.md`.

## 4. Fast-changing sections (flagged in `source-coverage.yaml`)

Every claim below is tied to a specific model/version and dated;
none should be read as a timeless fact:

- Chapter 6: Llama 3 405B (2024-07-31), DeepSeek-V3 (2024-12-27, rev.
  2025-02-18), Jamba (2024-03-28) -- three pinned model versions, not
  "the current best" models.
- Chapter 8: Nanbeige4.2-3B (arXiv v2, 2026-07-27) -- a specific,
  dated, released model. Mixture-of-Recursions (2025) is a research
  proposal, not (yet) a widely shipped production system.
- Chapter 8 / roadmap: the GPT-6 Astra caveat is explicitly a standing,
  unresolved uncertainty, not a claim expected to become stale in one
  direction -- it should be re-checked against official sources before
  ever being upgraded to a confirmed fact in a future revision.

## 5. Deferred Workbook 05 material (LLM Pretraining and Distributed Training)

Per `config/series-topic-roadmap.yaml`, not drafted anywhere in
workbook 04:

- Multi-token prediction's full training-time mechanics: loss
  construction, independent-heads ([@src-43]) vs. causal-chain
  (DeepSeek-V3, [@src-33]) designs, and the parameter/compute
  implications of each.
- Recurrent-depth/looped-transformer training-time consequences beyond
  what chapters 7-8 previewed (adaptive-halting training objectives,
  loss-landscape/training-stability effects in depth).
- Data, tensor, pipeline, and expert parallelism's full algorithmic
  and communication-volume treatment (chapter 7 gave only a minimal
  conceptual map, explicitly deferring derivation).

## 6. Deferred Workbook 06 material (LLM Inference Engineering)

Per `config/series-topic-roadmap.yaml`, not drafted anywhere in
workbook 04:

- The complete speculative-decoding algorithm: proposal, verification,
  acceptance/rejection and resampling, independent draft models,
  self-speculative methods, MTP-assisted drafting, acceptance rate,
  draft cost, batch-size effects, hardware/serving-engine dependence,
  and the lossless-distribution guarantee's exact assumptions.
- An implementation-companion source for speculative decoding (e.g. a
  specific serving engine's documentation) -- intentionally not yet
  selected; `config/series-topic-roadmap.yaml` records this as an open
  placeholder, not a silent omission.
- Recurrent depth/looped transformers' cache-and-latency consequences
  at the inference-serving-engine level (chapters 7-8 covered the
  architecture-level cache caveat only).
- Quantization, KV-cache paging, and continuous-batching's full
  serving-engine mechanics (chapter 7 used them only to establish the
  architecture-vs-runtime distinction).

## 7. Validation summary

`python -m unittest discover -s tests` passes all 234 tests.
`git diff --check` reports no whitespace errors. The full PDF text was
searched for internal-path leakage (none found in learner-facing
chapter/solutions text; all matches are confined to the Build and
Version Note's own provenance disclosure, consistent with every prior
chapter) and for the Stage 15 review-phrase list ("Astra uses,"
"confirmed," "free compute," "free depth," "same KV cache," "half the
model," "exact speedup," "MTP is speculative decoding," "hidden chain
of thought") -- no unhedged occurrence of any of them was found.

## 8. What remains before this is a finished book

This release candidate has been validated **chapter by chapter**, as
each was drafted, but has **not** yet had a single whole-book pass
across all eight chapters together. Specifically outstanding:

- **Consistent terminology check**: spot-checked, not exhaustively
  verified, that terms introduced in one chapter (e.g. "arithmetic
  intensity," ch. 7) are used identically in later chapters (ch. 8
  reuses it without redefinition, per design -- but a full
  terminology audit across all 8 chapters has not been performed).
- **Cross-reference accuracy**: every `ch. N` prose reference was
  written to be correct at drafting time, but has not been
  mechanically verified against the final, assembled table of contents
  now that all 8 chapters exist together.
- **Page-break aesthetics**: individual chapters were tuned to their
  own page budgets; the whole-book page flow (e.g. whether any chapter
  boundary now lands awkwardly given the final answer-key ordering)
  has not been reviewed as a single continuous document beyond the
  spot-checks in this session (title page, full TOC, final
  bibliography page, and chapter 8's own pages).
- **Final proofread**: no dedicated copy-edit pass for typos, awkward
  phrasing, or repeated words has been performed across the complete
  document.
- **Three named-but-unverified sources**: "Beyond Parameters...",
  "SMELT...", and "Full-bandwidth transformer" (named only in
  `src-47`) remain unverified candidates, not cited for any specific
  claim.

None of these are expected to require new content -- they are
consistency/polish passes over content that already exists and has
been individually validated.

## 9. Commit

See the commit this report accompanies for the final SHA. Working tree
was clean before this session's changes; nothing was pushed to any
remote. This release candidate is **not** the final edition -- see
Section 8.
