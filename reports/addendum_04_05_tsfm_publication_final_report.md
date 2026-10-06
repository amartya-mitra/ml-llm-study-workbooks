# Addendum 04-05 (TSFM): canonical build for publication

Date: 2026-10-06. Content status: `accepted_frozen`. This report is written
before publication; the outcome of the tag, release and remote verification
is recorded in the publication registry and README after they happen.

## Accepted inputs
- RC1 (independent human acceptance passed): 18 pages, 425,789 bytes,
  SHA-256 `a1599e499f3f02816961a7b78efcdef020dec5acfd150ce536c36a6e9b97286a`.
- Accepted review PDF SHA-256
  `d2fcd1cff746cbeeb154de0143d4996c6238f6fe715748ef713d8c589c4e3319`.
- Frozen source commit of the content: `aea2e38673556a8701c68fdb0fecddaab1a91d02`.

## Canonical build
Command: `python3 scripts/build_addendum_final.py`. It requires
`accepted_frozen`, renders from source (no copy of RC1), changes only the
subtitle in a temporary staging copy ("Release Candidate 1" becomes
"Final Edition"), fails if that substitution is absent, removes its staging
files, and refuses to overwrite a canonical PDF it cannot trace to its own
build manifest.

| Property | Value |
|---|---|
| Path (git-ignored; distributed only as a release asset) | `outputs/addendum-04-05-tsfm.pdf` |
| Pages | 18 (ceiling 24) |
| Words (pdftotext, all tokens) | 8,309 |
| Size | 425,777 bytes |
| SHA-256 | `b7096e9b9291dc4319f8f3740303b42dcf784d3ec80bb2fb63cc66f7ac242b65` |

## Verification
- RC1 versus final: a word-level text comparison shows exactly one change,
  "Release Candidate 1" replaced by "Final Edition". The renders are
  independent (different bytes and hashes from RC1 and the review PDF; both
  of those still match their accepted identities).
- `scripts/check_addendum_final.py` passes: page count, no near-empty pages,
  six module titles, six Quick recap sections, five figures, seven tables,
  six answer keys, bibliography, the corrected attention-cost, Moirai-cap,
  decoding and samples-versus-quantiles passages, no RC/review/draft wording,
  no learner-facing leakage, no unresolved references, no broken glyphs.
- All 18 freshly rendered pages were inspected at readable resolution: no
  clipping, overlap, broken glyphs, blank pages or fragments. Accepted
  intentional layouts are preserved: whitespace after pages 7 and 11 before
  atomic figures, partly empty last answer-key page, no table of contents.
- Scoped tests (116) and the registry, question, contract and
  publication-hygiene validators pass; `git diff --check` is clean. The full
  suite was not run.

## Publication plan
Tag `addendum-04-05-tsfm-v1.0.0` on the commit that contains this report and
the builder; release title "Addendum 04–05 v1.0.0 — Time-Series Foundation
Models"; one asset, `addendum-04-05-tsfm.pdf`. The publication registry stays
at `review_pending` in this commit because the recorded source commit must
equal the tag target, which is only known after this commit exists. The
registry and README move to `published` in the synchronization commit, after
the remote asset is downloaded and its checksum verified.
