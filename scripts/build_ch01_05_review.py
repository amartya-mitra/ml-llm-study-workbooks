#!/usr/bin/env python3
"""Build the Chapters 1-5 review PDF end to end:

    1. regenerate every figure (root + workbook-local)
    2. regenerate the build/version note with the current git commit
    3. render workbooks/04-llm-architecture/index.qmd via Quarto/Typst
    4. copy the result to outputs/04-llm-architecture-ch01-05-review.pdf
       (preserving any prior copy, per AGENTS.md)
    5. run pdfinfo / pdftotext / pdffonts / pdftoppm and print the results

This supersedes scripts/build_ch01_04_review.py now that
workbooks/04-llm-architecture/index.qmd includes Chapter 5 --
re-running the old script would render the same (now 5-chapter)
index.qmd but mislabel the output as "ch01-04", so use this script
(and `make review-ch01-05`) instead. Earlier scripts and their frozen
PDF artifacts are left in place as historical checkpoints, not deleted.

Requires the `ml-workbooks` conda env active (quarto + poppler-utils).
"""
import datetime
import os
import shutil
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WB04 = os.path.join(REPO_ROOT, "workbooks", "04-llm-architecture")
INDEX_QMD = os.path.join(WB04, "index.qmd")
OUTPUT_PDF = os.path.join(REPO_ROOT, "outputs", "04-llm-architecture-ch01-05-review.pdf")
PAGE_IMAGE_DIR = os.path.join(REPO_ROOT, "outputs", "04-llm-architecture-ch01-05-review-pages")

REQUIRED_TOOLS = ["quarto", "pdfinfo", "pdftotext", "pdffonts", "pdftoppm"]


def run(cmd, **kw):
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=REPO_ROOT, **kw)
    return result


def main():
    missing = [t for t in REQUIRED_TOOLS if shutil.which(t) is None]
    if missing:
        print(f"BLOCKED: missing required tool(s): {missing}")
        print("Activate the ml-workbooks conda env: "
              "source /opt/conda/etc/profile.d/conda.sh && conda activate ml-workbooks")
        sys.exit(2)

    print("--- Step 1: regenerate figures ---")
    r = run([sys.executable, "scripts/build_figures.py"])
    if r.returncode != 0:
        sys.exit(1)

    print("\n--- Step 2: regenerate build/version note ---")
    r = run([
        sys.executable, "scripts/generate_build_note.py",
        "--output", "workbooks/04-llm-architecture/includes/build-version-note.qmd",
        "--pilot-status", "Five-chapter pilot (Chapters 1-5 of 8) -- Chapters 6-8 are planned but not drafted; Chapter 5 covers MoE architecture only, deferring systems-level/distributed-training depth (see outline.yaml's ch5.drafting_note)",
        "--registry-note", "src-19..src-30, src-36 (primary sources for Ch.1-5) last verified 2026-09-22/2026-09-23; see sources/registry.yaml",
        "--provenance-note", "Tied-embeddings usage (Chapter 2) has no dedicated primary source; the sandwich-norm claim (Chapter 2) leans on a secondary source rather than a model's own technical report. Both are tracked sourcing gaps, not unsupported claims.",
        "--provenance-note", "All worked-example numbers in Chapters 1-5 (attention weights, parameter counts, KV-cache sizes, receptive fields, MoE parameter/routing counts) are computed by version-controlled project scripts and checked by the project's automated test suite, not hand-derived.",
        "--provenance-note", "Figures are generated from version-controlled scripts using a fixed visual-style configuration, not drawn freehand; each figure's caption credits its scholarly/technical source where one applies.",
        "--provenance-note", "Chapter 3's and Chapter 4's KV-cache/latent-cache/attention-projection-parameter figures and formulas are LOGICAL, theoretical minimums, not measured GPU memory -- they exclude allocator overhead, page metadata, fragmentation, and framework buffers.",
        "--provenance-note", "Chapter 4's MLA content (compression formula, decoupled-RoPE reasoning, cache-per-token table) was verified directly against DeepSeek-V2's full paper text ([@src-27], Sections 2.1.1-2.1.4 and Table 1), not a search-result snippet.",
        "--provenance-note", "Chapter 4 does not cite a primary source for recurrent/SSM/linear-attention mechanics (a tracked, disclosed sourcing gap) and deliberately keeps that family at the taxonomy level rather than teaching mechanics without one.",
        "--provenance-note", "Chapter 5's shared-experts claim was verified directly against DeepSeekMoE's full paper text ([@src-36], arXiv:2401.06066), not a snippet or blog summary; detailed distributed-training implementation, collective-communication algorithms, kernel optimization, inference-engine configuration, expert quantization, model-specific benchmark comparisons, post-training, and routing-research surveys are all deferred.",
    ])
    if r.returncode != 0:
        sys.exit(1)

    print("\n--- Step 3: render index.qmd ---")
    r = run(["quarto", "render", INDEX_QMD, "--to", "typst"], capture_output=True, text=True)
    print(r.stdout[-3000:])
    if r.returncode != 0:
        print(r.stderr[-3000:])
        print("BLOCKED: quarto render failed")
        sys.exit(1)

    rendered_pdf = os.path.join(WB04, "index.pdf")
    if not os.path.exists(rendered_pdf):
        print(f"BLOCKED: expected {rendered_pdf} was not produced")
        sys.exit(1)

    print("\n--- Step 4: copy to outputs/, preserving any prior copy ---")
    os.makedirs(os.path.dirname(OUTPUT_PDF), exist_ok=True)
    if os.path.exists(OUTPUT_PDF):
        stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
        backup = f"{OUTPUT_PDF}.prev-{stamp}"
        shutil.copy2(OUTPUT_PDF, backup)
        print(f"preserved existing PDF as {os.path.relpath(backup, REPO_ROOT)}")
    shutil.copy2(rendered_pdf, OUTPUT_PDF)
    print(f"wrote {os.path.relpath(OUTPUT_PDF, REPO_ROOT)}")

    print("\n--- Step 5: inspection pipeline ---")
    print("\n$ pdfinfo")
    print(subprocess.run(["pdfinfo", OUTPUT_PDF], capture_output=True, text=True).stdout)

    print("$ pdffonts")
    print(subprocess.run(["pdffonts", OUTPUT_PDF], capture_output=True, text=True).stdout)

    text = subprocess.run(["pdftotext", OUTPUT_PDF, "-"], capture_output=True, text=True).stdout
    print(f"$ pdftotext | wc -w  ->  {len(text.split())} words extracted")

    os.makedirs(PAGE_IMAGE_DIR, exist_ok=True)
    toppm = subprocess.run(
        ["pdftoppm", "-png", "-r", "170", OUTPUT_PDF, os.path.join(PAGE_IMAGE_DIR, "page")],
        capture_output=True, text=True,
    )
    if toppm.returncode != 0:
        print("BLOCKED: pdftoppm failed")
        print(toppm.stderr)
        sys.exit(1)
    pages = sorted(f for f in os.listdir(PAGE_IMAGE_DIR) if f.endswith(".png"))
    print(f"$ pdftoppm -> {len(pages)} page image(s) in {os.path.relpath(PAGE_IMAGE_DIR, REPO_ROOT)}")

    print(f"\nOK: {os.path.relpath(OUTPUT_PDF, REPO_ROOT)} built and inspected.")
    print("Manual step still required: open the PNG page images and visually confirm layout (AGENTS.md).")


if __name__ == "__main__":
    main()
