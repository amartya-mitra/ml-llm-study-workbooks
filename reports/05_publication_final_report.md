# Workbook 05 Final Publication Report
## LLM Pretraining and Distributed Training

**Publication Date:** 2026-10-05
**Status:** PUBLICATION-FROZEN (pending push; see Phase 8 in the task this report accompanies)

---

## Repository State at Finalization

**Starting HEAD:** `de11a1161850458f323b87ec297c8bf463d6ba57`
**Branch:** `main`
**Remote:** `github.com:amartya-mitra/ml-llm-study-workbooks.git`
**Divergence before this task:** 24 ahead / 0 behind `origin/main`; `git fetch` confirmed no new
remote commits before proceeding.

---

## Accepted Release Candidate

| Property | Value |
|---|---|
| **Path** | `outputs/_releases/05-llm-training/05-llm-training-workbook-rc1.pdf` |
| **Page count** | 64 |
| **SHA-256** | `2e14d7156dfc87967d2a3214fa2dc349add2d4582d910f7894e08a7231b347bb` |
| **Acceptance result** | PASS (independent human review) |
| **RC2** | Not required |

Accepted intentional layouts (not reopened in this task):
- Chapter 6's complete analogy callout on page 44 is intentionally sparse.
- The final bibliography continuation (page 64) contains three complete entries ([10], [11],
  [12]) and is acceptable.
- The known Chapter 1-2 answer-key anchor warnings are non-blocking.
- The chapter-local pagination adjustments in Chapters 2 and 5 (narrow prose compression plus a
  scoped Typst `block(spacing:...)`/`par(leading:...)` adjustment, reset at each chapter's own
  end) are accepted.

---

## Canonical Final Artifact

**Filename:** `outputs/05-llm-training-workbook.pdf`
**Path status:** build product, ignored by `.gitignore` (`outputs/*.pdf`); not a tracked file
**Reproducible via:** `python3 scripts/build_wb05_final.py` (requires the `ml-workbooks` conda
env active: `source /opt/conda/etc/profile.d/conda.sh && conda activate ml-workbooks`)

| Metric | Value |
|---|---|
| **Pages** | 64 |
| **File size** | 1,152,681 bytes |
| **Word count** | 36,597 words (`pdftotext \| wc -w`) |
| **SHA-256** | `25a393bb6b1bb1c42c836f08b4375e9e1a451792f4397665f63b69e1c1072a0c` |
| **PDF version** | 1.7 |
| **Creator** | Typst 0.14.2 |
| **Creation time** | 2026-10-05 22:45:20 UTC |
| **Subtitle** | Final Edition |

### Exact build command

```bash
cd /mnt/home/amitra/ml-llm-study-workbooks
source /opt/conda/etc/profile.d/conda.sh
conda activate ml-workbooks
python3 scripts/build_wb05_final.py
```

Internally: temporarily changes `workbooks/05-llm-training/index.qmd`'s subtitle from "Release
Candidate 1" to "Final Edition", renders via `quarto render ... --to typst`, copies the rendered
PDF to `outputs/05-llm-training-workbook.pdf` (preserving any pre-existing file at that path
under `outputs/_development/05-llm-training/canonical-pages/` first, per `AGENTS.md`), restores
the subtitle to "Release Candidate 1", then runs `pdfinfo`/`pdffonts`/`pdftotext`/`pdftoppm`
and prints the results. The subtitle swap is the same toggle-before-each-render pattern already
used to produce the development build and RC1.

---

## RC1-versus-Final Content Comparison

A direct `diff` between `pdftotext` extractions of RC1 and the canonical final PDF shows exactly
one differing line — the subtitle:

```
2c2
< Release Candidate 1
---
> Final Edition
```

Everything else (title, table of contents, all six chapters, all worked examples, all figures,
all questions, all six Answer Keys, the Bibliography) is byte-for-byte identical text. Page count
matches exactly (64 = 64). The low-content-page scan (per-page `pdftotext` character count)
produces the same set of flagged pages in both builds (64, 44, 39, 10, 28, 51, 13, 40, 23, 29,
22, 16, 31, 8, 7, ...), confirming pagination is unchanged. The checksums differ
(`2e14d7...` vs `25a393...`) because the canonical PDF is an independent Quarto/Typst render,
not a copy or a renamed file — exactly as expected for two separate builds from the same source
state.

No chapter content, prose, solutions, questions, figures, worked examples, source claims, or
accepted pagination changed during finalization. The only source change required was the
subtitle field in `workbooks/05-llm-training/index.qmd`, and even that is restored to "Release
Candidate 1" after each build (the "Final Edition" string exists only transiently during
rendering and permanently in the output PDF's own text, never as the file's committed state).

---

## Status-Registry Update

`config/chapter-status-registry.yaml`'s `workbooks.05-llm-training` entry gained four new
top-level fields (alongside its existing, unmodified `chapters:` block, which still records all
six chapters as `accepted_frozen` with their own unchanged commit SHAs):

```yaml
05-llm-training:
  status: "accepted_frozen"
  note: "Whole workbook accepted for canonical publication. RC1 ... passed independent
         human acceptance review; RC2 was not required. Ready for canonical publication
         build (outputs/05-llm-training-workbook.pdf)."
  rc1_accepted: true
  rc1_sha256: "2e14d7156dfc87967d2a3214fa2dc349add2d4582d910f7894e08a7231b347bb"
  rc1_page_count: 64
  acceptance_date: "2026-10-05"
```

This mirrors Workbook 04's own existing whole-workbook entry shape
(`status: "frozen"` + `note` + `last_touched_commit_sha`) exactly — no new, parallel status
mechanism was invented. No chapter-level entry, no chapter contract, and no chapter source file
was touched by this update.

---

## Validation Results (Phase 5, run sequentially)

| # | Check | Result |
|---|---|---|
| 1 | Registry validation | `OK: registry and coverage matrix are valid` |
| 2 | Question validation | `OK: 74 question(s) validated against shared/question-schema.yaml` |
| 3 | Chapter-contract validation (Ch. 1-6) | `OK: 2 chapter contract(s) validated` (only Ch. 5 and Ch. 6 have contract files; both agree with the registry) |
| 4 | Source and claim-ledger audit | `crc.check_claim_ledger_coverage` run directly for all six chapters: `ok: True`, zero unknown source IDs, for every chapter (8, 8, 11, 16, 18, and 6 claim entries respectively) |
| 5 | Worked-example tests | 79 tests, all passing |
| 6 | Figure semantic tests | 37 tests, all passing |
| 7 | Workbook 05 scoped tests | 48 tests, all passing |
| 8 | Chapter-factory workflow tests | 53 tests, all passing |
| 9 | Canonical-PDF text extraction and leakage check | zero matches for source IDs, repo paths, `.qmd` filenames, commit SHAs, build-script names, "Complete Content Draft", "Review Draft", or "Release Candidate" anywhere in the canonical PDF's extracted text |
| 10 | `git diff --check` | clean |
| 11 | Full repository test suite (run exactly once) | 482 tests: exactly the three known, pre-existing Workbook 04 baseline failures, zero new Workbook 05 failures |

**The three known Workbook 04 baseline failures** (not fixed in this task, per its own explicit
instruction):
- `test_index_subtitle_says_release_candidate_5`
- `test_each_two_line_chapter_heading_renders_completely`
- `test_chapter4_heading_renders_complete_title`

**Known non-blocking warnings** (unchanged from RC1, not reopened):
- Chapters 1-2 lack the `{#sec-chN-check}`-specific cross-reference anchor on their "Check your
  understanding" headings.
- Several Chapters 1-4 figures lack a dedicated semantic invariant test beyond the generic
  bounds/well-formed-XML check.

---

## Complete Visual Review (Phase 6)

All 64 canonical pages rendered fresh (stale renders cleared first) to
`outputs/_development/05-llm-training/canonical-pages/05-llm-training-workbook-pages/` and
inspected page-by-page (not contact-sheet-only). Confirmed:

- Title page reads "Final Edition" (not "Release Candidate 1", "Complete Content Draft", or
  "Review Draft").
- Table of contents page numbers match actual rendered pages exactly (spot-checked against
  Chapter 3 at page 15, Chapter 6 at page 43, Bibliography at page 63).
- All six chapter titles render completely and correctly: "Pretraining Objectives and Data"
  (p.3), "Multi-token Prediction as a Training Objective" (p.9), "Optimization and Scaling Laws"
  (p.15), "Parallelism Strategies for Distributed Training" (p.22), "Memory and Communication at
  Training Scale" (p.32), "Reading Real Pretraining Runs" (p.43).
- Chapter 3 starts cleanly immediately after Chapter 2's complete "Sources and further reading"
  section (page 14 -> page 15); Chapter 6 starts cleanly immediately after Chapter 5's complete
  "Sources and further reading" section (page 42 -> page 43). Neither of the two previously-fixed
  orphan-fragment pages has returned.
- Page 44 is Chapter 6's complete "6.3 Mental model or analogy" callout box, rendering identically
  to the accepted RC1 — confirmed intentionally sparse, not reopened.
- Figures remain sharp and legible (spot-checked Chapter 5's Figure 6, the critical-path timeline,
  on page 34); dense tables (Chapter 5's Table 10, page 39) and equations (e.g. page 34's
  Equations 17-19 plus the "Common misconception" callout) render intact with no clipping or
  overlap.
- Answer Key transitions are clean (e.g. Chapter 6's Answer Key flows directly into the
  Bibliography heading on page 63 without a split question/answer block).
- Bibliography entries are complete; the final continuation (page 64) still ends with exactly
  three complete entries ([10], [11], [12]) — confirmed unchanged and acceptable.
- Page headers, footers, and numbering are sequential 1-64 throughout, no resets, no duplicates.
- No clipping, overlap, broken glyphs, mid-word title splitting, or unintended blank pages found.
- No internal paths, raw source IDs, filenames, build-script names, commit metadata, revision
  history, or draft/RC wording appears anywhere in the extracted text.

### Low-content-page detector results (classified)

Per-page `pdftotext` character counts flagged the same pages as RC1's own scan, confirming
pagination is unchanged:

| Page | Characters | Classification |
|---|---|---|
| 64 | 428 | Acceptable — bibliography tail, three complete entries |
| 44 | 1,269 | Accepted intentional — Chapter 6's complete analogy callout |
| 39 | 1,314 | Intentional — dense table (Chapter 5's Table 10), low text density is expected for a table-heavy page |
| 10, 28, 51, 13, 40, 23, 29, 22, 16, 31, 8, 7 | 1,800-2,700 | Normal variation for chapter-opening pages, figure captions, and worked-example pages; not stray fragments |

**Zero stray-fragment pages** were found. No page contains only an orphaned continuation of a
sentence or list from the previous page.

---

## Artifact Preservation

All preserved, none deleted/renamed/overwritten:

```
outputs/_releases/05-llm-training/05-llm-training-workbook-rc1.pdf        (RC1, accepted, frozen)
outputs/_development/05-llm-training/superseded-rc1-pre-pagination-fix/
  05-llm-training-workbook-rc1-superseded.pdf                             (pre-pagination-fix RC1, preserved)
outputs/_development/05-llm-training/integrated-dev-build/
  05-llm-training-workbook-dev.pdf                                        (development build, preserved)
workbooks/05-llm-training/ch0[1-4]-review.pdf                             (chapter review packages, preserved)
workbooks/05-llm-training/chapters/, solutions/, data/, figures/          (all chapter sources and audit evidence, untouched)
```

### Build scripts

```
scripts/build_final.py        (Workbook 04's own canonical-build script -- untouched, reused as a model)
scripts/build_wb05_final.py   (new, Workbook 05's canonical-build script -- tracked)
```

---

## Process-Count Checkpoints

| Checkpoint | Count |
|---|---|
| Start of task (Phase 1) | 21 |
| After Phase 2 (registry update) | 22 |
| After Phase 4 (canonical build) | 22 |
| Before Phase 5 validation | 22-25 |
| Before pushing (Phase 8) | recorded at push time, see commit-time check |
| Completion | recorded in final report to user |

Never reached 28 (the stop-and-report threshold) or 32 (the hard-stop threshold) at any point in
this task.

---

## Workbook 04 Checksum Confirmation

`outputs/04-modern-llm-architecture-workbook.pdf` SHA-256:
`f1a8919587b0e61bd9d476d0b7c2e533d2e0428b03f4f1418b0c67433b14e048` — unchanged from every prior
check in this project's history. Workbook 04 was not touched by this task.

---

## Publication Readiness Statement

**Workbook 05 is PUBLICATION-FROZEN**, pending the commit and push recorded in Phase 8 of the
task this report accompanies. Every blocking gate in Phase 5 passed (only the three known,
pre-existing Workbook 04 baseline failures remain, explicitly out of scope for this task). The
canonical final PDF is content- and pagination-equivalent to the independently-accepted RC1,
differing only in its "Final Edition" subtitle designation. No further chapter editing, RC2, or
TSFM addendum work began in this task.

---

## Explicit Confirmations

- RC1 and all prior development/review artifacts are preserved, not deleted or overwritten.
- No chapter prose, solutions, questions, figures, worked examples, source claims, or accepted
  pagination changed during finalization.
- The canonical final PDF is a build product, correctly ignored by `.gitignore`, not committed
  as a tracked file.
- `git diff --check` is clean; the full test suite shows zero new failures.
- No internal paths, source IDs, commit metadata, or draft/RC wording leaked into the canonical
  PDF's learner-facing text.
- Workbook 04's canonical checksum is unchanged.
- No TSFM addendum work and no subagent/guardrail reconfiguration began in this task.

---

**Report compiled by:** Claude Sonnet 5 (single-session, sequential execution; no subagents, no
background/parallel execution)
**Report timestamp:** 2026-10-05
