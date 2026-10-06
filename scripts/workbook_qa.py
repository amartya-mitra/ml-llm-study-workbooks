#!/usr/bin/env python3
"""Deterministic QA entry point for any workbook in this repo.

    python3 scripts/workbook_qa.py --workbook 05-llm-training

One stable invocation, no environment-variable variants and no ad hoc
flags that change behavior -- meaningful differences (which workbook,
which canonical PDF name) live in WORKBOOK_REGISTRY below, in committed
config, not in how this script is invoked. This is the fixed run
command a local OpenResearch project (or any other orchestration layer)
should point at for this workbook's QA/RC cycle.

Steps (see README/AGENTS.md for the conventions this enforces):
    1. verify source structure (index.qmd, chapters/, solutions/, etc.)
    2. build the current candidate PDF via Quarto/Typst
    3. run the repo's test suite (tests/)
    4. run registry / question-bank validators
    5. extract PDF text
    6. scan extracted text for: internal paths, source-registry ids,
       commit metadata, stale release-status wording, duplicated
       chapter numbering, missing/incomplete chapter headings,
       unresolved placeholders (TODO/TBD/FIXME/lorem ipsum), and
       mojibake/encoding-failure characters
    7. verify page count and canonical output filename
    8. render every PDF page to a development-only directory
       (outputs/_development/<workbook>/qa-runs/<short-sha>/pages/)
    9. generate an HTML contact sheet of those page renders (pure
       stdlib -- no Pillow/ImageMagick available in this environment,
       confirmed by direct check; an HTML grid is the honest
       equivalent, not a stand-in claiming raster compositing)
   10. write a JSON summary with pass/fail, commit SHA, PDF path, page
       count, word count, test results, text-check results, rendered-
       page directory, and unresolved warnings

Exits 0 if every check passed, 1 otherwise. Never claims success for a
step it could not actually run (e.g. missing quarto/poppler-utils) --
it reports that step as failed/blocked in the JSON instead.
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)  # so "tests.<module>" dotted imports resolve regardless of invocation style
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import chapter_review_checks as crc  # noqa: E402
REQUIRED_TOOLS = ["quarto", "pdfinfo", "pdftotext", "pdffonts", "pdftoppm"]

# One entry per workbook this script knows how to QA. Add a workbook
# here, in one place, rather than branching on workbook id anywhere
# else in this script.
WORKBOOK_REGISTRY = {
    "04-llm-architecture": {
        "title": "Modern LLM Architecture",
        "canonical_pdf": "04-modern-llm-architecture-workbook.pdf",
    },
    "05-llm-training": {
        "title": "LLM Pretraining and Distributed Training",
        "canonical_pdf": "05-llm-training-workbook.pdf",
    },
    "addendum-04-05-tsfm": {
        "title": "Addendum 04-05: From Language Models to Time-Series Foundation Models",
        "canonical_pdf": "addendum-04-05-tsfm.pdf",  # not built: no canonical addendum PDF exists
    },
}

PLACEHOLDER_PATTERNS = [
    r"\bTODO\b", r"\bTBD\b", r"\bFIXME\b", r"\bXXX\b",
    r"lorem ipsum", r"\bPLACEHOLDER\b", r"\[insert",
]

# A commit hash is 7-40 lowercase hex chars. Require a word boundary on
# both sides and a minimum length of 7 to avoid matching ordinary words.
COMMIT_HASH_RE = re.compile(r"\b[0-9a-f]{7,40}\b")

INTERNAL_PATH_PATTERNS = [
    r"/mnt/home/", r"/mnt/[a-z]+/", r"\bworkbooks/[a-z0-9/_-]+\.qmd\b",
    r"\bscripts/[a-z0-9_]+\.py\b", r"\bworkbooks/[a-z0-9/_-]+\.py\b",
]
SOURCE_ID_RE = re.compile(r"\bsrc-\d+\b")
STALE_RC_RE = re.compile(
    r"release candidate [1-9]\b|complete content draft \(release candidate",
    re.IGNORECASE,
)
MOJIBAKE_RE = re.compile(r"[�□]|Ã[\x80-\xBF]|â€[\x80-\x9F]")


def run(cmd, **kw):
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, **kw)


def find_qmd_index(wb_dir):
    p = os.path.join(wb_dir, "index.qmd")
    return p if os.path.exists(p) else None


def check_structure(workbook_id):
    """Step 1: verify source structure exists. Returns (ok, details)."""
    wb_dir = os.path.join(REPO_ROOT, "workbooks", workbook_id)
    expected = {
        "workbook_dir": wb_dir,
        "index_qmd": os.path.join(wb_dir, "index.qmd"),
        "chapters_dir": os.path.join(wb_dir, "chapters"),
        "solutions_dir": os.path.join(wb_dir, "solutions"),
    }
    present = {k: os.path.exists(v) for k, v in expected.items()}
    ok = present["workbook_dir"] and present["index_qmd"]
    return ok, {
        "expected_paths": {k: os.path.relpath(v, REPO_ROOT) for k, v in expected.items()},
        "present": present,
    }


def build_pdf(workbook_id, cfg, run_dir):
    """Step 2: build the candidate PDF via Quarto/Typst.

    Returns (ok, details). Writes/overwrites the canonical PDF at
    outputs/<canonical_pdf> -- this script does not create release
    candidates; see the RC build scripts for that.
    """
    missing = [t for t in REQUIRED_TOOLS if shutil.which(t) is None]
    if missing:
        return False, {"blocked": f"missing required tool(s): {missing}"}

    wb_dir = os.path.join(REPO_ROOT, "workbooks", workbook_id)
    index_qmd = find_qmd_index(wb_dir)
    if index_qmd is None:
        return False, {"blocked": f"no index.qmd under workbooks/{workbook_id}/"}

    render = run(["quarto", "render", index_qmd, "--to", "typst"])
    if render.returncode != 0:
        return False, {
            "blocked": "quarto render failed",
            "stdout_tail": render.stdout[-2000:],
            "stderr_tail": render.stderr[-2000:],
        }

    rendered_pdf = os.path.join(wb_dir, "index.pdf")
    if not os.path.exists(rendered_pdf):
        return False, {"blocked": f"render reported success but {rendered_pdf} not found"}

    output_pdf = os.path.join(REPO_ROOT, "outputs", cfg["canonical_pdf"])
    os.makedirs(os.path.dirname(output_pdf), exist_ok=True)
    backup_path = None
    if os.path.exists(output_pdf):
        # Never silently overwrite a prior canonical PDF (AGENTS.md) --
        # preserve it under this run's own development directory rather
        # than cluttering outputs/ root with another *.pdf.prev-* file.
        stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
        backup_path = os.path.join(run_dir, f"{cfg['canonical_pdf']}.prev-{stamp}")
        shutil.copy2(output_pdf, backup_path)
    shutil.copy2(rendered_pdf, output_pdf)
    result = {"pdf_path": os.path.relpath(output_pdf, REPO_ROOT)}
    if backup_path:
        result["preserved_prior_copy"] = os.path.relpath(backup_path, REPO_ROOT)
    return True, result


def run_tests():
    """Step 3: run the full test suite in-process, no subprocess."""
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.join(REPO_ROOT, "tests"))
    stream = __import__("io").StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=1)
    result = runner.run(suite)
    return result.wasSuccessful(), {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "failure_names": [str(t[0]) for t in result.failures],
        "error_names": [str(t[0]) for t in result.errors],
    }


def run_validators():
    """Step 4: registry + question-bank validators (also cover notation
    and worked-example structure, since those are validated as part of
    the same registry/question-schema checks and the test suite's
    per-chapter worked-example tests)."""
    results = {}
    ok = True
    for name, cmd in [
        ("registry", [sys.executable, "scripts/validate_registry.py"]),
        ("questions", [sys.executable, "scripts/validate_questions.py"]),
    ]:
        r = run(cmd)
        results[name] = {"returncode": r.returncode, "stdout": r.stdout.strip()}
        ok = ok and (r.returncode == 0)
    return ok, results


def extract_text(pdf_path):
    """Step 5."""
    r = run(["pdftotext", pdf_path, "-"])
    return r.returncode == 0, r.stdout


def scan_text(text, source_qmd_files):
    """Step 6: internal paths, source ids, commit metadata, stale RC
    text, duplicated numbering, missing headings, placeholders,
    mojibake. Returns (ok, findings)."""
    findings = {}

    internal_paths = []
    for pat in INTERNAL_PATH_PATTERNS:
        internal_paths += re.findall(pat, text)
    findings["internal_paths"] = sorted(set(internal_paths))

    findings["source_registry_ids"] = sorted(set(SOURCE_ID_RE.findall(text)))

    # Commit-hash-shaped tokens minus common false positives (hex-looking
    # but actually a citation/id token already reported above).
    hash_candidates = set(COMMIT_HASH_RE.findall(text)) - set(findings["source_registry_ids"])
    findings["commit_hash_like_tokens"] = sorted(hash_candidates)[:20]

    findings["stale_release_candidate_wording"] = sorted(set(STALE_RC_RE.findall(text)))

    placeholders = []
    for pat in PLACEHOLDER_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            placeholders.append(pat)
    findings["unresolved_placeholders"] = placeholders

    findings["mojibake_matches"] = len(MOJIBAKE_RE.findall(text))

    # Duplicated numbering / missing headings: check each chapter source
    # file's heading appears in the extracted text, and that no chapter
    # number (e.g. "4 Reducing Attention Cost") appears more than once.
    heading_re = re.compile(r"^##\s+(.+?)\s*\{#sec-ch\d+\}", re.MULTILINE)
    chapter_titles = []
    for qmd_path in source_qmd_files:
        with open(qmd_path, encoding="utf-8") as f:
            content = f.read()
        m = heading_re.search(content)
        if m:
            # Strip any inline Typst/HTML directives before checking presence.
            clean_title = re.sub(r"`[^`]*`\{=typst\}", "", m.group(1)).strip()
            chapter_titles.append(clean_title)

    missing_headings = [t for t in chapter_titles if t not in text]
    findings["missing_or_incomplete_headings"] = missing_headings

    # A table-of-contents line echoes "<N> <Title> ... <page>" with a run
    # of leader dots -- that is the TOC doing its job, not a duplicate
    # heading. Excluding any line containing 3+ consecutive dots (a
    # pattern that essentially never appears in body prose) avoids
    # counting the TOC's own entry against the body heading it points to.
    toc_leader_re = re.compile(r"\.\s*\.\s*\.")
    body_lines = [ln for ln in text.splitlines() if not toc_leader_re.search(ln)]
    body_text = "\n".join(body_lines)
    # [ \t]+ (not \s+) deliberately excludes newlines: \s+ would let a
    # lone page-footer digit (e.g. "3" at the bottom of a page) bridge
    # across blank lines to an unrelated capitalized word starting the
    # next page's text, falsely matching as a second chapter heading.
    number_prefix_re = re.compile(r"^(\d+)[ \t]+[A-Z]", re.MULTILINE)
    numbers = number_prefix_re.findall(body_text)
    dupes = sorted({n for n in numbers if numbers.count(n) > 1}, key=int)
    findings["duplicated_chapter_numbers"] = dupes

    ok = not any([
        findings["internal_paths"],
        findings["source_registry_ids"],
        findings["stale_release_candidate_wording"],
        findings["unresolved_placeholders"],
        findings["mojibake_matches"],
        findings["missing_or_incomplete_headings"],
        findings["duplicated_chapter_numbers"],
    ])
    return ok, findings


def verify_output(pdf_path, cfg):
    """Step 7: page count + filename convention."""
    info = run(["pdfinfo", pdf_path])
    m = re.search(r"^Pages:\s+(\d+)", info.stdout, re.MULTILINE)
    page_count = int(m.group(1)) if m else None
    name_ok = os.path.basename(pdf_path) == cfg["canonical_pdf"]
    return (page_count is not None and name_ok), {
        "page_count": page_count,
        "expected_filename": cfg["canonical_pdf"],
        "actual_filename": os.path.basename(pdf_path),
    }


def render_pages(pdf_path, dev_dir):
    """Step 8: render every page to a development-only directory."""
    pages_dir = os.path.join(dev_dir, "pages")
    os.makedirs(pages_dir, exist_ok=True)
    toppm = run(["pdftoppm", "-png", "-r", "170", pdf_path, os.path.join(pages_dir, "page")])
    if toppm.returncode != 0:
        return False, {"blocked": "pdftoppm failed", "stderr": toppm.stderr}
    pages = sorted(f for f in os.listdir(pages_dir) if f.endswith(".png"))
    return True, {"pages_dir": os.path.relpath(pages_dir, REPO_ROOT), "page_files": pages}


def write_contact_sheet(dev_dir, page_files):
    """Step 9: an HTML grid of page thumbnails. No Pillow/ImageMagick is
    available in this environment (confirmed by direct check), so a
    composited raster contact sheet is not honestly claimable; an HTML
    grid referencing the already-rendered PNGs is the stdlib-only
    equivalent for broad visual inspection."""
    sheet_path = os.path.join(dev_dir, "contact-sheet.html")
    items = "\n".join(
        f'<figure><img src="pages/{p}" loading="lazy"><figcaption>{p}</figcaption></figure>'
        for p in page_files
    )
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Contact sheet</title>
<style>
body {{ font-family: sans-serif; background: #222; color: #eee; margin: 0; padding: 1rem; }}
div.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 8px; }}
figure {{ margin: 0; }}
img {{ width: 100%; border: 1px solid #555; }}
figcaption {{ font-size: 0.7rem; text-align: center; color: #aaa; }}
</style></head>
<body><div class="grid">
{items}
</div></body></html>
"""
    with open(sheet_path, "w", encoding="utf-8") as f:
        f.write(html)
    return os.path.relpath(sheet_path, REPO_ROOT)


def get_commit_sha():
    r = run(["git", "rev-parse", "HEAD"])
    return r.stdout.strip() if r.returncode == 0 else None


def run_chapter_scoped_qa(workbook_id, chapter, review_pdf, dev_dir):
    """Chapter-scoped review-package QA (item 9 of
    docs/chapter-review-checklist.md). Validates one chapter's review
    package -- its source files, claim ledger, questions/solutions,
    worked examples, figures, and (if --review-pdf is given) the
    actual rendered PDF -- without touching or rebuilding anything.

    Every category below is reported separately and independently, so
    a warning in one (e.g. a known pre-existing cross-reference gap in
    an already-accepted chapter) never hides a regression in another.
    """
    wb_dir = os.path.join(REPO_ROOT, "workbooks", workbook_id)
    summary = {
        "workbook": workbook_id,
        "chapter": chapter,
        "review_pdf": os.path.relpath(review_pdf, REPO_ROOT) if review_pdf else None,
        "checks": {},
    }

    try:
        chapter_path, solutions_path = crc.discover_chapter_files(workbook_id, chapter)
    except FileNotFoundError as e:
        summary["checks"]["structure"] = {"ok": False, "issue": str(e)}
        summary["status"] = "fail"
        return summary
    summary["checks"]["structure"] = {
        "ok": True,
        "chapter_path": os.path.relpath(chapter_path, REPO_ROOT),
        "solutions_path": os.path.relpath(solutions_path, REPO_ROOT),
    }
    chapter_slug = crc.chapter_slug_from_path(chapter_path)

    summary["checks"]["sources_and_claim_ledger"] = crc.check_claim_ledger_coverage(wb_dir, workbook_id, chapter)

    summary["checks"]["questions_and_solutions"] = crc.check_question_answer_correspondence(
        chapter_path, solutions_path, os.path.join(wb_dir, "questions.yaml"), chapter_slug,
    )

    we_check = crc.check_worked_example_scoped_test_exists(workbook_id, chapter)
    summary["checks"]["worked_examples"] = we_check

    figure_findings = crc.check_figure_invariant_tests(wb_dir)
    summary["checks"]["figure_invariants"] = {
        "ok": bool(figure_findings) and all(f["has_dedicated_semantic_test"] for f in figure_findings),
        "per_figure": figure_findings,
    }

    summary["checks"]["cross_references"] = crc.check_answer_key_cross_reference(chapter_path, solutions_path)

    if review_pdf and os.path.exists(review_pdf):
        info = run(["pdfinfo", review_pdf])
        m = re.search(r"^Pages:\s+(\d+)", info.stdout, re.MULTILINE)
        page_count = int(m.group(1)) if m else None
        summary["checks"]["build"] = {"ok": page_count is not None, "pdf_path": os.path.relpath(review_pdf, REPO_ROOT)}
        summary["checks"]["rendered_page_count"] = page_count

        text_ok, text = extract_text(review_pdf)
        leakage = crc.check_text_leakage(text) if text_ok else {"ok": False, "issue": "text extraction failed"}
        summary["checks"]["text_leakage"] = leakage

        if page_count:
            density = crc.run_page_density_diagnostics(review_pdf, page_count)
            summary["checks"]["sparse_page_warnings"] = density["sparse_page_flags"]
            summary["checks"]["bibliography_diagnostic"] = density["bibliography_diagnostic"]
        summary["checks"]["full_page_visual_review_completion"] = {
            "automatable": False,
            "note": (
                "Not automatable -- requires a human or a fresh-context adversarial review pass to "
                "actually view every rendered page (see docs/chapter-review-checklist.md item 8). "
                "This QA run does not claim that pass happened."
            ),
        }
    else:
        for key in ("build", "rendered_page_count", "text_leakage", "sparse_page_warnings",
                    "bibliography_diagnostic", "full_page_visual_review_completion"):
            summary["checks"][key] = {"ok": None, "note": "no --review-pdf supplied -- not verified"}

    # Scoped tests: the chapter's own worked-example test(s), plus the
    # workbook-wide scaffold and figure tests every chapter shares.
    scoped_modules = [os.path.splitext(os.path.basename(p))[0] for p in we_check["scoped_worked_example_test_files"]]
    scaffold_candidates = [
        f"test_workbook{workbook_id.split('-')[0]}_scaffold",
    ]
    for mod in scaffold_candidates:
        if os.path.exists(os.path.join(REPO_ROOT, "tests", mod + ".py")):
            scoped_modules.append(mod)
    scoped_modules.append("test_figures")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for mod in scoped_modules:
        try:
            suite.addTests(loader.loadTestsFromName(f"tests.{mod}"))
        except (ImportError, AttributeError) as e:
            summary["checks"].setdefault("scoped_test_load_errors", []).append(f"{mod}: {e}")
    stream = __import__("io").StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=1)
    scoped_result = runner.run(suite)
    summary["checks"]["scoped_tests"] = {
        "modules": scoped_modules,
        "tests_run": scoped_result.testsRun,
        "failures": len(scoped_result.failures),
        "errors": len(scoped_result.errors),
        "failure_names": [str(t[0]) for t in scoped_result.failures],
        "error_names": [f"{t[0]}: {t[1]}" for t in scoped_result.errors],
        "ok": scoped_result.wasSuccessful(),
    }

    full_ok, full_details = run_tests()
    new_failures = crc.new_failures_beyond_baseline(full_details["failure_names"])
    summary["checks"]["full_suite"] = {
        "tests_run": full_details["tests_run"],
        "failures": full_details["failures"],
        "known_preexisting_workbook04_baseline_failures": crc.KNOWN_BASELINE_FAILURES,
        "new_failures_beyond_baseline": new_failures,
        "ok": len(new_failures) == 0,
    }

    hard_fail_keys = ["structure", "sources_and_claim_ledger", "questions_and_solutions", "scoped_tests", "full_suite"]
    warn_keys = ["worked_examples", "figure_invariants", "cross_references", "text_leakage"]
    hard_fail = any(summary["checks"][k].get("ok") is False for k in hard_fail_keys)
    warnings = [k for k in warn_keys if summary["checks"].get(k, {}).get("ok") is False]
    summary["warnings"] = warnings
    summary["status"] = "fail" if hard_fail else ("pass_with_warnings" if warnings else "pass")

    json_path = os.path.join(dev_dir, "chapter-qa-summary.json")
    os.makedirs(dev_dir, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    print(f"\nWrote {os.path.relpath(json_path, REPO_ROOT)}", file=sys.stderr)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", required=True, choices=sorted(WORKBOOK_REGISTRY))
    parser.add_argument("--chapter", default=None,
                         help="two-digit chapter number (e.g. 04) -- switches to chapter-scoped review-package QA")
    parser.add_argument("--review-pdf", default=None,
                         help="path to an already-built standalone chapter review PDF (used with --chapter)")
    args = parser.parse_args()

    workbook_id = args.workbook

    if args.chapter:
        commit_sha = get_commit_sha()
        short_sha = (commit_sha or "unknown")[:12]
        dev_dir = os.path.join(REPO_ROOT, "outputs", "_development", workbook_id, "qa-runs", f"{short_sha}-ch{args.chapter}")
        summary = run_chapter_scoped_qa(workbook_id, args.chapter, args.review_pdf, dev_dir)
        sys.exit(0 if summary["status"] in ("pass", "pass_with_warnings") else 1)

    cfg = WORKBOOK_REGISTRY[workbook_id]
    commit_sha = get_commit_sha()
    short_sha = (commit_sha or "unknown")[:12]

    dev_dir = os.path.join(REPO_ROOT, "outputs", "_development", workbook_id, "qa-runs", short_sha)
    os.makedirs(dev_dir, exist_ok=True)

    summary = {
        "workbook": workbook_id,
        "title": cfg["title"],
        "commit_sha": commit_sha,
        "run_dir": os.path.relpath(dev_dir, REPO_ROOT),
        "generated_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "status": "unknown",
        "steps": {},
        "warnings": [],
    }

    ok, details = check_structure(workbook_id)
    summary["steps"]["structure"] = {"ok": ok, **details}
    if not ok:
        summary["status"] = "fail"
        summary["warnings"].append(
            f"workbooks/{workbook_id}/index.qmd does not exist -- nothing to build yet."
        )
        _finish(summary, dev_dir)
        return

    wb_dir = os.path.join(REPO_ROOT, "workbooks", workbook_id)

    ok, details = build_pdf(workbook_id, cfg, dev_dir)
    summary["steps"]["build"] = {"ok": ok, **details}
    if not ok:
        summary["status"] = "fail"
        _finish(summary, dev_dir)
        return
    pdf_path = os.path.join(REPO_ROOT, details["pdf_path"])

    ok, details = run_tests()
    summary["steps"]["tests"] = {"ok": ok, **details}

    ok2, details2 = run_validators()
    summary["steps"]["validators"] = {"ok": ok2, **details2}

    ok3, text = extract_text(pdf_path)
    summary["steps"]["text_extraction"] = {"ok": ok3, "word_count": len(text.split()) if ok3 else None}
    summary["word_count"] = len(text.split()) if ok3 else None

    chapters_dir = os.path.join(wb_dir, "chapters")
    qmd_files = []
    if os.path.isdir(chapters_dir):
        qmd_files = [os.path.join(chapters_dir, f) for f in sorted(os.listdir(chapters_dir)) if f.endswith(".qmd")]
    ok4, findings = scan_text(text, qmd_files)
    summary["steps"]["text_checks"] = {"ok": ok4, **findings}

    ok5, details5 = verify_output(pdf_path, cfg)
    summary["steps"]["output_verification"] = {"ok": ok5, **details5}
    summary["page_count"] = details5.get("page_count")
    summary["pdf_path"] = os.path.relpath(pdf_path, REPO_ROOT)

    ok6, details6 = render_pages(pdf_path, dev_dir)
    summary["steps"]["page_render"] = {"ok": ok6, **details6}

    if ok6:
        sheet_rel = write_contact_sheet(dev_dir, details6["page_files"])
        summary["steps"]["contact_sheet"] = {"ok": True, "path": sheet_rel}
    else:
        summary["steps"]["contact_sheet"] = {"ok": False, "blocked": "page render failed"}

    all_ok = all(
        summary["steps"][k]["ok"]
        for k in ["build", "tests", "validators", "text_extraction", "text_checks", "output_verification", "page_render", "contact_sheet"]
    )
    summary["status"] = "pass" if all_ok else "fail"
    _finish(summary, dev_dir)


def _finish(summary, dev_dir):
    json_path = os.path.join(dev_dir, "qa-summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    print(f"\nWrote {os.path.relpath(json_path, REPO_ROOT)}", file=sys.stderr)
    sys.exit(0 if summary["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
