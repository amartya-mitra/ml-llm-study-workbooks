# Bootstrap Environment Inventory

Recorded: 2026-09-21
Host: SLURM-managed HPC cluster (H100 nodes), user `amitra`

> **Correction added 2026-09-22:** the original scan below marked
> `conda`/`mamba` "unavailable" because `command -v conda` found nothing
> on the default `PATH`. That check was incomplete — it did not look for
> a conda install off-PATH. A conda 25.7.0 install exists at
> `/opt/conda` (read-only base env, but pre-configured to create new
> environments under `/mnt/home/amitra/.conda/envs`, which is writable).
> This was found while investigating an existing project venv
> (`~/chronos-env`) at the user's request, and was then used to install
> `quarto`/`typst`/`pandoc`/poppler-utils user-locally into a new
> `ml-workbooks` conda environment. See
> `reports/bootstrap_report.md`'s "Update: rendering toolchain installed"
> section for the full story — left here as-is (rather than rewritten)
> so the record of what the initial scan actually checked is preserved.

## Legend

- **available** — found on `PATH`, version confirmed
- **unavailable** — not found, no module offers it
- **available through a module** — found via `module avail`
- **uncertain** — partial signal, needs a closer look before relying on it

## Core tooling

| Tool | Status | Version / detail |
|---|---|---|
| python | available | Python 3.10.12 (`/usr/bin/python3`; no bare `python` symlink) |
| pip | unavailable | no `pip`/`pip3` binary; `python3 -m pip` → "No module named pip"; `ensurepip` also missing from the stdlib install |
| uv | unavailable | not on PATH, no module |
| conda / mamba | unavailable | not on PATH, no module |
| git | available | git version 2.34.1 |
| quarto | unavailable | not on PATH, no module |
| typst | unavailable | not on PATH, no module |
| pandoc | unavailable | not on PATH, no module |
| graphviz (`dot`) | unavailable | not on PATH; the only `dot` in `module avail` is an unrelated modulefile that appends `.` to `PATH` |
| node | available | v24.14.1, via nvm at `/mnt/home/amitra/.nvm/versions/node/v24.14.1` (user-local, not system) |
| npm | available | 11.12.1, same nvm install |
| mermaid CLI (`mmdc`) | unavailable | not installed; installable user-locally via `npm install` since node/npm already work |
| latexmk | unavailable | not on PATH, no module |
| xelatex | unavailable | not on PATH, no module |
| pdflatex | unavailable | not on PATH, no module |
| pdftotext (poppler) | unavailable | not on PATH, no module |
| pdftoppm (poppler) | unavailable | not on PATH, no module |
| pdfinfo (poppler) | unavailable | not on PATH, no module |
| imagemagick (`convert`/`magick`) | unavailable | not on PATH, no module |
| rsvg-convert | unavailable | not on PATH, no module |
| inkscape | unavailable | not on PATH, no module |

The environment's module system (`module avail`) only exposes a handful of unrelated modulefiles (`dot`, `image-defaults`, `module-git`, `module-info`, `modules`, `null`, `use.own`) — none of the rendering/document tools above are reachable through modules.

## Network and privilege notes (context for later install planning, no action taken)

- Outbound HTTPS works (`curl -sI https://quarto.org` → `HTTP/2 200`), so user-local downloads are technically possible later.
- `apt-get` exists and the account has passwordless `sudo`, but per project rules **no system-wide installs are performed** during bootstrap regardless of what's technically possible.
- Python has no `pip`/`ensurepip`, so even user-local Python package installs need a bootstrap step (e.g. fetching `get-pip.py`) before `uv`/`pip` can be used — not attempted in this stage.

## SLURM environment (inspected only — no jobs submitted)

`sinfo` output:

```
PARTITION AVAIL  TIMELIMIT  NODES  STATE NODELIST
all          up   infinite      3   mix- slurm-h100-206-[093,101,107]
all          up   infinite      1   drng slurm-h100-208-197
all          up   infinite      2    mix slurm-h100-206-[073,081]
hpc-high     up   infinite      3   mix- slurm-h100-206-[093,101,107]
hpc-high     up   infinite      1   drng slurm-h100-208-197
hpc-high     up   infinite      2    mix slurm-h100-206-[073,081]
hpc-low      up   infinite      3   mix- slurm-h100-206-[093,101,107]
hpc-low      up   infinite      1   drng slurm-h100-208-197
hpc-low      up   infinite      2    mix slurm-h100-206-[073,081]
hpc-mid*     up   infinite      3   mix- slurm-h100-206-[093,101,107]
hpc-mid*     up   infinite      1   drng slurm-h100-208-197
hpc-mid*     up   infinite      2    mix slurm-h100-206-[073,081]
hpc-prod     up   infinite      3   mix- slurm-h100-206-[093,101,107]
hpc-prod     up   infinite      1   drng slurm-h100-208-197
hpc-prod     up   infinite      2    mix slurm-h100-206-[073,081]
```

`squeue -u amitra`: empty (no jobs currently queued or running for this user).

Partitions, from `scontrol show partition`:

| Partition | Default | Nodes | Total CPUs | Total GPUs | Priority tier |
|---|---|---|---|---|---|
| all | no | 6 | 768 | 48 | 1 |
| hpc-high | no | 6 (same 6) | 768 | 48 | 32768 |
| hpc-low | no | 6 (same 6) | 768 | 48 | 1 |
| hpc-mid | **yes** | 6 (same 6) | 768 | 48 | 16384 |
| hpc-prod | no | 6 (same 6) | 768 | 48 | 65500 (PreemptMode=OFF) |

Key findings:

- **No dedicated CPU-only partition exists.** All five partitions resolve to the same underlying 6 nodes (`slurm-h100-206-[073,081,093,101,107]`, `slurm-h100-208-197`).
- **GPU type:** every node carries `Gres=gpu:h100:8` — i.e. all 6 nodes are 8x H100 nodes (48 GPUs total across the cluster), confirmed via `scontrol show node slurm-h100-206-073`.
- **Per-node resources:** 128 CPUs, ~1.98 TB RAM, 8x H100 per node.
- **Time limits:** `TIMELIMIT=infinite` at the partition level and `MaxTime=UNLIMITED`; no default wall-clock cap is enforced by the scheduler.
- **Interactive GPU jobs:** appear supported in principle (`srun`/`salloc` were not tested, per instructions not to submit jobs), since `OverSubscribe=NO` and node state shows a mix of `mix`/`drng` (draining) — i.e. the cluster is partially occupied but not full.

**Conclusion for this project:** none of this workbook-authoring work (rendering, source management, writing, most diagram generation) needs a GPU. The demonstration KV-cache figure is a static illustrative diagram, not a model run, so it also stays CPU-only. GPU/SLURM resources are recorded here for completeness only; no jobs are submitted during bootstrap, consistent with `AGENTS.md`.

## Summary for Stage 3 planning

The authoring stack described in the task (Quarto + Typst + Python + SVG diagrams) is **not currently available** on this system, and none of it is reachable via modules. `python3`, `git`, and a user-local `node`/`npm` (via nvm) are available and sufficient to scaffold the project, write validation scripts, and build the visual-style/figure infrastructure in pure Python/SVG. Actual PDF rendering is blocked pending a user-local installation decision — see `reports/bootstrap_report.md` for the specific proposed install plan and Stage 7 for what was attempted.
