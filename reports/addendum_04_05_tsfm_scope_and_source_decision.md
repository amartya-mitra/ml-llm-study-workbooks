# Addendum 04–05 (TSFM) — Scope and Source Decision Report

Date: 2026-10-06
Baseline commit: `c79f3f6` (branch `main`, equal to `origin/main` at start of work)
Scope: Step 2 only — define and source the standalone TSFM addendum.
**No addendum directory, chapter file, index, figure, worked example, question,
solution, claim-ledger entry, PDF or release candidate was created.** This
report is an approval-gate artifact; drafting requires explicit sign-off.

**Status: audited (four read-only auditors, 2026-10-06); corrections
applied; awaiting scope approval.** Every auditor finding and its
disposition is recorded in §24. Nothing here authorizes Step 3.

Conventions used in this report:

- **Source types** are always labeled: *paper* (arXiv/venue paper or report),
  *README* (official repository README), *model card*, *vendor blog*.
  Only papers carry mechanism-level claims in this plan; the other three
  are "documentation-only" and are used only for what they state.
- **"As of"** qualifiers: every post-2025 source and every release-specific
  fact is time-sensitive (AGENTS.md). All web sources were last verified
  on **2026-10-06**.
- Workbook references are **conceptual** ("Workbook 04, Chapter 1, tokens
  and embeddings"), never page numbers.

---

## 1. Executive recommendation

Build the addendum as **six compact modules, about 22 pages (ceiling 24)**:
five substantive modules plus a short synthesis module. The addendum is a
standalone companion; it restates what it needs from Workbooks 04 and 05 in
a quarter-to-half-page **Quick recap from the LLM workbooks** that opens
every module, so a reader who never opened those workbooks can follow.

Source position, in one paragraph: **nine papers were obtained as full
text and read in part, with the read depth recorded per entry (§10) and
the unread parts listed in §12, and are registered
(`src-56`–`src-64`)**: Chronos, Chronos-2, TimesFM (original), TiRex,
TiRex-2, Moirai (original), Moirai 2.0, Lag-Llama, PatchTST. **Four
documentation-only sources are registered (`src-65`–`src-68`)**: the
TimesFM README, the TimesFM 3.0 model card, the TimesFM-3 vendor blog,
and the Chronos repository README (the only source found for
Chronos-Bolt). **No paper was found for TimesFM 2.0/2.5/3.0 or
Chronos-Bolt**; the plan therefore never makes a mechanism claim about
those releases beyond what their documentation states, and labels each
such statement as vendor documentation.

What I recommend *against*: a standalone representation-depth /
layer-diagnostics module. No source read here supports one, and the plan
should not invent it (§7, Module 3 note; §12 gap G6).

Decisions requested of you at the end of this report are listed in §23.

## 2. Proposed title

**Addendum 04–05: From Language Models to Time-Series Foundation Models**

Subtitle (provisional): *Tokens, patches, channels, horizons, and
forecast distributions — what carries over from the LLM workbooks and what
does not.*

## 3. Proposed repository location

`workbooks/addendum-04-05-tsfm/` (id `addendum-04-05-tsfm`), mirroring the
Workbook 05 layout (`chapters/`, `solutions/`, `includes/`, `data/`,
`figures/{source,rendered}/`, `figure-plan.yaml`, `questions.yaml`,
`claim-ledger.yaml`, `chapter-contracts/`).

Why under `workbooks/`: `scripts/build_workbooks.py` renders every `.qmd`
under that tree, and the chapter factory expects the same layout. Why not
`reports/`: it is a reader-facing artifact, not a report.

**Registration caveat discovered during this step (affects Step 3):**
`config/project.yaml` lists exactly eight workbook ids and
`tests/test_project_structure.py::test_project_yaml_lists_all_eight_workbooks`
pins that list. `sources/registry.yaml` entries and
`sources/coverage-matrix.yaml` entries may only reference ids in
`project.yaml`. Adding the addendum id therefore requires editing a
pinned test. I did **not** do that in Step 2 (out of scope; it is a
scaffolding action). See §11 for how the new sources were registered
without it, and §23 for the request.

## 4. Canonical and development artifact names

Following the Workbook 05 precedent (short slug, no title embedded):

| Artifact | Path |
|---|---|
| Canonical final PDF | `outputs/addendum-04-05-tsfm.pdf` |
| Release candidates | `outputs/_releases/addendum-04-05-tsfm/addendum-04-05-tsfm-rc1.pdf` (then `-rc2`, …) |
| Development builds / page images | `outputs/_development/addendum-04-05-tsfm/…` |
| Per-module review PDFs | `workbooks/addendum-04-05-tsfm/mNN-review.pdf` (Workbook 05 `chNN-review.pdf` pattern) |

Per AGENTS.md, any replacement of an existing validated PDF must first
copy the prior version aside with a date or hash suffix. Workbook 04's
canonical name carries the full title and Workbook 05's does not; the
addendum follows Workbook 05 (the more recent convention). That
one-time inconsistency was already accepted in
`reports/05_llm_training_scope_and_source_decision.md` §5.

## 5. Relationship to frozen Workbooks 04 and 05

- **Standalone companion.** Neither frozen workbook is modified,
  rebuilt, retitled or republished. Verified at the start of this step:
  Workbook 04 is registered `frozen` with last-touched commit `a78a15e`
  (matches `git log -1 -- workbooks/04-llm-architecture`); Workbook 05 is
  `accepted_frozen`, all six chapter SHAs match
  `config/chapter-status-registry.yaml`, and
  `outputs/05-llm-training-workbook.pdf` exists
  (sha256 `25a393bb…2a0c`).
- **No cross-document references.** Quarto cannot resolve `@sec-`/`@eq-`
  labels across separate documents, and page references would be
  fragile. Every cross-reference is conceptual (workbook, chapter title,
  concept name) and every module restates what it needs.
- **Shared infrastructure only:** `shared/bibliography.bib`, the schemas
  in `shared/`, the figure template, `config/visual-style.yaml`.
- **Notation is inherited, not redefined.** The frozen workbooks reserve
  symbols the TSFM literature also uses; the addendum must pick
  non-colliding ones (table in §9).
- **Boundary rule with Workbook 05 Chapter 2:** the addendum may say a
  TSFM "predicts several future patches from one output token" and
  point at the idea of multi-token prediction; it must not re-teach
  independent-heads versus causal-chain MTP.

## 6. Recommended module count and page budget

Six modules, ~22 pages, ceiling 24 (for scale: Workbook 04's canonical
PDF is 70 pages and Workbook 05's is 64 pages as recorded at the start of
this step; I did not re-run `pdfinfo` during the audit; this is a
deliberately small companion).

**Accounting rule (all-in).** Each module row below includes its prose,
its quick recap, its figure, its worked example, **and its ~6 questions**
(the half-page "what transfers from LLM training systems" callout sits in
Module 5). Answer keys (compact, ~34 answers) and the references list are
separate back-matter rows and **count toward the 22/24 pages**. Step 3
must confirm that keys can be rendered compactly in-PDF (Workbook 05 keeps
them in separate `solutions/*.qmd` files; the page cost of that was not
measured here).

| # | Module | Pages |
|---|---|---|
| 0 | Front matter (title, how to use, source-type legend, notation table) | 1.0 |
| 1 | Turning a time series into model inputs: scaling, tokens, patches | 3.5 |
| 2 | What the model sees and predicts: context, channels, covariates, horizons | 3.5 |
| 3 | Architecture families and how a forecast is produced | 4.0 |
| 4 | Outputs, objectives and probabilistic forecasts | 3.5 |
| 5 | Pretraining data, adaptation, evaluation and leakage (incl. callout) | 3.0 |
| 6 | Reading a TSFM release: synthesis and practice | 2.0 |
| 7 | Answer keys (back matter) | 1.0 |
| 8 | References (13 registered sources) | 0.5 |
| | **Total** | **22.0 (target 22, ceiling 24; 2.0 pages of slack)** |

These figures are planning estimates, not measurements. If a module
overruns, the cut order is: Module 6 practice material (0.5), Module 5
adaptation subsection (0.5; thin on verified sources anyway, §12 G4), F6
reduced to a table (0.5). Do not cut the quick recaps.

## 7. Module-by-module scope and boundaries

Each block lists: purpose; LLM quick recap (detail in §9); new TSFM
concepts; primary sources; worked-example candidate; figure candidate;
page budget; explicit exclusions; dependency.

### Module 1 — Turning a time series into model inputs (3.5 pp)

- **Purpose:** show the three verified ways a real-valued series becomes
  model input, and why scaling comes first.
- **Quick recap:** tokens and embeddings, the residual MLP / feed-forward
  sublayer (WB04 Ch.1), tokenizer/loss comparability (WB05 Ch.1),
  RMSNorm/RoPE-as-conventions (WB04 Ch.2).
- **New concepts:** per-series scaling (mean scaling; z-score;
  standardization plus inverse-hyperbolic-sine; median/IQR); discrete
  quantized value tokens (uniform bins, fixed vocabulary, PAD/EOS);
  continuous patches (length P, stride S, non-overlapping versus
  overlapping); per-step lag-feature tokens; missing-value masks and
  time-index meta features; patch length versus forecast horizon.
- **Primary sources:** `src-56` (Chronos), `src-64` (PatchTST),
  `src-58` (TimesFM), `src-57` (Chronos-2), `src-59` (TiRex),
  `src-63` (Lag-Llama), `src-61` (Moirai).
- **Worked example:** (a) mean-scale and uniformly bin a 12-value series
  into a small *illustrative* bin count (labeled illustrative; the paper
  uses 4096 vocabulary entries including PAD/EOS over [−15, +15]);
  (b) patch counting on the **same 12 values** with illustrative
  P=4, S=2: `N_p = ⌊(12 − 4)/2⌋ + 2 = 6` with end padding (the padded patch
  is drawn visibly), versus non-overlapping `⌊12/4⌋ = 3`; (c) one
  arithmetic line using PatchTST/64's L=512, P=16, S=8 → 64 patches
  (versus `⌊512/16⌋ = 32`). **Caveat:** those PatchTST configuration
  values sit in a section the registry records as not read (`src-64`); keep
  (c) marked unverified, or re-read the paper before using it.
- **Figure:** "Three ways to tokenize a series": bin-index tokens, patch
  tokens, lag-vector tokens, drawn for the same 12 values. Lag choices are
  labeled illustrative and only tokens whose lags are fully available are
  drawn (Lag-Llama needs a history of its largest lag). Make the
  discrete/continuous contrast explicit: "bin id → embedding-table lookup"
  versus "P values → learned projection, no table".
- **Exclusions:** tokenizer *training* (BPE etc.); time-frequency or
  wavelet representations; Fourier features; image-based representations.
- **Dependency:** none (first module).

### Module 2 — What the model sees and predicts (3.5 pp)

- **Purpose:** fix the vocabulary of context, channels, covariates and
  horizons before architectures are compared; preserve the shape rules.
- **Quick recap:** attention and causal masking (WB04 Ch.1); attention
  cost and what is stored (WB04 Ch.4).
- **New concepts:** lookback/context length versus horizon; patch length
  versus horizon; univariate; channel-independent; channel-mixed
  (flattened any-variate attention; group attention; variate mixing);
  past-only versus known-future covariates; masks for missing values and
  for "unknown future"; the **4 × 16** shape rule (below).
- **Primary sources:** `src-57`, `src-60`, `src-61`, `src-62`, `src-64`,
  `src-58`; documentation-only: `src-67`, `src-65`.
- **Worked example:** four target variables over 16 future steps:
  4 × 16 = **64 predicted values across 16 future timestamps** (not 64
  timestamps); ×9 quantile levels = 576 numbers, presented as
  *illustrative* `n_q = 9` (Chronos-2 uses 21 levels; TiRex, Moirai 2.0
  and the TimesFM documentation use 9); covariates add inputs but no
  output axis; group-ID assignment for the three task types in the
  Chronos-2 report (independent series, multivariate,
  targets-plus-covariates). W2 holds the arithmetic; F2 stays schematic.
- **Figure:** a variates × time grid showing, side by side,
  channel-independent processing, flattening, and group attention. The
  grid's axes carry their units (columns = time steps, rows = variates).
  Moirai-style flattening is labeled "64 sequence positions (4 variates ×
  16 steps)" and "16 timestamps" appears only on the time axis; the
  4×16 output box is **not** repeated here (it lives in W2). If the budget
  allows, split into F2a (shape rule) and F2b (three attention regimes);
  otherwise draw only the regimes. Axis labels are generated from
  `(n_tgt, F)`.
- **Exclusions:** irregularly-sampled series (no verified source;
  Chronos names it as out of scope); spatial/graph structure; text or
  tabular side-inputs.
- **Dependency:** Module 1.

### Module 3 — Architecture families and how a forecast is produced (4.0 pp)

- **Purpose:** classify backbones by *what the step unit is*, *how the
  horizon is filled*, and *what is training-only versus inference-time*.
- **Quick recap:** autoregressive decoding cost (WB04 Ch.1); multi-token
  prediction (WB05 Ch.2); recurrent state versus growing cache and
  depth-versus-sequence recurrence (WB04 Ch.4, 6, 8). The recap states
  that WB04 teaches only causal, decoder-only attention: encoder-only,
  masked-encoder and encoder–decoder families and bidirectional attention
  are **new treatment, not in the LLM workbooks**, and are marked so.
- **New concepts:** encoder–decoder (token-sampling), encoder-only
  direct, masked-encoder with mask tokens for the horizon, decoder-only
  patch autoregression with longer output patches, recurrent (xLSTM)
  backbones and training-time Contiguous Patch Masking, multi-patch
  prediction, documented hybrids. Horizon filling is taught as **three
  classes**: (i) iterative feedback (each pass's output is fed back as
  input), (ii) single pass over placeholder inputs with no feedback
  (masked-encoder horizon patches, TiRex's future-as-missing inputs,
  Chronos-2 and TimesFM-3 future placeholders), (iii) direct head over
  the whole horizon. "Forward passes" and "sequential compute" are kept
  separate (a recurrent backbone is sequential even in one forecast
  pass). A quantile output cannot be fed back as a single next input,
  which is why Moirai 2.0's "recursive multi-quantile decoding" matters;
  its feedback details are unread (G8) and are not described. A training
  versus inference line covers teacher forcing: training sees all patches
  in parallel; error accumulation appears only in inference rollout.
- **Primary sources:** `src-56`, `src-57`, `src-58`, `src-59`, `src-60`,
  `src-61`, `src-62`, `src-63`; documentation-only: `src-68`
  (Chronos-Bolt), `src-67`/`src-66` (TimesFM-3).
- **Worked example:** rollout counting, using the TimesFM paper's own
  example (input patch 32, output patch 128, 256-step context, 256-step
  forecast): **2** autoregressive steps versus **8** if the output patch
  were also 32; contrast with one-token-per-step sampling and with a
  single-pass direct head. Pass counts are `⌈F / P_out⌉` (2, 8, 256, 1).
- **Figure:** horizon-filling strategies on **one shared timeline** drawn
  with the W3 numbers (context 256, horizon 256, input patch 32, output
  patch 128): context and horizon shaded distinctly, patch boundaries and
  the `F` axis marked, pass counts annotated; plus a small strip marking
  "training-only (CPM, MTP)" versus "inference rollout". Class (ii)
  (placeholder, no feedback) is annotated or explicitly excluded. Nothing
  about Moirai 2.0's feedback loop or TimesFM-3's single pass is drawn as
  paper-backed; if included it is labeled documentation-only/abstract-level.
- **Exclusions:** SSM/Mamba mechanics; xLSTM equations; MoE routing
  (Moirai-MoE is deferred); KV-cache engineering; looped-depth models.
  **Representation-depth / layer-diagnostics is not a module** — see
  gap G6; one sentence may note it as an open direction only if a source
  is registered first. (Bridge row 4 is accordingly titled "TSFM backbone
  choices" and teaches no diagnostics.)
- **Dependency:** Modules 1–2.

### Module 4 — Outputs, objectives and probabilistic forecasts (3.5 pp)

- **Purpose:** connect each output type to its loss and to what the user
  can compute from it.
- **Quick recap:** logits, softmax, cross-entropy (WB04 Ch.1, WB05
  Ch.1–2); "objective versus architecture" and "loss is not comparable
  across tokenizer changes" (WB05 Ch.1).
- **New concepts:** point forecast and MSE; quantile forecast and pinball
  loss; parametric head (Student-t) and mixture head with negative
  log-likelihood; categorical-over-bins cross-entropy ("regression via
  classification", not distance-aware); sampled predictive
  distributions; loss computed in normalized space; per-output-step
  supervision ("forecast after every input token").
- **Primary sources:** `src-56`, `src-57`, `src-59`, `src-60`, `src-61`,
  `src-62`, `src-63`, `src-58`, `src-64`; documentation-only: `src-67`
  (9 quantiles documented; training loss not documented).
- **Worked example:** pinball loss at τ = 0.1, 0.5, 0.9 for one observed
  value and three forecasts (including the check that τ = 0.5 equals half
  the absolute error, so a quantile model's point forecast is its
  median); and the "same CE for a near miss and a far miss"
  demonstration for bin tokens, with a small 6-bin strip.
- **Figure:** one illustrative forecast rendered as point, quantile fan,
  mixture density and sample paths, with the tensor shape under each panel
  (4×16, 4×16×`n_q`, 4×16×`n_samples`). The point panel is labeled
  "mean/median of the example distribution (illustrative)" because point
  models are trained with MSE, not derived from a distribution. The fan
  shows marginal per-step quantiles whereas sample paths are joint. The
  Student-t head and the categorical-over-bins case are covered either by
  a compact strip or by a caption pointing to the §15 table. Do not repeat
  the 4×16 box from F2.
- **Loss-comparability caveat (taught):** cross-entropy over bins is a
  pmf in normalized space whereas Student-t/mixture NLLs are densities
  (they differ by a log bin-width term); losses are comparable only
  within the same output type and the same scaling. Quantile crossing is
  out of scope (one sentence at most).
- **Exclusions:** CRPS/scored-metric derivations beyond one sentence;
  conformal prediction; flow-matching or diffusion heads (no registered
  source); calibration methodology.
- **Dependency:** Modules 1 and 3.

### Module 5 — Pretraining data, adaptation, evaluation and leakage (3.0 pp)

- **Purpose:** carry WB05's data-mixture and held-out-evaluation
  discipline to time series, and be honest about the thin evidence on
  adaptation.
- **Quick recap:** mixing weights and multi-stage mixtures; data/eval
  separation (WB05 Ch.1); scaling laws as single-axis fits (WB05 Ch.3:
  one variable varied at a time, so no joint predictions). Because this
  carries five concepts, the recap is ⅔ page.
- **New concepts:** multi-dataset pretraining archives and per-sub-dataset
  sampling caps; frequency and domain imbalance; synthetic data;
  augmentation (TSMixup); frequency handling (multi-patch-size, ignored,
  dropped); missingness; leakage routes specific to series (temporal
  overlap with a benchmark, normalization statistics that look into the
  future); zero-shot versus fine-tuned; what transfers from LLM training
  systems (little — the registered models are tens to hundreds of millions
  of parameters, e.g. TiRex ~35M, Chronos-2 120M, original TimesFM ~200M
  per the papers and TimesFM-3 330M per the vendor blog; no registered
  source supplies a field-wide bound) and what does not.
- **Primary sources:** `src-61` (LOTSA, sampling), `src-56` (TSMixup,
  scaling observations), `src-57` (synthetic ablation, leakage column),
  `src-62` (first-30% normalization window; parameter-plateau
  observation), `src-60` (synthetic coupling); documentation-only:
  `src-66` (3.0 pretraining-data list excluding fev-bench-overlapping
  datasets), `src-65` (LoRA fine-tuning example).
- **Worked example:** the per-sub-dataset sampling cap, mirroring WB05
  Ch.1's mixing-allocation example. **Verification item:** the extracted
  text of the cap formula is garbled; re-read it in the PDF before the
  example is built (§23 criterion 6). **Fallback** if the re-read fails: a
  toy proportional allocation with an explicitly invented cap, labeled
  illustrative, with no source formula attributed.
- **Figure:** a leakage timeline: training region, normalization-statistics
  window, evaluation window. The "correct" and "leaky" panels are
  **original explanatory illustrations**; `src-62` supports only the
  statement that Moirai 2.0 computes normalization statistics from the
  first 30% of each series (a normalization-window design choice, to be
  re-read before F5 and kept distinct from benchmark leakage, G5).
- **Exclusions:** distributed-training strategies, ZeRO/FSDP, memory
  accounting (WB05 Ch.4–5 territory — "unnecessary here", §8 row 8);
  benchmark leaderboards; fine-tuning how-to.
- **Dependency:** Modules 1 and 4.

### Module 6 — Reading a TSFM release: synthesis and practice (2.0 pp)

- **Purpose:** a reading checklist plus a comparison table, practiced on
  one documented release (TimesFM-3), mirroring WB04's
  architecture-reading checklist and WB05's discipline of labeling
  numbers by origin.
- **Quick recap:** the architecture-reading checklist is **listed item by
  item** in the recap (WB04 Ch.6, "The architecture-reading checklist";
  Ch.8 synthesis framework), so the reader has something to apply.
  WB05 Ch.6's "configured / observed / derived" labels describe
  training-run numbers; the addendum uses a **different term, "source
  type"** (paper / documentation / vendor claim) and cites WB05 only as an
  analogy.
- **New concepts:** labeling every fact by source type (paper /
  documentation / vendor claim) and by model *generation*; why
  cross-generation transfer of claims is the main failure mode.
- **Primary sources:** all registered; worked case uses `src-65`,
  `src-66`, `src-67` together.
- **Worked example:** classify each statement in the TimesFM-3 blog and
  model card as paper-backed (none), documentation, or vendor claim;
  surface the unreconciled 330M-parameter versus 20-layer/1280-width
  statements (G2). **No reconciliation is attempted** and drafting must not
  guess one.
- **Figure:** the synthesis map: models (rows) × design axes (columns:
  tokenization, family, horizon filling, channels, covariates, output,
  loss) with the source type per cell. Cap at **8 models**, with
  documentation-only models in a separate shaded row group; build it from
  one YAML source shared with the module tables; it may be rendered as a
  table (cut order, §6). Every cell cites a registry id, and no cell for
  `src-65`–`src-68` states a mechanism.
- **Exclusions:** new mechanism content; any ranking of models.
- **Dependency:** Modules 1–5.

## 8. LLM-to-TSFM bridge matrix

Columns: TSFM topic | necessary LLM quick recap | source workbook/chapter |
what transfers unchanged | what changes for time series | new treatment
required | duplication risk. (Chapter titles are the frozen workbooks'
own; "WB04 Ch.1" = *Transformer Refresher*, Ch.2 = *Anatomy of a Modern
Decoder*, Ch.3 = *Attention Head Structure and Cache-Efficient Variants*,
Ch.4 = *Reducing Attention Cost*, Ch.6 = *Reading Modern LLM
Architectures*, Ch.7 = *From Architecture to Systems Behavior*, Ch.8 =
*Emerging Directions and Architecture Synthesis*; "WB05 Ch.1" =
*Pretraining Objectives and Data*, Ch.2 = *Multi-token Prediction as a
Training Objective*, Ch.3 = *Optimization and Scaling Laws*, Ch.4 =
*Parallelism Strategies for Distributed Training*, Ch.5 = *Memory and
Communication at Training Scale*, Ch.6 = *Reading Real Pretraining Runs*.)

| # | TSFM topic | LLM quick recap | Source (WB/Ch.) | Transfers unchanged | Changes for time series | New treatment required | Duplication risk |
|---|---|---|---|---|---|---|---|
| 1 | Scalar, quantized, patched, lag-feature, channel-aware and covariate-aware representations | A token id indexes an embedding table to a width-`d_model` vector; the residual stream keeps that width; losses are not comparable across tokenizer changes | WB04 Ch.1 (tokens and embeddings, residual stream); WB05 Ch.1 (loss vs tokenizer) | An input unit becomes a `d_model` vector; everything downstream operates on vectors; the residual stream is additive and constant-width | The unit is real-valued, so it is scaled first and then either binned into a vocabulary (Chronos) or projected as a patch by a residual MLP (TimesFM, Chronos-2, TiRex, Moirai, PatchTST) or built as a lag vector (Lag-Llama); masks and time indices ride along | Per-series scaling; bin design and its range limit; patch length/stride and token-count arithmetic; padding versus mask channel; losses incomparable across scalers (extends WB05's tokenizer point) | **Low** — LLM tokenizers are only recapped; BPE is not taught |
| 2 | Lookback windows, resolution, horizon, masking, irregular observations | Causal masking allows every earlier-or-equal position; score matrix is O(S²), cache is linear; windows/sparsity/recurrent state change cost | WB04 Ch.1 (causal masking); WB04 Ch.4 (cost axes) | Self-attention over tokens; cost depends on token count: patching cuts the token count by about the patch stride (about P for non-overlapping patches), so score-matrix cost falls by about the square of that factor and linear terms (cache, per-token layers) by the factor itself | Context and horizon are two different axes; some inputs (known-future covariates) may be attended bidirectionally; a second mask (group/variate) exists; missing values are explicit | Context vs horizon vs patch length; channel-independent vs channel-mixed attention; past-only vs known-future covariates; missing-value masks. **Irregular sampling: no verified source — excluded** | **Medium** — attention-cost discussion must be one paragraph, not a re-derivation |
| 3 | Iterative forecasting, direct multi-horizon prediction, multi-patch prediction, multi-token prediction | Autoregressive decoding of N tokens costs at least N forward passes (scoped to autoregressive decoding; direct heads are a contrast, not a contradiction); MTP adds training-time heads for further offsets, discarded at inference by default in WB05 (Moirai 2.0 reuses the idea at inference, so that default does not carry over); recurrent state replaces a growing cache; depth recurrence ≠ sequence recurrence (applying "sequence recurrence" to xLSTM extends WB04's SSM-based definition) | WB04 Ch.1, Ch.4, Ch.6, Ch.8; WB05 Ch.2 | Autoregressive rollout costs steps; training-time objective ≠ inference procedure | The step is a patch, not a token; an output patch may be longer than the input patch; a head may emit the whole horizon at once; future inputs may be fed as missing values; Moirai 2.0 predicts several future patches per output token | Forward-pass counting for each strategy; training-only Contiguous Patch Masking; direct vs iterative error accumulation as a *paper claim*; hybrids | **Medium–high** with WB05 Ch.2 — share the idea only; do not re-teach independent-heads vs causal-chain designs |
| 4 | TSFM backbone choices | Width, depth, residual flow; RMSNorm/RoPE/SwiGLU are conventions; recurrent/SSM family named with mechanics deferred | WB04 Ch.1–2, Ch.4, Ch.6 | Residual-stream view; normalization/positional-encoding choices are conventions (Chronos-2 uses RoPE; TiRex RMSNorm; Moirai RMSNorm, SwiGLU, query-key norm) | Backbone families unseen in the LLM workbooks: xLSTM (recurrent, state-tracking) and its attention hybrid (TiRex-2); width/depth are small (tens to hundreds of millions of parameters) | A family taxonomy; one paragraph on state-tracking as the stated reason for recurrence. **Depth diagnostics: no registered source — not taught** (gap G6) | **Low** |
| 5 | Point, quantile, parametric, mixture and sampled outputs | A head maps the final hidden state to logits; softmax gives a distribution; sampling draws from it | WB04 Ch.1 (logits and next-token prediction) | A head converts hidden states to a predictive object | The "vocabulary" may be bins (categorical), `n_q` quantiles per step, distribution parameters, or a single value; shapes include a horizon axis (and a quantile axis) | Output taxonomy and tensor shapes; sampling as a way to *represent* a distribution; what can be computed from each output | **Low** |
| 6 | Point losses, pinball loss, negative log-likelihood, sample-based objectives | Cross-entropy is −log p(target); objective ≠ architecture | WB05 Ch.1 (objective vs architecture), Ch.2 (next-token loss) | Cross-entropy over bin tokens is exactly the NLL of a categorical distribution (a pmf over bins in normalized space; not directly comparable with density NLLs such as Student-t or mixtures, which differ by a log bin-width term) | Targets are normalized values; MSE/pinball/NLL replace or sit beside CE; per-output-step supervision; CE over bins is not distance-aware (the paper says so) | Definitions and units of each loss; why pinball loss yields quantiles; why sample-based training objectives are *not* in the registered sources | **Low–medium** with WB05 Ch.2's loss formulas — reuse notation, do not re-derive |
| 7 | Pretraining mixtures, normalization, frequency, covariates, missingness, leakage | Mixing weights allocate token budget; fixed vs multi-stage mixtures; pretraining and evaluation data must be strictly separate; scaling laws are single-axis fits | WB05 Ch.1, Ch.3, Ch.6 | The mixing-allocation arithmetic and the data/eval separation rule | Mixtures are over sub-datasets with per-dataset caps; frequency and domain imbalance; synthetic data; leakage through time overlap and through normalization statistics | Time-series-specific leakage routes; synthetic-data role as a *paper claim*; scaling-law transfer is **unverified** (only single-paper size observations) | **Medium** — keep to the mixing example and the leakage rule |
| 8 | Training and systems behavior that transfers | Parallelism strategies, memory and communication accounting, nominal vs achieved compute, logical vs measured memory | WB05 Ch.4–6; WB04 Ch.7 | The logical-vs-measured labeling rule; throughput as a measured quantity; prefill-vs-decode as an analogy for encode-context-then-roll-out | Registered models are tens to hundreds of millions of parameters (see Module 5 for the per-model figures and their sources); cluster-size claims are not in the registry's read lists and are **not stated**; parallelism machinery is mostly irrelevant | Half-page callout only: what transfers and why the rest is out of scope | **High if expanded** — keep to the callout |

## 9. Quick-recap plan

Rule for every recap: ¼–½ page; plain language first, then the minimum
notation; name the workbook and chapter conceptually; mark each
statement **same idea**, **adapted idea** or **time-series-specific idea**;
assume the reader remembers nothing.

### Notation reservation table (collision avoidance)

Frozen-workbook symbols the addendum must not reuse for a different
meaning: WB04 `B` (batch), `S` (sequence length), `T_q`, `d_model`,
`V` (vocabulary), `d_ff`, `H_q`, `H_kv`, `d_head`, `L` (layers),
`Q` (query matrix), `P_total`, `P_active`; WB04 also uses `E` for **two**
things (the expert count in its notation file, and the embedding table in
Ch.1 — the frozen workbook is itself inconsistent), so the addendum
**never uses `E`** and names the embedding table in words ("embedding
table; WB04 Ch.1 writes E") or as `W_emb`; further WB04 symbols to
reserve: `k`, `p_e`, `p_s`, `p_base`, `d_c`, `d_rope`, `L_distinct`,
`T_passes`, `L_effective`;
WB05 `N` (parameters), `D` (training tokens), `C` (training compute),
`L` (cross-entropy loss), `B` (batch size), `S` (training steps), `n`
(number of future offsets in MTP), `w_i` (mixing weight of source `i`),
`Ψ`, `N_d`, `P_os` and the `S`/`P` attention matrices of WB05 Ch.5 —
checked against WB05 Chapter 3's notation paragraph and, for `n`, `S` and
`w_i`, against WB05 Ch.1–3 (the audit located them there). The earlier
draft's "`p(D_k)`" for an allocation share is **withdrawn**: WB05 uses
`w_i`, and `D` is already training tokens.

The TSFM papers use `C`/`T`/`L` for context, `H` for horizon, `B` for bins,
`D`/`V_tgt` for targets, `P` for patch length and `Q` for quantile sets —
all colliding. **Source-symbol translation rule:** when a source's own
tensor shape or formula is quoted (TiRex-2's `V_tgt × K × (L−1) × P`,
Chronos-2's `H × D × |Q|`), its symbols are translated into the addendum's
symbols and each axis is labeled; source symbols are never mixed with
addendum symbols. **Proposed addendum symbols** (to be confirmed at
Step 3):

| Meaning | Addendum symbol | Collision avoided |
|---|---|---|
| Context (lookback) length, in time steps | `T_ctx` | WB04 `S`, `L`; WB05 `C` |
| Forecast horizon, in time steps | `F` | `H_q`/`H_kv` |
| Patch length (input / output, where they differ, e.g. TimesFM) / stride | `P_in` / `P_out` (plain `P` only when they coincide) / `S_p` | WB04 `S`; WB05 `S` (training steps); `S_p` is justified against both |
| Number of patches | `N_p` | WB05 `N` |
| Number of target variables / covariates | `n_tgt` / `n_cov` | `V`, WB05 `D` |
| Number of quantile levels; a level | `n_q`; `τ` (used everywhere, including pinball loss) | WB04 `Q`, lowercase query `q` |
| Number of bins | `n_bins` | WB04 `B` |
| Number of samples | `n_samples` | WB05 `n` |
| Probability of an event or token | `p(·)` (lowercase, never the patch length) | patch length `P_in`/`P_out` |
| Dataset index / share in a pretraining mixture | `j` / `w_j` (WB05's `w_i`, re-indexed) | WB05 `D`, `i` |
| Hidden width | `d_model` (inherit) | — |

### Per-module recaps

| Module | Exact prior concept | Source (conceptual) | Same | Adapted | Time-series-specific | Minimum notation | Length |
|---|---|---|---|---|---|---|---|
| 1 | Token → embedding table → residual stream; the residual MLP / feed-forward sublayer; loss not comparable across tokenizer changes; RMSNorm/RoPE are conventions | WB04 Ch.1 (the embedding step, the residual stream, the feed-forward sublayer — run-in labels, not section headings); WB05 Ch.1; WB04 Ch.2 | An input unit becomes a `d_model` vector and the stream stays that width | Table lookup becomes either a bin-index lookup or a projection of a patch of `P_in` values | Scaling before tokenization; masks; time index; bin range limit | embedding lookup in words (not `E`); `d_model`; `T_ctx`, `P_in`, `n_bins` | ⅓ page |
| 2 | Causal masking (all earlier-or-equal positions); attention cost grows with token count; windows/sparsity/recurrent state as cost axes | WB04 Ch.1 (the attention sublayer, causal mask); WB04 Ch.4 | Attention weights tokens; the mask decides who may see whom | The mask now has a time part and a series (group/variate) part; fewer tokens because of patching | Known-future inputs are not "future" for the model; context ≠ horizon | `softmax(QKᵀ/√d_head + mask)V` (stated in words first) | ⅓ page |
| 3 | Autoregressive decoding costs ≥ N passes (scoped to autoregressive decoding); MTP as a training-time objective, discarded at inference by default in WB05 — **this default does not carry over** to Moirai 2.0, which uses the same idea at inference (one term, "multi-patch prediction", is used for the TSFM mechanism; WB05's "MTP" is named only for the recap; the TimesFM-3 blog's "CPM" is not TiRex's CPM); recurrent state vs growing cache. **Marked "not in the LLM workbooks":** encoder-only, masked-encoder and encoder–decoder families, bidirectional attention | WB04 Ch.1 (prefill vs decode), Ch.4, Ch.8; WB05 Ch.2 | Rollout cost counts steps; training-time ≠ inference-time | The step is a patch; the output patch can be longer than the input patch | Direct multi-horizon heads; future-as-missing inputs; recurrence as state-tracking (extends WB04's SSM-based "sequence recurrence") | `n` future offsets (WB05 notation reused, never as sample count); `F` | ⅔ page |
| 4 | Logits → softmax → cross-entropy; objective vs architecture | WB04 Ch.1 (logits and next-token prediction); WB05 Ch.1–2 | A head makes a distribution; CE = −log p(target) | The "class" can be a bin; the head can emit quantiles or distribution parameters | MSE/pinball/NLL; loss lives in normalized space; per-output-step supervision | WB05 Ch.2's next-token loss, restated as `−Σ log p_θ(x_{t+1} \| x_{≤t})` copied in WB05's own form at drafting (lowercase `p`; `x` is a token here, a series value elsewhere) | ⅓ page |
| 5 | Mixing weights → token allocation; fixed vs multi-stage; strict pretraining/eval separation; scaling laws as single-axis fits (one variable varied at a time) | WB05 Ch.1, Ch.3 | Allocation arithmetic; separation rule | Mixing over sub-datasets with caps | Frequency/domain imbalance; leakage through time overlap and normalization windows; thin adaptation evidence | `w_j` as allocation share | ⅔ page |
| 6 | Architecture-reading checklist (items listed in the recap); labeling numbers by origin | WB04 Ch.6, Ch.8; WB05 Ch.6 (analogy only) | Ask the same questions of every report | Add "which generation, which source type" ("source type" ≠ WB05's configured/observed/derived) | Releases with no paper | none new | ⅓ page |

## 10. Verified source matrix

Evidence levels: **P** = paper evidence (full text read); **D-README** =
official repository README; **D-card** = official model card;
**D-blog** = official vendor blog / release announcement;
**Deferred/unverified** = not read.

| ID | Source | Type / level | Generation described | Read depth | Supports | Caveats |
|---|---|---|---|---|---|---|
| src-56 | Chronos (arXiv 2403.07815v3; TMLR 10/2024) | **P** | Original Chronos | Method, objective, forecasting, augmentation, hyperparameters, limitations, covariate discussion | Mean scaling; uniform bins; 4096-token vocabulary incl. PAD/EOS; CE; sampled paths; univariate; context 512 / prediction 64; TSMixup | Not Bolt, not Chronos-2; benchmark tables not re-checked |
| src-57 | Chronos-2 (arXiv 2510.15821v1, Oct 2025) | **P** (technical report) | Chronos-2 | Abstract, related work, §3.1–3.4, benchmark table | Patches + meta features; REG token; group attention; direct quantile head (21 levels, H×D×\|Q\|); pinball loss; two-stage context; 120M/28M | Patch length value and any fine-tuning not located; related-work claims about other models are secondary |
| src-58 | TimesFM (arXiv 2310.10688v4; ICML 2024 per README) | **P** | Original TimesFM (~200M) | Full architecture section + ablation paragraphs | Residual-MLP patches; decoder-only; output patch longer than input; patch masking; MSE; autoregressive rollout; quantile/likelihood heads only *proposed* | Not 2.0/2.5/3.0; data section not read |
| src-59 | TiRex (arXiv 2505.23719v2, Nov 2025) | **P** | Original TiRex (~35M) | Architecture, CPM, loss, training setup, limitations | sLSTM backbone; 32-step windows; z-score; 9 quantiles; pinball at every output token; multi-patch via missing inputs; univariate | TiRex 1.1 mentioned in acknowledgements, unverified |
| src-60 | TiRex-2 (arXiv 2607.01204v1, Jul 2026) | **P** (preprint) | TiRex-2 | Abstract, setup, architecture, output/loss, limitations | Time mixer + variate mixer; past/future covariates; K-quantile output tensor; arcsinh scaling; streaming | **Experiments/appendices not read**; very recent |
| src-61 | Moirai (arXiv 2402.02592v2) | **P** | Original Moirai (1.x) | Problem setup, architecture, data/task distribution, limitations | Masked encoder; multi-patch-size; any-variate attention; mixture NLL; LOTSA; sampling cap | Cap formula text garbled in extraction; not Moirai 2.0/MoE |
| src-62 | Moirai 2.0 (arXiv 2511.11698v3, Feb 2026) | **P** (preprint) | Moirai 2.0 | Abstract, related work, architecture, loss, limitations | Decoder-only; single patch; quantile loss; multi-token prediction; first-30% normalization window; univariate only | Experiments/ablation numbers/inference details not read |
| src-63 | Lag-Llama (arXiv 2310.08278v3) | **P** | Lag-Llama | Architecture section only | Lag-feature tokens; Student-t head + NLL; sampled trajectories; univariate | Scaling described two ways in the paper; pretraining/adaptation not read |
| src-64 | PatchTST (arXiv 2211.14730v2; ICLR 2023) | **P** (pre-foundation-model, supervised) | PatchTST | Model-structure text | Patching (P, S, N formula); channel-independence; MSE; instance norm | Not a TSFM |
| src-65 | TimesFM repository README | **D-README** | 2.5 and 3.0 (and pointers) | Read in full to code examples | 2.5: 200M, 16k context, optional 30M quantile head, no frequency flag; XReg covariates; LoRA example; 3.0 claims; license split; example output shapes | Snapshot with dated entries; vendor benchmark claims |
| src-66 | TimesFM 3.0 model card | **D-card** | 3.0 | Read in full | Patch lengths 32/64; 20 layers, width 1280, 16 heads; data list; license | Terms like "Stacked Mixing Transformer", "CPM Iterative RevIN" undefined; quantile values missing in fetch |
| src-67 | TimesFM-3 blog (31 Aug 2026) | **D-blog** (vendor) | 3.0 | Body read in full | 330M; >1T points; lookahead tokens; alternating temporal/variate attention; single-pass decoding; 9 quantiles | Vendor claims; no paper; "CPM" name collides with TiRex's |
| src-68 | Chronos repository README | **D-README** | Chronos-Bolt, Chronos-2 (pointers) | News, introduction, model table | Bolt: patch-based, direct multi-step quantile output; checkpoint sizes; release dates | Bolt loss/normalization undocumented; vendor speed claims |
| — | Moirai-MoE (arXiv 2410.10469) | **Deferred / unverified** | Moirai-MoE | **Downloaded, not read** | nothing | Keep deferred |
| — | uni2ts README, TiRex README, Lag-Llama README | Discovery only | — | Skimmed (uni2ts, TiRex) / downloaded unread (Lag-Llama) | Pointers (Moirai 2.0 release; TiRex-2) | Not registered |

## 11. Source-registration decisions

Classification of every candidate (rules from the task applied):

**Register and use (papers, `primary_technical`):** Chronos `src-56`;
Chronos-2 `src-57`; TimesFM original `src-58`; TiRex `src-59`; TiRex-2
`src-60`; Moirai original `src-61`; Moirai 2.0 `src-62`; Lag-Llama
`src-63`; PatchTST `src-64`.
Partially verified within that class (registered with the read depth
stated in each entry): `src-57` (patch length, fine-tuning not located),
`src-60` and `src-62` (experiments unread), `src-63` (architecture only).

**Register as official documentation only (`implementation_guide`):**
`src-65` TimesFM README; `src-66` TimesFM 3.0 model card; `src-67`
TimesFM-3 vendor blog; `src-68` Chronos README (Chronos-Bolt). Each has a
distinct `resource_type` (README / model card / vendor blog).

**Verified but deferred:** none. (Nothing was fully read and then judged
unneeded, other than the TimesFM 2.5 model card, which duplicates
`src-65` for every fact the scope uses and was therefore not registered.)

**Deferred, not read:** Moirai-MoE (downloaded, unread). Models named
inside the primary papers but never opened: TimesFM in-context
fine-tuning (arXiv 2410.24087), Toto, Sundial, Time-MoE, Kairos,
FlowState, TTM, COSMIC, TabPFN-TS.

**Gaps needing work before Module 5 can cite them:** the fev-bench and
GIFT-Eval benchmark papers (their arXiv ids were not verified here).

**Exclude:** third-party studies of TimesFM (arXiv 2607.12248 and
2610.00589 — seen only as search-result titles, not opened; they are
secondary and not mechanism sources); LLM-as-forecaster / LLM-reprogramming
approaches (out of scope, §22); TimesFM 2.5 model card (redundant, above).

**Rules honored:** (1) only sources the recommended scope needs were
registered; (2) papers and documentation have different
`authority_type`/`resource_type`; (3) documentation-only versions are
labeled in `expected_use`, `resource_type` and `topic_tags`
(`documentation-only`); (4) no paper is implied for TimesFM 2.5/3.0 or
Chronos-Bolt — `src-65`/`src-66`/`src-67`/`src-68` each say so; (5)
documentation is used only for claims it states; (6) mechanism,
objective, architecture and experiment claims use papers when one exists
for *that generation*; (7) Moirai-MoE deferred; (8) nothing registered
for bibliography breadth; (9) each registered source has a complete
registry entry and a matching `shared/bibliography.bib` key, with exact
version and 2026-10-06 access-date qualifiers; (10) no claim-ledger
entries created.

**Deviation from rule 9 — the coverage matrix was NOT updated, and
`workbook_categories` is empty.** Cause: the addendum id is not in
`config/project.yaml`, and the validator and tests reject unknown
workbook ids in both the registry and the coverage matrix; adding it
would edit a test pinned to the eight-workbook list (§3). Instead the
13 entries carry `workbook_categories: []` and the topic tag
`addendum-04-05-tsfm`, and a comment block in `sources/registry.yaml`
explains this. Coverage-matrix entries for the addendum should be added
in Step 3 together with the project id. The alternative — tagging the
sources as Workbook 04/05 sources — was rejected because it would
falsely claim those frozen workbooks cite them.

Validation of this step's metadata changes is recorded in the final
checkpoint report (registry validator OK; 68 registry ids ↔ 68
bibliography keys, no orphans).

## 12. Source gaps and deferred candidates

| ID | Gap | Consequence for scope | Resolution path |
|---|---|---|---|
| G1 | No paper found for TimesFM 2.0/2.5/3.0 or Chronos-Bolt | Mechanism of those releases is unverifiable; only documented facts allowed | Re-check for papers before drafting; keep documentation labels |
| G2 | TimesFM-3: blog says 330M parameters; model card lists 20 layers, width 1280, 16 heads; the "Mixing Transformer", "CPM Iterative RevIN" and blog "Contiguous Patch Masking" are undefined and share a name with TiRex's CPM | **Unresolved source disagreement/ambiguity — preserved, not smoothed.** No explanation (different checkpoints, different counting conventions, a different model variant) is supported by any source read; none may be asserted | Used as Module 6's teaching case; Module 6 contract states "no reconciliation attempted" |
| G3 | Chronos-2 patch length value and any fine-tuning procedure not located in the sections read | Do not state a patch length for Chronos-2 | Read appendix before citing a number |
| G4 | Adaptation/fine-tuning: only a documentation-level LoRA example (`src-65`); Chronos, Moirai, Lag-Llama fine-tuning behavior not read | Module 5 adaptation subsection stays short and documentation-labeled | Read the relevant paper sections if the subsection is expanded |
| G5 | fev-bench and GIFT-Eval papers not read; leakage *definitions* are only available via Chronos-2's table and TimesFM 3.0's card sentence | Module 5 may report what each source says, not define a benchmark's leakage protocol | Read both papers' leakage sections before drafting Module 5 evaluation text |
| G6 | No registered source on representation-depth / layer diagnostics for TSFMs | No diagnostics module | Register a primary source first, or leave out. **Search record:** no systematic literature search for layer-wise or representation-depth analyses of TSFMs is recorded for this step, so the absence is "no source registered", not "no such literature exists". Any later addition requires a registered, citable (preferably peer-reviewed) source; unpublished local experiments are not registrable sources |
| G7 | Pretraining-data composition for TimesFM-1, Chronos, Lag-Llama not read | Data claims limited to Moirai (LOTSA), Chronos-2/TiRex-2 (synthetic), documentation lists | Read data sections if needed |
| G8 | TiRex-2 and Moirai 2.0 experiments, ablations, inference details unread (including how Moirai 2.0 feeds quantiles back) | No performance claims; Moirai 2.0 "recursive multi-quantile decoding" described only at the level the abstract and figure state | Read before any efficiency or accuracy claim |
| G9 | No verified source on irregularly-sampled series | Excluded from scope | — |
| G10 | No verified TSFM scaling-law source | WB05 Ch.3 is recapped only; Chronos model-size trend and Moirai 2.0 parameter plateau are single-paper observations, possibly in tension (more parameters help vs. hurt) and presented as such | Keep both observations, attributed |
| G11 | TiRex paper vs "TiRex 1.1" release | Claims are the paper's | Check TiRex docs if a release-specific claim is needed |
| G12 | Related-work descriptions of other models inside papers are secondary | Always re-verify against the other model's own source (done for Moirai-1 masked encoder and flattening: consistent with `src-61`) | — |
| G13 | Cross-source ranking claims (Chronos-2, TiRex-2, TimesFM-3 each report top results on overlapping benchmarks at different dates) | Not restated; time-sensitive and mutually dependent on snapshot | Exclude rankings |

Source disagreements and ambiguities recorded rather than resolved: G2;
TimesFM-3 described as "decoder-only … of predecessors" while also
decoding the whole horizon in one non-autoregressive pass; Lag-Llama's
two scaling descriptions; Moirai 1.0's "multi-patch-size is somewhat
heuristic" (authors' own words) versus Moirai 2.0's replacement of it.

## 13. Architecture taxonomy

Axes: **backbone**, **step unit**, **how the horizon is filled**, and —
required by AGENTS.md — **training-time vs inference-time behavior**.
"Hybrid/ambiguous" cases are kept as such.

| Model (source) | Backbone | Step unit | Horizon filling | Training vs inference notes | Class |
|---|---|---|---|---|---|
| Chronos (`src-56`, P) | Encoder–decoder (T5); a GPT-2 decoder-only run also reported | One token (a bin) | Iterative: autoregressive sampling of sample paths | CE trained on tokens; sampling only at inference | Encoder–decoder, iterative |
| Chronos-Bolt (`src-68`, D-README) | "Encoder" and "decoder" per README wording | Patch (input) | Direct multi-step quantile output | Loss and normalization **not documented** | **Hybrid** (encoder–decoder + direct quantiles); documentation-only |
| Chronos-2 (`src-57`, P) | Encoder-only transformer (T5-encoder style, RoPE) | Patch per variate | Direct multi-step quantile head; multiple output patches in one pass | Output patches per batch randomly sampled in training; context 2048 → 8192 | Encoder-only, direct |
| TimesFM original (`src-58`, P) | Decoder-only (causal) | Patch; output patch may be longer | Autoregressive rollout over output patches | Trained "decoder-only" with patch masking; inference autoregressive | Decoder-only patch autoregression |
| TimesFM 2.5 (`src-65`, D-README) | Not stated beyond parameter count and context | — | Optional continuous quantile head up to 1k horizon (documented) | — | **Family not verified**; documentation-only |
| TimesFM 3.0 (`src-66`/`src-67`, D) | Documentation: transformer with alternating causal temporal and full variate attention | Patch (card: context patch length 32, forecast-horizon patch length 64 per `src-66`; blog: patches of 32 steps per `src-67`), lookahead tokens for known-future covariates (`src-67`) | Single forward pass over masked horizon placeholders | — | **Hybrid/ambiguous**; documentation-only |
| TiRex (`src-59`, P) | xLSTM (sLSTM blocks) | 32-step window | Multi-patch forecast by feeding future inputs as missing values | CPM is training-time; "forecast after each input token" loss | Recurrent, decoder-style |
| TiRex-2 (`src-60`, P) | xLSTM time mixer + grouped-attention variate mixer | Patch per variate | Quantiles per step of every output patch; future-known covariates processed in both directions | Targets/past covariates strictly forward; streaming constant per-patch cost (paper claim) | Recurrent–attention **hybrid** |
| Moirai (`src-61`, P) | Masked encoder | Patch (size by frequency) | Horizon patches replaced by a learnable [mask]; one pass | Trained on mixture log-likelihood | Masked encoder, direct |
| Moirai 2.0 (`src-62`, P) | Decoder-only | Single patch size | Multi-token prediction (several future patches per output token) with recursive multi-quantile decoding | Feedback details not read; "recursive multi-quantile decoding" is abstract/architecture-level only (G8) | Decoder-only; multi-patch |
| Lag-Llama (`src-63`, P) | Decoder-only (LLaMA-style) | One time step (lag vector) | Autoregressive sampling of trajectories | NLL per step | Decoder-only, iterative |
| PatchTST (`src-64`, P) | Encoder | Patch | Flatten + linear head → whole horizon | Supervised per dataset | Encoder, direct (pre-foundation-model) |

Distinctions that must survive drafting: **iterative autoregression (output
fed back) vs single pass over placeholder inputs with no feedback (TiRex,
Moirai, Chronos-2, TimesFM-3) vs direct multi-horizon head (PatchTST,
Chronos-Bolt per README)**; forward-pass count vs sequential compute;
teacher forcing in training vs error accumulation only in inference
rollout; **patch length vs forecast horizon**;
**sequence recurrence (xLSTM) vs depth recurrence (looped transformers,
WB04 Ch.8)**; **architecture claims vs release-specific implementation
claims** (e.g. TiRex paper vs TiRex 1.1; TimesFM paper vs 2.5/3.0).

## 14. Tokenization taxonomy

| Class | Examples (source) | Input unit | Scaling | Missing values | Limits stated by source |
|---|---|---|---|---|---|
| **Discrete quantized value tokens** | Chronos (`src-56`) | One scaled value → one of `n_bins` bin ids (+PAD, EOS) | Mean scaling (divide by mean absolute context value; preserves zeros) | PAD token | Range bounded by outer bin centers; "strong trend" case flagged; ignores time/frequency features |
| **Continuous patches** | PatchTST (`src-64`); TimesFM original (`src-58`); Chronos-2 (`src-57`); TiRex (`src-59`); TiRex-2 (`src-60`); Moirai (`src-61`, multi patch size); Moirai 2.0 (`src-62`, single size) | `P` consecutive values → one `d_model` vector via residual MLP | Instance norm (PatchTST, Moirai); standardization + arcsinh (Chronos-2, TiRex-2); z-score (TiRex); first-30%-window statistics (Moirai 2.0) | Mask channel (Chronos-2, TiRex, Moirai 2.0); padding mask (TimesFM) | Patch length is a tradeoff: longer input patches move TimesFM away from decoder-only training (its own ablation); Moirai's multi-size mapping is "somewhat heuristic" (authors) |
| **Per-step lag-feature tokens** | Lag-Llama (`src-63`) | One time step = vector of lagged values at chosen lags + date-time features + summary statistics | Mean/variance heuristic and robust median/IQR standardization both described | — (not extracted) | Needs a history of the largest lag before the first token |
| **Documented, mechanism unverified** | TimesFM 2.5/3.0, Chronos-Bolt | Patches (TimesFM 3.0: context patch 32 / horizon patch 64 per the card; 32-step patches per the blog) | "Similar to 2.5" (blog) | — | Documentation-only |

Preserve: a **discrete** token is an index into an embedding table; a
**continuous patch** is a vector computed by a learned projection and has
no table. Quantization loses information inside a bin; patching keeps
values but introduces a patch-length/stride choice (`N_p = ⌊(T_ctx−P)/S_p⌋+2`
for PatchTST's end-padded overlapping case, `⌊T_ctx/P⌋` for
non-overlapping with no padding).

## 15. Output and loss taxonomy

| Output type | Models | Training loss | What you can compute | Source |
|---|---|---|---|---|
| **Point forecast** | TimesFM original; PatchTST | MSE | One value per step | `src-58`, `src-64` |
| **Quantile forecast** | Chronos-2 (21 levels); TiRex (9: 0.1–0.9); TiRex-2 (K levels); Moirai 2.0 (9); TimesFM-3 (9, documented); Chronos-Bolt (quantiles, documented) | Pinball (quantile) loss: Chronos-2, TiRex, TiRex-2, Moirai 2.0 papers; **loss not documented** for TimesFM-3 and Bolt | Intervals at the trained levels; no density | `src-57`, `src-59`, `src-60`, `src-62`; `src-67`, `src-68` |
| **Parametric distribution** | Lag-Llama (Student-t: degrees of freedom, mean, scale) | NLL | Density and samples via the parametric form | `src-63` |
| **Mixture distribution** | Moirai (Student-t, negative binomial, log-normal, low-variance normal) | NLL (mixture log-likelihood) | Flexible density; sampling | `src-61` |
| **Categorical over bins → sampled** | Chronos | Cross-entropy over bin tokens (= NLL of a categorical) | Sample paths by autoregressive sampling, then dequantize/unscale | `src-56` |
| **Sampled predictive distribution** (a way to *represent* the distribution, not a loss) | Chronos; Lag-Llama | (as above) | Empirical quantiles/intervals from samples | `src-56`, `src-63` |
| **Proposed, not trained** | TimesFM original suggests quantile heads and likelihood heads | — | — | `src-58` |

Loss facts to preserve: **cross-entropy** over bins is not
distance-aware (the Chronos paper says so itself); **pinball loss** for
level `q` is `τ·max(z−ẑ,0) + (1−τ)·max(ẑ−z,0)` (form as printed in the
Chronos-2 and TiRex papers, written here with the addendum's `τ` rather
than the papers' own level symbol); the "averaged over levels and steps"
statement is to be confirmed per paper in the claim ledger; at `τ = 0.5`
pinball loss is half the absolute error, so a quantile model's point
forecast is its median;
**negative log-likelihood** underlies Lag-Llama, Moirai, and (as CE)
Chronos — but CE over bins is a pmf in normalized space while Student-t
and mixture NLLs are densities (they differ by a log bin-width term), so
losses are comparable only within the same output type and scaling; **point losses** (MSE) give no uncertainty. Losses are computed
in **normalized space**, so values are not comparable across different
scaling schemes (extension of WB05 Ch.1's tokenizer point). Sample-based
*training* objectives (e.g. flow-matching) have no registered source and
are not taught (§22).

## 16. Channel, covariate, context and horizon taxonomy

**Channels.**

| Class | Meaning | Examples |
|---|---|---|
| Univariate | The model interface accepts one series per forecast | Chronos, TimesFM original, Lag-Llama, TiRex, Moirai 2.0 (the paper's limitation: univariate only; its text on handling multivariate data as independent univariate series is the authors' wording) |
| Channel-independent | A multivariate input is split into independent univariate series processed by one shared backbone | PatchTST (by design) |
| Channel-mixed | Variates attend to each other | Moirai original (flatten all variates into one sequence, variate-ID biases); Chronos-2 (group attention); TiRex-2 (variate mixer); TimesFM-3 (documented variate attention) |

**Covariates.** Past-only versus known-future: Chronos-2 (both, via
group ID and mask; categorical covariates target/ordinal-encoded);
TiRex-2 (both); TimesFM-3 (documented, both); TimesFM 2.5 (documented
"XReg" support — mechanism unverified); Moirai original (dynamic
covariates in its formulation and figure); Chronos original, TimesFM original, TiRex, Moirai 2.0 (none —
Moirai 2.0 *dropped* them, stating minimal benefit).

**Deterministic time features** (kept separate from covariates):
Lag-Llama's date-time features; Chronos-2's time-index meta features.
These are computed from the timestamps, not supplied by the user.

**Context.** Each number is labeled by kind and unit: Chronos: 512 time
steps (training setting, paper); Chronos-2: 2048 then 8192 (two training
stages, paper; time steps vs tokens not stated here, and the patch length
is unlocated, G3); TiRex: 2048 (training context, paper); TimesFM 2.5:
up to 16k (README-documented maximum, an inference-supported figure, not a
training value); Moirai original: windows of at most 512 total positions
in training (paper; positions, not time steps). Training settings are not
guarantees of inference behavior.

**Horizon and shape rules (preserved verbatim from the handover).**

- **Four target variables forecast over 16 future steps produce a 4 × 16
  value tensor: 64 predicted values across 16 future timestamps — not
  64 timestamps.**
- Adding a quantile axis gives 4 × 16 × `n_q` numbers. Chronos-2's
  stated output is `H × D × |Q|` (horizon, targets, quantiles);
  TiRex-2's is `V_tgt × K × (L−1) × P` (targets, quantiles, patches,
  steps per patch); the TimesFM README example prints a point forecast
  of shape (12,) and quantiles of shape (12, 9). **Axis order differs by
  source; the addendum must label axes, never assume an order.**
- **Patch length ≠ horizon**: a horizon can be shorter than one output
  patch or span several (the surplus is truncated); `F` is in time steps,
  `P_in`/`P_out` are in time steps per patch, and the number of output
  patches is `⌈F / P_out⌉`. `F` counts time steps while a model's output
  tensor may carry the time axis as patches × steps per patch (TiRex-2).
- Covariates add inputs but no output axis.
- Sampling adds a **third** axis that replaces the quantile axis (the two
  are alternative ways to represent a distribution, not additive):
  4 × 16 × `n_samples`.

## 17. Worked-example plan

Plan only — no data files, scripts or tests created. At Step 3 each
example follows the Workbook 05 pattern (data under
`data/worked-examples/`, a script, a `tests/test_*_worked_examples.py`).
All numbers are hand-computable and labeled **logical/illustrative**,
never measured.

| # | Module | Example | Verification note |
|---|---|---|---|
| W1 | 1 | Mean-scale and bin 12 values into a small illustrative bin set; count patches on the same 12 values (P=4, S=2 → 6 with end padding; non-overlapping → 3); one arithmetic line for L=512, P=16, S=8 → 64 (vs ⌊L/P⌋ = 32) | Patch formula from `src-64`; bin and patch settings labeled illustrative; the 512/16/8 configuration is **unverified** until the `src-64` section is re-read |
| W2 | 2 | 4 targets × 16 steps = 64 values / 16 timestamps; ×9 quantiles = 576 (illustrative `n_q`); group IDs for the three Chronos-2 task types | Shapes are arithmetic; group-ID layout from `src-57` |
| W3 | 3 | Rollout counting: context 256, forecast 256, input patch 32; output patch 128 → 2 steps vs 8; one-token-per-step → 256; direct → 1 (`⌈F/P_out⌉`) | The 2-vs-8 case is `src-58`'s own example |
| W4 | 4 | Pinball loss for τ∈{0.1, 0.5, 0.9} (τ=0.5 = half the absolute error); CE identical for a near-miss bin and a far-miss bin | Formulas from `src-57`/`src-59`; CE property from `src-56` |
| W5 | 5 | Per-sub-dataset sampling cap with toy sub-datasets | **Re-read the exact formula in the PDF first** (§23.6); fallback: toy proportional allocation, labeled illustrative |
| W6 | 6 | Source-labeling exercise on the TimesFM-3 blog + card | Uses G2 as the teaching case |

## 18. Figure plan

Original diagrams only (AGENTS.md: no reuse of source figures; attribution
for ideas). Each figure has source code in `figures/source/` and a render
in `figures/rendered/`. "Semantic test" = something a script can check.

| # | Module | Figure | Pedagogical use | Semantic test | Redundancy risk |
|---|---|---|---|---|---|
| F1 | 1 | Three ways to tokenize the same 12 values (bin lookup vs projection-without-table made explicit) | Contrast bin / patch / lag-vector inputs | Number of drawn patches equals the computed `N_p` (6 for P=4, S=2, padded patch visible); bin ids match W1; only fully-available lag tokens drawn | Low |
| F2 | 2 | Variates × time grid with three attention regimes (axes carry units; flattening labeled "64 sequence positions") | Channels; variables vs timestamps | Axis labels and units are generated from `(n_tgt, F)`; "16 timestamps" appears only on the time axis; the 4×16 output box lives in W2, not here | Medium with W2 — keep the figure schematic |
| F3 | 3 | Horizon filling on one shared timeline with context/horizon shading, patch boundaries and a training-only vs inference strip | Iterative vs placeholder vs direct; context vs horizon | Pass counts equal `⌈F/P_out⌉` and W3 (2, 8, 256, 1) | Low |
| F4 | 4 | One illustrative forecast as point / quantile fan / mixture / samples, with shapes under each panel | Output types | Shape labels match 4×16, 4×16×`n_q`, 4×16×`n_samples`; empirical quantiles of the sample paths match the quantile fan within tolerance; point panel labeled mean/median of the example | Medium — avoid decoration; no 4×16 box |
| F5 | 5 | Leakage timeline (train, normalization window, evaluation); original illustration | Where leakage enters | Windows do not overlap in the "correct" panel, do in the "leaky" panel | Low |
| F6 | 6 | Models × design-axes synthesis map (or table) with source-type shading, ≤ 8 models, documentation-only group separated | Synthesis | Every cell cites a registry id; no cell for `src-65`–`src-68` states a mechanism | **Density risk** — hard cap 8 models |

Six figures for ~22 pages is deliberately light. Each figure has at least
one question answerable from it (e.g. "how many timestamps are in the
box?").

## 19. Question and answer-key plan

- ~6 questions per substantive module (Modules 1–5) and ~4 for Module 6:
  ~34 total; questions count inside each module's page budget and keys in
  the back-matter row (§6). Mix: recall of a definition, a hand calculation (W1–W5),
  a diagnosis ("which source type supports this sentence?"), and one
  interview-style tradeoff per module.
- **Answerable from preceding material only** (AGENTS.md): no question
  may require benchmark rankings, a model not introduced in the same
  module, or knowledge of Workbooks 04/05 beyond that module's quick
  recap.
- Answer keys in `solutions/`, following the Workbook 05 solution
  files, validated by `scripts/validate_questions.py` against
  `shared/question-schema.yaml`.
- Every numeric answer is reproduced by the same script as its worked
  example.

## 20. Claim-ledger strategy

- **None created in Step 2** (rule: no ledger before the scaffold).
- At Step 3, create `claim-ledger.yaml` per
  `shared/claim-ledger-schema.yaml`. Each substantive claim records: the
  claim; the **registry id**; the **model generation**; the **source
  type** (paper / README / model card / vendor blog); whether it is a
  paper claim, a documentation claim, a derived (computed) value, or an
  original explanatory statement; and a time-sensitive flag for every
  post-2025 source.
- Hard rules: **no claim may cite a source for a different generation
  than the one it describes**; documentation-only ids (`src-65`–`src-68`)
  may support only statements that appear in them; any claim resting on
  an unread section (G3, G4, G7, G8) is marked unverified or omitted.
- Chapter contracts (`chapter-contracts/mNN.yaml`) list required and
  forbidden claims per module; forbidden examples: "TimesFM 2.5 uses X
  because …" (no mechanism source), "Chronos-Bolt is trained with …",
  any ranking.

## 21. Build and review strategy

- Draft and review each module through the existing skills
  (`.claude/skills/draft-workbook-chapter/`,
  `.claude/skills/review-workbook-chapter/`; explicit invocation only),
  per `docs/chapter-factory-operator-guide.md`; deterministic gate
  `scripts/chapter_gate.py`; frozen-chapter registry entry for
  `addendum-04-05-tsfm` added **by hand at the end** of whichever task
  accepts a module.
- **Guardrail interaction:** each parent session admits at most four
  Agent launches. Plan one auditor batch per module per fresh session,
  or one combined batch for several modules if the operator guide
  allows; never reset the counter.
- Build only after approval: development builds to `outputs/_development/`,
  `pdftoppm` page images inspected visually (AGENTS.md), RC1 to
  `outputs/_releases/`, canonical PDF only after human acceptance; prior
  PDFs preserved with date/hash suffix.
- Scaffolding checklist (Step 3, not now): addendum id in
  `config/project.yaml` **and** updated pinned test; coverage-matrix
  entry; `scripts/workbook_qa.py` registry entry; Quarto/Typst
  configuration reuse; page-budget file.
- CPU-only; no SLURM; no full-repo test runs unless a task needs them.

## 22. Explicit exclusions

- Reprogramming or prompting general LLMs for forecasting (LLMTime,
  GPT4TS-style); text-conditioned or multimodal forecasting.
- Classical forecasting methods as a tutorial (ARIMA, ETS, Theta) — named
  only where a source compares against them.
- Benchmark leaderboards, rankings, "state of the art" claims (all are
  vendor/author claims and time-sensitive).
- Inference engineering, serving, quantization, deployment (Workbook 06
  territory).
- Parallelism, ZeRO/FSDP, memory/communication accounting (Workbook 05
  Ch.4–5), except the half-page "what transfers" callout.
- xLSTM/SSM equations; MoE TSFMs (Moirai-MoE deferred); looped-depth models.
- Anomaly detection, classification, representation-learning uses;
  representation-depth diagnostics (G6).
- Irregular sampling (G9); spatial/graph forecasting.
- Fine-tuning how-to and library tutorials (the README's LoRA example may
  be *mentioned*, labeled documentation).
- Flow-matching/diffusion output heads and sample-based training
  objectives (no registered source).
- Any claim about TimesFM 2.0/2.5/3.0 or Chronos-Bolt internals beyond
  what the documentation states.

## 23. Step 3 entry criteria

All must hold before scaffolding or drafting begins:

1. **You approve** the six-module scope and ~22-page budget (or request
   changes), and the title/location/artifact names.
2. **Audit completed** (§24): the four auditors ran, every required
   finding is resolved and recorded in §24 (hard gate), and the single
   local Step 2 commit exists.
3. **Explicit authorization** to add the `addendum-04-05-tsfm` id to
   `config/project.yaml` and to update the pinned
   `tests/test_project_structure.py` list accordingly (and then add
   coverage-matrix entries for `src-56`–`src-68`).
4. **Notation table confirmed** (§9) — in particular `T_ctx`, `F`,
   `P_in`/`P_out`, `n_q`, `τ`, `w_j`; the collisions found in the audit
   (`E`, `p(D_k)`, `P`, `q`/`Q`, `n`, `S`) are closed, and the
   source-symbol translation rule is adopted.
5. **Documentation sources re-checked** on the day drafting begins
   (`src-65`–`src-68` are mutable pages; re-check for a TimesFM-3 paper
   or technical report), with `last_verified` updated.
6. **Moirai sampling-cap formula re-read** in the PDF before W5 is built;
   decide whether W5 stays in scope.
7. **Module 5 evaluation text**: read the fev-bench and GIFT-Eval leakage
   sections (G5), or restrict Module 5 to statements attributed to the
   registered sources.
8. **Experiments-dependent claims**: read `src-60`/`src-62` experiment
   sections *only if* a module will cite performance or efficiency.
9. **Decision on G6**: confirm "no diagnostics module", or name a source
   to register first.
10. A chapter contract exists for each module before drafting (chapter
    factory requirement).
11. **Scaffolding prerequisites** (§21) are all authorized: the
    `scripts/workbook_qa.py` entry, the page-budget file, the
    Quarto/Typst configuration, and a chapter-status-registry entry for
    the addendum.
12. **Recap-sufficiency rule:** a cold-reader check or an audit rule that
    no module uses a notion absent from its quick recap or its own text.
13. **Re-read items resolved or marked unverified** before the dependent
    example is built: Moirai sampling cap (`src-61`); PatchTST
    L=512/P=16/S=8 and L=336 (`src-64`); Moirai 2.0 30%/70% normalization
    passage before F5 (`src-62`); `src-60` and `src-57` ablation/synthetic
    statements; "averaged over levels and steps" per paper.
14. **Page-budget feasibility** confirmed: how answer keys are rendered
    in-PDF, and that the §6 table (22.0 pages all-in) holds after the
    first module build.

## 24. Internal-audit status

- **Audit status: complete (2026-10-06).** Exactly four read-only
  auditors ran in two foreground waves of two (Wave 1: source, technical;
  Wave 2: consistency, visual), all against the same draft; the Agent
  counter reached exactly 4; no file was changed between waves.
- **Limits of the audit (stated by the auditors):** none re-opened the
  source PDFs or web pages; read-depth judgments rely on each registry
  entry's own `access_status`; the consistency auditor did not open the
  workbook PDFs (page counts unverified); the visual auditor reviewed
  plans only (no rendered pages exist).
- **Disposition rule applied:** each substantiated required finding was
  corrected; recommended findings were applied where they improved
  correctness, scope clarity or build feasibility and did not add pages.
  The six-module structure, the 22-page target and the 24-page ceiling
  are retained; no finding identified a blocking problem. No
  representation-depth module was added. The TimesFM-3 discrepancy stays
  open. **No finding was rejected.** Where the auditor's own evidence was
  recollection, the fix was to mark the claim unverified or remove it, not
  to substitute another unverified value.

### Source auditor (S)

| ID | Class | Finding (short) | Disposition |
|---|---|---|---|
| S-R1 | required | `src-61` states a 0.001 sampling cap as fact; report says text garbled | **Applied.** Value removed from `expected_use`, marked unverified in registry; W5 fallback added (§7, §17, §23.13) |
| S-R2 | required | `src-64` notes give L/P/S configs from sections recorded as unread | **Applied.** Registry notes now mark them unverified; W1 splits a 12-value example from the 512/16/8 line (§7, §17) |
| S-R3 | required | "9M–710M" and "8 × A100-40GB" unsupported by registry | **Applied.** Both removed; replaced by per-model figures with their sources (§7 M5, §8 row 8) |
| S-4 | recommended | `src-60`/`src-57` `expected_use` outruns read depth | **Applied** in registry (qualifiers added) |
| S-5 | recommended | `src-62` calls the 1.0-vs-2.0 summary primary for both generations | **Applied** in registry (secondary for Moirai 1.0, verify vs `src-61`) |
| S-6 | recommended | `src-68` asserts "T5-style" for Chronos-Bolt | **Applied** in registry (README wording only) |
| S-7 | recommended | §1 overstated verification as full-text | **Applied** (§1 now "read in part") |
| S-8 | recommended | TiRex listed as both univariate and channel-independent | **Applied** (§16: TiRex univariate only) |
| S-9 | recommended | Make "no reconciliation attempted" explicit for TimesFM-3 | **Applied** (G2, Module 6) |
| S-N | no action | Registry↔bibliography keys; last_verified; paper/doc split; version clauses; Moirai-MoE deferral; empty `workbook_categories` | Retained |

### Technical auditor (T)

| ID | Class | Finding (short) | Disposition |
|---|---|---|---|
| T-R1 | required | "patching cuts cost by roughly the stride" ignores O(tokens²) | **Applied** (§8 row 2) |
| T-R2 | required | Sampling axis miscounted ("fourth"); quantile and sample axes alternatives; truncation | **Applied** (§16) |
| T-R3 | required | Notation collisions: `P` (in/out, vs probability), `q` vs `τ`, reserved-list gaps, source-symbol translation | **Applied** (§9) |
| T-R4 | required | Iterative vs direct is a three-way split; passes vs sequential compute; teacher forcing | **Applied** (§7 M3, §13, F3/W3) |
| T-R5 | required | CE over bins vs density NLL not directly comparable | **Applied** (§7 M4, §8 row 6, §15) |
| T-R6 | required | "MTP discarded at inference" contradicts Moirai 2.0 | **Applied** (§8 row 3, §9 recap row 3, §13) |
| T-C1 | recommended | Page budget unitemized; 23.5 nominal | **Applied** (§6 all-in 22.0, cut list) |
| T-C2 | recommended | Channel taxonomy overlaps (TiRex, Moirai 2.0) | **Applied** (§16) |
| T-C3 | recommended | Calendar features conflated with covariates | **Applied** (§16 deterministic time features) |
| T-C4 | recommended | Context list mixes training and inference values, steps and tokens | **Applied** (§16) |
| T-C5 | recommended | TimesFM-3 patch length 32 vs 32/64; split joint citations | **Applied** in §13/§14 (card vs blog per fact); the Module 3 source line still lists `src-67`/`src-66` jointly — **partial**, to be split in the chapter contract |
| T-C6 | recommended | Parameter range mixes sources | **Applied** (range removed) |
| T-C7 | recommended | Moirai 2.0 30%/70% vs benchmark leakage | **Applied** (F5 reworded; re-read gate §23.13) |
| T-C8 | recommended | τ=0.5 median; quantile crossing; per-paper "averaged" claim | **Applied** (§15, W4) |
| T-C9 | recommended | 4×16 example: covariates add no axis; F vs patched axis | **Applied** (§16) |
| T-C10 | recommended | Record G6 searches; rename row 4 | **Applied**: row renamed; G6 records that **no systematic search was run** |
| T-N | no action | PatchTST/TimesFM arithmetic; pinball formula; doc-only separation; disagreements preserved | Retained |

### Consistency auditor (C)

| ID | Class | Finding (short) | Disposition |
|---|---|---|---|
| C-1 | required | `E` has two meanings in WB04; reservation incomplete | **Applied** (§9: never use `E`; extended list) |
| C-2 | required | WB05 uses `w_i`, not `p(D_k)`; reserve `n`, `S` | **Applied** (§9, recap row 5) |
| C-3 | recommended | Attention-cost bridge inconsistent | **Applied** (same as T-R1) |
| C-4 | recommended | `L_1` form not WB05's | **Applied** (copy WB05's form at drafting; lowercase `p`) |
| C-5 | recommended | MTP terminology trap | **Applied** (one TSFM term "multi-patch prediction"; same as T-R6) |
| C-6 | recommended | "N tokens ≥ N passes" needs scoping | **Applied** (§8 row 3, recap row 3) |
| C-7 | recommended | Recaps insufficient (M1 residual MLP; M3 encoder families; M5 caveat; M6 checklist) | **Applied** (§7, §9; M3/M5 recaps ⅔ page) |
| C-8 | recommended | "configured/observed/derived" term collision | **Applied** (renamed "source type") |
| C-9 | recommended | Quoted WB04 concept names are not headings | **Applied** in §9 (described as run-in labels); §8's source column still uses concept names in prose — acceptable as conceptual references |
| C-10 | recommended | "Sequence recurrence" for xLSTM extends WB04 | **Applied** (§8 row 3) |
| C-11 | recommended | Step 3 criteria incomplete | **Applied** (§23 items 2, 4, 11–14) |
| C-N | no action | Titles; frozen status; eight ids; bridges; boundaries; no `@sec-` references | Retained |

### Visual auditor (V)

| ID | Class | Finding (short) | Disposition |
|---|---|---|---|
| V-R1 | required | Page budget unrealistic; keys/refs/callout unassigned | **Applied** (§6) |
| V-R2 | required | F1 vs W1(b) mismatch; lag-token availability | **Applied** (12-value example; F1 test) |
| V-R3 | required | F2 risks "64 timestamps" confusion | **Applied** (§7 M2, F2) |
| V-R4 | required | F3 hides context/horizon, patch length | **Applied** (F3 shared timeline) |
| V-R5 | required | F4 omits output types; point not derived from a distribution | **Applied** (F4, §7 M4) |
| V-R6 | required | F5/W5 rest on unverified material | **Applied** (original illustration; W5 fallback) |
| V-R7 | required | 576 presented as Chronos-2 behavior | **Applied** (illustrative `n_q=9`) |
| V-8 | recommended | F6 is a table; cap models; shared YAML | **Applied** (cap 8; shaded doc-only group) |
| V-9 | recommended | No training-vs-inference visual in M3 | **Applied** (F3 strip) |
| V-10 | recommended | Figure-linked questions | **Applied** (§18) |
| V-11 | recommended | 6-bin strip for near/far-miss CE | **Applied** (W4) |
| V-12 | recommended | F2/W2, F4/W2 redundancy | **Applied** (4×16 box only in W2) |
| V-13 | recommended | Bin vs patch lookup in F1 | **Applied** |
| V-N | no action | Module coverage; W1/W3 arithmetic; 4×16 wording | Retained |

- **Hard constraints honored in consolidation:** no edit to
  `config/project.yaml`, project-list tests, frozen workbooks or output
  PDFs; no scaffold; edits limited to this report,
  `sources/registry.yaml` and `shared/bibliography.bib` (the latter needed
  no change from the audit).
- **Remaining open items** (not blocking; carried into §23): TimesFM-3
  parameter/architecture discrepancy (G2); Moirai sampling cap; PatchTST
  configurations; Moirai 2.0 normalization passage; fev-bench/GIFT-Eval
  leakage definitions (G5); answer-key page cost.
