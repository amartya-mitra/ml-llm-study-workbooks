"""Reusable chapter-review check library.

Extracted from the recurring defects found during independent review
of Workbook 05 Chapters 1-4 (see docs/chapter-review-checklist.md),
so every future chapter is checked the same way instead of relying on
a human reviewer to remember each lesson individually. Used by both
scripts/build_chapter_review.py (page-density/bibliography diagnostics
at build time) and scripts/workbook_qa.py's --chapter mode (the full
chapter-scoped report).

Every function here is read-only: none of them modify chapter content
or accepted artifacts. A finding is data for a human (or an adversarial
review pass) to act on, not an automatic edit.
"""
import glob
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from _yaml_lite import safe_load_path  # noqa: E402

# The three pre-existing Workbook 04 RC test failures every Workbook 05
# chapter review build has reported separately since Chapter 1 -- kept
# here once, instead of copy-pasted into every build_wb05_chNN_review.py.
# Update this list only if Workbook 04's own known baseline changes
# (never to silently absorb a new, unrelated failure).
KNOWN_BASELINE_FAILURES = [
    "test_index_subtitle_says_release_candidate_5 (test_release_candidate_rc2.TestReleaseStatusLanguage)",
    "test_each_two_line_chapter_heading_renders_completely (test_release_candidate_rc4.TestAllTwoLineChapterTitlesProtected)",
    "test_chapter4_heading_renders_complete_title (test_release_candidate_rc4.TestChapter4TitleNoHyphenation)",
]


def new_failures_beyond_baseline(failure_names):
    return [f for f in failure_names if f not in KNOWN_BASELINE_FAILURES]


def discover_chapter_files(workbook, chapter):
    """(chapter_path, solutions_path) for a two-digit chapter number,
    by this project's established naming convention. Raises
    FileNotFoundError with a clear message if the convention is not
    met, rather than silently returning None."""
    wb_dir = os.path.join(REPO_ROOT, "workbooks", workbook)
    chapter_matches = sorted(glob.glob(os.path.join(wb_dir, "chapters", f"{chapter}-*.qmd")))
    solutions_matches = sorted(glob.glob(os.path.join(wb_dir, "solutions", f"{chapter}-*-solutions.qmd")))
    if len(chapter_matches) != 1:
        raise FileNotFoundError(f"expected exactly one chapters/{chapter}-*.qmd under {workbook}, found {chapter_matches}")
    if len(solutions_matches) != 1:
        raise FileNotFoundError(f"expected exactly one solutions/{chapter}-*-solutions.qmd under {workbook}, found {solutions_matches}")
    return chapter_matches[0], solutions_matches[0]


def chapter_slug_from_path(chapter_path):
    """'04-distributed-parallelism.qmd' -> 'distributed-parallelism'."""
    base = os.path.basename(chapter_path)
    return re.sub(r"^\d+-", "", base)[:-len(".qmd")]


# --------------------------------------------------------------------
# 1 / sources and claim ledger
# --------------------------------------------------------------------
def check_claim_ledger_coverage(workbook_dir, workbook, chapter_num):
    """Every chN claim-ledger entry's source_ids must exist in the
    registry; the chapter must have at least one real entry (not only
    a planned_chapter_sources placeholder) once it is drafted."""
    ledger_path = os.path.join(workbook_dir, "claim-ledger.yaml")
    registry_path = os.path.join(REPO_ROOT, "sources", "registry.yaml")
    if not os.path.exists(ledger_path):
        return {"ok": False, "issue": "claim-ledger.yaml not found"}
    ledger = safe_load_path(ledger_path) or {}
    registry = safe_load_path(registry_path) or {}
    known_ids = {s["id"] for s in registry.get("sources", [])}

    chapter_tag = f"ch{int(chapter_num)}"
    entries = [e for e in (ledger.get("entries") or []) if e.get("chapter") == chapter_tag]
    unknown_sources = set()
    for e in entries:
        for sid in e.get("source_ids") or []:
            if sid not in known_ids:
                unknown_sources.add(sid)
    return {
        "chapter_tag": chapter_tag,
        "num_claim_entries": len(entries),
        "unknown_source_ids_cited": sorted(unknown_sources),
        "ok": len(entries) > 0 and not unknown_sources,
    }

# --------------------------------------------------------------------
# 3. Learner-facing leakage checks
# --------------------------------------------------------------------
# Deliberately specific patterns -- ordinary words like "source" or
# phrases like "script-backed calculation" / "programmatically
# verified" must NOT match any of these, since those are legitimate
# learner-facing phrasing this project uses throughout Chapters 1-4.
LEAKAGE_PATTERNS = {
    "source_registry_ids": r"\bsrc-\d+\b",
    "qmd_filenames": r"\b[a-zA-Z0-9_-]+\.qmd\b",
    "py_filenames": r"\b[a-zA-Z0-9_-]+\.py\b",
    "yaml_filenames": r"\b[a-zA-Z0-9_-]+\.ya?ml\b",
    "internal_absolute_paths": r"/mnt/[a-z0-9_/-]+",
    "repo_top_level_dirs": r"\b(?:outputs|workbooks|scripts)/[a-zA-Z0-9_./-]*",
    "review_process_phrases": (
        r"review manifest|contact sheet|page render(?:s|ed|ing)?\b|generating script|"
        r"build instruction|review package|About this review|release candidate \d"
    ),
    "commit_hash_like_tokens": r"\b[0-9a-f]{7,40}\b",
    "unresolved_placeholders": r"\bTODO\b|\bTBD\b|\bFIXME\b|\bXXX\b|lorem ipsum|\bPLACEHOLDER\b|\[insert",
}


def check_text_leakage(text):
    """Returns {category: [matches]} for every category with at least
    one match, plus "ok": True iff no category matched."""
    findings = {}
    for name, pattern in LEAKAGE_PATTERNS.items():
        matches = sorted(set(re.findall(pattern, text, re.IGNORECASE)))
        if matches:
            findings[name] = matches[:20]
    findings["ok"] = len(findings) == 0
    return findings


# --------------------------------------------------------------------
# 4. Cross-reference checks
# --------------------------------------------------------------------
def check_answer_key_cross_reference(chapter_path, solutions_path):
    """Generalizes the exact bug found in Chapter 3's first review
    round: the Answer Key's intro cross-referenced the chapter's
    top-level section id (@sec-chN, "Section 1") instead of the
    "Check your understanding" subsection specifically ("Section
    1.8"). Flags the same failure mode for any chapter."""
    with open(chapter_path, encoding="utf-8") as f:
        chapter_text = f.read()
    with open(solutions_path, encoding="utf-8") as f:
        solutions_text = f.read()

    m_chapter = re.search(r"^##\s+.+?\{#(sec-ch\d+)\}", chapter_text, re.MULTILINE)
    chapter_anchor = m_chapter.group(1) if m_chapter else None

    m_check = re.search(r"^###\s+Check your understanding\s*\{#([a-z0-9-]+)\}", chapter_text, re.MULTILINE)
    check_anchor = m_check.group(1) if m_check else None

    m_ref = re.search(r'"Check your understanding"\s+questions\s*\n?\(@([a-z0-9-]+)\)', solutions_text)
    referenced_anchor = m_ref.group(1) if m_ref else None

    result = {
        "chapter_level_anchor": chapter_anchor,
        "check_your_understanding_anchor": check_anchor,
        "answer_key_references": referenced_anchor,
        "ok": True,
        "issue": None,
    }
    if check_anchor is None:
        result["ok"] = False
        result["issue"] = "'Check your understanding' heading has no explicit {#...} anchor"
    elif referenced_anchor is None:
        result["ok"] = False
        result["issue"] = "Answer Key intro does not reference any @anchor in the expected pattern"
    elif referenced_anchor == chapter_anchor:
        result["ok"] = False
        result["issue"] = (
            f"Answer Key references the chapter-level anchor ({chapter_anchor}) "
            f"instead of the Check-your-understanding anchor ({check_anchor}) -- "
            "this is the exact Chapter 3 round-1 defect pattern"
        )
    elif referenced_anchor != check_anchor:
        result["ok"] = False
        result["issue"] = (
            f"Answer Key references '{referenced_anchor}', which does not match "
            f"the Check-your-understanding anchor ({check_anchor})"
        )
    return result


# --------------------------------------------------------------------
# 5. Figure correctness contract (existence half; semantic correctness
#    is necessarily figure-specific and lives in each figure's own
#    dedicated test, see docs/chapter-review-checklist.md item 5)
# --------------------------------------------------------------------
def check_figure_invariant_tests(workbook_dir):
    """For every figures/source/*.py (excluding _helpers), checks
    whether at least one file under tests/ mentions that module's
    name -- a necessary (not sufficient) condition for "this figure
    has a dedicated semantic test," not merely the generic bounds/XML
    check every figure already gets from tests/test_figures.py."""
    figures_source_dir = os.path.join(workbook_dir, "figures", "source")
    findings = []
    if not os.path.isdir(figures_source_dir):
        return findings
    tests_dir = os.path.join(REPO_ROOT, "tests")
    combined_test_text = ""
    for fn in os.listdir(tests_dir):
        if fn.endswith(".py"):
            with open(os.path.join(tests_dir, fn), encoding="utf-8") as f:
                combined_test_text += f.read()
    for fn in sorted(os.listdir(figures_source_dir)):
        if not fn.endswith(".py") or fn.startswith("_"):
            continue
        module_name = fn[:-3]
        findings.append({
            "figure_script": fn,
            "has_dedicated_semantic_test": module_name in combined_test_text,
        })
    return findings


# --------------------------------------------------------------------
# 7. Worked-example contract (existence half; numeric correctness is
#    verified by actually running the scoped test, see run_scoped_tests)
# --------------------------------------------------------------------
def check_worked_example_scoped_test_exists(workbook, chapter_num):
    """Filename globbing alone is unreliable across workbooks: e.g.
    tests/test_ch03_worked_examples.py and test_ch04_worked_examples.py
    already belong to Workbook 04's own Chapter 3/4 (a pre-existing,
    coincidental name collision -- see tests/test_wb05_ch03_worked_examples.py's
    own docstring). Filters candidates by actually referencing this
    workbook's path, not just by filename pattern."""
    candidates = glob.glob(os.path.join(REPO_ROOT, "tests", f"test_*ch{chapter_num}_worked_examples.py"))
    matches = []
    for path in candidates:
        with open(path, encoding="utf-8") as f:
            if workbook in f.read():
                matches.append(path)
    return {
        "scoped_worked_example_test_files": [os.path.relpath(p, REPO_ROOT) for p in matches],
        "found": len(matches) > 0,
    }


# --------------------------------------------------------------------
# 6. Question and answer contract: one answer per question
# --------------------------------------------------------------------
def check_question_answer_correspondence(chapter_path, solutions_path, questions_yaml_path, chapter_slug):
    with open(chapter_path, encoding="utf-8") as f:
        chapter_text = f.read()
    section_match = re.search(
        r"###\s+Check your understanding.*?\n(.*?)(?=\n###|\Z)", chapter_text, re.DOTALL,
    )
    section_text = section_match.group(1) if section_match else ""
    n_questions_in_chapter = len(re.findall(r"^\d+\.\s+\*\*", section_text, re.MULTILINE))

    with open(solutions_path, encoding="utf-8") as f:
        solutions_text = f.read()
    n_answers = len(re.findall(r"^\*\*\d+\.\s", solutions_text, re.MULTILINE))

    n_in_yaml = 0
    if os.path.exists(questions_yaml_path):
        data = safe_load_path(questions_yaml_path) or {}
        n_in_yaml = len([q for q in data.get("questions", []) if q.get("chapter") == chapter_slug])

    return {
        "questions_in_chapter_prose": n_questions_in_chapter,
        "answers_in_solutions_file": n_answers,
        "questions_in_questions_yaml": n_in_yaml,
        "ok": n_questions_in_chapter == n_answers == n_in_yaml and n_questions_in_chapter > 0,
    }


# --------------------------------------------------------------------
# 2. Pagination: page-density diagnostic + bibliography-split flag
# --------------------------------------------------------------------
def per_page_text(pdf_path, page_count):
    pages = []
    for p in range(1, page_count + 1):
        r = subprocess.run(
            ["pdftotext", "-f", str(p), "-l", str(p), pdf_path, "-"],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )
        pages.append(r.stdout)
    return pages


def diagnose_bibliography_split(pages_text):
    """Flags a suspicious Bibliography split for MANUAL inspection --
    it cannot, by itself, distinguish an accidental mid-list split
    from a bibliography that legitimately needs two-plus pages (e.g.
    the full canonical book's 11-entry bibliography, which splits
    cleanly between whole entries and is not a defect)."""
    bib_page = None
    for i, text in enumerate(pages_text, start=1):
        if re.search(r"^Bibliography\s*$", text, re.MULTILINE):
            bib_page = i
            break
    if bib_page is None:
        return {"bibliography_page": None, "flagged": False, "note": "no Bibliography heading found"}

    entries_on_bib_page = len(re.findall(r"^\[\d+\]", pages_text[bib_page - 1], re.MULTILINE))
    next_page_has_entries = bib_page < len(pages_text) and bool(
        re.search(r"^\[\d+\]", pages_text[bib_page], re.MULTILINE)
    )
    flagged = next_page_has_entries and entries_on_bib_page <= 1
    return {
        "bibliography_page": bib_page,
        "entries_on_bibliography_page": entries_on_bib_page,
        "continues_on_next_page": next_page_has_entries,
        "flagged": flagged,
        "note": (
            "possible mid-list bibliography split (heading + <=1 entry, more entries follow on the "
            "next page) -- inspect visually; a complete bibliography split cleanly between whole "
            "entries across multiple pages is NOT a defect"
            if flagged else
            "no suspicious split detected"
        ),
    }


def flag_sparse_pages(word_counts, bib_diag, min_words=40):
    """Flags unusually sparse non-title pages for manual inspection.
    A sparse-but-complete bibliography or answer-key page is
    explicitly acceptable and is labeled as such, not failed."""
    flags = []
    bib_page = bib_diag.get("bibliography_page")
    for i, wc in enumerate(word_counts, start=1):
        if i == 1:
            continue
        if wc < min_words:
            reason = "sparse page -- requires manual inspection to confirm intent"
            if bib_page and i == bib_page and not bib_diag.get("flagged"):
                reason = "sparse but flagged as a complete bibliography/answer-key page (likely acceptable)"
            flags.append({"page": i, "word_count": wc, "reason": reason})
    return flags


def run_page_density_diagnostics(pdf_path, page_count):
    pages_text = per_page_text(pdf_path, page_count)
    word_counts = [len(t.split()) for t in pages_text]
    bib_diag = diagnose_bibliography_split(pages_text)
    sparse_flags = flag_sparse_pages(word_counts, bib_diag)
    return {
        "word_counts_by_page": word_counts,
        "bibliography_diagnostic": bib_diag,
        "sparse_page_flags": sparse_flags,
    }
