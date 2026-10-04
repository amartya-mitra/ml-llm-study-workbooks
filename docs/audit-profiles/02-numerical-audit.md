# Audit profile: numerical audit (stage 2 of 4)

**This is documentation, not an executable Claude Code subagent
definition.** It carries no YAML frontmatter and defines no tool
permissions, because it is not invoked via the Agent/Task tool and
must never be. The main agent performing a chapter review reads this
file and performs the checks below itself, as the second of four
**sequential** audit stages (after the source audit, before the figure
audit -- see `docs/audit-profiles/01-source-audit.md` for the full
stage order). No stage runs in parallel with another, and no stage is
delegated to a subagent, an Agent-tool call, a Workflow, or any nested
session.

## Purpose

Try to **falsify** a drafted workbook chapter's quantitative content:
equations, units, worked-example calculations, rounding,
collective-volume conventions, per-device vs. global quantities,
constraint uniqueness, and question/answer/figure/JSON numerical
agreement.

## Scope discipline while performing this stage

Perform this stage read-only: never edit, write, or delete any file,
and never run a command that modifies repository state. Shell access
during this stage is for inspection only: running the chapter's own
worked-example script to recompute its output, `grep`/`pdftotext` for
cross-checking, and read-only validator scripts. If recomputing
requires writing a JSON output file, write it to a scratch location
(e.g. `/tmp` or a scratchpad directory), never over the repo's
committed `data/worked-examples/*.json` file, unless deliberately
diffing against the committed version -- in which case discard the
scratch copy afterward and leave the repo clean.

This stage is explicitly **adversarial**: attempt to falsify the
worked example and every numerical claim, not merely to confirm the
chapter's own intended result. A clean rerun that matches the
chapter's stated numbers is necessary but not sufficient -- also check
whether the calculation is *correct*, not just *internally consistent
with itself*.

Ground every check in:
- `docs/chapter-review-checklist.md` sections 5-7 (figure/question/
  worked-example contracts) and the "false positives" history at the
  bottom of that file (read it -- several real bugs from past chapters
  are documented there, e.g. a local-shard-size mistaken for a
  communication payload, a flawed uniqueness claim in a design
  question).
- The chapter's own `data/worked-examples/*.py` script and its `.json`
  output.
- The chapter's own scoped test file(s) (`tests/test_wb0N_chNN_*.py`).

## What to check

1. **Recompute, don't trust.** Actually run the worked-example script
   (to a scratch output path) and diff its numbers against what the
   chapter prose, the figure, the questions, and the answer key each
   state. Any mismatch -- even a rounding-direction difference -- is a
   finding.
2. **Units and dimensional consistency.** Every formula must be
   dimensionally sound; every number in prose must carry (or clearly
   inherit from context) the correct unit, and bytes-vs-bits,
   MiB-vs-MB, and elements-vs-bytes must never be conflated.
3. **Collective-volume and measurement conventions.** If the chapter
   involves a communication collective (all-reduce, all-gather,
   reduce-scatter, etc.), confirm the chapter declares one explicit
   convention (e.g. "one-direction send volume per rank") and uses it
   consistently -- not local-shard-size in one place and transmitted
   volume in another. If it involves memory, confirm logical/
   theoretical/measured-allocator/sampled-framebuffer categories (per
   whichever taxonomy the workbook has already established) are not
   conflated.
4. **Per-device vs. global quantities.** Explicitly check every
   throughput/memory/compute number for whether it is per-device or
   aggregate, and whether the chapter is consistent about which one it
   means at each point it's used.
5. **Rounding and significant figures.** Check that stated rounded
   values are consistent with the underlying computation (e.g. a value
   stated as "approximately X" should actually round to X, not to
   something else that was silently substituted).
6. **Constraint uniqueness.** For any question or worked example that
   claims a quantity is the *unique* solution to stated constraints,
   verify that claim directly -- brute-force or algebraically check
   whether an unstated counterexample satisfies the same constraints
   but gives a different answer. This exact failure mode (an
   under-constrained question whose claimed-unique answer is not
   actually unique) has happened in this project before; treat it as a
   known, high-probability defect class, not a hypothetical.
7. **Question/answer/figure/JSON four-way agreement.** Every number
   that appears in more than one of {chapter prose, figure, Check-your-
   understanding questions, Answer Key, worked-example JSON} must be
   identical (after correct rounding) everywhere it appears. Grep for
   the number in all four places explicitly.
8. **Invalid-input handling.** If the worked-example script validates
   its own inputs (rejects a bad config), confirm the validation logic
   is actually correct and not merely present -- try to think of an
   invalid input it would wrongly accept, or a valid one it would
   wrongly reject.

## Output format

End the response for this stage with exactly one fenced ```json block
containing a JSON array of finding objects. Produce **one entry per
distinct check area** (items 1-8 above), even when clean -- use
`"severity": "no_action"` for a clean area instead of omitting it, so
the array is a complete coverage record of every number/claim actually
recomputed or cross-checked, not just a list of problems.

```json
[
  {
    "severity": "blocker | required | optional | no_action",
    "file": "repo-relative path, or 'PDF p.N'",
    "issue": "one-sentence statement of the problem (or 'no issue found' for no_action)",
    "evidence": "the specific numbers compared, and the recomputation showing the discrepancy or confirming agreement",
    "proposed_correction": "the minimal concrete fix, or null for no_action",
    "affected_acceptance_criterion": "e.g. worked_examples.prose_crosscheck_required"
  }
]
```

Save this array verbatim (e.g. to
`outputs/_development/<workbook>/chapter-gate/ch<NN>-numerical-audit.json`)
for `scripts/chapter_gate.py --numerical-audit-json` to ingest. Report
findings only during this stage; do not edit any file.
