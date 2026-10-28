"""Structural and integration tests for the Workbook 06 scaffold
(LLM Inference Engineering; scaffold only, no chapter drafted -- see
reports/06_llm_inference_scope_and_source_decision.md).

They check structure, registration and output routing, not content:
the seven approved chapters exist in order with stable anchors and the
required headings; the scaffold carries no citations, figures or
question/answer content; contracts, the status registry, the claim
ledger's planned source mappings and the registry agree; development
builds route away from the canonical PDF, which stays absent.
"""
import importlib.util
import os
import re
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from _yaml_lite import safe_load_path  # noqa: E402

WB_ID = "06-llm-inference"
WB = os.path.join(REPO_ROOT, "workbooks", WB_ID)
SLUGS = [
    "01-inference-workload",
    "02-kv-cache-memory",
    "03-serving-and-scheduling",
    "04-efficient-execution",
    "05-quantization",
    "06-speculative-decoding",
    "07-reading-and-benchmarking",
]
REQUIRED_HEADINGS = [
    "Learning objectives", "Why this matters", "Mental model or analogy", "Visual overview",
    "Technical core", "Worked example", "Compare and contrast", "Check your understanding",
    "Applied exercise", "Interview lens", "Chapter recap", "Sources and further reading",
]
CANONICAL = os.path.join(REPO_ROOT, "outputs", "06-llm-inference-workbook.pdf")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def chapter(n):
    return read(os.path.join(WB, "chapters", SLUGS[n - 1] + ".qmd"))


def solution(n):
    return read(os.path.join(WB, "solutions", SLUGS[n - 1] + "-solutions.qmd"))


def load_workbook_qa():
    spec = importlib.util.spec_from_file_location("workbook_qa", os.path.join(REPO_ROOT, "scripts", "workbook_qa.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestStructure(unittest.TestCase):
    def test_exactly_the_seven_approved_chapters_and_solutions(self):
        self.assertEqual(sorted(f for f in os.listdir(os.path.join(WB, "chapters")) if f.endswith(".qmd")),
                         [s + ".qmd" for s in SLUGS])
        self.assertEqual(sorted(f for f in os.listdir(os.path.join(WB, "solutions")) if f.endswith(".qmd")),
                         [s + "-solutions.qmd" for s in SLUGS])

    def test_index_includes_chapters_then_solutions_in_order(self):
        includes = re.findall(r"\{\{< include ([a-z]+/[a-z0-9-]+\.qmd) >\}\}", read(os.path.join(WB, "index.qmd")))
        self.assertEqual(includes, [f"chapters/{s}.qmd" for s in SLUGS] + [f"solutions/{s}-solutions.qmd" for s in SLUGS])

    def test_index_is_labelled_a_development_scaffold(self):
        index = read(os.path.join(WB, "index.qmd"))
        self.assertIn('title: "LLM Inference Engineering"', index)
        self.assertIn("Development scaffold", index)
        front = index.split("---")[1]  # YAML title block only (the source comment may say what it is not)
        self.assertNotRegex(front, r"(?i)release candidate|final edition")

    def test_stable_anchors(self):
        for n in range(1, 8):
            text = chapter(n)
            self.assertEqual(re.findall(r"^## .+\{#(sec-ch\d+)\}", text, re.MULTILINE), [f"sec-ch{n}"])
            self.assertIn(f"### Check your understanding {{#sec-ch{n}-check}}", text)
            self.assertIn(f"{{#sec-solutions-ch{n} .unnumbered}}", solution(n))
            self.assertIn(f"@sec-ch{n}-check", solution(n))

    def test_required_headings_in_order(self):
        for n in range(1, 8):
            found = re.findall(r"^### ([^{\n]+?)(?: \{#[^}]+\})?$", chapter(n), re.MULTILINE)
            self.assertEqual(found, REQUIRED_HEADINGS, msg=f"chapter {n}")

    def test_scaffold_has_no_content_or_evidence(self):
        for n in range(1, 8):
            text = chapter(n) + solution(n)
            self.assertIn("drafting has not yet begun", chapter(n))
            for label in ("**Purpose.**", "**Prerequisites and planned recap.**", "**Scope boundaries.**"):
                self.assertIn(label, chapter(n))
            self.assertIsNone(re.search(r"@src-\d+", text), msg=f"chapter {n}: no citations before drafting")
            self.assertIsNone(re.search(r"figures/rendered|\.svg|\$\$", text), msg=f"chapter {n}: no figures or equations")
            self.assertIsNone(re.search(r"^\d+\. \*\*|^\*\*\d+\.\*\*", text, re.MULTILINE), msg=f"chapter {n}: no questions/answers")
            self.assertIsNone(re.search(r"(?i)\bTODO\b|\bTBD\b|\bFIXME\b|lorem ipsum|\bplaceholder\b", text))


class TestRecords(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = safe_load_path(os.path.join(REPO_ROOT, "config", "chapter-status-registry.yaml"))
        cls.sources = {s["id"] for s in safe_load_path(os.path.join(REPO_ROOT, "sources", "registry.yaml"))["sources"]}

    def test_status_registry_and_contracts_agree_at_scaffold_only(self):
        entry = self.reg["workbooks"][WB_ID]
        self.assertEqual(entry["status"], "scaffold_only")
        self.assertEqual(sorted(str(k).zfill(2) for k in entry["chapters"]), [f"{n:02d}" for n in range(1, 8)])
        for n in range(1, 8):
            ch = entry["chapters"][f"{n:02d}"] if f"{n:02d}" in entry["chapters"] else entry["chapters"][n]
            self.assertEqual(ch["status"], "scaffold_only")
            self.assertEqual(ch["chapter_path"], f"workbooks/{WB_ID}/chapters/{SLUGS[n - 1]}.qmd")
            contract = safe_load_path(os.path.join(WB, "chapter-contracts", f"ch{n:02d}.yaml"))
            self.assertEqual(contract["identity"]["status"], "scaffold_only")
            self.assertEqual(contract["content"]["question_count"], 5)
            self.assertFalse(contract["scope"]["canonical_output_allowed"])
            self.assertFalse(contract["scope"]["push_allowed"])
            self.assertEqual(set(contract["acceptance"].values()), {"not_yet_run"})
            for frozen in ("workbooks/04-llm-architecture/**", "workbooks/05-llm-training/**", "workbooks/addendum-04-05-tsfm/**"):
                self.assertIn(frozen, contract["scope"]["frozen_paths"])

    def test_planned_sources_are_registered_and_kept_apart_from_claims(self):
        ledger = safe_load_path(os.path.join(WB, "claim-ledger.yaml"))
        self.assertEqual(ledger["entries"], [])  # no claim exists before drafting
        planned = {p["chapter"]: p["source_ids"] for p in ledger["planned_chapter_sources"]}
        for n in range(1, 8):
            contract = safe_load_path(os.path.join(WB, "chapter-contracts", f"ch{n:02d}.yaml"))
            ids = contract["sources"]["required_source_ids"]
            self.assertEqual(ids, planned[f"ch{n}"])
            self.assertEqual(set(ids) - self.sources, set())
        self.assertEqual(safe_load_path(os.path.join(WB, "questions.yaml"))["questions"], [])

    def test_figure_plan_and_page_budget(self):
        figs = safe_load_path(os.path.join(WB, "figure-plan.yaml"))["figures"]
        self.assertTrue(figs)
        self.assertEqual({f["status"] for f in figs}, {"planned"})
        self.assertTrue(all(f["must_be_redrawn"] is True for f in figs))
        self.assertEqual({f["chapter"] for f in figs}, {f"ch{n}" for n in range(1, 8)})
        self.assertEqual(os.listdir(os.path.join(WB, "figures", "source")), [".gitkeep"])
        self.assertEqual(os.listdir(os.path.join(WB, "figures", "rendered")), [".gitkeep"])
        budget = safe_load_path(os.path.join(WB, "page-budget.yaml"))
        self.assertEqual((budget["target_pages"], budget["hard_ceiling_pages"]), (72, 78))

    def test_publication_record_is_in_development_and_readme_agrees(self):
        pub = self.reg["publications"]["workbook-06"]
        self.assertEqual(pub["status"], "drafting")
        self.assertEqual(pub["canonical_path"], "outputs/06-llm-inference-workbook.pdf")
        self.assertEqual(pub["development_dir"], "outputs/_development/06-llm-inference/")
        self.assertEqual(pub["release_candidate_dir"], "outputs/_releases/06-llm-inference/")
        self.assertNotIn("publication_date", pub)
        row = [l for l in read(os.path.join(REPO_ROOT, "README.md")).splitlines() if l.startswith("| `workbook-06` |")]
        self.assertEqual(len(row), 1)
        self.assertIn("| Drafting |", row[0])
        self.assertNotIn("releases/download", row[0])
        project = safe_load_path(os.path.join(REPO_ROOT, "config", "project.yaml"))
        self.assertEqual([w for w in project["workbooks"] if w["id"] == WB_ID][0]["status"], "scaffold_only")


class TestBuildRouting(unittest.TestCase):
    def test_development_builds_never_target_the_canonical_pdf(self):
        qa = load_workbook_qa()
        cfg = qa.WORKBOOK_REGISTRY[WB_ID]
        self.assertTrue(qa.is_development(cfg))
        self.assertEqual(cfg["canonical_pdf"], "06-llm-inference-workbook.pdf")
        self.assertNotEqual(cfg["development_pdf"], cfg["canonical_pdf"])
        out = qa.development_build_dir(WB_ID)
        self.assertTrue(out.startswith(os.path.join(REPO_ROOT, "outputs", "_development", WB_ID)))
        self.assertEqual(cfg["test_pattern"], "test_workbook06_*.py")
        for other in ("04-llm-architecture", "05-llm-training", "addendum-04-05-tsfm"):
            self.assertFalse(qa.is_development(qa.WORKBOOK_REGISTRY[other]))  # unchanged behaviour

    def test_canonical_pdf_is_absent_and_nothing_is_tracked(self):
        self.assertFalse(os.path.exists(CANONICAL))
        import subprocess
        tracked = subprocess.run(["git", "ls-files", "outputs", f"workbooks/{WB_ID}"], cwd=REPO_ROOT,
                                 capture_output=True, text=True).stdout.split()
        self.assertEqual([p for p in tracked if p.endswith((".pdf", ".png"))], [])


if __name__ == "__main__":
    unittest.main()
