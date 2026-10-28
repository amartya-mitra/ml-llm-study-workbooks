# Workbook 06, Chapter 3 — draft report

**Chapter:** Serving and Scheduling: Continuous Batching, Chunked Prefill, and Disaggregation
**Date:** 2026-10-28
**Status:** `drafted_pending_human_review`. Chapters 1–2 are `accepted_frozen` (Chapter 2 acceptance in commit 6d4235c); Chapters 4–7 remain `scaffold_only`.
**Builds:** development and review only. No canonical PDF, no RC, no GPU, SLURM or model download.

## Chapter 2 acceptance (separate commit, 6d4235c)

The accepted review PDF is `outputs/_development/06-llm-inference/chapter-02-review/06-llm-inference-ch02-review.pdf`: 13 pages, 258,003 bytes, sha256 `d3417eab33a702fbcb16239ee04ea118835aa7048006d6f4816d0608dd5ead73`, source commit `4a5d05d`. Its identity was verified before the acceptance was recorded.

- **Status:** `accepted_frozen`, dated 2026-10-28. The acceptance block records the review PDF, its hash, byte count, page count and source commit.
- **Contract:** frozen paths list the chapter, solutions, worked example and figures.
- **Accepted layout:** the two-entry bibliography continuation on page 13.
- **Content:** no Chapter 2 content changed.

## Sources and reading depth

| Source | What was read |
|---|---|
| src-74 Orca | Sec. 3 (C1, S1, S2), the Sec. 4 scheduler (iteration-level FCFS, max batch size) and Sec. 4.2 (max_tokens reservation) |
| src-75 Sarathi-Serve | Sec. 1, 2, 3.2, 4.1–4.3 and 5.4.1; the registry was updated to record 5.4.1 |
| src-76 DistServe | Sec. 1, 2.1–2.3, 3.3 and 4 |
| src-73 PagedAttention | Sec. 4.5 (preemption order) |
| src-77 SGLang | Sec. 3 (starvation caveat) |
| src-10 | The "Inference" chapter's discussion of interleaved and disaggregated serving |
| src-82 vLLM v0.32.0 (commit 5df63a72) | See locators below |

The src-82 locators are recorded in the registry and the ledger:

- `config/scheduler.py:40-77, 134, 159-165`
- `engine/arg_utils.py:695, 2900-2960, 2987-2994` (the effective chunked-prefill default comes from `model_config.is_chunked_prefill_supported`)
- `v1/core/sched/scheduler.py:132-136, 657-659, 795-803, 899-923, 1155-1169, 1345`
- `docs/features/disagg_prefill.md:1-19`

KV-connector transfer internals were not examined.

The source disagreement is preserved in both directions. Sarathi-Serve argues that chunking keeps token gaps low and that re-reads cost little because chunked attention prefill stays compute-bound. DistServe argues that chunking trades TTFT for TPOT, does not remove interference, and causes quadratic re-reads.

## Worked example

The trace is synthetic and the outputs come from a deterministic simulator. Nothing is measured.

**Inputs:**
- **Requests:** A (0 ms, 512 prompt, 8 out), B (0 ms, 256, 4), C (12 ms, 1,024, 4) and D (30 ms, 128, 6).
- **Step cost:** $t = 5 + 0.015\,P + 0.2\,D$ ms. It omits chunk re-reads, which is stated in the chapter.
- **Budgets:** 2,048 tokens unchunked, 256 tokens chunked, at most 4 sequences.
- **SLO:** TTFT ≤ 40 ms and TPOT ≤ 10 ms, both required.
- **Throughput:** output tokens over the window from first arrival to last completion.
- **Disaggregation:** 25 GB/s effective bandwidth plus 2 ms fixed overhead per transfer, no link contention, a decode device with room for every cache, and requests joining the decode device at a step boundary.
- **Static batching:** finished requests leave without padding, which is kinder than Orca's description.

**Results** (tok/s · C wait/TTFT · B TPOT · worst gap · good requests · goodput per device):

| Policy | tok/s | C wait / TTFT (ms) | B TPOT (ms) | Worst gap (ms) | Meet SLO | Goodput per device |
|---|---|---|---|---|---|---|
| Static | 215 | 41.5 / 63.8 | 5.4 | 5.4 | A, B | 19.5 |
| Continuous | 304 | 4.5 / 25.3 | 11.4 | 20.8 | A, C, D | 41.4 |
| Chunked (256) | 226 | 14.7 / 58.6 | 9.2 | 9.2 | A, B | 20.5 |
| Disaggregated | 280 | 4.5 / 24.9 | 6.4 | 14.8 | all | 25.5 (51.0 over two devices) |

- **Throughput gain worsening a latency metric:** continuous batching raises throughput, but pushes B's TPOT from 5.4 to 11.4 ms.
- **KV transfer:** C's transfer takes 7.37 ms (128 MiB), yet its first gap is 14.8 ms.
- **Preemption:** for A after 5 selected tokens, 516 KV entries are freed and the resume is a 517-token pass costing 12.76 ms, against 5.2 ms for a normal decode step.
- **Applied exercise (512-token budget):** worst gap 13.05 ms, C TTFT 37.8 ms, 284 tok/s, A, C and D good, 38.8 req/s.

## Tests

- `tests/test_workbook06_ch03_worked_examples.py` (25 tests):
  - no step overlap, and the cost model holds on every step;
  - nothing is processed before it arrives;
  - token budgets and sequence limits hold, including the 512-token run;
  - prompts complete in full, and each request needs n − 1 decode steps because its last selected token is never processed;
  - selection comes before processing;
  - static batching admits nothing mid-batch;
  - iteration-level FCFS order holds, and decodes come before prefills within a step;
  - disaggregated requests wait for their transfer and join at the first step boundary;
  - the metric and aggregate arithmetic is correct;
  - the teaching contrasts hold;
  - the prose and answer numbers match the data, and the layout guards are present.
- `tests/test_workbook06_ch03_figure_invariants.py` (10 tests): every work item is drawn as a bar; dots, arrivals and transfers are drawn correctly; stacked step parts sum to step durations; and the committed SVGs match the scripts' current output.

## Audit dispositions

Four bounded, read-only audits ran in parallel (sources, technical, pedagogy, visual). There were no blockers, and all 12 required findings were resolved. The full records are in `outputs/_development/06-llm-inference/chapter-gate/ch03-*-audit.json`.

| Audit | Finding | Resolution |
|---|---|---|
| Source | Sarathi's counter-argument on chunk re-reads was missing. | Added. |
| Source | The vLLM chunked-prefill default was stated too strongly. | Now "for models that support it", with `arg_utils` locators. |
| Source | The src-75 reading depth did not record Sec. 5.4.1. | Registry updated. |
| Technical | The cost model omits chunk re-reads, without saying so. | The limitation is now stated in the chapter. |
| Technical | The static model is kinder than Orca's description. | Labelled in the worked-example inputs. |
| Technical + pedagogy | Throughput did not name its token type. | Now says output tokens. |
| Pedagogy | Answer 3 misattributed the evidence for each source. | Rewritten, and the question record updated. |
| Pedagogy | The table said disaggregation "protects TTFT and gaps". | Now "TTFT, later gaps", with an explanation in the caption. |
| Visual | The subtitle hyphenated, and a space was missing in a callout. | Fixed (see the builder change below). |

Optional items applied: FCFS and decode-first tests; a test for the 512-token exercise; first-boundary joining; stated disaggregation assumptions; goodput type; TTFT start event; budget-sharing rule; the five-chunk split; preemption cache-hit caveat; running-list order; D's numbers attributed to the simulated schedule; the exercise asking for waiting time and goodput; units; terminology; removal of process wording; table widths; caption wording.

Optional items accepted unchanged: about 8 pt figure labels (the same standard as Chapters 1–2), and a sparse lower part of page 4 where Figure 2 is kept whole.

## Tooling change

`scripts/build_chapter_review.py` now puts a markdown hard line break before the chapter title in the review subtitle, so long titles break between words instead of hyphenating. This affects only future review builds. The accepted Chapter 1 and 2 review PDFs are not rebuilt and are byte-identical.

## Validation (fresh, scoped)

- **Review build** (`--test-pattern 'test_workbook06_*.py'`): scoped, 106 tests, 0 failures, 12 pages.
- **Chapter gate** (same pattern, run after all corrections): `pass_with_warnings`.
  - Scoped suite: 106 tests, 0 failures or errors.
  - All four audit records are ok.
  - The only warning is `text_leakage`, from the pinned vLLM commit URL in the bibliography.
- **Scoped tests:** 135 Workbook 06 and review-workflow tests pass.
- **Validators:** `validate_registry`, `validate_questions`, `validate_chapter_contract` and `validate_publication_hygiene` all OK. `git diff --check` is clean.
- **Full suite:** not run.

## Limitations

- Nothing is measured. The cost model, trace, bandwidth and overheads are illustrative.
- The re-reads of earlier chunks are not modelled.
- There is no queueing theory and no autoscaling.
- KV-connector transfer internals in vLLM v0.32.0 were not examined.
- The audits were not rerun after corrections. Fixes were verified by tests, rebuilds, page inspection and a fresh gate run.
