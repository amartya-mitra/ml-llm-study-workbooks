---
name: integrate-workbook
description: Prepares the future whole-workbook integration workflow (combining all accepted chapters into one canonical book, with cross-chapter consistency checks). NOT run by the infrastructure task that created this file -- it is a scaffold for a later task to execute explicitly. Has significant side effects (would produce a canonical PDF). Only invoke this explicitly, and only once every required chapter is accepted_frozen -- never automatically.
allowed-tools: Read, Grep, Glob, Bash
disable-model-invocation: true
---

# Integrate a workbook (scaffold -- not yet executable end to end)

**Status: prepared, not run.** This skill was authored as part of the
"chapter factory" infrastructure task
(see `docs/chapter-factory-operator-guide.md`) specifically to be
*ready to invoke later*, once every chapter of a workbook is
`accepted_frozen` in `config/chapter-status-registry.yaml`. That
infrastructure task explicitly did not execute this skill, does not
mark any chapter accepted as a side effect of writing it, and does not
build a canonical PDF while authoring it.

Do not invoke this until:

1. Every chapter listed for the target workbook in
   `config/chapter-status-registry.yaml` has `status:
   "accepted_frozen"` -- not `"drafted_pending_human_review"`. As of
   this skill's authoring, Workbook 05's Chapter 6 is still
   `drafted_pending_human_review`; this skill is not yet runnable for
   `05-llm-training` for that reason alone.
2. A human has explicitly asked for whole-workbook integration, by
   name -- never infer this from "the last chapter looks done."

## Intended steps (for the task that eventually runs this)

1. **Repository-state gate** identical in spirit to
   `draft-workbook-chapter`'s step 1: confirm branch/HEAD/clean tree,
   confirm every chapter's `accepted_frozen` status in the registry,
   confirm no chapter contract disagrees with the registry
   (`python3 scripts/validate_chapter_contract.py`).
2. **Cross-chapter consistency pass**: notation/symbol reuse across
   chapters, no duplicate claim-ledger ids, no duplicate question ids
   (`python3 scripts/validate_questions.py` already checks this
   project-wide), consistent voice/terminology at chapter boundaries,
   no chapter re-teaching another's mechanism where it should instead
   cite back to it.
3. **Full-book build**: this is the one context where producing the
   actual canonical PDF (`outputs/<workbook>-workbook.pdf`, per
   `scripts/workbook_qa.py`'s `WORKBOOK_REGISTRY`) is appropriate --
   everywhere else in this workflow, that output is explicitly
   forbidden during chapter-level drafting/review.
4. **Full-book QA**: `python3 scripts/workbook_qa.py --workbook <id>`
   (no `--chapter`), which runs structure/build/test/validator/text-
   scan checks against the whole book.
5. **Visual regression against the full book**, following the same
   page-hash-and-diff approach `scripts/visual_regression.py`
   established at chapter scope (see that script and
   `docs/chapter-factory-operator-guide.md`'s visual-regression
   section) -- extended to whole-book page count.
6. **Commit locally; do not push** unless the task explicitly says
   otherwise.
7. **Stop for human acceptance** of the integrated book -- this skill
   does not itself promote anything to a release candidate; that is
   `freeze-workbook-release`'s job, invoked separately.

This skill intentionally stops here. Flesh out the steps above into
real, tested orchestration only when a task actually asks for
whole-workbook integration to run.
