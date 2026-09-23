# ML/LLM Study Workbooks

A collection of concise, visual, source-grounded study workbooks covering
machine learning foundations through modern LLM architecture, training,
inference, post-training/alignment, and research careers. Each workbook
is built to be a durable study guide: comprehensive enough to rely on,
concise enough to actually finish.

## Workbooks

| # | Directory | Title | Status |
|---|---|---|---|
| 01 | `workbooks/01-ml-foundations/` | Machine Learning Foundations | not started |
| 02 | `workbooks/02-ml-interviews/` | ML Interview Practice | not started |
| 03 | `workbooks/03-ml-systems-design/` | ML Systems Design | not started |
| 04 | `workbooks/04-llm-architecture/` | Modern LLM Architecture | **pilot — bootstrap sample drafted** |
| 05 | `workbooks/05-llm-training/` | LLM Pretraining and Distributed Training | not started |
| 06 | `workbooks/06-llm-inference/` | LLM Inference Engineering | not started |
| 07 | `workbooks/07-llm-post-training/` | LLM Post-Training and Alignment | not started |
| 08 | `workbooks/08-research-careers/` | ML/LLM Research Careers | not started |

Workbook 04 is the pilot. See `reports/bootstrap_report.md` for what
exists so far and the recommended next step.

## How each chapter is structured

Every chapter follows `shared/chapter-template.qmd`:

learning objectives -> why this matters -> mental model/analogy -> visual
overview -> technical core -> worked example -> compare and contrast ->
check your understanding -> common misconception -> applied exercise ->
interview lens -> chapter recap -> sources and further reading.

Comprehension questions are stored as structured records (not just prose)
in `workbooks/<id>/questions.yaml`, validated against
`shared/question-schema.yaml`.

## Source policy

- All sources are tracked in `sources/registry.yaml`, one entry per
  source, with an explicit `authority_type` (primary technical,
  implementation guide, visual reference, interview question bank,
  secondary summary, source-discovery index, or experiential account).
- `sources/coverage-matrix.yaml` records which sources back which
  workbook, and at what strength (primary / supporting / discovery).
- The full durable sourcing rules live in `AGENTS.md` — read it before
  drafting content. In short: synthesize and cite, never copy long
  passages or reuse a figure without a clear license, keep primary
  sources separate from commentary, and record when a source was last
  actually verified (don't backdate `last_verified`).

## Copyright and attribution policy

- Prose is written by this project, synthesizing multiple sources; it is
  not copied from any single source.
- Figures are original, generated from `figures/source/*.py`, and use
  only the shared palette in `config/visual-style.yaml`. Source figures
  from third parties are used only for inspiration/scoping, never
  reproduced, unless a source's license clearly permits reuse (tracked
  per-entry in `sources/registry.yaml`'s `license_or_reuse` field).
- Every substantive factual claim should be traceable to a
  `sources/registry.yaml` id, either via a `.bib` citation in the `.qmd`
  or a `source_ids` entry in a `questions.yaml` record.

## Development setup

Base tooling: `python3` (3.10), `git`, and a user-local `node`/`npm`
(via `nvm`). No system-wide `pip`/`uv` for the base Python (see
`reports/bootstrap_environment.md`), so everything under `scripts/` and
`figures/source/` is written against the Python 3.10 standard library
only — no PyYAML/jsonschema required for validation or figure builds.

The Quarto/Typst/Pandoc/poppler-utils rendering toolchain lives in a
dedicated, user-local conda environment (not on `PATH` by default):

```bash
source /opt/conda/etc/profile.d/conda.sh
conda activate ml-workbooks
```

This environment was created with
`conda create -n ml-workbooks -c conda-forge --override-channels quarto typst pandoc poppler`
using the read-only shared conda install at `/opt/conda` (new envs land
under `$HOME/.conda/envs`, so nothing system-wide was touched — see
`reports/bootstrap_report.md`). Activate it before running `make
workbooks` or `make render-sample`; it is not needed for `make validate`
or `make figures`, which are pure-Python.

- `scripts/_yaml_lite.py` is a small dependency-free loader for the
  restricted YAML subset used by every `.yaml` file in this repo (no
  PyYAML required).
- `figures/source/_svg_helpers.py` builds SVG figures directly (no
  plotting/diagramming library required).

If a full toolchain becomes available later, the optional dependency
group in `pyproject.toml` (`pip install -e ".[full]"`) upgrades to
PyYAML/jsonschema/pytest, but nothing in the repo requires it today.

## Build commands

```bash
make validate        # validate sources/registry.yaml, coverage-matrix.yaml, questions.yaml
make figures          # regenerate figures/rendered/*.svg from figures/source/*.py
make workbooks        # render every workbooks/**/*.qmd via Quarto (requires quarto on PATH)
make render-sample    # render + pdfinfo/pdftotext/pdftoppm-inspect the Stage-7 bootstrap sample
make check-links      # network check of every URL in sources/registry.yaml
make test             # run tests/ (unittest, no pytest required)
```

## Output locations

- `outputs/` — top-level bootstrap/whole-project PDF outputs.
- `workbooks/<id>/*.pdf` — per-workbook rendered PDFs (git-ignored; build
  products, not source).
- `workbooks/<id>/page-images/` — per-page PNGs from `pdftoppm`, used for
  the mandatory visual-inspection step before treating a PDF as complete
  (git-ignored).
- `figures/rendered/*.svg` — committed, since these are the actual
  original-figure deliverables, not disposable build output.

## Validation commands

```bash
python3 scripts/validate_registry.py     # registry + coverage matrix structure
python3 scripts/validate_questions.py    # question records against the schema
python3 -m unittest discover -s tests -v # full test suite
```

## Visual conventions

Defined once in `config/visual-style.yaml` and used by every figure
script:

- **blue** = stored information/state, **orange** = computation,
  **green** = trainable component, **purple** = device-to-device
  communication, **red** = bottleneck/failure/high cost, **gray** =
  frozen/inactive component.
- **solid** arrows = inference/ordinary data flow, **dashed** =
  training-only flow, **dotted** = optional/conditional flow.
- Vector-first (SVG), colorblind-safe, grayscale-legible, no 3D effects,
  no unexplained icons. Captions state what to notice, not just what is
  drawn.

## GPU and SLURM policy

Authoring, rendering, and validation in this project are CPU-only.
Compute inventory was recorded in `reports/bootstrap_environment.md` for
completeness (this host has 6 nodes / 48 H100 GPUs across several SLURM
partitions that all resolve to the same nodes), but no job is submitted
by this project unless a specific task genuinely benefits from GPU/SLURM
resources — which none of the current workbook-authoring work does.
