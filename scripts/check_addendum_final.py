#!/usr/bin/env python3
"""Verify the canonical TSFM addendum PDF against the accepted RC1.

    python3 scripts/check_addendum_final.py

Read-only. Checks: independent render (different bytes and hash from RC1 and
from the review PDF, both of which must still match their accepted
identities); the only text difference from RC1 is the subtitle ("Release
Candidate 1" -> "Final Edition"); page count within the ceiling; no
near-empty pages; required content; no RC, review or draft wording and no
learner-facing leakage; no unresolved references or broken glyphs.
Exit 0 when everything passes.
"""
import difflib
import hashlib
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import chapter_review_checks as crc  # noqa: E402

WB = "addendum-04-05-tsfm"
FINAL = os.path.join(REPO_ROOT, "outputs", f"{WB}.pdf")
RC1 = os.path.join(REPO_ROOT, "outputs", "_releases", WB, f"{WB}-rc1.pdf")
REVIEW = os.path.join(REPO_ROOT, "outputs", "_development", WB, "integrated-review", f"{WB}-review.pdf")
RC1_SHA = "a1599e499f3f02816961a7b78efcdef020dec5acfd150ce536c36a6e9b97286a"
RC1_BYTES = 425789
REVIEW_SHA = "d2fcd1cff746cbeeb154de0143d4996c6238f6fe715748ef713d8c589c4e3319"
CEILING = 24
MODULE_TITLES = [
    "Model inputs: scaling, tokens and patches",
    "Context, channels, covariates and horizons",
    "Architecture families and horizon filling",
    "Outputs and losses",
    "Pretraining data, adaptation and leakage",
    "Reading a TSFM release",
]
REQUIRED = [
    "total attention interaction work by about 𝑘2",
    "attention interaction work per token by about 𝑘",
    "not every component of model FLOPs or wall-clock time",
    "cap each sub-dataset’s proportional weight at 𝜖 = 0.001",
    "renormalize",
    "sum to 0.60",
    "conventional token-by-token autoregressive decoding",
    "do not remove the causal dependency across accepted output positions",
    "alternative representations of predictive uncertainty",
]
BAD_WORDING = re.compile(r"(?i)release candidate|\brc\s?\d|review draft|draft only|for review|review pdf|this review|\bdrafted\b")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def text_of(pdf):
    return subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout


def norm(t):
    return re.sub(r"\s+", " ", t).strip()


def main():
    problems = []

    def check(cond, msg):
        print(("PASS " if cond else "FAIL ") + msg)
        if not cond:
            problems.append(msg)

    check(all(os.path.exists(p) for p in (FINAL, RC1, REVIEW)), "final, RC1 and review PDFs all exist")
    check(os.path.getsize(RC1) == RC1_BYTES and sha(RC1) == RC1_SHA, "accepted RC1 still has its recorded size and SHA-256")
    check(sha(REVIEW) == REVIEW_SHA, "accepted review PDF still matches its recorded SHA-256")
    check(sha(FINAL) not in (RC1_SHA, REVIEW_SHA) and os.path.getsize(FINAL) != RC1_BYTES, "final differs from RC1 and the review PDF (independent render)")
    pages = int(re.search(r"^Pages:\s+(\d+)", subprocess.run(["pdfinfo", FINAL], capture_output=True, text=True).stdout, re.MULTILINE).group(1))
    check(pages <= CEILING, f"final has {pages} pages (ceiling {CEILING})")

    fin, rc = text_of(FINAL), text_of(RC1)
    pts = fin.split("\f")[:pages]
    check(all(len(re.findall(r"\w+", p)) > 150 for p in pts), "no blank or near-empty pages")
    a, b = norm(rc).split(" "), norm(fin).split(" ")
    diff = [d for d in difflib.unified_diff(a, b, lineterm="", n=0) if not d.startswith(("---", "+++", "@@"))]
    removed = " ".join(d[1:] for d in diff if d.startswith("-"))
    added = " ".join(d[1:] for d in diff if d.startswith("+"))
    print("removed words:", removed)
    print("added words:  ", added)
    check(removed == "Release Candidate 1" and added == "Final Edition", "the only text difference from RC1 is the subtitle")

    nf = norm(fin)
    check("Final Edition" in pts[0] and fin.count("Final Edition") == 1, "title page carries the 'Final Edition' subtitle exactly once")
    check("Addendum 04–05: From Language Models to Time-Series Foundation Models" in norm(pts[0]), "title present")
    check(not BAD_WORDING.search(fin), "no RC, review or draft wording")
    for t in MODULE_TITLES:
        check(t in nf, f"module title present: {t}")
    check(len(re.findall(r"Quick recap from LLMs", fin)) == 6, "six Quick recap sections")
    check(len(re.findall(r"Figure \d+:", fin)) == 5, "five figure captions")
    check(len(re.findall(r"Table \d+:", fin)) == 7, "seven table captions")
    check(len(re.findall(r"Answer Key: Module \d", fin)) == 6, "six answer keys")
    check("Bibliography" in fin, "bibliography present")
    for ph in REQUIRED:
        check(ph in nf, f"corrected passage present: {ph[:56]}")
    body = re.sub(r"(?i)\bplaceholders?\b", "stand-in", fin)
    leak = crc.check_text_leakage(body)
    check(leak["ok"], f"no learner-facing leakage {({k: v for k, v in leak.items() if k != 'ok'} or '')}")
    check(not re.search(r"\?\?|@src-|@sec-|@fig-|@tbl-|\[\?\]", fin), "no unresolved references")
    check(not re.search("[�□]", fin), "no broken glyphs")
    print("RESULT:", "clean" if not problems else f"{len(problems)} problem(s)")
    sys.exit(0 if not problems else 1)


if __name__ == "__main__":
    main()
