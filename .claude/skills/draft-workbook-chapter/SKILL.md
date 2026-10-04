---
name: draft-workbook-chapter
description: Orchestrates drafting one new workbook chapter end to end -- repository-state verification, chapter-contract loading, source evidence preparation, drafting, worked examples, figures, questions/answers, four SEQUENTIAL audit stages performed directly by the main agent (no subagents, no Agent-tool calls, no parallel execution), one bounded correction pass, standalone review-PDF generation, local commit, and stop for human review. Has side effects (writes files, commits locally). Only invoke this explicitly when the user asks to draft a new chapter -- never automatically.
allowed-tools: Read, Grep, Glob, Bash, Edit, Write
disable-model-invocation: true
---

# Draft a workbook chapter

This skill turns "draft chapter N" from a repeated draft -> external
correction cycle into draft -> internal multi-audit -> one review PDF
-> human acceptance. It builds entirely on existing infrastructure --
read these before step 1, every time, even if you drafted a chapter
recently and remember the conventions:

- `AGENTS.md` (durable sourcing/technical-accuracy/pedagogy rules).
- `docs/chapter-review-checklist.md` (the full policy this workflow
  encodes).
- `docs/chapter-factory-operator-guide.md` (how this skill, its
  sibling `review-workbook-chapter`, the four sequential audit
  profiles under `docs/audit-profiles/`, and `scripts/chapter_gate.py`
  fit together).
- `shared/chapter-contract-schema.yaml` and an existing instance under
  `workbooks/<id>/chapter-contracts/*.yaml` as a concrete template.
- `config/chapter-status-registry.yaml` (frozen/accepted status of
  every existing chapter -- never edit this file from within this
  skill; it is updated by hand, separately, only after a human
  accepts a chapter).

## Step 1 -- Repository-state gate

Before touching anything:

1. `git branch --show-current`, `git rev-parse HEAD`, `git status
   --short`, `git rev-list --left-right --count origin/main...HEAD`.
2. If the working tree is not clean, STOP and report what is dirty --
   do not stash or discard anything yourself; ask the human.
3. Confirm the workbook's most recently accepted chapter(s) are
   present in `git log` as expected (cross-check against
   `config/chapter-status-registry.yaml`).
4. Confirm you are not about to touch any path listed as `frozen_paths`
   in that chapter's own contract (there isn't one yet for a brand-new
   chapter, but sibling chapters' contracts list them) or in
   `config/chapter-status-registry.yaml`'s entries for already-
   `accepted_frozen` chapters -- if the task asks you to touch one of
   those paths, STOP and report that this looks like a correction task
   for an existing chapter, not a new-chapter draft (use
   `review-workbook-chapter`'s bounded correction pass for that
   instead, under explicit human direction).

## Step 2 -- Load or create the chapter contract

- If `workbooks/<id>/chapter-contracts/ch<NN>.yaml` already exists
  (e.g. re-running after an interruption), read it and resume from
  wherever `acceptance` fields are still `"not_yet_run"`.
- Otherwise, write a new one now, `identity.status:
  "scaffold_only"` initially, `scope.allowed_paths` listing exactly the
  files you intend to create (chapter `.qmd`, solutions `.qmd`,
  worked-example `.py`/`.json`, figure `.py`/`.svg`,
  `questions.yaml`/`claim-ledger.yaml` entries), `scope.frozen_paths`
  listing every sibling chapter and Workbook 04 explicitly,
  `scope.canonical_output_allowed`/`release_output_allowed`/
  `push_allowed` all `false`. Validate it immediately: `python3
  scripts/validate_chapter_contract.py`.
- Update `identity.status` to `"drafted_pending_human_review"` once
  drafting (steps 3-7) is complete -- not before.

## Step 3 -- Source evidence preparation

Per `AGENTS.md`: every substantive claim must be traceable to a source
read in full, never a registry summary alone.

1. Check `sources/registry.yaml` for every source id the chapter
   contract names under `sources.required_source_ids`.
2. For each, fetch/read the actual primary text (or the specific
   sections needed) -- do not rely on the registry's own description.
3. Spot-check every quoted number, quote, or table value directly
   against that text.
4. Register any genuinely new source following the exact pattern an
   existing source uses across `sources/registry.yaml`,
   `sources/coverage-matrix.yaml`, `shared/bibliography.bib`, and (once
   a claim exists) `claim-ledger.yaml` -- only when a required concept
   is not adequately supported by already-registered sources.
5. Never silently compare numbers from runs/configs with different
   hardware, precision, sequence length, batch size, token budgets,
   model sizes, checkpoint positions, or evaluation protocols --
   either flag the difference explicitly in prose or avoid the
   comparison.

## Step 4 -- Draft the chapter

Follow the established section order exactly (see any already-accepted
chapter as the concrete reference for voice and rigor):

1. Learning objectives
2. Why this matters
3. Mental model or analogy
4. Visual overview
5. Technical core
6. Worked example
7. Compare and contrast
8. Check your understanding (5 questions, `{#sec-chN-check}` anchor on
   the heading -- never omit this; Chapters 1-2 predate this fix and
   are a known, documented gap, not a pattern to repeat)
9. Applied exercise
10. Interview lens
11. Chapter recap
12. Sources and further reading
13. Answer Key (separate solutions file, intro referencing
    `(@sec-chN-check)` directly, never the bare chapter-level anchor)

Use inline `callout-warning` "Common misconception" blocks where a
real, specific misconception exists to correct -- do not invent one
just to fill the slot.

## Step 5 -- Worked example and figure(s)

- One deterministic, pure-stdlib Python script under
  `data/worked-examples/`, writing a JSON output; explicitly separate
  sourced values, derived/computed values, and deliberately synthetic/
  toy values, both in the script's docstring and in chapter prose.
- At least one figure under `figures/source/fig_*.py` using the
  existing `_svg_helpers.py` `SVGCanvas`/`palette_hex`/
  `load_visual_style` helpers -- reuse established color semantics,
  don't invent new ones. Every figure must read its numbers from the
  worked example's own JSON, never hardcode/re-derive them.
- Guard every text label on a variable-width shape against overflow
  (see `figures/source/fig_training_step_timeline.py`'s
  `label_segment` helper for the established pattern) -- a narrow-bar
  label overflow has been a real, repeated defect.

## Step 6 -- Questions and answers

Exactly 5 questions in `questions.yaml` (ids like
`q-<NN>-<topic>-001..005`) plus 5 matching Answer Key entries, each
with an `*Answer.*` paragraph and a `*Common trap:*` paragraph. Cover
at minimum: one conceptual/terminology distinction, one calculation,
one comparison/validity judgment, one diagnosis, one synthesis/design
question requiring a justified next step. If any question claims a
unique numeric answer, prove uniqueness (brute-force enumeration in a
dedicated test), not merely assert it in prose.

## Step 7 -- Claim ledger

Record every substantive sourced claim in `claim-ledger.yaml` under
`chapter: "chNN"`, following an existing chapter's entries exactly
(`source_ids`, precise claim statement, `verification_status`,
location).

## Step 8 -- Internal multi-audit (sequential, no subagents)

Build the review package first (so the audits have a PDF to inspect):

```
python3 scripts/build_chapter_review.py --workbook <id> --chapter <NN>
```

**No subagents. No Agent-tool calls. No Workflow calls. No parallel
execution.** You (the main agent) perform all four audit stages
yourself, one after another, in this order:

```
docs/audit-profiles/01-source-audit.md       -> source audit
docs/audit-profiles/02-numerical-audit.md    -> numerical audit
docs/audit-profiles/03-figure-audit.md       -> figure audit
docs/audit-profiles/04-learner-pdf-audit.md  -> learner/PDF audit
```

For each stage: read that profile's "What to check" list immediately
before performing it, check it against the workbook id / chapter
number / review-PDF path / chapter/solutions/worked-example/figure
file paths, and end your own response for that stage with the
required fenced ```json findings array. Save each stage's JSON
verbatim to
`outputs/_development/<id>/chapter-gate/ch<NN>-<stage>-audit.json`
(`<stage>` is `source`/`numerical`/`figure`/`learner-pdf`; create the
directory if needed) before moving to the next stage -- do not
paraphrase or summarize the JSON before saving it, write it verbatim
so `scripts/chapter_gate.py` can parse it.

Run the deterministic gate:

```
python3 scripts/chapter_gate.py --workbook <id> --chapter <NN> \
  --review-pdf outputs/_development/<id>/chapter-<NN>-review/<id>-ch<NN>-review.pdf \
  --source-audit-json outputs/_development/<id>/chapter-gate/ch<NN>-source-audit.json \
  --numerical-audit-json outputs/_development/<id>/chapter-gate/ch<NN>-numerical-audit.json \
  --figure-audit-json outputs/_development/<id>/chapter-gate/ch<NN>-figure-audit.json \
  --learner-pdf-audit-json outputs/_development/<id>/chapter-gate/ch<NN>-learner-pdf-audit.json
```

## Step 9 -- One bounded correction pass

If the gate reports `fail` (any `blocker`/`required` finding, or a
missing/skipped check): make **one** consolidated pass fixing every
`blocker` and `required` finding together, then rebuild the review
package and rerun **only the audits that found something** (not
necessarily all four) plus the gate. Maximum one such cycle inside
this skill -- if the gate still fails after that one correction pass,
STOP and report the remaining blockers; do not loop again
automatically (a second cycle needs explicit human direction). You may
leave `optional` findings unaddressed; record them in the chapter
contract's notes rather than chasing them indefinitely.

## Step 10 -- Finalize the chapter contract

Update `acceptance.*` fields in `workbooks/<id>/chapter-contracts/ch<NN>.yaml`
to reflect the gate's actual results (`pass`/`pass_with_warnings`/
`fail` per category), `acceptance.visual_review: "not_yet_run"` always
(only a human sets this to `"pass"` -- see
`docs/chapter-factory-operator-guide.md`), and
`identity.status: "drafted_pending_human_review"`. Re-validate:
`python3 scripts/validate_chapter_contract.py`.

## Step 11 -- Commit locally

Stage exactly the files this chapter's contract names under
`scope.allowed_paths` (plus the contract file itself, `questions.yaml`,
`claim-ledger.yaml`, `index.qmd`, and the relevant scoped test files) --
never stage anything under a `frozen_paths` glob, never stage
`outputs/`. Commit with a descriptive message. **Do not push.**

## Step 12 -- Stop for human review

Report: commit SHA, files touched, sources read and how verified, the
gate's final JSON status, the review-PDF path and page count, and any
`optional` findings left unaddressed. Do not begin the next chapter,
integration, or a release freeze -- those are separate skills
(`integrate-workbook`, `freeze-workbook-release`), invoked only when
explicitly asked.
