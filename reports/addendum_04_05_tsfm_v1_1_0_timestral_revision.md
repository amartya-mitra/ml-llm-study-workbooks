# Addendum 04–05 v1.1.0 — Timestral revision (pending human review)

Date: 2026-10-27. Base commit: `e863c419ec231e7b15c62c23219077f8685b8199`
(published v1.0.0). Status: **drafted_pending_human_review**; publication
record `addendum-04-05-tsfm-v1.1.0` is `review_pending`. v1.0.0 (tag,
release asset, `outputs/addendum-04-05-tsfm.pdf`) is unchanged.

## Reopening

Human-instructed, narrowly scoped (see `reopenings` in
`config/chapter-status-registry.yaml`). Module contracts list only their
own chapter and answer key as `allowed_paths` (Module 3 also the new
`w7_timestral.py` and `fig_dhf_layout.py`). The six existing worked-example
scripts and five existing figure scripts are unchanged and regenerate
byte-identical SVGs. While the status is not `accepted_frozen`,
`scripts/build_addendum_final.py` refuses to build.

## Sources (verified 2026-10-27)

| id | source | evidence kind | pin |
|---|---|---|---|
| src-69 | Mistral news post (15 Oct 2026) | vendor claims | page fetched 2026-10-27 |
| src-70 | HF model cards + config.json, 4 sizes | documentation | 5M `bdd20cf…`, 28M `49b2640…`, 123M `5a14728…`, 209M `9874d25…` |
| src-71 | `mistralai/timestral` code + README | code-verified (inference) / documentation | commit `a534bdbd244d64f3d9d743f46c7bf6fc330ed4ff` |
| src-72 | docs.mistral.ai Timestral 1.0 page | documentation | fetched 2026-10-27 |

No paper or technical report exists ("will follow" / "coming soon"); a web
search found none. Nothing was installed, no weights downloaded, no
inference run. Benchmark leadership was **not** independently verified.

## Code-verified (inference) mechanisms

Causal per-patch scaling (running mean/std to each patch's end) + asinh;
NaN → 0 with missing flag, excluded from statistics; left padding to a
multiple of 32; 32-step patches embedded from 32 values + 32 flags;
time / time+variate layer schedule; variate attention without position
encoding; role rules (targets/past-only causal, known-future bidirectional
over context + block horizon; covariates never read targets; known-future
read only known-future); `[Enc ; Dec]` layout with shared learned
forecast-query tokens (no-covariate path) and the general one-token-per-patch
layout (covariate path); single active block of ≤ K = 32 patches; block
rollout with median feedback; advancing refine frame; non-crossing quantile
head (21 levels); output axes (series, variates, horizon, quantiles);
categorical target encoding; default symmetric averaging and non-negative
clipping. Parameter counts from shapes: 5.21M / 27.8M / 122.6M / 209.3M,
matching documented fp32 sizes (21 / 111 / 490 / 837 MB).

## Unresolved (kept open in the text)

- Categorical covariates: blog "as categorical inputs directly" vs card,
  README and code (target encoding).
- GIFT-Eval metric label: blog "GMean WQL" vs card "CRPS" for 0.446.
- Training masks, loss weighting, synthetic generator, real-data mixture,
  and the "Modified MIT" modification: undisclosed.
- Code comments that state training equivalence (refine frame, numeric
  covariates) are maintainer statements, not verified.

## Review

Four read-only audits (source, technical, recap/Q&A, visual) found no
must-fix issues; all confirmed should-fix items were fixed before the final
build. Known v1.0.0-era issues deliberately left untouched (not in this
revision's scope): a prime-like glyph after digits before "'s" (also in the
published PDF), raw underscore labels in Figures 1/3/5, float-driven blank
space at some page bottoms, Figure 6 annotation wording.

Review PDF: `outputs/_development/addendum-04-05-tsfm/v1.1.0-review/addendum-04-05-tsfm-v1.1.0-review.pdf`
(23 pages, ceiling 24). `check_addendum_pdf_text.py` reports only the
pinned src-71 commit hash in the bibliography, kept on purpose.

## Correction pass (2026-10-28)

- Module 2 answer key: intro sentence and answer 1 wrapped in one
  non-breakable Typst block in that solutions file only; the sticky heading
  now moves with them (no global typography change, answer text unchanged).
- Module 6 licensing: the weights LICENSE was read in full on 2026-10-28
  (1,695 bytes, SHA-256 `648194727930df730890e9f9affdbcc5c930d406d6829559b25ca3d5a973fc8c`),
  byte-identical on `main` of all four model repos and at the cited
  Timestral-209M revision `9874d252ab0aae16f7f7c999f98f98d6ad7d8365`, which is
  still `main` (last commit 2026-10-15). Prose now separates the Apache-2.0
  inference-code license from the weights' "Modified MIT" license (attribution
  condition; USD 20 million monthly-revenue condition), restated without
  interpretation. src-70 registry/bibliography and claim-tsfm-release-012 updated.
  The LICENSE numbers the revenue condition "2." but refers to it as "(b)";
  recorded only in the registry note.
- Figure 4 and its prose: forecast tokens read the valid context, themselves
  and earlier forecast tokens in their block (mask geometry unchanged).
