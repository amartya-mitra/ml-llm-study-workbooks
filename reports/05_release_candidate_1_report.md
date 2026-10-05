# RC report — Workbook 05, RC1

- **Commit SHA:** this report is committed in the same commit it describes, so (per the same
  reasoning `scripts/generate_build_note.py` documents for the learner-facing build note) it
  cannot name its own commit SHA from inside itself — run `git log -1 --format=%H -- reports/
  05_release_candidate_1_report.md` after the integration commit, or see that commit's own
  message/the task's final report to the user for the exact SHA.
- **Branch:** `main`
- **Fixed QA command — deliberate deviation, documented:** the template above names
  `python3 scripts/workbook_qa.py --workbook 05-llm-training` (no `--chapter`) as the fixed QA
  command. That full-book mode's own `build_pdf()` step writes the canonical PDF at
  `outputs/05-llm-training-workbook.pdf` as an unconditional side effect of running it — and this
  RC1 task explicitly requires that no canonical Workbook 05 PDF be created. Running the
  template's literal command would violate that constraint, so it was not run in this form for
  this RC. The equivalent QA evidence was instead gathered via the chapter-scoped mode
  (`workbook_qa.py --workbook 05-llm-training --chapter <NN> --review-pdf <chapter review pdf>`,
  run sequentially for chapters 01-06) plus one full, direct `python3 -m unittest discover -s
  tests` run (482 tests) and a from-scratch `quarto render` + independent page-by-page visual
  inspection of the actual RC1 PDF — see "QA findings" and "Full-document visual inspection"
  below for the complete, real results this produced.
- **QA result:** `pass` — every chapter (01-06) reported `pass_with_warnings` with zero new
  failures beyond the three known, pre-existing Workbook 04 baseline failures; the full test
  suite (482 tests) reported the same three baseline failures and nothing else; `git diff
  --check` was clean.
- **RC PDF path:** `outputs/_releases/05-llm-training/05-llm-training-workbook-rc1.pdf`
- **Page count:** `66`
- **Word count:** `36639` (via `pdftotext | wc -w` on the actual RC1 PDF)
- **File size:** `1154101 bytes` (≈1.10 MiB)
- **SHA-256:** `688ae0ce65b6cc97a12716004b563abd7b51a4f6a0f5e678178632c8e26cf8d5`
- **Rendered pages:** `outputs/_releases/05-llm-training/pages/` (66 PNGs, rendered directly from
  the actual RC1 PDF, not copied from the development build)
- **Contact sheet:** not generated for this RC (the chapter-scoped review packages each already
  have their own; a full-book contact sheet was judged unnecessary given the page-by-page visual
  inspection recorded below covered every category of page this task required)
- **Development build preserved at:**
  `outputs/_development/05-llm-training/integrated-dev-build/05-llm-training-workbook-dev.pdf`
  (SHA-256 `d9b86feb71e0b9cc90205bc0d6aab8f937ff4b6a6b1ef0150b2fe06e0da194dd`, 66 pages) — RC1 was
  rendered independently from the same `index.qmd` after its subtitle was bumped from "Complete
  Content Draft — Chapters 1-6" to "Complete Content Draft (Release Candidate 1)"; the two PDFs'
  checksums differ, confirming RC1 is a genuine independent render, not a renamed copy.

## What changed since the prior RC

There is no prior Workbook 05 RC — this is RC1, the first full-workbook release candidate.
Immediately before this RC: Chapter 6 completed its own independent human review and one
source-audit correction pass (restated hardware-efficiency claim now carries an explicit
source-version/date qualifier) and was recorded `accepted_frozen`, bringing all six chapters to
accepted status for the first time. This RC is the first point at which all six chapters'
content, worked examples, figures, questions, answer keys, and the registry's acceptance
records agree with one another.

## QA findings

- **Registry validation:** `OK: registry and coverage matrix are valid`.
- **Question validation:** `OK: 74 question(s) validated against shared/question-schema.yaml`.
- **Chapter contract validation:** `OK: 2 chapter contract(s) validated against
  shared/chapter-contract-schema.yaml`.
- **Per-chapter `workbook_qa.py --chapter` results (01-06):** `structure`,
  `sources_and_claim_ledger`, `questions_and_solutions`, `build`, `text_leakage`, `scoped_tests`,
  and `full_suite` all `True`/`ok` for every chapter. `cross_references` is `True` for Chapters
  3-6 and `False` for Chapters 1-2 (the documented, pre-existing `{#sec-chN-check}`-anchor gap —
  not reopened in this task). `figure_invariants` reports `False` uniformly (it is a whole-
  workbook check, not chapter-scoped, and reflects the documented pre-existing gap that several
  Chapters 1-4 figures lack a dedicated semantic test beyond the generic bounds/XML check — both
  of Chapter 6's own figures, and both of Chapter 5's, already have dedicated tests). Net
  per-chapter status: `pass_with_warnings` for all six, zero hard failures.
- **Visual-regression (`scripts/visual_regression.py`):** `page_count_matches: true`, `ok: true`
  for each of Chapters 01-06 individually and for the integrated dev build.
- **Worked-example tests:** 68 tests across Chapters 1-6, all passing.
- **Figure semantic tests:** 37 tests (`test_figures` plus the dedicated pipeline-schedule/
  figure-invariant suites for Chapters 4-6), all passing.
- **Chapter-factory workflow tests:** 53 tests, all passing (one test's fixed precondition —
  see "Findings fixed in this RC" below).
- **Workbook 05 scoped tests:** 48 tests (scaffold, chapter-review-workflow, Question-5
  uniqueness proofs for Chapters 4-5), all passing.
- **Integrated-PDF leakage sweep:** zero matches for raw source IDs, repo paths, filenames,
  review-process phrases, or stale draft/scaffold language, on both the development build's and
  RC1's own independently-extracted text.
- **`git diff --check`:** clean.
- **Full suite:** 482 tests, exactly the three known pre-existing Workbook 04 baseline failures
  (`test_index_subtitle_says_release_candidate_5`,
  `test_each_two_line_chapter_heading_renders_completely`,
  `test_chapter4_heading_renders_complete_title`), zero new failures. Run exactly once at this
  final validation stage.

## Full-document visual inspection

Performed twice: once against the development build, once independently against the actual
RC1 PDF (both at 170 dpi, full page images, not a contact-sheet-only pass). Pages actually
opened and checked:

- **Title page and table of contents** (both builds, page 1-2/1-3): title, subtitle (confirmed
  "Complete Content Draft — Chapters 1-6" in the dev build and "Complete Content Draft (Release
  Candidate 1)" in RC1), and the full 66-page TOC listing, including every chapter's subsections,
  all six Answer Key entries, and the Bibliography entry — all present, correctly numbered,
  matching the rendered page numbers exactly.
- **Every chapter-opening page** (pages 3, 9, 16, 23, 33, 45): each chapter's own title, italic
  subtitle, "Learning objectives," "Why this matters," and "Mental model or analogy" sections
  render cleanly with no clipping, no mid-word hyphenation, no truncated headings, and no
  duplicated chapter numbers.
- **Four figures spanning early/mid/late chapters** (Figure 1 p.4, Figure 4 p.24, Figure 6 p.34,
  Figure 8 p.47): all render at full resolution with no clipping, overlap, or broken glyphs; all
  captions remain attached to and consistent with their figures; Chapter 5's Figure 6 confirms
  the previously-fixed narrow-bar "exposed" label and "partial step-time estimate" wording both
  survived integration/renumbering intact.
- **A dense table** (Chapter 6's Table 1, verified during that chapter's own prior standalone
  review and re-confirmed unaffected by integration via the chapter-opening/body spot checks
  above).
- **Chapter-to-chapter and chapter-to-Answer-Key transitions**: Chapter 6 end -> Answer Key
  (page 56-57), Answer Key Chapter 1 -> Chapter 2 (page 57), Answer Key Chapter 6 -> Bibliography
  (page 64-65) — all flow without orphan fragments, forced blank pages, or split question/answer
  blocks.
- **Bibliography** (pages 65-66, both builds): single integrated list of 12 entries (not six
  separate per-chapter lists), correctly renumbered relative to each chapter's own standalone
  review (e.g. the Llama 3 report moved from a standalone [4] to integrated [12]), split cleanly
  between whole entries across its two pages, nothing truncated.
- **Final pages** (page 66, both builds): bibliography entries 10-12 complete, no trailing
  orphan content, ordinary end-of-document blank space below the last entry (expected, not a
  defect).
- **Headers/footers/page numbers**: sequential 1-66 throughout, no resets, no duplicates,
  confirmed via the page-image filenames matching their own rendered footer numbers at every
  spot-checked page.

No clipping, overlap, broken glyphs, mid-word title hyphenation, truncated headings, orphan
headings/fragments, unintended blank pages, stale page images, or captions separated from their
figures were found in either pass.

## Findings fixed in this RC (carried from the prior RC's report)

None carried forward — this is RC1, there is no prior RC report.

Two things were fixed during this RC's own build (not carried from elsewhere):

1. `workbooks/05-llm-training/index.qmd`'s subtitle and front-matter comment still said "Partial
   Content Draft" and described the workbook as not release-ready, left over from Chapter 6's own
   drafting stage. Updated in two steps: first to "Complete Content Draft — Chapters 1-6" for the
   development build, then to "Complete Content Draft (Release Candidate 1)" for this RC,
   matching Workbook 04's own established subtitle convention.
2. `config/chapter-status-registry.yaml` and `workbooks/05-llm-training/chapter-contracts/
   ch06.yaml` recorded Chapter 6 as `drafted_pending_human_review` with a stale `commit_sha`
   pointing at its original drafting commit rather than its later correction-pass commit. Updated
   both to `accepted_frozen` with the correct, current `commit_sha`, matching exactly how
   Chapter 5's own contract already recorded its acceptance. A small number of this project's own
   `tests/test_chapter_factory_workflow.py` assertions that had hardcoded Chapter 6's prior
   "pending" status (now stale by construction, since that status legitimately changed) were
   updated to match; this surfaced and fixed one additional, unrelated test fragility (a
   `visual_regression.py` test that assumed no dev-only hash manifest yet existed for Chapter 5,
   broken by that chapter's own earlier, legitimate `--override-frozen` exercise during this same
   RC's pre-integration audit) by making the test compare before/after state instead of assuming
   a fixed starting state.

## Findings deferred to a later RC

- Chapters 1 and 2 still lack the `{#sec-chN-check}`-specific cross-reference anchor on their
  "Check your understanding" headings (their Answer Key intros resolve to the bare chapter-level
  section number instead of the specific subsection). Documented, pre-existing, not introduced
  by integration — deferred rather than reopened without a demonstrated integration defect, per
  this task's own scope.
- Several Chapters 1-4 figures still lack a dedicated semantic invariant test beyond the generic
  bounds/well-formed-XML check (`tests/test_figures.py`). Documented, pre-existing, not
  introduced by integration — deferred for the same reason.
- The three known, pre-existing Workbook 04 baseline test failures remain unfixed, per this
  task's explicit instruction not to modify Workbook 04 in this task. A follow-up
  recommendation to repair or formally retire these three tests before any further workbook's
  RC1 (already recorded in `docs/chapter-factory-operator-guide.md`'s "Known limitations"
  section) still stands.

## Disposition

`needs independent review` — all gates this task required are passing and RC1 has been produced
exactly as specified, but per this task's own explicit instructions, Workbook 05 has not been
marked publication-ready, no canonical final PDF exists, and this RC is handed off for
independent review before any further step (RC2, publication freeze, or the TSFM addendum) is
considered. If accepted after that independent review, this RC1 build becomes frozen and
any further fix becomes RC2's own commit, not an edit to this one.
