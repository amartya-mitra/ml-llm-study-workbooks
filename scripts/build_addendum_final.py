#!/usr/bin/env python3
"""Reproducible canonical (final edition) builder for the TSFM addendum.

    python3 scripts/build_addendum_final.py

Renders workbooks/addendum-04-05-tsfm/index.qmd (accepted, frozen content)
from source. The only learner-facing difference from Release Candidate 1 is
the subtitle: "Release Candidate 1" becomes "Final Edition". RC1 is never
copied or renamed.

Output: outputs/addendum-04-05-tsfm.pdf  (git-ignored; distributed only as a
GitHub Release asset). Also writes page renders, extracted text and a
manifest under the git-ignored outputs/_development/addendum-04-05-tsfm/final/.

Safeguards:
  - refuses to run unless the addendum is accepted_frozen;
  - the subtitle is substituted in a temporary staging copy (the frozen
    source is never edited); the build fails if the expected substitution
    is absent or the index.qmd subtitle is not the accepted descriptive one;
  - the staging files are removed even on failure;
  - an existing canonical PDF is replaced only if its SHA-256 matches the
    previous build manifest (verified provenance); otherwise the script stops.
    A replaced file is first preserved with a hash suffix (AGENTS.md).
RC1, the accepted review PDF and all development artifacts are untouched.

Requires the ml-workbooks conda env's quarto, typst and poppler tools.
Steps run one after another in the foreground.
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
OUTPUT_PDF = os.path.join(REPO_ROOT, "outputs", f"{WB_ID}.pdf")
DEV_DIR = os.path.join(REPO_ROOT, "outputs", "_development", WB_ID, "final")
MANIFEST = os.path.join(DEV_DIR, "final-manifest.json")
STAGING_QMD = os.path.join(WB_DIR, "final-build.qmd")
STAGING_PDF = os.path.join(WB_DIR, "final-build.pdf")
FINAL_SUBTITLE = "Final Edition"
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


def check_existing_canonical():
    """Return True if an existing canonical PDF may be replaced (verified provenance)."""
    if not os.path.exists(OUTPUT_PDF):
        return False
    if not os.path.exists(MANIFEST):
        sys.exit("BLOCKED: an unexpected canonical PDF exists with no build manifest; not overwriting")
    with open(MANIFEST, encoding="utf-8") as f:
        recorded = json.load(f).get("sha256")
    if sha256(OUTPUT_PDF) != recorded:
        sys.exit("BLOCKED: the existing canonical PDF does not match its recorded build; not overwriting")
    return True


def main():
    require_accepted()
    replace_existing = check_existing_canonical()
    env = tool_env()
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

    print("--- step 2: staging copy with the Final Edition subtitle ---")
    with open(os.path.join(WB_DIR, "index.qmd"), encoding="utf-8") as f:
        src = f.read()
    if "Release Candidate" in src:
        sys.exit("BLOCKED: the frozen index.qmd unexpectedly contains RC wording")
    new_src, n = SUBTITLE_RE.subn(f'subtitle: "{FINAL_SUBTITLE}"', src, count=1)
    if n != 1 or f'subtitle: "{FINAL_SUBTITLE}"' not in new_src:
        sys.exit("BLOCKED: expected subtitle substitution did not happen")
    with open(STAGING_QMD, "w", encoding="utf-8") as f:
        f.write(new_src)

    try:
        print("--- step 3: render ---")
        r = run(["quarto", "render", STAGING_QMD, "--to", "typst"], env=env)
        if r.returncode != 0 or not os.path.exists(STAGING_PDF):
            print(r.stderr[-2500:])
            sys.exit("BLOCKED: quarto render failed")
        print("--- step 4: place canonical PDF ---")
        if replace_existing:
            aside = f"{OUTPUT_PDF}.prev-{sha256(OUTPUT_PDF)[:12]}"
            shutil.move(OUTPUT_PDF, aside)
            print("preserved previous canonical build as " + os.path.relpath(aside, REPO_ROOT))
        shutil.copy2(STAGING_PDF, OUTPUT_PDF)
    finally:
        for p in (STAGING_QMD, STAGING_PDF):
            if os.path.exists(p):
                os.remove(p)

    print("--- step 5: fresh page renders, text, manifest ---")
    pages_dir = os.path.join(DEV_DIR, "pages")
    if os.path.isdir(pages_dir):
        shutil.rmtree(pages_dir)
    os.makedirs(pages_dir)
    r = run(["pdftoppm", "-png", "-r", str(DPI), OUTPUT_PDF, os.path.join(pages_dir, "page")], env=env)
    if r.returncode != 0:
        sys.exit("BLOCKED: pdftoppm failed: " + r.stderr[-500:])
    run(["pdftotext", "-layout", OUTPUT_PDF, os.path.join(DEV_DIR, "final.txt")], env=env)
    info = run(["pdfinfo", OUTPUT_PDF], env=env).stdout
    pages = int(re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE).group(1))
    with open(os.path.join(DEV_DIR, "final.txt"), encoding="utf-8") as f:
        words = len(re.findall(r"\w+", f.read()))
    manifest = {
        "workbook": WB_ID,
        "edition": "final",
        "path": os.path.relpath(OUTPUT_PDF, REPO_ROOT),
        "page_count": pages,
        "page_ceiling": PAGE_CEILING,
        "within_ceiling": pages <= PAGE_CEILING,
        "word_count": words,
        "bytes": os.path.getsize(OUTPUT_PDF),
        "sha256": sha256(OUTPUT_PDF),
        "subtitle": FINAL_SUBTITLE,
    }
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(json.dumps(manifest, indent=2))
    if pages > PAGE_CEILING:
        sys.exit(f"FAIL: {pages} pages exceeds the {PAGE_CEILING}-page ceiling")


if __name__ == "__main__":
    main()
