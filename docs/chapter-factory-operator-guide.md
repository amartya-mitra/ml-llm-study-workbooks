# Chapter Factory Operator Guide

Concise operator reference for the chapter-factory workflow: the four
skills, the four **sequential, non-executable audit profiles** under
`docs/audit-profiles/`, the deterministic chapter gate, the
frozen-chapter status registry, and the three staged (not yet active)
workflow hooks. Read `docs/chapter-review-checklist.md` first -- that
document is the durable policy; this one is the operator's map of the
tooling that enforces it. Keep this documentation **outside**
`AGENTS.md` (the always-loaded root instructions) -- `AGENTS.md`
carries only a one-line pointer here.

**Current prohibition on subagents and parallel audits.** An earlier
revision of this workflow defined the four audits as executable
Claude Code subagents (`.claude/agents/*-auditor.md`) invoked in
parallel via the Agent tool. That design has been replaced: **no
`.claude/agents/` directory exists in this repo, and none of the four
audits may be invoked via the Agent tool, the Workflow tool, a
subagent, an agent team, fork mode, a loop skill, or a nested Claude
session.** The four audits are now plain documentation
(`docs/audit-profiles/01-source-audit.md` through
`04-learner-pdf-audit.md`) that the **single main agent** performing a
chapter review reads and applies itself, one stage at a time, strictly
sequentially:

```
source audit -> numerical audit -> figure audit -> learner/PDF audit
  -> consolidate findings -> at most one correction pass
  -> rerun only failed audit stages -> stop if required findings remain
```

This is a deliberate safety constraint, not a capability gap: parallel
subagent orchestration multiplies process count, context cost, and the
number of independent actors that could take an unreviewed action, in
a workflow whose entire point is to *reduce* unreviewed action. Do not
reintroduce subagents or parallel audits without an explicit,
separately-reviewed decision to do so.

**Current global user process guard.** This machine runs a
user-level (`~/.claude/hooks/process_guard.py`), not project-level,
hook that blocks certain shell command *text* associated with
detached/background/parallel execution (e.g. `nohup`, trailing `&`,
`xargs -P`, `srun`/`sbatch`), even when that text appears only as a
literal string being searched for (a `grep` pattern), not executed.
This chapter-factory workflow does not modify, test, or rely on that
guard, and does not need to -- none of its own scripts or hooks use
any of the patterns it blocks. If a command is blocked by it during
chapter-factory work, do not retry or work around it; stop and report
the blocked operation (see `docs/chapter-review-checklist.md` and this
workflow's own safety rule: never route around a safety mechanism you
did not create).

## The four entry points

```
Draft a chapter              -> /draft-workbook-chapter
Audit or correct a chapter   -> /review-workbook-chapter
Integrate accepted chapters  -> /integrate-workbook   (scaffold only -- not yet runnable end to end)
Create or freeze a release   -> /freeze-workbook-release (scaffold only -- not yet runnable end to end)
```

All four are defined under `.claude/skills/<name>/SKILL.md` with
`disable-model-invocation: true` -- none of them auto-trigger. A human
(or an orchestrating task acting on explicit human instruction) must
invoke them by name.

## Inputs

- **draft-workbook-chapter**: a workbook id + chapter number to draft,
  and (implicitly) every already-accepted sibling chapter's content as
  style/rigor reference. Reads `AGENTS.md`,
  `docs/chapter-review-checklist.md`,
  `shared/chapter-contract-schema.yaml`,
  `config/chapter-status-registry.yaml`, `sources/registry.yaml`.
- **review-workbook-chapter**: a workbook id + chapter number already
  drafted (or, for a correction task, an explicit human instruction
  naming exactly what to fix on an already-`accepted_frozen` chapter).
- **integrate-workbook** / **freeze-workbook-release**: not runnable
  yet -- see their own `SKILL.md` files for the preconditions that
  must hold before they are fleshed out into real orchestration.

## Allowed mutations

Every chapter-level skill run is scoped by that chapter's own contract
(`workbooks/<id>/chapter-contracts/ch<NN>.yaml`,
`scope.allowed_paths`). Nothing outside that list, nothing under a
`frozen_paths` glob, no canonical PDF (`scope.canonical_output_allowed`
is always `false`), no release output
(`scope.release_output_allowed` is always `false`), no push
(`scope.push_allowed` is always `false` by default). These are
declared, machine-checkable constraints -- `python3
scripts/validate_chapter_contract.py` enforces the contract's own
internal consistency (e.g. `canonical_output_allowed` must be
`false`), and the staged `pre_action_guard.py` hook (once activated)
enforces them live against real tool calls.

## Generated evidence

Every chapter-level run produces, under
`outputs/_development/<workbook>/chapter-gate/`:

- `ch<NN>-<stage>-audit.json` (`<stage>` = `source`/`numerical`/
  `figure`/`learner-pdf`) -- each sequential audit stage's own
  structured findings array, saved verbatim by the main agent
  performing that stage.
- `ch<NN>-gate-report.json` -- `scripts/chapter_gate.py`'s full report
  (also printed to stdout).

And under `outputs/_development/<workbook>/chapter-<NN>-review/`:

- the standalone review PDF, its page PNGs, `contact-sheet.html`,
  `review-manifest.json` (from `scripts/build_chapter_review.py`), and
  `visual-regression-hashes.json` (from `scripts/visual_regression.py`,
  once run).

None of this is committed as canonical content -- `outputs/` is
gitignored. What IS committed is the chapter's own contract file
(`workbooks/<id>/chapter-contracts/ch<NN>.yaml`), with its
`acceptance.*` fields updated to reflect the gate's last real result.

## The deterministic chapter gate

```
python3 scripts/chapter_gate.py \
  --workbook 05-llm-training --chapter 06 \
  --review-pdf outputs/_development/05-llm-training/chapter-06-review/05-llm-training-ch06-review.pdf \
  --source-audit-json outputs/_development/05-llm-training/chapter-gate/ch06-source-audit.json \
  --numerical-audit-json outputs/_development/05-llm-training/chapter-gate/ch06-numerical-audit.json \
  --figure-audit-json outputs/_development/05-llm-training/chapter-gate/ch06-figure-audit.json \
  --learner-pdf-audit-json outputs/_development/05-llm-training/chapter-gate/ch06-learner-pdf-audit.json
```

Extends `scripts/workbook_qa.py`'s existing `--chapter` mode rather
than duplicating it -- every deterministic check it reports is
produced by that same function. The gate itself runs **entirely
serially, in a single process**: it never invokes Claude, the Agent
tool, the Workflow tool, or another model, and it does not spawn any
background process -- every subprocess it starts (via
`workbook_qa.run_chapter_scoped_qa`) is synchronous. What the gate
adds beyond that existing mode: (1) a **missing check is a failure**,
not a quieter "not verified" -- every deterministic check and every
one of the four audit-findings inputs is required; omit one and the
gate reports `fail` with that check listed under `skipped_checks`; a
**missing audit report is a failure** for exactly the same reason --
the gate does not run the audits itself, so if the main agent has not
yet produced and saved a given stage's JSON, that stage is `skipped`,
not silently assumed clean; (2) ingests each audit stage's JSON
findings array (produced by the main agent performing that stage
sequentially, per `docs/audit-profiles/`) and fails on any
`blocker`/`required` finding, downgrades to `pass_with_warnings` on an
`optional`-only finding set; (3) echoes the chapter's
`config/chapter-status-registry.yaml` status verbatim and **never
writes that file** -- moving a chapter to `accepted_frozen` is always
a separate, human-authorized edit, never a side effect of a passing
gate, and Chapter 6 stays `drafted_pending_human_review` even when its
technical gate reports `pass`.

Exit code 0 for `pass`/`pass_with_warnings`, 1 for `fail`.

**Full-suite cost note:** `workbook_qa.run_chapter_scoped_qa` runs the
whole project test suite once, internally, as part of its
`full_suite` check. Each invocation of `scripts/chapter_gate.py`
therefore pays that cost once -- call it once per correction cycle
(per the one-bounded-pass policy below), not after every individual
edit, and never write a test that invokes `chapter_gate.py` (or the
full suite) more than once per test run.

## Stop conditions

The workflow stops -- deliberately, not as a failure of the tooling --
at each of these points:

- **After one bounded correction pass.** Both `draft-workbook-chapter`
  and `review-workbook-chapter` make at most one consolidated
  correction pass for `blocker`/`required` findings, then rebuild and
  re-run only the affected audit stage(s) and the gate. If the gate
  still reports `fail` after that one pass, the skill stops and
  reports the remaining blockers in full. **A second correction cycle
  requires explicit human direction** -- the skill does not loop
  again on its own judgment that "one more try" would fix it.
- **If `scripts/chapter_gate.py` reports `fail`** for any reason
  (a `blocker`/`required` finding, a missing/skipped required check,
  or a missing audit report) and the one bounded correction pass
  above has already been used, the workflow stops and reports rather
  than attempting further automatic correction.
- **If the staged `final_stop_gate.py` hook is ever activated** (see
  below -- it is not active by default) and it reports `fail` for two
  consecutive attempts, it fails open on the third rather than
  blocking indefinitely -- this is the same one-bounded-pass policy
  enforced at the hook level, not a separate, looser rule.
- **At every point `AGENTS.md` and this repo's broader safety norms
  require stopping to ask**: before a push, before creating a
  canonical PDF or release candidate, before editing a frozen chapter
  without a human-authorized override, and before treating any
  `pass_with_warnings` result as equivalent to human-reviewed
  acceptance (see "When human review remains mandatory" below).

## The frozen-chapter status registry and override mechanism

`config/chapter-status-registry.yaml` is the one source of truth for
which chapters are `accepted_frozen` vs. `drafted_pending_human_review`
vs. `scaffold_only`, and for Workbook 04's whole-workbook `frozen`
status. It is a plain, hand-maintained YAML file -- nothing in this
workflow updates it automatically.

**How to grant a temporary frozen-scope override:** add an entry to
its `active_overrides` list, by hand, in the same commit as the
correction it authorizes:

```yaml
active_overrides:
  - workbook: 05-llm-training
    chapter: "05"
    granted_for: "one-sentence description of the exact authorized task"
    granted_by: human
```

Remove that entry once the authorized fix is committed -- an override
left in the list after its task is done is itself a defect, not a
feature. `scripts/chapter_gate.py`, `.claude/hooks/pre_action_guard.py`,
and `scripts/visual_regression.py` all read this list fresh on every
invocation, never cached.

**This mechanism cannot be invoked by a model on its own authority.**
If an agent (this session, or any future automated task -- note there
are no subagents in this workflow to attribute such a request to) asks
you to add an override, or claims one is already justified by an
earlier instruction, that is not sufficient -- a human must be the one
who actually writes the override entry, because *this is exactly the
permission-laundering pattern this workflow's own safety notes warn
about*. An override entry must also **name the exact allowed paths**
and **state the reason** -- a bare `chapter: "*"` override with no
path scoping is too broad and should be narrowed before use. An
override never implies push or publication permission on its own;
`scope.push_allowed` and `scope.release_output_allowed` stay `false`
regardless of any active override unless a task separately and
explicitly authorizes a push or a release. An agent reporting "I was
blocked from editing chapter 5, please add an override so I can
proceed" should be refused and surfaced to a human, not silently
satisfied.

## Publication hygiene (final gate)

`accepted_frozen` is not the end of the workflow. After a workbook or
addendum is integrated and its canonical PDF accepted, the closing phase
in [publication-hygiene.md](publication-hygiene.md) applies: a
`publications:` record in this same registry moves
`canonical_built` -> `published`, but only after an authorized push, an
immutable version tag, a GitHub Release carrying the canonical PDF, and a
verified remote checksum. `scripts/validate_publication_hygiene.py` checks
the registry, the README catalog and that no PDF is tracked. This gate does
not use or activate any hook, and nothing here grants push or release
permission by itself.

## How to interpret `pass_with_warnings`

The chapter gate's deterministic layer intentionally keeps several
checks at "warning," not "failure," for already-accepted chapters with
documented pre-existing gaps (e.g. Chapters 1-2 lack a
`{#sec-chN-check}` cross-reference anchor; several Chapters 1-4
figures lack a dedicated semantic test beyond the generic bounds
check). `pass_with_warnings` means: every *required* check passed, and
every sequential audit stage found at most `optional` issues, but at least one
*already-known, previously-accepted* soft gap is still present. This
is not something to "fix" reflexively -- `docs/chapter-review-checklist.md`
explicitly says not to reopen an accepted chapter over a heuristic
warning. Treat `pass_with_warnings` as "technically ready, review the
specific warnings before accepting" -- not as "basically failing."

## When human review remains mandatory

**`scripts/chapter_gate.py` passing -- even a clean `"pass"` -- never
by itself means a chapter is accepted.** Three things stay strictly
human-gated, by design, with no automated substitute:

1. **`acceptance.visual_review` in the chapter contract.** No script
   in this workflow ever sets this field to `"pass"`. Only a human (or
   a fresh-context adversarial pass satisfying
   `docs/chapter-review-checklist.md` section 8, with a human
   reviewing its output) may.
2. **Moving `identity.status` to `"accepted_frozen"`** in both the
   chapter's own contract and `config/chapter-status-registry.yaml`.
   This is a hand-edit, in its own commit, after a human has reviewed
   the gate's output and the rendered PDF.
3. **Any correction to a chapter already marked `accepted_frozen`.**
   Always requires an explicit, task-scoped override (see above) --
   never inferred, never pre-authorized by a prior unrelated
   conversation.

## Recovery after a failed hook (once activated -- see below)

If `.claude/hooks/pre_action_guard.py` blocks an action you believe is
legitimate: check whether the path genuinely matches a `frozen_paths`
glob in `config/chapter-status-registry.yaml` or a chapter contract.
If it's a false positive (the guard's path-matching is a documented
heuristic, not a perfect parser -- see that script's own docstring),
report it; do not work around it by renaming the hook, disabling it in
`.claude/settings.json`, or asking an agent to "just this once" treat
the block as pre-authorized. If `.claude/hooks/final_stop_gate.py`
ever blocks completion and you want to stop anyway before its own
two-attempt bound is reached, remove
`.claude/.active-chapter-task.json` by hand -- that marker is exactly
what the hook checks for, and removing it is the documented, safe way
to abort an in-progress gated task.

## How to disable or re-enable hooks safely

**As of this infrastructure task, none of the three chapter-factory
hooks are active.** They live fully implemented and already tested
(via synthetic stdin, standalone -- never wired live) under
`.claude/hooks/*.py`, with the exact hook block to activate kept in
`.claude/hooks.staged.json` -- a file Claude Code does **not**
automatically read (it is deliberately not named `settings.json`).

**To activate:** merge the `"hooks"` key from `.claude/hooks.staged.json`
into `.claude/settings.json` (create that file if it doesn't exist).
Do this one hook at a time, in this order, each with its own
standalone test first:

1. **`pre_action_guard.py` (PreToolUse)** -- lowest risk; it only
   blocks `git push`, frozen-path edits, and canonical/release writes,
   all narrow and already covered by
   `tests/test_chapter_factory_workflow.py::TestPreActionGuardFrozenScope`
   and `TestPreActionGuardPushAndCanonicalOutput`. Test standalone
   first: `echo '{"tool_name":"Bash","tool_input":{"command":"git push"}}' | python3 .claude/hooks/pre_action_guard.py; echo $?`
   (expect exit 2).
2. **`post_edit_quick_checks.py` (PostToolUse)** -- never blocks (always
   exits 0), so the only risk is noisy/slow output, not a trapped
   session. Still worth a standalone smoke test first.
3. **`final_stop_gate.py` (Stop)** -- the only hook that can force
   Claude to keep going instead of finishing. **Do not activate this
   one without first re-reading its own docstring's two safety
   properties** (marker-gated; bounded-retry, fail-open) and running
   `tests/test_chapter_factory_workflow.py::TestFinalStopGateBoundedRetry`
   to confirm they hold in your current environment. If in doubt,
   activate only the first two hooks and leave this one staged.

**To disable:** remove the corresponding entry from `.claude/settings.json`'s
`"hooks"` key (or delete the whole key to disable all three at once).
A hook that is merely staged (not merged into `settings.json`) is
already fully inert -- Claude Code never reads `.claude/hooks.staged.json`
on its own.

**To test any hook script in isolation without wiring it live:**

```
echo '{"tool_name":"Bash","tool_input":{"command":"git push"}}' \
  | python3 .claude/hooks/pre_action_guard.py; echo "exit: $?"
```

Every hook script accepts a `CHAPTER_GATE_REPO_ROOT` environment
variable override, so you can also point a test at an isolated temp
fixture instead of this repo's real `config/chapter-status-registry.yaml`
-- see `tests/test_chapter_factory_workflow.py`'s `_write_fixture_registry`
helper for a worked example.

## Token/context tradeoffs of single-agent sequential audits

Running all four audit stages as one main agent, sequentially, instead
of as four parallel subagents, has a specific, known cost profile:

- **Lower peak process/context count, higher wall-clock time.** Four
  sequential stages in one context cannot overlap; a chapter review
  takes roughly the sum of the four stages' time rather than the max.
  This is the intended trade -- the whole point of removing parallel
  subagent orchestration was to reduce concurrent actors and process
  count, not to minimize latency.
- **One growing context instead of four isolated ones.** Each stage's
  findings accumulate in the same conversation rather than being
  computed in isolated subagent contexts and merged. This means later
  stages (figure audit, learner/PDF audit) have the earlier stages'
  findings available for cross-referencing "for free," but also means
  a very large chapter could push total context usage higher than four
  separately-scoped subagent calls would have. If a single review
  session's context grows uncomfortably large, prefer ending the
  review and resuming with a fresh context over trying to compress the
  audit stages.
- **No cost paid for orchestration/merge logic.** There is no
  cross-subagent message-passing, no "launch N, wait for all N, merge"
  bookkeeping, and no risk of one stage's failure silently dropping
  out of a parallel batch -- each stage either produces its JSON file
  or the chapter gate reports it as a skipped, failing check.

## Known limitations

- **The four audits are intentionally not executable subagents.** This
  is a design decision (see the prohibition at the top of this
  document), not a workaround for a technical limitation -- Claude
  Code subagents defined under `.claude/agents/*.md` are in fact
  invocable once registered. This workflow chooses not to use that
  mechanism for the audit stages, on purpose, to keep chapter review to
  one main agent with no parallel or nested execution.
- **`pre_action_guard.py`'s frozen-path matching is a documented
  heuristic** (glob matching against `chapter_path` and contract
  `frozen_paths`), not a byte-exact parser of every possible path a
  tool call could name. False negatives (an edit that should have
  been blocked but wasn't) are more likely than false positives, by
  design -- see that script's own docstring for the reasoning.
- **Three pre-existing Workbook 04 test failures remain** (see
  `scripts/chapter_review_checks.py`'s `KNOWN_BASELINE_FAILURES`):
  `test_index_subtitle_says_release_candidate_5`,
  `test_each_two_line_chapter_heading_renders_completely`,
  `test_chapter4_heading_renders_complete_title`. This infrastructure
  task did not touch Workbook 04 or its tests, per its own scope.
  **Recommendation:** repair or formally retire these three tests
  before Workbook 05's RC1, so the "known baseline" this workflow
  carries forward does not silently grow stale across two workbooks'
  lifetimes.
- **Token/context cost**: a full `scripts/chapter_gate.py` invocation
  runs the entire project test suite internally (via
  `workbook_qa.run_chapter_scoped_qa`), which is correct for a real
  acceptance decision but expensive to call repeatedly in a tight loop
  -- prefer calling it once per correction cycle (per the
  one-bounded-pass policy), not after every individual edit. The
  `post_edit_quick_checks.py` hook exists specifically to give cheap,
  per-edit feedback without paying the full-suite cost every time.
