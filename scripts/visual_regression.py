#!/usr/bin/env python3
"""Visual-regression support for the chapter-factory workflow.

Extends scripts/build_chapter_review.py's page-rendering step (reuses
the same `pdftoppm` invocation) rather than duplicating it.

    python3 scripts/visual_regression.py --workbook 05-llm-training --chapter 06 \\
        --pdf outputs/_development/05-llm-training/chapter-06-review/05-llm-training-ch06-review.pdf \\
        --expected-changed-pages 3,7

Hashing note: this computes an exact SHA-256 hash per rendered page
PNG, not a true perceptual hash -- no PIL/ImageMagick/numpy-based PNG
decoder is available in this environment (confirmed directly; see
scripts/workbook_qa.py's own docstring for the same honesty
convention -- an HTML contact sheet instead of raster compositing). An
exact hash has zero false negatives for "did this page's rendered
bytes change at all," which is what this workflow needs; it cannot
express "how similar," only "identical or not," and is not oversold as
more than that.

Steps:
    1. Clear stale page images under <pdf's own directory>/pages/
       before re-rendering. Never touches any OTHER chapter's review
       directory, outputs/_releases/, or any accepted/committed
       artifact as a side effect of this script's own normal run.
    2. Render pages via `pdftoppm` and confirm the rendered PNG count
       equals `pdfinfo`'s own reported page count (a mismatch is
       itself a finding, not silently ignored).
    3. (Re)write the HTML contact sheet (same format
       build_chapter_review.py already uses).
    4. Compute a SHA-256 hash per page.
    5. If a prior hash manifest exists
       (<pdf's own directory>/visual-regression-hashes.json), diff
       against it and classify every page as: unchanged,
       expected_changed (hash differs AND the page number is in
       --expected-changed-pages, or matches a known-intentional-layout
       entry below), or unexpected_changed (hash differs and neither
       of those -- requires full-resolution inspection before being
       accepted).
    6. Write the new hash manifest -- but refuses to overwrite the
       manifest for a chapter whose config/chapter-status-registry.yaml
       status is "accepted_frozen", unless --override-frozen is passed
       explicitly (same discipline .claude/hooks/pre_action_guard.py
       applies to editing a frozen chapter's own content).
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from _yaml_lite import safe_load_path  # noqa: E402

# Known-intentional layout decisions, carried over from
# docs/chapter-review-checklist.md section 2 ("Known intentional
# layouts that must not be re-litigated") -- a changed page matching
# one of these is reported as expected_changed, not unexpected_changed,
# on every subsequent run, not just the run where it was first
# reviewed and accepted.
KNOWN_INTENTIONAL_LAYOUT_CHANGES = {
    ("05-llm-training", "02"): "sparse-but-complete bibliography page (accepted)",
    ("05-llm-training", "03"): "sparse-but-complete bibliography page (accepted)",
    ("05-llm-training", "04"): "page 12/13: Question 5 answer block and bibliography placed via one deliberate #pagebreak() (accepted)",
}


def run(cmd, **kw):
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, **kw)


def pdf_page_count(pdf_path):
    info = run(["pdfinfo", pdf_path]).stdout
    for line in info.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    return None


def render_pages(pdf_path, pages_dir):
    if os.path.isdir(pages_dir):
        shutil.rmtree(pages_dir)
    os.makedirs(pages_dir, exist_ok=True)
    r = run(["pdftoppm", "-png", "-r", "170", pdf_path, os.path.join(pages_dir, "page")])
    if r.returncode != 0:
        raise SystemExit(f"BLOCKED: pdftoppm failed: {r.stderr}")
    return sorted(f for f in os.listdir(pages_dir) if f.endswith(".png"))


def write_contact_sheet(review_dir, page_files):
    items = "\n".join(
        f'<figure><img src="pages/{p}" loading="lazy"><figcaption>{p}</figcaption></figure>'
        for p in page_files
    )
    path = os.path.join(review_dir, "contact-sheet.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            "<!doctype html><html><head><meta charset=\"utf-8\"><title>Chapter review contact sheet</title>"
            "<style>body{font-family:sans-serif;background:#222;color:#eee;margin:0;padding:1rem}"
            "div.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px}"
            "figure{margin:0}img{width:100%;border:1px solid #555}"
            "figcaption{font-size:.7rem;text-align:center;color:#aaa}</style></head>"
            f"<body><div class=\"grid\">{items}</div></body></html>"
        )
    return path


def hash_pages(pages_dir, page_files):
    hashes = {}
    for fn in page_files:
        with open(os.path.join(pages_dir, fn), "rb") as f:
            hashes[fn] = hashlib.sha256(f.read()).hexdigest()
    return hashes


def is_frozen(workbook, chapter):
    reg_path = os.path.join(REPO_ROOT, "config", "chapter-status-registry.yaml")
    if not os.path.exists(reg_path):
        return False
    reg = safe_load_path(reg_path) or {}
    wb = (reg.get("workbooks") or {}).get(workbook, {})
    chapters = wb.get("chapters") or {}
    entry = chapters.get(chapter) or {}
    return entry.get("status") == "accepted_frozen"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workbook", required=True)
    parser.add_argument("--chapter", required=True)
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--expected-changed-pages", default="",
                         help="comma-separated 1-indexed page numbers the caller already expects to differ")
    parser.add_argument("--override-frozen", action="store_true",
                         help="allow updating the hash manifest for an accepted_frozen chapter")
    args = parser.parse_args()

    pdf_path = os.path.abspath(args.pdf)
    if not os.path.exists(pdf_path):
        raise SystemExit(f"BLOCKED: {pdf_path} does not exist")
    review_dir = os.path.dirname(pdf_path)
    pages_dir = os.path.join(review_dir, "pages")
    manifest_path = os.path.join(review_dir, "visual-regression-hashes.json")

    if is_frozen(args.workbook, args.chapter) and not args.override_frozen:
        print(json.dumps({
            "ok": False,
            "issue": f"{args.workbook} chapter {args.chapter} is accepted_frozen in "
                     f"config/chapter-status-registry.yaml -- refusing to update its visual-regression "
                     f"manifest without --override-frozen",
        }, indent=2))
        sys.exit(1)

    expected_pages = set()
    if args.expected_changed_pages:
        expected_pages = {int(x) for x in args.expected_changed_pages.split(",") if x.strip()}

    declared_count = pdf_page_count(pdf_path)
    page_files = render_pages(pdf_path, pages_dir)
    rendered_count = len(page_files)
    write_contact_sheet(review_dir, page_files)
    new_hashes = hash_pages(pages_dir, page_files)

    old_hashes = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            old_hashes = json.load(f).get("page_hashes", {})

    unchanged, expected_changed, unexpected_changed, new_pages, missing_pages = [], [], [], [], []
    for fn, h in new_hashes.items():
        page_num = int(fn.replace("page-", "").replace(".png", ""))
        if fn not in old_hashes:
            new_pages.append(fn)
            continue
        if old_hashes[fn] == h:
            unchanged.append(fn)
            continue
        known = (args.workbook, args.chapter) in KNOWN_INTENTIONAL_LAYOUT_CHANGES
        if page_num in expected_pages or known:
            expected_changed.append(fn)
        else:
            unexpected_changed.append(fn)
    for fn in old_hashes:
        if fn not in new_hashes:
            missing_pages.append(fn)

    report = {
        "workbook": args.workbook,
        "chapter": args.chapter,
        "pdf_path": os.path.relpath(pdf_path, REPO_ROOT),
        "declared_page_count": declared_count,
        "rendered_page_count": rendered_count,
        "page_count_matches": declared_count == rendered_count,
        "has_prior_manifest": bool(old_hashes),
        "unchanged_pages": unchanged,
        "expected_changed_pages": expected_changed,
        "unexpected_changed_pages": unexpected_changed,
        "new_pages": new_pages,
        "missing_pages": missing_pages,
        "known_intentional_layout_note": KNOWN_INTENTIONAL_LAYOUT_CHANGES.get((args.workbook, args.chapter)),
        "requires_full_resolution_inspection": sorted(set(unexpected_changed + new_pages)),
        "ok": declared_count == rendered_count and len(unexpected_changed) == 0,
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"page_hashes": new_hashes, "last_report": report}, f, indent=2)

    print(json.dumps(report, indent=2))
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
