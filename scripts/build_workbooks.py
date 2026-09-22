#!/usr/bin/env python3
"""Render every .qmd file under workbooks/ with Quarto, if Quarto is
available.

This intentionally does NOT try to fake success if Quarto/Typst are
missing: it reports the exact blocker and exits non-zero rather than
silently doing nothing. See reports/bootstrap_report.md for the current
rendering-stack status in this environment.
"""
import glob
import os
import shutil
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKBOOKS_DIR = os.path.join(REPO_ROOT, "workbooks")


def find_qmd_files():
    return sorted(glob.glob(os.path.join(WORKBOOKS_DIR, "**", "*.qmd"), recursive=True))


def main():
    if shutil.which("quarto") is None:
        print("BLOCKED: 'quarto' is not on PATH in this environment.")
        print("See reports/bootstrap_environment.md and reports/bootstrap_report.md")
        print("for the proposed user-local installation plan. Not attempting to render.")
        sys.exit(2)

    qmd_files = find_qmd_files()
    if not qmd_files:
        print("No .qmd files found under workbooks/ yet.")
        return

    failures = []
    for qmd in qmd_files:
        rel = os.path.relpath(qmd, REPO_ROOT)
        result = subprocess.run(["quarto", "render", qmd], cwd=REPO_ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            failures.append(rel)
            print(f"[FAIL] {rel}\n{result.stderr}")
        else:
            print(f"[ OK ] {rel}")

    if failures:
        print(f"\n{len(failures)} file(s) failed to render: {failures}")
        sys.exit(1)
    print(f"\nAll {len(qmd_files)} workbook file(s) rendered successfully.")


if __name__ == "__main__":
    main()
