# Addendum 04–05 v1.1.0 — publication report

Date: 2026-10-28. Follows `docs/publication-hygiene.md`.

## Acceptance

Human acceptance (user instruction, 2026-10-28) of the review PDF
`outputs/_development/addendum-04-05-tsfm/v1.1.0-review/addendum-04-05-tsfm-v1.1.0-review.pdf`:
23 pages, 508,460 bytes, SHA-256
`e3268c0d80f78c68e39334c9a8dd20305eb3049971d1d8285e08bba67e28887d`, at source
commit `774cf8a20c8a2f82420a0dc905408d4c63441777`. The v1.1.0 reopening is
closed and the addendum, chapters and contracts are `accepted_frozen`. No RC
checkpoint: the hygiene sequence does not require one.

## Canonical build

- Source commit (tag target): `00f3bb63185114f0c2231703cd2ea93394f77ac2`
- Command: `python3 scripts/build_addendum_final.py` (clean tree; worked
  examples and figures regenerate byte-identically).
- Output: `outputs/addendum-04-05-tsfm.pdf` (git-ignored) — 23 pages,
  508,386 bytes, SHA-256
  `68467ffb62bbf7734bb97e4387d5956349811d6d211b5d12501c5166b87d6ea2`.
- Earlier canonical preserved before replacement:
  `outputs/_development/addendum-04-05-tsfm/v1.0.0-canonical-archive/addendum-04-05-tsfm-v1.0.0.pdf`
  (SHA-256 `b7096e9b9291dc4319f8f3740303b42dcf784d3ec80bb2fb63cc66f7ac242b65`,
  verified), plus the builder's own `outputs/addendum-04-05-tsfm.pdf.prev-b7096e9b9291`.

## Final versus accepted review

- `scripts/check_addendum_final.py`: RESULT clean. The only text difference
  is the page-1 subtitle (descriptive subtitle → "Final Edition, version
  1.1.0"); page count 23 = 23; PDF Title metadata unchanged.
- 150-dpi renders: pages 2–23 are pixel-identical to the accepted review;
  page 1 differs only in the subtitle line and was inspected. Figure 4
  (p. 10), the licensing paragraph (p. 17), the answer-key transitions
  (pp. 19–22) and the bibliography (p. 23) are therefore identical to the
  pages inspected at review.
- The bibliography's pinned source-code commit (`a534bdb…`) is intended
  provenance, not leakage.

## Publication

Tag `addendum-04-05-tsfm-v1.1.0` (annotated) → `00f3bb6…`; release
"Addendum 04–05 v1.1.0 — Time-Series Foundation Models" with exactly one
asset, `addendum-04-05-tsfm.pdf`. The remote verification result is
recorded in the publication registry (`status: published`) only after a
fresh download reproduced the SHA-256 above. v1.0.0 (tag, release, asset)
is untouched and listed under `previous_releases`.

## Remote verification (2026-10-28)

- Release: https://github.com/amartya-mitra/ml-llm-study-workbooks/releases/tag/addendum-04-05-tsfm-v1.1.0
  (id 426278481; created as a draft, asset uploaded and verified by
  authenticated download, then published 2026-10-28T05:00:16Z; public,
  not draft, not prerelease; exactly one asset).
- Direct download: https://github.com/amartya-mitra/ml-llm-study-workbooks/releases/download/addendum-04-05-tsfm-v1.1.0/addendum-04-05-tsfm.pdf
  — anonymous download: 508,386 bytes, SHA-256 `68467ffb…6ea2`, 23 pages,
  "Final Edition, version 1.1.0" on page 1.
- Annotated tag object `9644d45f7593797529019141e6c776d95056fc5c` →
  commit `00f3bb63185114f0c2231703cd2ea93394f77ac2`.
- v1.0.0 re-verified read-only: annotated tag → `39294a2…`, single asset
  425,777 bytes, SHA-256 `b7096e9b…2b65`, 18 pages — unchanged.
