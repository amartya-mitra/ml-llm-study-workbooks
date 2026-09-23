# Draft Report — Workbook 04, Chapter 5

Date: 2026-09-23
Scope: drafting, illustrating, rendering, and validating Chapter 5
("Mixture of Experts: More Parameters, Selective Compute") of workbook
04, added to the existing Chapters 1-4 pilot. Chapters 6-8 were not
drafted, per instructions.

Final artifact: `outputs/04-llm-architecture-ch01-05-review.pdf`
(50 pages). Build command: `make review-ch01-05`
(`scripts/build_ch01_05_review.py`). Prior review PDFs
(`-ch01-02`, `-ch01-03`, `-ch01-04`) were left untouched, not
overwritten — frozen historical checkpoints, per each superseded
script's own notice.

## 1. Blueprint scope reduction

`outline.yaml`'s original ch5 plan (8 pages, 4 figures, real-model
active/total bar chart, dedicated expert-parallel-communication
figure) exceeded this task's 5-preferred/6-hard-maximum instructional
budget and explicitly-excluded topics (distributed-training
implementation, collective-communication algorithms, kernel
optimization, inference-engine configuration, expert quantization,
model-specific benchmark comparisons, post-training, routing-research
surveys). Resolved by updating `outline.yaml`'s ch5 entry in place
(new `drafting_note` field, retitled to "Mixture of experts: more
parameters, selective compute," `estimated_pages` 8 → 5): dropped the
real-model bar chart (would have required model-specific benchmark
comparisons) and merged the expert-parallel-communication figure into
the routing figure (3 figures instead of 4). `outline.md`'s chapter
table, total-page estimate, and a new "Drafting-time adjustment"
section were updated to match; `estimated_total_pages` revised
54 → 51.

## 2. Sourcing (Stage 13)

Reused three already-deeply-verified primary sources from the
original Stage 4/5 research pass, all previously fetched in full via
WebFetch (not snippets): [@src-28] (Shazeer et al., sparsely-gated MoE,
noisy top-k gating, importance/load losses), [@src-29] (GShard, top-2
gating, its own auxiliary load-balancing loss, expert-parallel
sharding), [@src-30] (Switch Transformer, top-1 routing, a *different*
load-balancing loss form — restated as genuinely non-equivalent to
GShard's and Shazeer's, per `source-coverage.yaml`'s pre-existing
"disputed" status for this exact claim).

**One new source added**, per Stage 8's explicit invitation to use
"DeepSeekMoE or another verified primary source" for the shared-experts
section: [@src-36], DeepSeekMoE (Dai et al., 2024, arXiv:2401.06066).
Chosen over DeepSeek-V3 (`src-33`, already registered) because it is
the *architecture-defining* source for shared experts, not a
downstream user of the idea. Fetched and read in full via WebFetch
(the paper's HTML rendering, not the abstract), confirming: the exact
motivation quote ("if there are shared experts dedicated to capturing
and consolidating common knowledge... the parameter redundancy among
other routed experts will be alleviated"), the exact real configs
(2B model: 1 shared/63 routed; 16B: 2 shared/64 routed; 145B: 4
shared/128 routed), and the compute-held-constant tradeoff (routed
top-k activation is *reduced* when shared experts are added). Recorded
in `sources/registry.yaml` (`src-36`), `shared/bibliography.bib`, and
a new `source-coverage.yaml` claim entry, per Stage 13's explicit
instruction. Model-specific benchmark sources (`src-33`, `src-34`)
were deliberately **not** cited in the chapter body, consistent with
Stage 1's exclusion of model-specific benchmark comparisons — they
appear only as `source_ids` on a few question records (internal
metadata, not rendered into the PDF).

## 3. Chapter 5 content

- **Dense-to-sparse baseline (Stage 3).** One paragraph: router scores
  $E$ experts, top-$k$ selected, outputs combined, exact rules
  architecture-dependent.
- **Routing equations (Stage 4).** Compact: $r=W_r x$, $p=\text{softmax}(r)$,
  $T(x)=\text{TopK}(p,k)$, $y(x) = \sum_{e \in T(x)} \alpha_e(x)\cdot
  \text{Expert}_e(x)$ — with an explicit note that normalization,
  capacity handling, and auxiliary losses are not identical across
  production systems.
- **Total vs. active parameters (Stage 5).** The chapter's central
  equation block: routed-bank total/active ($Ep_e$, $kp_e$) and
  complete-model total/active ($p_{\text{base}}+Ep_e+p_s$,
  $p_{\text{base}}+kp_e+p_s$), with $E/k$ explicitly named as the
  bank's own ratio, not the model's. States "A-B" notation is
  convention-dependent and active parameters $\neq$ exact FLOPs.
- **Load balancing and capacity (Stage 7).** Imbalance/routing-collapse
  risk, capacity factor, overflow (drop/reroute, implementation-
  dependent), auxiliary loss stated as *encouraging*, not
  *guaranteeing*, balance.
- **Shared experts (Stage 8).** Motivation and compute tradeoff, cited
  to [@src-36] directly, with an explicit "not universally necessary"
  hedge.
- **Expert parallelism (Stage 9).** One paragraph, architecture-level
  only: all-to-all defined in plain language, uneven routing → uneven
  device load, "fewer active parameters ≠ all experts fit on one
  device" stated explicitly. Collective algorithms/topology explicitly
  out of scope.
- **Worked examples (Stage 6-7).** Two scripts:
  `data/worked-examples/moe_param_counts.py` ($E=8$, $k=2$,
  $p_e=p_s=100$M, $p_{\text{base}}=1.2$B → routed-bank ratio exactly
  4.0 = $E/k$, complete-model ratio 1.4 — the chapter's central
  invariant, checked as a hard test assertion) and
  `moe_routing_imbalance.py` (6 tokens, top-1, 4 experts, a
  deliberately skewed assignment matching Figure C exactly, capacity
  factor 1.2 → one expert overflows by exactly 1 token).
- **Figures (Stage 10).** Exactly 3, matching the hard maximum: (A)
  dense FFN vs. sparse MoE, same tokens in both panels; (B) total vs.
  active parameters, distinguishing always-active/active-for-this-token/
  stored-but-inactive; (C) routing + expert parallelism combined,
  showing dispatch/return across a 2-device boundary with one
  overloaded expert highlighted. Two real bugs were found and fixed
  during drafting (Section 5).
- **Comparison table (Stage 11).** Dense FFN vs. routed MoE vs. MoE +
  shared expert, qualified throughout, explicitly captioned "MoE does
  not automatically mean lower latency, lower memory, better quality,
  or balanced routing." One rendering bug (leading `=`/`+` characters
  in table cells being misparsed as Typst markup) was found and fixed
  here (Section 5).
- **Misconceptions and questions (Stage 12).** Exactly the 2 required
  boxed misconceptions ("2/64 of the whole model," "inactive experts
  consume no memory"). 8 formal question records added to
  `questions.yaml` (`q-04-ch5-001` through `008`): 3 general
  quick-check items (explanation/explanation/compare_and_contrast), 2
  misconception-check items (the 2 boxed ones, each with a paired quiz
  item), 1 calculation, 1 design exercise, 1 interview-style question
  — matching Stage 12's exact target composition.

## 4. Build integration (Stage 14)

- `index.qmd`: added `chapters/05-mixture-of-experts.qmd` (with a
  `#pagebreak()` before it) and
  `solutions/05-mixture-of-experts-solutions.qmd`. Title/subtitle
  updated to "Five-Chapter Review Pilot"; "How to use" and
  notation-reference text updated to "Chapters 1-5."
- `draft-scope-note.qmd`: updated to "Chapters 1 through 5," disclosing
  Chapter 5's excluded-topics list explicitly.
- New `scripts/build_ch01_05_review.py` and `make review-ch01-05`
  target, superseding `build_ch01_04_review.py` the same way each
  prior script superseded its predecessor (documented in both
  scripts' docstrings and the Makefile). The old script and its frozen
  PDF are left in place.
- `notation.yaml` and `notation-summary.qmd` extended with `p_e`,
  `p_s`, `p_base` (E and k already existed from the original bootstrap
  pass; their meanings were tightened to explicitly say "routed"
  experts, since Chapter 5 now distinguishes routed from shared).

## 5. Testing and bugs found (Stage 15)

New `tests/test_ch05_worked_examples.py` (26 tests): independent
recomputation of both worked-example formulas, a hard invariant that
$E/k$ (4.0) is NOT approximately equal to the complete model's ratio
(1.4), the check-your-understanding Q6 instantiation checked
independently, a hard check that the routing-imbalance script's
assignment matches the figure's assignment exactly (so the worked
example and the figure describe the same concrete scenario, not two
different ones), figure/render pairing, exactly-3-figures enforcement,
citation resolution (asserting `src-36` is cited), no banned
substrings or raw schema enums, at-most-2-boxed-misconceptions, a
Stage-15 review-phrase hedging scan, disclosed-deferred-topics
presence, and page-budget structure/ceiling checks. Full project
suite: **129 tests, all passing**
(`python3 -m unittest discover -s tests`). `git diff --check`: clean.

**Two real bugs found and fixed during drafting/review**, both before
this report's tests were finalized:

1. **Worked-example/figure mismatch.** The routing-imbalance script
   initially used 8 tokens with a different assignment than
   `fig_moe_routing_parallelism.py`'s hand-chosen 6-token assignment —
   the chapter text and figure would have described two different
   scenarios. Fixed by changing the script to use the identical
   6-token assignment (and a capacity factor, 1.2, that actually
   produces a nonzero overflow, since 1.5 happened to produce exactly
   zero overflow for this specific load pattern) and adding a test
   (`test_matches_figure_assignment`) asserting they stay in sync.
2. **Typst table-cell misparsing.** Two comparison-table cells starting
   with a bare `=` or `+` character (`"= total"`, `"+ reduced routed
   redundancy"`) were silently reinterpreted by Typst as block-level
   heading/list markup — rendering as a giant auto-numbered heading
   ("8 total") and an ordered-list item ("1. reduced routed
   redundancy") instead of table text. Found only by rendering and
   visually inspecting the actual PDF page, not by any automated
   check. Fixed by rephrasing both cells to not start with a bare
   `=`/`+` ("equals total," "also reduces routed redundancy," "also
   costs always-active compute"); re-verified by rebuilding and
   re-inspecting the page.

Extracted-PDF-text searches (whole 50-page document) for
`figures/source`, `data/worked-examples`, `workbooks/04`,
`shared/question-schema`, `misconception_diagnosis`,
`compare_and_contrast`: **zero occurrences of any**. A manual scan for
"only," "exactly," "always," "no memory," "no compute," "balanced,"
"specialization," "faster," "cheaper," "2/64" across the full document
found no unqualified occurrences in Chapter 5 or its answer key; the
handful of hits elsewhere are pre-existing, already-correctly-hedged
content from Chapters 1-4 (e.g. Chapter 1's "faster" appears only
inside a rejected "common trap" quote).

## 6. Visual and technical review (Stage 16)

All 50 pages were rendered to PNG (170 DPI) and inspected — Chapter
5's 5 instructional pages, its 3 figures, its comparison table, its
check-your-understanding/answer-key page, and the front matter (to
confirm the notation-table addition didn't disturb earlier chapters)
were each viewed individually before and after the two bug fixes above.

**Technical audit, explicitly checked:**
- Attention is never described as sparse because the FFN is MoE — the
  chapter states MoE sparsity and sparse attention are "orthogonal
  axes" in both the technical core and a dedicated compare-type
  question.
- Total and active parameters are never conflated — @eq-total-active
  and the worked example both keep the four quantities (routed total,
  routed active, model total, model active) visually and numerically
  distinct.
- Expert-bank ratios are never presented as whole-model ratios — this
  is the chapter's headline boxed misconception, and the worked
  example's own numbers (4.0 vs. 1.4) make the distinction concrete
  rather than asserted.
- Inactive experts are explicitly stated as still counted in stored
  weights (second boxed misconception, plus Figure B's "stored, not
  active for this token" legend entry).
- Active parameters are explicitly stated as not identical to FLOPs
  (the router itself costs compute too) — stated once in the technical
  core, reinforced in the interview-lens answer.
- Shared experts are included in active compute in every formula
  ($p_s$ appears in both the "expert-related active" and "model
  active" terms, never omitted).
- Routing weights ($\alpha_e(x)$) and expert outputs
  ($\text{Expert}_e(x)$) are kept as distinct symbols in
  @eq-moe-combine, never conflated into one quantity.
- Load balancing is explicitly described as "encourages, but does not
  guarantee" balance — stated in the technical core and tested by the
  hedging-scan test.
- Communication cost is acknowledged explicitly (Figure C, the
  expert-parallelism paragraph, the comparison table's "distributed
  communication" row, and the interview-lens answer's fourth
  quantity).
- Model-specific values: none are stated as fact in the chapter body
  (the worked examples use an explicitly-labeled toy config); the one
  real-model-adjacent claim (DeepSeekMoE's shared-expert configs) is
  cited to its verified primary source, not asserted from memory.

## 7. Page budget (Stage 14/16)

| Section | Actual pages |
|---|---|
| Front matter | 4 |
| Chapter 1 (instructional) | 9 |
| Chapter 2 (instructional) | 9 |
| Chapter 3 (instructional) | 7 |
| Chapter 4 (instructional) | 7 |
| **Chapter 5 (instructional)** | **5** |
| Answer Key: Chapter 1 | 1.6 |
| Answer Key: Chapter 2 | 2.0 |
| Answer Key: Chapter 3 | 1.6 |
| Answer Key: Chapter 4 | 1.0 |
| **Answer Key: Chapter 5** | **~0.69** |
| Build note + bibliography | 2.1 |
| **Total** | **50** |

Chapter 5's instructional content lands **exactly** at the 5-page
preferred budget, and its answer key at **~0.69 pages**, comfortably
under even the 0.75-page preferred target (hard maximum was 1.0) —
this is the best-fitting chapter of the pilot so far, on both
dimensions simultaneously. Chapter 5's word count is **2,205**
(1,853 instructional + 352 answer key).

**Full-workbook projection.** Before this chapter (per
`reports/04_ch04_draft_report.md`), the projection was 68-70.7 pages.
Chapter 5's actual 6-page total (5 + 0.69, rounding) is well under its
own previously-provisioned 5.75-7.8-page range. Updating
`page-budget.yaml`'s projection with the actual 50-page total and the
unchanged (not further loosened) Chapters 6-8 provisional ranges gives
a **revised projected full-workbook range of 67-68.9 pages** — within
the 72-page hard ceiling on both ends, and now also touching the low
end of the original 60-68 preferred range. This is **not** used as
license to relax Chapters 6-8's budgets; they remain the same
provisional numbers set after Chapter 4.

## 8. Deferred material

Per Stage 1's explicit exclusions, this chapter does not teach: detailed
distributed-training implementation, collective-communication
algorithms, kernel optimization, inference-engine configuration,
expert quantization, model-specific benchmark comparisons,
post-training, or a survey of routing research. Expert parallelism is
covered only as one architecture-level paragraph plus Figure C —
explicitly not a systems treatment. All of these are disclosed in the
chapter's own "Sources and further reading" closing sentence and in
`draft-scope-note.qmd`, not silently omitted.

## 9. Remaining limitations

- Chapter 6 (case studies) will need to decide how to present
  model-specific active/total parameter numbers (e.g. DeepSeek-V3's
  671B/37B) that this chapter deliberately avoided — that is Chapter
  6's job, not resolved here.
- The full-workbook projection's comfortable margin (67-68.9 vs. a
  72-page ceiling) assumes Chapters 6-8 hold to their provisional
  budgets; Chapter 4's own experience (landing at its hard maximum
  despite trimming effort) shows this is not automatic.
- No independent re-audit of Chapters 1-4's content was performed
  beyond what this chapter's own cross-references (Chapter 3's KV-cache
  formula, Chapter 4's sparse-attention distinction) required.
- The Typst table-cell-misparsing bug (Section 5) was caught only by
  visual inspection, not by any automated test — a similar bug could
  exist undetected in earlier chapters' tables if none of their cells
  happened to start with a bare `=` or `+`. A full re-scan of Chapters
  1-4's tables for this specific pattern was done via `grep` (Section 5
  of the process, not repeated here) and found no other instances, but
  this was a targeted check, not a rendering-level guarantee.
