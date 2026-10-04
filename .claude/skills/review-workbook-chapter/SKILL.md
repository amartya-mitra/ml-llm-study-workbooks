---
name: review-workbook-chapter
description: Orchestrates auditing (and, if needed, one bounded correction of) an already-drafted workbook chapter -- review-PDF verification, four SEQUENTIAL audit stages performed directly by the main agent (source, numerical, figure, learner/PDF -- no subagents, no Agent-tool calls, no parallel execution), severity classification via the deterministic chapter gate, one bounded correction pass for required findings, rebuild and re-audit, an acceptance report, local commit, and stop without beginning the next chapter. Has side effects (may edit files, commits locally). Only invoke this explicitly -- never automatically.
allowed-tools: Read, Grep, Glob, Bash, Edit, Write
disable-model-invocation: true
---

# Review (and optionally correct) a workbook chapter

Use this on a chapter that is already drafted
(`identity.status: "drafted_pending_human_review"` in its contract) --
either for a fresh acceptance review, or for a scoped correction task a
human has explicitly requested on an `accepted_frozen` chapter (in
which case step 0 below is mandatory and non-negotiable).

Read `docs/chapter-review-checklist.md` and
`docs/chapter-factory-operator-guide.md` first.

## Step 0 -- Frozen-scope check (mandatory before touching anything)

1. Read `config/chapter-status-registry.yaml`. If this chapter's
   status is `accepted_frozen`, you may still **audit** it (read-only)
   freely, but you may **not edit** any of its `frozen_paths` unless
   the human's own request for this task explicitly names a correction
   to make -- and even then, add an entry to `active_overrides` in the
   registry (by hand, in the same commit as your fix) naming exactly
   what was authorized, then remove that entry once the fix is
   committed. Never grant yourself an override from an ambiguous or
   implied instruction -- if in doubt, audit only and report back
   without editing.
2. If this chapter's status is `drafted_pending_human_review`, proceed
   normally -- this is the expected, common case (fresh review of a
   just-drafted chapter).

## Step 1 -- Review-PDF verification

Build or confirm the standalone review package:

```
rm -rf outputs/_development/<id>/chapter-<NN>-review/pages
python3 scripts/build_chapter_review.py --workbook <id> --chapter <NN>
```

Confirm the manifest and page count look sane before proceeding --
don't audit a stale or partially-built PDF.

## Step 2 -- Run the four audit stages sequentially, yourself

**No subagents. No Agent-tool calls. No Workflow calls. No parallel
execution.** You (the main agent) perform all four stages yourself,
one after another, reading each profile document immediately before
performing that stage:

```
docs/audit-profiles/01-source-audit.md       -> source audit
docs/audit-profiles/02-numerical-audit.md    -> numerical audit
docs/audit-profiles/03-figure-audit.md       -> figure audit
docs/audit-profiles/04-learner-pdf-audit.md  -> learner/PDF audit
```

For each stage: read that profile's "What to check" list, perform the
checks against the workbook id / chapter number / review-PDF path /
relevant file paths you were given, and end your own response for that
stage with the required fenced ```json findings array. Save each
stage's JSON verbatim to
`outputs/_development/<id>/chapter-gate/ch<NN>-<stage>-audit.json`
(`<stage>` is `source`/`numerical`/`figure`/`learner-pdf`) before
moving to the next stage.

## Step 3 -- Severity classification via the deterministic gate

```
python3 scripts/chapter_gate.py --workbook <id> --chapter <NN> \
  --review-pdf outputs/_development/<id>/chapter-<NN>-review/<id>-ch<NN>-review.pdf \
  --source-audit-json outputs/_development/<id>/chapter-gate/ch<NN>-source-audit.json \
  --numerical-audit-json outputs/_development/<id>/chapter-gate/ch<NN>-numerical-audit.json \
  --figure-audit-json outputs/_development/<id>/chapter-gate/ch<NN>-figure-audit.json \
  --learner-pdf-audit-json outputs/_development/<id>/chapter-gate/ch<NN>-learner-pdf-audit.json
```

Read the resulting `status` (`pass` / `pass_with_warnings` / `fail`),
`skipped_checks`, and every audit's `blocker`/`required`/`optional`
counts. Known pre-existing Workbook 04 baseline failures are reported
separately (`known_baseline_failures`/`new_failures_beyond_baseline`)
-- never treat them as this chapter's problem, and never suppress or
hide them from your report either.

## Step 4 -- One bounded correction pass (only if `status == "fail"` from real findings, not from a scope violation)

If the gate failed because of actual `blocker`/`required` findings
(not because step 0 told you not to edit anything): make **one**
consolidated pass fixing every blocker/required finding together.
Prefer the minimal, surgical fix the finding's own
`proposed_correction` suggests; do not refactor or rewrite beyond
what's needed. Common fix patterns already established in this
project:

- all-gather/payload or unit-convention bugs -> fix the worked-example
  script, regenerate its JSON, then grep every place that number
  appears (chapter prose, figure, questions, answer key) and update
  all of them together, not just the one the finding named.
- a figure label overflowing its shape -> use the width-guard pattern
  in `figures/source/fig_training_step_timeline.py`.
- editorial-history leakage ("an earlier version/draft...") -> delete
  the offending clause, keep the underlying pedagogical point (e.g.
  the "Common trap" explanation) intact.
- an under-constrained "unique answer" question -> either add the
  missing constraint and prove uniqueness with a brute-force test, or
  redesign the question to ask the learner to demonstrate the
  non-uniqueness itself (see Workbook 05 Chapter 5's Question 5
  history for both failure and recovery patterns).

Then: rebuild the review package, re-run **only the audits whose
findings you addressed** (not necessarily all four), and re-run the
gate. **Maximum one correction cycle.** If the gate still fails after
that one pass, STOP and report the remaining blockers in full --
escalate to the human rather than attempting a second automatic cycle.

## Step 5 -- Acceptance report

Whether the outcome is `pass`, `pass_with_warnings`, or a stopped
`fail`, write a clear report covering: gate status, every
blocker/required finding and its disposition (fixed / still open),
every optional finding (recorded, not chased), the known baseline
failures (listed, not hidden), and the review-PDF path/page count.
**`pass_with_warnings` still requires a human visual-review pass**
before the chapter contract's `acceptance.visual_review` field may be
set to `"pass"` -- this skill never sets that field itself (see
`docs/chapter-factory-operator-guide.md`, "When human review remains
mandatory").

## Step 6 -- Commit locally

If you made any correction edits in step 4, commit them with a
message describing exactly what was fixed and citing the gate run that
found it. **Do not push.** If you made no edits (pure audit, or step 0
blocked you from editing), do not create an empty commit.

## Step 7 -- Stop

Do not begin drafting the next chapter, integration, or a release
freeze. Report and stop.
