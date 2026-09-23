# Draft Report — Workbook 04, Chapters 1-2 Review Pilot

Date: 2026-09-23
Scope: drafting, illustrating, rendering, and validating Chapters 1
("Transformer Refresher") and 2 ("Anatomy of a Modern Decoder") of
workbook 04 as a two-chapter review artifact. Chapters 3-8 were not
drafted, per instructions.

Final artifact: `outputs/04-llm-architecture-ch01-02-review.pdf`
(24 pages). Build command: `make review-ch01-02`
(`scripts/build_ch01_02_review.py`).

## 1. Accuracy

- **Equations.** All six of Chapter 1's equations (token embedding,
  residual update, Q/K/V projection, scaled dot-product attention,
  causal mask, next-token softmax) and Chapter 2's four (RMSNorm,
  RoPE rotation, plain FFN, SwiGLU) were checked against their primary
  sources (src-19, src-22, src-23, src-24) while drafting, and every
  symbol is defined at or immediately after first use.
- **Tensor shapes.** Verified programmatically, not just asserted in
  prose: `tests/test_ch01_02_worked_examples.py` checks that the tiny
  decoder trace's $Q$/$K$/$V$/attention-score/output shapes are
  internally consistent with the stated $d_{\text{model}}$, $H_q$, and
  $d_{\text{head}}$ for every layer of the computation, not just spot
  numbers.
- **Architectural claims.** Every claim in Chapter 2 about which
  component is a "convention" vs. a "requirement" traces to a specific
  source or an explicit hedge (see `source-coverage.yaml`'s
  `partially_supported`/`source_needed` entries for pre-norm/sandwich-
  norm and tied embeddings, both called out again in-chapter via
  callouts rather than smoothed over).
- **Causal-mask explanation.** Explicitly corrected against the
  "attend only to the immediately previous token" misconception in
  three independent places: the technical-core prose, the dedicated
  figure (@fig-causal-mask), and a formal `misconception_diagnosis`
  question record (`q-04-ch1-004`) — checked for consistency across
  all three during drafting.
- **Prefill/decode distinction.** Traced with real, reproducible
  numbers (`data/worked-examples/tiny_decoder_trace.py`), not just
  asserted: the decode step's softmax weights are verified to sum to
  1.0 and to have zero blocked entries (`test_decode_step_query_has_no_blocked_positions`),
  and the cache is verified to grow by exactly one slot
  (`test_decode_step_cache_grows_by_exactly_one`).
- **RMSNorm/gated-MLP explanation and parameter calculation.** The
  1.5x-vs-compensated parameter tradeoff is computed by
  `data/worked-examples/gated_mlp_params.py`, not hand-derived, and
  independently re-verified by three separate test assertions
  (`test_gated_same_d_ff_is_exactly_1_5x_plain`,
  `test_compensated_d_ff_lands_close_to_plain`,
  `test_applied_exercise_instantiation`).

**No accuracy issues found that weren't already fixed during drafting**
(see Section 5 for the sourcing gaps carried over from the blueprint
stage, which are disclosed, not errors).

## 2. Pedagogy

- **Prerequisites before use.** Chapter 2 explicitly reuses Chapter 1's
  residual-stream picture and receipt analogy rather than introducing
  a competing one; RoPE, RMSNorm, and SwiGLU are each introduced only
  after the generic `Norm`/feed-forward slots they fill were already
  established in Chapter 1's equations.
- **Figures reduce cognitive load, checked concretely.** Each figure
  was designed around one relationship (per the original figure plan)
  and this was checked during visual inspection, not assumed: e.g.
  Chapter 2's annotated-block figure (@fig-annotated-block) reuses
  Chapter 1's block-anatomy skeleton with components filled in, rather
  than introducing a new diagram grammar the reader has to relearn.
- **Analogies clarify, not replace.** The single residual-stream
  analogy (a receipt) includes an explicit breakdown point (contributions
  can't be individually read back out, unlike a paper receipt's
  individually-readable lines) — this was a deliberate design choice,
  not an afterthought, and is referenced again in the Chapter 1 answer
  key's misconception explanation for `q-04-ch1-005`.
- **Questions match preceding material.** Every question record's
  `source_ids` traces to a source already introduced in that chapter;
  no question requires material from Chapter 3+ (checked by construction,
  since none of the 17 new records cite anything beyond src-14/19/22/23/24).
- **Chapter transitions.** Chapter 2 opens by explicitly naming what
  Chapter 1 established and what's new, rather than assuming continuity.

## 3. Compression

- Chapter 1's "Technical core" originally risked repeating the same
  "in words" framing pattern for every equation; kept but varied in
  emphasis (embedding = lookup, residual = addition constraint,
  attention = three roles, causal mask = triangular region, logits =
  final projection) so each "in words" line adds new information rather
  than restating the equation.
- No redundant callouts were found needing combination: each callout
  (Analogy, Working approximation, Common misconception x2 per chapter,
  Implementation-dependent detail, Notation note) serves a distinct
  labeled purpose per Stage 4's simplification-labeling requirement,
  and none overlaps in content with another.
- Figure captions were written to state what to notice, not to restate
  the caption in the body text — checked by re-reading each figure's
  caption against its immediately surrounding prose during the
  visual-inspection pass; no caption merely repeats adjacent prose.
- Removed nothing post-hoc: the chapters were drafted directly against
  the outline's stated scope (Chapter 1 explicitly avoids backprop/
  training derivations; Chapter 2 avoids claiming any normalization or
  MLP design is universally best, per Stage 3's constraint) rather than
  written broad and trimmed.

## 4. Source discipline

- **Primary-source support.** RoPE, RMSNorm, and SwiGLU are each cited
  to their defining papers (src-22, src-23, src-24) for the equation
  and mechanism; the encoder-decoder/decoder-only framing and the norm-
  placement comparison use src-14 (secondary) explicitly labeled as
  such, not presented as primary.
- **Citation placement.** Every citation sits at the specific claim it
  supports (e.g. `[@src-22]` immediately after the RoPE rotation
  equation), not batched into a single end-of-section citation dump.
- **No copied prose.** All explanatory text, analogies, and the receipt
  metaphor are original to this workbook; no source's sentences were
  reused.
- **No copied figure composition.** All 7 new figures are original
  layouts generated from project-controlled Python/SVG scripts (per
  `figures/source/*.py`); the one reused figure
  (`fig_prefill-vs-decode`, via `kv_cache_demo.py`) is this project's
  own prior original work, not a third party's.
- **No unsupported "modern models generally..." claims.** Chapter 2
  explicitly rejects this pattern in its own misconception callout
  ("Every modern decoder uses exactly the same block ordering" — false),
  and every specific claim about a convention vs. requirement is
  qualified (e.g. "real, current models make both choices differently"
  rather than "models generally prefer X").
- **No new sources added.** Per Stage 5's instruction to add sources
  "only when a concrete gap appears," none of Chapters 1-2's content
  required a source beyond what the blueprint stage had already
  verified (src-14, src-19, src-22, src-23, src-24) — no broad
  literature expansion was conducted.

## 5. Visual quality

**Page-level issues found and corrected** (via actual page-by-page
visual inspection at final printed dimensions, not just compilation
success — five real bugs, none caught by the automated SVG bounds
check):

1. Equation 4 (`\text{softmax}\!\left(...\right)`): the `\!` negative-
   thin-space command caused "softmax" to visually overlap the fraction
   that followed it. Fixed by removing the `\!`.
2. Equation 5 (the causal-mask cases block): `0 & j \le i` rendered with
   almost no visible gap between the value and its condition. Fixed by
   adding explicit `\text{if}` to both cases.
3. `fig-causal-attention-mask`'s title text ("...( rows = query, columns
   = key)") overflowed its own SVG canvas width, clipping to "...columns
   = l". Fixed by shortening the title (the axis labels already convey
   the same information).
4. `fig-norm-placement`'s main title and its three panel sub-labels
   (pre-norm/post-norm/sandwich-norm) were only 5px apart vertically and
   visibly overlapped. Fixed by increasing the panel layout's base
   vertical offset.
5. A table caption used a literal `d_ff` instead of proper math notation
   ($d_{\text{ff}}$), inconsistent with the rest of the document. Fixed.

**Remaining compromise, disclosed rather than hidden:** adding the
required "prefill vs. iterative decode" figure (Stage 2's visual-concept
list) pushed Chapter 1 from 8 to 9 pages (target: 6-8) and leaves
moderate (not severe) trailing whitespace on page 8, where the figure
didn't fit in the remaining space and moved to page 9 in full. A width
reduction was tried and did not change the outcome (the figure is tall
regardless of width, at its own fixed aspect ratio), so the tradeoff was
accepted rather than shrinking the figure to the point of hurting
readability, or omitting a required visual concept to hit a soft page
target. No other page in the 24-page document has this issue — this was
the only page found with more than ~20% trailing whitespace after all
fixes above.

## Counts

- **PDF page count:** 24
- **Chapter page counts:** Chapter 1: 9 pages (pp. 3-11); Chapter 2: 8
  pages (pp. 12-19); answer key: 4 pages (pp. 20-23); build note +
  bibliography: 1 page (p. 24); front matter (title/TOC): 2 pages.
- **Approximate word counts:** Chapter 1: ~3,368 words; Chapter 2:
  ~2,852 words; answer key (both chapters): ~1,952 words; whole
  document: ~11,406 words.
- **Figure count:** 8 (7 original + 1 reused from the project's existing
  KV-cache demonstration).
- **Table count:** 4 (1 in Chapter 1, 3 in Chapter 2).
- **Question count:** 19 total in `questions.yaml` (17 new for Chapters
  1-2: 7 quick comprehension + 5 misconception checks + 2 applied
  exercises + 3 interview-style; 2 pre-existing from the Stage 7
  bootstrap sample, untouched).
- **Citation count:** 5 unique sources cited across both chapters
  (src-14, src-19, src-22, src-23, src-24).
- **New sources added:** 0.
- **Known simplifications** (all explicitly labeled in-text per Stage
  4's requirement, not presented as universally exact): the worked
  example's toy config ($d_{\text{model}}=4$, one block, hand-picked
  untrained embeddings); RoPE's figure shows one 2D rotation subspace
  at one frequency, not the full multi-frequency mechanism; tied
  embeddings is labeled an "implementation-dependent detail" rather
  than a historical/performance claim, per the tracked sourcing gap.
- **Remaining content concerns:** none blocking. Two sourcing gaps
  inherited from the blueprint stage remain open (tied embeddings has
  no dedicated primary source; RMSNorm and the MoE-routing-origin paper
  each lack an independently-verified secondary/explanatory source) —
  tracked in `reports/04_source_audit.md`, not newly introduced here,
  and both are explicitly hedged in-chapter rather than overstated.
- **Remaining visual concerns:** the single page-8 whitespace tradeoff
  described in Section 5, accepted deliberately.
- **Recommendation for the next drafting phase:** see the end of this
  report.

## Recommendation for the next drafting phase

This pilot's main finding is **not** about content quality — the
outline, sourcing, and equations held up — it's about **process**: five
of the real bugs found here (equation spacing, title overflow, label
overlap) were invisible to automated checks (`tests/test_figures.py`'s
bounds check, `quarto render`'s exit code) and were only caught by
actually opening the rendered PDF page by page at final print size. That
process now has two additional, tested building blocks that didn't
exist before this pilot: a working `{{< include >}}`-based multi-chapter
composition pattern (proven to correctly resolve citations, figures,
and cross-references across separate chapter/solution/include files
without needing a second nested Quarto project), and a
`data/worked-examples/*.py` -> `chapters/*.qmd` -> `tests/*.py` pipeline
that makes prose numbers checkable rather than trusted.

**Recommended next task: draft Chapter 3** ("Attention head structure
and cache-efficient variants") next, not all of Chapters 3-8 at once.
Chapter 3 is the single most load-bearing chapter in the blueprint (per
`reports/04_blueprint_report.md`'s drafting order, chapters 4/6/7 all
reference its KV-cache formula rather than re-deriving it) and is
planned to have the most figures (4) and worked examples (4) of any
chapter — drafting it next will show whether the patterns established
in this pilot (per-chapter figure/question/solution files, script-
backed worked examples, the width-constrained-figure convention) hold
up under a chapter with meaningfully more visual and numerical density
than Chapters 1-2, before committing to drafting the remaining five
chapters at scale.

## Revision — post-review polish pass (2026-09-23)

External review of `outputs/04-llm-architecture-ch01-02-review.pdf`
(the 24-page build referenced above) found one technical error and
several production-quality issues. This section records the fixes.
Chapter 3 was **not** drafted in this pass.

### Technical corrections

- **KV-cache vs. residual stream (the one real error).** Chapter 1's
  worked example previously stated that the post-attention residual
  stream "is exactly the state that gets cached" for the KV-cache. This
  is wrong: what gets cached is each layer's own $K$/$V$ projections,
  computed from that layer's *input*, before the attention sublayer's
  output is folded back into the residual stream. The residual stream
  is recomputed fresh at every step; the $K$/$V$ rows are what actually
  persist. Fixed in `chapters/01-transformer-refresher.qmd`'s worked
  example, with a brief, unnamed hedge for RoPE-style cached-key
  transforms so the claim doesn't go stale when Chapter 3 introduces
  them. Added a regression test,
  `test_kv_cache_is_not_the_residual_stream` in
  `tests/test_ch01_02_worked_examples.py`, which asserts the
  script-computed `K_full` and `residual_stream_after_attn` arrays
  differ (the underlying `tiny_decoder_trace.py` computation was
  already correct; only the chapter's prose narration was wrong).
- **Prefill qualification.** Added a callout in Chapter 1's worked
  example, and updated the Interview lens Q&A (chapter prose and
  `solutions/01-transformer-refresher-solutions.qmd` answer 7), so that
  "prefill processes the prompt in one pass" is presented as the
  conceptual model, with an explicit note that a production serving
  engine may chunk a long prompt for scheduling/memory reasons without
  changing the logical prefill/decode distinction.
- **RMSNorm epsilon.** Added $\epsilon$ explicitly to the RMSNorm
  equation in `chapters/02-modern-decoder.qmd`
  ($\text{RMS}_\epsilon(x) = \sqrt{\frac{1}{d_{\text{model}}}\sum x_k^2 + \epsilon}$),
  with $\epsilon$ defined in prose as a fixed, non-learned
  numerical-stability constant. The LayerNorm/RMSNorm comparison and
  the "RMSNorm drops mean-centering and the learned bias" claim are
  unaffected and remain accurate; no claim that RMSNorm is universally
  preferable was introduced.

### Reader-facing cleanup

- **Internal paths removed.** All repo-relative paths and file
  references (`figures/source/*.py`, `data/worked-examples/*.py`,
  `workbooks/04-llm-architecture/questions.yaml`, `notation.yaml`,
  `sources/registry.yaml`, `reports/04_source_audit.md`, `outline.md`)
  were removed from both chapters, both solutions files, and
  `includes/notation-summary.qmd` / `includes/draft-scope-note.qmd`.
  Reproducibility is preserved, not deleted: `scripts/generate_build_note.py`
  now takes a repeatable `--provenance-note` argument, and the Build
  and Version Note has a new "Provenance" subsection (populated by
  `scripts/build_ch01_02_review.py`) that states, in plain language,
  that worked-example numbers and figures are script-generated and
  test-checked, and that two sourcing gaps (tied embeddings, sandwich-
  norm) are tracked. All underlying scripts, records, and tests stay in
  the repo; only the rendered PDF's prose stopped naming their paths.
- **Question labels humanized.** Added a `display_labels` mapping to
  `shared/question-schema.yaml` (machine `question_type` values stay
  unchanged for `scripts/validate_questions.py`) and used it to relabel
  every in-chapter and answer-key question tag: `recall` → "Quick
  check", `explanation` → "Explain", `calculation` → "Calculation",
  `compare_and_contrast` → "Compare", `misconception_diagnosis` →
  "Misconception check", `design` → "Design exercise", and
  interview-framed questions → "Interview practice". No raw enum name
  with an underscore appears anywhere in the rendered PDF. Added
  `TestLearnerFacingTextIsClean` to
  `tests/test_ch01_02_worked_examples.py`, asserting both the absence
  of every banned path/enum substring and the presence of at least one
  humanized label in each learner-facing file.
- **Answer-key framing compacted.** Replaced the inconsistent
  "Common wrong answer" / "Common wrong answer's origin" / "Common
  mistake" / "Weak-answer pattern" / "Evaluation criteria" labels with
  a lighter, consistent set (*Answer* / *Why* / *Common trap* /
  *Interview criteria*), used only where each adds something — not
  every answer has every field. Full explanatory content was preserved
  for the four call-outs specifically flagged as worth keeping in full:
  the causal-mask misconception, the residual-stream analogy breakdown,
  the prefill-vs-decode interview question, and the gated-MLP parameter
  calculation.
- **"One-page recap" renamed to "Chapter recap"** in both chapters,
  `shared/chapter-template.qmd`, and `README.md`, since this pilot's
  recap was never redesigned as a standalone page.

### Figure changes (Stage 7)

All 8 figures (`figures/source/kv_cache_demo.py` plus the 7
workbook-local scripts) had essential labels enlarged so they print at
approximately 8-9pt at final embed size — previously, several were
printing at roughly 4-7pt because SVG font sizes hadn't been scaled for
each figure's actual embed width. Figures 1 (`fig_decoder_end_to_end`),
5 (`fig_annotated_modern_block`), 7 (`fig_rope_rotation`), and 8
(`fig_gated_mlp`) were explicitly flagged by the reviewer and received
the largest adjustments (label sizes roughly doubled, with matching box
widening so text doesn't overflow). Two nonessential in-figure
annotations that duplicated their figure's own caption almost verbatim
(`fig_decoder_block_anatomy`'s "each box below reads a normalized
COPY..." note; `fig_causal_attention_mask`'s "row 5 can see..." note)
were removed rather than shrunk further, since there was no room to
enlarge them to a legible size without overcrowding. One genuine
overlap (a label colliding with an arrowhead in the reused KV-cache
figure) was found and fixed during visual inspection. All figures were
re-rendered, re-checked against `tests/test_figures.py`'s bounds check,
and visually inspected page-by-page at final print size before this
report was written.

### Page-break changes (Stage 6)

Chapter 2 now begins on a fresh page (`index.qmd` inserts
`#pagebreak()` before its include), and Answer Key: Chapter 1 begins on
a fresh page as well, since both are major navigational boundaries and
the preceding section ends with enough trailing whitespace that the
break costs little. Answer Key: Chapter 2 was deliberately **not**
forced onto its own page — it's the same "answer key" family as
Chapter 1's, and Chapter 1's answer key already ends close to a natural
page boundary, so a forced break there would only have wasted space.
The Build and Version Note and Bibliography were left to flow
naturally; Typst's native bibliography is appended at the absolute end
of the document regardless of source order, so its position isn't a
content choice.

### Page and word counts

| Metric | Before this revision | After this revision |
|---|---|---|
| Total pages | 24 | 26 |
| Chapters 1-2 instructional pages | 17 | ~19 (Ch.1 ~10, Ch.2 ~9, boundaries approximate since chapters share page transitions) |
| Total words (pdftotext) | ~11,400 | 11,732 |

The 2-page growth comes from the two mandatory fresh-page breaks
(Chapter 2, Answer Key: Chapter 1) plus the expanded KV-cache
correction and prefill-chunking-qualification prose — both net
additions of accuracy-necessary text, not padding. See
`workbooks/04-llm-architecture/page-budget.yaml` for the full
breakdown and the projected implications for Chapters 3-8: at the
provisional per-chapter instructional-page budgets given for Chapters
3-8 (7-8, 6-7, 6-7, 5-6, 5-6, 4-5 pages respectively), plus
proportionally-scaled answer-key growth, the full eight-chapter
workbook is projected to land in the 66.5-74 page range — the high end
of which exceeds the 72-page hard ceiling. This is a projection, not a
current problem (only Chapters 1-2 exist), but it means later chapters
should be drafted toward the lower half of their provisional ranges
where the topic allows, rather than treating the upper end as a
default.

### Remaining limitations

- The two sourcing gaps carried over from the blueprint stage (tied
  embeddings has no dedicated primary source; the sandwich-norm claim
  leans on a secondary source) remain open, now tracked via the Build
  and Version Note's Provenance subsection rather than in-chapter
  path references. Neither is a new issue introduced by this revision.
- The page-budget projection above shows real risk of exceeding the
  72-page hard ceiling if Chapters 3-8 land at the top of their
  provisional ranges with proportionally-sized answer keys; this
  should be watched chapter-by-chapter as Chapters 3-8 are drafted, not
  addressed retroactively by shrinking Chapters 1-2.
- This revision did not re-run a full independent source-accuracy
  audit; it corrected the one error the external review found and
  the production-quality issues it flagged. A fresh technical-accuracy
  pass is still worthwhile before Chapters 1-2 are treated as fully
  final, independent of this pass's fixes.
