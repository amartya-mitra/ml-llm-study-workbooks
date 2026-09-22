"""Structural tests: expected directories exist, figures have sources,
bibliography keys are consistent with the registry.
"""
import glob
import os
import re
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from _yaml_lite import safe_load_path  # noqa: E402

EXPECTED_DIRS = [
    "config", "sources", "sources/snapshots", "shared", "shared/figure-template",
    "workbooks/01-ml-foundations", "workbooks/02-ml-interviews",
    "workbooks/03-ml-systems-design", "workbooks/04-llm-architecture",
    "workbooks/05-llm-training", "workbooks/06-llm-inference",
    "workbooks/07-llm-post-training", "workbooks/08-research-careers",
    "figures/source", "figures/rendered", "scripts", "reports", "tests", "outputs",
]

EXPECTED_WORKBOOK_IDS = [
    "01-ml-foundations", "02-ml-interviews", "03-ml-systems-design",
    "04-llm-architecture", "05-llm-training", "06-llm-inference",
    "07-llm-post-training", "08-research-careers",
]


class TestProjectStructure(unittest.TestCase):
    def test_expected_directories_exist(self):
        for rel in EXPECTED_DIRS:
            path = os.path.join(REPO_ROOT, rel)
            self.assertTrue(os.path.isdir(path), msg=f"missing expected directory: {rel}")

    def test_project_yaml_lists_all_eight_workbooks(self):
        project = safe_load_path(os.path.join(REPO_ROOT, "config", "project.yaml"))
        ids = [wb["id"] for wb in project["workbooks"]]
        self.assertEqual(ids, EXPECTED_WORKBOOK_IDS)

    def test_every_rendered_figure_has_a_source_script(self):
        rendered = glob.glob(os.path.join(REPO_ROOT, "figures", "rendered", "*.svg"))
        for svg_path in rendered:
            figure_id = os.path.splitext(os.path.basename(svg_path))[0]
            source_path = os.path.join(REPO_ROOT, "figures", "source", f"{figure_id}.py")
            self.assertTrue(
                os.path.exists(source_path),
                msg=f"rendered figure {svg_path} has no matching source script {source_path}",
            )

    def test_bibliography_keys_match_registry_ids(self):
        bib_path = os.path.join(REPO_ROOT, "shared", "bibliography.bib")
        with open(bib_path, encoding="utf-8") as f:
            bib_text = f.read()
        bib_keys = set(re.findall(r"@\w+\{([^,]+),", bib_text))

        registry = safe_load_path(os.path.join(REPO_ROOT, "sources", "registry.yaml"))
        registry_ids = {s["id"] for s in registry["sources"]}

        self.assertEqual(bib_keys, registry_ids, msg="bibliography.bib keys and registry.yaml ids have diverged")


if __name__ == "__main__":
    unittest.main()
