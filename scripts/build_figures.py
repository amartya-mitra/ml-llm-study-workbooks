#!/usr/bin/env python3
"""Run every figures/source/*.py generator script to (re)build
figures/rendered/*.svg.

Each figure script is expected to be runnable standalone
(`python3 figures/source/<name>.py`) and to write its own output; this
script just discovers and invokes all of them, so a single command
rebuilds every figure after a palette or content change.
"""
import glob
import os
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIGURES_SOURCE = os.path.join(REPO_ROOT, "figures", "source")
SKIP_PREFIXES = ("_",)  # helper modules like _svg_helpers.py are not standalone figures


def find_figure_scripts():
    scripts = sorted(glob.glob(os.path.join(FIGURES_SOURCE, "*.py")))
    return [s for s in scripts if not os.path.basename(s).startswith(SKIP_PREFIXES)]


def main():
    scripts = find_figure_scripts()
    if not scripts:
        print("No figure scripts found under figures/source/")
        return

    failures = []
    for script in scripts:
        rel = os.path.relpath(script, REPO_ROOT)
        result = subprocess.run([sys.executable, script], cwd=REPO_ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            failures.append(rel)
            print(f"[FAIL] {rel}\n{result.stderr}")
        else:
            print(f"[ OK ] {rel}: {result.stdout.strip()}")

    if failures:
        print(f"\n{len(failures)} figure script(s) failed: {failures}")
        sys.exit(1)
    print(f"\nAll {len(scripts)} figure script(s) ran successfully.")


if __name__ == "__main__":
    main()
