# Figure Plan — Workbook 04 (Modern LLM Architecture)

Date: 2026-09-22
Structured data: `workbooks/04-llm-architecture/figure-plan.yaml` (18
figures, full per-figure detail). This report is the narrative summary.

## Count and distribution

18 figures total, within the Stage 7 target range of 12-18. Distribution
across the refined 8-chapter outline:

| Chapter | Figures |
|---|---|
| ch1 (refresher) | 2 |
| ch2 (modern decoder anatomy) | 3 |
| ch3 (attention variants + KV cache) | 4 |
| ch4 (restricting attention's reach) | 2 |
| ch5 (mixture-of-experts) | 4 |
| ch6 (case studies) | 1 |
| ch7 (architecture -> systems) | 1 |
| ch8 (synthesis) | 1 |

Chapter 3 and chapter 5 get the most figures, matching their status as
the two most mechanism-dense chapters in the outline (9 and 8 estimated
pages respectively, the two longest chapters).

## Every figure teaches one relationship, not everything at once

Per Stage 7's instruction to avoid "everything in one diagram" figures,
each entry's `teaching_purpose` and `learner_takeaway` fields were
written to isolate a single relationship:

- Attention head-sharing (MHA/MQA/GQA) is its own figure, separate from
  MLA's compression/reconstruction mechanism, even though both live in
  ch. 3 and both reduce KV-cache size — they reduce it by genuinely
  different mechanisms, so they get genuinely different diagrams
  (`fig-mha-mqa-gqa-head-sharing` vs. `fig-mla-compression-reconstruction`).
- MoE gets four figures rather than one crowded one: the single-token
  routing structure (`fig-dense-mlp-vs-moe`), the batch-level imbalance
  problem (`fig-token-to-expert-routing`), the resulting systems
  consequence (`fig-expert-parallel-communication`), and the parameter
  accounting (`fig-active-vs-total-params`) are four different claims
  that would blur together in one diagram.
- The general architecture-to-consequence map (`fig-architecture-to-consequence-map`,
  ch. 7) is deliberately separate from the case-study chapter's
  per-model instantiation (`fig-case-study-architecture-comparison`,
  ch. 6) — one is the general pattern, the other is four worked
  examples of it; conflating them would make neither land clearly.

## Reuse of the existing bootstrap figure

Two entries (`fig-prefill-vs-decode-extended`, `fig-kv-cache-growth-gqa-variant`)
explicitly reuse or lightly adapt the existing
`figures/source/kv_cache_demo.py` figure from the project bootstrap
(the one that already went through five rounds of real layout fixes and
visual PNG inspection — see `reports/bootstrap_report.md`) rather than
designing a new figure from scratch. Both are marked `must_be_redrawn: false`
specifically because there is no third-party source figure involved at
all — the "redraw" question doesn't apply when the starting point is
already this project's own original work.

## Attribution and licensing discipline

Every other figure (16 of 18) is marked `must_be_redrawn: true` with an
explicit `attribution_requirement` naming which registry source(s) the
*concept* (never the figure itself) is informed by. This follows
directly from `reports/04_source_audit.md`'s licensing findings: none of
the newly-added arXiv papers grant figure-reuse rights, and src-14/src-15
(Raschka's comparison article and gallery) explicitly say not to
reproduce their diagrams. No figure in this plan cites a source for its
*visual design* — only ever for the underlying fact, config number, or
mechanism the redraw depicts.

## Accessibility and grayscale behavior

Every entry has a `grayscale_behavior` field stating a second visual
channel (shape, border weight, fill pattern, hatch) beyond color alone,
and an `accessibility_description` field written as a genuine
alt-text-style description of the diagram's content — not a repeat of
the caption. This follows `config/visual-style.yaml`'s existing
colorblind-safe/grayscale-legible requirements, applied per-figure
rather than left as a general policy to remember later.

## What was deliberately left out

No figure was planned for the SSM/linear-attention recurrence mechanism
itself, consistent with `reports/04_source_audit.md`'s finding that no
primary source for that specific mechanism has been verified yet, and
with `outline.md`'s explicit scope fence against a from-scratch SSM
derivation. If that source gap closes later, a figure could be added to
ch. 4 — but not before the source exists to back it.
