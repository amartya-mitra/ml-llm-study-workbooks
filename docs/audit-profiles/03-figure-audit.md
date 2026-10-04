# Audit profile: figure audit (stage 3 of 4)

**This is documentation, not an executable Claude Code subagent
definition.** It carries no YAML frontmatter and defines no tool
permissions, because it is not invoked via the Agent/Task tool and
must never be. The main agent performing a chapter review reads this
file and performs the checks below itself, as the third of four
**sequential** audit stages (after the numerical audit, before the
learner/PDF audit -- see `docs/audit-profiles/01-source-audit.md` for
the full stage order). No stage runs in parallel with another, and no
stage is delegated to a subagent, an Agent-tool call, a Workflow, or
any nested session.

## Purpose

Check a drafted workbook chapter's figures for semantic correctness,
dependency/causal ordering, label and legend accuracy, whether a
schematic is presented as measured data, consistency with the
worked-example JSON, presence of dedicated semantic invariant tests,
and visual bounds/clipping/overflow at final print scale.

## Scope discipline while performing this stage

Perform this stage read-only: never edit, write, or delete any file.
Shell access during this stage is for inspection only (e.g.
regenerating a figure's SVG to a scratch path to compare against the
committed one, running `pdftoppm`/`pdftotext` on an already-built
review PDF, grepping test files). Never overwrite a committed
`figures/rendered/*.svg` or any other tracked file.

Ground every check in `docs/chapter-review-checklist.md` section 5
(figure correctness contract) and its "false positives" / known-defect
history at the bottom of that file -- several real figure bugs from
past chapters are documented there (a causally-invalid pipeline
schedule, a mislabeled caption, a narrow-bar label overflowing its own
canvas, a legend overlapping an adjacent label). Treat these as a
known defect class to specifically re-check for, not merely background
reading.

## What to check

For every figure the chapter cites (every `figures/rendered/*.svg`
referenced from the chapter `.qmd`, with its generating
`figures/source/fig_*.py` script):

1. **Semantic correctness.** Does the figure actually show what its
   caption and surrounding prose claim it shows? Re-derive the
   figure's intended meaning from the prose, then check the rendered
   image (and, if useful, the generating script's logic) against that
   meaning directly -- not just "does it render without error."
2. **Dependency/causal ordering.** If the figure depicts a sequence,
   pipeline, or dependency graph (e.g. a schedule, a flow of
   derivation), verify the depicted order is actually valid -- no step
   drawn before its prerequisite, no cycle that shouldn't exist, no two
   things drawn as simultaneous that the underlying logic requires to
   be sequential (or vice versa).
3. **Labels, legends, captions.** Every label must be legible and
   correctly attached to what it labels; the legend must cover every
   distinct visual encoding used (color, dash pattern, border style);
   the caption's wording must match the diagram, not a stale or
   slightly-off description of what it used to show.
4. **Schematic vs. measured data.** If a figure's numbers come from a
   toy/illustrative worked example, confirm the figure itself (its
   title bar, caption, or an explicit label) says so -- a schematic
   must never be presented in a way a skimming reader could mistake
   for a measured/published result.
5. **Consistency with the worked-example JSON.** Read the figure's
   generating script and confirm it loads its numbers from the
   chapter's own worked-example JSON output rather than hardcoding or
   re-deriving values independently. Cross-check a few values directly
   against that JSON.
6. **Dedicated semantic invariant test.** Confirm a test file exists
   that checks this figure's actual semantic invariants (ordering,
   value-equality against the JSON, label-to-category mapping) -- not
   merely that `tests/test_figures.py`'s generic bounds/well-formed-XML
   check passes. A figure with only the generic check is a `required`
   finding, not a pass.
7. **Visual bounds, clipping, overflow.** At final print scale (inspect
   the actual rendered page PNG from the review PDF, not just the raw
   SVG), check for: text overflowing its containing shape or the
   canvas edge, overlapping labels, labels placed on a shape too narrow
   to contain them, and any element clipped at a page margin.

## Output format

End the response for this stage with exactly one fenced ```json block
containing a JSON array of finding objects. Produce **one entry per
figure per check area** (items 1-7 above), even when clean -- use
`"severity": "no_action"` for a clean figure/area instead of omitting
it, so the array is a complete coverage record of every figure
inspected and what was checked on each.

```json
[
  {
    "severity": "blocker | required | optional | no_action",
    "file": "figure script/SVG path, or 'PDF p.N'",
    "issue": "one-sentence statement of the problem (or 'no issue found' for no_action)",
    "evidence": "what was compared -- caption text vs. rendered content, script logic vs. JSON values, or the specific visual defect",
    "proposed_correction": "the minimal concrete fix, or null for no_action",
    "affected_acceptance_criterion": "e.g. figures.semantic_tests_required"
  }
]
```

Save this array verbatim (e.g. to
`outputs/_development/<workbook>/chapter-gate/ch<NN>-figure-audit.json`)
for `scripts/chapter_gate.py --figure-audit-json` to ingest. Report
findings only during this stage; do not edit any file.
