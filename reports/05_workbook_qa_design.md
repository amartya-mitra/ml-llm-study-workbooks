# Workbook QA Design — `scripts/workbook_qa.py`

Date: 2026-09-26
Baseline commit SHA: `e604832`
Companion to: `reports/05_openresearch_integration_notes.md`

This is the fixed QA contract for workbook 05 (and, since the script is
parameterized by `--workbook`, reusable for any future workbook without
code changes — only a new `WORKBOOK_REGISTRY` entry).

## The one stable invocation

```sh
python3 scripts/workbook_qa.py --workbook 05-llm-training
```

No other flags change behavior, and no environment variable is read by
this script. Per-workbook differences (title, canonical PDF filename)
live in `WORKBOOK_REGISTRY`, a plain dict at the top of the script —
committed code, not an invocation-time choice. This mirrors the "fixed
run command, identical on every node" rule `orx-experiment-tree`
describes, without requiring the `orx` binary.

## What each step does, and why

| # | Step | Implementation | Notes |
|---|---|---|---|
| 1 | Verify source structure | Checks `workbooks/<id>/index.qmd`, `chapters/`, `solutions/` exist | Fails fast, structured JSON, no traceback, if a workbook has no content yet (verified against workbook 05 today — see baseline run below) |
| 2 | Build the candidate PDF | `quarto render <index.qmd> --to typst`, copy to `outputs/<canonical_pdf>` | **Preserves any prior canonical PDF** under this run's own dev directory before overwriting — added after noticing no other step in this script did that by default; every existing RC build script in this repo does |
| 3 | Run the test suite | `unittest.TestLoader().discover("tests")`, in-process | Reuses the repo's existing `tests/` — no new test infra |
| 4 | Registry/question/notation/worked-example validators | `scripts/validate_registry.py`, `scripts/validate_questions.py` | Notation and worked-example checks are covered by the same registry/question validation and by step 3's per-chapter worked-example tests — not reimplemented separately |
| 5 | Extract PDF text | `pdftotext <pdf> -` | Feeds steps 6 and the word-count field |
| 6 | Text checks | Regex scans for internal paths, `src-\d+` ids, commit-hash-shaped tokens, stale "release candidate N" wording, duplicated chapter numbers, missing/incomplete chapter headings (cross-checked against each chapter `.qmd`'s own heading, with inline Typst directives stripped first), unresolved placeholders (TODO/TBD/FIXME/lorem ipsum/etc.), and mojibake characters | Same categories this project's WB04 RC-review passes checked by hand, now automated |
| 7 | Page count + filename | `pdfinfo`, compare basename to `WORKBOOK_REGISTRY` | Catches a build that silently wrote the wrong file |
| 8 | Render every page | `pdftoppm -png -r 170` into `outputs/_development/<id>/qa-runs/<short-sha>/pages/` | Development-only, gitignored by the existing generic `outputs/_development/` rule — no `.gitignore` change needed |
| 9 | Contact sheet | A pure-stdlib HTML grid (`<img>` tags over the page PNGs) | **No Pillow, no ImageMagick, no PyYAML are installed in this environment** — confirmed by direct check before writing this script, not assumed. A composited raster contact sheet was not honestly claimable; an HTML grid is the stdlib-only equivalent and is genuinely useful for broad inspection in a browser |
| 10 | JSON summary | `outputs/_development/<id>/qa-runs/<short-sha>/qa-summary.json` | Keyed by commit SHA (not a timestamp) so re-running the same commit reuses the same evidence directory — durable, reproducible evidence per Phase 4 |

## Baseline run (the smoke test)

```sh
$ python3 scripts/workbook_qa.py --workbook 05-llm-training
```

Result: `"status": "fail"`, stopping cleanly at step 1 with
`"workbooks/05-llm-training/index.qmd does not exist -- nothing to
build yet."` — no crash, no traceback, a valid structured result.
This is the correct outcome today: workbook 05 has no chapters, so
there is nothing to build. It demonstrates the script itself works
before any chapter exists, and will re-run automatically once
`index.qmd` is scaffolded — no script changes needed at that point.

Full JSON at
`outputs/_development/05-llm-training/qa-runs/e604832...b/qa-summary.json`
(gitignored, per the existing `outputs/_development/` rule).

**This script was not run against workbook 04** in this session, to
guarantee zero risk of touching its published, checksum-verified
canonical PDF (`outputs/04-modern-llm-architecture-workbook.pdf`,
confirmed unchanged before and after this session's work — see below).

## Known limitation, stated rather than hidden

Step 2's build path does not special-case a workbook's release-status
subtitle the way `scripts/build_final.py` does for workbook 04 (which
temporarily swaps "Release Candidate N" for "Final Edition" before
rendering the canonical PDF, then restores the source). This script
always builds from the source `.qmd` files exactly as committed. For
workbook 05, this is not yet a concern (no release-status text exists
yet); if a future canonical build needs the same subtitle swap, that
logic should be added to this script's `build_pdf()` rather than
duplicated into a fifth `build_final.py`-style one-off script.
