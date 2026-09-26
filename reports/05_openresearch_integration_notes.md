# OpenResearch (`orx`) Integration Notes — Workbook 05

Date: 2026-09-26
Baseline commit SHA: `e604832`
Scope: Phase 1 evaluation and integration decision only. **The `orx`
binary was not installed.** See "Installation decision," below, for why,
and for what would need explicit approval to proceed.

---

## What `orx` actually is

Fetched directly from `github.com/alphaXiv/OpenResearch` (`SKILL.md` and
the five named skill modules: `orx-experiment-tree`, `orx-lit-review`,
`orx-reports`, `orx-figures`, `orx-agent-delegation`) — read-only,
nothing executed.

`orx` is a Rust CLI + local dashboard/server for driving **ML
experiment trees**: a project is a tree of git-branch nodes, each
running a **fixed shell command** against a compute backend (local,
SSH, SLURM, Modal, Ray, HF, k8s, Tinker). Its cardinal rules:

1. Never edit a node once a run has answered it — branch a child instead.
2. The run command *and* environment are a fixed contract, identical on
   every node — vary committed code, never the invocation.
3. Vary code, not knobs in the command — no env-var sweeps.
4. Grow the tree downward ("stacked bushes"), not sideways (a flat fan
   of un-related siblings off the root).

It also bundles: literature retrieval (`orx discover` / `orx paper`
against alphaXiv, OpenAlex, bioRxiv, PubMed — no login required),
figure-styling guidance for matplotlib/TikZ, a `orx-reports` convention
for writing durable outputs to a project "artifacts directory," and
`orx agent spawn` for delegating independent work to a fresh Claude
Code session with its own git worktree.

## Is `orx` installed?

**No.** `orx --version` → command not found; no trace anywhere under
`$HOME` or common install paths. Confirmed by direct search, not
inferred.

## Exact installation requirement

From the repo's own `README.md` (fetched read-only):

```sh
curl -LsSf https://openresearch.sh/install.sh | sh
orx up
```

- `install.sh` is piped directly into `sh` — an unreviewed remote
  script executed with the invoking user's permissions. This is a real
  trust decision, not a routine `pip install`.
- `orx up` opens a **local dashboard/server at `http://127.0.0.1:4791`**
  — i.e. this is not a one-shot CLI invocation; it stands up a
  persistent local service.
- The binary lands in `~/.local/bin` (or `~/.cargo/bin` for the
  `install.sh` path specifically — the two install methods conflict and
  the docs say to remove one before using the other).
- **Local projects and local run commands do not require `orx login`.**
  Login (browser OAuth, token at `~/.config/openresearch/credentials.json`)
  is only needed for *managed* compute, org listing, and account
  settings — none of which this task needs. This one requirement is
  therefore **not** a blocker for a local-only integration.
- No package-manager path exists in this environment either way: `pip`/
  `pip3`/`pipx` are not on `PATH` here (consistent with this repo's own
  documented "no system-wide pip" policy), and there is no cached copy
  of `orx` or "OpenResearch" anywhere on disk.

Per this task's own instruction ("do not silently install remote
compute, log in, or modify unrelated system configuration"), none of
the above was executed. This section reports the requirement; it does
not authorize it.

## Fit assessment for Workbook 05's actual workflow

Workbook 05's "runs" are Quarto/Typst PDF builds and RC review cycles
— not GPU training/eval sweeps. Mapping `orx`'s model onto that:

| `orx` concept | Maps onto... | Fit |
|---|---|---|
| Fixed run command per project | `python3 scripts/workbook_qa.py --workbook 05-llm-training` | **Good fit** — this is exactly what Phase 2 of this task asked for, and is now implemented (see below) whether or not `orx` itself is installed. |
| Experiment node = git branch, frozen once answered | An RC candidate build | **Partial fit** — workbook 04's actual RC history is a *linear* sequence of commits on `main` (RC1 through RC7, each fixing the prior's findings), not a branch-per-RC tree. Adopting `orx`'s branch-per-node model now would be a real workflow change, not just a QA-tooling addition. |
| Compute backends (SLURM/Modal/Ray/k8s/SSH/Tinker/HF) | N/A | **No fit** — a Quarto render needs no GPU/cluster backend. This is `orx`'s actual center of gravity and is irrelevant here. |
| `orx discover` / `orx paper` (alphaXiv/OpenAlex/bioRxiv/PubMed) | Workbook 05's source-verification work (Phase 5) | **Genuinely useful, if installed** — this is the one piece with real, unique value for this project that plain WebFetch/web search doesn't replicate as cleanly (automatic dedup, ranking, full-text extraction with a consistent citation format). |
| `orx-figures` styling module | Workbook 05's figure scripts | **Redundant** — this repo already has its own `config/visual-style.yaml` and `figures/source/_svg_helpers.py` convention (colorblind-safe, SVG-first, no unexplained icons), independently arrived at and already enforced by `tests/test_figures.py`. Adopting a second, parallel style system would fragment rather than help. |
| `orx-reports` "artifacts directory" | This repo's `reports/` + `outputs/_releases/`/`outputs/_development/` convention | **Redundant/conflicting** — this repo already has its own, already-working output convention (documented in the WB04 cleanup passes). `orx`'s artifacts-directory model is a different, competing convention, not a superset. |
| `orx agent spawn` | Delegating independent audits (Phase 7) | **Redundant** — functionally similar to this session's own `Agent` tool with `isolation: "worktree"`, which is already available without installing anything. |

## Installation decision

**Recommendation: do not install `orx` for this project.** Reasoning:

1. Its actual design center — compute-backend orchestration for
   training/eval experiment trees — has no work to do here. A Quarto
   render is a few seconds on one CPU core; there is no sweep to
   parallelize across backends.
2. Every genuinely useful discipline it encodes (fixed run command,
   frozen-once-answered nodes, "vary code not knobs," stacked-bush
   iteration instead of a flat fan of unrelated edits) is a **process
   convention**, not something that requires the binary to adopt. This
   task's own Phase 2-8 instructions describe exactly these disciplines
   in `orx`-flavored language; they are captured below as plain
   repository conventions instead.
3. Installing it means piping an unreviewed script into `sh` and
   running a persistent local server for the lifetime of this project
   — a real, only-partially-reversible environment change — in exchange
   for one clearly useful capability (literature search) that has a
   workable substitute (direct WebFetch/web search against arXiv/
   alphaXiv/etc., with more manual ranking effort) and several
   capabilities that would actively conflict with this repo's own,
   already-working conventions (figures, output layout, reports).
4. Retrofitting `orx`'s branch-per-experiment-node model onto workbook
   04's established linear-commit RC history (RC1 → RC7, each commit
   fixing the prior's findings on `main`) would be a workflow change
   affecting how *all* future workbooks are versioned, not a
   contained addition to workbook 05 alone — too large a decision to
   make unilaterally inside this task.

**This recommendation is not final** — if literature search via `orx
discover`/`orx paper` turns out to be worth the install cost on its
own once Phase 5 (source verification) actually starts, that is a
narrower, revisitable decision than adopting the whole tool now.

## What was adopted instead (no install required)

The disciplines this task asked `orx` to enforce are now encoded
directly as repository conventions:

- **Fixed QA command** — `scripts/workbook_qa.py --workbook <id>`. One
  stable invocation; per-workbook differences live in the script's
  `WORKBOOK_REGISTRY` dict (committed code), never in an env var or an
  ad hoc flag. See `reports/05_workbook_qa_design.md` for the full
  design and its Phase-2-to-implementation mapping.
- **Frozen-once-answered discipline** — already this repo's actual RC
  practice (workbook 04's RC1 through RC7 each froze the prior RC's
  PDF under `outputs/_releases/`, never edited it, and fixed forward on
  a new commit) — documented, not new.
- **Structured evidence capture** — `scripts/workbook_qa.py` writes one
  JSON summary per run under
  `outputs/_development/<workbook>/qa-runs/<short-sha>/`, keyed by
  commit SHA exactly as `orx`'s run-evidence model would key it by run
  id — durable, reproducible, and tied to an exact commit.
- **Literature workflow** — for now, direct WebFetch/search against
  arXiv/alphaXiv/OpenAlex, recorded manually in the source/claim ledger
  (see the companion RC-report template), matching this repo's existing
  `sources/registry.yaml` discipline. Revisit `orx discover`/`orx paper`
  specifically if/when that manual effort becomes the bottleneck.

## Open item

If a future session decides the literature-search capability alone is
worth it, the narrower ask is: install `orx` **locally only** (no
`orx login`), and use exclusively `orx discover`/`orx paper` — do not
adopt its experiment-tree, figures, reports, or agent-delegation
conventions, which would conflict with this repo's own. That is a
smaller, more clearly-scoped decision than "integrate OpenResearch,"
and should be asked for explicitly when it comes up.
