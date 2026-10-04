#!/usr/bin/env python3
"""The single, stable chapter-acceptance gate command.

    python3 scripts/chapter_gate.py --workbook 05-llm-training --chapter 06 \\
        --review-pdf outputs/_development/05-llm-training/chapter-06-review/05-llm-training-ch06-review.pdf \\
        --source-audit-json <path> --numerical-audit-json <path> \\
        --figure-audit-json <path> --learner-pdf-audit-json <path>

This is the deterministic entry point the chapter-factory workflow
(.claude/skills/draft-workbook-chapter/, .claude/skills/
review-workbook-chapter/) and a human reviewer both run to decide
whether one chapter is ready to move from drafted to accepted. It
extends scripts/workbook_qa.py's existing --chapter mode
(run_chapter_scoped_qa) rather than duplicating it -- every
deterministic check below is produced by that same function.

What this script adds beyond workbook_qa.py's chapter mode:

1. A stricter missing-check policy. workbook_qa.py quietly reports
   build-dependent checks as {"ok": null, "note": "not verified"} when
   --review-pdf is omitted. This script treats that same condition as
   a SKIPPED required check, which makes the overall gate result
   "fail" -- a missing check is a failure, not a pass. The same
   applies to each of the four audit-findings inputs below: if one is
   not supplied, that audit is "skipped" and the gate fails, because
   this script's whole purpose is to certify that all of them ran.
2. Slots for the four SEQUENTIAL audit stages' own structured JSON
   findings (--source-audit-json / --numerical-audit-json /
   --figure-audit-json / --learner-pdf-audit-json), each expected to
   be a JSON array of {severity, file, issue, evidence,
   proposed_correction, affected_acceptance_criterion} objects -- see
   docs/audit-profiles/0{1,2,3,4}-*.md for the exact schema each stage
   emits. These stages are performed directly by the main agent, one
   after another -- never via a subagent, an Agent-tool call, a
   Workflow, or in parallel; this script has no opinion about how the
   JSON was produced, only that it is present and well-formed. A
   "blocker" or "required" finding in any of these fails the gate; an
   "optional" finding downgrades an otherwise-passing gate to
   pass_with_warnings; "no_action" findings are informational only.
3. The chapter's current accepted/frozen status, read from
   config/chapter-status-registry.yaml and echoed verbatim in the
   report -- this script never infers or sets that status itself, and
   never writes to that registry file. A chapter marked
   "drafted_pending_human_review" there stays reported that way no
   matter how many checks pass; only a human, editing that file by
   hand, moves a chapter to "accepted_frozen".
4. Exact-match known-baseline classification is unchanged from
   chapter_review_checks.KNOWN_BASELINE_FAILURES / new_failures_
   beyond_baseline (already an exact list, never a wildcard or a bare
   count comparison) -- this script does not relax that.

Exit code: 0 iff status == "pass" or "pass_with_warnings"; 1 iff
"fail". Writes its full JSON report to
outputs/_development/<workbook>/chapter-gate/ch<NN>-gate-report.json
and also prints a short human-readable summary to stdout followed by
the full JSON.
"""
import argparse
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from _yaml_lite import safe_load_path  # noqa: E402
import chapter_review_checks as crc  # noqa: E402
import workbook_qa as wq  # noqa: E402

AUDIT_FLAG_TO_KEY = {
    "source_audit": "source_audit_findings",
    "numerical_audit": "numerical_audit_findings",
    "figure_audit": "figure_audit_findings",
    "learner_pdf_audit": "learner_pdf_findings",
}

# Deterministic checks this gate treats as required to have RUN AT ALL
# (distinct from whether their content came back clean -- that
# distinction is preserved from workbook_qa.py's own hard_fail_keys/
# warn_keys split, which this script reuses unchanged).
REQUIRED_TO_HAVE_RUN = [
    "structure", "sources_and_claim_ledger", "questions_and_solutions",
    "worked_examples", "figure_invariants", "cross_references",
    "build", "rendered_page_count", "text_leakage", "scoped_tests", "full_suite",
]

NOT_VERIFIED_PLACEHOLDER_KEYS = {"ok", "note"}


def _was_actually_run(check_value):
    """Distinguishes a real check result from workbook_qa.py's own
    '{"ok": null, "note": "...not verified"}' placeholder, which it
    writes for every build-dependent check when --review-pdf is
    omitted. An int (e.g. rendered_page_count) or a dict with keys
    other than exactly {"ok","note"} both count as 'actually run'."""
    if check_value is None:
        return False
    if isinstance(check_value, dict) and set(check_value.keys()) == NOT_VERIFIED_PLACEHOLDER_KEYS and check_value.get("ok") is None:
        return False
    return True


def load_frozen_status(workbook, chapter):
    """Reads (never writes) config/chapter-status-registry.yaml.
    Returns (status, source_note) -- status is None if this
    workbook/chapter has no registry entry at all."""
    path = os.path.join(REPO_ROOT, "config", "chapter-status-registry.yaml")
    if not os.path.exists(path):
        return None, "config/chapter-status-registry.yaml not found"
    reg = safe_load_path(path) or {}
    wb_entry = (reg.get("workbooks") or {}).get(workbook)
    if wb_entry is None:
        return None, f"no registry entry for workbook '{workbook}'"
    if "chapters" in wb_entry:
        chapters = wb_entry["chapters"] or {}
        entry = chapters.get(chapter)
        if entry is None:
            return None, f"no registry entry for {workbook} chapter {chapter}"
        return entry.get("status"), None
    # Whole-workbook status (e.g. Workbook 04, no chapter granularity).
    return wb_entry.get("status"), "workbook-level status, not chapter-granular"


def load_active_override(workbook, chapter):
    path = os.path.join(REPO_ROOT, "config", "chapter-status-registry.yaml")
    reg = safe_load_path(path) or {}
    overrides = reg.get("active_overrides") or []
    for o in overrides:
        if o.get("workbook") == workbook and o.get("chapter") in (chapter, "*"):
            return o
    return None


def load_audit_findings(path):
    """Returns (findings_list_or_None, error_or_None)."""
    if not path:
        return None, "not supplied"
    if not os.path.exists(path):
        return None, f"path does not exist: {path}"
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return None, f"could not parse as JSON: {e}"
    if not isinstance(data, list):
        return None, "audit JSON must be a top-level array of finding objects"
    return data, None


def classify_findings(findings):
    counts = {"blocker": 0, "required": 0, "optional": 0, "no_action": 0, "unknown_severity": 0}
    for item in findings:
        sev = item.get("severity")
        if sev in counts:
            counts[sev] += 1
        else:
            counts["unknown_severity"] += 1
    ok = counts["blocker"] == 0 and counts["required"] == 0 and counts["unknown_severity"] == 0
    has_warning = counts["optional"] > 0
    return {"ok": ok, "has_warning": has_warning, "counts": counts}


def build_gate_report(workbook, chapter, review_pdf, audit_json_paths, qa_dev_dir, run_scoped_qa=None):
    """Pure(ish) report-building logic, factored out of main() so tests
    can call it directly -- in-process, no subprocess -- and inject a
    fast fake for `run_scoped_qa` instead of paying the real full-suite
    cost on every call. Defaults to the real
    `workbook_qa.run_chapter_scoped_qa` when not overridden, which is
    exactly what every real (non-test) invocation of this script uses.
    `audit_json_paths` is a dict with keys "source_audit",
    "numerical_audit", "figure_audit", "learner_pdf_audit" -> path or
    None. Returns the full report dict; does not print or write
    anything itself (main() does both, exactly once per real run)."""
    run_scoped_qa = run_scoped_qa or wq.run_chapter_scoped_qa
    qa_summary = run_scoped_qa(workbook, chapter, review_pdf, qa_dev_dir)

    skipped_checks = []
    for key in REQUIRED_TO_HAVE_RUN:
        value = qa_summary["checks"].get(key)
        if not _was_actually_run(value):
            note = value.get("note") if isinstance(value, dict) else "check did not run"
            skipped_checks.append({"check": key, "reason": note})

    review_manifest_present = None
    if review_pdf:
        manifest_path = os.path.join(os.path.dirname(review_pdf), "review-manifest.json")
        review_manifest_present = os.path.exists(manifest_path)
        if not review_manifest_present:
            skipped_checks.append({"check": "review_manifest", "reason": f"not found at {manifest_path}"})
    else:
        skipped_checks.append({"check": "review_manifest", "reason": "no --review-pdf supplied"})

    audits = {}
    for name, path in audit_json_paths.items():
        findings, err = load_audit_findings(path)
        key = AUDIT_FLAG_TO_KEY[name]
        if findings is None:
            audits[key] = {"findings": None, "classification": None, "error": err}
            skipped_checks.append({"check": name, "reason": err})
        else:
            audits[key] = {"findings": findings, "classification": classify_findings(findings), "error": None}

    frozen_status, frozen_note = load_frozen_status(workbook, chapter)
    active_override = load_active_override(workbook, chapter)

    deterministic_hard_fail = qa_summary["status"] == "fail"
    deterministic_warn = qa_summary["status"] == "pass_with_warnings"
    audit_hard_fail = any(
        a["classification"] is not None and a["classification"]["ok"] is False
        for a in audits.values()
    )
    audit_warn = any(
        a["classification"] is not None and a["classification"]["ok"] is True and a["classification"]["has_warning"]
        for a in audits.values()
    )
    missing_required_check = len(skipped_checks) > 0

    if deterministic_hard_fail or audit_hard_fail or missing_required_check:
        status = "fail"
    elif deterministic_warn or audit_warn:
        status = "pass_with_warnings"
    else:
        status = "pass"

    return {
        "workbook": workbook,
        "chapter": chapter,
        "frozen_status": {
            "status": frozen_status,
            "note": frozen_note,
            "active_override": active_override,
        },
        "deterministic_checks": qa_summary["checks"],
        "deterministic_checks_status": qa_summary["status"],
        "review_manifest_present": review_manifest_present,
        **audits,
        "known_baseline_failures": crc.KNOWN_BASELINE_FAILURES,
        "new_failures_beyond_baseline": qa_summary["checks"].get("full_suite", {}).get("new_failures_beyond_baseline"),
        "skipped_checks": skipped_checks,
        "status": status,
        "note": (
            "This gate reports a technical pass/fail only. It never writes "
            "config/chapter-status-registry.yaml -- moving a chapter to "
            "accepted_frozen is always a separate, human-authorized edit."
        ),
    }


def print_human_summary(report):
    print(f"Chapter gate: {report['workbook']} chapter {report['chapter']}")
    print(f"  Registry status : {report['frozen_status']['status']} ({report['frozen_status']['note'] or 'chapter-granular'})")
    print(f"  Deterministic    : {report['deterministic_checks_status']}")
    for name, key in AUDIT_FLAG_TO_KEY.items():
        audit = report[key]
        cls = audit["classification"]
        print(f"  {name:<16}: {'skipped (' + audit['error'] + ')' if cls is None else ('ok' if cls['ok'] else 'FINDINGS')}")
    if report["skipped_checks"]:
        print(f"  Skipped checks   : {', '.join(s['check'] for s in report['skipped_checks'])}")
    print(f"  Known baseline   : {len(report['known_baseline_failures'])} pre-existing Workbook 04 failures (reported separately, never suppressed)")
    print(f"  New failures     : {report['new_failures_beyond_baseline']}")
    print(f"  GATE STATUS      : {report['status']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workbook", required=True)
    parser.add_argument("--chapter", required=True, help="two-digit chapter number, e.g. 06")
    parser.add_argument("--review-pdf", default=None)
    parser.add_argument("--source-audit-json", default=None)
    parser.add_argument("--numerical-audit-json", default=None)
    parser.add_argument("--figure-audit-json", default=None)
    parser.add_argument("--learner-pdf-audit-json", default=None)
    parser.add_argument("--audit-only", action="store_true",
                         help="write the report under outputs/_development/<workbook>/chapter-gate/audit-only/ "
                              "instead of chapter-gate/ -- use for read-only validation dry runs that must not "
                              "be mistaken for a real acceptance-gate run")
    args = parser.parse_args()

    workbook, chapter = args.workbook, args.chapter
    subdir = "audit-only" if args.audit_only else None
    dev_dir = os.path.join(REPO_ROOT, "outputs", "_development", workbook, "chapter-gate")
    if subdir:
        dev_dir = os.path.join(dev_dir, subdir)

    qa_dev_dir = os.path.join(REPO_ROOT, "outputs", "_development", workbook, "qa-runs", f"gate-{chapter}")
    audit_json_paths = {
        "source_audit": args.source_audit_json,
        "numerical_audit": args.numerical_audit_json,
        "figure_audit": args.figure_audit_json,
        "learner_pdf_audit": args.learner_pdf_audit_json,
    }
    report = build_gate_report(workbook, chapter, args.review_pdf, audit_json_paths, qa_dev_dir)

    os.makedirs(dev_dir, exist_ok=True)
    report_path = os.path.join(dev_dir, f"ch{chapter}-gate-report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print_human_summary(report)
    print(f"\nWrote {os.path.relpath(report_path, REPO_ROOT)}")
    print(json.dumps(report, indent=2))

    sys.exit(0 if report["status"] in ("pass", "pass_with_warnings") else 1)


if __name__ == "__main__":
    main()
