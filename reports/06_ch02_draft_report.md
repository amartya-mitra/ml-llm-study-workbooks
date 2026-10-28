# Workbook 06, Chapter 2 — draft report

**Chapter:** KV-Cache Memory: Capacity, Paging, Prefix Reuse, and Eviction
**Date:** 2026-10-28
**Status:** `drafted_pending_human_review`. Chapter 1 is `accepted_frozen` (commit 6504798); Chapters 3–7 remain `scaffold_only`.
**Builds:** development and review only. No canonical PDF, no release candidate, no GPU, SLURM or model download.

## Chapter 1 acceptance (recorded first, separate commit)

The accepted review PDF is `outputs/_development/06-llm-inference/chapter-01-review/06-llm-inference-ch01-review.pdf`: 14 pages, 346,478 bytes, sha256 `675e64ee23a4ac5060605212137aedec054e0cbf365a51cb4c8079c580f5e8de`, source commit `7e12422`. It was verified byte-for-byte before the acceptance was recorded.

- **Status registry:** `accepted_frozen`, with an acceptance block holding the path, hash, byte count, page count and source commit.
- **Contract:** `allowed_paths: []`, with the Chapter 1 chapter, solutions, worked-example and figure files listed as frozen.
- **Content:** no Chapter 1 content changed. Chapter 2 imports Chapter 1's worked example and `_common.py` read-only.

## Sources, reading depth and pins

- **src-73 (PagedAttention):** targeted full-text read of Sec. 3, 4.2–4.5 and 7.2–7.3.
- **src-77 (SGLang):** Sec. 3, RadixAttention. Kept to a bounded mechanism comparison.
- **src-25 (Mistral 7B):** re-read from the arXiv v1 PDF (Sec. 2) before any sliding-window or rolling-buffer claim. The registry entry, previously web-search-verified only, was updated. The paper's own inconsistency is preserved: its text says W = 3 for Fig. 2, while the caption says W = 4.
- **src-82 (vLLM v0.32.0, commit 5df63a72):** read with file:line locators, which are recorded in the registry notes and the ledger. The prefix-caching design doc, the KV cache manager, the partial-hit copy-on-write path, sliding-window block freeing, scheduler preemption and the cache-budget calculation were all checked. Optional KV-offloading connectors were not examined, and the chapter says so.
- **src-10 (scaling book):** shared-cache storage versus step time; the quotation is exact.
- **Paper versus engine:** the 2023 paper offers swap or recompute, while vLLM v0.32.0 recomputes only. This drift is stated in the chapter and recorded in the src-73 notes.

## Worked example

The inputs are illustrative and reuse Chapter 1's model and device: 128 KiB per token, 16.06 GB of weights, 80 GB of memory. They add u = 0.92, a 4 GiB runtime headroom and 16-token blocks. All results are derived:

- **Cache budget:** 53.25 GB = 49.59 GiB, or 25,391 blocks.
- **Concurrency:** 99 sequences of 4,096 tokens. The remaining 47 blocks hold one more sequence of up to 752 tokens; 753 tokens would not fit.
- **2,048-token sequences:** 198 fit, or 182 with 8 GiB of headroom.
- **Reservation versus paging:** 30.9% versus 99.4% of allocated slots in use, for a chosen workload of eight requests.
- **External fragmentation:** a toy arena with 1.5 GiB free in 512 MiB gaps refuses a 768 MiB contiguous request.
- **Toy lifecycle:** prefix sharing, reverse free order, idle cached reuse, eviction on reallocation and one copy-on-write. Tests replay it with invariants, including a guard against releasing a shared block early.
- **Radix tree versus full-block hashing:** in the toy, the tree reuses 7 and 6 tokens where hashing reuses 4 and 4.
- **Prefix sharing at scale:** 4,096 blocks shrink to 2,112, raising capacity from 198 to 395 requests, but each decode step still reads 8 GiB.
- **Architecture variants:** a looped model needs 256 KiB per token if each pass keeps its own cache; a sliding window cuts the cache 8× at 32k tokens.

## Audit findings and dispositions

Four bounded, read-only audits ran in parallel: sources and implementation; capacity and lifecycle; pedagogy and Q&A; rendered layout. None found a blocker. Every required finding was resolved; the full records are in `outputs/_development/06-llm-inference/chapter-gate/ch02-*-audit.json`.

### Required findings (all resolved)

- **Notation:** `M_KV` was used both for the logical size and for the budget. The budget is now `M_budget`. The recap now defines L, H_kv, d_head, b_kv and GB/GiB.
- **Lifecycle trace:** row 2 omitted P3's reference count, and "R1 writes 3" was ambiguous (P4 was never shown). Both are fixed.
- **Q3 counterfactual:** the claim that R4 overwrites R2 contradicted the trace order. I simulated the faulty allocator to correct it. The free queue becomes 5 6 7 4 2 1 0, so a six-block request arriving while R2 runs would take shared blocks. After R3, the queue holds stale P0 and P1 entries (6 7 4 2 3 1 0). The chapter, answer key and question record now describe exactly this.
- **Comparison table:** it credited contiguous reservation with provider-set prefix reuse. That column now says "none", and the caption attributes the sharing correctly.
- **Table layout:** two tables were cramped and hyphenated. Their cells were shortened.

### Optional findings resolved

- vLLM budget now includes the CUDA-graph estimate.
- The logprob-stability citation now uses `README.md:212-214`, and the batch-shape wording was softened.
- The KV-offloading exclusion is now stated.
- The bitwise-identity caveat for recomputation was added.
- Internal fragmentation now has a single definition.
- Workbook 04 back-references were added.
- Toy simplifications are labelled.
- A test for the last-prompt-token cap was added.
- The copy-on-write copy count is now derived in code rather than hard-coded.
- Equation units are stated.
- Two figure-label issues were fixed: the wrapped '?' and the C label.
- The math spacing problem was fixed.
- A page-8 gap was removed. Figures were reordered and the "Full solutions" lead-in made sticky, bringing the PDF back to 12 pages.

### Accepted as-is

- **Page 5:** about a quarter page is blank before Figure 2, a figure keep-together.
- **Figure text:** prints at about 8 pt, the same as accepted Chapter 1.
- **Section numbering:** the standalone build numbers the chapter's sections 1.x.
- **Bibliography:** the Mistral entry's format, and the missing years on two entries, were left unchanged because those entries are shared with frozen, published workbooks.

## Tooling change

The chapter gate always ran the full suite. I added `--test-pattern` to `scripts/workbook_qa.py` (chapter mode) and `scripts/chapter_gate.py`.

- **Default:** the full suite (`test*.py`), unchanged.
- **Scoped runs:** labelled `mode: scoped` in the QA summary and gate report, and printed in the gate summary.
- **Zero-test guard:** a pattern that discovers no tests, or that hits errors, fails the gate.
- **Tests:** a workflow test checks the defaults and the zero-test rule.

The existing workflow and factory tests (82) pass.

## Validation (fresh, scoped)

- **Review build** (`build_chapter_review.py --test-pattern 'test_workbook06_*.py'`): scoped, 80 tests, 0 failures, 12 pages.
- **Chapter gate** (`--test-pattern 'test_workbook06_*.py'`), run fresh after all corrections: `pass_with_warnings`.
  - Its scoped suite is 80 tests with no failures; its chapter modules run 35 tests.
  - All four audit records are ok.
  - Its only warning is `text_leakage`, from the pinned vLLM commit URL and a free-queue table cell ("5 6 7 4 2 3 1 0") that extracts as 56742310. Both are benign.
- **Validators:** `validate_registry`, `validate_questions`, `validate_chapter_contract` and `validate_publication_hygiene` all OK. `git diff --check` is clean.
- **Full suite:** not run.

## Limitations

- No number is measured. Runtime headroom and allocator behaviour are illustrative.
- The toy pool and radix tree illustrate mechanisms; they are not engine state.
- In vLLM v0.32.0, KV-offloading connectors and hybrid-model paths were not examined.
- The audits were not rerun after the correction pass. The main agent verified each fix through tests, the rebuilt PDF, page-by-page inspection and a fresh gate run.

## Correction pass 1 (Question 2 wording)

This was a narrow correction after review. No numbers changed.

**Question 2.** The question now asks whether a sequence with KV entries for 48 processed tokens can process an already-selected next token and append its KV entries. It previously asked whether the sequence could "generate its next token". The answer, the question record and the common trap now keep selection apart from processing and storage:
- processing token 48 produced the logits from which token 49 was selected;
- selecting token 49 stores nothing;
- processing token 49 writes its K/V and produces the logits for token 50, and that needs a fourth block, so the forward pass waits.

**Related wording.** Two passages were reworded to make the same distinction:
- the preemption sentence ("the keys and values of the tokens every running sequence must process next");
- the lifecycle lead-in ("R1 processes 3 more tokens, whose keys and values fill P2 and take P4").

The retained-length definition is unchanged.

**Validation.**
- **Test:** a new scoped check covers the prompt, the answer's selection-versus-storage phrases, the block arithmetic and the question-registry record.
- **Review build:** scoped, 81 tests, 0 failures, 13 pages.
- **Page comparison against the previous build:** pages 1–5 and 10 are byte-identical. Pages 6–9 and 11–13 changed, and all of them were inspected.
- **Audits and gate:** not rerun.
