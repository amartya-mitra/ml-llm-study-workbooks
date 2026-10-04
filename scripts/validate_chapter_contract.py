#!/usr/bin/env python3
"""Validate every workbooks/*/chapter-contracts/*.yaml against
shared/chapter-contract-schema.yaml, and cross-check it against the
real repo state: config/chapter-status-registry.yaml (identity.status
must agree exactly) and sources/registry.yaml (every required source
id must actually exist).

This is the chapter-contract analogue of scripts/validate_questions.py
(shared/question-schema.yaml) and follows the same hand-written,
no-PyYAML/no-jsonschema convention -- see that script and
shared/claim-ledger-schema.yaml for the established pattern this one
extends rather than duplicates.
"""
import glob
import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from _yaml_lite import safe_load_path  # noqa: E402

REQUIRED_SECTIONS = [
    "identity", "scope", "sources", "content",
    "worked_examples", "figures", "learner_facing", "acceptance",
]


def load_schema():
    return safe_load_path(os.path.join(REPO_ROOT, "shared", "chapter-contract-schema.yaml"))


def load_known_source_ids():
    reg = safe_load_path(os.path.join(REPO_ROOT, "sources", "registry.yaml"))
    return {s["id"] for s in reg["sources"]}


def load_status_registry():
    path = os.path.join(REPO_ROOT, "config", "chapter-status-registry.yaml")
    if not os.path.exists(path):
        return None
    return safe_load_path(path)


def find_contract_files():
    return sorted(glob.glob(os.path.join(REPO_ROOT, "workbooks", "*", "chapter-contracts", "*.yaml")))


def _check_section_fields(rel, section_name, section_def, section_data, errors):
    fields = {f["name"]: f for f in section_def.get("fields", [])}
    for fname, fdef in fields.items():
        qualified = f"{section_name}.{fname}"
        if fdef.get("required") and fname not in section_data:
            errors.append(f"{rel}: missing required field '{qualified}'")
            continue
        if fname not in section_data:
            continue
        value = section_data[fname]
        ftype = fdef.get("type", "")
        if ftype == "string" and fdef.get("required") and not str(value).strip():
            errors.append(f"{rel}: required field '{qualified}' is present but empty")
        if ftype.startswith("list") and not isinstance(value, list):
            errors.append(f"{rel}: field '{qualified}' must be a list, got {type(value).__name__}")
        if ftype == "bool" and not isinstance(value, bool):
            errors.append(f"{rel}: field '{qualified}' must be a bool, got {type(value).__name__}")
        if ftype == "int" and not isinstance(value, int):
            errors.append(f"{rel}: field '{qualified}' must be an int, got {type(value).__name__}")
        allowed = fdef.get("allowed_values")
        if allowed and value not in allowed:
            errors.append(f"{rel}: field '{qualified}' value {value!r} not in {allowed}")
        pattern = fdef.get("pattern")
        if pattern and not re.match(pattern, str(value)):
            errors.append(f"{rel}: field '{qualified}' value {value!r} does not match pattern {pattern}")


def validate_one(path, schema, known_source_ids, status_registry):
    rel = os.path.relpath(path, REPO_ROOT)
    errors = []
    data = safe_load_path(path) or {}

    for section_name in REQUIRED_SECTIONS:
        if section_name not in data:
            errors.append(f"{rel}: missing required top-level section '{section_name}'")
    if errors:
        return errors  # no point checking nested fields on a structurally broken file

    schema_sections = {s["name"]: s for s in schema["sections"]}
    for section_name, section_def in schema_sections.items():
        _check_section_fields(rel, section_name, section_def, data.get(section_name, {}), errors)

    # Cross-checks against real repo state.
    identity = data.get("identity", {})
    workbook = identity.get("workbook")
    chapter = identity.get("chapter")
    contract_status = identity.get("status")

    if status_registry is not None and workbook and chapter:
        wb_entry = (status_registry.get("workbooks") or {}).get(workbook, {})
        chapters = wb_entry.get("chapters") or {}
        registry_status = (chapters.get(chapter) or {}).get("status")
        if registry_status is None:
            errors.append(
                f"{rel}: identity.workbook/chapter ({workbook}/{chapter}) has no entry in "
                f"config/chapter-status-registry.yaml -- every real chapter contract must be "
                f"registered there"
            )
        elif registry_status != contract_status:
            errors.append(
                f"{rel}: identity.status ({contract_status!r}) does not match "
                f"config/chapter-status-registry.yaml's status ({registry_status!r}) for "
                f"{workbook}/{chapter} -- these two files must never silently disagree"
            )

    for sid in (data.get("sources") or {}).get("required_source_ids", []) or []:
        if sid not in known_source_ids:
            errors.append(f"{rel}: sources.required_source_ids contains '{sid}', not found in sources/registry.yaml")

    content = data.get("content") or {}
    if "question_count" in content and "answer_count" in content:
        if content["question_count"] != content["answer_count"]:
            errors.append(
                f"{rel}: content.question_count ({content['question_count']}) != "
                f"content.answer_count ({content['answer_count']})"
            )

    scope = data.get("scope") or {}
    if scope.get("canonical_output_allowed") is not False:
        errors.append(f"{rel}: scope.canonical_output_allowed must be false for a chapter-level contract")
    if scope.get("release_output_allowed") is not False:
        errors.append(f"{rel}: scope.release_output_allowed must be false for a chapter-level contract")

    return errors


def validate_all():
    schema = load_schema()
    known_source_ids = load_known_source_ids()
    status_registry = load_status_registry()
    files = find_contract_files()

    all_errors = []
    for path in files:
        all_errors.extend(validate_one(path, schema, known_source_ids, status_registry))
    return all_errors, len(files)


def main():
    errors, total = validate_all()
    if errors:
        print(f"FAILED: {len(errors)} issue(s) found across {total} chapter contract(s)")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print(f"OK: {total} chapter contract(s) validated against shared/chapter-contract-schema.yaml")


if __name__ == "__main__":
    main()
