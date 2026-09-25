"""Stage 10 review-gate tests for the workbook 04 blueprint.

Formalizes the manual checks run during blueprint design so a future
edit to outline.yaml/figure-plan.yaml/example-plan.yaml/question-plan.yaml
can't silently violate a review gate (page budget, figure count, source
id references) without a test catching it.
"""
import os
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WB04 = os.path.join(REPO_ROOT, "workbooks", "04-llm-architecture")
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from _yaml_lite import safe_load_path  # noqa: E402


def collect_source_ids(obj, found=None):
    """Recursively collect every value under a 'source_ids' key, plus
    every value under 'primary_source_ids'/'explanatory_source_ids'/
    'primary_sources'/'secondary_sources' keys, anywhere in a nested
    YAML-lite structure."""
    if found is None:
        found = []
    id_keys = {
        "source_ids", "primary_source_ids", "explanatory_source_ids",
        "primary_sources", "secondary_sources",
    }
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in id_keys and isinstance(v, list):
                found.extend(v)
            else:
                collect_source_ids(v, found)
    elif isinstance(obj, list):
        for item in obj:
            collect_source_ids(item, found)
    return found


class TestWorkbook04Blueprint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outline = safe_load_path(os.path.join(WB04, "outline.yaml"))
        cls.glossary = safe_load_path(os.path.join(WB04, "glossary.yaml"))
        cls.notation = safe_load_path(os.path.join(WB04, "notation.yaml"))
        cls.source_coverage = safe_load_path(os.path.join(WB04, "source-coverage.yaml"))
        cls.figure_plan = safe_load_path(os.path.join(WB04, "figure-plan.yaml"))
        cls.example_plan = safe_load_path(os.path.join(WB04, "example-plan.yaml"))
        cls.question_plan = safe_load_path(os.path.join(WB04, "question-plan.yaml"))
        registry = safe_load_path(os.path.join(REPO_ROOT, "sources", "registry.yaml"))
        cls.known_source_ids = {s["id"] for s in registry["sources"]}

    def test_all_blueprint_files_parse(self):
        for data in (self.outline, self.glossary, self.notation, self.source_coverage,
                     self.figure_plan, self.example_plan, self.question_plan):
            self.assertIsInstance(data, dict)

    def test_outline_has_eight_chapters(self):
        self.assertEqual(len(self.outline["chapters"]), 8)

    def test_outline_page_budget_within_ceiling(self):
        total = sum(c["estimated_pages"] for c in self.outline["chapters"])
        self.assertEqual(total, self.outline["estimated_total_pages"])
        self.assertLessEqual(total, self.outline["page_ceiling"])

    def test_every_chapter_has_a_purpose_and_objectives(self):
        for c in self.outline["chapters"]:
            self.assertTrue(c["purpose"].strip(), msg=f"{c['id']} has no purpose")
            self.assertGreater(len(c["learning_objectives"]), 0, msg=f"{c['id']} has no learning objectives")

    def test_figure_count_within_stage7_target_range(self):
        # Ceiling raised 18->19->20 (2026-09-23, 2026-09-25): Chapters 6
        # and 7 each had their own drafting task mandate exactly 2
        # figures, one more than each chapter's original single-figure
        # plan -- a disclosed, deliberate increase, not scope creep.
        # See figure-plan.yaml's figure_count_check.revision_note.
        count = len(self.figure_plan["figures"])
        self.assertGreaterEqual(count, 12)
        self.assertLessEqual(count, 20)
        self.assertEqual(count, self.figure_plan["figure_count_check"]["planned_count"])

    def test_every_figure_has_an_attribution_decision(self):
        for f in self.figure_plan["figures"]:
            self.assertIn("must_be_redrawn", f)
            self.assertIn("attribution_requirement", f)

    def test_cumulative_and_interview_question_counts_within_target(self):
        self.assertGreaterEqual(len(self.question_plan["cumulative_review_questions"]), 10)
        self.assertLessEqual(len(self.question_plan["cumulative_review_questions"]), 15)
        self.assertGreaterEqual(len(self.question_plan["interview_style_questions"]), 6)
        self.assertLessEqual(len(self.question_plan["interview_style_questions"]), 10)

    def test_every_quick_question_targets_two_to_four_per_chapter(self):
        per_chapter = {}
        for q in self.question_plan["quick_questions"]:
            per_chapter[q["chapter"]] = per_chapter.get(q["chapter"], 0) + 1
        chapter_ids = {c["id"] for c in self.outline["chapters"]}
        for ch_id in chapter_ids:
            count = per_chapter.get(ch_id, 0)
            # ch8 is a deliberate exception (see question-plan.yaml's ch8_note):
            # it is the cumulative/interview capstone and introduces no new
            # quick questions of its own.
            if ch_id == "ch8":
                self.assertEqual(count, 0)
            else:
                self.assertGreaterEqual(count, 2, msg=f"{ch_id} has fewer than 2 quick questions")
                self.assertLessEqual(count, 4, msg=f"{ch_id} has more than 4 quick questions")

    def test_all_referenced_source_ids_exist_in_registry(self):
        for label, data in [
            ("outline.yaml", self.outline),
            ("glossary.yaml", self.glossary),
            ("source-coverage.yaml", self.source_coverage),
            ("figure-plan.yaml", self.figure_plan),
            ("example-plan.yaml", self.example_plan),
            ("question-plan.yaml", self.question_plan),
        ]:
            for sid in collect_source_ids(data):
                self.assertIn(sid, self.known_source_ids, msg=f"{label} references unknown source id {sid!r}")

    def test_disputed_claims_are_not_silently_flattened(self):
        disputed = [c for c in self.source_coverage["claims"] if c["status"] == "disputed"]
        self.assertGreater(len(disputed), 0, msg="expected at least the MoE load-balancing disagreement to be tracked as disputed")
        for c in disputed:
            self.assertGreater(len(c["primary_source_ids"]), 1, msg="a disputed claim should cite more than one disagreeing source")


if __name__ == "__main__":
    unittest.main()
