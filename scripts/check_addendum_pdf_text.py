#!/usr/bin/env python3
"""Scan the addendum's integrated review PDF text for leakage and defects.

    python3 scripts/check_addendum_pdf_text.py [path/to/review.pdf]

Extracts text with pdftotext (one call) and reports:
  - learner-facing leakage (source ids, filenames, repo paths, review-process
    phrases, commit-like tokens, unresolved placeholder markers), using the
    shared checker with the same single exemption the scoped tests use: the
    ordinary technical word "placeholder" (horizon placeholder inputs);
  - unresolved cross-references or citations ("??", "@src", "@sec", "@fig",
    "@tbl", "[?]");
  - mojibake / replacement glyphs;
  - the page count against the 24-page ceiling, and per-page word counts.
Exit status 0 when clean, 1 otherwise.
"""
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import chapter_review_checks as crc  # noqa: E402

DEFAULT_PDF = os.path.join(REPO_ROOT, "outputs", "_development", "addendum-04-05-tsfm",
                           "integrated-review", "addendum-04-05-tsfm-review.pdf")
CEILING = 24
UNRESOLVED_RE = re.compile(r"\?\?|@src-|@sec-|@fig-|@tbl-|@eq-|\[\?\]")
MOJIBAKE_RE = re.compile("[�□]|Ã[\u0080-¿]|â€")


def main():
    pdf = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF
    info = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    pages = int(re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE).group(1))
    text = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout
    per_page = [len(re.findall(r"\w+", p)) for p in text.split("\f") if p.strip()]

    body = re.sub(r"(?i)\bplaceholders?\b", "stand-in", text)
    body = body.replace("Release Candidate 1", "", 1)  # the intended RC1 subtitle, when scanning the RC1 PDF
    leak = crc.check_text_leakage(body)
    unresolved = sorted(set(UNRESOLVED_RE.findall(text)))
    mojibake = sorted(set(MOJIBAKE_RE.findall(text)))

    print(f"pages: {pages} (ceiling {CEILING})")
    print("words per page:", per_page)
    print("leakage:", {k: v for k, v in leak.items() if k != "ok"} or "none")
    print("unresolved references:", unresolved or "none")
    print("broken glyph patterns:", mojibake or "none")
    ok = leak["ok"] and not unresolved and not mojibake and pages <= CEILING
    print("RESULT:", "clean" if ok else "FINDINGS")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
