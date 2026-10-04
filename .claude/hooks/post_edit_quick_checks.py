#!/usr/bin/env python3
"""PostToolUse quick-check hook for the chapter-factory workflow.

STAGED, NOT ACTIVE by default -- see .claude/hooks.staged.json and
docs/chapter-factory-operator-guide.md for the exact activation step.
Safe to run standalone against synthetic stdin; never blocks (always
exits 0) and never modifies any file -- it only runs cheap, targeted
checks and reports them back to the model via a "systemMessage" so the
model sees the result on its next turn, without the cost of the full
test suite after every single edit.

Dispatch, by which file the just-completed Edit/Write/NotebookEdit
touched:

    *.qmd under workbooks/*/chapters/ or workbooks/*/solutions/
        -> chapter_review_checks.check_text_leakage (on that file's
           own text) + check_answer_key_cross_reference (if a
           matching chapter/solutions pair exists)
    data/worked-examples/*.py or *.json
        -> run that chapter's own scoped worked-example test module,
           if scripts/chapter_review_checks.check_worked_example_
           scoped_test_exists finds one
    figures/source/fig_*.py or figures/rendered/*.svg
        -> regenerate the figure (python3 <script>) + run
           tests/test_figures.py (generic bounds/XML check only --
           this hook does not know which figure-specific semantic test
           file to run without more context than a path gives it; the
           orchestrating skill runs the full, correct test after a
           batch of edits)
    questions.yaml or solutions/*.qmd
        -> chapter_review_checks.check_question_answer_correspondence,
           if the chapter can be inferred from the path

Anything else: no-op, exit 0, no output.
"""
import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.environ.get(
    "CHAPTER_GATE_REPO_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
)
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

try:
    import chapter_review_checks as crc
except ImportError:
    crc = None


def _rel(path):
    if not path:
        return ""
    if os.path.isabs(path):
        try:
            return os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")
        except ValueError:
            return path
    return path.replace(os.sep, "/")


def _infer_workbook_and_chapter(rel_path):
    m = re.match(r"workbooks/([^/]+)/(?:chapters|solutions)/(\d{2})-", rel_path)
    if m:
        return m.group(1), m.group(2)
    return None, None


def check_qmd(rel_path):
    if crc is None:
        return None
    if not re.match(r"workbooks/[^/]+/(chapters|solutions)/.*\.qmd$", rel_path):
        return None
    full_path = os.path.join(REPO_ROOT, rel_path)
    if not os.path.exists(full_path):
        return None
    with open(full_path, encoding="utf-8") as f:
        text = f.read()
    leakage = crc.check_text_leakage(text)
    # check_text_leakage is designed for RENDERED PDF text, not raw
    # .qmd source -- "source_registry_ids" (@src-NN) is a correct,
    # required citation key in source that citeproc resolves away
    # before the reader ever sees it, so it is not a real finding
    # here. Every other category (stray filenames in prose, internal
    # paths, review-process phrases, placeholders) is still a genuine
    # problem even in source and stays flagged.
    leakage.pop("source_registry_ids", None)
    messages = []
    if any(k != "ok" for k in leakage):
        categories = [k for k in leakage if k != "ok"]
        messages.append(f"post-edit quick check: possible leakage in {rel_path}: {categories}")
    workbook, chapter = _infer_workbook_and_chapter(rel_path)
    if workbook and chapter:
        try:
            chapter_path, solutions_path = crc.discover_chapter_files(workbook, chapter)
            xref = crc.check_answer_key_cross_reference(chapter_path, solutions_path)
            if not xref.get("ok"):
                messages.append(f"post-edit quick check: cross-reference issue for {workbook} ch{chapter}: {xref.get('issue')}")
        except FileNotFoundError:
            pass
    return messages


def check_worked_example(rel_path):
    m = re.match(r"workbooks/([^/]+)/data/worked-examples/", rel_path)
    if not m or crc is None:
        return None
    workbook = m.group(1)
    messages = []
    # Try every two-digit chapter number this workbook has drafted so
    # far, cheaply -- this hook does not try to parse the chapter
    # number out of an arbitrary worked-example filename.
    contracts_dir = os.path.join(REPO_ROOT, "workbooks", workbook, "chapter-contracts")
    if not os.path.isdir(contracts_dir):
        return messages
    for fn in sorted(os.listdir(contracts_dir)):
        m2 = re.match(r"ch(\d{2})\.yaml$", fn)
        if not m2:
            continue
        chapter = m2.group(1)
        we_check = crc.check_worked_example_scoped_test_exists(workbook, chapter)
        for test_path in we_check.get("scoped_worked_example_test_files", []):
            module = os.path.splitext(os.path.basename(test_path))[0]
            r = subprocess.run(
                [sys.executable, "-m", "unittest", f"tests.{module}", "-v"],
                cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
            )
            status = "pass" if r.returncode == 0 else "FAIL"
            messages.append(f"post-edit quick check: {module} -> {status}")
    return messages


def check_figure(rel_path):
    is_source = rel_path.startswith(tuple(
        f"workbooks/{wb}/figures/source/fig_" for wb in os.listdir(os.path.join(REPO_ROOT, "workbooks"))
        if os.path.isdir(os.path.join(REPO_ROOT, "workbooks", wb))
    )) if os.path.isdir(os.path.join(REPO_ROOT, "workbooks")) else False
    is_rendered = "/figures/rendered/" in rel_path and rel_path.endswith(".svg")
    if not (is_source or is_rendered):
        return None
    messages = []
    if is_source:
        full_path = os.path.join(REPO_ROOT, rel_path)
        if os.path.exists(full_path):
            r = subprocess.run([sys.executable, full_path], cwd=REPO_ROOT, capture_output=True, text=True, timeout=30)
            messages.append(f"post-edit quick check: regenerated {rel_path} -> {'ok' if r.returncode == 0 else 'FAIL: ' + r.stderr[-300:]}")
    r = subprocess.run([sys.executable, "-m", "unittest", "tests.test_figures", "-v"],
                        cwd=REPO_ROOT, capture_output=True, text=True, timeout=60)
    messages.append(f"post-edit quick check: tests.test_figures -> {'pass' if r.returncode == 0 else 'FAIL'}")
    return messages


def check_questions(rel_path):
    if not (rel_path.endswith("questions.yaml") or ("/solutions/" in rel_path and rel_path.endswith(".qmd"))):
        return None
    if crc is None:
        return None
    workbook, chapter = _infer_workbook_and_chapter(rel_path) if "/solutions/" in rel_path else (None, None)
    messages = []
    if workbook and chapter:
        try:
            chapter_path, solutions_path = crc.discover_chapter_files(workbook, chapter)
            slug = crc.chapter_slug_from_path(chapter_path)
            qa = crc.check_question_answer_correspondence(
                chapter_path, solutions_path,
                os.path.join(REPO_ROOT, "workbooks", workbook, "questions.yaml"),
                slug,
            )
            if not qa.get("ok"):
                messages.append(f"post-edit quick check: question/answer mismatch for {workbook} ch{chapter}: {qa}")
        except FileNotFoundError:
            pass
    else:
        messages.append("post-edit quick check: questions.yaml changed -- run scripts/validate_questions.py before committing")
    return messages


DISPATCH = [check_qmd, check_worked_example, check_figure, check_questions]


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = event.get("tool_name", "")
    if tool_name not in ("Edit", "Write", "NotebookEdit"):
        sys.exit(0)

    rel_path = _rel((event.get("tool_input") or {}).get("file_path", ""))
    if not rel_path:
        sys.exit(0)

    all_messages = []
    for check in DISPATCH:
        try:
            result = check(rel_path)
        except Exception as e:  # a quick check must never crash the hook / block the edit
            result = [f"post-edit quick check error (non-blocking): {check.__name__}: {e}"]
        if result:
            all_messages.extend(result)

    if all_messages:
        print(json.dumps({"systemMessage": " | ".join(all_messages)}))
    sys.exit(0)  # this hook never blocks


if __name__ == "__main__":
    main()
