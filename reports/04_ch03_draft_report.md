# Draft Report — Workbook 04, Chapter 3

Date: 2026-09-23
Scope: drafting, illustrating, rendering, and validating Chapter 3
("Attention Head Structure and Cache-Efficient Variants") of workbook
04, added to the existing Chapters 1-2 pilot. Chapters 4-8 were not
drafted, per instructions.

Final artifact: `outputs/04-llm-architecture-ch01-03-review.pdf`
(35 pages). Build command: `make review-ch01-03`
(`scripts/build_ch01_03_review.py`). The prior
`outputs/04-llm-architecture-ch01-02-review.pdf` (26 pages) was left
untouched, not overwritten — it is a frozen historical checkpoint, per
`scripts/build_ch01_02_review.py`'s new superseded-script notice.

## 1. Blueprint conflict, disclosed and resolved

The task governing this chapter explicitly scoped Chapter 3 to MHA,
MQA, and GQA only, with an explicit "do not substantially teach: MLA"
instruction and a 7-preferred/8-hard-maximum instructional-page budget.
`outline.yaml`'s and `outline.md`'s existing chapter-3 plan (written
during an earlier session) assigned MLA to chapter 3 as well ("MHA ->
MQA -> GQA -> MLA as one progression"), with a 9-page estimate that
assumed that MLA content.

This is a real, structural conflict between the approved blueprint and
this task's explicit instructions, not a minor wording difference.
Per the task's own Stage 0 instruction ("if this prompt conflicts with
the approved chapter boundary, preserve the intended learning goals
while documenting the adjustment"), the resolution taken:

- Chapter 3, as drafted, covers MHA/MQA/GQA and the KV-cache formula
  they share. It ends with one unnamed, one-sentence forward reference
  to "a further latent-compression technique" left for a later
  chapter — not a taught mechanism, and MLA is never named in the
  chapter body (verified by a dedicated test,
  `test_mla_not_substantially_taught_in_chapter_3`).
- `outline.yaml`'s ch3 entry was updated in place: a `drafting_note`
  field records the deviation and its reasoning; every MLA-specific
  item (learning objective, core concept, equation, worked example,
  figure, misconception check, question, primary source) that was
  previously inline in ch3's plan was moved, verbatim, into a new
  `deferred_content` sub-block rather than deleted, so no planning work
  is lost. `outline.md` gained a matching prose section. `glossary.yaml`'s
  MLA entry's `chapter` field was changed from `"ch3"` to an explicit
  `"deferred"` marker naming where the decision is recorded.
- **MLA's actual future chapter placement is an open decision, not
  resolved here.** The two candidates (a later addition to chapter 3,
  or a slice of chapter 6's case studies, since DeepSeek-V2/V3 are
  already chapter 6's MLA-bearing case-study source) are both named in
  `outline.yaml`'s `drafting_note`, but neither is chosen. This must be
  decided explicitly before chapter 6 is drafted.
- `outline.yaml`'s chapter-3 `estimated_pages` was revised from 9 to 8,
  and the workbook-wide `estimated_total_pages` from 56 to 55, to match
  the descoped chapter.

## 2. Chapter 3 content

- **Notation (Stage 3).** Added `T_q` (query positions in the current
  step) to the project-wide `notation.yaml`, since neither Chapters 1-2
  nor the existing table distinguished "positions retained in the
  cache" ($S$) from "positions this step is computing queries for"
  ($T_q$) — a distinction chapter 3's decode-step discussion needs.
  `notation-summary.qmd`'s quick-reference table was extended with
  $T_q$, $H_{kv}$, and $\text{bytes\_per\_elem}$, and its caption
  updated from "Chapters 1-2 only" to "Chapters 1-3 only."
- **Technical core (Stage 4).** MHA → MQA → GQA presented as one axis
  ($H_{kv}$ ranging from $H_q$ down to 1), with an explicit statement
  of what stays fixed (query projection shape, output projection
  shape, per-head output shape, query-side computation count) versus
  what changes (K/V projection shape, cache size). Four projection-
  parameter formulas ($P_Q, P_K, P_V, P_O$) and the KV-cache formula
  ($M_{KV} = 2BSLH_{kv}d_{\text{head}}\,\text{bytes\_per\_elem}$) are
  both stated with every symbol defined, matching
  `notation.yaml`'s `formula_assumption_checklist`. The KV-cache
  formula's exclusion list (allocator overhead, page metadata,
  fragmentation, workspaces, framework buffers, sharding layouts,
  prefix-sharing, unstated quantization) is stated in full. Decode-time
  computation is described without ever claiming a fixed speedup
  factor — "GQA makes attention some fixed multiple faster" is
  explicitly named and rejected.
- **Worked examples (Stage 5-6).** One script,
  `data/worked-examples/attention_head_variants.py`, produces both the
  KV-cache and projection-parameter numbers from one shared base config
  ($L=32$, $H_q=32$, $d_{\text{head}}=128$ so $d_{\text{model}}=4096$,
  $S=8192$, $B=1$, bf16). Exact results: MHA/GQA($H_{kv}=8$)/MQA
  cache sizes are 4 GiB / 1 GiB / 128 MiB (4x / 32x smaller than MHA);
  the $B=16$ concurrency extension scales every number linearly by 16x
  (64 GiB / 16 GiB / 2 GiB). Per-layer attention parameters: $K$+$V$
  shrinks by exactly the same ratio as the cache (0.25x for GQA,
  0.03125x for MQA), but the complete attention block ($Q$+$K$+$V$+$O$)
  shrinks by only 0.625x and 0.516x respectively — the chapter's
  central point, made numeric.
- **Figures (Stage 7).** Exactly 3, matching the task's target (not the
  blueprint's originally-planned 4, since the 4th was the now-deferred
  MLA figure):
  1. `fig-mha-mqa-gqa-head-sharing` — three panels (MHA/GQA/MQA) at a
     constant $H_q=8$, query heads fanning into 8/2/1 key-value heads.
  2. `fig-tensor-shape-gqa` — Q/K/V logical shapes, MHA vs. GQA, with
     the one differing axis outlined.
  3. `fig-kv-cache-scaling` — a log2-height-scaled bar chart of the
     worked example's three cache sizes, values labeled directly in
     linear units, captioned with the logical-vs-measured caveat.
  All three were built fresh (not reusing the blueprint's planned
  `fig-mla-compression-reconstruction`, which was dropped along with
  MLA). One real bug was found and fixed during drafting: figure 1's
  three panel-notes were long enough to overflow their columns and run
  into each other, with the last one clipped at the canvas edge —
  fixed by shortening each note to a two-line label.
- **Analogy (Stage 8).** One analogy (readers/index/store), with a
  named breakdown (K/V are learned projections, not literal documents;
  sharing changes representational capacity, not just storage).
- **Comparison table (Stage 9).** One table (MHA vs. GQA vs. MQA) with
  qualitative, non-ranked language throughout ("intermediate," "a
  tunable tradeoff point") — no "best/fastest/negligible loss" claims;
  verified by a dedicated test scanning for exactly those phrases.
- **Misconceptions (Stage 10).** All 5 required misconceptions are
  addressed. 4 got full boxed callouts ("GQA reduces query heads,"
  "the KV-cache formula = exact GPU memory," "4x cache cut ⇒ 4x smaller
  model," "MQA is universally superior") — 2 of these are paired with
  a formal quiz question, the other 2 stand alone in the technical
  core. The 5th ("reducing KV heads reduces every attention FLOP by
  the same factor") is addressed as a concise inline correction inside
  the decode-time-computation paragraph rather than its own box, since
  it fits naturally as that paragraph's closing point rather than
  needing a separate box. This ended up as 4 boxed + 1 inline rather
  than the originally-planned 2 boxed + 3 inline, a page-budget-neutral
  judgment call made while drafting (each of the 4 turned out to need
  its own precise wording once written, not just a passing mention).
- **Questions (Stage 11).** 9 formal records added to `questions.yaml`
  (`q-04-ch3-001` through `009`, chapter slug
  `"attention-head-structure"`): 4 general quick-check items (mixed
  recall/explain/calculation types), 2 misconception-check items, 1
  additional calculation, 1 design exercise, 1 interview-style
  question — matching the task's "3-4 quick + 2 misconception + 1
  calculation + 1 design + 1 interview" target exactly. All use
  human-facing display labels only (Quick check / Explain / Calculation
  / Misconception check / Design exercise / Interview practice); no
  schema enum, id, or YAML path appears in learner-facing text.
- **Sources (Stage 12).** Primary: [@src-19] (MHA/Transformer),
  [@src-20] (MQA), [@src-21] (GQA, including its ~5%-of-pretraining
  uptraining figure, stated as their own reported number). Secondary:
  [@src-14], [@src-10]. No model-adoption claims were inferred from the
  GQA paper alone; no model catalog was added; MLA was not introduced
  merely because a GQA-vs-MLA comparison would be tempting.

## 3. Build integration (Stage 13)

- `index.qmd`: added `chapters/03-attention-head-structure.qmd` after
  chapter 2 (with a `#pagebreak()` before it, matching chapter 2's
  treatment) and `solutions/03-attention-head-structure-solutions.qmd`
  after the chapter 1/2 solutions. Title/subtitle updated to
  "Three-Chapter Review Pilot"; the "How to use" and notation-reference
  text updated to say "Chapters 1-3."
- `draft-scope-note.qmd`: updated to "Chapters 1, 2, and 3," with an
  explicit note that MLA is not yet covered and its placement is
  undecided.
- New `scripts/build_ch01_03_review.py` and `make review-ch01-03`
  target, rather than overwriting `scripts/build_ch01_02_review.py`'s
  target — the old script now carries a superseded-script notice
  (running it would render the same 3-chapter `index.qmd` and mislabel
  the output). The old script and its frozen PDF are left in place.
- `scripts/generate_build_note.py`'s `--provenance-note` mechanism
  (added in the Chapters 1-2 revision pass) was reused, with one new
  chapter-3-specific provenance note stating the KV-cache/parameter
  figures are logical minimums, not measured memory.

## 4. Testing (Stage 14)

New `tests/test_ch03_worked_examples.py` (23 tests): independent
recomputation of the KV-cache and projection-parameter formulas (not
trusting the script's own arithmetic), binary-unit conversion checks,
a hard invariant that $P_Q$/$P_O$ never differ across variants, a hard
invariant that the total-attention-block reduction is always less
extreme than the K/V-only reduction, group-size divisibility, the
check-your-understanding Q7 instantiation checked independently,
figure/render pairing, citation resolution, no duplicate figure ids,
no banned substrings or raw schema enums in chapter-3 learner-facing
text, no unqualified superiority claims, MLA-not-substantially-taught,
and page-budget structure/ceiling checks. Full project suite: **75
tests, all passing** (`python3 -m unittest discover -s tests`).
`git diff --check`: clean.

Extracted-PDF-text searches (whole document) for `figures/source`,
`data/worked-examples`, `workbooks/04`, `shared/question-schema`,
`misconception_diagnosis`, `compare_and_contrast`: **zero occurrences
of any**. Searches for "exactly Nx times faster," "exact GPU memory,"
"always better," "no quality loss": **zero occurrences**. Every
occurrence of "universally" in the extracted text is inside a sentence
that negates it ("without claiming... universally best," "is
universally superior" inside a rejected-misconception quote, "None of
... is universally best").

## 5. Visual and technical review (Stage 15)

Every one of the 35 pages was rendered to PNG (170 DPI) and inspected.
Chapter 3's 7 instructional pages, its 3 figures, its comparison table,
its check-your-understanding page, its recap/sources page, and its
full answer-key section were each viewed individually, plus the
unchanged front matter (to confirm the notation-table and
draft-scope-note edits didn't disturb Chapters 1-2) and the
bibliography (to confirm the two new citations, [6] MQA and [7] GQA,
resolve to the correct papers).

**Issues found and fixed during this pass:**
- Figure 1 (`fig-mha-mqa-gqa-head-sharing`)'s three panel-notes
  overflowed their columns and the last one was clipped at the canvas
  edge — fixed by shortening each to a two-line label; re-verified
  against `tests/test_figures.py`'s bounds check and by re-rendering.
- The answer key's initial draft landed at exactly the 2-page hard
  maximum (pages 32-34, ~2.0 pages) rather than the 1-1.5 preferred
  range. Tightened by merging redundant "Why"/"Interview criteria"
  sentences into their "Answer" paragraphs (891 → 771 words), bringing
  it to ~1.6 pages — under the hard maximum, close to (if still
  slightly above) the preferred range. Not tightened further, to avoid
  cutting the GQA-cache-cost interview question's reasoning, which
  plays the same "preserve in full" role for this chapter that the
  causal-mask/residual-stream/prefill-decode/gated-MLP answers played
  in the Chapters 1-2 revision pass.

**Technical audit, explicitly checked:**
- $H_q$ and $H_{kv}$ are never conflated anywhere in the chapter or its
  answer key (both terms are used consistently and the distinction is
  itself the subject of misconception-check #1).
- The factor of 2 for keys and values is stated in the formula and
  named explicitly in prose ("where the factor 2 counts keys *and*
  values").
- Layer count ($L$) and a batch/concurrency assumption ($B=1$, with the
  $B=16$ extension) are both present in every worked-example
  instantiation, never omitted.
- The numeric data type (bf16, $\text{bytes\_per\_elem}=2$) is stated
  explicitly in the base config and both check-your-understanding
  calculation questions.
- Binary units are computed correctly and verified by dedicated tests
  ($2^{20}$ bytes = 1 MiB, $2^{30}$ bytes = 1 GiB); all reported byte
  counts in the chapter converted to exact round MiB/GiB values (4 GiB,
  1 GiB, 128 MiB, 768 MiB), which is a property of the chosen example
  configs, not a rounding artifact — verified bit-exact in
  `tests/test_ch03_worked_examples.py`.
- Runtime-overhead exclusions are stated once, in full, immediately
  after the KV-cache formula, and referenced again in the matching
  misconception callout and the figure 3 caption.
- Attention-compute claims are qualified throughout — no "GQA is
  $N\times$ faster" claim anywhere; the decode-time-computation
  paragraph explicitly distinguishes what shrinks (stored/moved state)
  from what doesn't (query-side computation count).
- Model-size claims are qualified: every place the chapter could have
  implied "cache reduction ⇒ proportional model shrinkage," it instead
  states the actual, smaller total-attention-block reduction number
  (1.6x for GQA, not 4x) and names the feed-forward sublayers as
  additionally untouched.

## 6. Page budget (Stage 15/16)

| Section | Actual pages |
|---|---|
| Front matter | 2 |
| Chapter 1 (instructional) | 10 |
| Chapter 2 (instructional) | 9 |
| **Chapter 3 (instructional)** | **7** |
| Answer Key: Chapter 1 | 1.6 |
| Answer Key: Chapter 2 | 2.0 |
| **Answer Key: Chapter 3** | **~1.6** |
| Build note + bibliography | 1.8 |
| **Total** | **35** |

Chapter 3's instructional content lands exactly at the 7-page
*preferred* budget (hard maximum was 8) and its answer key at ~1.6
pages (hard maximum 2, preferred 1-1.5) — both within budget, achieved
through scope discipline (deferring MLA, 3 figures instead of 4) rather
than any typography, figure, margin, or writing-space reduction.

**Full-workbook projection:** updated in
`workbooks/04-llm-architecture/page-budget.yaml`. With the pilot actual
now at 35 pages and Chapters 4-8's provisional budgets unchanged, the
projected complete-workbook range is **67-73 pages** — the high end
still exceeds the 72-page hard ceiling (previously projected at ~74
before Chapter 3 was drafted, so essentially unchanged; Chapter 3
itself landed efficiently, but that alone isn't enough evidence to
lower Chapters 4-8's estimates). **The 72-page ceiling is not yet
guaranteed feasible.** Concrete scope reductions to consider before or
during Chapter 4, without shrinking typography: (1) hold every
remaining chapter to at most 2-3 figures, following Chapter 3's
precedent rather than each chapter's original 3-4-figure plan; (2) box
at most 2 of any chapter's required misconceptions, addressing the
rest inline; (3) if a future chapter's blueprint bundles two mechanisms
without a shared formula, consider deferring the less central one, the
way MLA was deferred here.

## 7. Remaining limitations

- MLA's chapter placement is an open decision (see Section 1) and must
  be resolved before Chapter 6 is drafted.
- The full-workbook page projection's high end still exceeds the
  72-page hard ceiling; see Section 6's concrete mitigation options.
- Chapter 3 ended up with 4 boxed misconception callouts (plus 1
  addressed inline) rather than the originally-planned 2 boxed + 3
  inline — a deliberate in-drafting judgment call (Section 2), not an
  error, but it means Chapter 3 has more callout boxes than Chapters
  1-2 had per chapter (2 each), which is one contributor to watch if
  later chapters also have 5-misconception requirements and need to
  stay within a tighter page budget than Chapters 1-2 had.
- No independent source-accuracy re-audit was performed beyond what
  this drafting pass itself required (source-coverage claims for MHA,
  MQA, GQA were already `supported` in `source-coverage.yaml` from an
  earlier session; this pass did not add new claims requiring new
  entries there).
