# Chapter Review Checklist and Workflow

Durable policy for drafting and reviewing one chapter of any workbook
in this repo. Written after Workbook 05 Chapters 1-4's review cycles,
to convert recurring review findings into persistent templates, tests,
and QA checks — so a future chapter handoff is usually one independent
acceptance review, not several correction rounds.

This document is referenced by `scripts/chapter_review_checks.py`,
`scripts/build_chapter_review.py`, and `scripts/workbook_qa.py`'s
`--chapter` mode. Read it before drafting a new chapter or reviewing
one.

## 0. Definition of done (quick checklist)

A chapter is review-ready only when every line below is true. Use
this list in a chapter-drafting or chapter-review prompt instead of
re-deriving each requirement from scratch.

- [ ] **Source-ready** — every primary source cited is read in full
      text (not abstract/registry-summary only) and registered in
      `sources/registry.yaml` + `shared/bibliography.bib` (both —
      citeproc resolves against the `.bib` file, not the registry).
- [ ] **Content-complete** — all required chapter sections present;
      no scaffold/placeholder markers remain.
- [ ] **Numerically verified** — every worked-example number quoted in
      prose is produced by a committed script with machine-readable
      output, checked by a scoped test (§7).
- [ ] **Figures semantically tested** — every new figure has a
      dedicated test of the mechanism it teaches, not only the generic
      bounds/XML check (§5).
- [ ] **Questions well-posed** — every calculation/design question's
      constraints are stated explicitly, admit at least one valid
      solution, and — if uniqueness is claimed — uniqueness is proven
      or enumerated, not asserted (§6).
- [ ] **Text sanitized** — no leaked source IDs, filenames, paths, or
      review-process language in learner-facing content (§3).
- [ ] **Visually inspected** — every rendered page viewed at full
      resolution by a pass whose job is to find faults, ideally with
      fresh context (§8).
- [ ] **Pagination clean** — no orphan continuation fragments; no
      forced breaks where unforced reflow already works (§2).
- [ ] **Bibliography complete** — never split after a single entry;
      sparse-but-complete is fine, mid-list splits are not (§2).
- [ ] **No canonical PDF or RC created** during chapter review — QA
      runs delete any canonical PDF they produce as a side effect.
- [ ] **Local commit only**, unless a task explicitly says otherwise.

## 1. Standard standalone-review structure

`shared/chapter-review-template.qmd.tmpl` + `scripts/build_chapter_review.py`
replace the old one-bespoke-file-per-chapter pattern
(`ch01-review.qmd` .. `ch04-review.qmd`, `build_wb05_ch01_review.py` ..
`build_wb05_ch04_review.py`). For **Chapter 5 onward**:

```
python3 scripts/build_chapter_review.py --workbook 05-llm-training --chapter 05
```

This auto-discovers the chapter file, solutions file, cited figures,
and cited sources by naming convention, fills in the shared template,
and produces the same review-package layout Chapters 1-4 already
established (`outputs/_development/<workbook>/chapter-<NN>-review/`:
PDF, page PNGs, contact sheet, figure copies, `review-manifest.json`).

**Chapters 1-4's existing bespoke scripts and hand-written
`ch0N-review.qmd` files are frozen, accepted artifacts.** They are not
retargeted onto the new mechanism — this is the path forward, not a
retroactive migration.

The template file uses a `.qmd.tmpl` extension, not `.qmd` — Quarto's
project-wide file discovery otherwise tries to process the template's
own unfilled `__PLACEHOLDER__` tokens as if it were a real document
and breaks *every* workbook's canonical build (found and fixed while
building this mechanism; see `git log` on this file for the exact
failure).

## 2. Pagination rules

Defaults, in order of preference:

1. No forced page break between chapter content and the Answer Key —
   let it flow onto whatever space remains.
2. Keep each question/answer/common-trap block together. Prefer a
   deliberate page break *before* a question over splitting its tail
   onto a new page.
3. Never leave only the last few lines of an answer as an orphan
   continuation on an otherwise near-empty page.
4. Keep the complete bibliography together. If it cannot fit at the
   end of the preceding page, give it a fresh page of its own — a
   sparse-but-complete bibliography page is explicitly acceptable.
5. Never add filler text solely to occupy space, to fix any of the
   above.

**Automated diagnostic** (`chapter_review_checks.run_page_density_diagnostics`,
wired into both `build_chapter_review.py` and `workbook_qa.py --chapter`):
computes per-page word count (a stdlib-only, `pdftotext`-based proxy
for ink/content occupancy — no Pillow/ImageMagick available in this
environment) and:

- flags pages below a low word-count threshold for manual inspection;
- specifically flags a Bibliography heading page with ≤1 entry whose
  list continues on the next page (`diagnose_bibliography_split`) —
  the exact Chapter 2→3 defect pattern;
- does **not** flag a bibliography that legitimately spans multiple
  pages by splitting between whole entries (verified against the real
  Workbook 05 canonical book's 11-entry, 2-page bibliography — that is
  not a defect and must not be reported as one);
- labels every flag as requiring manual inspection, never as an
  automatic failure — intent cannot always be inferred from word count
  alone.

**Known intentional layouts that must not be re-litigated** (do not
reopen these chapters over a heuristic warning):
- Chapter 2 and Chapter 3: sparse-but-complete bibliography pages.
- Chapter 4 page 12: the complete Question 5 answer block, placed
  there deliberately via one `#pagebreak()` in the shared solutions
  file.
- Chapter 4 page 13: the complete bibliography, on its own page for
  the same reason.

## 3. Learner-facing leakage checks

`chapter_review_checks.check_text_leakage(text)` rejects, in
learner-facing text:

- raw source IDs (`src-N`);
- `.qmd` / `.py` / `.yaml`/`.yml` filenames;
- `outputs/`, `workbooks/`, `scripts/` path fragments;
- review-process phrases ("review manifest", "contact sheet", "page
  render(s)", "generating script", "build instruction", "review
  package", "About this review", "release candidate N");
- commit-hash-shaped tokens;
- unresolved placeholders (`TODO`, `TBD`, `FIXME`, `XXX`, lorem ipsum).

Ordinary learner-facing phrasing — "source," "script-backed
calculation," "verified programmatically" — is deliberately **not**
matched by any pattern; see
`tests/test_chapter_review_workflow.py::TestLeakageChecker` for the
permitted-vs-rejected fixtures that pin this down.

## 4. Cross-reference checks

`chapter_review_checks.check_answer_key_cross_reference(chapter_path,
solutions_path)` generalizes the exact Chapter 3 round-1 defect: the
Answer Key's intro cross-referenced the chapter's top-level section id
(`@sec-chN`, rendering as "Section 1") instead of the "Check your
understanding" subsection specifically ("Section 1.8"). The check
requires:

- the "Check your understanding" heading to carry its own explicit
  `{#sec-chN-check}` anchor;
- the Answer Key's intro to reference *that* anchor;
- the reference to **not** fall back to the bare chapter-level anchor.

Quarto/Typst already hard-fails the build on a genuinely unresolved
`@label` (confirmed the hard way when `src-52/53/54` were cited before
their `shared/bibliography.bib` entries existed) — this check exists
for the more insidious case where a reference resolves successfully,
just to the wrong target.

**Known pre-existing gap, not fixed by this task:** Chapters 1 and 2
predate this fix and fail this specific check today (their Answer Key
intros reference the bare chapter-level anchor). This is a real,
reportable finding — see §11 — not something this task's scope
authorized fixing.

## 5. Figure correctness contract

Every figure needs, beyond a successful SVG render and the generic
`tests/test_figures.py` bounds/well-formedness check:

- a machine-readable data/layout representation separate from the
  rendered SVG (e.g. a schedule dict, a rank/group mapping) — not
  hard-coded coordinates with no underlying model;
- a **dedicated test of the semantic invariant the figure teaches**.
  Examples already in this repo: pipeline schedules need causality
  checks (`test_wb05_ch04_pipeline_schedule.py` — F before B, forward/
  backward propagation order, no double-booked time slots); process
  groups need membership/intersection checks; allocation charts need
  plotted-values-equal-computed-values checks; flow diagrams need
  edge-direction/label-agreement checks;
- readable labels at final print scale, no clipping/overlap, no
  source filenames drawn into the image;
- a caption that agrees with what the diagram actually shows (the
  exact Chapter 4 "disjoint pairs" → "shared member" correction).

`chapter_review_checks.check_figure_invariant_tests(workbook_dir)`
checks only the *existence* half (does at least one test file mention
this figure's module) — it cannot verify semantic correctness for a
figure it has never seen, and must not be treated as if it did.

## 6. Question and answer contract

For every calculation/design question:

- state every constraint explicitly, in the question itself;
- verify at least one valid solution exists;
- if uniqueness is claimed, **prove it** — enumerate the space (see
  `tests/test_wb05_ch04_question5_constraint.py`, which brute-forces
  every factorization of a target world size) rather than asserting
  it in prose;
- test the obvious counterexample a loose constraint would admit (the
  exact Chapter 4 Question 5 defect: "tp ≤ 8" admits `tp=1, dp=64`,
  which the original answer's "maximizes dp" claim did not survive);
- keep the question's prose, its Answer Key entry, and its
  `questions.yaml` record synchronized.

`chapter_review_checks.check_question_answer_correspondence(...)`
checks that the count of numbered questions in the chapter's "Check
your understanding" section, the count of numbered answers in the
solutions file, and the count of matching `questions.yaml` records
(filtered by chapter slug) are all equal — i.e. every question has
exactly one answer-key entry and one question-bank record. It cannot
verify a uniqueness *proof* exists; that remains a manual/adversarial-
review requirement, satisfied by adding a test like
`test_wb05_ch04_question5_constraint.py` per uniqueness-claiming
question.

## 7. Worked-example contract

- a deterministic script under `data/worked-examples/`, pure stdlib,
  writing a machine-readable JSON output;
- a scoped test file (named `test_wb0<N>_ch<NN>_worked_examples.py`,
  or `test_ch<NN>_worked_examples.py` if that name is not already
  claimed by another workbook — check first) that runs the script,
  asserts on its JSON output, and asserts every number repeated in
  chapter prose appears in the chapter text;
- explicit separation, in both the script's own docstring and the
  chapter prose, of: values quoted directly from a source; values
  computed from those sourced values; and deliberately chosen toy
  assumptions that are not claims about any real model or run;
- no universal performance/superiority claim derived from a toy
  example's numbers.

`chapter_review_checks.check_worked_example_scoped_test_exists(workbook,
chapter_num)` checks only that a workbook-appropriate scoped test file
exists (filtering out same-numbered files that happen to belong to a
*different* workbook — a real, pre-existing collision: see
`tests/test_ch03_worked_examples.py` / `test_ch04_worked_examples.py`,
which are Workbook 04's own Chapter 3/4 files). It does not re-verify
numeric correctness; running the scoped test itself does that.

## 8. Adversarial pre-commit review (manual, not automatable)

Before declaring a chapter review-ready, run a second pass whose job
is to find faults, not summarize accomplishments. This pass must
actually inspect, page by page, at full resolution:

- title and TOC;
- every figure, at final print scale;
- every dense table;
- all equations;
- every question and its answer;
- the transition into the Answer Key and into the Bibliography;
- the final two pages of the document;
- caption-vs-figure agreement;
- whether any stated constraint admits an unstated counterexample.

**This cannot be replaced by the automated checks above.** Every
correction round in Chapters 1-4 that found a real defect (title
hyphenation, bibliography splits, a causally-invalid pipeline
schedule, a mislabeled figure caption, an underconstrained question)
was found by *looking at the rendered pages*, not by a heuristic. Use
a fresh-context review pass (a separate agent invocation, or an
independent human reviewer) rather than trusting the drafting pass's
own summary of its work — the drafting pass's report describes what it
intended to do, not necessarily what actually rendered.

Do not commit a chapter as review-ready until every confirmed finding
from this pass is corrected.

## 9. Chapter-scoped QA command

```
python3 scripts/workbook_qa.py \
  --workbook 05-llm-training \
  --chapter 04 \
  --review-pdf outputs/_development/05-llm-training/chapter-04-review/05-llm-training-ch04-review.pdf
```

`--review-pdf` is optional; without it, the PDF-dependent checks
(build, rendered page count, text leakage, sparse-page/bibliography
diagnostics) report `"ok": null` with a "not verified" note instead of
silently skipping or falsely passing.

Reports, as independent top-level keys under `"checks"` (a warning in
one never hides a regression in another):

`structure`, `sources_and_claim_ledger`, `questions_and_solutions`,
`worked_examples`, `figure_invariants`, `cross_references`, `build`,
`rendered_page_count`, `text_leakage`, `sparse_page_warnings`,
`bibliography_diagnostic`, `full_page_visual_review_completion`
(always reports `automatable: false` — §8 is never claimed to have
run), `scoped_tests`, `full_suite` (with
`known_preexisting_workbook04_baseline_failures` and
`new_failures_beyond_baseline` reported as separate lists, never
merged).

Overall `status` is `"pass"`, `"pass_with_warnings"` (a soft-check
category failed — currently only `worked_examples`, `figure_invariants`,
`cross_references`, `text_leakage`), or `"fail"` (a hard-check
category — `structure`, `sources_and_claim_ledger`,
`questions_and_solutions`, `scoped_tests`, `full_suite` — failed, or a
genuinely new full-suite failure appeared beyond the known baseline).

## 10. Acceptance checklist

See §0 above — kept short deliberately so a chapter-drafting prompt
can reference "pass the definition of done in
`docs/chapter-review-checklist.md`" instead of restating every rule.

## 11. Validation against Chapters 1-4 (as of this writing)

Ran `scripts/workbook_qa.py --workbook 05-llm-training --chapter <NN>
--review-pdf <accepted PDF>` and the standalone check functions
against all four accepted chapters, without modifying any of them.

| Check | Ch1 | Ch2 | Ch3 | Ch4 |
|---|---|---|---|---|
| structure | pass | pass | pass | pass |
| sources_and_claim_ledger | pass | pass | pass | pass |
| questions_and_solutions | pass | pass | pass | pass |
| worked_examples (scoped test exists) | pass | pass | pass | pass |
| cross_references | **fail** (no `{#...check}` anchor) | **fail** (same) | pass | pass |
| figure_invariants (dedicated semantic test) | fail (none) | fail (none) | fail (none) | pass\* |
| full_page_visual_review_completion | manual, not re-run | manual, not re-run | manual, not re-run | manual, not re-run |

\* Chapter 4 has two figures; only `fig_pipeline_timeline.py` has a
dedicated semantic test. `fig_process_group_composition.py` does not,
so the chapter-level `figure_invariants` check still reports a
warning for Chapter 4 too.

**These are real, pre-existing findings, not corrected by this task**
(out of scope: "do not reopen an accepted chapter merely because of a
heuristic warning" / "do not modify accepted content without explicit
approval"). They are recorded here so a future task can decide whether
to spend a correction round on Chapters 1, 2, and 4's figures, or
accept the gap.

**False positives found and fixed while building this workflow** (not
left in the shipped checkers):
- `check_worked_example_scoped_test_exists` originally matched by
  filename glob alone, which also matched Workbook 04's own
  `test_ch03_worked_examples.py` / `test_ch04_worked_examples.py` — a
  real, pre-existing cross-workbook name collision. Fixed by filtering
  candidates to those whose *content* actually references the target
  workbook.
- The chapter-scoped test loader in `workbook_qa.py` failed with
  `ModuleNotFoundError: No module named 'tests'` when the script was
  invoked as `python3 scripts/workbook_qa.py ...` (as opposed to
  imported), because script-mode `sys.path` does not include the repo
  root. Fixed by explicitly adding `REPO_ROOT` to `sys.path`.
- `shared/chapter-review-template.qmd` (with a real `.qmd` extension)
  broke the canonical build for *every* workbook, because Quarto's
  project-wide file discovery tried to process its unfilled
  `__PLACEHOLDER__` include directive. Fixed by using a `.qmd.tmpl`
  extension instead.
- `build_chapter_review.py`'s first real exercise (drafting Chapter 5)
  found that the generated `ch0N-review.qmd` and Quarto's own rendered
  `ch0N-review.pdf` byproduct were left behind in `workbooks/<id>/` as
  untracked cruft after a successful build — unlike Chapters 1-4's
  hand-written, intentionally committed `ch0N-review.qmd` files, this
  generated one has no reason to persist once the PDF is copied to its
  real destination. Fixed generically (not via a bespoke per-chapter
  script) by having the builder delete both staging files in its own
  final step.

No universal rule was encoded from a single chapter's one-off choice:
the bibliography-split diagnostic was explicitly tested against both
a single-chapter review's clean bibliography *and* the full canonical
book's legitimately multi-page bibliography, so it does not flag the
latter as a defect.

## 12. Adding Chapter 5 (or any future chapter)

1. Draft the chapter, worked example, figure(s), questions, solutions,
   and claim-ledger entries following Chapters 1-4's established
   conventions (see any accepted chapter file as the concrete
   reference).
2. Give "Check your understanding" an explicit `{#sec-chN-check}`
   anchor and point the Answer Key's intro at it directly (§4) —
   Chapters 1-2 predate this and are the two known gaps; do not repeat
   it in a new chapter.
3. Build the review package: `scripts/build_chapter_review.py
   --workbook <id> --chapter <NN>`.
4. Run the chapter-scoped QA command (§9); read every warning.
5. Run the adversarial visual pass (§8) — do not skip this because the
   automated checks were clean.
6. Fix confirmed findings; rebuild; re-run §9 and §8 until clean.
7. Commit locally. Do not create a canonical PDF or release candidate
   as part of chapter review.
