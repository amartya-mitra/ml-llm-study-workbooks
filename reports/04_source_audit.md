# Source Audit — Workbook 04 (Modern LLM Architecture)

Date: 2026-09-22
Scope: Stage 4-6 of the workbook-04 blueprint task — source discovery,
verification of the 7 previously-registered core sources, and the
claim-level coverage matrix.

Structured data: `sources/registry.yaml` (src-19 through src-35 added
this pass; src-10/11/12/14/15/16/17 updated), `sources/coverage-matrix.yaml`
(workbook-04 section rewritten with per-chapter mapping and Stage 5's
`role` classification), `workbooks/04-llm-architecture/source-coverage.yaml`
(28 claim-level entries). This report is the narrative summary; the YAML
files are authoritative for anything the two disagree on.

## Sources reviewed and added

**17 new primary/official sources added** (src-19 through src-35),
found via a dedicated research pass covering every topic Stage 4 named
explicitly: the Transformer paper, MQA, GQA, RoPE, RMSNorm, SwiGLU,
sliding-window attention (Mistral 7B), sparse attention, MLA
(DeepSeek-V2), MoE routing (Shazeer 2017), GShard, Switch Transformer,
DeepSpeed-MoE, and one representative model each for dense (Llama 3),
MoE (DeepSeek-V3), a simpler MoE contrast (Mixtral), and hybrid (Jamba).
Every one of these 17 was verified this session via WebSearch and, for
several (DeepSeek-V2, GShard, Switch Transformer, Shazeer 2017), via
WebFetch of the full arXiv/ar5iv text to confirm the exact equation or
claim needed — see each entry's `access_status` field for exactly which
method was used per source.

**7 previously-registered sources verified for the first time**
(src-10, 11, 12, 14, 15, 16, 17) — all had sat with
`last_verified: null` since the project's bootstrap. All 7 were actually
fetched this session (not just searched). Outcomes:

| Source | Title | Fetch result | Workbook-04 role |
|---|---|---|---|
| src-10 | How To Scale Your Model | full success | core narrative source (KV-cache/systems math) |
| src-11 | Inference Engineering | full success | systems companion |
| src-12 | LLM Inference Handbook | full success | systems companion |
| src-14 | The Big LLM Architecture Comparison | full success | core narrative source |
| src-15 | LLM Architecture Gallery | success via WebFetch; direct `curl` blocked (406/mod_security) — discrepancy preserved, not smoothed over | visual/reference source |
| src-16 | The Smol Training Playbook | **partial** — HTML shell + meta only, body is client-rendered JS and was not retrievable | excluded (out of scope for wb 04; also a workbook-05 source) |
| src-17 | The Ultra-Scale Playbook | **partial** — same client-rendering limitation as src-16 | systems companion (provisional on the meta description alone) |

## New primary sources added, by topic

See `sources/registry.yaml` src-19..src-35 for full entries. Summary:
Transformer (src-19), MQA (src-20), GQA (src-21), RoPE (src-22),
RMSNorm (src-23), SwiGLU (src-24), sliding-window/Mistral (src-25),
sparse attention (src-26), MLA/DeepSeek-V2 (src-27), MoE routing origin
(src-28), GShard (src-29), Switch Transformer (src-30), DeepSpeed-MoE
(src-31), Llama 3 (src-32), DeepSeek-V3 (src-33), Mixtral (src-34),
Jamba (src-35).

## Inaccessible sources

- **src-16 and src-17** (both HuggingFace Spaces) are client-side-rendered
  apps. Neither WebFetch nor a raw `curl` could retrieve the actual
  article body this session — only the HTML shell and
  `<meta>`/JSON-LD tags. Per AGENTS.md's "do not infer detailed contents
  from a snippet" rule, neither source's specific topic-coverage claims
  are treated as verified; src-16 was excluded from workbook 04 entirely
  (it's really a workbook-05 source anyway), and src-17's `systems_companion`
  role for workbook 04 is explicitly marked provisional pending a
  render-capable fetch or a direct read of the Space's underlying
  markdown source files.
- **src-15**'s direct `curl` fetch was blocked with HTTP 406
  (mod_security), while the WebFetch tool succeeded. Both outcomes are
  recorded rather than treating the `curl` failure as authoritative —
  see the entry's `access_status` field.
- Several **secondary/explanatory** sources surfaced during research
  (the EleutherAI RoPE blog post, Raschka's dedicated GQA gallery page,
  a Jamba architecture explainer on Medium, and others named in the
  research agents' own findings) were only confirmed to **exist** via a
  search result, not fetched for content accuracy. None of these were
  added to the registry as citable sources — they are listed for
  awareness only, in case a future drafting pass wants to fetch and add
  them properly.

## Refined chapter list

See `workbooks/04-llm-architecture/outline.md` for the full rationale.
Summary: the provisional 9-chapter outline is now 8 chapters. The
"reducing attention cost" chapter's MLA content was merged into a new
"attention head structure and cache-efficient variants" chapter
(MHA -> MQA -> GQA -> MLA as one progression, with the KV-cache formula
built up once, in the place that motivates it), and the old "KV cache as
an architectural constraint" chapter's remaining job (architecture vs.
runtime, quantization/paging framing) was folded into the
architecture-to-systems chapter rather than kept as a standalone chapter
that would mostly be a coda to the attention-variants chapter.

## Estimated page count

**56 pages** (ceiling: 65). Per-chapter breakdown in
`workbooks/04-llm-architecture/outline.yaml`; sum verified
programmatically to match the stated total.

## Source-coverage gaps (see source-coverage.yaml for the full claim-level detail)

- **RESOLVED (2026-09-23), no primary source for the linear/recurrent
  (SSM-style) attention mechanism itself.** The research pass verified
  sources for MQA, GQA, MLA, sliding-window, and sparse attention, but
  not for Mamba/SSM specifically — Jamba (src-35) is registered as a
  model that *uses* Mamba layers, not Mamba's own defining paper. Per
  ch. 4's deliberate scope fence (intuition-level treatment, not a
  from-scratch SSM derivation), this did not need closing before ch. 4
  was drafted — but ch. 6's hybrid case study needed a source for *how*
  the recurrent state update works before it could responsibly discuss
  Jamba's Mamba layers. Closed by adding src-37 (Gu & Dao, "Mamba:
  Linear-Time Sequence Modeling with Selective State Spaces,"
  arXiv:2312.00752), verified via full-text fetch and pdftotext
  extraction (not a snippet), and confirmed via Jamba's own reference
  [17] that Jamba uses exactly this mechanism, not Mamba-2 or Gated
  DeltaNet. See sources/registry.yaml src-37 and source-coverage.yaml's
  new ch6 "Mamba selective state-space mechanism" entry. Ch. 6 still
  cites only enough of the mechanism to interpret Jamba's architecture,
  not a full derivation — that remains out of scope per outline.md's
  non-goals (see below).
- **Tied vs. untied embeddings** has no primary source of its own — it's
  a widespread convention rather than the subject of one canonical
  paper. A specific model's config/report that states its tying choice
  and reasoning would close this before ch. 2 is drafted.
- **RMSNorm** and **MoE routing origin (Shazeer 2017)** each have no
  independently-verified secondary/explanatory source — only the
  primary paper. Not a blocker, but worth a secondary-source pass before
  those sections are finalized if a more accessible explainer is wanted
  alongside the primary paper.
- **Pre-norm vs. sandwich-norm**: the general training-stability
  tradeoff is well supported, but the specific "which real model uses
  sandwich-norm and why" claim currently leans on src-14 (a secondary,
  actively-updated source) rather than a model's own technical report.
  Marked `partially_supported`, not `supported`.

## Topics with strong primary coverage

Every attention-family mechanism (MHA/MQA/GQA/MLA), every ch. 2
mechanism (RoPE/RMSNorm/SwiGLU), sparse/sliding-window attention, MoE
routing/load-balancing/expert-parallelism (multiple sources per topic,
capturing real disagreement rather than one flattened claim), and all
four ch. 6 case-study models now have a primary/official source
verified this session, not carried over from background knowledge.

## Topics where sources disagree (preserved, not flattened)

**The MoE load-balancing loss has four non-equivalent formulations**
across the sources registered for this workbook: Shazeer 2017's
coefficient-of-variation-based importance/load losses (src-28), GShard's
`aux_loss = (1/E) * sum_e (c_e/S) * m_e` (src-29), Switch Transformer's
restated `alpha * N * sum_i f_i * P_i` (src-30, the form most open MoE
codebases actually implement), and DeepSeek-V3's explicitly
auxiliary-loss-free strategy (src-33) — a genuine departure from all
three prior approaches, not a refinement of one of them. `source-coverage.yaml`
marks this claim `disputed` and explicitly instructs ch. 5's drafter not
to flatten it into a single "the loss is..." statement.

## Fast-changing / model-specific facts (dated explicitly per AGENTS.md)

Every ch. 6 case-study claim (Llama 3's 405B/128K, DeepSeek-V3's
671B/37B/14.8T-tokens, Jamba's 12B/52B/256K, Mixtral's 46.7B/12.9B) is
marked `fast_changing` in `source-coverage.yaml` specifically because
these are one model's reported numbers at one point in time, not a
general law. Ch. 6 prose must name the model and the report's date
whenever citing one of these, per AGENTS.md's time-sensitivity rule. In
addition, src-14 (the Raschka comparison, workbook 04's core narrative
source) is itself an actively-updated source — last updated 2026-04-02
per its own page — so any claim drawn from it about a specific model
should be treated as current as of that date, not timeless.

## Copyright/licensing cautions

None of the newly-added arXiv papers carry an open-reuse license for
their figures — cite/restate the definitions and equations, never copy
a figure. src-14's comparison diagrams and src-15's gallery images are
explicitly marked "do not reproduce" in their registry entries (the
project's original figures must be redrawn using `config/visual-style.yaml`'s
palette, per AGENTS.md). src-32's paper is arXiv-licensed, but the
underlying Llama 3 model weights carry Meta's own Llama Community
License — the two are not the same thing and should not be conflated
when the workbook discusses "using" vs. "citing" this model.

## Proposed claims that were removed before they were ever added

Two claims were deliberately kept out of `source-coverage.yaml` rather
than added and then hedged: a full from-scratch derivation of Mamba/SSM
recurrence equations (out of scope per outline.md's non-goals), and any
ranked "best" attention variant or MoE routing scheme (no source
consulted actually supports a strict ranking — every one presents these
as tradeoffs against different constraints). See `source-coverage.yaml`'s
`removed_or_descoped_claims` section.

## Series-wide roadmap source registration (2026-09-25)

Twelve sources (`src-38` through `src-49`) were added this session to
support `config/series-topic-roadmap.yaml`'s three cross-workbook
topics (recurrent depth/looped transformers, multi-token prediction,
speculative decoding) — see `reports/series_topic_roadmap.md` for the
full assignment rationale. None of these sources back any claim drafted
this session beyond Chapter 7's single-paragraph, deliberately shallow
looped-depth preview row; the workbooks that will actually teach these
topics in depth (04 ch. 8, 05, 06) have not been drafted.

- **Looped/recurrent depth** (`src-38` Universal Transformers, `src-39`
  Geiping et al.'s recurrent-depth paper, `src-40` Mixture-of-Recursions,
  `src-41` Ouro/looped language models, `src-42` Nanbeige4.2-3B): all
  five verified via full-text PDF download and `pdftotext` extraction,
  not a search snippet or a WebFetch tool's own summary — matching this
  project's established rigor. Each covers a distinct required concept
  from the task's list (Universal Transformers: adaptive per-position
  halting, 2018; Mixture-of-Recursions: per-token recursion routing AND
  the KV-cache-implications concept specifically, via its own
  "recursion-wise caching vs. recursive sharing" comparison; Nanbeige:
  a FIXED loop count in a shipped model, distinct from MoR's adaptive
  depth; Geiping et al.: the compute-vs-parameter-storage tradeoff
  framing). These five are not treated as interchangeable — the
  registry notes for each state explicitly which required concept it is
  the primary source for.
- **Multi-token prediction** (`src-43` Gloeckle et al.): verified the
  same way. Its independent-output-heads design is explicitly flagged
  in the registry as materially different from DeepSeek-V3's (`src-33`)
  sequential/causal-chain design — both are real MTP variants, neither
  is treated as "the" canonical one.
- **Speculative decoding** (`src-44` Leviathan et al., `src-45` Chen et
  al.): both foundational papers verified via full-text extraction,
  registered as co-foundational (published within ~2 months of each
  other in early 2023), not one derivative of the other. Per the task's
  own scope fence, no speculative-decoding *mechanism* content was
  drafted anywhere this session — these sources are registered for
  Workbook 06's future use only.
- **Expert-explanatory/visual-reference sources** (`src-46`/`src-47`
  Raschka's looped-transformer blog/newsletter pieces, `src-48`/`src-49`
  his architecture-gallery sub-pages on looped depth and MTP): all four
  verified via WebFetch of the live page (title, date, author, and the
  specific distinctions/paper-names each one makes), and explicitly
  registered as `secondary_summary`/`visual_reference` — not a
  substitute for the primary papers above. `src-47` also names three
  additional papers ("Beyond Parameters...", "SMELT...", "Full-bandwidth
  transformer") that were **not** independently verified this session;
  the registry entry says so explicitly rather than silently omitting
  them or presenting them as checked.

**GPT-6 Astra caution (explicit, per this session's task instructions):**
no official OpenAI technical source for "GPT-6 Astra" was found or
sought this session. `src-46`/`src-47` themselves present the
looped-transformer claim about Astra as third-party-reported speculation,
not OpenAI's own confirmed disclosure. Any future workbook text that
mentions Astra must preserve this hedge — it must not be upgraded to a
verified architectural fact.
