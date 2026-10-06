# Addendum 04-05 (TSFM): internal audit report and dispositions

Status of the addendum: `drafted_pending_human_review`.
Date: 2026-10-06.

## How this audit was performed (read this first)

The plan called for four read-only subagent auditors in two waves. Both
Wave 1 launches (source-auditor, technical-auditor) were **rejected by the
Agent process guard** (process count 28 at its pre-launch cutoff of 28).
**Zero auditors were admitted.** No retry, reset or workaround was made, and
no further Agent call was issued. By explicit instruction, the four audits
were replaced by **four role-separated internal audit passes in the parent
session** (source, technical, visual, consistency), run over the same
17-page PDF and the same source state, with corrections applied only after
all four passes.

This is **not equivalent to four independent subagent audits**: the same
agent that drafted the text also audited it. The independent check that
remains is the human review of the integrated review PDF.

Limits: no source PDF or web page was re-opened in this pass; source
checks rely on each registry entry's `expected_use` and `access_status`.
Frozen-workbook checks used targeted reads of Workbook 04 Chapters 1, 2, 6
and Workbook 05 Chapters 1 to 3.

## Findings and dispositions

Severity: blocker, required, recommended, no-action. Confidence: H/M/L.

### Pass 1: source audit

| ID | Sev. | Location | Finding | Evidence | Disposition and correction | Conf. |
|---|---|---|---|---|---|---|
| S1 | required | Module 5, recap (PDF p.10) | Recap sentence "Fine-tuning continues training ... baseline" asserted LLM-workbook content that those chapters do not teach | grep of WB05 Ch.1 to 3 and WB04 Ch.1 found no fine-tuning treatment | **Accepted.** Sentence removed; fine-tuning is defined where used (Module 5 section 5.4) | H |
| S2 | recommended | Front matter (p.1) | 2026 preprints (Moirai 2.0, TiRex-2) not flagged as changeable | registry notes: time-sensitive preprints | **Accepted.** Qualifier added | H |
| S3 | recommended | Module 3 table (p.7), Moirai 2.0 row | Class (i) is inferred from the paper's "recursive" wording, not from a described feedback loop | registry gap G8 | **Accepted.** Cell now says "(i), from the paper's 'recursive' wording; details not covered here"; ledger statement updated | M |
| S4 | recommended | Claim ledger, claim-tsfm-inputs-001 | Recap statements (feed-forward sublayer, RMSNorm/RoPE as conventions) lacked a ledger statement | WB04 Ch.1 lines 25, 179; Ch.2 | **Accepted.** Statement extended | H |
| S5 | recommended | Module 5 recap, scope report | Scope report describes WB05 Ch.3 as "single-axis fits (one variable varied at a time)"; that wording is not in Ch.3 | grep found no such text; Ch.3 says fitted relation, not universal law, loss is not capability | **Accepted.** Recap uses the phrases Ch.3 actually contains; divergence recorded here and in the ledger note | H |
| S6 | no-action | TimesFM-3 (M5 p.11, M6 p.13) | 330M vs 20-layer/1280/16-head discrepancy preserved, no reconciliation, no parameter estimate | text read; test asserts no 12 x 1280 arithmetic | **No action.** Meets the requirement | H |
| S7 | no-action | All modules | Moirai-MoE absent; documentation-only releases carry "doc:"/vendor labels and "as of October 2026"; no rankings | tests and text read | **No action** | H |
| S8 | no-action | Modules 1, 5 | Moirai sampling-cap value/rule, PatchTST configurations, Chronos-2 patch length, Moirai 2.0 first-30% passage remain unverified or not re-read | registry access_status | **No action; kept as stated limits.** Cap not stated; 512/16/8 is labeled illustrative and not attributed; first-30% is stated as the paper's own design choice and recorded in the ledger as not independently re-read | M |

### Pass 2: technical audit

| ID | Sev. | Location | Finding | Evidence | Disposition and correction | Conf. |
|---|---|---|---|---|---|---|
| T1 | required | Module 1, section 1.3 (p.3) and answer 6 (p.14) | "per-token work falls by about k" is ambiguous: per-token cost is unchanged, total work falls | cost per token is independent of token count for the linear parts | **Accepted.** Reworded to total work over all tokens | H |
| T2 | recommended | Module 2 worked example (p.6) | 1024 vs 4096 assumes full attention | a causal mask halves both counts alike | **Accepted.** Assumption stated | H |
| T3 | recommended | Module 2, section 2.4 (p.5) | "a second kind marks unknown future" is vague | scope: masks for "unknown future" are model-specific | **Accepted.** Reworded to "some designs also mark positions whose future values are unknown" | M |
| T4 | no-action | W1 to W6 and answers | Recomputed independently by the tests: scale 220/12, bin ids, N_p 6 and 3, 8 lag tokens, 64 vs 32 patches, 576 numbers, 1024/4096, ceil passes 2/8/256/1, pinball 0.2/0.5/0.3, 2.7 vs 0.3, CE 2.303, shares 0.5/0.375/0.125, 500M/375M/125M | 90 scoped tests pass | **No action** | H |
| T5 | no-action | Module 4 | Mass vs density (log w relation), marginal fan vs joint paths, point panel labeled as median of an example, loss on scaled values | text and figure read | **No action** | H |
| T6 | no-action | Module 3 table | Chronos-2 listed as class (ii) (future placeholders, one pass, quantile head): the (ii)/(iii) boundary is a judgment; PatchTST is (iii) | scope section 13 | **No action.** Boundary stated in text (placeholders versus a head over the horizon) | M |
| T7 | no-action | LLM analogies | Recaps mark where the analogue is exact, adapted, time-series-specific, or absent (MTP default does not carry over; encoder families not in the LLM workbooks) | text read | **No action** | H |

### Pass 3: visual audit (all 17 pages, full resolution)

| ID | Sev. | Location | Finding | Disposition | Conf. |
|---|---|---|---|---|---|
| V1 | required | Question lists, all modules | A first attempt at keeping question lists together collapsed each list into one paragraph | **Accepted and fixed** (wrapper removed; global keep-together rule used instead) | H |
| V2 | required | pp.7 to 9 | Large blank areas where figures/tables did not fit | **Accepted.** Figure 3 resized, Figure 4 moved after Table 5; remaining gap on p.8 (about 35%) is accepted because Figure 4 cannot fit there | H |
| V3 | required | Module 6 synthesis table | Table split across a page with an orphan fragment | **Accepted.** Split into two tables (paper-backed; documentation-only) with their own captions | H |
| V4 | required | p.17 | Two-line orphan of the last answer on its own page | **Accepted.** Two answers tightened; key now ends on p.16, bibliography on its own page | H |
| V5 | required | Module 5 recap (p.10) | Bullets rendered inline ("- Same idea") after sentence removal left no blank line | **Accepted and fixed;** regression test added for every list in all modules | H |
| V6 | recommended | Figure 4 | Component annotation overlapped the density curve | **Accepted.** Moved into the panel's caption line | H |
| V7 | recommended | Figure 1, panel B | Dashed padded patch label is dark on white while others are white on green | **No action.** Intentional: dashed outline means padded; label stays readable | M |
| V8 | no-action | Whole PDF | No clipping, overlap or broken glyphs; equations render; headings complete; numbering and cross-references resolve; there is no table of contents by design (TOC is off in the project setup); colors and legends consistent with the project palette | **No action** | H |

### Pass 4: consistency audit

| ID | Sev. | Location | Finding | Disposition | Conf. |
|---|---|---|---|---|---|
| C1 | no-action | Recaps M1 to M6 | Checked against WB04 Ch.1 (embedding, residual stream, feed-forward), Ch.2 (RMSNorm, RoPE), Ch.6 (the ten-item checklist, reproduced in order), Ch.8 (depth vs sequence recurrence); WB05 Ch.1 (mixing weights, separation, tokenizer comparability, multi-stage), Ch.2 (MTP, teacher forcing, capital P in the next-token loss), Ch.3 (fitted laws, capability caveat) | **No action** (S1, S5 were the only deviations and are fixed) | H |
| C2 | no-action | Notation | Symbols follow the approved table; `E` never used; `P` kept for patch length with lowercase `p(.)` for probability; WB05's `w_i` re-indexed as `w_j` in the table but the recap uses `w_i` because it quotes WB05's own symbol | **No action** (stated in the recap) | M |
| C3 | no-action | Terminology | "source type" used instead of WB05's "configured/observed/derived"; "multi-patch prediction" for the TSFM mechanism; "class (i)/(ii)/(iii)" used consistently | **No action** | H |
| C4 | no-action | Questions, answers, cross-references | 34 questions, 34 keys, 34 question records; each key links to its "Check your understanding" section; answers recomputed | **No action** | H |
| C5 | no-action | Scope | Six modules, user-specified titles, no representation-depth module, no Moirai-MoE; 17 pages against the 24-page ceiling | **No action** | H |
| C6 | no-action | Leakage | No source ids, paths, filenames, revision history or build metadata in learner text; the shared checker's "placeholder" pattern is exempted only for the ordinary technical word | **No action** | H |

## Verification of corrections

All corrections were applied after the four passes, in the parent session.
The review PDF was rebuilt with stale page renders cleared, the scoped
tests were rerun (91 tests), the PDF text scan was rerun, and every page
was inspected again at full resolution.
