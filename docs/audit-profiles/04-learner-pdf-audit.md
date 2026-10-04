# Audit profile: learner/PDF audit (stage 4 of 4)

**This is documentation, not an executable Claude Code subagent
definition.** It carries no YAML frontmatter and defines no tool
permissions, because it is not invoked via the Agent/Task tool and
must never be. The main agent performing a chapter review reads this
file and performs the checks below itself, as the fourth and final
sequential audit stage (after the figure audit, before consolidating
findings -- see `docs/audit-profiles/01-source-audit.md` for the full
stage order). No stage runs in parallel with another, and no stage is
delegated to a subagent, an Agent-tool call, a Workflow, or any nested
session.

## Purpose

Check a drafted workbook chapter's rendered review PDF and
learner-facing text: chapter structure, clarity, leakage of source
IDs/paths/filenames/editorial history, broken cross-references,
question/answer matching, table overflow, title wrapping, orphan
fragments, sparse-page intent, and bibliography completeness, by
inspecting every rendered page at full resolution.

## Scope discipline while performing this stage

Perform this stage read-only: never edit, write, or delete any file.
Shell access during this stage is for inspection only (`pdftotext`,
`pdfinfo`, `pdftoppm` on an already-built review PDF; `grep` over
`.qmd`/`.yaml` files). Never regenerate or overwrite the review PDF or
any page render during this stage -- if it does not already exist at
the expected path, report that as a `blocker` finding (the build step
must run before this audit, not be triggered by it).

Ground every check in `docs/chapter-review-checklist.md` sections 2-4
and 8 (pagination rules, leakage checks, cross-reference checks, and
the adversarial pre-commit review process), plus the "false positives"
/ known-defect history at the end of that file and its section 11
table of pre-existing gaps in already-accepted chapters (Chapters 1-2
lack a `{#sec-chN-check}` cross-reference; several chapters' figures
lack dedicated semantic tests). **Do not re-report a documented
pre-existing gap in an already-accepted chapter as a new defect** --
only report it if the chapter being audited actually owns the gap, and
even then, note explicitly whether it is a newly-introduced regression
or a previously-known, accepted gap.

## What to check

1. **Every rendered page, full resolution.** View every PNG in the
   review package's `pages/` directory, in order -- do not sample a
   subset. This is the one check in the whole workflow that cannot be
   replaced by a heuristic; actually look.
2. **Leakage.** Grep the extracted PDF text (`pdftotext`) and read the
   rendered pages for: raw `src-NN` ids, `.qmd`/`.py`/`.yaml`
   filenames, `outputs/`/`workbooks/`/`scripts/` path fragments,
   commit-hash-shaped tokens, review-process phrases ("review
   manifest", "contact sheet", "page render", "build instruction"),
   unresolved placeholders (TODO/TBD/FIXME/lorem ipsum), and -- a
   recurring real defect class in this project -- **editorial-history
   leakage**: phrases like "an earlier version/draft of this
   question/example...", "...and then corrected", "this was flawed and
   is now fixed". Ordinary learner-facing phrasing ("source,"
   "script-backed calculation," "verified programmatically") is NOT a
   leak; do not over-flag it.
3. **Broken cross-references.** Confirm every `@sec-...`/`@fig-...`/
   `@tbl-...`/`@eq-...` reference resolves to the right target, not
   merely to *some* target (the classic failure: the Answer Key
   references the bare chapter-level anchor instead of the "Check your
   understanding" subsection's own anchor).
4. **Question/answer matching.** Confirm the chapter's numbered
   questions, the Answer Key's numbered answers, and the
   `questions.yaml` records for this chapter are all the same count
   and address the same content, in the same order.
5. **Structure and clarity.** Confirm every required section is
   present (Learning objectives, Why this matters, Mental model,
   Visual overview, Technical core, Worked example, Compare and
   contrast, Check your understanding, Applied exercise, Interview
   lens, Chapter recap, Sources and further reading, Answer Key), with
   no scaffold/placeholder markers remaining, and that prose is
   genuinely readable (not just present) -- flag anything confusing
   enough that a learner seeing it cold would misunderstand it.
6. **Table overflow, title wrapping, clipping.** On every page with a
   table or a multi-line heading, confirm nothing overflows its
   column, cell, or the page margin, and that wrapped titles break at
   a sensible point rather than mid-word or illegibly.
7. **Orphan fragments.** Flag any page that is just the trailing 1-3
   lines of the previous section's content, stranded with mostly blank
   space below it, when a different page-break choice would have kept
   that content with the rest of its block.
8. **Sparse pages -- intentional vs. accidental.** A sparse-but-complete
   bibliography or answer-key page is acceptable; a sparse page caused
   by a mid-list split or an accidental break is not. Check which one
   is present by reading the actual content, not just the word count.
9. **Bibliography completeness.** Confirm every cited source has a
   bibliography entry, the entry list is not split mid-entry across
   pages, and (per project convention) a bibliography that legitimately
   spans multiple pages by splitting between whole entries is not
   itself a defect.

## Output format

End the response for this stage with exactly one fenced ```json block
containing a JSON array of finding objects. Produce **one entry per
page inspected plus one entry per check area** (items 1-9 above) --
use `"severity": "no_action"` for a clean page/area instead of
omitting it, so the array is a complete record that every page was
actually viewed, not merely assumed clean.

```json
[
  {
    "severity": "blocker | required | optional | no_action",
    "file": "'PDF p.N' or repo-relative path",
    "issue": "one-sentence statement of the problem (or 'no issue found' for no_action)",
    "evidence": "what was seen on the page, or the leakage match, or the cross-reference mismatch",
    "proposed_correction": "the minimal concrete fix, or null for no_action",
    "affected_acceptance_criterion": "e.g. learner_facing.forbid_revision_history"
  }
]
```

Include one `no_action`-or-worse entry per page number so the chapter
gate can confirm full-page coverage by counting entries against the
PDF's page count. Save this array verbatim (e.g. to
`outputs/_development/<workbook>/chapter-gate/ch<NN>-learner-pdf-audit.json`)
for `scripts/chapter_gate.py --learner-pdf-audit-json` to ingest.
Report findings only during this stage; do not edit any file.

## After this stage: consolidate and stop condition

Once all four stages have run, consolidate every finding across the
four JSON arrays. If any `blocker` or `required` finding remains, make
**at most one** consolidated correction pass addressing all of them
together, then rerun **only the audit stage(s) whose findings were
addressed** (not necessarily all four), then re-run
`scripts/chapter_gate.py`. If `blocker`/`required` findings still
remain after that one pass, stop and report them in full -- a second
correction cycle requires explicit human direction (see
`.claude/skills/review-workbook-chapter/SKILL.md`). `optional` findings
may be recorded without being chased, and do not block completion.
