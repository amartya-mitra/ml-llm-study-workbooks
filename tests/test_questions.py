"""Tests for shared/question-schema.yaml and workbooks/**/questions.yaml."""
import os
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from _yaml_lite import safe_load_path  # noqa: E402
from validate_questions import find_question_files, validate_all, load_schema  # noqa: E402


class TestQuestionSchema(unittest.TestCase):
    def test_schema_loads(self):
        schema = load_schema()
        self.assertIn("fields", schema)
        field_names = {f["name"] for f in schema["fields"]}
        expected = {
            "id", "workbook", "chapter", "topic", "difficulty",
            "question_type", "prompt", "expected_answer", "explanation",
            "common_wrong_answer", "source_ids",
        }
        self.assertEqual(field_names, expected)

    def test_allowed_question_types_match_workbook_defaults(self):
        schema = load_schema()
        defaults = safe_load_path(os.path.join(REPO_ROOT, "config", "workbook-defaults.yaml"))
        qtype_field = next(f for f in schema["fields"] if f["name"] == "question_type")
        self.assertEqual(set(qtype_field["allowed_values"]), set(defaults["question_defaults"]["allowed_types"]))

    def test_no_validation_errors_in_existing_question_files(self):
        errors, total = validate_all()
        self.assertEqual(errors, [], msg="\n".join(errors))

    def test_question_files_are_discoverable(self):
        # Not an error if there are none yet at bootstrap time; just checks
        # the glob pattern matches the convention used elsewhere in the repo.
        files = find_question_files()
        for f in files:
            self.assertTrue(f.endswith("questions.yaml"))


if __name__ == "__main__":
    unittest.main()
