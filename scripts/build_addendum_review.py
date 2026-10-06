#!/usr/bin/env python3
"""Scoped review-build entry point for the TSFM addendum.

    python3 scripts/build_addendum_review.py

Builds ONE integrated development/review PDF of
workbooks/addendum-04-05-tsfm/index.qmd and its page images under
outputs/_development/addendum-04-05-tsfm/integrated-review/. It never
writes a canonical PDF under outputs/ and never creates a release
candidate or release directory.

Steps (strictly sequential, one process at a time):
  1. regenerate the addendum's worked-example data and figures,
  2. render index.qmd with Quarto/Typst,
  3. copy the PDF to the review directory (an existing review PDF is
     first preserved with a hash suffix),
  4. clear stale page renders and render fresh page PNGs,
  5. write a contact sheet and a small manifest,
  6. remove the Quarto staging PDF from the source directory.

Requires the ml-workbooks conda env's quarto, typst and poppler tools.
"""
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WB_ID = "addendum-04-05-tsfm"
WB_DIR = os.path.join(REPO_ROOT, "workbooks", WB_ID)
REVIEW_DIR = os.path.join(REPO_ROOT, "outputs", "_development", WB_ID, "integrated-review")
REVIEW_PDF = os.path.join(REVIEW_DIR, f"{WB_ID}-review.pdf")
CONDA_ENV = os.environ.get("ML_WORKBOOKS_ENV", "/mnt/home/amitra/.conda/envs/ml-workbooks")
PAGE_CEILING = 24
DPI = 150


def tool_env():
    env = dict(os.environ)
    env["PATH"] = os.path.join(CONDA_ENV, "bin") + os.pathsep + env.get("PATH", "")
    script = os.path.join(CONDA_ENV, "etc", "conda", "activate.d", "quarto.sh")
    if os.path.exists(script):
        with open(script, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"\s*export\s+([A-Z_]+)=(\S+)", line)
                if m and "build_artifacts" not in m.group(2):
                    env[m.group(1)] = m.group(2)
    return env


def run(cmd, env=None):
    print("$ " + " ".join(cmd))
    return subprocess.run(cmd, cwd=REPO_ROOT, env=env, capture_output=True, text=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    env = tool_env()
    os.makedirs(REVIEW_DIR, exist_ok=True)

    print("--- step 1: worked-example data and figures ---")
    for script in sorted(glob.glob(os.path.join(WB_DIR, "data", "worked-examples", "w*.py"))):
        r = run([sys.executable, script])
        if r.returncode != 0:
            print(r.stderr[-1500:])
            sys.exit("BLOCKED: worked-example script failed: " + os.path.basename(script))
    for script in sorted(glob.glob(os.path.join(WB_DIR, "figures", "source", "fig_*.py"))):
        r = run([sys.executable, script])
        if r.returncode != 0:
            print(r.stderr[-1500:])
            sys.exit("BLOCKED: figure script failed: " + os.path.basename(script))

    print("--- step 2: render ---")
    index_qmd = os.path.join(WB_DIR, "index.qmd")
    r = run(["quarto", "render", index_qmd, "--to", "typst"], env=env)
    print(r.stdout[-800:])
    staging_pdf = os.path.join(WB_DIR, "index.pdf")
    if r.returncode != 0 or not os.path.exists(staging_pdf):
        print(r.stderr[-2500:])
        sys.exit("BLOCKED: quarto render failed")

    print("--- step 3: copy PDF ---")
    if os.path.exists(REVIEW_PDF):
        aside = f"{REVIEW_PDF}.prev-{sha256(REVIEW_PDF)[:12]}"
        shutil.move(REVIEW_PDF, aside)
        print("preserved previous review PDF as " + os.path.relpath(aside, REPO_ROOT))
    shutil.copy2(staging_pdf, REVIEW_PDF)

    info = run(["pdfinfo", REVIEW_PDF], env=env).stdout
    pages = int(re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE).group(1))

    print("--- step 4: fresh page renders ---")
    pages_dir = os.path.join(REVIEW_DIR, "pages")
    if os.path.isdir(pages_dir):
        shutil.rmtree(pages_dir)
    os.makedirs(pages_dir)
    r = run(["pdftoppm", "-png", "-r", str(DPI), REVIEW_PDF, os.path.join(pages_dir, "page")], env=env)
    if r.returncode != 0:
        sys.exit("BLOCKED: pdftoppm failed: " + r.stderr[-500:])
    page_files = sorted(os.listdir(pages_dir))

    print("--- step 5: contact sheet and manifest ---")
    items = "\n".join(f'<figure><img src="pages/{p}" loading="lazy"><figcaption>{p}</figcaption></figure>' for p in page_files)
    with open(os.path.join(REVIEW_DIR, "contact-sheet.html"), "w", encoding="utf-8") as f:
        f.write("<!doctype html><html><head><meta charset=\"utf-8\"><title>Review contact sheet</title>"
                "<style>body{font-family:sans-serif;background:#222;margin:0;padding:1rem}"
                "div{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px}"
                "img{width:100%;border:1px solid #555}figcaption{color:#aaa;font-size:.7rem;text-align:center}"
                f"</style></head><body><div>{items}</div></body></html>")
    manifest = {
        "workbook": WB_ID,
        "status": "accepted_frozen",
        "pdf": os.path.relpath(REVIEW_PDF, REPO_ROOT),
        "page_count": pages,
        "page_ceiling": PAGE_CEILING,
        "within_ceiling": pages <= PAGE_CEILING,
        "sha256": sha256(REVIEW_PDF),
        "note": "Development/review artifact. Not a canonical PDF, release candidate or release.",
    }
    with open(os.path.join(REVIEW_DIR, "review-manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("--- step 6: remove staging PDF ---")
    os.remove(staging_pdf)

    print(json.dumps(manifest, indent=2))
    if pages > PAGE_CEILING:
        sys.exit(f"FAIL: {pages} pages exceeds the {PAGE_CEILING}-page ceiling")


if __name__ == "__main__":
    main()
