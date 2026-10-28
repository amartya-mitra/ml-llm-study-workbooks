# ML/LLM Study Workbooks

Study guides on how modern large language models are built and trained,
and how those ideas carry over to time-series forecasting. Each guide
explains one area through original diagrams, worked numerical examples,
and questions with full answers, so you can check your understanding as
you go.

The guides are written for learners and for practitioners who want a
careful, source-backed reference. They are not an introduction to
machine learning: you will get the most from them if you are comfortable
with matrix multiplication, basic probability, and the idea of training a
neural network by gradient descent.

## Choose a study guide

[Browse all study guides](https://amartya-mitra.github.io/ml-llm-study-workbooks/) on the reading site.

<!-- publication-catalog:start -->
| Study guide | What you will learn | Read |
|---|---|---|
| **Modern LLM Architecture** | How a decoder-only transformer turns tokens into a next-token prediction; attention variants and the KV cache; ways to reduce attention cost; mixture-of-experts; hybrid and looped designs; how to read a model report | [Read in browser](https://amartya-mitra.github.io/ml-llm-study-workbooks/editions/workbook-04-v1.0.0/04-modern-llm-architecture-workbook.pdf) · [Download PDF](https://github.com/amartya-mitra/ml-llm-study-workbooks/releases/download/workbook-04-v1.0.0/04-modern-llm-architecture-workbook.pdf) (69 pages) |
| **LLM Pretraining and Distributed Training** | Pretraining objectives and data; multi-token prediction; optimization and scaling laws; data, tensor and pipeline parallelism; training memory and communication; how to read a real training run | [Read in browser](https://amartya-mitra.github.io/ml-llm-study-workbooks/editions/workbook-05-v1.0.0/05-llm-training-workbook.pdf) · [Download PDF](https://github.com/amartya-mitra/ml-llm-study-workbooks/releases/download/workbook-05-v1.0.0/05-llm-training-workbook.pdf) (64 pages) |
| **From Language Models to Time-Series Foundation Models** (addendum) | Which LLM ideas carry over to forecasting models and which do not: patches instead of tokens, channels and covariates, architecture families, probabilistic outputs and losses, pretraining data and leakage, and how to read a model release | [Read in browser](https://amartya-mitra.github.io/ml-llm-study-workbooks/editions/addendum-04-05-tsfm-v1.1.0/addendum-04-05-tsfm.pdf) · [Download PDF](https://github.com/amartya-mitra/ml-llm-study-workbooks/releases/download/addendum-04-05-tsfm-v1.1.0/addendum-04-05-tsfm.pdf) (23 pages) |
<!-- publication-catalog:end -->

Both links give the current edition. **Read in browser** opens the PDF
in your browser's built-in viewer; some browsers or settings download it
instead. **Download PDF** saves the released file from GitHub. Earlier
editions, and checksums for confirming that a download is intact, are
listed in [Editions and verification](docs/editions-and-verification.md).

## Where to start

If you are new to the topic, read in this order:

1. **Modern LLM Architecture**: what the model computes.
2. **LLM Pretraining and Distributed Training**: how it is trained at
   scale.
3. **From Language Models to Time-Series Foundation Models**: how the
   same ideas apply to forecasting.

You do not have to read a guide from cover to cover. Chapters in the two
main guides begin with their learning objectives, so you can go straight
to the topic you need. The time-series addendum opens most modules with
a quick recap of the LLM ideas they rely on, so it can be read on its
own.

## How to study

Most chapters follow the same pattern:

1. **Read** the explanation and the diagram that goes with it.
2. **Follow the worked example**, which puts numbers through the idea
   step by step.
3. **Attempt the questions** before looking at any answers.
4. **Check your answers** in the chapter's answer key, which shows the
   full working and, for many questions, a common mistake to avoid.

Pay attention to what kind of number you are looking at. Most worked
examples use **illustrative** values, chosen to make the arithmetic
clear, or **derived** values, calculated from stated assumptions. These
show how a mechanism behaves, not how fast or how large a particular
system is. Numbers that a paper or report actually measured are
attributed to that source. When a chapter estimates memory or compute
from a formula, it says so and does not present the estimate as a
measurement. The time-series addendum labels every number as reported,
derived or illustrative.

## In progress and planned

<!-- in-progress:start -->
- **LLM Inference Engineering**: In progress, 3 of 7 chapters accepted
  so far. Covers prefill and decode, KV-cache memory, serving and
  scheduling, efficient attention kernels and inference parallelism,
  quantization, speculative decoding, and how to benchmark a deployment.
  It will be listed above once the complete guide is released.
<!-- in-progress:end -->

Further guides are planned on machine learning foundations, ML interview
practice, ML systems design, LLM post-training and alignment, and
research careers in ML and LLMs.

## Sources and corrections

The guides rest mainly on primary sources: the research papers that
introduced each method, official documentation, and, for a few
implementation details, source code pinned to a specific version.
Secondary summaries are used only as supporting material. Each chapter
ends with its sources. Where sources disagree, the guide says so
instead of picking a side quietly. Facts that change quickly, such as
which models exist or what a library does by default, are dated in the
text.

If you find an error, a broken link, or an explanation that does not make
sense, please [open an issue](https://github.com/amartya-mitra/ml-llm-study-workbooks/issues).
Mention the guide, its page number, and what you expected to see.
Corrections to a released guide are published as a new edition, and
earlier editions remain available.

<details>
<summary>Build or contribute</summary>

The guides are written in Quarto and typeset with Typst. The figures are
generated from Python scripts kept in this repository.

- [Building and contributing](docs/building-and-contributing.md): setup,
  build and validation commands, repository layout, source and figure
  policy.
- [Editions and verification](docs/editions-and-verification.md): every
  released edition with its page count, size and SHA-256 checksum.
- [Publication process](docs/publication-hygiene.md): how a guide goes
  from accepted draft to released PDF.
- [Browser reading site](docs/browser-reading.md): how the static reading
  site is built and deployed.
- [AGENTS.md](AGENTS.md): the durable rules for sourcing, accuracy and
  validation that apply to all contributions.

</details>
