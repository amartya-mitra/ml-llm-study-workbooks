# Building and contributing

Technical reference for building the study guides from source and for
contributing to them. Readers who only want the PDFs need none of this;
see the [README](../README.md). The durable rules for sourcing,
accuracy, pedagogy and validation are in [AGENTS.md](../AGENTS.md):
read them before drafting content.

## Repository layout

| Path | Contents |
|---|---|
| `workbooks/<id>/` | One directory per guide: `index.qmd`, `chapters/`, `solutions/`, `questions.yaml`, chapter contracts and claim ledgers. Directories for planned guides (`01-ml-foundations`, `02-ml-interviews`, `03-ml-systems-design`, `07-llm-post-training`, `08-research-careers`) are empty placeholders. |
| `figures/source/` | Python scripts that generate every figure. |
| `figures/rendered/` | The generated SVGs (committed; they are deliverables, not disposable output). |
| `sources/registry.yaml` | One entry per source, with `authority_type`, `expected_use`, `license_or_reuse` and `last_verified`. |
| `sources/coverage-matrix.yaml` | Which sources back which guide, and how strongly (primary / supporting / discovery). |
| `config/chapter-status-registry.yaml` | Chapter status (`workbooks:`) and publication records (`publications:`); the source of truth for what is accepted and released. |
| `config/visual-style.yaml` | The shared figure palette and line conventions. |
| `shared/` | The chapter template and the question schema. |
| `scripts/` | Build, validation and gate scripts. |
| `tests/` | `unittest` tests (no pytest needed). |
| `docs/` | Process and reference documentation (this file, publication, verification, browser reading, chapter factory). |
| `reports/` | Draft, review and environment reports. |

The workbook IDs used in the registry are `workbook-04` (Modern LLM
Architecture, `workbooks/04-llm-architecture/`), `workbook-05` (LLM
Pretraining and Distributed Training, `workbooks/05-llm-training/`),
`addendum-04-05-tsfm` (`workbooks/addendum-04-05-tsfm/`) and
`workbook-06` (LLM Inference Engineering, `workbooks/06-llm-inference/`,
in development).

## Development setup

Base tooling: `python3` (3.10), `git`, and a user-local `node`/`npm`
(via `nvm`). There is no system-wide `pip`/`uv` for the base Python (see
`reports/bootstrap_environment.md`), so everything under `scripts/` and
`figures/source/` uses only the Python 3.10 standard library: no
PyYAML or jsonschema is required for validation or figure builds.

- `scripts/_yaml_lite.py` is a small dependency-free loader for the
  restricted YAML subset used by every `.yaml` file in this repository.
- `figures/source/_svg_helpers.py` builds SVG figures directly, with no
  plotting or diagramming library.

The Quarto/Typst/Pandoc/poppler-utils rendering toolchain lives in a
dedicated, user-local conda environment that is not on `PATH` by
default:

```bash
source /opt/conda/etc/profile.d/conda.sh
conda activate ml-workbooks
```

It was created with
`conda create -n ml-workbooks -c conda-forge --override-channels quarto typst pandoc poppler`
from the read-only shared conda install at `/opt/conda` (new
environments land under `$HOME/.conda/envs`, so nothing system-wide was
touched; see `reports/bootstrap_report.md`). Activate it before
`make workbooks` or `make render-sample`; `make validate` and
`make figures` are pure Python and do not need it. Run the test suite
with the system Python (`/usr/bin/python3`), not the conda one.

If a full toolchain becomes available later, the optional dependency
group in `pyproject.toml` (`pip install -e ".[full]"`) adds
PyYAML/jsonschema/pytest, but nothing in the repository requires it.

## Build commands

```bash
make validate        # validate sources/registry.yaml, coverage-matrix.yaml, questions.yaml
make figures         # regenerate figures/rendered/*.svg from figures/source/*.py
make workbooks       # render every workbooks/**/*.qmd via Quarto (requires quarto on PATH)
make render-sample   # render + pdfinfo/pdftotext/pdftoppm-inspect the bootstrap sample
make check-links     # network check of every URL in sources/registry.yaml
make test            # run tests/ (unittest, no pytest required)
```

### Reproducing a released PDF

```bash
source /opt/conda/etc/profile.d/conda.sh && conda activate ml-workbooks
/usr/bin/python3 scripts/build_final.py           # Modern LLM Architecture -> outputs/04-modern-llm-architecture-workbook.pdf
/usr/bin/python3 scripts/build_wb05_final.py      # LLM Pretraining and Distributed Training -> outputs/05-llm-training-workbook.pdf
/usr/bin/python3 scripts/build_addendum_final.py  # Time-series addendum (current edition) -> outputs/addendum-04-05-tsfm.pdf
```

Each publication record stores the exact `reproduction_command` and
`source_commit`. Build from that commit to reproduce the released file;
compare the result against [editions-and-verification.md](editions-and-verification.md).

Chapter review builds for guides in development use
`scripts/build_chapter_review.py` (see
[chapter-factory-operator-guide.md](chapter-factory-operator-guide.md)).

## Output policy and locations

- Source, figure-generating code and reproducibility files are tracked
  in Git.
- `outputs/<name>.pdf`: canonical final PDFs. Local, git-ignored build
  products; released ones are distributed only as GitHub Release assets.
- `outputs/_releases/` and `outputs/_development/`: release-candidate and
  development artifacts (review PDFs, page renders, review bundles).
  Local and git-ignored; never published.
- `workbooks/<id>/*.pdf` and `workbooks/<id>/page-images/`: per-workbook
  review/sample PDFs and the `pdftoppm` page images used for the
  mandatory visual inspection. Git-ignored.
- `figures/rendered/*.svg`: committed.
- `_site/`: the browser-reading site build (see
  [browser-reading.md](browser-reading.md)). Git-ignored.
- Before replacing an existing validated `outputs/*.pdf`, copy the prior
  version aside (date or hash suffix).
- Corrections after release use a new patch version and a new release;
  an existing release asset is never replaced. The full release
  procedure is in [publication-hygiene.md](publication-hygiene.md).

## Validation commands

```bash
python3 scripts/validate_registry.py              # source registry + coverage matrix structure
python3 scripts/validate_questions.py             # question records against the schema
python3 scripts/validate_publication_hygiene.py   # publication records, README catalog, editions doc, untracked PDFs (offline)
python3 -m unittest discover -s tests -v          # full test suite
```

`scripts/chapter_gate.py`, `scripts/workbook_qa.py` and
`scripts/build_chapter_review.py` accept `--test-pattern` to run a
scoped subset of tests; scoped runs are labelled as such in their
reports.

## How each chapter is structured

Every chapter follows `shared/chapter-template.qmd`:

learning objectives → why this matters → mental model/analogy → visual
overview → technical core → worked example → compare and contrast →
check your understanding → common misconception → applied exercise →
interview lens → chapter recap → sources and further reading.

Case-study and synthesis chapters may adapt the pattern (for example, a
case-study table in place of a single worked example). Comprehension
questions are stored as structured records in
`workbooks/<id>/questions.yaml`, validated against
`shared/question-schema.yaml`.

## Source policy

- Every source has one entry in `sources/registry.yaml`, with an explicit
  `authority_type` (primary technical, implementation guide, visual
  reference, interview question bank, secondary summary,
  source-discovery index, or experiential account).
- Synthesize and cite; never copy long passages or reuse a figure
  without a clear license. Keep primary sources separate from
  commentary, and record when a source was actually last verified (do
  not backdate `last_verified`).
- Every substantive factual claim must be traceable to a
  `sources/registry.yaml` id, through a `.bib` citation in the `.qmd`
  or a `source_ids` entry in a `questions.yaml` record.

## Copyright and attribution

- Prose is written by this project, synthesizing several sources; it is
  not copied from any single source.
- Figures are original, generated from `figures/source/*.py`, and use
  only the shared palette in `config/visual-style.yaml`. Third-party
  figures are used only for inspiration and scoping, never reproduced,
  unless the source's license clearly permits reuse (tracked per entry
  in the `license_or_reuse` field).

## Visual conventions

Defined once in `config/visual-style.yaml` and used by every figure
script:

- **blue** = stored information/state, **orange** = computation,
  **green** = trainable component, **purple** = device-to-device
  communication, **red** = bottleneck/failure/high cost, **gray** =
  frozen/inactive component.
- **solid** arrows = inference/ordinary data flow, **dashed** =
  training-only flow, **dotted** = optional/conditional flow.
- Vector-first (SVG), colorblind-safe, legible in grayscale, no 3D
  effects, no unexplained icons. Captions state what to notice, not just
  what is drawn.

## GPU and SLURM policy

Authoring, rendering and validation are CPU-only. The compute inventory
is recorded in `reports/bootstrap_environment.md` for completeness (this
host has 6 nodes / 48 H100 GPUs across several SLURM partitions that
resolve to the same nodes), but no job is submitted unless a specific
task genuinely benefits from GPU or SLURM resources; none of the current
authoring work does.

## Reporting problems

Use [GitHub Issues](https://github.com/amartya-mitra/ml-llm-study-workbooks/issues)
for errors in the guides or the tooling.
