# RC report — Workbook 05, RC1

- **Commit SHA:** this report is committed in the same commit it describes, so it cannot name its
  own commit SHA from inside itself — run `git log -1 --format=%H -- reports/
  05_release_candidate_1_report.md` after this correction's commit, or see that commit's own
  message/the task's final report to the user for the exact SHA.
- **Branch:** `main`
- **Revision note (narrow pagination/metadata correction, same RC1):** after RC1 was first
  produced (commit `8eba94d55ef19ca6bc468d22146739c7a815940e`), independent human inspection of
  the actual rendered PDF found two orphan-fragment pages (former pages 15 and 44) and one
  metadata error (the subtitle still read "Complete Content Draft (Release Candidate 1)" instead
  of exactly "Release Candidate 1"). This section and "Findings fixed in this RC" below record
  that narrow correction; everything else in this report describing RC1's original production is
  left as originally written, since it is still accurate. This remains RC1 — the fix was applied
  as a correction to the same, not-yet-accepted candidate, not as a new RC2.
- **Fixed QA command — deliberate deviation, documented:** the template above names
  `python3 scripts/workbook_qa.py --workbook 05-llm-training` (no `--chapter`) as the fixed QA
  command. That full-book mode's own `build_pdf()` step writes the canonical PDF at
  `outputs/05-llm-training-workbook.pdf` as an unconditional side effect of running it — and this
  RC1 task explicitly requires that no canonical Workbook 05 PDF be created. Running the
  template's literal command would violate that constraint, so it was not run in this form for
  this RC. The equivalent QA evidence was instead gathered via registry/question/contract
  validators, the Workbook 05 scoped + chapter-factory test suites, a PDF leakage sweep, and one
  full, direct `python3 -m unittest discover -s tests` run, plus a from-scratch `quarto render` +
  independent page-by-page visual inspection of the actual RC1 PDF — see "QA findings" and
  "Full-document visual inspection" below for the complete, real results this produced.
- **QA result:** `pass` — the full test suite (482 tests) reported exactly the three known,
  pre-existing Workbook 04 baseline failures and nothing else; `git diff --check` was clean; the
  PDF leakage sweep on the rebuilt RC1's own extracted text found zero matches.
- **RC PDF path:** `outputs/_releases/05-llm-training/05-llm-training-workbook-rc1.pdf`
- **Page count:** `64` (was `66`; the two orphan-fragment pages were eliminated, not replaced by
  blank or forced-break pages — see "Findings fixed in this RC")
- **Word count:** `36598` (via `pdftotext | wc -w` on the actual, rebuilt RC1 PDF; was `36639` —
  the small decrease is the narrow prose compression described below, not a content removal)
- **File size:** `1152876 bytes` (≈1.10 MiB; was `1154101 bytes`)
- **SHA-256:** `2e14d7156dfc87967d2a3214fa2dc349add2d4582d910f7894e08a7231b347bb` (was
  `688ae0ce65b6cc97a12716004b563abd7b51a4f6a0f5e678178632c8e26cf8d5` — the superseded RC1 build,
  preserved rather than deleted, at `outputs/_development/05-llm-training/
  superseded-rc1-pre-pagination-fix/05-llm-training-workbook-rc1-superseded.pdf`)
- **Rendered pages:** `outputs/_releases/05-llm-training/pages/` (64 PNGs, rendered directly from
  the actual, rebuilt RC1 PDF, not copied from the development build)
- **Contact sheet:** not generated for this RC (the chapter-scoped review packages each already
  have their own; a full-book contact sheet was judged unnecessary given the page-by-page visual
  inspection recorded below covered every category of page this task required)
- **Development build preserved at:**
  `outputs/_development/05-llm-training/integrated-dev-build/05-llm-training-workbook-dev.pdf`
  (SHA-256 `74cc70031acd9c1a8aaa7bf5e828d4fd3beab959f48ac9e1c3bf71e9c1e17dee`, 64 pages, subtitle
  "Complete Content Draft — Chapters 1-6") — RC1 was rendered independently from the same
  `index.qmd` after its subtitle was changed to exactly "Release Candidate 1"; the two PDFs'
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
- **Full suite (at original RC1 production):** 482 tests, exactly the three known pre-existing
  Workbook 04 baseline failures, zero new failures.

## Pagination and metadata correction (this revision, same RC1)

Independent human inspection of the originally-produced RC1 PDF found two integration-only
pagination defects and one metadata error, not present in any individual chapter's own prior
standalone review (each chapter's own review build paginates differently once concatenated
after five other chapters' content):

1. **Page 15 (orphan fragment).** Chapter 2's "2.12 Sources and further reading" section's
   closing sentences spilled onto their own page, leaving page 15 containing only a
   three/four-line continuation fragment before Chapter 3 began on page 16.
2. **Page 44 (orphan fragment).** Chapter 5's "5.12 Sources and further reading" section's
   closing sentences spilled onto their own page, leaving page 44 containing only a two-line
   continuation fragment before Chapter 6 began on page 45.
3. **Subtitle.** RC1's subtitle read "Complete Content Draft (Release Candidate 1)" — stale
   "Complete Content Draft" wording left over from the draft-stage convention, rather than the
   exact string "Release Candidate 1" this task requires for a release candidate.

**Correction applied, in the preferred order given for this task:**

- **Prose compression (tried first, for both pages):** in
  `workbooks/05-llm-training/chapters/02-multi-token-prediction.qmd` and `.../
  05-training-memory-and-communication.qmd`, each chapter's own "Sources and further reading"
  paragraph was narrowed by removing only the cross-workbook provenance aside ("already
  registered for workbook 04 chapter 6, this time read for its MTP section specifically rather
  than its architecture case-study content" in Chapter 2; "own"/"narrowly"/the `$k\Psi$` notation
  aside in Chapter 5) and other single-word filler. Every citation (`[@src-43]`, `[@src-33]` in
  Chapter 2; `[@src-17]`, `[@src-54]`, `[@src-52]`, `[@src-53]`, `[@src-10]`, `[@src-55]` in
  Chapter 5), every technical claim about what each source verifies, every "verified via
  full-text extraction of ..." qualifier, and both chapters' full chapter-boundary statements
  (Chapter 2's speculative-decoding/workbook-06 boundary; Chapter 5's Chapter-4/Chapter-6
  boundaries) were preserved word-for-word. This compression alone was insufficient to close
  either page's overflow (confirmed by rendering and re-measuring before adding any spacing
  change).
- **Chapter-local spacing adjustment (used as the stated fallback, since compression alone did
  not close either gap):** a scoped `#set block(spacing: 0.9em)` (both chapters) and, for Chapter
  5 only, an additional `#set par(leading: 0.55em)`, inserted immediately after each chapter's
  own heading and reset to Typst's own defaults (`1.2em` block spacing, `0.65em` leading)
  immediately before each chapter ends — confined entirely within that one chapter's own
  rendered span, never touching the project-wide Typst/Quarto typography, margins, font size, or
  base line spacing. Every other chapter's own pages were re-inspected after this change and
  render identically to before (confirmed via `pdftotext` character counts and direct page
  images — see Chapter 2 page 9/13 and Chapter 5 page 33/37/41 in the working record; no visible
  tightening, no overlapping lines). No forced page break, no filler text, and no citation
  removal or shrinking was used.
- **Subtitle:** `workbooks/05-llm-training/index.qmd`'s `subtitle` field changed to exactly
  `"Release Candidate 1"` for this RC1 render (and to `"Complete Content Draft — Chapters 1-6"`
  for the separate development-build render — the same toggle-before-each-render pattern used
  for RC1's original production).

**Result:** Chapter 2's complete "Sources and further reading" section (heading and full
paragraph) now ends on page 14; Chapter 3 begins cleanly on page 15. Chapter 5's complete
"Sources and further reading" section now ends on page 42; Chapter 6 begins cleanly on page 43.
The whole-book page count dropped from 66 to 64 (an expected, not required, consequence of
removing two near-empty fragment pages without inserting any replacement page). The bibliography
continuation (previously page 66, now page 64) still ends with three complete entries ([10],
[11], [12]) and was not touched — it remains the explicitly-acceptable pattern, not a defect.

**Files changed:** `workbooks/05-llm-training/chapters/02-multi-token-prediction.qmd`,
`workbooks/05-llm-training/chapters/05-training-memory-and-communication.qmd`,
`workbooks/05-llm-training/index.qmd` (subtitle only), plus two latent, pre-existing test
assertions updated to match a repo state change neither test had been updated for (see
"Findings fixed in this RC" below) — `tests/test_chapter_factory_workflow.py` and
`tests/test_workbook05_scaffold.py`.

**Validation for this correction specifically (run sequentially):** registry validation (`OK`),
question-bank validation (`OK: 74 question(s)`), chapter-contract validation (`OK: 2 chapter
contract(s)`), Workbook 05 scoped + chapter-factory workflow test modules (214 tests, 2 failures
— both diagnosed as pre-existing/latent, not new, and fixed; see below), a PDF-text leakage
sweep on the rebuilt RC1's own extracted text (zero matches for source IDs, repo paths,
filenames, review-process phrases, stale draft language, or "Complete Content Draft"), `git diff
--check` (clean), and one full `python3 -m unittest discover -s tests` run (482 tests, exactly
the three known Workbook 04 baseline failures, zero new failures) — run exactly once, after the
two latent test fixes below, as this task's single official full-suite run.
**Per-chapter `workbook_qa.py --chapter --review-pdf` re-runs were not repeated for Chapters 2
and 5** in this correction: that mode validates a chapter against its own standalone review PDF,
which this narrow, integration-only pagination fix did not rebuild (rebuilding it was out of this
task's explicit scope). The registry/question/contract validators, the scoped test modules above,
and the full suite together provide equivalent coverage for the actual changes made (prose
wording and Typst-only spacing, not structure, claims, or citations).
**`scripts/visual_regression.py` was not run against Chapters 2/5's standalone review PDFs**
for the same reason (it compares a chapter's own standalone review PDF against its own prior
hash manifest, which this task did not touch); the integration-level visual-regression check
this task actually needed — confirming only the two targeted transitions changed and every other
page renders identically — was performed directly via full before/after page image and
`pdftotext`-character-count comparison, recorded in "Full-document visual inspection" below.

**Two pre-existing, latent test failures found and fixed (not new, not caused by this
correction):** `test_no_canonical_pdf_or_release_dir_exists`
(`tests/test_chapter_factory_workflow.py`) and
`test_release_and_development_directories_not_prematurely_created`
(`tests/test_workbook05_scaffold.py`) both asserted that
`outputs/_releases/05-llm-training/` stays empty/nonexistent. Both assertions were written
during Workbook 05's scaffolding/drafting phase, before any RC existed, and never updated when
RC1 was legitimately produced in the immediately-prior integration task (commit `8eba94d`) —
`outputs/_releases/` is gitignored, so this is a filesystem-state assumption, not something
either test's own source-code history would flag. The failure is reproducible independent of any
edit this task made (RC1 already existed on disk before this task's first `git status` check).
Both were updated to match the now-permanent reality that RC1 exists: the chapter-factory test
now asserts before/after state around the specific calls it is actually testing (gate-report
building, visual-regression) rather than absolute non-existence — mirroring the sibling test
immediately above it in the same file, which already used that pattern; the scaffold test now
asserts the release directory contains only the recorded RC1 artifacts (the RC1 PDF and its
`pages/` directory), not that it is empty.

## Full-document visual inspection

Performed against both the rebuilt development build and the independently rebuilt RC1 PDF
(both at 170 dpi, full page images, not a contact-sheet-only pass; this supersedes the original
RC1 production's own pass, which inspected the now-superseded 66-page build). Pages actually
opened and checked:

- **Title page and table of contents** (both builds, pages 1-2): title, subtitle (confirmed
  "Complete Content Draft — Chapters 1-6" in the dev build and exactly "Release Candidate 1" in
  RC1 — not "Complete Content Draft" anywhere in RC1's own extracted text), and the full 64-page
  TOC listing, including every chapter's subsections, all six Answer Key entries, and the
  Bibliography entry — all present, correctly numbered, matching the rendered page numbers
  exactly (Chapter 3 at page 15, Chapter 6 at page 43, Bibliography at page 63, both confirmed
  against the TOC and the actual page content).
- **The two corrected transitions, independently re-opened in the rebuilt RC1 PDF itself** (not
  inferred from the development build): page 14 ends with Chapter 2's complete "Sources and
  further reading" paragraph and its full chapter-boundary sentence; page 15 opens cleanly with
  "3 Optimization and Scaling Laws." Page 42 ends with Chapter 5's complete "Sources and further
  reading" paragraph and its full chapter-boundary sentence; page 43 opens cleanly with "6
  Reading Real Pretraining Runs." Neither former fragment page exists in any form.
- **Every chapter-opening page** (pages 3, 9, 15, 22, 32, 43): each chapter's own title, italic
  subtitle, "Learning objectives," "Why this matters," and "Mental model or analogy" sections
  render cleanly with no clipping, no mid-word hyphenation, no truncated headings, and no
  duplicated chapter numbers.
- **Chapter 2 and Chapter 5's own earlier pages, re-checked for the chapter-local spacing
  change's side effects** (Chapter 2 pages 9 and 13; Chapter 5 pages 33, 37, and 41): all render
  with normal, consistent line and paragraph spacing — no visible tightening, no overlapping
  lines or glyphs, figures and captions unaffected.
- **Figures spanning early/mid/late chapters** (Figure 6, Chapter 5's critical-path timeline,
  page 33): renders at full resolution with no clipping, overlap, or broken glyphs; the caption
  remains attached and consistent; the previously-fixed "exposed" label and "partial step-time
  estimate" wording both survived this correction intact.
- **Bibliography** (pages 63-64): single integrated list of 12 entries, split cleanly between
  whole entries across its two pages (entries 1-9 on page 63, 10-12 on page 64), nothing
  truncated — explicitly confirmed as the acceptable pattern, not reopened or altered.
- **Answer Key transitions**: Chapter 1 -> Chapter 2 (both within page 55) flows without a split
  question/answer block; re-confirmed consistent with the TOC's own page numbers for every Answer
  Key chapter (55, 55, 56, 58, 59, 61) and the Bibliography (63).
- **Headers/footers/page numbers**: sequential 1-64 throughout, no resets, no duplicates,
  confirmed via the page-image filenames matching their own rendered footer numbers at every
  spot-checked page.
- **Leakage sweep on RC1's own extracted text**: zero matches for raw source IDs, repo paths,
  `.qmd` filenames, commit/registry/process-guard references, or stale draft-status wording
  (including "Complete Content Draft," confirming the subtitle correction left no residual trace
  elsewhere in the document).

No clipping, overlap, broken glyphs, mid-word title hyphenation, truncated headings, orphan
headings/fragments, unintended blank pages, stale page images, or captions separated from their
figures were found in this pass.

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

Three more things were fixed in this later, narrow correction to the same RC1 (see "Pagination
and metadata correction" above for full detail):

3. Two orphan-fragment pages (former pages 15 and 44) found by independent human inspection of
   the rendered PDF, eliminated via narrow prose compression plus a chapter-local Typst spacing
   adjustment confined to Chapters 2 and 5 respectively.
4. The subtitle's stale "Complete Content Draft" wording, changed to exactly "Release
   Candidate 1".
5. Two pre-existing, latent test assertions (in `tests/test_chapter_factory_workflow.py` and
   `tests/test_workbook05_scaffold.py`) that had never been updated for RC1's own existence,
   updated to match that now-permanent repo state (before/after comparison instead of absolute
   non-existence) — see "Pagination and metadata correction" above for why these are not new
   failures introduced by this correction.

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

`needs independent review` — all gates this task required are passing and RC1 (now corrected as
described above) has been produced exactly as specified, but per this task's own explicit
instructions, Workbook 05 has not been marked publication-ready, no canonical final PDF exists,
and this RC is handed off for independent review before any further step (RC2, publication
freeze, or the TSFM addendum) is considered. If accepted after that independent review, this RC1
build becomes frozen and any further fix becomes RC2's own commit, not an edit to this one.

The originally-produced RC1 build (SHA-256
`688ae0ce65b6cc97a12716004b563abd7b51a4f6a0f5e678178632c8e26cf8d5`, 66 pages) is preserved,
not deleted, at `outputs/_development/05-llm-training/superseded-rc1-pre-pagination-fix/
05-llm-training-workbook-rc1-superseded.pdf`, for reference should the independent reviewer want
to compare the two.
