#!/usr/bin/env python3
"""Generic, reusable standalone chapter-review-package builder.

    python3 scripts/build_chapter_review.py --workbook 05-llm-training --chapter 05
    python3 scripts/build_chapter_review.py --workbook 05-llm-training --chapter 05 --pagebreak-before-bibliography

Replaces the old one-bespoke-python-script-per-chapter pattern
(scripts/build_wb05_ch01_review.py .. build_wb05_ch04_review.py) with
a single script that auto-discovers each chapter's files by naming
convention and fills in shared/chapter-review-template.qmd.tmpl (the
".tmpl" extension keeps Quarto's project-wide file discovery from
trying to process the template's own unfilled __PLACEHOLDER__ tokens
as if it were a real document), so a new
chapter needs zero new committed review-build code -- only its own
chapter/solutions/figure files.

Chapters 1-4's existing bespoke build_wb05_ch0N_review.py scripts and
hand-written ch0N-review.qmd files are frozen, accepted artifacts and
are NOT replaced by this script -- this is the mechanism for Chapter 5
onward. See docs/chapter-review-checklist.md for the pagination
defaults this script follows.

Auto-discovery conventions (must hold for every chapter):
    - chapter file:   workbooks/<workbook>/chapters/<chapter>-*.qmd
    - solutions file: workbooks/<workbook>/solutions/<chapter>-*-solutions.qmd
    - chapter title:  the first "## <Title> {#sec-chN}" heading in the
      chapter file (any inline Typst/HTML directive stripped)
    - book title:     the "title:" field in workbooks/<workbook>/index.qmd
    - cited figures:  every figures/rendered/*.svg path referenced in
      the chapter file, matched to its figures/source/*.py generator
      by filename (fig-a-b.svg <-> fig_a_b.py)
    - cited sources:  every @src-N token in the chapter or solutions file

Requires the `ml-workbooks` conda env active (quarto + poppler-utils).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from chapter_review_checks import (  # noqa: E402
    discover_chapter_files, run_page_density_diagnostics,
    KNOWN_BASELINE_FAILURES, new_failures_beyond_baseline,
)

TEMPLATE_PATH = os.path.join(REPO_ROOT, "shared", "chapter-review-template.qmd.tmpl")
REQUIRED_TOOLS = ["quarto", "pdfinfo", "pdftotext", "pdftoppm"]

HEADING_RE = re.compile(r"^##\s+(.+?)\s*\{#sec-ch(\d+)\}", re.MULTILINE)
SVG_REF_RE = re.compile(r"figures/rendered/([a-zA-Z0-9_-]+)\.svg")
SRC_ID_RE = re.compile(r"@(src-\d+)")


def run(cmd, **kw):
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=REPO_ROOT, **kw)


def discover_book_title(workbook):
    index_path = os.path.join(REPO_ROOT, "workbooks", workbook, "index.qmd")
    with open(index_path, encoding="utf-8") as f:
        content = f.read()
    m = re.search(r'^title:\s*"(.+?)"', content, re.MULTILINE)
    if not m:
        raise SystemExit(f"BLOCKED: could not find title: field in {index_path}")
    return m.group(1)


def discover_chapter_title(chapter_path, chapter):
    with open(chapter_path, encoding="utf-8") as f:
        content = f.read()
    m = HEADING_RE.search(content)
    if not m:
        raise SystemExit(f"BLOCKED: no '## <Title> {{#sec-chN}}' heading found in {chapter_path}")
    title = re.sub(r"`[^`]*`\{=typst\}", "", m.group(1)).strip()
    return title, content


def discover_figures(workbook, chapter_text):
    wb_dir = os.path.join(REPO_ROOT, "workbooks", workbook)
    svg_ids = sorted(set(SVG_REF_RE.findall(chapter_text)))
    figures = []
    for svg_id in svg_ids:
        svg_path = os.path.join(wb_dir, "figures", "rendered", f"{svg_id}.svg")
        script_name = svg_id.replace("-", "_") + ".py"
        script_path = os.path.join(wb_dir, "figures", "source", script_name)
        figures.append({
            "svg_id": svg_id,
            "svg_path": svg_path,
            "script_path": script_path if os.path.exists(script_path) else None,
        })
    return figures


def discover_source_ids(chapter_text, solutions_text):
    return sorted(set(SRC_ID_RE.findall(chapter_text)) | set(SRC_ID_RE.findall(solutions_text)))


def render_template(book_title, chapter_num, chapter_title, chapter_rel, solutions_rel, pagebreak_before_bib):
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()
    subtitle = f"Chapter {int(chapter_num)} Review Draft — {chapter_title}"
    bib_pagebreak = "\n```{=typst}\n#pagebreak()\n```\n" if pagebreak_before_bib else ""
    filled = (
        template
        .replace("__BOOK_TITLE__", book_title)
        .replace("__SUBTITLE__", subtitle)
        .replace("__CHAPTER_INCLUDE__", chapter_rel)
        .replace("__SOLUTIONS_INCLUDE__", solutions_rel)
        .replace("__PAGEBREAK_BEFORE_BIBLIOGRAPHY__", str(pagebreak_before_bib))
        .replace("__BIBLIOGRAPHY_PAGEBREAK__", bib_pagebreak)
    )
    return filled


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workbook", required=True)
    parser.add_argument("--chapter", required=True, help="two-digit chapter number, e.g. 05")
    parser.add_argument("--pagebreak-before-bibliography", action="store_true",
                         help="force the Bibliography onto its own fresh page (apply only after visually "
                              "confirming a mid-list split on a first, unforced build)")
    args = parser.parse_args()

    missing = [t for t in REQUIRED_TOOLS if shutil.which(t) is None]
    if missing:
        print(f"BLOCKED: missing required tool(s): {missing}")
        sys.exit(2)

    workbook = args.workbook
    chapter = args.chapter
    wb_dir = os.path.join(REPO_ROOT, "workbooks", workbook)

    chapter_path, solutions_path = discover_chapter_files(workbook, chapter)
    book_title = discover_book_title(workbook)
    chapter_title, chapter_text = discover_chapter_title(chapter_path, chapter)
    with open(solutions_path, encoding="utf-8") as f:
        solutions_text = f.read()
    figures = discover_figures(workbook, chapter_text)
    source_ids = discover_source_ids(chapter_text, solutions_text)

    chapter_rel = os.path.relpath(chapter_path, wb_dir).replace(os.sep, "/")
    solutions_rel = os.path.relpath(solutions_path, wb_dir).replace(os.sep, "/")

    review_dir = os.path.join(REPO_ROOT, "outputs", "_development", workbook, f"chapter-{chapter}-review")
    pages_dir = os.path.join(review_dir, "pages")
    os.makedirs(review_dir, exist_ok=True)

    review_qmd_path = os.path.join(wb_dir, f"ch{chapter}-review.qmd")
    filled = render_template(book_title, chapter, chapter_title, chapter_rel, solutions_rel,
                              args.pagebreak_before_bibliography)
    with open(review_qmd_path, "w", encoding="utf-8") as f:
        f.write(filled)
    print(f"generated {os.path.relpath(review_qmd_path, REPO_ROOT)} (git-ignored working file, not committed content)")

    print("\n--- Step 1: regenerate figures ---")
    r = run([sys.executable, "scripts/build_figures.py"])
    if r.returncode != 0:
        sys.exit(1)

    print(f"\n--- Step 2: render {os.path.basename(review_qmd_path)} ---")
    r = run(["quarto", "render", review_qmd_path, "--to", "typst"], capture_output=True, text=True)
    print(r.stdout[-2000:])
    if r.returncode != 0:
        print(r.stderr[-2000:])
        print("BLOCKED: quarto render failed")
        sys.exit(1)

    rendered_pdf = os.path.join(wb_dir, f"ch{chapter}-review.pdf")
    if not os.path.exists(rendered_pdf):
        print(f"BLOCKED: expected {rendered_pdf} was not produced")
        sys.exit(1)

    print("\n--- Step 3: copy PDF + render pages + contact sheet ---")
    if os.path.isdir(pages_dir):
        shutil.rmtree(pages_dir)
    os.makedirs(pages_dir, exist_ok=True)
    output_pdf = os.path.join(review_dir, f"{workbook}-ch{chapter}-review.pdf")
    shutil.copy2(rendered_pdf, output_pdf)
    print(f"wrote {os.path.relpath(output_pdf, REPO_ROOT)}")

    info = subprocess.run(["pdfinfo", output_pdf], cwd=REPO_ROOT, capture_output=True, text=True).stdout
    page_count = None
    for line in info.splitlines():
        if line.startswith("Pages:"):
            page_count = int(line.split(":", 1)[1].strip())

    toppm = subprocess.run(
        ["pdftoppm", "-png", "-r", "170", output_pdf, os.path.join(pages_dir, "page")],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    if toppm.returncode != 0:
        print("BLOCKED: pdftoppm failed")
        print(toppm.stderr)
        sys.exit(1)
    page_files = sorted(f for f in os.listdir(pages_dir) if f.endswith(".png"))
    print(f"rendered {len(page_files)} page(s) to {os.path.relpath(pages_dir, REPO_ROOT)}")

    contact_sheet_path = os.path.join(review_dir, "contact-sheet.html")
    items = "\n".join(
        f'<figure><img src="pages/{p}" loading="lazy"><figcaption>{p}</figcaption></figure>'
        for p in page_files
    )
    with open(contact_sheet_path, "w", encoding="utf-8") as f:
        f.write(
            "<!doctype html><html><head><meta charset=\"utf-8\"><title>Chapter review contact sheet</title>"
            "<style>body{font-family:sans-serif;background:#222;color:#eee;margin:0;padding:1rem}"
            "div.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px}"
            "figure{margin:0}img{width:100%;border:1px solid #555}"
            "figcaption{font-size:.7rem;text-align:center;color:#aaa}</style></head>"
            f"<body><div class=\"grid\">{items}</div></body></html>"
        )
    print(f"wrote {os.path.relpath(contact_sheet_path, REPO_ROOT)}")

    print("\n--- Step 4: copy figures + their generating scripts ---")
    for fig in figures:
        if os.path.exists(fig["svg_path"]):
            shutil.copy2(fig["svg_path"], os.path.join(review_dir, os.path.basename(fig["svg_path"])))
        if fig["script_path"]:
            shutil.copy2(fig["script_path"], os.path.join(review_dir, os.path.basename(fig["script_path"])))
    print(f"copied {len(figures)} figure(s) and their scripts")

    print("\n--- Step 5: page-density / bibliography-split diagnostics ---")
    density = run_page_density_diagnostics(output_pdf, page_count)
    bib_diag = density["bibliography_diagnostic"]
    sparse_flags = density["sparse_page_flags"]
    print(json.dumps({"bibliography_diagnostic": bib_diag, "sparse_page_flags": sparse_flags}, indent=2))

    print("\n--- Step 6: registry/question validators + full suite ---")
    registry_result = run([sys.executable, "scripts/validate_registry.py"], capture_output=True, text=True)
    questions_result = run([sys.executable, "scripts/validate_questions.py"], capture_output=True, text=True)
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.join(REPO_ROOT, "tests"))
    stream = __import__("io").StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=1)
    full_suite_result = runner.run(suite)

    manifest = {
        "workbook": workbook,
        "chapter": chapter,
        "chapter_title": chapter_title,
        "source_path": os.path.relpath(chapter_path, REPO_ROOT),
        "solutions_path": os.path.relpath(solutions_path, REPO_ROOT),
        "review_qmd_path": os.path.relpath(review_qmd_path, REPO_ROOT),
        "pdf_path": os.path.relpath(output_pdf, REPO_ROOT),
        "page_count": page_count,
        "source_ids_used": source_ids,
        "figures": [os.path.basename(f["svg_path"]) for f in figures],
        "pagebreak_before_bibliography_applied": args.pagebreak_before_bibliography,
        "bibliography_diagnostic": bib_diag,
        "sparse_page_flags": sparse_flags,
        "registry_validation": {"returncode": registry_result.returncode, "stdout": registry_result.stdout.strip()},
        "question_validation": {"returncode": questions_result.returncode, "stdout": questions_result.stdout.strip()},
        "full_test_suite": {
            "tests_run": full_suite_result.testsRun,
            "failures": len(full_suite_result.failures),
            "errors": len(full_suite_result.errors),
            "failure_names": [str(t[0]) for t in full_suite_result.failures],
        },
        "known_preexisting_workbook04_baseline_failures": KNOWN_BASELINE_FAILURES,
        "new_failures_beyond_baseline": new_failures_beyond_baseline(
            [str(t[0]) for t in full_suite_result.failures]
        ),
        "note": "This PDF is a development/review artifact -- not the canonical workbook PDF and not a release candidate.",
    }
    manifest_path = os.path.join(review_dir, "review-manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nwrote {os.path.relpath(manifest_path, REPO_ROOT)}")

    print("\n--- Step 7: clean up generated staging files ---")
    # review_qmd_path and rendered_pdf are disposable: the PDF has
    # already been copied to output_pdf, so nothing in workbooks/<id>/
    # needs to persist -- unlike Chapters 1-4's hand-written,
    # intentionally committed ch0N-review.qmd files, this one is
    # regenerated from the template on every run.
    for staging_path in (review_qmd_path, rendered_pdf):
        if os.path.exists(staging_path):
            os.remove(staging_path)
            print(f"removed staging file {os.path.relpath(staging_path, REPO_ROOT)}")

    print(f"\nOK: review package assembled at {os.path.relpath(review_dir, REPO_ROOT)}")


if __name__ == "__main__":
    main()
