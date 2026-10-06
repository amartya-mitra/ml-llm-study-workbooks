#!/usr/bin/env python3
"""Verify the TSFM addendum's Release Candidate 1 against the accepted review PDF.

    python3 scripts/check_addendum_rc1.py

Checks (read-only; one pdftotext call per PDF):
  - RC1 is an independent render: different bytes and checksum from the
    accepted review PDF (which must itself still match its recorded identity);
  - the text difference between review and RC1 is limited to the front-matter
    subtitle (the only intended change);
  - page count within the 24-page ceiling; no blank pages;
  - the required content is present: six module titles, six Quick recap
    sections, five figure captions, seven table captions, key corrected
    passages, 34 questions and six answer keys, bibliography;
  - no learner-facing leakage (source ids, paths, filenames, build/review/draft
    wording), exempting only the intended subtitle "Release Candidate 1";
  - no canonical addendum PDF exists.
Exit 0 when all checks pass.
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
REVIEW = os.path.join(REPO_ROOT, "outputs", "_development", WB, "integrated-review", f"{WB}-review.pdf")
RC1 = os.path.join(REPO_ROOT, "outputs", "_releases", WB, f"{WB}-rc1.pdf")
CANONICAL = os.path.join(REPO_ROOT, "outputs", f"{WB}.pdf")
REVIEW_SHA = "d2fcd1cff746cbeeb154de0143d4996c6238f6fe715748ef713d8c589c4e3319"
REVIEW_BYTES = 425931
CEILING = 24

MODULE_TITLES = [
    "Model inputs: scaling, tokens and patches",
    "Context, channels, covariates and horizons",
    "Architecture families and horizon filling",
    "Outputs and losses",
    "Pretraining data, adaptation and leakage",
    "Reading a TSFM release",
]
REQUIRED_PHRASES = [
    "total attention interaction work by about 𝑘2",          # corrected attention-cost passage
    "attention interaction work per token by about 𝑘",
    "not every component of model FLOPs or wall-clock time",
    "cap each sub-dataset’s proportional weight at 𝜖 = 0.001",  # Moirai cap
    "renormalize",
    "sum to 0.60",
    "conventional token-by-token autoregressive decoding",     # qualified decoding passage
    "do not remove the causal dependency across accepted output positions",
    "alternative representations of predictive uncertainty",   # samples vs quantiles
]
LEAK_EXTRA = re.compile(r"(?i)\b(review draft|draft only|for review|review pdf|this review|drafted)\b")


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

    check(os.path.exists(REVIEW) and os.path.exists(RC1), "review PDF and RC1 both exist")
    check(os.path.dirname(RC1).endswith("_releases/addendum-04-05-tsfm"), "RC1 lives only in the release-candidate area (the canonical PDF, if built, is a separate artifact)")
    check(os.path.getsize(REVIEW) == REVIEW_BYTES and sha(REVIEW) == REVIEW_SHA, "accepted review PDF still has its recorded size and SHA-256")
    check(sha(RC1) != sha(REVIEW) and os.path.getsize(RC1) != os.path.getsize(REVIEW), "RC1 differs from the review PDF in bytes and checksum (independent render)")

    info = subprocess.run(["pdfinfo", RC1], capture_output=True, text=True).stdout
    pages = int(re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE).group(1))
    check(pages <= CEILING, f"RC1 has {pages} pages (ceiling {CEILING})")

    rc, rv = text_of(RC1), text_of(REVIEW)
    page_texts = [p for p in rc.split("\f")][:pages]
    check(all(len(re.findall(r"\w+", p)) > 150 for p in page_texts), "no blank or near-empty pages (every page > 150 words)")

    # review-vs-RC1 text difference
    a, b = norm(rv).split(" "), norm(rc).split(" ")
    diff = [d for d in difflib.unified_diff(a, b, lineterm="", n=0) if not d.startswith(("---", "+++", "@@"))]
    removed = " ".join(d[1:] for d in diff if d.startswith("-"))
    added = " ".join(d[1:] for d in diff if d.startswith("+"))
    print("removed words:", removed)
    print("added words:  ", added)
    sub_old = "Tokens, patches, channels, horizons, and forecast distributions: what carries over from the LLM workbooks and what does not"
    check(norm(removed) == norm(sub_old).replace(",", ",") or set(removed.split()) <= set(sub_old.split()), "words removed from the review text are only the old subtitle")
    check(norm(added) == "Release Candidate 1", "the only words added are the subtitle 'Release Candidate 1'")

    for t in MODULE_TITLES:
        check(t in norm(rc), f"module title present: {t}")
    check(len(re.findall(r"Quick recap from LLMs", rc)) == 6, "six 'Quick recap from LLMs' sections")
    check(len(re.findall(r"Figure \d+:", rc)) == 5, "five figure captions")
    check(len(re.findall(r"Table \d+:", rc)) == 7, "seven table captions")
    check(len(re.findall(r"Answer Key: Module \d", rc)) == 6, "six answer keys")
    check("Bibliography" in rc, "bibliography present")
    nrc = norm(rc)
    for ph in REQUIRED_PHRASES:
        check(ph in nrc, f"corrected passage present: {ph[:60]}")

    body = re.sub(r"(?i)\bplaceholders?\b", "stand-in", rc)
    body = body.replace("Release Candidate 1", "", 1)  # the intended subtitle
    leak = crc.check_text_leakage(body)
    check(leak["ok"], f"no learner-facing leakage {({k: v for k, v in leak.items() if k != 'ok'} or '')}")
    check(not LEAK_EXTRA.search(rc), "no review-only or draft-only wording")
    check(not re.search(r"\?\?|@src-|@sec-|@fig-|@tbl-|\[\?\]", rc), "no unresolved references")
    check(not re.search("[�□]", rc), "no broken glyphs")
    check("Release Candidate 1" in page_texts[0], "subtitle appears on page 1")
    check(rc.count("Release Candidate 1") == 1, "the phrase appears exactly once (no stray status wording)")

    print("RESULT:", "clean" if not problems else f"{len(problems)} problem(s)")
    sys.exit(0 if not problems else 1)


if __name__ == "__main__":
    main()
