# Bootstrap Report — ML/LLM Study Workbooks

Date: 2026-09-22 (updated same day after the rendering toolchain was
installed and the Stage 7 sample was actually rendered — see "Update:
rendering toolchain installed" below)
Scope: Stage 0–9 bootstrap of `/mnt/home/amitra/ml-llm-study-workbooks`, per
the bootstrap task. No workbook content beyond the Stage 7 sample was
drafted, per instructions.

## What was created

- Git repository initialized with default branch `main` (no commits made
  yet by this process — see "Git status" below for what to do next).
- Full directory scaffold: `config/`, `sources/` (+ `snapshots/`),
  `shared/` (+ `figure-template/`), `workbooks/01..08-*/`,
  `figures/{source,rendered}/`, `scripts/`, `reports/`, `tests/`,
  `outputs/`.
- `AGENTS.md` with the durable project rules from Stage 2, verbatim in
  spirit (sourcing, accuracy, pedagogy, build/validation discipline).
- Config: `config/project.yaml` (8 workbooks registered),
  `config/visual-style.yaml` (palette + arrow semantics), 
  `config/workbook-defaults.yaml` (chapter sections, question types,
  citation/figure/rendering defaults).
- `sources/registry.yaml` — all 18 supplied URLs registered with id,
  title, url, authors, resource type, workbook categories, topic tags,
  authority type, expected use, license/reuse note, and notes.
  **`last_verified` is `null` and `access_status` is "not yet fetched in
  this session" for every entry** — none were re-fetched this session, so
  claiming a verification date would have been fabricated. Fetching and
  verifying is deliberately left for a later, explicit step
  (`scripts/check_links.py` does a live reachability check on request but
  does not itself update the registry).
- `sources/coverage-matrix.yaml` mapping each of the 8 workbooks to its
  backing sources with a coverage strength (primary/supporting/discovery),
  plus a `gaps_and_notes` section flagging that workbook 01 (ML
  Foundations) currently has no primary technical source registered —
  the most important pre-drafting gap found.
- `shared/bibliography.bib` — one BibTeX entry per registry source
  (`src-01`..`src-18`), keys matching registry ids 1:1. `year` is
  deliberately omitted from every entry (not fabricated) pending actual
  verification — Typst's BibLaTeX parser rejects a non-numeric
  placeholder like `n.d.` outright, which is how this was caught (see
  "Update: rendering toolchain installed" below).
- `shared/glossary.yaml` — 8 starter terms relevant to the workbook 04
  pilot (KV-cache, prefill, decode step, GQA, MoE, 3D parallelism, RLHF,
  LoRA), each with a short definition and source id.
- `shared/question-schema.yaml` — hand-written schema (id, workbook,
  chapter, topic, difficulty, question_type, prompt, expected_answer,
  explanation, common_wrong_answer, source_ids) with allowed values and
  validation rules, since `jsonschema` is not installable here (see
  below). Enforced by `scripts/validate_questions.py`.
- `shared/chapter-template.qmd` — the 13-section reusable chapter
  template (learning objectives through sources/further reading), with
  Typst/Quarto frontmatter, an equation, a table, and citation
  placeholders already wired up.
- `shared/figure-template/` — a copyable figure-script starting point
  plus a README explaining the figure convention.
- `figures/source/_svg_helpers.py` — a small dependency-free SVG builder
  (rects, text, arrows with solid/dashed/dotted markers) that reads
  `config/visual-style.yaml` so no figure script hardcodes a color.
- `figures/source/kv_cache_demo.py` -> `figures/rendered/kv_cache_demo.svg`
  — the Stage 6 original demonstration figure: prompt tokens -> prefill ->
  KV-cache creation -> one decode step -> cache extended by exactly one
  slot, with a dotted "repeat" loop and a color legend. Initially only
  verified well-formed (`xml.etree.ElementTree.parse`) and bounds-checked
  programmatically, since no PDF/SVG rasterizer was available yet at that
  point in the bootstrap. Once the rendering toolchain was installed
  (see "Update: rendering toolchain installed" below), this figure was
  actually rendered into the sample PDF and visually inspected as a PNG,
  which caught five real layout bugs the bounds check had missed — all
  now fixed.
- `scripts/_yaml_lite.py` — a minimal dependency-free YAML-subset
  loader (block mappings/sequences, inline flow lists, quoted/plain
  scalars, comments). All `.yaml` files in this repo are authored within
  this subset intentionally.
- `scripts/validate_registry.py`, `scripts/validate_questions.py`,
  `scripts/check_links.py`, `scripts/build_figures.py`,
  `scripts/build_workbooks.py`, `scripts/render_and_check.py` — all
  runnable today with only `python3` (no third-party packages).
- `workbooks/04-llm-architecture/bootstrap-sample.qmd` — the Stage 7
  minimal build test (title/subtitle/author, one equation, the KV-cache
  figure, one analogy callout, one misconception callout, a 3-row
  comparison table, two comprehension questions, citations to `src-10`
  and `src-11`).
- `workbooks/04-llm-architecture/questions.yaml` — the two comprehension
  questions from the sample, as machine-validated records
  (`q-04-kv-cache-001`, `q-04-kv-cache-002`), passing
  `scripts/validate_questions.py`.
- `tests/test_registry.py`, `tests/test_questions.py`,
  `tests/test_project_structure.py` — 15 tests total (see "Tests
  performed" below), run via `python3 -m unittest discover -s tests`.
- `README.md` (purpose, workbook list, source/copyright policy, dev
  setup, build/validation commands, visual conventions, GPU/SLURM
  policy) and this report.
- `.gitignore`, `pyproject.toml`, `Makefile` as specified.

## Environment findings

Full detail in `reports/bootstrap_environment.md`. Summary:

| Category | Available | Unavailable |
|---|---|---|
| Core | python3 3.10.12, git 2.34.1, node v24.14.1 + npm 11.12.1 (via nvm, user-local) | pip, uv, conda/mamba, `ensurepip` (missing even from stdlib) |
| Rendering stack | — | quarto, typst, pandoc |
| Diagrams | — | graphviz (`dot`), mermaid CLI (`mmdc`) |
| TeX | — | latexmk, xelatex, pdflatex |
| PDF tooling | — | pdftotext, pdftoppm, pdfinfo (poppler-utils) |
| Raster/vector tools | — | imagemagick, rsvg-convert, inkscape |
| Module system | only unrelated modulefiles (`dot` [PATH helper, not graphviz], `image-defaults`, etc.) | none of the above reachable via `module load` |
| Network | outbound HTTPS confirmed working | — |
| Privilege | passwordless `sudo` available | **not used** — task explicitly forbids system-wide installs regardless of technical possibility |

SLURM (inspected only, no jobs submitted): 5 partitions (`all`,
`hpc-high`, `hpc-low`, `hpc-mid` [default], `hpc-prod`) all resolve to the
same 6 nodes (`slurm-h100-206-[073,081,093,101,107]`,
`slurm-h100-208-197`), each an 8x H100 node (48 GPUs total, 768 CPUs,
~11.9 TB aggregate RAM). No dedicated CPU-only partition exists, and none
is needed: this project's authoring/rendering/validation work is
entirely CPU-bound, and no job was submitted.

## Rendering stack selected

Quarto (Markdown/QMD) + Typst (PDF) + Python (figures/examples) + SVG, as
specified. At initial bootstrap time, none of Quarto/Typst/Pandoc/
poppler-utils was installed or reachable via modules, and this report
originally documented (but did not execute) two candidate user-local
install plans. **That has since changed — see below.**

## Update: rendering toolchain installed

At the user's explicit request, the missing tools were installed
user-locally, with no system-wide changes and no sudo use:

- `/opt/conda` turned out to already exist on this host as a **read-only
  shared base conda install** (`conda 25.7.0`), pre-configured with
  `envs directories: /mnt/home/amitra/.conda/envs` — i.e. new environments
  it creates land under `$HOME`, fully writable, without ever touching
  the read-only base. This was discovered by checking an existing
  project venv at `~/chronos-env` (per the user's suggestion while
  looking for a working `pip`), which led to finding the conda install
  it was itself built from.
- Created a new, isolated environment for this project only:
  `/opt/conda/bin/conda create -n ml-workbooks -c conda-forge --override-channels quarto typst pandoc poppler -y`
  (channel restricted to `conda-forge`, deliberately excluding
  Anaconda's default channel, which carries commercial-use licensing
  terms many organizations restrict).
- This installed real, working `quarto` 1.9.38, `typst` 0.14.2, `pandoc`
  3.8.3, and poppler-utils (`pdfinfo`/`pdftotext`/`pdftoppm`) 26.09.0, all
  under `/mnt/home/amitra/.conda/envs/ml-workbooks/bin/`, activated via
  `conda activate ml-workbooks`. Nothing outside `$HOME` was modified;
  `/opt/conda`'s base environment was never written to.
- **This project's config now assumes this environment is activated**
  when rendering. `Makefile`/`scripts/*.py` still just call `quarto`,
  `pdfinfo`, etc. by name on `PATH` — activate `ml-workbooks` first
  (`source /opt/conda/etc/profile.d/conda.sh && conda activate
  ml-workbooks`), then run `make render-sample` / `make workbooks`.

Two structural fixes were required beyond just installing the binaries
(both are now permanent parts of the repo, not one-off workarounds):

1. **Added `_quarto.yml` at the repo root.** Without a project file,
   Quarto renders each `.qmd` in isolation and Typst's file-access
   sandbox then refuses to read anything outside the `.qmd`'s own
   directory — so `bootstrap-sample.qmd` (under `workbooks/04-.../`)
   could not read `figures/rendered/kv_cache_demo.svg` (two directories
   up). A root-level `_quarto.yml` declaring `project: type: default`
   makes the whole repo the Typst project root, fixing this for every
   future chapter, not just the sample.
2. **Removed the `year = {n.d.}` placeholder from every entry in
   `shared/bibliography.bib`.** Typst's native BibLaTeX parser (used when
   rendering to the `typst` format) rejects a non-numeric `year` value
   outright ("failed to parse BibLaTeX (wrong number of digits)"),
   unlike citeproc/pandoc's more lenient BibTeX handling. The field is
   now omitted entirely rather than fabricated — `shared/bibliography.bib`
   still deliberately has no `year` for any of the 18 sources, since none
   have been actually re-verified yet (see "Unresolved blockers").

## Sample PDF render result

**Succeeded.** `workbooks/04-llm-architecture/bootstrap-sample.pdf` now
renders end to end via
`python3 scripts/render_and_check.py workbooks/04-llm-architecture/bootstrap-sample.qmd`
(with the `ml-workbooks` conda env active).

**Sample PDF page count: 3** (per `pdfinfo`; US Letter, 612x792pt, Typst
1.7 PDF, ~76KB).

Per AGENTS.md, the 3 rendered pages were actually opened as PNGs
(`pdftoppm -png -r 150`, saved under
`workbooks/04-llm-architecture/page-images/`) and visually inspected —
not just compiled. That inspection caught four real, non-cosmetic layout
bugs that a bounds-check alone would have missed, all now fixed in
`figures/source/kv_cache_demo.py`:

1. **Broken callout icons.** Quarto's Font Awesome callout icons
   rendered as empty/broken glyph boxes in front of "Analogy" and
   "Common misconception" (the icon font isn't wired up for this
   Typst install). Fixed by setting `callout-icon: false` once in
   `_quarto.yml` (project-wide), rather than patching every callout.
2. **An arrow drawn straight through label text.** The connector arrow
   from the prefill compute box down to the cache row shared a y-band
   with the "KV-cache after prefill" label, so the arrow visibly crossed
   the words. Fixed by adding explicit label/arrow spacing constants so
   an arrow's path and a label's text vertical extent never overlap.
3. **Dotted "cache read" lines tunneling through the decode box and the
   section-2 title.** These lines originally ended below the decode box
   instead of at its top edge (visibly cutting through the box and its
   caption), and separately crossed straight through the "Decode step:
   ..." title text. Fixed by (a) stopping the lines at the box edge
   instead of past it, and (b) breaking each line into two segments that
   skip over the title's text band entirely.
4. **The "repeat" loop-back arrow cut diagonally through the whole
   lower diagram**, including straight through the newly-appended
   `K/V[4]` box. Fixed by rerouting it along the empty right margin
   (an L-shaped dotted path) instead of a direct diagonal.

A fifth, self-inflicted regression surfaced while fixing #2/#3 (widening
a vertical gap pushed the "Repeated once per generated token..." caption
down into the legend row — caught because `pdftotext`'s reading-order
output showed the two rows' words interleaved character-by-character,
a good tell for real overlapping text). Fixed at the root cause: the
canvas height is now derived from the last element actually placed
(`canvas.height = legend_y + 40`, set just before `save()`) instead of a
hardcoded constant, so this class of bug can't reappear after a future
spacing change upstream.

The programmatic SVG bounds-check from the original bootstrap (parse as
XML, check no shape exceeds the canvas) is kept in the figure script's
dev loop, but it is explicitly **not a substitute** for the PNG
inspection above — it caught zero of the five real issues found, since
all five were about elements overlapping *each other* within a
technically in-bounds canvas, not about elements exceeding the canvas.

## Tests performed

`python3 -m unittest discover -s tests -v` — **15/15 passed**:

- `test_registry.py` (6 tests): registry has sources, unique ids, id
  pattern, valid URLs, required fields present, workbook categories known,
  coverage matrix references only known sources/workbooks.
- `test_questions.py` (4 tests): schema loads with the expected field
  set, schema's allowed question types match `config/workbook-defaults.yaml`,
  all existing question records pass validation, question files are
  discoverable by the expected glob convention.
- `test_project_structure.py` (4 tests): all expected directories exist,
  `config/project.yaml` lists exactly the 8 expected workbook ids in
  order, every rendered figure has a matching source script, and
  `shared/bibliography.bib` keys exactly match `sources/registry.yaml`
  ids (no drift in either direction).

Also run standalone and passing: `python3 scripts/validate_registry.py`,
`python3 scripts/validate_questions.py`, `python3 scripts/build_figures.py`
(regenerates `kv_cache_demo.svg` from source, `make figures`).
`scripts/check_links.py` (live network reachability check) exists but was
**not run** in this report — it's a deliberately manual, network-using
step per its own docstring, not part of default validation.

## Unavailable dependencies

**Resolved:** quarto, typst, pandoc, pdftotext, pdftoppm, pdfinfo — now
available via the user-local `ml-workbooks` conda environment (see
above). `uv` and `jsonschema`/`PyYAML` remain unnecessary in practice
(`scripts/_yaml_lite.py` covers every `.yaml` file in this repo; the
`ml-workbooks` env's own `pip` could add them if ever needed).

**Still unavailable, not requested/needed for this pilot:** graphviz
(`dot`), mermaid CLI (`mmdc`), latexmk/xelatex/pdflatex (TinyTeX),
imagemagick, rsvg-convert, inkscape. All of these are installable the
same way (`conda install -n ml-workbooks -c conda-forge <package>`,
or `quarto install tinytex` for the TeX tools) if a later workbook needs
Graphviz/Mermaid diagrams or LaTeX math beyond what Typst covers
natively — not installed now since nothing in the current scope needs
them yet.

## Unresolved blockers

1. **`sources/registry.yaml` entries are all still unverified** — every
   `last_verified` is intentionally `null` and `shared/bibliography.bib`
   has no `year` for any entry. A future step should actually open each
   of the 18 URLs, confirm reachability/content, and update
   `last_verified` + `access_status` + `license_or_reuse` (+ a real
   `year` in the `.bib` entry) with what was actually found.
2. **Workbook 01 (ML Foundations) has no primary source registered** —
   flagged in `sources/coverage-matrix.yaml`'s `gaps_and_notes`.
3. **The `ml-workbooks` conda env must be activated manually** before
   running `make workbooks` / `make render-sample` — it is not on `PATH`
   by default in a fresh shell (`source /opt/conda/etc/profile.d/conda.sh
   && conda activate ml-workbooks`). A future session should decide
   whether to document this as a standing step (current approach) or
   have the Makefile targets activate it automatically.

## Recommended next step

Plan and draft **04 — Modern LLM Architecture** (the designated pilot).
The rendering pipeline is no longer a blocker, so, concretely, in order:

1. Actually fetch/verify `src-10` (Scaling Book), `src-14` (Big LLM
   Architecture Comparison), and `src-15` (LLM Architecture Gallery) —
   the three sources `sources/coverage-matrix.yaml` marks as primary/
   supporting for workbook 04 — and update their registry entries with
   real `last_verified` dates, a real `year` in `shared/bibliography.bib`,
   and confirmed `license_or_reuse` notes.
2. Draft a chapter outline for workbook 04 (which architectures/models to
   cover, in what order) informed by `src-15`'s gallery scope, using
   `shared/chapter-template.qmd` as the per-chapter skeleton and
   `bootstrap-sample.qmd` as a structurally-proven, now render-verified
   starting point.
3. For each new figure, budget time for an actual PNG visual-inspection
   pass (`make render-sample`-style), not just a bounds check — this
   bootstrap's own sample figure needed five rounds of real layout fixes
   that a bounds check alone did not catch.

Explicitly **not done** in this bootstrap, per instructions: no full
workbook chapter beyond the Stage 7 sample, no SLURM job submitted, no
system-wide package installed (the conda env created is entirely
user-local, under `$HOME`).

## Update: bootstrap audit (before the baseline commit)

Before treating this scaffold as a stable baseline, every file listed in
the audit task was re-read critically rather than trusted because tests
passed. Real issues found and fixed:

- **Fabricated-risk author metadata.** `sources/registry.yaml` entries
  for `src-03` and `src-09` asserted specific real-world full names
  ("Khang Pham", "Alisa Liu") that were never actually verified against
  the source pages in any session — they came from background pattern-
  matching on the GitHub/blog handles, which is exactly what AGENTS.md's
  "do not fabricate... do not invent missing metadata" rules exist to
  catch. Both were actually fetched this session: `src-03`'s page does
  not reliably confirm a full name (only the handle `khangich`); `src-09`
  confirms only the first name "Alisa", not a surname. Both entries now
  state only what was actually confirmed, with `last_verified` set to a
  real date since they were genuinely checked.
- **A public-repo PII exposure.** `config/project.yaml`'s
  `maintainer_email` held a real work email address, already committed
  and pushed to what turned out to be a **public** GitHub repo (verified
  via the GitHub API: `"private": false`). Flagged to the user directly
  rather than silently changed; per their explicit choice, the field is
  now `null` going forward (the already-pushed history still has it —
  that requires a separate, deliberate history-rewrite decision this
  task did not take).
- **Validators that silently accepted malformed input.**
  `scripts/validate_registry.py` never actually required
  `last_verified` to be present (despite AGENTS.md mandating it), never
  rejected an empty-string value for any required field, and never
  checked `authority_type` against the fixed set of categories
  README.md documents. `scripts/validate_questions.py` had the same
  empty-string gap for `explanation` (only `prompt`/`expected_answer`
  were special-cased) and would silently iterate over the *characters*
  of `source_ids` if it were ever a string instead of a list. All four
  gaps are now closed, generically, with matching new/updated tests in
  `tests/test_registry.py`.
- **An unverified manual check masquerading as a real regression test.**
  The Stage 6/7 bootstrap's canvas-bounds check on
  `figures/rendered/kv_cache_demo.svg` was run once, by hand, in a bash
  one-liner, and never became a real test — so a future edit to the
  figure script could silently reintroduce clipping with nothing to
  catch it. Formalized as `tests/test_figures.py` (well-formed XML +
  no shape/text outside the declared canvas, for every rendered figure).
- **Redundant, driftable Quarto frontmatter.** Both
  `shared/chapter-template.qmd` and
  `workbooks/04-llm-architecture/bootstrap-sample.qmd` repeated
  `papersize`/`margin`/`toc`/`bibliography` settings that `_quarto.yml`
  already sets project-wide — meaning a future project-level change
  (e.g. a margin adjustment) would silently *not* apply to any chapter
  that had copy-pasted the old per-document override. Removed the
  duplication from both files and re-rendered
  `bootstrap-sample.qmd` from a clean invocation to confirm the project
  defaults still apply correctly on their own (identical 3-page output,
  citations still render as `[1]`/`[2]`, callout-icon fix still holds —
  compared page-by-page against the previously-inspected PNGs).
- **Stale documentation.** `pyproject.toml` and
  `config/workbook-defaults.yaml` still described the pre-conda state
  (no pip/uv path found yet, pandoc "unavailable") after the toolchain
  install; both updated to reflect the actual current environment.
- **A cosmetic `.gitignore` duplicate** (`.quarto/` and `/.quarto/` both
  present) was cleaned up; Quarto's own render step re-added the
  anchored form afterward, which is Quarto's own project tooling and is
  harmless (the unanchored `.quarto/` rule already covers every depth).

Nothing else audited raised a real issue: no accidental absolute paths
in code/config (only in prose reports, describing the actual
environment, which is appropriate), no generated files tracked by git
(`git ls-files` confirms `.quarto/`, `*.pdf`, `page-images/`, and
`__pycache__/` are all correctly untracked despite existing on disk),
and README/Makefile/actual script behavior were cross-checked and found
consistent.

All 20 tests pass (`python3 -m unittest discover -s tests`, up from 15 —
5 new/updated: 3 in `test_figures.py`, 2 in `test_registry.py`), the
registry/question validators pass, and the sample PDF was rebuilt from a
clean invocation (`rm` the old PDF/page-images, rerun
`scripts/build_figures.py` then `scripts/render_and_check.py`) and
re-inspected page-by-page.
