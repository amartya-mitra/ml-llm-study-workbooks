#!/usr/bin/env python3
"""Render one .qmd file to PDF and run the Stage 7 visual-inspection
pipeline: pdfinfo -> pdftotext -> pdftoppm (page images).

Usage:
    python3 scripts/render_and_check.py workbooks/04-llm-architecture/bootstrap-sample.qmd

Reports the exact missing dependency and exits non-zero rather than
claiming success if quarto/pdfinfo/pdftotext/pdftoppm are unavailable.
Never overwrites a previously validated PDF silently: if the target
output already exists, the prior copy is preserved with a
`.prev-<timestamp>` suffix first (AGENTS.md).
"""
import datetime
import os
import shutil
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REQUIRED_TOOLS = ["quarto", "pdfinfo", "pdftotext", "pdftoppm"]


def check_tools():
    missing = [t for t in REQUIRED_TOOLS if shutil.which(t) is None]
    return missing


def preserve_existing(pdf_path: str):
    if os.path.exists(pdf_path):
        stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
        backup = f"{pdf_path}.prev-{stamp}"
        shutil.copy2(pdf_path, backup)
        print(f"preserved existing PDF as {os.path.relpath(backup, REPO_ROOT)}")


def main():
    if len(sys.argv) != 2:
        print("usage: render_and_check.py <path-to-qmd>")
        sys.exit(2)
    qmd_path = os.path.abspath(sys.argv[1])
    if not os.path.exists(qmd_path):
        print(f"BLOCKED: no such file: {qmd_path}")
        sys.exit(2)

    missing = check_tools()
    if missing:
        print(f"BLOCKED: missing required tool(s): {missing}")
        print("Not attempting to render. See reports/bootstrap_report.md for the")
        print("proposed user-local installation plan for these tools.")
        sys.exit(2)

    base = os.path.splitext(os.path.basename(qmd_path))[0]
    pdf_path = os.path.join(os.path.dirname(qmd_path), f"{base}.pdf")

    preserve_existing(pdf_path)

    render = subprocess.run(["quarto", "render", qmd_path, "--to", "typst"], cwd=REPO_ROOT, capture_output=True, text=True)
    if render.returncode != 0:
        print("BLOCKED: quarto render failed")
        print(render.stdout)
        print(render.stderr)
        sys.exit(1)

    if not os.path.exists(pdf_path):
        print(f"BLOCKED: render reported success but expected PDF not found at {pdf_path}")
        sys.exit(1)

    info = subprocess.run(["pdfinfo", pdf_path], capture_output=True, text=True)
    print("--- pdfinfo ---")
    print(info.stdout)

    text = subprocess.run(["pdftotext", pdf_path, "-"], capture_output=True, text=True)
    print("--- pdftotext (first 2000 chars) ---")
    print(text.stdout[:2000])

    png_dir = os.path.join(os.path.dirname(pdf_path), "page-images")
    os.makedirs(png_dir, exist_ok=True)
    png_prefix = os.path.join(png_dir, base)
    toppm = subprocess.run(["pdftoppm", "-png", "-r", "150", pdf_path, png_prefix], capture_output=True, text=True)
    if toppm.returncode != 0:
        print("BLOCKED: pdftoppm failed")
        print(toppm.stderr)
        sys.exit(1)

    pages = sorted(f for f in os.listdir(png_dir) if f.startswith(base) and f.endswith(".png"))
    print(f"--- rendered {len(pages)} page image(s) to {os.path.relpath(png_dir, REPO_ROOT)} ---")
    for p in pages:
        print(f"  {p}")

    print(f"\nOK: {os.path.relpath(pdf_path, REPO_ROOT)} rendered and inspected.")
    print("Manual step still required: open the PNG page images and visually confirm layout (AGENTS.md).")


if __name__ == "__main__":
    main()
