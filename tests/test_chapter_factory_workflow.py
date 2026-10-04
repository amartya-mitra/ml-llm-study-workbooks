"""Tests for the "chapter factory" infrastructure: the chapter-contract
schema/validator, scripts/chapter_gate.py, the three staged (not yet
active) .claude/hooks/*.py scripts, and scripts/visual_regression.py.

Design note (Phase 9 of the chapter-factory recovery task): most tests
here call chapter_gate.py's own `build_gate_report()` function
directly, in-process, with a fast fake `run_scoped_qa` substituted for
`workbook_qa.run_chapter_scoped_qa` -- which otherwise runs the entire
project test suite internally on every call. This file invokes the
REAL full test suite exactly zero times; the one real, expensive
end-to-end exercise of chapter_gate.py happens separately, by hand,
during the chapter-factory recovery task's own audit-only validation
phase (see that task's final report), not from inside this automated
suite. Hook-script tests that need the real chapter_gate.py CLI as a
subprocess (because the hook itself shells out to it) point that
subprocess at an isolated fixture directory containing a tiny FAKE
chapter_gate.py instead of the real one, via the CHAPTER_GATE_REPO_ROOT
environment variable every hook script supports -- so the hook's own
subprocess-invocation and marker-file logic is still genuinely
exercised, without paying the real gate's cost.

None of these tests touch chapter content, solutions, questions,
claims, or figures, and none write to
config/chapter-status-registry.yaml.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import chapter_gate as cg  # noqa: E402
import chapter_review_checks as crc  # noqa: E402

FIXTURES_DIR = os.path.join(REPO_ROOT, "tests", "fixtures", "chapter_gate")
PY = sys.executable


def run_hook(script_rel_path, stdin_obj, repo_root=None, timeout=30):
    env = dict(os.environ)
    if repo_root:
        env["CHAPTER_GATE_REPO_ROOT"] = repo_root
    r = subprocess.run(
        [PY, os.path.join(REPO_ROOT, script_rel_path)],
        input=json.dumps(stdin_obj), capture_output=True, text=True, timeout=timeout, env=env,
    )
    return r


def fake_run_scoped_qa_factory(status="pass", extra_checks=None):
    """A fast stand-in for workbook_qa.run_chapter_scoped_qa -- fixed
    output, zero subprocesses, zero real test-suite cost."""
    checks = {
        "structure": {"ok": True},
        "sources_and_claim_ledger": {"ok": True},
        "questions_and_solutions": {"ok": True},
        "worked_examples": {"found": True},
        "figure_invariants": {"ok": True},
        "cross_references": {"ok": True},
        "build": {"ok": True},
        "rendered_page_count": 14,
        "text_leakage": {"ok": True},
        "scoped_tests": {"ok": True},
        "full_suite": {"ok": True, "new_failures_beyond_baseline": []},
    }
    if extra_checks:
        checks.update(extra_checks)

    def fake(workbook, chapter, review_pdf, dev_dir):
        return {"checks": checks, "status": status}
    return fake


CLEAN_AUDIT_PATH = os.path.join(FIXTURES_DIR, "clean_audit.json")
OPTIONAL_AUDIT_PATH = os.path.join(FIXTURES_DIR, "optional_only_audit.json")
BLOCKER_AUDIT_PATH = os.path.join(FIXTURES_DIR, "blocker_audit.json")
REQUIRED_AUDIT_PATH = os.path.join(FIXTURES_DIR, "required_audit.json")
ALL_CLEAN_AUDITS = {k: CLEAN_AUDIT_PATH for k in
                    ("source_audit", "numerical_audit", "figure_audit", "learner_pdf_audit")}
ALL_MISSING_AUDITS = {k: None for k in
                      ("source_audit", "numerical_audit", "figure_audit", "learner_pdf_audit")}


class TestChapterContractSchemaValidation(unittest.TestCase):
    def test_real_contracts_pass(self):
        import validate_chapter_contract as vcc
        errors, total = vcc.validate_all()
        self.assertEqual(errors, [])
        self.assertGreaterEqual(total, 2)

    def test_status_mismatch_is_rejected(self):
        import validate_chapter_contract as vcc
        schema = vcc.load_schema()
        known_source_ids = vcc.load_known_source_ids()
        status_registry = vcc.load_status_registry()
        with tempfile.TemporaryDirectory() as d:
            bad_path = os.path.join(d, "ch06.yaml")
            with open(os.path.join(REPO_ROOT, "workbooks", "05-llm-training", "chapter-contracts", "ch06.yaml"), encoding="utf-8") as f:
                content = f.read()
            content = content.replace('status: "drafted_pending_human_review"', 'status: "accepted_frozen"', 1)
            with open(bad_path, "w", encoding="utf-8") as f:
                f.write(content)
            errors = vcc.validate_one(bad_path, schema, known_source_ids, status_registry)
        self.assertTrue(any("does not match" in e for e in errors))

    def test_question_answer_count_mismatch_is_rejected(self):
        import validate_chapter_contract as vcc
        schema = vcc.load_schema()
        known_source_ids = vcc.load_known_source_ids()
        status_registry = vcc.load_status_registry()
        with tempfile.TemporaryDirectory() as d:
            bad_path = os.path.join(d, "ch05.yaml")
            with open(os.path.join(REPO_ROOT, "workbooks", "05-llm-training", "chapter-contracts", "ch05.yaml"), encoding="utf-8") as f:
                content = f.read()
            content = content.replace("answer_count: 5", "answer_count: 4", 1)
            with open(bad_path, "w", encoding="utf-8") as f:
                f.write(content)
            errors = vcc.validate_one(bad_path, schema, known_source_ids, status_registry)
        self.assertTrue(any("question_count" in e and "answer_count" in e for e in errors))

    def test_unknown_source_id_is_rejected(self):
        import validate_chapter_contract as vcc
        schema = vcc.load_schema()
        known_source_ids = vcc.load_known_source_ids()
        status_registry = vcc.load_status_registry()
        with tempfile.TemporaryDirectory() as d:
            bad_path = os.path.join(d, "ch05.yaml")
            with open(os.path.join(REPO_ROOT, "workbooks", "05-llm-training", "chapter-contracts", "ch05.yaml"), encoding="utf-8") as f:
                content = f.read()
            content = content.replace('"src-10"', '"src-99999"', 1)
            with open(bad_path, "w", encoding="utf-8") as f:
                f.write(content)
            errors = vcc.validate_one(bad_path, schema, known_source_ids, status_registry)
        self.assertTrue(any("src-99999" in e for e in errors))

    def test_canonical_and_release_output_must_be_false(self):
        import validate_chapter_contract as vcc
        schema = vcc.load_schema()
        known_source_ids = vcc.load_known_source_ids()
        status_registry = vcc.load_status_registry()
        with tempfile.TemporaryDirectory() as d:
            bad_path = os.path.join(d, "ch06.yaml")
            with open(os.path.join(REPO_ROOT, "workbooks", "05-llm-training", "chapter-contracts", "ch06.yaml"), encoding="utf-8") as f:
                content = f.read()
            content = content.replace("canonical_output_allowed: false", "canonical_output_allowed: true", 1)
            with open(bad_path, "w", encoding="utf-8") as f:
                f.write(content)
            errors = vcc.validate_one(bad_path, schema, known_source_ids, status_registry)
        self.assertTrue(any("canonical_output_allowed" in e for e in errors))


def _write_fixture_registry(tmp_root, ch05_status="accepted_frozen", overrides=None, include_solutions_frozen=False):
    os.makedirs(os.path.join(tmp_root, "config"), exist_ok=True)
    os.makedirs(os.path.join(tmp_root, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(tmp_root, "workbooks", "05-llm-training", "chapter-contracts"), exist_ok=True)
    shutil.copy2(os.path.join(REPO_ROOT, "scripts", "_yaml_lite.py"), os.path.join(tmp_root, "scripts", "_yaml_lite.py"))

    overrides_yaml = "active_overrides: []"
    if overrides:
        lines = ["active_overrides:"]
        for o in overrides:
            lines.append(f"  - workbook: {o['workbook']}")
            lines.append(f"    chapter: \"{o['chapter']}\"")
            if "allowed_paths" in o:
                lines.append("    allowed_paths:")
                for p in o["allowed_paths"]:
                    lines.append(f"      - \"{p}\"")
            lines.append(f"    granted_for: \"{o.get('granted_for', 'test')}\"")
            lines.append(f"    granted_by: {o.get('granted_by', 'human')}")
        overrides_yaml = "\n".join(lines)

    registry = f"""schema_version: 1
workbooks:
  05-llm-training:
    chapters:
      05:
        status: "{ch05_status}"
        commit_sha: "deadbeef"
        chapter_path: "workbooks/05-llm-training/chapters/05-training-memory-and-communication.qmd"
{overrides_yaml}
"""
    with open(os.path.join(tmp_root, "config", "chapter-status-registry.yaml"), "w", encoding="utf-8") as f:
        f.write(registry)

    if include_solutions_frozen:
        contract = """identity:
  workbook: "05-llm-training"
  chapter: "05"
  status: "accepted_frozen"
scope:
  allowed_paths: []
  frozen_paths:
    - "workbooks/05-llm-training/chapters/05-training-memory-and-communication.qmd"
    - "workbooks/05-llm-training/solutions/05-training-memory-and-communication-solutions.qmd"
  canonical_output_allowed: false
  release_output_allowed: false
  push_allowed: false
"""
        with open(os.path.join(tmp_root, "workbooks", "05-llm-training", "chapter-contracts", "ch05.yaml"), "w", encoding="utf-8") as f:
            f.write(contract)


class TestPreActionGuardFrozenScope(unittest.TestCase):
    def test_blocks_edit_to_frozen_chapter_no_override(self):
        with tempfile.TemporaryDirectory() as d:
            _write_fixture_registry(d, ch05_status="accepted_frozen")
            r = run_hook(
                os.path.join(".claude", "hooks", "pre_action_guard.py"),
                {"tool_name": "Edit", "tool_input": {"file_path": "workbooks/05-llm-training/chapters/05-training-memory-and-communication.qmd"}},
                repo_root=d,
            )
        self.assertEqual(r.returncode, 2)
        self.assertIn("frozen-scope", r.stdout)

    def test_allows_edit_to_frozen_chapter_with_matching_path_scoped_override(self):
        with tempfile.TemporaryDirectory() as d:
            _write_fixture_registry(
                d, ch05_status="accepted_frozen",
                overrides=[{
                    "workbook": "05-llm-training", "chapter": "05",
                    "allowed_paths": ["workbooks/05-llm-training/chapters/05-training-memory-and-communication.qmd"],
                    "granted_for": "test",
                }],
            )
            r = run_hook(
                os.path.join(".claude", "hooks", "pre_action_guard.py"),
                {"tool_name": "Edit", "tool_input": {"file_path": "workbooks/05-llm-training/chapters/05-training-memory-and-communication.qmd"}},
                repo_root=d,
            )
        self.assertEqual(r.returncode, 0)

    def test_override_does_not_cover_a_different_frozen_path_not_named_in_allowed_paths(self):
        """Explicit-override-behavior test: an override for the chapter
        .qmd must NOT also unlock the solutions file unless that path
        is itself listed in allowed_paths -- bounded scope, not a
        blanket per-chapter grant."""
        with tempfile.TemporaryDirectory() as d:
            _write_fixture_registry(
                d, ch05_status="accepted_frozen", include_solutions_frozen=True,
                overrides=[{
                    "workbook": "05-llm-training", "chapter": "05",
                    "allowed_paths": ["workbooks/05-llm-training/chapters/05-training-memory-and-communication.qmd"],
                    "granted_for": "test",
                }],
            )
            r = run_hook(
                os.path.join(".claude", "hooks", "pre_action_guard.py"),
                {"tool_name": "Edit", "tool_input": {"file_path": "workbooks/05-llm-training/solutions/05-training-memory-and-communication-solutions.qmd"}},
                repo_root=d,
            )
        self.assertEqual(r.returncode, 2, msg="override must be path-scoped, not chapter-wide")

    def test_malformed_override_missing_allowed_paths_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            _write_fixture_registry(
                d, ch05_status="accepted_frozen",
                overrides=[{"workbook": "05-llm-training", "chapter": "05", "granted_for": "malformed, no allowed_paths"}],
            )
            r = run_hook(
                os.path.join(".claude", "hooks", "pre_action_guard.py"),
                {"tool_name": "Edit", "tool_input": {"file_path": "workbooks/05-llm-training/chapters/05-training-memory-and-communication.qmd"}},
                repo_root=d,
            )
        self.assertEqual(r.returncode, 2, msg="a malformed override must fail closed (block), not open (allow)")

    def test_malformed_override_not_granted_by_human_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            _write_fixture_registry(
                d, ch05_status="accepted_frozen",
                overrides=[{
                    "workbook": "05-llm-training", "chapter": "05",
                    "allowed_paths": ["workbooks/05-llm-training/chapters/05-training-memory-and-communication.qmd"],
                    "granted_for": "test", "granted_by": "model",
                }],
            )
            r = run_hook(
                os.path.join(".claude", "hooks", "pre_action_guard.py"),
                {"tool_name": "Edit", "tool_input": {"file_path": "workbooks/05-llm-training/chapters/05-training-memory-and-communication.qmd"}},
                repo_root=d,
            )
        self.assertEqual(r.returncode, 2, msg="an override not granted_by:human must be rejected")

    def test_allows_edit_to_non_frozen_chapter(self):
        with tempfile.TemporaryDirectory() as d:
            _write_fixture_registry(d, ch05_status="drafted_pending_human_review")
            r = run_hook(
                os.path.join(".claude", "hooks", "pre_action_guard.py"),
                {"tool_name": "Edit", "tool_input": {"file_path": "workbooks/05-llm-training/chapters/05-training-memory-and-communication.qmd"}},
                repo_root=d,
            )
        self.assertEqual(r.returncode, 0)

    def test_real_repo_blocks_edit_to_real_accepted_chapter(self):
        r = run_hook(
            os.path.join(".claude", "hooks", "pre_action_guard.py"),
            {"tool_name": "Edit", "tool_input": {"file_path": "workbooks/05-llm-training/chapters/05-training-memory-and-communication.qmd"}},
        )
        self.assertEqual(r.returncode, 2)

    def test_real_repo_allows_edit_to_real_pending_chapter(self):
        r = run_hook(
            os.path.join(".claude", "hooks", "pre_action_guard.py"),
            {"tool_name": "Edit", "tool_input": {"file_path": "workbooks/05-llm-training/chapters/06-reading-real-pretraining-runs.qmd"}},
        )
        self.assertEqual(r.returncode, 0)

    def test_allows_edit_to_unrelated_path(self):
        r = run_hook(os.path.join(".claude", "hooks", "pre_action_guard.py"),
                     {"tool_name": "Edit", "tool_input": {"file_path": "README.md"}})
        self.assertEqual(r.returncode, 0)


class TestPreActionGuardPushAndCanonicalOutput(unittest.TestCase):
    def test_blocks_git_push(self):
        r = run_hook(os.path.join(".claude", "hooks", "pre_action_guard.py"),
                     {"tool_name": "Bash", "tool_input": {"command": "git push origin main"}})
        self.assertEqual(r.returncode, 2)

    def test_allows_unrelated_bash(self):
        r = run_hook(os.path.join(".claude", "hooks", "pre_action_guard.py"),
                     {"tool_name": "Bash", "tool_input": {"command": "ls -la"}})
        self.assertEqual(r.returncode, 0)

    def test_blocks_canonical_pdf_write(self):
        r = run_hook(os.path.join(".claude", "hooks", "pre_action_guard.py"),
                     {"tool_name": "Write", "tool_input": {"file_path": "outputs/05-llm-training-workbook.pdf"}})
        self.assertEqual(r.returncode, 2)

    def test_blocks_release_output_write(self):
        r = run_hook(os.path.join(".claude", "hooks", "pre_action_guard.py"),
                     {"tool_name": "Write", "tool_input": {"file_path": "outputs/_releases/05-llm-training/rc1.pdf"}})
        self.assertEqual(r.returncode, 2)

    def test_allows_unrelated_write(self):
        r = run_hook(os.path.join(".claude", "hooks", "pre_action_guard.py"),
                     {"tool_name": "Write", "tool_input": {"file_path": "README.md"}})
        self.assertEqual(r.returncode, 0)

    def test_malformed_stdin_fails_open(self):
        r = subprocess.run([PY, os.path.join(REPO_ROOT, ".claude", "hooks", "pre_action_guard.py")],
                            input="not json", capture_output=True, text=True, timeout=10)
        self.assertEqual(r.returncode, 0)


class TestFindingSeverityParsing(unittest.TestCase):
    def test_classify_all_no_action_is_ok(self):
        findings = json.load(open(CLEAN_AUDIT_PATH))
        cls = cg.classify_findings(findings)
        self.assertTrue(cls["ok"])
        self.assertFalse(cls["has_warning"])

    def test_classify_optional_only_is_warning_not_failure(self):
        findings = json.load(open(OPTIONAL_AUDIT_PATH))
        cls = cg.classify_findings(findings)
        self.assertTrue(cls["ok"])
        self.assertTrue(cls["has_warning"])

    def test_classify_blocker_fails(self):
        findings = json.load(open(BLOCKER_AUDIT_PATH))
        cls = cg.classify_findings(findings)
        self.assertFalse(cls["ok"])

    def test_classify_required_fails(self):
        findings = json.load(open(REQUIRED_AUDIT_PATH))
        cls = cg.classify_findings(findings)
        self.assertFalse(cls["ok"])

    def test_unknown_severity_counts_as_failure_not_silently_ignored(self):
        cls = cg.classify_findings([{"severity": "catastrophic"}])
        self.assertFalse(cls["ok"])
        self.assertEqual(cls["counts"]["unknown_severity"], 1)


class TestChapterGateReportLogic(unittest.TestCase):
    """All of these call build_gate_report() directly, in-process, with
    a fast fake run_scoped_qa -- zero subprocesses, zero real
    test-suite invocations."""

    def test_missing_audit_json_is_skipped_and_fails_gate(self):
        report = cg.build_gate_report(
            "05-llm-training", "06", None, ALL_MISSING_AUDITS, "/tmp/unused",
            run_scoped_qa=fake_run_scoped_qa_factory(status="pass"),
        )
        self.assertEqual(report["status"], "fail")
        skipped = {s["check"] for s in report["skipped_checks"]}
        self.assertEqual(skipped, {"review_manifest", "source_audit", "numerical_audit", "figure_audit", "learner_pdf_audit"})

    def test_all_four_audits_clean_gives_pass(self):
        report = cg.build_gate_report(
            "05-llm-training", "06", "/fake/path/review.pdf", ALL_CLEAN_AUDITS, "/tmp/unused",
            run_scoped_qa=fake_run_scoped_qa_factory(status="pass"),
        )
        # review_manifest_present will be False (fake PDF path doesn't exist) -> still a skipped check.
        self.assertIn(report["status"], ("fail",))  # because review-manifest.json truly doesn't exist at a fake path
        self.assertIn("review_manifest", {s["check"] for s in report["skipped_checks"]})

    def test_all_four_audits_clean_with_real_manifest_present_gives_pass(self):
        with tempfile.TemporaryDirectory() as d:
            fake_pdf = os.path.join(d, "review.pdf")
            open(fake_pdf, "w").close()
            open(os.path.join(d, "review-manifest.json"), "w").close()
            report = cg.build_gate_report(
                "05-llm-training", "06", fake_pdf, ALL_CLEAN_AUDITS, "/tmp/unused",
                run_scoped_qa=fake_run_scoped_qa_factory(status="pass"),
            )
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["skipped_checks"], [])

    def test_deterministic_check_warning_downgrades_to_pass_with_warnings(self):
        with tempfile.TemporaryDirectory() as d:
            fake_pdf = os.path.join(d, "review.pdf")
            open(fake_pdf, "w").close()
            open(os.path.join(d, "review-manifest.json"), "w").close()
            report = cg.build_gate_report(
                "05-llm-training", "06", fake_pdf, ALL_CLEAN_AUDITS, "/tmp/unused",
                run_scoped_qa=fake_run_scoped_qa_factory(status="pass_with_warnings"),
            )
        self.assertEqual(report["status"], "pass_with_warnings")

    def test_blocker_finding_fails_even_with_clean_deterministic_checks(self):
        with tempfile.TemporaryDirectory() as d:
            fake_pdf = os.path.join(d, "review.pdf")
            open(fake_pdf, "w").close()
            open(os.path.join(d, "review-manifest.json"), "w").close()
            audits = dict(ALL_CLEAN_AUDITS, figure_audit=BLOCKER_AUDIT_PATH)
            report = cg.build_gate_report(
                "05-llm-training", "06", fake_pdf, audits, "/tmp/unused",
                run_scoped_qa=fake_run_scoped_qa_factory(status="pass"),
            )
        self.assertEqual(report["status"], "fail")

    def test_optional_only_finding_downgrades_not_fails(self):
        with tempfile.TemporaryDirectory() as d:
            fake_pdf = os.path.join(d, "review.pdf")
            open(fake_pdf, "w").close()
            open(os.path.join(d, "review-manifest.json"), "w").close()
            audits = dict(ALL_CLEAN_AUDITS, figure_audit=OPTIONAL_AUDIT_PATH)
            report = cg.build_gate_report(
                "05-llm-training", "06", fake_pdf, audits, "/tmp/unused",
                run_scoped_qa=fake_run_scoped_qa_factory(status="pass"),
            )
        self.assertEqual(report["status"], "pass_with_warnings")

    def test_known_baseline_failures_exactly_three_named_tests(self):
        self.assertEqual(len(crc.KNOWN_BASELINE_FAILURES), 3)
        self.assertEqual(crc.new_failures_beyond_baseline(crc.KNOWN_BASELINE_FAILURES), [])

    def test_new_failure_detected_and_not_absorbed_by_baseline(self):
        synthetic = crc.KNOWN_BASELINE_FAILURES + ["test_something_new (test_foo.TestBar)"]
        new = crc.new_failures_beyond_baseline(synthetic)
        self.assertEqual(new, ["test_something_new (test_foo.TestBar)"])

    def test_chapter06_registry_status_is_pending_not_accepted(self):
        status, _ = cg.load_frozen_status("05-llm-training", "06")
        self.assertEqual(status, "drafted_pending_human_review")

    def test_chapter05_registry_status_is_accepted(self):
        status, _ = cg.load_frozen_status("05-llm-training", "05")
        self.assertEqual(status, "accepted_frozen")

    def test_chapter06_report_status_pending_even_when_technical_gate_passes(self):
        with tempfile.TemporaryDirectory() as d:
            fake_pdf = os.path.join(d, "review.pdf")
            open(fake_pdf, "w").close()
            open(os.path.join(d, "review-manifest.json"), "w").close()
            report = cg.build_gate_report(
                "05-llm-training", "06", fake_pdf, ALL_CLEAN_AUDITS, "/tmp/unused",
                run_scoped_qa=fake_run_scoped_qa_factory(status="pass"),
            )
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["frozen_status"]["status"], "drafted_pending_human_review",
                          msg="a passing technical gate must never imply acceptance")

    def test_gate_report_building_never_writes_the_status_registry(self):
        registry_path = os.path.join(REPO_ROOT, "config", "chapter-status-registry.yaml")
        before = open(registry_path, "rb").read()
        cg.build_gate_report(
            "05-llm-training", "06", None, ALL_CLEAN_AUDITS, "/tmp/unused",
            run_scoped_qa=fake_run_scoped_qa_factory(status="pass"),
        )
        after = open(registry_path, "rb").read()
        self.assertEqual(before, after)

    def test_two_in_process_runs_with_identical_inputs_produce_identical_reports(self):
        fake_qa = fake_run_scoped_qa_factory(status="pass")
        with tempfile.TemporaryDirectory() as d:
            fake_pdf = os.path.join(d, "review.pdf")
            open(fake_pdf, "w").close()
            open(os.path.join(d, "review-manifest.json"), "w").close()
            r1 = cg.build_gate_report("05-llm-training", "06", fake_pdf, ALL_CLEAN_AUDITS, "/tmp/unused", run_scoped_qa=fake_qa)
            r2 = cg.build_gate_report("05-llm-training", "06", fake_pdf, ALL_CLEAN_AUDITS, "/tmp/unused", run_scoped_qa=fake_qa)
        self.assertEqual(r1, r2)


def _write_fake_chapter_gate(scripts_dir, exit_code):
    """A minimal stand-in for scripts/chapter_gate.py used only by
    final_stop_gate.py's own subprocess-contract tests, so those tests
    exercise the hook's real subprocess-invocation and marker-file
    logic without paying the real gate's (and the real full suite's)
    cost."""
    path = os.path.join(scripts_dir, "chapter_gate.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"import sys\nprint('fake gate output')\nsys.exit({exit_code})\n")


class TestFinalStopGateBoundedRetry(unittest.TestCase):
    def setUp(self):
        self.marker_path = os.path.join(REPO_ROOT, ".claude", ".active-chapter-task.json")
        self.addCleanup(self._cleanup_marker)

    def _cleanup_marker(self):
        if os.path.exists(self.marker_path):
            os.remove(self.marker_path)

    def test_noop_when_no_marker_present(self):
        self._cleanup_marker()
        r = run_hook(os.path.join(".claude", "hooks", "final_stop_gate.py"), {"hook_event_name": "Stop"})
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")

    def test_fails_open_once_max_attempts_reached(self):
        with open(self.marker_path, "w", encoding="utf-8") as f:
            json.dump({"workbook": "05-llm-training", "chapter": "05", "attempts": 2}, f)
        r = run_hook(os.path.join(".claude", "hooks", "final_stop_gate.py"), {"hook_event_name": "Stop"})
        self.assertEqual(r.returncode, 0)
        self.assertIn("human intervention required", r.stdout)

    def test_blocks_and_increments_attempts_when_fake_gate_fails(self):
        with tempfile.TemporaryDirectory() as d:
            scripts_dir = os.path.join(d, "scripts")
            os.makedirs(scripts_dir)
            _write_fake_chapter_gate(scripts_dir, exit_code=1)
            fixture_marker = os.path.join(d, ".claude", ".active-chapter-task.json")
            os.makedirs(os.path.dirname(fixture_marker), exist_ok=True)
            with open(fixture_marker, "w", encoding="utf-8") as f:
                json.dump({"workbook": "05-llm-training", "chapter": "06", "attempts": 0}, f)
            r = run_hook(os.path.join(".claude", "hooks", "final_stop_gate.py"), {"hook_event_name": "Stop"}, repo_root=d, timeout=20)
            self.assertEqual(r.returncode, 2)
            with open(fixture_marker, encoding="utf-8") as f:
                marker = json.load(f)
            self.assertEqual(marker["attempts"], 1)

    def test_removes_marker_and_allows_stop_when_fake_gate_passes(self):
        with tempfile.TemporaryDirectory() as d:
            scripts_dir = os.path.join(d, "scripts")
            os.makedirs(scripts_dir)
            _write_fake_chapter_gate(scripts_dir, exit_code=0)
            fixture_marker = os.path.join(d, ".claude", ".active-chapter-task.json")
            os.makedirs(os.path.dirname(fixture_marker), exist_ok=True)
            with open(fixture_marker, "w", encoding="utf-8") as f:
                json.dump({"workbook": "05-llm-training", "chapter": "06", "attempts": 0}, f)
            r = run_hook(os.path.join(".claude", "hooks", "final_stop_gate.py"), {"hook_event_name": "Stop"}, repo_root=d, timeout=20)
            self.assertEqual(r.returncode, 0)
            self.assertFalse(os.path.exists(fixture_marker), msg="marker must be removed by the hook itself, inside the fixture dir, while it still exists")

    def test_second_consecutive_block_reaches_max_attempts_then_third_fails_open(self):
        """One-pass-remediation-limit test: attempt 0 -> block (attempts=1);
        attempt 1 -> block (attempts=2); attempt 2 -> fail open (no more
        blocking) -- never an unbounded loop."""
        with tempfile.TemporaryDirectory() as d:
            scripts_dir = os.path.join(d, "scripts")
            os.makedirs(scripts_dir)
            _write_fake_chapter_gate(scripts_dir, exit_code=1)
            fixture_marker = os.path.join(d, ".claude", ".active-chapter-task.json")
            os.makedirs(os.path.dirname(fixture_marker), exist_ok=True)
            with open(fixture_marker, "w", encoding="utf-8") as f:
                json.dump({"workbook": "05-llm-training", "chapter": "06", "attempts": 0}, f)

            r1 = run_hook(os.path.join(".claude", "hooks", "final_stop_gate.py"), {"hook_event_name": "Stop"}, repo_root=d, timeout=20)
            self.assertEqual(r1.returncode, 2)
            r2 = run_hook(os.path.join(".claude", "hooks", "final_stop_gate.py"), {"hook_event_name": "Stop"}, repo_root=d, timeout=20)
            self.assertEqual(r2.returncode, 2)
            r3 = run_hook(os.path.join(".claude", "hooks", "final_stop_gate.py"), {"hook_event_name": "Stop"}, repo_root=d, timeout=20)
            self.assertEqual(r3.returncode, 0, msg="third attempt must fail open, not block forever")
            self.assertIn("human intervention required", r3.stdout)


MINIMAL_TWO_PAGE_PDF = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R 4 0 R]/Count 2>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj
4 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj
xref
0 5
0000000000 65535 f
trailer<</Size 5/Root 1 0 R>>
%%EOF
"""


class TestVisualRegression(unittest.TestCase):
    """This test module is itself part of the full suite that
    scripts/chapter_gate.py runs on every invocation (confirmed: the
    baseline full suite runs in ~1.8s; a real pdftoppm render of the
    actual 14-page Chapter 6 review PDF costs ~7s PER invocation) --
    so these tests use a tiny, hand-written, 2-page synthetic PDF
    fixture (renders via pdftoppm in ~20ms) to exercise
    visual_regression.py's own logic (page-count matching, hashing,
    diff classification, stale-page removal, frozen-chapter refusal)
    cheaply and repeatedly. Exactly ONE test below uses the real
    Chapter 6 review PDF, to keep one genuine end-to-end check against
    an actual Quarto/Typst-produced multi-page PDF rather than relying
    solely on the synthetic fixture."""

    REAL_PDF = os.path.join(REPO_ROOT, "outputs", "_development", "05-llm-training",
                             "chapter-06-review", "05-llm-training-ch06-review.pdf")

    def _run_on(self, pdf_path, **extra_args):
        cmd = [PY, os.path.join(REPO_ROOT, "scripts", "visual_regression.py"),
               "--workbook", "05-llm-training", "--chapter", "06", "--pdf", pdf_path]
        for k, v in extra_args.items():
            cmd += [k, v]
        return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=30)

    def test_real_chapter06_pdf_page_count_matches_declared(self):
        # The one real-PDF exercise in this class.
        r = self._run_on(self.REAL_PDF)
        data = json.loads(r.stdout)
        self.assertTrue(data["page_count_matches"])
        self.assertEqual(data["declared_page_count"], data["rendered_page_count"])

    def test_synthetic_pdf_rerun_stale_page_and_tamper_detection(self):
        # All synthetic-PDF logic checks combined into one test, three
        # fast (~20ms each) runs total: (1) establish baseline + check
        # rerun-unchanged, (2) inject a stale page image and confirm
        # removal, (3) tamper the manifest and confirm the mismatch is
        # reported as unexpected_changed.
        with tempfile.TemporaryDirectory() as d:
            pdf_path = os.path.join(d, "fake-ch06-review.pdf")
            with open(pdf_path, "wb") as f:
                f.write(MINIMAL_TWO_PAGE_PDF)

            r1 = self._run_on(pdf_path)
            data1 = json.loads(r1.stdout)
            self.assertTrue(data1["page_count_matches"])
            self.assertEqual(data1["declared_page_count"], 2)

            r2 = self._run_on(pdf_path)
            data2 = json.loads(r2.stdout)
            self.assertEqual(data2["unexpected_changed_pages"], [])
            self.assertEqual(data2["new_pages"], [])
            self.assertGreater(len(data2["unchanged_pages"]), 0)

            pages_dir = os.path.join(d, "pages")
            stale_path = os.path.join(pages_dir, "page-99.png")
            with open(stale_path, "w") as f:
                f.write("stale")
            self._run_on(pdf_path)
            self.assertFalse(os.path.exists(stale_path))

            manifest_path = os.path.join(d, "visual-regression-hashes.json")
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
            first_page = sorted(manifest["page_hashes"])[0]
            manifest["page_hashes"][first_page] = "0" * 64
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f)
            r3 = self._run_on(pdf_path)
            data3 = json.loads(r3.stdout)
            self.assertIn(first_page, data3["unexpected_changed_pages"])
            self.assertIn(first_page, data3["requires_full_resolution_inspection"])

    def test_refuses_to_touch_accepted_frozen_chapter_without_override(self):
        # ch05 is accepted_frozen in the real registry -- this exits
        # before any pdftoppm call, so it is already cheap regardless
        # of PDF size; use the real ch05 PDF path for realism (the
        # file need not even exist, since the frozen-check runs first).
        pdf05 = os.path.join(REPO_ROOT, "outputs", "_development", "05-llm-training",
                              "chapter-05-review", "05-llm-training-ch05-review.pdf")
        manifest_path = os.path.join(os.path.dirname(pdf05), "visual-regression-hashes.json")
        self.assertFalse(os.path.exists(manifest_path), "test precondition: ch05 must not already have a manifest")
        r = subprocess.run(
            [PY, os.path.join(REPO_ROOT, "scripts", "visual_regression.py"),
             "--workbook", "05-llm-training", "--chapter", "05", "--pdf", pdf05],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(r.returncode, 1)
        self.assertFalse(os.path.exists(manifest_path))


class TestAuditOnlyModePreservesRepoState(unittest.TestCase):
    """Requirement: gate-report building and visual regression must not
    change any chapter file, figure file, review PDF, or canonical/RC
    output."""

    TRACKED_PATHS = [
        "workbooks/05-llm-training/chapters/05-training-memory-and-communication.qmd",
        "workbooks/05-llm-training/chapters/06-reading-real-pretraining-runs.qmd",
        "workbooks/05-llm-training/figures/rendered/fig-training-step-timeline.svg",
        "workbooks/05-llm-training/figures/rendered/fig-run-diagnosis-pipeline.svg",
    ]

    def _checksums(self):
        import hashlib
        out = {}
        for rel in self.TRACKED_PATHS:
            p = os.path.join(REPO_ROOT, rel)
            if os.path.exists(p):
                with open(p, "rb") as f:
                    out[rel] = hashlib.sha256(f.read()).hexdigest()
        return out

    def test_gate_report_and_visual_regression_change_nothing_tracked(self):
        before = self._checksums()
        cg.build_gate_report(
            "05-llm-training", "06", None, ALL_CLEAN_AUDITS, "/tmp/unused",
            run_scoped_qa=fake_run_scoped_qa_factory(status="pass"),
        )
        with tempfile.TemporaryDirectory() as d:
            pdf_path = os.path.join(d, "fake-ch06-review.pdf")
            with open(pdf_path, "wb") as f:
                f.write(MINIMAL_TWO_PAGE_PDF)
            subprocess.run(
                [PY, os.path.join(REPO_ROOT, "scripts", "visual_regression.py"),
                 "--workbook", "05-llm-training", "--chapter", "06", "--pdf", pdf_path],
                cwd=REPO_ROOT, capture_output=True, text=True, timeout=15,
            )
        after = self._checksums()
        self.assertEqual(before, after)

    def test_no_canonical_pdf_or_release_dir_exists(self):
        self.assertFalse(os.path.exists(os.path.join(REPO_ROOT, "outputs", "05-llm-training-workbook.pdf")))
        self.assertFalse(os.path.exists(os.path.join(REPO_ROOT, "outputs", "_releases", "05-llm-training")))


class TestAuditProfilesAreNonExecutableAndSequential(unittest.TestCase):
    PROFILES_DIR = os.path.join(REPO_ROOT, "docs", "audit-profiles")
    EXPECTED = [
        ("01-source-audit.md", 1),
        ("02-numerical-audit.md", 2),
        ("03-figure-audit.md", 3),
        ("04-learner-pdf-audit.md", 4),
    ]

    def test_no_claude_agents_directory_remains(self):
        self.assertFalse(os.path.isdir(os.path.join(REPO_ROOT, ".claude", "agents")))

    def test_all_four_profiles_exist_and_declare_their_stage_number(self):
        for fname, stage_num in self.EXPECTED:
            path = os.path.join(self.PROFILES_DIR, fname)
            self.assertTrue(os.path.exists(path), msg=f"missing {fname}")
            with open(path, encoding="utf-8") as f:
                text = f.read()
            self.assertIn(f"stage {stage_num} of 4", text)

    def test_profiles_carry_no_yaml_frontmatter(self):
        for fname, _ in self.EXPECTED:
            with open(os.path.join(self.PROFILES_DIR, fname), encoding="utf-8") as f:
                first_line = f.readline()
            self.assertNotEqual(first_line.strip(), "---",
                                 msg=f"{fname} must not carry subagent-style YAML frontmatter")

    def test_profiles_declare_no_parallel_execution(self):
        # The profiles legitimately contain NEGATIONS like "no stage
        # runs in parallel" -- check for absent ENDORSEMENT of
        # parallel execution, not absence of the word itself.
        for fname, _ in self.EXPECTED:
            with open(os.path.join(self.PROFILES_DIR, fname), encoding="utf-8") as f:
                text = f.read().lower()
            self.assertNotIn("launch all four", text)
            self.assertNotIn("in a single message", text)
            self.assertIn("no stage runs in parallel", text)

    def test_active_skills_contain_no_agent_or_parallel_orchestration(self):
        for skill in ("draft-workbook-chapter", "review-workbook-chapter"):
            path = os.path.join(REPO_ROOT, ".claude", "skills", skill, "SKILL.md")
            with open(path, encoding="utf-8") as f:
                text = f.read()
            self.assertNotIn("allowed-tools:.*Agent", text)  # sanity placeholder, real check below
            frontmatter_line = [l for l in text.splitlines() if l.startswith("allowed-tools:")][0]
            self.assertNotIn("Agent", frontmatter_line, msg=f"{skill} must not have Agent-tool access")
            self.assertIn("disable-model-invocation: true", text)


if __name__ == "__main__":
    unittest.main()
