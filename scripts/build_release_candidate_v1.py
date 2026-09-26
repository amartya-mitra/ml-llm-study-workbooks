#!/usr/bin/env python3
"""Build the workbook 04 release-candidate PDF end to end:

    1. regenerate every figure (root + workbook-local)
    2. regenerate the build/version note with the current git commit
    3. render workbooks/04-llm-architecture/index.qmd via Quarto/Typst
    4. copy the result to outputs/04-modern-llm-architecture-workbook-rc1.pdf
       (preserving any prior copy, per AGENTS.md)
    5. run pdfinfo / pdftotext / pdffonts / pdftoppm and print the results

This supersedes scripts/build_ch01_07_review.py as the LIVE build
script now that workbooks/04-llm-architecture/index.qmd includes all
eight chapters -- this is the complete-content-draft release
candidate, not another incremental chapter-range checkpoint. Earlier
"-ch01-0N-review.pdf" scripts and their frozen artifacts are left in
place as historical checkpoints, not deleted.

This is a content-complete DRAFT, not the final edition -- a whole-book
editorial and visual QA pass still remains (see
workbooks/04-llm-architecture/includes/draft-scope-note.qmd).

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
OUTPUT_PDF = os.path.join(REPO_ROOT, "outputs", "_releases", "04-llm-architecture", "04-modern-llm-architecture-workbook-rc1.pdf")
DEV_DIR = os.path.join(REPO_ROOT, "outputs", "_development", "04-llm-architecture", "workbook-rc1")
PAGE_IMAGE_DIR = os.path.join(DEV_DIR, "04-modern-llm-architecture-workbook-rc1-pages")
BACKUP_DIR = DEV_DIR

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
        "--pilot-status", "Complete content draft (release candidate 1) -- all 8 chapters drafted; a whole-book editorial and visual QA pass has NOT yet been performed (see includes/draft-scope-note.qmd); do not call this the final edition",
        "--registry-note", "src-19..src-49 (primary/roadmap sources for Ch.1-8 and the series-wide topic roadmap) last verified 2026-09-22..2026-09-25; see sources/registry.yaml",
        "--provenance-note", "Tied-embeddings usage (Chapter 2) has no dedicated primary source; the sandwich-norm claim (Chapter 2) leans on a secondary source rather than a model's own technical report. Both are tracked sourcing gaps, not unsupported claims.",
        "--provenance-note", "All worked-example numbers in Chapters 1-8 (attention weights, parameter counts, KV-cache sizes, receptive fields, MoE parameter/routing counts, ch. 6's hypothetical-config GQA group size, ch. 7's two-model resource diagnosis, ch. 8's looped-vs-unrolled depth arithmetic) are computed by version-controlled project scripts and checked by the project's automated test suite, not hand-derived.",
        "--provenance-note", "Figures are generated from version-controlled scripts using a fixed visual-style configuration, not drawn freehand; each figure's caption credits its scholarly/technical source where one applies.",
        "--provenance-note", "Chapter 8 is this workbook's assigned primary home for recurrent depth/looped transformers (config/series-topic-roadmap.yaml). Its two verified examples (Mixture-of-Recursions, a research proposal; Nanbeige4.2-3B, a released open-weight model) were each verified via full-text PDF extraction. Public reporting associating recurrent depth with 'GPT-6 Astra' is explicitly treated as unconfirmed, not verified fact, everywhere it is mentioned.",
        "--provenance-note", "Chapter 8's MTP bridge and Chapter 7's MTP/speculative-decoding cross-reference are both deliberately shallow -- MTP's training mechanics (workbook 5) and the speculative-decoding algorithm (workbook 6) are assigned to future workbooks, not taught in workbook 4.",
        "--provenance-note", "This release candidate has NOT yet undergone a whole-book editorial and visual QA pass across all eight chapters together (consistent terminology, cross-reference accuracy, page-break aesthetics, final proofread) -- each chapter was validated individually as it was drafted, not as a completed whole.",
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
        os.makedirs(BACKUP_DIR, exist_ok=True)
        backup = os.path.join(BACKUP_DIR, f"04-modern-llm-architecture-workbook-rc1.pdf.prev-{stamp}")
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
    print("Reminder: this is a complete CONTENT DRAFT (release candidate), not the final edition.")


if __name__ == "__main__":
    main()
