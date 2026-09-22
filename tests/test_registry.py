"""Tests for sources/registry.yaml and sources/coverage-matrix.yaml.

Run with: python3 -m unittest discover -s tests -v
(no pytest dependency required — see reports/bootstrap_environment.md)
"""
import os
import re
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from _yaml_lite import safe_load_path  # noqa: E402


class TestRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = safe_load_path(os.path.join(REPO_ROOT, "sources", "registry.yaml"))
        cls.sources = cls.registry["sources"]
        cls.coverage = safe_load_path(os.path.join(REPO_ROOT, "sources", "coverage-matrix.yaml"))
        cls.project = safe_load_path(os.path.join(REPO_ROOT, "config", "project.yaml"))
        cls.known_workbooks = {wb["id"] for wb in cls.project["workbooks"]}

    def test_registry_has_sources(self):
        self.assertGreater(len(self.sources), 0)

    def test_unique_source_ids(self):
        ids = [s["id"] for s in self.sources]
        self.assertEqual(len(ids), len(set(ids)), "duplicate source id found")

    def test_source_id_pattern(self):
        pattern = re.compile(r"^src-\d{2,}$")
        for s in self.sources:
            self.assertRegex(s["id"], pattern)

    def test_valid_urls(self):
        for s in self.sources:
            self.assertRegex(s["url"], r"^https?://", msg=f"{s['id']} has a malformed url")

    def test_required_fields_present(self):
        required = [
            "id", "title", "url", "authors", "resource_type",
            "workbook_categories", "topic_tags", "authority_type",
            "expected_use", "access_status", "license_or_reuse", "notes",
        ]
        for s in self.sources:
            for field in required:
                self.assertIn(field, s, msg=f"{s.get('id')} missing field {field}")

    def test_workbook_categories_are_known(self):
        for s in self.sources:
            for wb in s["workbook_categories"]:
                self.assertIn(wb, self.known_workbooks, msg=f"{s['id']} references unknown workbook {wb}")

    def test_coverage_matrix_references_known_sources(self):
        known_ids = {s["id"] for s in self.sources}
        for wb_entry in self.coverage["workbooks"]:
            self.assertIn(wb_entry["id"], self.known_workbooks)
            for src_entry in wb_entry["sources"]:
                self.assertIn(src_entry["id"], known_ids)


if __name__ == "__main__":
    unittest.main()
