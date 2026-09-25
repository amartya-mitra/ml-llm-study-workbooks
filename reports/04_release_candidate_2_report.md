# Release Candidate Report — Workbook 04, Complete Content Draft (RC2)

Date: 2026-09-25
Status: **Complete content draft — release candidate 2.** A whole-book
editorial, cross-reference, and visual-production pass across all
eight chapters has now been completed over RC1. This is a release
candidate, not the final edition — no substitute exists for an
independent human proofread pass beyond what this project's own
automated and visual checks can catch.

PDF: `outputs/04-modern-llm-architecture-workbook-rc2.pdf`
Prior artifact (preserved, not overwritten): `outputs/04-modern-llm-architecture-workbook-rc1.pdf`
Build script: `scripts/build_release_candidate_v2.py`

## 1. What this pass covered

RC1 (see `reports/04_release_candidate_report.md`) assembled all eight
chapters for the first time but had not yet had a whole-book editorial
or visual QA pass across the assembled document. This session
performed that pass: baseline re-render and inspection, three
release-blocking layout fixes, a document-hierarchy/numbering
refactor, a whole-book terminology/cross-reference/prose consistency
sweep, release-status/provenance updates, a technical spot-check audit,
and a full page-by-page visual re-inspection. No chapter content was
rewritten or expanded; this is a polishing and correction pass, not a
broad rewrite.

## 2. Complete-workbook statistics

| Metric | RC1 | RC2 |
|---|---|---|
| Total PDF pages | 68 | **69** (within the 72-page hard ceiling; within the 67-69 preferred range) |
| Total word count (rendered) | 33,415 | **33,881** |
| Chapters | 8 of 8 | 8 of 8 (unchanged) |
| Distinct figures (`{#fig-...}`) | 20 | 20 (unchanged) |
| Distinct tables (`{#tbl-...}`) | 16 | 19 (+3, from splitting one 18-row notation table into three 8-row tables) |
| Distinct sources cited in chapter text (`@src-N`) | — | 33 |
| Tests passing | 234 | **255** (21 new regression tests added this session) |

## 3. Release-blocking layout fixes (Stage 2)

1. **Notation table overlap (page 5, RC1).** The original single
   18-row table did not cleanly overflow to the next page — rows
   genuinely overlapped and clipped adjacent cells' text. Root cause
   was row count/wrap-complexity at that table size, not a simple
   page-fit problem. Fixed by splitting into three 8-row tables
   (`includes/notation-summary.qmd`, now rendering cleanly across pages
   5-7, each with substantial unused whitespace below — confirming the
   fix has margin to spare, not a fix at the edge of failing again).
2. **Chapter 4 orphan page (page 37, RC1).** The last two lines of
   Chapter 4's "Sources and further reading" were stranded alone on a
   page that was otherwise nearly empty, because the preceding page was
   100% full with zero slack. Fixed by trimming roughly one line's
   worth of prose from both the chapter-recap bullet list and the
   sources paragraph (`chapters/04-reducing-attention-cost.qmd`) — the
   full recap and sources section now fit together on page 38, and
   Chapter 5 starts fresh on page 39. No other chapter's whitespace was
   touched.
3. **Chapter 4 title line-break ("La-tent").** Fixed with a raw Typst
   `#linebreak()` forcing the break after "Sparsity," instead of
   letting Typst hyphenate "Latent" — the title now reads "Windows,
   Sparsity, / and Latent KV Representations."

## 4. Document hierarchy and numbering (Stage 3)

RC1's auto-numbering produced misleading results (e.g. "3 Chapter 1,"
"11 Answer Key: Chapter 1," 18 numbered top-level sections total).
Fixed by applying Pandoc's `.unnumbered` heading attribute to: the two
front-matter headings ("How to use this workbook," "Notation quick
reference"), all eight Answer Key headings, and the Build/Version Note
and its Provenance subsection. Instructional Chapters 1-8 are now the
*only* numbered top-level sections, and their subsection numbers (e.g.
"4.9 Applied exercise") match the logical chapter number exactly —
verified by full TOC inspection (see rendered pages 1-3).

This broke every cross-reference that had pointed at a now-unnumbered
heading (they had rendered as "Section 11" etc.). Fixed by switching
those specific references from Pandoc's auto-numbered `@sec-xxx` syntax
to literal markdown anchor links (e.g. `[Answer Key: Chapter 4](#sec-solutions-ch4)`),
which render as clickable text regardless of numbering. All other
`@sec-/@fig-/@tbl-` references (chapter-to-chapter, figure, table)
were left as auto-numbered crossrefs, since those targets remained
numbered headings.

Four new regression tests (`tests/test_release_candidate_rc2.py`)
check for recurrence of the "3 Chapter 1" / "10 Chapter 8" / "Section
11"–"Section 18" patterns against the rendered PDF text.

## 5. Whole-book editorial consistency pass (Stage 4)

- **Terminology**: KV-cache hyphenation, K/V vs. key/value, query vs.
  KV heads, residual-stream-vs-cache non-conflation, and the
  chunked-prefill qualification were all checked across the assembled
  document — no inconsistencies found beyond the two factual bugs
  below.
- **Structural promise**: `index.qmd`'s "How to use this workbook"
  claimed every chapter follows an identical structure, which was not
  true for Chapters 6-8 (case studies, systems synthesis, emerging
  directions). Rewritten to describe Chapters 1-5's common pattern and
  state that Chapters 6-8 adapt it deliberately rather than repeating
  it verbatim.
- **Two real factual bugs found and fixed** (not pre-planned; found by
  systematic cross-reference auditing):
  1. `chapters/03-attention-head-structure.qmd` claimed MLA was
     deferred to "a later chapter's case studies" — MLA actually
     landed in Chapter 4. Fixed to "the next chapter."
  2. `chapters/07-architecture-to-systems-behavior.qmd` claimed both
     multi-token prediction's training treatment *and*
     speculative decoding belonged to "a future inference workbook."
     Per `config/series-topic-roadmap.yaml`, MTP's primary home is the
     future **pretraining** workbook, not the inference one — Chapter
     8's own bridge language already had this right and was used as
     the reference to fix Chapter 7's.
- **Cross-reference integrity**: a custom anchor/reference parser
  confirmed 0 orphaned references across 78 defined anchors and 44
  crossref-style references.
- **Questions/solutions correspondence**: verified one-to-one across
  all eight chapters; apparent count differences were all confirmed as
  the expected extra applied-exercise/interview-lens answer items, not
  mismatches.
- No exact-duplicate sentences were found within any chapter (recap vs.
  misconception vs. answer-explanation text).

## 6. Release-status and provenance updates (Stage 5)

- Title/subtitle: "Release Candidate 1" → "Release Candidate 2".
- `includes/draft-scope-note.qmd`: rewritten to state the editorial
  pass has been completed (naming the four specific fixes), while
  still honestly disclosing that no independent human proofread has
  occurred.
- `scripts/generate_build_note.py`: dirty-tree wording changed from
  "pre-commit -- working tree had uncommitted changes at build time"
  to "this build was rendered with additional, not-yet-committed
  changes on top of this commit" (less easily misread as an error
  state); the "do not hand-edit" maintainer instruction was removed
  from the learner-facing generated template (kept only in the
  generator script's own docstring); build-note headings marked
  `.unnumbered`.
- The RC2 PDF's own Build and Version Note records **source commit
  `7b46a58`** (the commit at the start of this session) plus the
  explicit, honest disclosure that this build was rendered with
  additional uncommitted changes on top of it — since the PDF cannot
  self-reference the commit that includes its own build, per this
  project's established convention for that unavoidable
  chicken-and-egg case.

## 7. Technical audit (Stage 6)

This pass was primarily editorial. Spot-checks performed this session:
RMSNorm epsilon consistency (1e-5 in both chapter and solutions
text, confirmed). The chapter-by-chapter mechanism claims (causal
masking, RoPE, MHA/MQA/GQA cache formulas, MLA cache accounting,
MoE total-vs-active arithmetic, the three case-study model ledgers,
looped-depth ratios, MTP-vs-speculative-decoding) were verified against
primary sources in the individual drafting sessions that produced each
chapter (see `reports/04_ch0N_draft_report.md`); this session did not
re-derive them from scratch, since the audit surfaced no unsupported or
contradictory claim requiring a new source. All ten worked-example
scripts in `workbooks/04-llm-architecture/data/worked-examples/` were
re-run this session and reproduce byte-identical output against their
committed JSON — no numeric drift.

## 8. Visual QA (Stage 7)

All pages were re-rendered to PNG at 170 DPI from the final RC2 PDF and
inspected. Categories explicitly re-inspected at full size: the
notation table (pages 5-7), every one of the eight chapter-opening
pages, all comparison/ledger tables (Tables 9-12, 15, 17, 19), every
page containing more than one figure or table, the Chapter 4 ending
(page 38), a representative sample of the answer key (Chapters 1, 5,
6, 7, 8), the Build and Version Note, and the bibliography (pages
67-69). No overlapping rows, clipped text, orphan pages, or internal
path/placeholder leakage were found in this final inspection pass.

## 9. Validation summary

- `python -m pytest tests/ -q`: **255 passed** (65 subtests), including
  21 new RC2-specific regression tests.
- `make validate` (`validate_registry.py` + `validate_questions.py`):
  both **OK**.
- `git diff --check`: no whitespace/conflict-marker errors.
- All ten worked-example scripts reproduce their committed JSON
  byte-for-byte.
- Rendered-PDF text extraction confirms zero occurrences of "3 Chapter
  1," "10 Chapter 8," or "Section 11" through "Section 18" patterns.

## 10. Remaining limitations

- No independent human copy-edit/proofread pass has been performed —
  automated and visual checks catch structural and factual-consistency
  issues, not every stylistic rough edge.
- The three previously-flagged unverified named sources ("Beyond
  Parameters...", "SMELT...", "Full-bandwidth transformer," `src-47`)
  remain unverified candidates, not cited for any specific claim — not
  newly introduced or resolved this session.
- RC2 is 69 pages, at the top edge of (not below) the 67-69 preferred
  range; a further page reduction (e.g. merging the two smaller
  notation tables into one 16-row table) was deliberately not
  attempted, since it risks reproducing the exact row-overlap defect
  this session fixed, for a benefit (1 page) the task's own priority
  ordering ranks below correctness and legibility.

## 11. Commit

See the commit this report accompanies for the final SHA. Nothing was
pushed to any remote.
