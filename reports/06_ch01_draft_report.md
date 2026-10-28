# Workbook 06, Chapter 1 — draft report

**Chapter:** The Inference Workload: Prefill, Decode, the Roofline, and the Latency–Throughput Trade-off
**Date:** 2026-10-28
**Status:** `drafted_pending_human_review` (contract and status registry). Chapters 2–7 remain `scaffold_only`.
**Builds:** development/review only. No canonical PDF, no RC. No GPU, SLURM or model download.

## What was produced

| Artifact | Path |
|---|---|
| Chapter prose (12 required sections) | `workbooks/06-llm-inference/chapters/01-inference-workload.qmd` |
| Answer key (5 answers + applied exercise) | `workbooks/06-llm-inference/solutions/01-inference-workload-solutions.qmd` |
| Question records | `workbooks/06-llm-inference/questions.yaml` (`q-06-inference-workload-001..005`) |
| Claim ledger | `workbooks/06-llm-inference/claim-ledger.yaml` (`claim-06-inference-workload-001..017`) |
| Worked example (numeric source of truth) | `workbooks/06-llm-inference/data/worked-examples/inference_workload_and_metrics.{py,json}` |
| Figures | `figures/source/fig_{roofline_prefill_decode,request_timeline,latency_throughput_frontier}.py` and `_common.py` -> `figures/rendered/*.svg` |
| Tests | `tests/test_workbook06_ch01_worked_examples.py` (18), `tests/test_workbook06_ch01_figure_invariants.py` (18); `tests/test_workbook06_scaffold.py` narrowed (13) |
| Review package | `outputs/_development/06-llm-inference/chapter-01-review/` (not committed) |
| Audit records and gate report | `outputs/_development/06-llm-inference/chapter-gate/ch01-*.json` (not committed) |

## Sources and reading depth

All sources were read directly in the passages cited. Locators are in the claim ledger.

- **src-78** (Pope et al.): targeted full text, Sec. 2–2.1.
- **src-79** (Roofline): Berkeley tech report, Sec. 2–4. The CACM version was not read.
- **src-75** (Sarathi-Serve): Sec. 2.4 and Sec. 5.
- **src-76** (DistServe): Sec. 1, Sec. 3.1 Eq. 1 and fn. 3.
- **src-10** (scaling book): "Inference" chapter, critical batch, attention intensity, step-time equations and the roofline caveat.
- **src-44** (Leviathan et al.): Sec. 2.2.
- **src-96** (Holtzman et al.): **newly registered**. Sec. 3.1–3.3, Eqs. 2–4.
- **src-82** (vLLM v0.32.0): code at commit 5df63a72, `endpoint_request_func.py:228-287` and `serve.py:600-664, 749-764, 1011, 1081-1090`. The registry notes were extended with these locators.
- **src-81** (MLPerf rules): `inference_rules.adoc:270` at commit d3eba2f.

## Worked-example assumptions

All inputs are illustrative and all outputs are derived and idealized.

- **Model:** a dense, 8B-class shape with GQA (32 layers, d_model 4096, 32 query and 8 KV heads, d_head 128, gated FFN 14,336, vocabulary 128,000). Weights and cache are 2-byte.
- **Accelerator:** 1e15 FLOP/s, 3e12 B/s, 80 GB.
- **Logical bytes:** each weight and cache element is read once per step. Activations and the decode KV write are ignored.
- **Prefill:** unembedding is applied at the last position only. Causal attention counts only unmasked pairs.

## Audit dispositions

Four bounded, read-only audits ran in parallel as subagents: sources/claims, technical/numerical, pedagogy/Q&A, and rendered layout. This was done under the user's explicit request for bounded read-only audits and the standing restoration of subagent use (max 4, depth 1).

**Note:** `docs/chapter-factory-operator-guide.md` still describes a single-agent, sequential audit process. That text predates the restoration and was not changed here.

No blockers were found. Every required finding was fixed.

### Required findings (all resolved)

| Audit | Finding | Resolution |
|---|---|---|
| Technical | Prefill counted unembedding FLOPs at all 2048 positions, which is a training-time convention. | Script fixed: 28.6 TFLOP, weight-only intensity about 1,905, bound 29.7 ms (was 30.7 / 2048 / 31.8). Prose, ledger and tests updated. |
| Source | Chapter said DistServe "treats queueing separately" from TTFT. | Its Sec. 3.1 queueing model includes queueing. The chapter now reports both of the paper's usages and no longer claims a firm disagreement with Sarathi-Serve. |
| Source | Engine-order claim for the sampling transforms had no source. | Softened to "order changes the result" and cited to Holtzman Sec. 3.3. |
| Source | Missing version pins. | MLPerf is now "as of August 2026"; vLLM sentences are now "v0.32.0". |
| Pedagogy | B, S, d_head and b_kv were used before being defined. | They are now defined in the recap. |
| Visual + technical | Roofline label collision. | Label moved. |
| Visual + technical | Figure 3 caption claimed values the table omits. | Caption reworded. |

### Optional findings (resolved)

- Throughput window now ends at the last end-of-stream marker (1.04 s), matching vLLM's duration as verified at `serve.py:1081-1090`. Results: 3.85 req/s and goodput 2.88 / 1.92 (were 3.86 and 2.90 / 1.93).
- Integer crossover of 334 tokens is now stated and tested.
- Statement on when the cache dominates traffic is corrected to B·S > about 114k tokens.
- Attention byte and causal-FLOP conventions are stated.
- Activation caveat added at prefill.
- Arithmetic intensity and operational intensity reconciled.
- E2E relation wording corrected.
- Ledger locators tightened, and src-96 added to the planned sources.
- "(Chapter 3)" pointer added.
- Full question text restated in the answer key.
- Legend backing added.
- Lead-in punctuation fixed.

### Optional findings (accepted, not changed)

- Blank space at the bottom of p.2 before the unbreakable Analogy callout (section boundary).
- One inline-math line break on p.4.
- Figure labels print at about 8.4 pt, which is above the 8 pt floor.
- Bibliography entry [9] (src-44) has no venue or year. The `.bib` entry is shared with published workbooks, so it was left unchanged.

### Defects found by main-agent page inspection before the audits (resolved)

- Equation overlapping its number.
- Apostrophes after digits rendered as primes (U+2032). The pipeline converts them, so those possessives were reworded.
- Wrapped and stretched table headers and question lines.
- Stranded lead-in line.
- Clipped B=1 label.
- Two half-empty pages.
- Rounding error (5.03 -> 5.02 ms) and a wrong ratio ("26-fold" -> about 20-fold), both caught by the new prose-crosscheck tests.

## Validation

- **Scoped tests:** 49 pass (Ch1 + scaffold).
- **Full suite:** 695 tests. Only the 3 known WB04 baseline failures remain, and there are no new failures.
- **Validators:** `validate_registry`, `validate_questions`, `validate_chapter_contract` and `validate_publication_hygiene` all OK. `git diff --check` is clean.
- **Chapter gate:** `pass_with_warnings`. The only remaining deterministic warning is `text_leakage`, caused by hash-like tokens that are the Roofline DOI and the pinned vLLM and MLPerf commit URLs in the bibliography. These are legitimate citations.
- **Environment note:** running the suite under the conda Python (3.14, no numpy) rewrites three frozen WB05/addendum JSON files with float-precision churn, and one WB04 test errors. Those files were restored with `git checkout`. Suites and builds were then run with system Python 3.10, which leaves them unchanged.

## Limitations

- No number in the chapter is measured. Hardware is illustrative and is not a registered specification.
- The vLLM request-function locator covers the OpenAI-completions client only.
- The audits were not rerun after the correction pass. The main agent verified each fix directly (tests, rebuilt PDF, page-by-page inspection).

## Correction pass 1 (2026-10-28, after commit 2119ff7)

Scope was narrow and requested by the reviewer. No numerical results changed.

- **Integrated subtitle.** Changed "Development scaffold: drafting has not yet begun" to "Development draft: Chapter 1 drafted; Chapters 2–7 scaffolded". The index status comment was updated to match. The scaffold test now checks the new subtitle and rejects "complete" and "release-ready".
- **Equation 1 scope.** Equation 1 now splits weights into backbone weights $P_\text{bb}$, applied at all $N_\text{tok}$ processed positions, and output-head weights $P_\text{out}$, applied at $N_\text{logit}$ logit-producing positions. The text beside the equation states two cases:
  - At decode, $N_\text{logit} = N_\text{tok}$.
  - On the generation-prefill path, only the last position needs logits. Training, and requests for prompt log-probabilities, need more positions.

  The intensity bound is reached only when $N_\text{logit} = N_\text{tok}$. The crossover (334 tokens) and the prefill intensity (about 1,900) are labelled idealized weight-only estimates. The prefill paragraph now cites Equation 1 with $N_\text{logit} = 1$, and a new test checks that this reproduces the prefill FLOPs in the JSON.
- **Question layout.** Each "Check your understanding" item is now a one-item list in a non-breakable Typst block, so every prompt stays with its answer line. Question text is unchanged.
  - Two show-rule approaches were tried first and rejected: one reset the numbering, and the other hit Typst's maximum show-rule depth.
  - In the standalone review, the worked-example blocks were reordered (Table 1, Figure 2, prefill paragraph, decode discussion, Figure 3) to remove a mostly blank page introduced by the longer Equation 1 text.
  - Questions 1–5 are on one page in both artifacts: page 10 of the standalone review and page 12 of the integrated build.
- **Validation.**
  - Scoped Workbook 06 tests: 50 passed.
  - All four validators passed, and `git diff --check` is clean.
  - Chapter gate: `pass_with_warnings`. The only warning is the same `text_leakage` bibliography hash/DOI warning as before.
  - Integrated development build: status `pass`, 28 pages.
  - The review-package builder runs the full suite as its own Step 6. It ran under system Python 3.10: 696 tests, the 3 known WB04 baseline failures, 0 errors, and frozen files unchanged. The full suite was not run separately.
- **Audits.** Not rerun. The changes are presentational, plus a clarification of a formula whose results are unchanged.

## Correction pass 2 — pagination only (2026-10-28, after commit 3202b3f)

No prose, equations, numbers, figures, questions or answers changed.

- **Answer Key opening and solution prompts.** The introductory sentence and each of the five repeated question prompts in the answer key are wrapped in a `sticky` Typst block (`#block(sticky: true, width: 100%)`). A sticky block stays on the same page as the start of whatever follows it, and the heading is already sticky. The result:
  - heading, introduction, prompt 1 and the opening of answer 1 now stay together;
  - every prompt stays with the first lines of its answer.

  The answers themselves are not wrapped and still break across pages normally. `width: 100%` is required: without it the block shrinks to fit its content, and justified lines stop short of the margin (measured with `pdftotext -bbox`, then fixed).
- **Review builder.** `scripts/build_chapter_review.py` gains `--test-pattern`. The default is `test*.py`, so the full suite still runs unless the option is given. The manifest now records `test_selection.mode` as `full` or `scoped`. A small test checks that the default is unchanged.
- **Validation for this pass.**
  - Standalone review built with `--test-pattern 'test_workbook06_*.py'`: scoped mode, 50 tests, 0 failures.
  - Integrated development build: `pass`, 28 pages. It used its registry `test_pattern` `test_workbook06_*.py` (50 tests).
  - Scoped tests: 77 passed (Workbook 06 plus the review-workflow tests).
  - All four validators passed, and `git diff --check` is clean.
  - The chapter gate was **not** rerun, because its QA step (`workbook_qa.py:503`) always runs the full suite. Its last result, `pass_with_warnings` at commit 3202b3f, covers the same content.
