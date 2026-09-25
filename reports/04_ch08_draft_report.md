# Draft Report — Workbook 04, Chapter 8 (Final Content Chapter)

Date: 2026-09-25
Scope: drafting, illustrating, rendering, and validating Chapter 8
("Emerging Directions and Architecture Synthesis: Looped Depth, Design
Tradeoffs, and How to Read What Comes Next") of workbook 04 -- the
final content chapter, added to the existing Chapters 1-7 pilot. No
other workbook was begun; no final publication-level editorial pass
was performed (see `reports/04_release_candidate_report.md`).

Final artifact: `outputs/04-modern-llm-architecture-workbook-rc1.pdf`
(68 pages, all 8 chapters). Build command: `make release-candidate-v1`
(`scripts/build_release_candidate_v1.py`). All prior chapter-range
review PDFs (`-ch01-02` through `-ch01-07`) were left untouched.

## 0. Preflight

HEAD was `c74391f` ("Draft architecture-to-systems chapter and series
roadmap") with a clean working tree, matching expectations.
`outline.yaml`'s existing ch8 entry ("Synthesis and practice") and
`config/series-topic-roadmap.yaml`'s `recurrent-depth-looped-transformers`
topic (`primary_home.location: "ch8 (or a compact emerging-architectures
appendix)"`) agreed with this task's premise -- ch8 is confirmed as
this workbook's assigned primary home for recurrent depth/looped
transformers, not a silent scope replacement.

## 1. Rescoping ch8 (Stage 2, disclosed)

`outline.yaml`'s pre-existing ch8 plan ("no new concepts... explicitly
a review/practice capstone") was rescoped to match this session's task:
looped depth taught at full mechanism depth, fixed-vs-adaptive
computation, an MTP bridge, a 10-question synthesis framework, and one
cumulative design exercise -- replacing the old worksheet-only plan.
Updated in place: `outline.yaml` (new `drafting_note`, `estimated_pages`
6->4), `figure-plan.yaml` (the old "compact visual reference sheet"
replaced with two new figures), `example-plan.yaml` (added the
looped-depth arithmetic example and the cumulative design exercise),
`question-plan.yaml` (added ch8's own 4-question quick-question block,
a misconception entry, and an interview-style entry -- ch8 previously
had zero dedicated quick questions by design; the blueprint test
enforcing that exception was updated accordingly), `notation.yaml`
(added $L_{\text{distinct}}$, $T_{\text{passes}}$, $L_{\text{effective}}$),
`glossary.yaml` (added three new terms), `source-coverage.yaml` (added
five new ch8 claim entries, including one for the GPT-6 Astra
uncertainty caveat with zero primary sources by design).

## 2. Page budget (Stage 1) — a disclosed hard-maximum result

| Section | Preferred | Hard max | Actual |
|---|---|---|---|
| Instructional | 4 pages | 5 pages | **5 pages** (hard max, matching Chapter 6's pattern) |
| Answer key | 0.5 pages | 0.75 pages | **~0.65 pages** |
| Figures | 2 | 2 | 2 |
| Boxed misconceptions | 1 | 1 | 1 |
| Questions | 5-6 | 5-6 | 6 (4 check-your-understanding + 1 applied exercise + 1 interview lens) |

The instructional-page result required one compression pass (a
shortened "Why architecture keeps evolving" paragraph, tighter figure
spacing) before settling at the 5-page hard maximum -- looped depth's
full mechanism treatment, two verified examples, a fixed-vs-adaptive
table, a worked arithmetic example, an MTP bridge, the 10-question
framework, a figure, a boxed misconception, and the cumulative design
exercise did not compress into 4 pages without cutting a required
element. The answer key needed a much larger compression pass: the
initial draft's design-exercise answer (item 5) alone spilled across
two pages, putting the whole answer key at roughly 1.3 pages -- nearly
double the 0.75-page hard maximum. Rewriting every answer more tersely
(especially items 5 and 6) brought it down to ~0.65 pages.

## 3. A rendering bug caught only by visual inspection

The chapter's first draft tried to lay out the 10-question synthesis
framework as two visual columns by writing pairs like `"1. What is
reused? 6. How many block/module applications run per token?"` on one
line. Typst rendered this as a single list item containing both
questions as plain text, not two columns -- confusing and wrong. Found
only by rendering the page to PNG and reading it, not by any automated
test. Fixed by using one straightforward 10-item ordered list instead
of attempting a two-column layout in Markdown.

## 4. Looped depth taught at full mechanism depth (Stages 3-4)

$L_{\text{effective}} = L_{\text{distinct}} \times T_{\text{passes}}$ for
a fixed full-stack loop. The chapter explicitly states: the same block
weights are reused across passes; hidden states evolve pass to pass;
effective computation depth increases; distinct-parameter storage does
not increase proportionally; compute still occurs for every
application; shared weights imply neither shared intermediate
activations nor one shared KV-cache across passes. Depth recurrence
(looped transformers) is explicitly distinguished from sequence
recurrence (ch. 6's Mamba/SSM state, [@src-37]) -- both called
"recurrent" casually, but named as different mechanisms in the text
itself, verified present by an automated test.

## 5. Two verified examples, deliberately different loop policies (Stage 6)

- **Mixture-of-Recursions** ([@src-40], Bae et al., 2025) -- explicitly
  labeled a *research proposal*: adaptive per-token recursion depth via
  a router, with the paper's own "recursion-wise caching" vs. "recursive
  sharing" comparison used as the chapter's primary source for the
  KV-cache caveat specifically.
- **Nanbeige4.2-3B** ([@src-42], arXiv v2 dated 2026-07-27) --
  explicitly labeled a *released, open-weight model*: a fixed two-pass
  loop over a 22-layer stack (44 total block applications), chosen to
  raise effective depth under a fixed parameter budget.

Both were verified via full-text PDF extraction in the prior
series-topic-roadmap session (not re-verified from scratch, since
nothing about either source changed) and are explicitly stated as
different design choices, not interchangeable.

**GPT-6 Astra caution.** Per this task's explicit instruction, the
chapter includes a visible callout: "Public reporting has associated
recurrent depth with 'GPT-6 Astra,' but no official technical source
confirms this architecture -- this workbook does not treat that
proprietary architecture as verified." This exact language is checked
by an automated test (`test_astra_uncertainty_language_present`).

## 6. Fixed vs. adaptive computation (Stage 5)

A three-row table (fixed loop count, adaptive halting, token-level
recursion routing), each with its idea/benefit/complication, plus the
explicit caveat that "a released implementation may compute all passes
before selecting an exit even when a paper describes early exit" --
research-proposal behavior and released-implementation behavior are
not assumed to match.

## 7. Worked example (Stage 7)

$L_{\text{distinct}}=22$, $T_{\text{passes}}=2$ (matching
Nanbeige4.2-3B's own reported loop policy for the loop-COUNT numbers
specifically) vs. a conventional 44-distinct-block stack, under an
explicitly-illustrative equal-per-block-size assumption (not
Nanbeige's own exact parameter breakdown). Backed by
`data/worked-examples/looped_vs_unrolled_depth.py`: block-parameter
ratio is exactly $1/T_{\text{passes}}=0.5$; block applications are
equal (44=44); the complete-model ratio (0.59) is verified to be
strictly greater than 0.5, confirming the chapter's own claim that
embeddings/output heads/routers prevent the two ratios from being
equal.

## 8. Figures (Stage 8)

Exactly two, both original SVGs:

- `fig-looped-vs-unrolled-depth`: three panels (single pass; looped
  2-pass; unrolled 44-application view with repeated-weight-identity
  markers and schematic pass-specific cache icons).
- `fig-architecture-decision-map`: seven mechanism nodes (ch. 1-7's six
  mechanisms plus looped depth... resolved to seven total including
  MTP) each under the one resource/behavior header it primarily
  changes, with MTP's node given two dashed bridge arrows to
  "Workbook 5: training objective" and "Workbook 6: optional
  speculative-drafting use" instead of a resource-axis header.

## 9. MTP bridge (Stage 9)

A single callout, not a re-teaching of ch. 7's own MTP cross-reference:
standard training predicts $t{+}1$; MTP adds objectives/modules for
further offsets; auxiliary components may be removed at inference or
repurposed to propose draft tokens; proposing tokens does not by
itself define the complete speculative-decoding algorithm. No
acceptance/rejection mathematics, lossless-distribution proofs,
draft-model scheduling, serving-engine configuration, or
acceptance-rate optimization are taught -- all explicitly deferred to
workbook 6.

## 10. Synthesis framework and cumulative design exercise (Stages 10-11)

The 10-question framework (reused verbatim from this task's own list)
organizes the chapter without adding a wider model catalog. The
cumulative design exercise (long-context, weight-memory-constrained,
moderate-concurrency multi-GPU serving) is posed in-chapter only, with
its answer -- one defensible design, one alternative, evaluation
criteria, and common overclaims to avoid -- given only in the answer
key, matching the applied-exercise pattern established in chapters 6-7.

## 11. Misconception and questions (Stage 12)

One boxed misconception: "Reusing the same layers gives the depth of a
larger model at the compute and cache cost of the smaller model,"
corrected in three parts (distinct storage may be smaller; compute is
not reduced; cache is not automatically shared). Six total questions:
2 looped-depth recall checks, 1 parameter-vs-compute calculation, 1
misconception check, 1 design exercise (the cumulative scenario, as the
applied exercise), 1 interview-style question (the suggested
three-way-scaling-comparison prompt).

## 12. Sources (Stage 13)

No new sources were registered this session -- all of chapter 8's
citations (`src-38`, `src-40`, `src-42`, `src-43`, plus `src-14`,
`src-15`, `src-39`, `src-41`, `src-46`-`src-49`) were already verified
and registered in the prior series-topic-roadmap session. The four
Raschka sources (`src-46`-`src-49`) are cited only as
expert-explanatory/source-discovery aids, never as a substitute for a
primary source on any specific mechanism claim -- consistent with
their own registry entries' `authority_type`.

## 13. Validation (Stage 15)

Added `tests/test_ch08_worked_examples.py`: the looped-depth arithmetic
(L_effective, the block-parameter ratio, the complete-model-ratio
inequality), learner-facing-text cleanliness (including the Astra
uncertainty-language check and the depth-vs-sequence-recurrence
distinction check), citation resolution, figure/render pairing,
question-count range, and page-budget validity (including a new check
that no `*_provisional` key in `page-budget.yaml` still lists any
chapter, now that Chapter 8 is workbook 04's last one).
`python -m unittest discover -s tests` passes all 234 tests;
`git diff --check` reports no whitespace errors. Manually searched the
full release-candidate PDF text for every Stage 15 phrase ("Astra
uses," "confirmed," "free compute," "free depth," "same KV cache,"
"half the model," "exact speedup," "MTP is speculative decoding,"
"hidden chain of thought") -- no unhedged occurrence of any of them was
found anywhere in the document.

## 14. Visual and technical review (Stage 16)

Rendered all 68 pages to PNG and inspected Chapter 8's own pages
(52-56, 65-66), plus a whole-book integration spot-check (title page,
full table of contents confirming all 8 chapters and 8 answer keys
with correct page numbers, and the final bibliography page confirming
sources 25-33 render with complete URLs). Two issues were found and
fixed (Sections 2-3 above: the answer-key length, and the 10-question
list rendering bug). Technical audit confirmed: effective depth is not
equated with parameter count anywhere; weight sharing is not called
compute sharing; cache sharing is not assumed; fixed and adaptive loops
are kept as distinct rows in their own table; depth recurrence and
sequence recurrence are named as different mechanisms in the chapter's
own text; research-proposal and released-implementation behavior are
distinguished per example; the Astra caveat is present verbatim; MTP is
explicitly not equated with speculative decoding; speculative decoding
is deferred to workbook 6, not taught; and architecture is stated as
not determining benchmark quality or latency alone, both in this
chapter's own recap and as this workbook's closing line.

## 15. Deferred / out of scope

Consistent with the task's explicit exclusions: MTP's training
mechanics (workbook 5), the speculative-decoding algorithm in full
(workbook 6), and a from-scratch derivation of adaptive-halting
training objectives are all out of scope. No new workbook was begun.
No final publication-level editorial pass was performed -- see
`reports/04_release_candidate_report.md` for the explicit disclosure of
what remains before this can be called a finished book.

## 16. Commit

See the commit this report accompanies for the final SHA. Working tree
was clean before this session's changes; nothing was pushed to any
remote.
