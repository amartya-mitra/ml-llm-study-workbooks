#!/usr/bin/env python3
"""Validate sources/registry.yaml and sources/coverage-matrix.yaml.

Checks (see tests/test_registry.py for the pytest-free test wrapper):
    - registry loads and has a top-level 'sources' list
    - every source has all required fields
    - every source id is unique
    - every source id matches the expected pattern
    - every url looks like a URL
    - every workbook_categories entry is a known workbook id
    - every source id referenced in coverage-matrix.yaml exists in the registry
"""
import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from _yaml_lite import safe_load_path  # noqa: E402

REQUIRED_FIELDS = [
    "id", "title", "url", "authors", "resource_type", "workbook_categories",
    "topic_tags", "authority_type", "expected_use", "last_verified",
    "access_status", "license_or_reuse", "notes",
]

# Non-empty is checked for every required field except these two, which are
# allowed to be empty/null by design: workbook_categories/topic_tags are
# lists (checked separately), and last_verified is legitimately null until
# a source has actually been fetched and checked (AGENTS.md).
NON_EMPTY_STRING_FIELDS = [
    f for f in REQUIRED_FIELDS if f not in ("workbook_categories", "topic_tags", "last_verified")
]

# Matches the categories documented in README.md's "Source policy" section.
ALLOWED_AUTHORITY_TYPES = {
    "primary_technical",
    "implementation_guide",
    "visual_reference",
    "interview_question_bank",
    "secondary_summary",
    "source_discovery_index",
    "experiential_account",
}

ID_PATTERN = re.compile(r"^src-\d{2,}$")
URL_PATTERN = re.compile(r"^https?://")


def known_workbook_ids():
    project = safe_load_path(os.path.join(REPO_ROOT, "config", "project.yaml"))
    return {wb["id"] for wb in project["workbooks"]}


def validate_registry():
    errors = []
    reg_path = os.path.join(REPO_ROOT, "sources", "registry.yaml")
    data = safe_load_path(reg_path)
    if not data or "sources" not in data:
        return [f"{reg_path}: missing top-level 'sources' key"]

    sources = data["sources"]
    ids_seen = set()
    valid_workbooks = known_workbook_ids()

    for entry in sources:
        sid = entry.get("id", "<missing id>")
        for field in REQUIRED_FIELDS:
            if field not in entry:
                errors.append(f"{sid}: missing required field '{field}'")
        for field in NON_EMPTY_STRING_FIELDS:
            if field in entry and not str(entry[field]).strip():
                errors.append(f"{sid}: field '{field}' is present but empty")
        if not ID_PATTERN.match(str(sid)):
            errors.append(f"{sid}: id does not match pattern ^src-\\d{{2,}}$")
        if sid in ids_seen:
            errors.append(f"{sid}: duplicate source id")
        ids_seen.add(sid)

        url = entry.get("url", "")
        if not URL_PATTERN.match(str(url)):
            errors.append(f"{sid}: url does not look like http(s) url: {url!r}")

        authority_type = entry.get("authority_type")
        if authority_type is not None and authority_type not in ALLOWED_AUTHORITY_TYPES:
            errors.append(
                f"{sid}: authority_type '{authority_type}' not in {sorted(ALLOWED_AUTHORITY_TYPES)}"
            )

        workbook_categories = entry.get("workbook_categories")
        if workbook_categories is not None and not isinstance(workbook_categories, list):
            errors.append(f"{sid}: workbook_categories must be a list, got {type(workbook_categories).__name__}")
        for wb in workbook_categories or []:
            if wb not in valid_workbooks:
                errors.append(f"{sid}: unknown workbook_category '{wb}'")

    cov_path = os.path.join(REPO_ROOT, "sources", "coverage-matrix.yaml")
    cov = safe_load_path(cov_path)
    for wb_entry in cov.get("workbooks", []):
        wb_id = wb_entry.get("id")
        if wb_id not in valid_workbooks:
            errors.append(f"coverage-matrix: unknown workbook id '{wb_id}'")
        for src_entry in wb_entry.get("sources", []) or []:
            sid = src_entry.get("id")
            if sid not in ids_seen:
                errors.append(f"coverage-matrix: workbook '{wb_id}' references unknown source id '{sid}'")

    return errors


def main():
    errors = validate_registry()
    if errors:
        print(f"FAILED: {len(errors)} issue(s) found")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("OK: registry and coverage matrix are valid")


if __name__ == "__main__":
    main()
