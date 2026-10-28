#!/usr/bin/env python3
"""Verify the canonical TSFM addendum PDF (v1.1.0) against its accepted review.

    python3 scripts/check_addendum_final.py

Read-only. Checks: the accepted v1.1.0 review PDF still has its accepted
identity; the v1.0.0 artifacts (RC1, the v1.0.0 review PDF and the archived
v1.0.0 canonical) are unchanged; the final is an independent render
(different bytes from the review); the only text difference from the
accepted review is the title-page subtitle (descriptive subtitle ->
"Final Edition, version 1.1.0"); the page count equals the review's; no
near-empty pages; required content; no RC, review or draft wording and no
learner-facing leakage (the bibliography's pinned source-code commit is
provenance and is exempted explicitly); no unresolved references or broken
glyphs. Exit 0 when everything passes.

(v1.0.0 was checked against Release Candidate 1 with the subtitle
"Final Edition"; that check is preserved in Git history at 39294a2.)
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
DEV = os.path.join(REPO_ROOT, "outputs", "_development", WB)
FINAL = os.path.join(REPO_ROOT, "outputs", f"{WB}.pdf")
REVIEW = os.path.join(DEV, "v1.1.0-review", f"{WB}-v1.1.0-review.pdf")
REVIEW_SHA = "e3268c0d80f78c68e39334c9a8dd20305eb3049971d1d8285e08bba67e28887d"
REVIEW_BYTES = 508460
REVIEW_PAGES = 23
SUBTITLE = "Final Edition, version 1.1.0"
DESCRIPTIVE_SUBTITLE = ("Tokens, patches, channels, horizons, and forecast distributions: "
                        "what carries over from the LLM workbooks and what does not")
# v1.0.0 artifacts that must stay byte-identical
PRESERVED = {
    os.path.join(REPO_ROOT, "outputs", "_releases", WB, f"{WB}-rc1.pdf"):
        "a1599e499f3f02816961a7b78efcdef020dec5acfd150ce536c36a6e9b97286a",
    os.path.join(DEV, "integrated-review", f"{WB}-review.pdf"):
        "d2fcd1cff746cbeeb154de0143d4996c6238f6fe715748ef713d8c589c4e3319",
    os.path.join(DEV, "v1.0.0-canonical-archive", f"{WB}-v1.0.0.pdf"):
        "b7096e9b9291dc4319f8f3740303b42dcf784d3ec80bb2fb63cc66f7ac242b65",
}
PINNED_COMMIT = "a534bdbd244d64f3d9d743f46c7bf6fc330ed4ff"  # src-71 citation: provenance, not leakage
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
    "conventional token-by-token autoregressive decoding",
    "alternative representations of predictive uncertainty",
    "Decoupled Horizon Forecasting: forecast tokens instead of masks",
    "reads the valid context patches, itself and the earlier forecast tokens",
    "forecast tokens read the valid context, themselves",
    "The inference code is under Apache-2.0",
    "global consolidated monthly revenue above $20 million",
    "does not interpret them",
]
BAD_WORDING = re.compile(r"(?i)release candidate|\brc\s?\d|review draft|draft only|for review|review pdf|this review|\bdrafted\b|pending human review")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def text_of(pdf):
    return subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout


def pages_of(pdf):
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    return int(re.search(r"^Pages:\s+(\d+)", out, re.MULTILINE).group(1))


def norm(t):
    return re.sub(r"\s+", " ", t).strip()


def main():
    problems = []

    def check(cond, msg):
        print(("PASS " if cond else "FAIL ") + msg)
        if not cond:
            problems.append(msg)

    check(os.path.exists(FINAL) and os.path.exists(REVIEW), "final and accepted v1.1.0 review PDFs exist")
    if problems:
        print("RESULT:", f"{len(problems)} problem(s)")
        sys.exit(1)
    check(os.path.getsize(REVIEW) == REVIEW_BYTES and sha(REVIEW) == REVIEW_SHA,
          "accepted v1.1.0 review PDF still has its accepted size and SHA-256")
    for path, expected in PRESERVED.items():
        check(os.path.exists(path) and sha(path) == expected,
              f"v1.0.0 artifact unchanged: {os.path.relpath(path, REPO_ROOT)}")
    check(sha(FINAL) != REVIEW_SHA, "final differs in bytes from the review PDF (independent render)")
    pages = pages_of(FINAL)
    check(pages == REVIEW_PAGES == pages_of(REVIEW), f"final has {pages} pages, same as the accepted review")
    check(pages <= CEILING, f"within the {CEILING}-page ceiling")

    fin, rev = text_of(FINAL), text_of(REVIEW)
    fpages, rpages = fin.split("\f")[:pages], rev.split("\f")[:pages]
    check(all(len(re.findall(r"\w+", p)) > 150 for p in fpages), "no blank or near-empty pages")
    changed = [i + 1 for i, (a, b) in enumerate(zip(fpages, rpages)) if norm(a) != norm(b)]
    check(changed == [1], f"only page 1 differs in text from the review (changed pages: {changed})")
    a, b = norm(rev).split(" "), norm(fin).split(" ")
    diff = [d for d in difflib.unified_diff(a, b, lineterm="", n=0) if not d.startswith(("---", "+++", "@@"))]
    removed = " ".join(d[1:] for d in diff if d.startswith("-"))
    added = " ".join(d[1:] for d in diff if d.startswith("+"))
    print("removed words:", removed)
    print("added words:  ", added)
    check(removed == DESCRIPTIVE_SUBTITLE and added == SUBTITLE,
          "the only text difference from the accepted review is the edition subtitle")

    nf = norm(fin)
    check(SUBTITLE in norm(fpages[0]) and fin.count("Final Edition") == 1,
          f"title page carries '{SUBTITLE}' exactly once")
    check("Addendum 04–05: From Language Models to Time-Series Foundation Models" in norm(fpages[0]), "title present")
    check(not BAD_WORDING.search(fin), "no RC, review or draft wording")
    for t in MODULE_TITLES:
        check(t in nf, f"module title present: {t}")
    check(len(re.findall(r"Quick recap from LLMs", fin)) == 6, "six Quick recap sections")
    check(len(re.findall(r"Figure \d+:", fin)) == 6, "six figure captions")
    check(len(re.findall(r"Table \d+:", fin)) == 7, "seven table captions")
    check(len(re.findall(r"Answer Key: Module \d", fin)) == 6, "six answer keys")
    check("Bibliography" in fin and PINNED_COMMIT in fin,
          "bibliography present with the pinned source-code commit (provenance)")
    for ph in REQUIRED:
        check(ph in nf, f"required passage present: {ph[:56]}")
    body = re.sub(r"(?i)\bplaceholders?\b", "stand-in", fin)
    body = body.replace(PINNED_COMMIT, "").replace(PINNED_COMMIT[:7], "")
    leak = crc.check_text_leakage(body)
    check(leak["ok"], f"no learner-facing leakage {({k: v for k, v in leak.items() if k != 'ok'} or '')}")
    check(not re.search(r"\?\?|@src-|@sec-|@fig-|@tbl-|\[\?\]", fin), "no unresolved references")
    check(not re.search("[�□]", fin), "no broken glyphs")
    print("RESULT:", "clean" if not problems else f"{len(problems)} problem(s)")
    sys.exit(0 if not problems else 1)


if __name__ == "__main__":
    main()
