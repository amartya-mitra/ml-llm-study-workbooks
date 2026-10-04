# AGENTS.md — Durable Project Rules

These rules govern all work in this repository, for both human contributors
and AI agents. They are durable: they should not be relaxed for convenience
and should not need to be repeated in every task prompt.

## Sourcing and originality

- Never copy long passages from web sources. Summarize and cite instead.
- Never reuse a source figure unless its license clearly permits it.
- Prefer original explanatory diagrams with source attribution over
  reproducing someone else's figure.
- Every substantive factual claim must be traceable to a source (registry
  entry ID, bibliography key, or explicit primary-source citation).
- Separate primary sources from commentary and secondary summaries — track
  this distinction in `sources/registry.yaml` (`authority_type`,
  `expected_use`).
- Record when every web source was last verified (`last_verified` field in
  the registry). Stale entries should be re-checked, not assumed current.
- Mark fast-changing claims and technologies as time-sensitive in the prose
  (e.g. "as of early 2026") rather than stating them as timeless fact.

## Technical accuracy

- Distinguish training-time behavior from inference-time behavior
  explicitly wherever both exist for a mechanism (e.g. attention, KV-cache,
  normalization).
- Distinguish logical/theoretical memory estimates (parameter counts x
  bytes, back-of-envelope FLOPs) from measured runtime memory (profiler or
  `nvidia-smi` output). Label which kind any number is.
- Do not fabricate citations, quotations, benchmarks, or equations. If a
  number or quote cannot be verified against a source, mark it as
  unverified or omit it.
- Preserve negative findings, ambiguities, and source disagreements rather
  than smoothing them over. If two sources disagree, say so.

## Pedagogy and content quality

- Keep questions answerable from the preceding material in the same
  chapter/workbook — no questions that require outside knowledge not yet
  introduced.
- Store figure-generating code beside or traceably linked to the rendered
  figure it produces (see `figures/source/` -> `figures/rendered/`
  convention).

## Build and validation discipline

- Render and visually inspect PDFs (via `pdftoppm` page images, or
  equivalent) before treating a document as complete. A successful compile
  is not the same as a correct layout.
- Do not use GPU or SLURM resources unless the task genuinely benefits from
  them. Authoring, rendering, and validation are CPU-only workloads.
- Never overwrite an existing validated PDF without preserving it (copy the
  prior version aside, e.g. with a date or hash suffix, before replacing
  `outputs/*.pdf`).

## Chapter factory workflow

Chapter-level drafting/review for any workbook goes through
`.claude/skills/draft-workbook-chapter/` and
`.claude/skills/review-workbook-chapter/` (explicit invocation only).
See `docs/chapter-factory-operator-guide.md` for the full mechanism
(audit subagents, the deterministic gate, the frozen-chapter status
registry and its override process) -- that detail stays out of this
file on purpose.
