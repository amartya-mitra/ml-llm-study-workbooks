# Blueprint Report — Workbook 04 (Modern LLM Architecture)

Date: 2026-09-22
Baseline commit SHA (Stage 1, audited bootstrap): `559d9fd`
Scope: Stages 2-11 of the workbook-04 blueprint task. No workbook
chapter was drafted; this is design/planning output only, per
instructions.

## Sources reviewed

- **7 previously-registered sources actually fetched and verified for
  the first time this session**: src-10 (How To Scale Your Model),
  src-11 (Inference Engineering), src-12 (LLM Inference Handbook),
  src-14 (The Big LLM Architecture Comparison), src-15 (LLM Architecture
  Gallery) — all fully accessible; src-16 (Smol Training Playbook) and
  src-17 (Ultra-Scale Playbook) — both partially accessible only (HTML
  shell/metadata; the actual article body is client-side-rendered and
  was not retrievable via WebFetch or raw `curl` this session).
- **17 new primary/official sources found, verified, and registered**:
  src-19 through src-35 (the original Transformer paper, MQA, GQA,
  RoPE, RMSNorm, SwiGLU, Mistral's sliding-window attention, Sparse
  Transformers, DeepSeek-V2's MLA, the original sparsely-gated MoE
  paper, GShard, Switch Transformer, DeepSpeed-MoE, and four
  representative model reports: Llama 3, DeepSeek-V3, Mixtral, Jamba).
- Full detail, per-source access method, and every honesty flag (which
  secondary sources were only confirmed to exist vs. actually read) is
  in `reports/04_source_audit.md`.

## New primary sources added

17 (src-19 through src-35). See the table in `reports/04_source_audit.md`
and each entry's full detail in `sources/registry.yaml`.

## Inaccessible sources

src-16 and src-17 (both HuggingFace Spaces, client-side-rendered apps —
body content not retrievable by either WebFetch or raw `curl` this
session). src-15's direct `curl` was blocked (HTTP 406/mod_security)
while WebFetch succeeded — both outcomes recorded rather than treating
the `curl` failure as authoritative. Full detail in
`reports/04_source_audit.md`.

## Refined chapter list

The provisional 9-chapter outline is now **8 chapters**. Full rationale
in `workbooks/04-llm-architecture/outline.md`; summary of what changed:

1. MLA was listed in two places in the provisional outline (once under
   "reducing attention cost," once under "KV cache as an architectural
   constraint") — merged into one chapter.
2. The provisional "reducing attention cost" chapter mixed three
   genuinely different axes (head-sharing, connectivity-pattern
   restriction, and architecture-family replacement) — split so the
   head-sharing axis (MHA -> MQA -> GQA -> MLA) gets its own chapter
   with the KV-cache-size formula built up once, where it's motivated.
3. The remainder of "KV cache as an architectural constraint" (the
   architecture-vs-runtime distinction) was folded into the
   architecture-to-systems chapter as its opening section, rather than
   kept as a standalone chapter that would mostly be a coda.

Final list: (1) Transformer refresher, (2) Anatomy of a modern decoder,
(3) Attention head structure and cache-efficient variants, (4)
Restricting attention's reach, (5) Mixture-of-experts models, (6) Modern
architecture case studies, (7) From architecture to systems
consequences, (8) Synthesis and practice.

## Estimated page count

**56 pages** (ceiling: 65), verified programmatically to match the
per-chapter sum (`tests/test_workbook04_blueprint.py::test_outline_page_budget_within_ceiling`).

## Source-coverage gaps

Two genuine, honestly-flagged gaps (see `source-coverage.yaml` and
`reports/04_source_audit.md` for full detail):

1. **No primary source for the linear/recurrent (SSM-style) attention
   mechanism itself** — only for a model (Jamba) that uses it. Given
   ch. 4's deliberate intuition-level scope fence, this may not block
   drafting, but any claim about *how* the mechanism works needs a
   source added first.
2. **Tied vs. untied embeddings has no primary source of its own** — a
   widespread convention, not the subject of one canonical paper.

Two secondary-source gaps (RMSNorm and MoE-routing-origin each have no
independently-verified explanatory secondary source) and one
partial-access caveat (src-16/src-17's role for workbook 04 is
provisional pending a render-capable fetch) are also tracked.

## Proposed figures

**18 figures** planned (Stage 7 target: 12-18), one per major mechanism,
none crowding more than one relationship into a single diagram. Two
figures explicitly reuse/extend the project's own existing
`figures/source/kv_cache_demo.py` bootstrap figure rather than
introducing a new third-party-inspired redraw. Every other figure is
marked for an original redraw with an explicit attribution requirement
(citing the source for the *fact*, never for the *figure*). Full detail
in `workbooks/04-llm-architecture/figure-plan.yaml` and
`reports/04_figure_plan.md`.

## Proposed worked examples

**10 worked examples** (Stage 8 named 7 explicitly; 3 more added to
cover ch. 6, ch. 7, and ch. 8, which the named 7 didn't reach). Several
examples deliberately chain from a prior example's exact config
(`chains_from` field) so the reader sees one number change when one
architectural choice changes, holding everything else fixed. Full
detail in `workbooks/04-llm-architecture/example-plan.yaml`.

## Question inventory

- **24 quick questions** (target: 2-4 per chapter; ch. 8 deliberately
  has zero, since it is itself the cumulative/interview capstone).
- **13 misconception checks** (one per major concept, cross-referenced
  from `outline.yaml`'s per-chapter `misconception_checks` fields).
- **8 applied exercises** (one per chapter).
- **12 cumulative review questions** (target: 10-15), each explicitly
  spanning 2-3 chapters to force combining material, never testing a
  single chapter in isolation.
- **8 interview-style questions** (target: 6-10), each phrased the way
  a real interviewer would ask it.

Full detail, including `skill_tested`/`expected_reasoning`/
`likely_misconception`/`source_ids`/`difficulty` per item, in
`workbooks/04-llm-architecture/question-plan.yaml`.

## Fast-changing sections

Every ch. 6 case-study claim (Llama 3, DeepSeek-V3, Jamba, Mixtral's
specific reported numbers) is marked `fast_changing` in
`source-coverage.yaml`. src-14 (the workbook's core narrative source) is
itself an actively-updated source (last updated 2026-04-02 per its own
page) — treat anything drawn from it as current as of that date, not
timeless. RoPE's base mechanism (ch. 2) is stable, but any long-context
extrapolation trick built on top of it (base/theta rescaling, YaRN, etc.)
would be a separate, more time-sensitive topic if ever added.

## Copyright or licensing cautions

No source in this workbook's registry grants figure-reuse rights.
src-14 and src-15 explicitly say not to reproduce their comparison
diagrams/gallery images. Every one of the 18 planned figures is an
original redraw (or extends this project's own prior original figure);
none cite a source for visual design, only for the underlying fact. Do
not conflate a paper's own arXiv license with a model's separate weights
license (flagged specifically for src-32/Llama 3, whose weights carry
Meta's Llama Community License, distinct from the paper's own terms).

## Recommended drafting order

Per conceptual dependency, not chapter number (full reasoning in
`outline.md`): **ch. 1 -> ch. 2 -> ch. 3 -> {ch. 5 in parallel with ch. 4} -> ch. 6 -> ch. 7 -> ch. 8**.
Chapter 3 is the single most load-bearing chapter (ch. 4, 6, and 7 all
reference its KV-cache formula rather than re-deriving it) and should be
drafted as early as the prerequisite chapters 1-2 allow. Chapter 5 (MoE)
is architecturally independent of the attention-mechanism chapters and
can be drafted in parallel with chapter 4 once chapters 1-2 exist.
Chapter 8 must be drafted last, since it is explicitly a worksheet over
the preceding seven chapters.

## Unresolved decisions

1. **Jamba vs. Jamba 1.5** (ch. 4/ch. 6): a newer, larger report exists
   (arXiv:2408.12570) and was not verified this session. Whoever drafts
   these chapters must decide to use the original architecture-defining
   paper (src-35, as currently registered) or re-verify and switch to
   1.5 — not silently substitute either way.
2. **GShard vs. DeepSpeed-MoE as the primary expert-parallelism source**
   (ch. 5/ch. 7): both are registered (src-29, src-31) with different
   framings (compiler/sharding abstraction vs. end-to-end training+
   inference system); pick based on which framing the chapter actually
   needs.
3. **Whether to add a Mamba/SSM primary source** before ch. 4 makes any
   claim about how the recurrent-state update works, specifically (see
   "Source-coverage gaps" above) — currently no such claim is planned,
   consistent with the chapter's intuition-level scope fence, but this
   should be revisited if drafting pulls the chapter deeper than
   currently planned.
4. **Whether `src-16`/`src-17`'s workbook-04 role should be finalized or
   re-verified** — both are currently provisional because their body
   content could not be fetched this session (client-side-rendered
   apps). A render-capable fetch, or reading the underlying Space's
   markdown source files directly, would resolve this.
5. **Whether Makefile/render tooling should auto-activate the
   `ml-workbooks` conda environment** — carried over from
   `reports/bootstrap_report.md`'s own unresolved item; still open, not
   revisited in this blueprint task since it's outside this task's scope
   (no rendering was needed for planning-only YAML/Markdown artifacts).

## Tests

`python3 -m unittest discover -s tests` — **30/30 passed** (up from 20
at the start of this task): 5 new tests in
`tests/test_workbook04_blueprint.py` formalize the Stage 10 review gates
(chapter count, page budget, figure count, question-count targets, that
every source id referenced across every blueprint YAML file resolves to
a real registry entry, and that the disputed MoE load-balancing claim
cites more than one disagreeing source rather than being silently
flattened). `python3 scripts/validate_registry.py` and
`python3 scripts/validate_questions.py` both pass.
