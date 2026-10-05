#!/usr/bin/env python3
"""Build the final Workbook 05 PDF (canonical, non-RC version).

    1. temporarily update index.qmd subtitle to remove the RC
       designation
    2. render workbooks/05-llm-training/index.qmd via Quarto/Typst
    3. copy to outputs/05-llm-training-workbook.pdf (preserving any
       existing file at that path first, per AGENTS.md)
    4. restore index.qmd subtitle to "Release Candidate 1"
    5. run pdfinfo / pdftotext / pdffonts / pdftoppm and print results

RC1 (outputs/_releases/05-llm-training/05-llm-training-workbook-rc1.pdf)
and all development builds/review packages are preserved as historical
artifacts -- this script never touches them. The canonical final PDF
uses the standard workbook filename without any RC designation, per
scripts/workbook_qa.py's WORKBOOK_REGISTRY.

Modeled directly on scripts/build_final.py (Workbook 04's own
canonical-build script); Workbook 05's index.qmd has no build-version-
note include to regenerate, so that step is omitted here.

Requires the `ml-workbooks` conda env active (quarto + poppler-utils).
"""
import datetime
import os
import shutil
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WB05 = os.path.join(REPO_ROOT, "workbooks", "05-llm-training")
INDEX_QMD = os.path.join(WB05, "index.qmd")
OUTPUT_PDF = os.path.join(REPO_ROOT, "outputs", "05-llm-training-workbook.pdf")
DEV_DIR = os.path.join(REPO_ROOT, "outputs", "_development", "05-llm-training", "canonical-pages")
PAGE_IMAGE_DIR = os.path.join(DEV_DIR, "05-llm-training-workbook-pages")
BACKUP_DIR = DEV_DIR

RC_SUBTITLE = "Release Candidate 1"
FINAL_SUBTITLE = "Final Edition"

REQUIRED_TOOLS = ["quarto", "pdfinfo", "pdftotext", "pdffonts", "pdftoppm"]


def run(cmd, **kw):
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=REPO_ROOT, **kw)
    return result


def read_file(path):
    with open(path, "r") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)


def main():
    missing = [t for t in REQUIRED_TOOLS if shutil.which(t) is None]
    if missing:
        print(f"BLOCKED: missing required tool(s): {missing}")
        print("Activate the ml-workbooks conda env: "
              "source /opt/conda/etc/profile.d/conda.sh && conda activate ml-workbooks")
        sys.exit(2)

    original_content = read_file(INDEX_QMD)
    if f'subtitle: "{RC_SUBTITLE}"' not in original_content:
        print(f"BLOCKED: expected subtitle '{RC_SUBTITLE}' not found in {INDEX_QMD}; "
              "refusing to guess which line to replace.")
        sys.exit(1)

    print("--- Step 1: temporarily remove RC designation from subtitle ---")
    modified_content = original_content.replace(
        f'subtitle: "{RC_SUBTITLE}"',
        f'subtitle: "{FINAL_SUBTITLE}"',
    )
    write_file(INDEX_QMD, modified_content)
    print(f"Temporarily modified {os.path.relpath(INDEX_QMD, REPO_ROOT)}")

    print("\n--- Step 2: render index.qmd ---")
    r = run(["quarto", "render", INDEX_QMD, "--to", "typst"], capture_output=True, text=True)
    print(r.stdout[-3000:])
    if r.returncode != 0:
        print(r.stderr[-3000:])
        write_file(INDEX_QMD, original_content)
        print("BLOCKED: quarto render failed; restored original index.qmd")
        sys.exit(1)

    rendered_pdf = os.path.join(WB05, "index.pdf")
    if not os.path.exists(rendered_pdf):
        write_file(INDEX_QMD, original_content)
        print(f"BLOCKED: expected {rendered_pdf} was not produced; restored original index.qmd")
        sys.exit(1)

    print("\n--- Step 3: copy to outputs/ ---")
    os.makedirs(os.path.dirname(OUTPUT_PDF), exist_ok=True)
    if os.path.exists(OUTPUT_PDF):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
        backup = os.path.join(BACKUP_DIR, f"05-llm-training-workbook.pdf.prev-{stamp}")
        shutil.copy2(OUTPUT_PDF, backup)
        print(f"preserved existing PDF as {os.path.relpath(backup, REPO_ROOT)}")
    shutil.copy2(rendered_pdf, OUTPUT_PDF)
    os.remove(rendered_pdf)
    print(f"wrote {os.path.relpath(OUTPUT_PDF, REPO_ROOT)}")

    print("\n--- Step 4: restore original index.qmd ---")
    write_file(INDEX_QMD, original_content)
    print(f"Restored {os.path.relpath(INDEX_QMD, REPO_ROOT)} to '{RC_SUBTITLE}' subtitle")

    print("\n--- Step 5: inspection pipeline ---")
    print("\n$ pdfinfo")
    print(subprocess.run(["pdfinfo", OUTPUT_PDF], capture_output=True, text=True).stdout)

    print("$ pdffonts")
    print(subprocess.run(["pdffonts", OUTPUT_PDF], capture_output=True, text=True).stdout)

    text = subprocess.run(["pdftotext", OUTPUT_PDF, "-"], capture_output=True, text=True).stdout
    print(f"$ pdftotext | wc -w  ->  {len(text.split())} words extracted")

    os.makedirs(PAGE_IMAGE_DIR, exist_ok=True)
    for f in os.listdir(PAGE_IMAGE_DIR):
        if f.endswith(".png"):
            os.remove(os.path.join(PAGE_IMAGE_DIR, f))
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
    print("Note: This PDF is a build product and is ignored by .gitignore.")
    print("The canonical artifact path is recorded but not committed as a tracked file.")


if __name__ == "__main__":
    main()
