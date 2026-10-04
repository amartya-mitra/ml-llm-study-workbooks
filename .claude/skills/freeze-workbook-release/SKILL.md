---
name: freeze-workbook-release
description: Prepares the future release-candidate / publication-freeze workflow for a fully integrated workbook. NOT run by the infrastructure task that created this file -- it is a scaffold for a later task to execute explicitly. Has significant, hard-to-reverse side effects (would create a release-candidate artifact and may push). Only invoke this explicitly, and only after integrate-workbook has produced an accepted canonical build -- never automatically.
allowed-tools: Read, Grep, Glob, Bash
disable-model-invocation: true
---

# Freeze a workbook release (scaffold -- not yet executable end to end)

**Status: prepared, not run.** Authored as part of the "chapter
factory" infrastructure task
(see `docs/chapter-factory-operator-guide.md`) to be ready to invoke
later, once `integrate-workbook` has produced an accepted canonical
build for the target workbook. This infrastructure task did not
execute this skill, created no release candidate, and pushed nothing.

Do not invoke this until:

1. `integrate-workbook` has run and a human has accepted the resulting
   canonical PDF.
2. A human has explicitly asked for a release candidate / publication
   freeze, by name.

This is the highest-stakes skill in the chapter-factory workflow --
`scope.release_output_allowed` is `false` in every chapter contract on
purpose, and `scope.push_allowed` is `false` by default everywhere
else in this workflow. A release freeze is exactly the one place that
default may need to flip, and only on explicit human instruction for
that specific push.

## Intended steps (for the task that eventually runs this)

1. **Repository-state gate**: confirm the canonical build from
   `integrate-workbook` is the one being frozen (matching commit SHA),
   confirm every chapter contract's `acceptance.visual_review` is
   `"pass"` (a human actually looked at every page -- never inferred),
   confirm working tree clean.
2. **Preserve the prior validated PDF before replacing it** -- per
   `AGENTS.md`: "Never overwrite an existing validated PDF without
   preserving it (copy the prior version aside, e.g. with a date or
   hash suffix, before replacing `outputs/*.pdf`)."
3. **Produce the release candidate** under `outputs/_releases/<id>/`,
   following Workbook 04's own RC1-RC7 numbering convention as
   precedent (see `scripts/build_release_candidate_v*.py` for the
   established pattern this workbook's own RC script should follow --
   write a new `build_release_candidate_v1.py` for the target
   workbook rather than reusing Workbook 04's numbered scripts
   directly, since those are that workbook's own frozen artifacts).
4. **Full validation**: the complete test suite, both validators,
   `git diff --check`, and a full adversarial visual pass over the RC
   PDF -- the same rigor as a chapter-level review, at whole-book
   scope.
5. **Commit locally.**
6. **Push only if the task explicitly authorizes it for this specific
   release** -- never by default, and never inferred from "the RC
   looks ready."
7. **Stop for human sign-off.**

This skill intentionally stops here. Flesh out the steps above into
real, tested orchestration only when a task actually asks for a
release freeze to run, and treat every step involving `push` or
`outputs/_releases/` with the scrutiny `AGENTS.md`'s build-and-
validation-discipline rules and this repo's broader "confirm before
any hard-to-reverse action" norms require.
