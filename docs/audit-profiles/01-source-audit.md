# Audit profile: source audit (stage 1 of 4)

**This is documentation, not an executable Claude Code subagent
definition.** It carries no YAML frontmatter and defines no tool
permissions, because it is not invoked via the Agent/Task tool and
must never be. The main agent performing a chapter review reads this
file and performs the checks below itself, as the first of four
**sequential** audit stages:

```
source audit (this file)
  -> numerical audit
  -> figure audit
  -> learner/PDF audit
  -> consolidate findings
  -> at most one correction pass
  -> rerun only failed audit stages
  -> stop if required findings remain
```

No stage runs in parallel with another. No stage is delegated to a
subagent, an Agent-tool call, a Workflow, or any nested session. See
`.claude/skills/review-workbook-chapter/SKILL.md` for how this stage
fits into the full review procedure, and
`docs/chapter-factory-operator-guide.md` for why the four files that
used to live under `.claude/agents/*.md` were migrated here.

## Purpose

Verify a drafted workbook chapter's sourcing discipline: every primary
source was read in full text (not registry-summary-only), every
substantive claim has an evidence locator, quotations and numbers
match the source, and measured/reported/inferred/synthetic values are
kept distinct.

## Scope discipline while performing this stage

Perform this stage read-only: do not edit, write, or delete any file,
and do not run a command that modifies repository state (no `git
commit`, `git add`, `rm`, `mv`, redirection into a tracked file, `sed
-i`, etc.). Shell access during this stage is for inspection only:
reading files, `grep`, `pdftotext`/`pdfinfo` on an already-built
review PDF, and running an existing script read-only (e.g. `python3
scripts/validate_registry.py`). If a command would change any file
under version control, do not run it -- report that the item could not
be checked instead.

You will be told which chapter to audit (workbook id + two-digit
chapter number, e.g. `05-llm-training` chapter `06`). Ground every
check in these repo conventions -- read them first if not already read
this session:

- `AGENTS.md` (sourcing/originality rules -- this audit exists to
  enforce them).
- `docs/chapter-review-checklist.md` section 0 ("Source-ready") and
  its claim-ledger coverage guidance.
- `sources/registry.yaml`, `sources/coverage-matrix.yaml`,
  `shared/bibliography.bib`, `shared/claim-ledger-schema.yaml`.
- The chapter's own `claim-ledger.yaml` entries (filter by
  `chapter: "chNN"`).

## What to check

1. **Full-text verification, not registry-summary reliance.** For
   every `src-NN` cited in the chapter/solutions `.qmd` files, confirm
   the registry entry's `authority_type`/`expected_use`/`last_verified`
   fields are sane, then independently confirm -- by fetching or
   reading the actual source text, not by trusting the registry's own
   summary prose -- that at least the specific sections the chapter
   draws on were genuinely read. If the primary source cannot be
   accessed during this stage, flag that as a `required` finding
   rather than assuming the drafting pass did the verification
   correctly.
2. **Evidence locators.** Every substantive factual claim (a number, a
   quote, a named result) must be traceable to a specific location --
   an equation/table/section number, not just "the paper." Check the
   claim-ledger entries for this chapter: each needs a `source_ids`
   list that resolves in the registry, a `verification_status` that is
   not silently `unverified_candidate` for a claim stated as fact in
   the chapter, and -- for `computed_by_script` entries -- that the
   referenced script actually exists and its output actually matches
   what the chapter states (spot-check a few).
3. **Quotation and number fidelity.** Spot-check at least 3-5 of the
   chapter's most load-bearing quoted numbers or direct quotes against
   the primary source. Flag any mismatch, paraphrase presented as a
   direct quote, or number that doesn't resolve to what the source
   actually states (units, rounding, and scope included).
4. **Measured vs. reported vs. inferred vs. synthetic.** The chapter
   must never blur these. A number from a paper's own measured
   benchmark, a number the paper itself reports without claiming to
   have measured it, a number this chapter derives/infers from stated
   formulas, and a deliberately synthetic/illustrative number (a toy
   worked example) must each be labeled as what they are, consistently.
5. **No registry-summary-only sourcing.** If a claim's only backing is
   a short registry description rather than content from the actual
   source, flag it -- the registry is a navigation aid, never itself
   evidence (see `AGENTS.md`).
6. **No unsupported causal inference.** Flag any sentence that asserts
   X caused Y when the evidence given is correlational, temporal
   co-occurrence, or a single source's own unverified claim.
7. **Time-sensitivity.** Confirm fast-changing claims (hardware specs,
   achieved-vs-peak percentages, current-as-of numbers) are marked
   with an explicit "as of" qualifier rather than stated as timeless.

## Output format

End the response for this stage with exactly one fenced ```json block
containing a JSON array of finding objects -- this is the
authoritative, machine-readable output the chapter gate parses; any
prose before it is for the human reader only. Produce **one entry per
distinct check area** (items 1-7 above), even when that area is clean
-- use `"severity": "no_action"` for a clean area instead of omitting
it, so the array is a complete coverage record, not just a list of
problems.

```json
[
  {
    "severity": "blocker | required | optional | no_action",
    "file": "repo-relative path, or 'PDF p.N' for the rendered review PDF",
    "issue": "one-sentence statement of the problem (or 'no issue found' for no_action)",
    "evidence": "what was checked and what was found -- quote the relevant chapter text and source text side by side when possible",
    "proposed_correction": "the minimal concrete fix, or null for no_action",
    "affected_acceptance_criterion": "e.g. sources.full_text_required"
  }
]
```

Save this array verbatim (e.g. to
`outputs/_development/<workbook>/chapter-gate/ch<NN>-source-audit.json`)
for `scripts/chapter_gate.py --source-audit-json` to ingest. Do not
propose edits to any file during this stage; report findings only --
corrections happen in the single bounded correction pass after all
four stages have run (see `.claude/skills/review-workbook-chapter/SKILL.md`).
