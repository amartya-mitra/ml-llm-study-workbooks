# Release Candidate Report — Workbook 04, Complete Content Draft (RC3)

Date: 2026-09-25
Status: **Complete content draft — release candidate 3.** A small
acceptance-fix pass over RC2's four remaining findings. This is a
release candidate, not the final edition.

PDF: `outputs/04-modern-llm-architecture-workbook-rc3.pdf`
Prior artifacts (preserved, not overwritten): `outputs/04-modern-llm-architecture-workbook-rc1.pdf`, `outputs/04-modern-llm-architecture-workbook-rc2.pdf`
Build script: `scripts/build_release_candidate_v3.py`

**Source commit this build was rendered from:** `2ab64806c1c60b13c06812cc3341e58e6d07a9e2`
(this build was rendered with additional, not-yet-committed changes on
top of that commit -- the commit this report accompanies supersedes it).
This exact commit information is deliberately recorded only here, not
in the learner-facing PDF -- see Section 4 below.

## 1. What this pass covered

RC2 completed a whole-book editorial and visual-production pass but
left four acceptance findings open. This session fixed exactly those
four, and nothing else:

1. Chapter 1 shared page 7 with the final notation table (Table 3) --
   every other chapter starts on its own fresh page.
2. Every chapter heading rendered as "N Chapter N: Title" -- a
   duplicated leading number, since Typst's auto-numbering already
   prepends "N" and the heading text itself also said "Chapter N:".
3. The notation reference's Table 2 defined `KV_bytes`, a symbol no
   equation or prose anywhere in Chapters 1-8 actually uses; the real
   symbols the equations use ($M_{KV}$ in Chapter 3's cache equation,
   $M_{\text{MLA}}$ in Chapter 4's Equation 15) were undocumented.
4. The Build and Version Note contained repository-internal strings
   (`src-19..src-49`, `sources/registry.yaml`,
   `includes/draft-scope-note.qmd`) that have no place in a
   learner-facing rendered book.

## 2. Statistics

| Metric | RC2 | RC3 |
|---|---|---|
| Total PDF pages | 69 | **69** (unchanged) |
| Total word count (`pdftotext \| wc -w`) | 33,881 | **33,739** |
| Distinct tables (`{#tbl-...}`) | 19 | 19 (unchanged; Table 2 grew from 8 to 10 rows) |
| Tests passing | 255 | **272** (17 new RC3 regression tests) |

RC3 was pre-approved to grow to 70 pages if needed (an added page break
plus 2 net new notation rows could plausibly cost a page). It did not:
shortening every chapter title by removing the redundant "Chapter N: "
prefix freed enough space to absorb both additions, so the page count
stayed at 69 -- not the result of any font, figure, or margin shrink
(see `page-budget.yaml`'s `release_candidate_v3.page_count_change_note`).

## 3. Fix 1 — Chapter 1's page break

Added an explicit `#pagebreak()` between the notation-summary include
and Chapter 1's include in `index.qmd`, matching the pattern already
used between every other pair of chapters. Verified: Table 3 now ends
alone on page 7; Chapter 1 begins fresh on page 8. Regression test:
`tests/test_release_candidate_rc3.py::TestChapter1FreshPageBreak`
(source-level check that the pagebreak directive exists between the
two specific includes, plus a rendered-PDF check that Chapter 1's
heading page differs from, and comes strictly after, Table 3's page).

## 4. Fix 2 — Chapter title numbering

Removed the literal "Chapter N: " prefix from all 8 chapter headings'
source text (e.g. `## Chapter 1: Transformer Refresher {#sec-ch1}` ->
`## Transformer Refresher {#sec-ch1}`). Typst's `number-sections: true`
auto-numbering still prepends the leading numeral, so the rendered
title is now exactly **"N Title"** (e.g. "1 Transformer Refresher", "4
Reducing Attention Cost: Windows, Sparsity, and Latent KV
Representations", "8 Emerging Directions and Architecture Synthesis:
Looped Depth, Design Tradeoffs, and How to Read What Comes Next") --
one leading number, never two. Subsection numbering (1.1, 4.9, 8.12,
...) is untouched, since only the top-level chapter heading's text
changed.

A side effect: Chapter 4's title, now shorter without the "Chapter 4:
" prefix, no longer needs the manual `#linebreak()` RC2 added to dodge
a "La-tent" hyphenation break -- it now wraps naturally at
"Rep-/resentations", a normal syllable hyphenation. The manual
linebreak span was removed.

Regression tests: `tests/test_release_candidate_rc2.py`'s
`test_each_chapter_heading_matches_its_file_number` (updated to assert
the prefix is gone) and `test_chapter_headings_numbered_1_through_8`
(unchanged, now passing against RC3's actual clean numbering);
`tests/test_release_candidate_rc3.py::TestNoDuplicatedChapterTitleNumbering`
(new: checks source headings, rendered body text, and the TOC against
the exact banned regex `^\s*[1-8]\s+Chapter\s+[1-8]`).

## 5. Fix 3 — Notation reference correction

Audited every displayed equation (`{#eq-...}`) in Chapters 1-8 against
the three notation tables. Findings:

- `KV_bytes` was defined but never referenced by any equation or prose
  anywhere in the book -- dead notation. Removed.
- `$M_{KV}$` (Chapter 3's KV-cache-size equation) and
  `$M_{\text{MLA}}$` (Chapter 4's Equation 15, MLA's cache-size
  equation) are the symbols actually used, and were previously absent
  from the reference entirely. Added both, with meanings pointing back
  to their defining chapter's equation rather than re-deriving the
  formula in the table (consistent with the table's existing brevity).
- `$W$` (sliding-window width) is used in a displayed equation
  (Chapter 4's receptive-field equation) and referenced repeatedly
  outside that equation's own paragraph -- in the worked example, two
  check-your-understanding questions, the chapter recap, and the
  interview lens. This is exactly the kind of chapter-spanning symbol
  the reference exists to cover, and was missing. Added.
- No other displayed-equation symbol was found missing from the
  reference. Equation-local algebra ($Q$, $K$, $V$, $W_Q$, $r$, $p$,
  $\theta_j$, $\epsilon$, etc.) remains intentionally excluded, per the
  table's existing, already-established scope (these are redefined at
  each point of use, not flip-back-here symbols).

Table 2 grew from 8 to 10 rows (net: -1 `KV_bytes`, +3 `M_KV`,
`M_MLA`, `W`). Rendered cleanly with substantial unused whitespace
remaining below the table (page 6) -- no overlap or clipping, well
within the existing `MAX_SAFE_ROWS_PER_TABLE = 10` regression-tested
ceiling.

Regression tests: `tests/test_release_candidate_rc2.py`'s notation
tests (updated: `test_all_notation_symbols_still_present` now expects
$M_{KV}$/$M_{\text{MLA}}$/$W$ instead of `KV_bytes`; new
`test_kv_bytes_symbol_fully_retired`); `tests/test_release_candidate_rc3.py::TestNotationReferenceMKvMMla`
(new: confirms $M_{KV}$/$M_{\text{MLA}}$/$W$ present, `KV_bytes` absent
from the notation reference AND absent from every chapter file --
i.e., confirms it really was dead notation before celebrating its
removal -- plus a row-count safety check and a rendered-PDF check).

## 6. Fix 4 — Build and Version Note sanitization

`scripts/generate_build_note.py`'s learner-facing template
(`content = f"""..."""`) no longer contains: a raw commit SHA (the
"Source commit used to render this PDF" line was removed entirely --
see the note at the top of this report on why that value belongs only
here, not in the PDF), the source-registry path or ID range
(`sources/registry.yaml`, `src-19..src-49` -- replaced by a plain
learner-facing sentence: "Primary and roadmap sources for Chapters 1-8
and the series-wide topic roadmap were last verified between
2026-09-22 and 2026-09-25"), and the `includes/draft-scope-note.qmd`
path (replaced by "see the release-candidate note earlier in this
book").

The script's `--registry-note` flag is kept as a backward-compatible
alias for the new `--source-verification-note`, specifically so
`scripts/build_release_candidate_v1.py` and
`scripts/build_release_candidate_v2.py` -- RC1's and RC2's frozen build
scripts -- continue to run unmodified if anyone re-runs them; only the
label in the generated template's output changed for those, which
does not affect either PDF already sitting in `outputs/`, both left
untouched. `git_commit_or_precommit()` is still computed every build
and printed to stdout for whoever is running the build to copy into a
maintainer report like this one -- it is never interpolated into the
learner-facing `content` string.

Detailed provenance that used to live in the build note (source
verification specifics, the numbering-scheme rationale, this session's
own fix list) is preserved in this report and in the build note's own
still-present, still-learner-appropriate Provenance bullets, which
were rewritten to stay useful without naming any file.

Regression tests: `tests/test_release_candidate_rc2.py`'s
`test_build_note_generator_does_not_overclaim_clean_state` (updated:
no longer requires the commit-SHA line; now requires the template
contain no "commit" text at all, while the honest dirty-tree wording
must still exist in the generator's *source*, just not embedded in the
template); `tests/test_release_candidate_rc3.py::TestBuildNoteSanitization`
(new: checks the generated `.qmd` fragment and the full rendered PDF
text against all seven banned patterns -- `.yaml`, `.qmd`, `src-\d`,
`scripts/`, `includes/`, `figures/source`, `data/worked-examples` --
confirms zero occurrences in both; confirms the note still states
generation date, source-verification range, release status, and a
Provenance section).

## 7. Visual QA

RC3 was rendered fresh and all 69 pages re-rendered to PNG at 170 DPI.
Manually inspected in full: the title page and TOC (pages 1-3, confirm
clean "N Title" numbering throughout and no duplicated-number pattern),
all three notation-table pages (5-7, confirming the 10-row Table 2
renders without overlap and Table 3 now ends alone on page 7), Chapter
1's fresh opening (page 8), Chapter 4's title wrapping (page 33, "Rep-
/resentations" hyphenation, no "La-tent" defect), and the answer-key
tail / Build and Version Note / Bibliography (pages 66-67, confirming
full sanitization). The remaining pages were swept by an independent
visual-inspection pass reading every one of the 69 page images for
overlap, clipping, orphan pages, awkward heading breaks, broken
cross-references, and internal-path leakage; see this report's
companion inspection notes for that pass's findings, folded into
Section 9 below.

## 8. Validation summary

- `python -m pytest tests/ -q`: **272 passed** (65 subtests), including
  17 new RC3 regression tests across two files
  (`test_release_candidate_rc2.py`'s updates,
  `test_release_candidate_rc3.py`'s new classes).
- `make validate` (`validate_registry.py` + `validate_questions.py`):
  both **OK**.
- `git diff --check`: no whitespace/conflict-marker errors.
- All ten worked-example scripts in
  `workbooks/04-llm-architecture/data/worked-examples/` were re-run and
  reproduce their committed JSON byte-for-byte -- no numeric drift from
  this session's edits (which touched only headings and the notation
  reference's prose, not any worked-example script).
- Rendered-PDF text extraction confirms: zero occurrences of the
  duplicated chapter-numbering pattern; zero occurrences of any of the
  seven banned internal-path patterns; zero `??` placeholder
  occurrences; zero stale "Section 11"-"Section 18" references; page
  count 69, within the 72-page hard ceiling.

## 9. Remaining limitations

- No independent human copy-edit/proofread pass has been performed --
  unchanged from RC2's own disclosed limitation.
- The three previously-flagged unverified named sources ("Beyond
  Parameters...", "SMELT...", "Full-bandwidth transformer," `src-47`)
  remain unverified candidates -- not touched this session.
- This was a narrowly-scoped acceptance-fix pass by design; no chapter
  content, question, or citation changed.

## 10. Commit

See the commit this report accompanies for the final SHA. Nothing was
pushed to any remote.
