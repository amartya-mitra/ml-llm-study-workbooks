#!/usr/bin/env python3
"""Reproducible Release Candidate 1 builder for the TSFM addendum.

    python3 scripts/build_addendum_rc1.py

Renders workbooks/addendum-04-05-tsfm/index.qmd (accepted, frozen content)
with exactly one change: the learner-facing subtitle becomes
"Release Candidate 1". The RC1 PDF is an independent Quarto/Typst render
from source; it is never a copy or rename of the review PDF.

Writes ONLY:
  outputs/_releases/addendum-04-05-tsfm/addendum-04-05-tsfm-rc1.pdf
and, under the git-ignored development area,
  outputs/_development/addendum-04-05-tsfm/rc1/ (page renders, text, manifest).

Refuses to run unless the addendum is accepted_frozen in the status
registry. If an RC1 PDF already exists it is preserved with a hash suffix
before being replaced (AGENTS.md). Never creates a canonical PDF
(outputs/addendum-04-05-tsfm.pdf), an RC2, a tag or a release.

Steps run strictly one after another: regenerate worked-example data and
figures (deterministic), render, copy, fresh page renders, manifest, remove
the temporary staging files.

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
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from _yaml_lite import safe_load_path  # noqa: E402

WB_ID = "addendum-04-05-tsfm"
WB_DIR = os.path.join(REPO_ROOT, "workbooks", WB_ID)
RC_DIR = os.path.join(REPO_ROOT, "outputs", "_releases", WB_ID)
RC_PDF = os.path.join(RC_DIR, f"{WB_ID}-rc1.pdf")
DEV_DIR = os.path.join(REPO_ROOT, "outputs", "_development", WB_ID, "rc1")
STAGING_QMD = os.path.join(WB_DIR, "rc1-build.qmd")
STAGING_PDF = os.path.join(WB_DIR, "rc1-build.pdf")
SUBTITLE = "Release Candidate 1"
PAGE_CEILING = 24
DPI = 150
CONDA_ENV = os.environ.get("ML_WORKBOOKS_ENV", "/mnt/home/amitra/.conda/envs/ml-workbooks")
SUBTITLE_RE = re.compile(r'^subtitle:\s*".*"\s*$', re.MULTILINE)


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


def require_accepted():
    reg = safe_load_path(os.path.join(REPO_ROOT, "config", "chapter-status-registry.yaml"))
    entry = (reg.get("workbooks") or {}).get(WB_ID) or {}
    if entry.get("status") != "accepted_frozen":
        sys.exit(f"BLOCKED: {WB_ID} is not accepted_frozen in config/chapter-status-registry.yaml")
    pub = (reg.get("publications") or {}).get(WB_ID) or {}
    if pub.get("status") in ("canonical_built", "published"):
        sys.exit("BLOCKED: publication record is already past the release-candidate stage")


def main():
    require_accepted()
    env = tool_env()
    os.makedirs(RC_DIR, exist_ok=True)
    os.makedirs(DEV_DIR, exist_ok=True)

    print("--- step 1: deterministic worked-example data and figures ---")
    for script in sorted(glob.glob(os.path.join(WB_DIR, "data", "worked-examples", "w*.py"))):
        r = run([sys.executable, script])
        if r.returncode != 0:
            sys.exit("BLOCKED: worked-example script failed: " + os.path.basename(script) + "\n" + r.stderr[-800:])
    for script in sorted(glob.glob(os.path.join(WB_DIR, "figures", "source", "fig_*.py"))):
        r = run([sys.executable, script])
        if r.returncode != 0:
            sys.exit("BLOCKED: figure script failed: " + os.path.basename(script) + "\n" + r.stderr[-800:])

    print("--- step 2: write staging source (subtitle replaced, nothing else) ---")
    with open(os.path.join(WB_DIR, "index.qmd"), encoding="utf-8") as f:
        src = f.read()
    new_src, n = SUBTITLE_RE.subn(f'subtitle: "{SUBTITLE}"', src, count=1)
    if n != 1:
        sys.exit("BLOCKED: could not find the subtitle line in index.qmd")
    with open(STAGING_QMD, "w", encoding="utf-8") as f:
        f.write(new_src)

    try:
        print("--- step 3: render ---")
        r = run(["quarto", "render", STAGING_QMD, "--to", "typst"], env=env)
        if r.returncode != 0 or not os.path.exists(STAGING_PDF):
            print(r.stderr[-2500:])
            sys.exit("BLOCKED: quarto render failed")

        print("--- step 4: place RC1 ---")
        if os.path.exists(RC_PDF):
            aside = f"{RC_PDF}.prev-{sha256(RC_PDF)[:12]}"
            shutil.move(RC_PDF, aside)
            print("preserved previous RC1 as " + os.path.relpath(aside, REPO_ROOT))
        shutil.copy2(STAGING_PDF, RC_PDF)
    finally:
        for p in (STAGING_QMD, STAGING_PDF):
            if os.path.exists(p):
                os.remove(p)

    print("--- step 5: fresh page renders, text, manifest ---")
    pages_dir = os.path.join(DEV_DIR, "pages")
    if os.path.isdir(pages_dir):
        shutil.rmtree(pages_dir)
    os.makedirs(pages_dir)
    r = run(["pdftoppm", "-png", "-r", str(DPI), RC_PDF, os.path.join(pages_dir, "page")], env=env)
    if r.returncode != 0:
        sys.exit("BLOCKED: pdftoppm failed: " + r.stderr[-500:])
    text = run(["pdftotext", "-layout", RC_PDF, os.path.join(DEV_DIR, "rc1.txt")], env=env)
    info = run(["pdfinfo", RC_PDF], env=env).stdout
    pages = int(re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE).group(1))
    with open(os.path.join(DEV_DIR, "rc1.txt"), encoding="utf-8") as f:
        words = len(re.findall(r"\w+", f.read()))
    manifest = {
        "workbook": WB_ID,
        "release_candidate": 1,
        "path": os.path.relpath(RC_PDF, REPO_ROOT),
        "page_count": pages,
        "page_ceiling": PAGE_CEILING,
        "within_ceiling": pages <= PAGE_CEILING,
        "word_count": words,
        "bytes": os.path.getsize(RC_PDF),
        "sha256": sha256(RC_PDF),
        "subtitle": SUBTITLE,
        "note": "Release candidate awaiting independent review. Not a canonical PDF; no tag or release exists.",
    }
    with open(os.path.join(DEV_DIR, "rc1-manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(json.dumps(manifest, indent=2))
    if pages > PAGE_CEILING:
        sys.exit(f"FAIL: {pages} pages exceeds the {PAGE_CEILING}-page ceiling")


if __name__ == "__main__":
    main()
