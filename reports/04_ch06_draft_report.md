# Draft Report — Workbook 04, Chapter 6

Date: 2026-09-23
Scope: drafting, illustrating, rendering, and validating Chapter 6
("Reading Modern LLM Architectures: Three Designs, Three Sets of
Tradeoffs") of workbook 04, added to the existing Chapters 1-5 pilot.
Chapters 7-8 were not drafted, per instructions.

Final artifact: `outputs/04-llm-architecture-ch01-06-review.pdf`
(57 pages). Build command: `make review-ch01-06`
(`scripts/build_ch01_06_review.py`). Prior review PDFs (`-ch01-02`
through `-ch01-05`) were left untouched, not overwritten — frozen
historical checkpoints, per each superseded script's own notice.

## 0. Preflight

HEAD was `82540ca` ("Draft mixture-of-experts architecture chapter")
with a clean working tree, matching expectations. `outline.yaml`'s
existing ch6 entry ("Modern architecture case studies") matched this
task's expected role (a case-study chapter applying chapters 2-5's
mechanisms to real models) — not a silent scope replacement.

## 1. Case-study selection (Stage 2)

Selected exactly three model families, dropping Mixtral entirely as a
fourth main case study (it remains registered only as a ch. 5-adjacent
supporting reference, consistent with its pre-existing
source-coverage.yaml notes):

- **Llama 3 405B** ([@src-32], 2024-07-31) — dense decoder baseline.
- **DeepSeek-V3** ([@src-33], 2024-12-27, rev. 2025-02-18) — sparse
  MoE combined with compressed-KV attention (MLA), one model
  exemplifying both slots per Stage 2's "small, defensible set" goal.
- **Jamba** ([@src-35], 2024-03-28) — hybrid attention/recurrent
  (Mamba) architecture. The ORIGINAL Jamba paper was selected over the
  later "Jamba 1.5" report (arXiv:2408.12570, not verified this
  session), per the selection rule to prefer conceptual contrast over
  recency and this workbook's established preference for
  architecture-defining sources over their scaled-up successors.

## 2. Resolving the hybrid-mechanism source gap (Stage 3)

`reports/04_source_audit.md` had flagged (since Chapter 4) that Jamba
(`src-35`) is a model that *uses* Mamba layers, not Mamba's own
defining paper — a real gap for any claim about *how* the recurrent
state update works. Resolved by adding **`src-37`**: Gu and Dao,
"Mamba: Linear-Time Sequence Modeling with Selective State Spaces"
(arXiv:2312.00752), to `sources/registry.yaml`, `shared/bibliography.bib`,
`source-coverage.yaml` (new ch6 claim entry), and marking the gap
RESOLVED in `reports/04_source_audit.md`. Jamba's own reference [17]
was checked and confirms Jamba uses exactly this Mamba mechanism, not
Mamba-2 or Gated DeltaNet — those are not treated as synonyms anywhere
in the chapter.

## 3. Verification method (all three case studies + Mamba)

Every architecture fact in the chapter was verified by downloading the
primary source's PDF and extracting its full text with `pdftotext`,
then searching with `/usr/bin/grep -a` (the shell's aliased `grep`
function was independently confirmed unreliable on extracted text
files earlier in this project) — not by trusting a WebSearch snippet
or a WebFetch tool's own summary, per this workbook's established
standard (first applied to DeepSeek-V2/DeepSeekMoE in Chapters 4-5).

- **Llama 3 405B**: verified against the paper's Table 3 and Section
  3.2.1. The 405B config.json on Hugging Face is gated (HTTP 401) and
  was not used or worked around.
- **DeepSeek-V3**: verified against Section 4.2 ("Hyper-Parameters").
- **Jamba**: verified against the paper's full text plus the
  Jamba-v0.1 Hugging Face config.json (not gated).
- **Mamba**: verified against the paper's Section 3.2 (the selective
  SSM recurrence) and its fixed-state-vs-growing-cache framing.

## 4. Page budget (Stage 1/12) — two disclosed misses

| Section | Preferred | Hard max | Actual |
|---|---|---|---|
| Instructional | 4 pages | 5 pages | **5 pages** (hard max) |
| Answer key | 0.5 pages | 0.75 pages | **~0.67 pages** |
| Figures | 2 | 2 | 2 |
| Boxed misconceptions | 1 | 1 | 1 |
| Questions | 5-6 | 5-6 | 6 (4 check-your-understanding + 1 applied exercise + 1 interview lens) |

Both misses are disclosed, not silent scope creep — see
`outline.yaml`'s `ch6.drafting_note` and `page-budget.yaml`'s
`chapter_6`/`answer_key_chapter_6`/`chapter_6_specific` entries. Two
compression passes were applied before accepting the hard-max result:
merging two planned ledger tables into one (row-per-attribute, three
model columns), trimming the "Why this matters" paragraph and all
three case-study paragraphs by roughly 20%, tightening the
architecture-cards figure's internal spacing (SVG height 397→348
units), and compressing the answer key's design-exercise and
interview-practice answers (initial draft was ~0.87 pages). Further
compression toward the 4-page/0.5-page preferred targets was not
pursued once two figures, one merged table, three equal-space case
studies, and a hypothetical-config exercise were all confirmed to fit
within the hard maximums without sacrificing legibility.

Full-workbook projection updated: pilot actual is now 57 pages
(27,312 words), with `chapters_7_to_8_provisional` (renamed from
`chapters_6_to_8_provisional`) projecting a final total of 68-69.2
pages — within the 72-page hard ceiling, marginally over the 60-68
preferred range at the high end. Chapters 7-8 were **not** loosened to
compensate for Chapter 6's own miss.

## 5. Architecture-reading checklist (Stage 4)

A 10-question checklist (block structure, normalization, position
representation, sequence-mixing mechanism, head counts, dense-vs-MoE,
expert counts if MoE, what state grows with context, what is always
active, what training/serving complication follows) organizes the
chapter. No RMSNorm/RoPE/GQA/MLA/MoE mechanism is re-explained — each
case study cross-references the chapter (ch. 2-5) that already taught
it.

## 6. Architecture ledger (Stage 5/8)

One merged table (`@tbl-case-study-ledger`, row-per-attribute, three
model columns) rather than Stage 8's row/column split, since the
merged form fit compactly once cell text was abbreviated using
already-defined notation (`$H_q$`, `$H_{kv}$`, `$d_c$`, `$d_{\text{rope}}$`).
"Not applicable" is used for Llama 3's expert-count row rather than a
guessed number.

## 7. Figures (Stage 7)

Exactly two, both original SVGs built from `figures/source/_svg_helpers.py`:

- `fig-case-study-architecture-cards`: three schematic "architecture
  cards" in one visual grammar, each showing the sequence-mixing
  mechanism, FFN/MoE path (active-vs-total experts marked), and a
  cache-state icon (growing bars vs. a fixed box) — the one comparison
  the figure is built to make visible at a glance.
- `fig-case-study-tradeoff-map`: a qualitative tradeoff map with
  ordinal (not numeric) marker placement on two axes, plus marker
  shape (uniform vs. hybrid layer pattern) and color (communication
  complexity, three qualitative levels tied to documented expert
  counts, not a benchmark number).

Two rendering bugs were caught by visual inspection (not by any
automated test) and fixed: the tradeoff map's y-axis label text was
clipped at the canvas edge (fixed by widening the left margin and
shortening the label text), and the architecture-cards figure's third
legend entry overflowed the canvas's right edge (fixed by stacking the
legend vertically instead of horizontally).

## 8. Worked reading exercise (Stage 9)

Implemented as the chapter's "Applied exercise" (posed in-chapter,
answered only in the solutions file) rather than a mid-chapter worked
example, since Stage 9 explicitly asked for an exercise the *learner*
completes, not another instructor-solved calculation. Uses a 4th,
unnamed hypothetical config (32 query/8 KV heads, alternating
local/global attention, 64 routed experts top-2 plus 1 shared expert,
recurrent layers interleaved with attention) and asks for: GQA group
size, growing-vs-fixed state, active-vs-total expert distinction, a
likely communication concern, which chapters 2-5 mechanisms are
present, and at least one conclusion the config cannot support. Backed
by `data/worked-examples/hypothetical_architecture_reading.py`
(computes only the two genuinely numeric facts — GQA group size and
the routed-bank active fraction — per Stage 9's "do not turn into
another large numerical calculation").

## 9. Misconception and questions (Stage 10)

One boxed misconception: "A more sophisticated architecture is
necessarily a better model," corrected by distinguishing architecture
from data, training recipe, optimization, evaluation, and serving
implementation. Six total questions: 2 recall-style architecture-
reading checks, 1 comparison, 1 misconception check, 1 design exercise
(the hypothetical-config applied exercise), 1 interview-style question
(the suggested "predict memory/compute/communication bottlenecks
without overclaiming benchmark performance" prompt).

## 10. Fast-changing-information policy (Stage 11)

Every model is cited with its exact version and date; `source-coverage.yaml`
marks all four ch6 claims (three models plus Mamba) with a
`last_verified` date. "Latest," "newest," "leading," "state of the
art," and bare "best" are avoided as unqualified claims — the one
place "the best"/"the latest" appear in the chapter text, they are
inside a negated, hedged sentence explaining why the chapter avoids
that framing (see the "Why this matters" section). A reader-facing note
states that model families evolve but the checklist stays useful.

## 11. Validation (Stage 13)

Added `tests/test_ch06_worked_examples.py`: model-identifier and
pinned-date checks, active/total parameter consistency, GQA
group-size arithmetic for both Llama 3 and Jamba, expert-count
consistency for DeepSeek-V3 and Jamba, Mamba layer-ratio arithmetic,
citation resolution (including that `src-32`/`src-33`/`src-35`/`src-37`
are all cited, and that each model's source id appears near that
model's own paragraph, not just anywhere), figure/render pairing,
exactly-2-figures and exactly-1-table checks, question-count range,
and page-budget structure (including that the stale ch6-provisional
projection entry was removed, not left stale). Two pre-existing tests
in `tests/test_workbook04_blueprint.py` needed updating as a direct,
disclosed consequence of this chapter's content (not a bug): the
workbook-wide figure-count ceiling (18→19, since ch6's own task
mandated exactly 2 figures instead of the blueprint's original 1) and
`outline.yaml`'s `estimated_total_pages` (51→47, since ch6's estimate
dropped 8→4). `python -m unittest discover -s tests` passes all 167
tests; `git diff --check` reports no whitespace errors.

Searched the extracted PDF text for every banned internal string
(`figures/source`, `data/worked-examples`, `sources/registry.yaml`,
`/mnt/home`, `.qmd`, etc.) — the only two matches are inside the Build
and Version Note's own provenance disclosure (an intentionally
internal-facing section, not learner-facing chapter text), consistent
with every prior chapter. Manually re-scanned for every Stage 13
review phrase ("latest," "newest," "best," "leading," "state of the
art," "faster," "cheaper," "more efficient," "designed to,"
"equivalent," "same as") across the rendered chapter text; every
occurrence in Chapter 6's own content is hedged or negated (e.g. "Do
not infer... that Llama 3 is cheaper or simpler to train... —
architecture alone does not settle that").

## 12. Visual and technical review (Stage 14)

Rendered all 57 pages to PNG and inspected Chapter 6's own pages
(42-46), its answer key (53-54, spanning into the Build and Version
Note on 54), the table of contents (page 2, confirming the new
subsection list and page numbers), the bibliography (57, confirming
`src-37`'s entry `[19]` and all three model papers `[16]-[18]`), and
the chapter/answer-key pagebreak boundaries (46→47). Checked: figure
label legibility, consistent visual grammar across the three
architecture cards, table width (fits without wrapping past the
printed page), model/version visibility, active-vs-total expert
labels, cache-state labels, hybrid-layer representation (Jamba's
1-attention-layer-per-8 pattern), figure captions, question-writing
space, and citation resolution. Two visual bugs were found and fixed
(see Section 7); no leading-`=`/`+` table-cell misparsing (the bug
pattern discovered in Chapter 5) was found in Chapter 6's merged
ledger table.

## 13. Deferred / out of scope

Consistent with Stage 1's explicit exclusions: no survey of every
current model, no benchmark ranking, no vendor marketing tables, no
re-teaching of ch. 1-5 mechanisms, no release-history timeline, no
speculation about undocumented proprietary architectures, and no use
of "latest" as a durable technical category. DeepSeek-V3's specific
`d_c`/`d_{\text{rope}}` values were confirmed to match DeepSeek-V2's
own reported ratio (`d_c = 4 d_head = 512`, from Chapter 4's already-
verified sourcing), not re-derived from scratch.

## 14. Commit

See the commit this report accompanies for the final SHA. Working
tree was clean before this session's changes; nothing was pushed to
any remote.
