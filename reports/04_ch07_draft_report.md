# Draft Report — Workbook 04, Chapter 7, and the Series-Wide Topic Roadmap

Date: 2026-09-25
Scope: (1) creating a series-wide topic roadmap for three cross-workbook
topics (recurrent depth/looped transformers, multi-token prediction,
speculative decoding), including verifying and registering 12 new
sources; (2) drafting, illustrating, rendering, and validating Chapter 7
("From Architecture to Systems Behavior: Memory, Compute,
Communication, and Throughput") of workbook 04, added to the existing
Chapters 1-6 pilot. Chapter 8 was not drafted, per instructions, nor
was any section of the future training/inference workbooks.

Final artifact: `outputs/04-llm-architecture-ch01-07-review.pdf`
(62 pages). Build command: `make review-ch01-07`
(`scripts/build_ch01_07_review.py`). Prior review PDFs (`-ch01-02`
through `-ch01-06`) were left untouched, not overwritten.

## 0. Preflight

HEAD was `2c48fb8` ("Draft modern architecture case studies") with a
clean working tree, matching expectations. `outline.yaml`'s existing
ch7 entry ("From architecture to systems consequences") matched this
task's expected role -- not a silent scope replacement.

## 1. Series-wide topic roadmap (Stages 1-2)

Created `config/series-topic-roadmap.yaml` (machine-readable) and
`reports/series_topic_roadmap.md` (prose rationale), recording where
each of three cross-workbook topics will be taught:

- **Recurrent depth / looped transformers**: primary home workbook 04
  ch. 8 (not yet drafted); secondary mention workbook 06 (cache/latency
  consequences, not yet drafted); interview treatment workbook 02 (not
  yet drafted); Chapter 7 (this session) adds only a one-row,
  systems-oriented preview, explicitly deferring the full mechanism to
  ch. 8.
- **Multi-token prediction**: primary home workbook 05 (not yet
  drafted); architecture bridge workbook 04 ch. 8 (not yet drafted);
  inference bridge workbook 06 (not yet drafted); Chapter 7 adds only a
  short cross-reference.
- **Speculative decoding**: primary home workbook 06 (not yet drafted);
  Chapter 7 adds only a short cross-reference alongside the MTP
  mention; the algorithm itself is not taught anywhere in workbook 04.

Twelve new sources (`src-38` through `src-49`) were verified and
registered in `sources/registry.yaml`, `shared/bibliography.bib`, and
`sources/coverage-matrix.yaml` (which also received two retroactive
entries for `src-36`/`src-37`, missed in the Chapter 5/6 sessions --
found and fixed as a byproduct of this session's more thorough pass):

- Five looped-depth primary papers (`src-38` Universal Transformers,
  `src-39` Geiping et al.'s recurrent-depth paper, `src-40`
  Mixture-of-Recursions, `src-41` Ouro/looped language models, `src-42`
  Nanbeige4.2-3B), each independently verified via full-text PDF
  download and `pdftotext` extraction -- not a search snippet or a
  fetch tool's own summary.
- One MTP primary paper (`src-43`, Gloeckle et al.), verified the same
  way, with its independent-heads design explicitly flagged as
  materially different from DeepSeek-V3's (`src-33`) causal-chain
  design.
- Two co-foundational speculative-decoding papers (`src-44` Leviathan
  et al., `src-45` Chen et al.), both verified the same way.
- Four expert-explanatory/visual-reference sources (`src-46`/`src-47`
  Raschka's looped-transformer blog/newsletter pieces, `src-48`/`src-49`
  his architecture-gallery sub-pages), verified via WebFetch of the
  live pages.

**GPT-6 Astra caution**: no official OpenAI technical source for
"GPT-6 Astra" was found. `src-46`/`src-47` themselves present the
looped-transformer claim about it as third-party-reported speculation,
not OpenAI's own disclosure -- this hedge is recorded explicitly in the
registry, the roadmap, and (see below) verified as present in Chapter
7's own text by an automated test.

## 2. Chapter 7 rescoping (Stage 3, disclosed)

`outline.yaml`'s pre-existing ch7 plan (a quantization/paging/
continuous-batching answer-key table) was rescoped to match this
session's task: a resource ledger (five distinct resource categories),
a prefill-vs-decode operational contrast, an architecture-to-systems
consequence map (GQA/MQA, MLA, sliding attention, MoE, hybrid recurrent
layers, plus a looped-depth PREVIEW row only), a minimal parallelism
overview, and a two-model diagnosis exercise. Quantization/paging/
continuous-batching are folded into the resource-ledger's
runtime-vs-architecture framing rather than kept as a standalone table.
`estimated_pages` dropped 7->4, matching the task's tighter budget.
Updated in place: `outline.yaml`, `figure-plan.yaml` (split the
original single ch7 figure into two), `example-plan.yaml` (replaced
the prefill/decode arithmetic exercise with the two-model diagnosis
exercise), `question-plan.yaml` (rebuilt the ch7 question set to match
the new 6-question composition), `estimated_total_pages` (44, was 47
pre-ch7).

## 3. Page budget (Stage 3/13) — the best-fitting chapter since Chapter 5

| Section | Preferred | Hard max | Actual |
|---|---|---|---|
| Instructional | 4 pages | 5 pages | **4 pages** (exactly preferred) |
| Answer key | 0.5 pages | 0.75 pages | **~0.68 pages** |
| Figures | 2 | 2 | 2 |
| Boxed misconceptions | 1 | 1 | 1 |
| Questions | 5-6 | 5-6 | 6 (4 check-your-understanding + 1 applied exercise + 1 interview lens) |

The instructional-page result (exactly 4, the preferred target, not
merely the 5-page hard maximum) is the best result since Chapter 5's
exact preferred-budget hit. The answer key needed one compression pass
(from an initial ~0.95-page draft) to land within its hard maximum.

Full-workbook projection updated: pilot actual is now 62 pages
(30,231 words). The remaining `chapter_8_provisional` allowance was
widened slightly (4.5->5 instructional pages at the hard end) since
Chapter 8 must now also absorb the full looped-depth/recurrent-depth
treatment Chapter 7 deferred to it -- a disclosed, deliberate widening,
not silent scope creep. Projected final total: 67-68 pages -- within
both the 60-68 preferred range and the 72-page hard ceiling, the
best-positioned projection in the pilot so far.

## 4. The resource ledger and prefill/decode (Stages 5-6)

Five resource categories (weight memory, KV-cache/state memory,
activation memory, temporary workspace, communication) are kept
explicitly separate, with a compact table distinguishing each
category's logical/architectural quantity from its measured/runtime
counterpart -- never presented as the same number, per AGENTS.md.
Prefill-vs-decode uses qualified language throughout ("often
compute-heavy," "often memory-bandwidth-sensitive") with an explicit
statement that batching, context length, and serving engine all
interact with these tendencies -- no universal claim is made.

## 5. Architecture-to-systems consequence map (Stage 7)

A six-mechanism x five-resource-dimension comparison matrix (GQA/MQA,
MLA, sliding/local attention, MoE, hybrid recurrent layers, looped
depth) with qualitative markers only -- no fabricated numeric
measurement. The looped-depth row is explicitly marked "preview only
-- see ch. 8" in both the figure and the surrounding prose, and states
the two required caveats: weight sharing lowers distinct parameter
count but does NOT automatically lower compute (the repeated block
applications still run) or cache/state size. MTP and speculative
decoding are deliberately NOT given a row -- only a short cross-
reference sentence, per Stage 7's explicit instruction.

## 6. Parallelism overview (Stage 8)

A five-row table (data, tensor, pipeline, expert, sequence/context
parallelism), each with the resource pressure it addresses and the
communication it introduces -- no communication-volume formula is
derived, and the table explicitly defers to `src-10` and a future
training workbook rather than attempting the Ultra-Scale Playbook's own
depth. `src-17` (Ultra-Scale Playbook) is cited only for the conceptual
map, consistent with its own registry entry's "access partial" caveat
-- no specific claim from its unverified body content is used.

## 7. Worked diagnosis exercise (Stage 9)

Model A (dense, GQA) vs. Model B (MoE + MLA), both hypothetical/
illustrative, sharing the same context length and concurrency.
Backed by `data/worked-examples/two_model_resource_diagnosis.py`,
which reuses ch. 3's GQA KV-cache formula, ch. 4's MLA cache formula,
and ch. 5's total/active-parameter formula VERBATIM -- no new formula
was derived, per the task's explicit instruction to avoid another long
arithmetic derivation. Computed result: Model B uses ~0.28x Model A's
logical cache but ~1.2x Model A's total weight storage, and introduces
expert communication Model A does not.

## 8. Figures (Stage 10)

Exactly two, both original SVGs:

- `fig-memory-state-lifecycle`: six resource boxes tagged with one of
  four lifecycles (persistent across training+inference; training-only;
  request-specific; implementation-dependent).
- `fig-architecture-to-consequence-map`: the six-mechanism comparison
  matrix described above.

One rendering bug was caught by visual inspection (not by any
automated test) and fixed: the lifecycle figure's third column
overflowed the canvas's right edge by 10 SVG units due to an
off-by-one width calculation; fixed by deriving column width from the
canvas width directly rather than a fixed per-column subtraction.

## 9. Misconception and questions (Stage 11)

One boxed misconception: "The architecture with fewer theoretical
FLOPs must be faster," corrected via arithmetic intensity, memory
traffic, communication, batching, kernels, scheduling, and hardware
utilization. Six total questions: 2 recall-style resource-ledger
checks, 1 prefill/decode comparison, 1 misconception check (which also
serves as the architecture-consequence-comparison question, since the
misconception itself is a FLOPs-vs-architecture comparison), 1 design
exercise (the two-model diagnosis, as the applied exercise), 1
interview-style question (the suggested "estimate serving bottlenecks
without overclaiming" prompt).

## 10. Validation (Stage 14)

Added `tests/test_ch07_worked_examples.py`: worked-example formula
reuse checks (confirming the diagnosis exercise's numbers match ch.
3/4/5's formulas exactly, not a new derivation), model-scenario value
checks, learner-facing-text cleanliness (including two internal-path-
leakage checks that initially FAILED against the first draft -- see
Section 11), citation resolution, figure/render pairing, page-budget
validity, and four new test classes for the series-wide roadmap
(`TestSeriesTopicRoadmap`, `TestRoadmapSourceRegistration`) verifying
every roadmap source id resolves in the registry, the looped-depth/
speculative-decoding source sets match exactly what was registered,
and the GPT-6 Astra caveat is present in the roadmap file itself. Two
tests in the EXISTING `tests/test_ch06_worked_examples.py` needed
updating as a direct, disclosed consequence of chapter 7 making chapter
6's own "next chapters are provisional" tracking stale (the
`chapters_7_to_8_provisional` key was renamed to `chapter_8_provisional`
now that chapter 7 is also actual) -- generalized that test to check
whichever `*_provisional` key currently exists, rather than hardcoding
one key name, so it will not go stale again at chapter 8.
`python -m unittest discover -s tests` passes all 204 tests;
`git diff --check` reports no whitespace errors. Manually re-scanned
Chapter 7's own pages for every Stage 14 review phrase ("faster,"
"slower," "compute-bound," "memory-bound," "efficient," "bottleneck,"
"scales," "fixed," "eliminates," "guarantees") -- every occurrence is
hedged, qualified, or is the misconception statement itself being
corrected.

## 11. Visual and technical review (Stage 15)

Rendered all 62 pages to PNG and inspected Chapter 7's own pages
(48-51), its answer key (59-60, sharing pages with Chapter 6's answer
key and the Build and Version Note), and the bibliography's final page
(62, confirming sources 21 and 24-28 -- the subset of the 12 new
roadmap sources actually cited in ch. 7's own text -- render correctly
with full URLs). Two issues were found and fixed:

1. The lifecycle figure's canvas-width overflow (Section 8 above).
2. **Internal-path leakage**: the chapter's own learner-facing prose
   twice wrote the literal path `` `config/series-topic-roadmap.yaml` ``
   (once in the MTP/speculative-decoding cross-reference paragraph,
   once in the Sources section) -- a violation of this project's
   established banned-substring convention for learner-facing text,
   caught only by visual inspection (the automated banned-substrings
   test did not yet check for this specific new path until it was
   added to the test's list afterward). Also found and fixed the same
   pattern in `includes/draft-scope-note.qmd` (learner-visible, though
   not covered by the automated per-chapter test). All three were
   rewritten to describe the roadmap in plain language instead of
   citing its file path.

Technical audit confirmed: weights/activations/cache/optimizer state
are not conflated (the resource ledger keeps them as five distinct
rows); prefill/decode claims are qualified ("often," not "always");
logical estimates are explicitly distinguished from measured usage (a
dedicated table); MoE active compute is not equated with total weight
storage (the diagnosis exercise's own answer keeps these as separate
numbers); looped weight sharing is explicitly NOT called compute-free
(both the figure and prose state compute is "NOT reduced"); looped
depth is distinguished from sequence recurrence (via the roadmap's
`required_distinctions` and the chapter's own ch. 3/ch. 6 cross-
references); MTP is not called speculative decoding (explicit "not the
same thing" sentence); speculative decoding is deferred to workbook 06
(stated explicitly, with no algorithmic content taught); theoretical
FLOPs are not equated with latency (the chapter's headline
misconception); parallelism types are not conflated (five distinct
rows, each with its own resource pressure and communication shape).

## 12. Deferred / out of scope

Consistent with the task's explicit exclusions: no full derivation of
communication-volume formulas, no serving-engine implementation guide,
no speculative-decoding algorithm, and no training-systems or
inference-serving textbook depth. Chapter 8 was not drafted, nor was
any section of workbooks 05/06/08. Three papers named only in `src-47`
("Beyond Parameters...", "SMELT...", "Full-bandwidth transformer")
remain unverified candidates, recorded as such rather than silently
dropped or falsely presented as checked.

## 13. Commit

See the commit this report accompanies for the final SHA. Working tree
was clean before this session's changes; nothing was pushed to any
remote.
