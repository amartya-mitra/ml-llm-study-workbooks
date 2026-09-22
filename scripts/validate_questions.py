#!/usr/bin/env python3
"""Validate every workbooks/**/questions.yaml against shared/question-schema.yaml.

Checks: required fields present, allowed_values respected, id pattern and
uniqueness (project-wide), and that every source_ids entry exists in
sources/registry.yaml.
"""
import glob
import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from _yaml_lite import safe_load_path  # noqa: E402


def load_schema():
    return safe_load_path(os.path.join(REPO_ROOT, "shared", "question-schema.yaml"))


def load_known_source_ids():
    reg = safe_load_path(os.path.join(REPO_ROOT, "sources", "registry.yaml"))
    return {s["id"] for s in reg["sources"]}


def find_question_files():
    return sorted(glob.glob(os.path.join(REPO_ROOT, "workbooks", "**", "questions.yaml"), recursive=True))


def validate_all():
    errors = []
    schema = load_schema()
    fields = {f["name"]: f for f in schema["fields"]}
    known_source_ids = load_known_source_ids()
    seen_ids = set()

    files = find_question_files()
    if not files:
        return [], 0  # no questions authored yet is not an error at bootstrap time

    total = 0
    for path in files:
        rel = os.path.relpath(path, REPO_ROOT)
        data = safe_load_path(path)
        questions = (data or {}).get("questions", [])
        for q in questions:
            total += 1
            qid = q.get("id", "<missing id>")
            for fname, fdef in fields.items():
                if fdef.get("required") and fname not in q:
                    errors.append(f"{rel}::{qid}: missing required field '{fname}'")
                    continue
                if fname not in q:
                    continue
                value = q[fname]
                field_type = fdef.get("type", "")
                if field_type == "string" and fdef.get("required") and not str(value).strip():
                    errors.append(f"{rel}::{qid}: required field '{fname}' is present but empty")
                if field_type.startswith("list") and not isinstance(value, list):
                    errors.append(f"{rel}::{qid}: field '{fname}' must be a list, got {type(value).__name__}")
                allowed = fdef.get("allowed_values")
                if allowed and value not in allowed:
                    errors.append(f"{rel}::{qid}: field '{fname}' value {value!r} not in {allowed}")
                pattern = fdef.get("pattern")
                if pattern and fname == "id" and not re.match(pattern, str(value)):
                    errors.append(f"{rel}::{qid}: id {value!r} does not match pattern {pattern}")

            if qid in seen_ids:
                errors.append(f"{rel}::{qid}: duplicate question id across project")
            seen_ids.add(qid)

            source_ids = q.get("source_ids", [])
            if isinstance(source_ids, list):
                for sid in source_ids:
                    if sid not in known_source_ids:
                        errors.append(f"{rel}::{qid}: source id '{sid}' not found in sources/registry.yaml")

    return errors, total


def main():
    errors, total = validate_all()
    if errors:
        print(f"FAILED: {len(errors)} issue(s) found across {total} question(s)")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print(f"OK: {total} question(s) validated against shared/question-schema.yaml")


if __name__ == "__main__":
    main()
