#!/usr/bin/env python3
"""Build the Workbook 05 Chapter 4 review PDF end to end:

    1. regenerate every figure (root + workbook-local)
    2. render workbooks/05-llm-training/ch04-review.qmd via Quarto/
       Typst (a standalone, chapter-4-only document -- NOT the
       workbook's canonical index.qmd)
    3. copy the result, plus page renders and a contact sheet, into
       outputs/_development/05-llm-training/chapter-04-review/
    4. copy the chapter-4 figures and their generating scripts alongside
    5. write a short review manifest (commit SHA, source path, PDF
       path, page count, source ids, figure filenames, test results,
       known baseline failures)

This is a development/review artifact, not the canonical workbook PDF
and not a release candidate -- it is never written to
outputs/05-llm-training-workbook.pdf or outputs/_releases/.

Requires the `ml-workbooks` conda env active (quarto + poppler-utils).
"""
import json
import os
import shutil
import subprocess
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)  # so "tests.<module>" is importable by dotted name below
WB05 = os.path.join(REPO_ROOT, "workbooks", "05-llm-training")
REVIEW_QMD = os.path.join(WB05, "ch04-review.qmd")
REVIEW_DIR = os.path.join(REPO_ROOT, "outputs", "_development", "05-llm-training", "chapter-04-review")
PAGES_DIR = os.path.join(REVIEW_DIR, "pages")
OUTPUT_PDF = os.path.join(REVIEW_DIR, "05-llm-training-ch04-review.pdf")

FIGURE_SVGS = [
    os.path.join(WB05, "figures", "rendered", "fig-process-group-composition.svg"),
    os.path.join(WB05, "figures", "rendered", "fig-pipeline-timeline.svg"),
]
FIGURE_SCRIPTS = [
    os.path.join(WB05, "figures", "source", "fig_process_group_composition.py"),
    os.path.join(WB05, "figures", "source", "fig_pipeline_timeline.py"),
]

REQUIRED_TOOLS = ["quarto", "pdfinfo", "pdftotext", "pdftoppm"]


def run(cmd, **kw):
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=REPO_ROOT, **kw)


def write_contact_sheet(page_files, out_path):
    items = "\n".join(
        f'<figure><img src="pages/{p}" loading="lazy"><figcaption>{p}</figcaption></figure>'
        for p in page_files
    )
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Chapter 4 review contact sheet</title>
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
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)


def run_scoped_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for module in [
        "test_wb05_ch04_worked_examples",
        "test_wb05_ch04_pipeline_schedule",
        "test_wb05_ch04_question5_constraint",
        "test_workbook05_scaffold",
        "test_figures",
    ]:
        suite.addTests(loader.loadTestsFromName(f"tests.{module}"))
    stream = __import__("io").StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=1)
    result = runner.run(suite)
    return {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "failure_names": [str(t[0]) for t in result.failures],
    }


def run_full_suite():
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.join(REPO_ROOT, "tests"))
    stream = __import__("io").StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=1)
    result = runner.run(suite)
    return {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "failure_names": [str(t[0]) for t in result.failures],
    }


def get_commit_sha():
    r = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def main():
    missing = [t for t in REQUIRED_TOOLS if shutil.which(t) is None]
    if missing:
        print(f"BLOCKED: missing required tool(s): {missing}")
        sys.exit(2)

    print("--- Step 1: regenerate figures ---")
    r = run([sys.executable, "scripts/build_figures.py"])
    if r.returncode != 0:
        sys.exit(1)

    print("\n--- Step 2: render ch04-review.qmd ---")
    r = run(["quarto", "render", REVIEW_QMD, "--to", "typst"], capture_output=True, text=True)
    print(r.stdout[-2000:])
    if r.returncode != 0:
        print(r.stderr[-2000:])
        print("BLOCKED: quarto render failed")
        sys.exit(1)

    rendered_pdf = os.path.join(WB05, "ch04-review.pdf")
    if not os.path.exists(rendered_pdf):
        print(f"BLOCKED: expected {rendered_pdf} was not produced")
        sys.exit(1)

    print("\n--- Step 3: copy PDF + render pages + contact sheet ---")
    if os.path.isdir(PAGES_DIR):
        shutil.rmtree(PAGES_DIR)  # clear stale page renders from a prior, different-length build
    os.makedirs(PAGES_DIR, exist_ok=True)
    shutil.copy2(rendered_pdf, OUTPUT_PDF)
    print(f"wrote {os.path.relpath(OUTPUT_PDF, REPO_ROOT)}")

    info = subprocess.run(["pdfinfo", OUTPUT_PDF], capture_output=True, text=True).stdout
    print(info)
    text = subprocess.run(["pdftotext", OUTPUT_PDF, "-"], capture_output=True, text=True).stdout
    word_count = len(text.split())
    page_count = None
    for line in info.splitlines():
        if line.startswith("Pages:"):
            page_count = int(line.split(":", 1)[1].strip())

    toppm = subprocess.run(
        ["pdftoppm", "-png", "-r", "170", OUTPUT_PDF, os.path.join(PAGES_DIR, "page")],
        capture_output=True, text=True,
    )
    if toppm.returncode != 0:
        print("BLOCKED: pdftoppm failed")
        print(toppm.stderr)
        sys.exit(1)
    page_files = sorted(f for f in os.listdir(PAGES_DIR) if f.endswith(".png"))
    print(f"rendered {len(page_files)} page(s) to {os.path.relpath(PAGES_DIR, REPO_ROOT)}")

    contact_sheet_path = os.path.join(REVIEW_DIR, "contact-sheet.html")
    write_contact_sheet(page_files, contact_sheet_path)
    print(f"wrote {os.path.relpath(contact_sheet_path, REPO_ROOT)}")

    print("\n--- Step 4: copy figures + their generating scripts ---")
    for svg, script in zip(FIGURE_SVGS, FIGURE_SCRIPTS):
        shutil.copy2(svg, os.path.join(REVIEW_DIR, os.path.basename(svg)))
        shutil.copy2(script, os.path.join(REVIEW_DIR, os.path.basename(script)))
    print(f"copied {len(FIGURE_SVGS)} figure(s) and their scripts")

    print("\n--- Step 5: registry/question validators + scoped tests + full suite ---")
    registry_result = run([sys.executable, "scripts/validate_registry.py"], capture_output=True, text=True)
    questions_result = run([sys.executable, "scripts/validate_questions.py"], capture_output=True, text=True)
    scoped_tests = run_scoped_tests()
    full_suite = run_full_suite()

    known_baseline_failures = [
        "test_index_subtitle_says_release_candidate_5 (test_release_candidate_rc2.TestReleaseStatusLanguage)",
        "test_each_two_line_chapter_heading_renders_completely (test_release_candidate_rc4.TestAllTwoLineChapterTitlesProtected)",
        "test_chapter4_heading_renders_complete_title (test_release_candidate_rc4.TestChapter4TitleNoHyphenation)",
    ]
    new_failures = [f for f in full_suite["failure_names"] if f not in known_baseline_failures]

    manifest = {
        "commit_sha": get_commit_sha(),
        "source_path": "workbooks/05-llm-training/chapters/04-distributed-parallelism.qmd",
        "review_qmd_path": "workbooks/05-llm-training/ch04-review.qmd",
        "pdf_path": os.path.relpath(OUTPUT_PDF, REPO_ROOT),
        "page_count": page_count,
        "word_count": word_count,
        "source_ids_used": ["src-17", "src-52", "src-53", "src-54"],
        "figure_filenames": [os.path.basename(s) for s in FIGURE_SVGS],
        "figure_script_filenames": [os.path.basename(s) for s in FIGURE_SCRIPTS],
        "registry_validation": {"returncode": registry_result.returncode, "stdout": registry_result.stdout.strip()},
        "question_validation": {"returncode": questions_result.returncode, "stdout": questions_result.stdout.strip()},
        "chapter4_scoped_tests": scoped_tests,
        "full_test_suite": full_suite,
        "known_preexisting_workbook04_baseline_failures": known_baseline_failures,
        "new_failures_beyond_baseline": new_failures,
        "note": "This PDF is a development/review artifact. It is NOT outputs/05-llm-training-workbook.pdf (the canonical path, reserved for the completed workbook) and it is NOT a release candidate.",
    }
    manifest_path = os.path.join(REVIEW_DIR, "review-manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nwrote {os.path.relpath(manifest_path, REPO_ROOT)}")
    print(json.dumps(manifest, indent=2))

    print(f"\nOK: review package assembled at {os.path.relpath(REVIEW_DIR, REPO_ROOT)}")


if __name__ == "__main__":
    main()
