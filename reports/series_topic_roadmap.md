# Series-Wide Topic Roadmap

Date: 2026-09-25
Machine-readable version: `config/series-topic-roadmap.yaml`

This report records where three cross-cutting topics — recurrent
depth/looped transformers, multi-token prediction (MTP), and
speculative decoding — will be taught across the ML/LLM Study
Workbooks series, and why. It is a decision record for future
drafting sessions, not a drafting plan in itself: none of the
primary-home locations below have been drafted yet, except where
noted (workbook 04 chapter 7's brief, deliberately shallow previews).

## Why a cross-workbook roadmap, now

All three topics touch more than one workbook: a topic like "looped
transformers" is an architecture choice (workbook 04's domain), has
training-time consequences (workbook 05), has inference-time cache and
latency consequences (workbook 06), and is a natural interview topic
(workbook 02). Without an explicit assignment, two failure modes are
likely: the same mechanism gets taught in full twice (wasted pages,
and a risk the two explanations drift apart), or it never gets a full
treatment anywhere because each workbook assumes another one will
cover it. This roadmap exists to prevent both failure modes before any
of workbooks 05/06/08's chapters are drafted.

## Topic 1: Recurrent depth / looped transformers

**Primary home:** Workbook 04, Chapter 8 (or a compact
emerging-architectures appendix) — full mechanism-level treatment.

**Secondary mentions:** Workbook 06, brief cache/latency-consequence
treatment. Workbook 04 Chapter 7 (drafted this session) already
includes a one-row, systems-oriented *preview* in its
architecture-to-systems consequence map — explicitly deferring the
full explanation to Chapter 8, per Chapter 7's own scope fence.

**Interview treatment:** Workbook 02, conceptual and calculation
questions (not yet drafted).

**Required concepts:** depth-wise weight sharing; distinct parameters
versus effective block applications; fixed loop counts; adaptive
halting; per-token recursion routing; the compute-versus-
parameter-storage tradeoff; sequence recurrence versus depth
recurrence; and KV-cache implications across repeated block
applications.

**Sources registered:** five primary papers, each independently
verified via full-text PDF download and extraction (not a search
snippet or a fetch tool's own summary) — Universal Transformers
(`src-38`, Dehghani et al. 2018 — the earliest source, defining
depth-wise weight sharing and adaptive per-position halting), Geiping
et al.'s recurrent-depth paper (`src-39`, 2025 — the clearest source
for the compute-vs-parameter-storage tradeoff at scale), Mixture-of-
Recursions (`src-40`, Bae et al. 2025 — per-token recursion routing
*and*, specifically, the KV-cache-implications concept via its own
"recursion-wise caching vs. recursive sharing" comparison), Ouro
(`src-41`, Zhu et al. 2025 — a second large-scale looped-pretraining
result), and the Nanbeige4.2-3B technical report (`src-42` — a
*fixed*, not adaptive, loop count in a shipped, open-weight model).
Three expert-explanatory/visual-reference sources (`src-46`/`src-47`/
`src-48`, all by Sebastian Raschka) were also verified via WebFetch and
registered — useful for framing and figure-scoping, explicitly *not*
treated as a substitute for the five primary papers on any specific
mechanism claim.

**Required distinctions:** depth recurrence (looping the same block
over the same tokens) is not sequence recurrence (an RNN's or a
Mamba/SSM's token-by-token hidden state, already taught in Chapter 6
via `src-37`) — both get called "recurrent" casually, but they are
different mechanisms and must not be conflated. An adaptive per-token
halting/routing mechanism (Universal Transformers' ACT, Mixture-of-
Recursions' router) is not the same design as a fixed loop count
applied uniformly to every token (Nanbeige4.2-3B) — check which a
given model actually uses before describing it. And critically: looped
weight sharing reduces *distinct stored parameters*; it does **not**
reduce the compute of the repeated block applications, and it does
**not** automatically reduce or share KV-cache/recurrent state across
passes unless the specific architecture says so.

**Standing caveat:** treat any claim about an undocumented proprietary
model's architecture as unconfirmed unless an official technical
source from that model's own developer exists. This session found no
official OpenAI technical source for "GPT-6 Astra." The two Raschka
pieces that discuss it (`src-46`/`src-47`) themselves present the
looped-transformer claim as third-party-reported speculation, not
OpenAI's own confirmed disclosure — this hedge must survive into any
future workbook text that mentions Astra, not be upgraded to fact.

## Topic 2: Multi-token prediction (MTP)

**Primary home:** Workbook 05 (LLM Pretraining and Distributed
Training), in a pretraining-objectives chapter — full training-time
mechanism treatment. Not yet planned in chapter-level detail.

**Architecture bridge:** Workbook 04 Chapter 8, a concise
emerging-architecture note (not yet drafted). Workbook 04 Chapter 7
(drafted this session) adds only a short cross-reference stating that
an auxiliary MTP module *may* become an inference-time draft
mechanism — not a main architecture row, and not a teaching of the
mechanism itself.

**Inference bridge:** Workbook 06, brief treatment of an MTP module's
use as an internal drafting mechanism for speculative decoding. Not
yet drafted.

**Required concepts:** predicting multiple future offsets; auxiliary
heads or modules; loss construction; independent versus causal-chain
MTP designs; training-only use; and parameter/compute implications.

**Sources registered:** Gloeckle et al.'s original MTP paper
(`src-43`, verified via full-text extraction), which defines the
*independent*-heads design (n independent output heads on a shared
trunk, one auxiliary loss per future offset, only the next-token head
kept at inference). DeepSeek-V3 (`src-33`, already registered and
deeply verified in Chapter 6) is the primary source for the
*causal-chain* design — its own MTP module conditions each predicted
offset on the previous module's output. These are two materially
different MTP implementations, not two names for one mechanism; the
registry entries for both state this explicitly. Raschka's MTP
architecture-gallery page (`src-49`, verified via WebFetch) is an
expert-explanatory source for the training-vs-inference-use
distinction and for scoping three additional models (Qwen3-Next, Step
3.5 Flash, Nemotron 3 Super) that reportedly use MTP variants — those
three model-specific claims were **not** independently verified this
session and must be checked before Workbook 05/06 relies on them for
anything beyond "this source says so."

**Required distinction:** MTP is a training-time objective/module
design choice. It is **not** itself synonymous with speculative
decoding, an inference-time serving technique. An MTP module *can* be
repurposed as a draft source for speculative decoding, but does not
have to be — having MTP heads does not imply a model is served with
speculative decoding.

## Topic 3: Speculative decoding

**Primary home:** Workbook 06 (LLM Inference Engineering), in an
inference-serving-techniques chapter — full algorithmic and systems
treatment. Not yet planned in chapter-level detail.

**Architecture mention:** Workbook 04 only adds a short cross-reference
where MTP is introduced (Chapter 7, drafted this session) — the
algorithm itself is explicitly not taught in Workbook 04.

**Interview treatment:** Workbook 02, systems and tradeoff questions.
Not yet drafted.

**Required concepts:** proposal; verification; acceptance; rejection
and resampling; independent draft models; self-speculative methods;
MTP-assisted drafting; acceptance rate; draft cost; batch-size effects;
hardware and serving-engine dependence; latency versus throughput; and
lossless-distribution guarantees under the relevant algorithmic
assumptions.

**Sources registered:** the two co-foundational papers, both verified
via full-text PDF extraction — Leviathan et al. (`src-44`, "Fast
Inference from Transformers via Speculative Decoding," confirming its
own "without changing the distribution" framing) and Chen et al.
(`src-45`, "Accelerating Large Language Model Decoding with
Speculative Sampling," confirming its "modified rejection sampling
scheme which preserves the distribution of the target model" and its
acceptance-rate framing). These were published within about two months
of each other in early 2023 and are registered as co-foundational —
Workbook 06 should credit both by name, not present one as derivative
of the other. No implementation-companion source (e.g. a specific
serving engine's documentation) has been registered yet; the roadmap
records this as a placeholder to add *when* Workbook 06 is actually
drafted, per the instruction to use such a source as an implementation
companion, never as the algorithm's sole source.

**Required distinctions:** speculative decoding is an inference-time
serving technique — it does not change training and is not itself an
architecture. An MTP module is only *one* possible source of draft
tokens; an independent smaller draft model, or a self-speculative
method drafting from the same model's own earlier layers/state, are
others. The lossless-distribution guarantee holds under the specific
algorithmic assumptions each paper states (matching sampling
procedures / a correct rejection-sampling implementation) — it is not
an unconditional property that survives any implementation.

**Standing caveat:** do not cite vendor serving-engine marketing claims
as neutral, hardware-independent performance evidence — acceptance
rate, draft cost, batch size, and hardware all affect the realized
speedup.

## What this roadmap does not do

It does not draft any section of workbooks 05, 06, or 08. It does not
add mechanism-level teaching content to Workbook 04 beyond Chapter 7's
own deliberately shallow preview row and short cross-reference (both
consistent with Chapter 7's Stage 7 instruction that the looped-depth
row is "a systems-oriented preview only" and that MTP/speculative
decoding get "a short cross-reference," not a main architecture row).
It does not resolve every open question about these three topics —
three papers named only in `src-47` ("Beyond Parameters...", "SMELT...",
"Full-bandwidth transformer") remain unverified candidates, and no
implementation-companion source for speculative decoding has been
selected yet. Both gaps are recorded in `config/series-topic-roadmap.yaml`
and `sources/registry.yaml`, not silently dropped.
