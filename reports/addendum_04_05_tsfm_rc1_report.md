# Addendum 04-05 (TSFM): acceptance, content freeze and Release Candidate 1

Date: 2026-10-06. Status of the content: `accepted_frozen`.
Status of RC1: awaiting independent review. This is not a canonical build,
and no tag, release or push exists.

## 1. Accepted review artifact

| Property | Value |
|---|---|
| Path | `outputs/_development/addendum-04-05-tsfm/integrated-review/addendum-04-05-tsfm-review.pdf` |
| Pages | 18 |
| Size | 425,931 bytes |
| SHA-256 | `d2fcd1cff746cbeeb154de0143d4996c6238f6fe715748ef713d8c589c4e3319` |
| Accepted source commit | `aea2e38673556a8701c68fdb0fecddaab1a91d02` |
| Acceptance date | 2026-10-06 |

The human acceptance is recorded as reported by the project owner (independent
review of the corrected 18-page PDF passed). Properties were verified against
the file before any repository change.

## 2. Status changes

| Location | Before | After |
|---|---|---|
| `config/chapter-status-registry.yaml`, workbook entry and six chapters | `drafted_pending_human_review` | `accepted_frozen`, plus acceptance date, accepted source commit, review PDF SHA-256 and page count |
| `config/project.yaml` | `drafted_pending_human_review` | `accepted_frozen` |
| Six chapter contracts | `drafted_pending_human_review` | `accepted_frozen`; `allowed_paths` emptied and the module files moved to `frozen_paths`; `scoped_tests` and `visual_review` set to `pass` |
| Publication record | `review_pending` | **unchanged** (`review_pending`); note updated. Not `canonical_built`, not `published` |
| Tests | pinned the draft status | pin the frozen status and acceptance record |

`accepted_frozen` is the schema's existing value (chapter-contract schema,
status registry); no new value was invented.

## 3. RC1 build

Command: `python3 scripts/build_addendum_rc1.py`

The builder refuses to run unless the addendum is `accepted_frozen`, renders
`index.qmd` from source with Quarto/Typst (the only change is the subtitle
`Release Candidate 1`, applied to a temporary staging copy that is deleted
afterwards), and writes only the RC1 path. It never copies the review PDF and
never creates a canonical PDF, an RC2, a tag or a release.

| Property | Value |
|---|---|
| Path | `outputs/_releases/addendum-04-05-tsfm/addendum-04-05-tsfm-rc1.pdf` |
| Pages | 18 (ceiling 24) |
| Words (pdftotext, all tokens) | 8,310 |
| Size | 425,789 bytes |
| SHA-256 | `a1599e499f3f02816961a7b78efcdef020dec5acfd150ce536c36a6e9b97286a` |

## 4. Review versus RC1

- **Independent render:** different byte size (425,789 vs 425,931) and
  different SHA-256 from the review PDF. The review PDF is unchanged and still
  matches its recorded identity.
- **Text difference:** a word-level comparison of the extracted text shows
  exactly one change. The words of the old subtitle ("Tokens, patches,
  channels, horizons, and forecast distributions: what carries over from the
  LLM workbooks and what does not") are replaced by "Release Candidate 1".
  Nothing else differs. The phrase "Release Candidate 1" appears exactly once.
- The page structure, page count and figures are the same as in the accepted
  review.

## 5. Verification and validation

- `scripts/check_addendum_rc1.py`: all checks pass (independent render,
  subtitle-only text difference, 18 pages, no near-empty pages, six module
  titles, six Quick recap sections, five figure captions, seven table
  captions, six answer keys, bibliography, the corrected passages, no
  leakage or review/draft wording, no unresolved references, no broken
  glyphs, no canonical PDF).
- Scoped tests: 108 pass (structure, worked examples, figures, RC1).
- Validators: registry, questions (108 records), chapter contracts (8) and
  publication hygiene (offline, with local PDF check) pass. `git diff --check`
  is clean.
- Full repository suite: not run (no scoped failure required it).
- Workbooks 04 and 05: zero diffs; their canonical PDF checksums are unchanged
  (`12bcc6c1...`, `25a393bb...`).

## 6. Visual inspection (all 18 RC1 pages, fresh renders, readable resolution)

Title page with the RC1 subtitle; notation table; all six module openings
with their Quick recap sections; the corrected attention-cost passage and
its answer; the samples-versus-quantiles passage; the qualified
autoregressive-decoding passage; the Moirai cap equation, toy example,
question and answer; all five figures; all seven tables; module and answer-key
transitions; the bibliography; page numbering. No clipping, overlap, broken
glyphs, accidental blank pages, unresolved references, internal paths,
source IDs, filenames, editorial history, or review/draft wording.

## 7. Known intentional layouts

- Modest whitespace follows pages 7 and 11, where the next figure is atomic
  and does not fit.
- The last answer-key page and the bibliography page are partly empty; the
  bibliography is kept together on its own page.
- No table of contents, by design for a short addendum.

## 8. Freeze and safety

- The chapter prose, questions, solutions, claims, figures, worked examples
  and source mappings were not changed in this task.
- No canonical addendum PDF, tag, GitHub release or push exists. The
  publication record has not advanced.
- No Agent, background process or SLURM job was used. The temporary
  process-ceiling exception was not needed and the guard script was not
  altered.
