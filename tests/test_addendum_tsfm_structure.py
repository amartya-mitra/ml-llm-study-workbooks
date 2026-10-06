"""Scoped structural, source, claim-ledger, question, leakage, cross-reference
and publication-safety tests for the TSFM addendum (status: drafted pending
human review). Nothing here builds a PDF.
"""
import hashlib
import os
import re
import subprocess
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from _yaml_lite import safe_load_path  # noqa: E402
import chapter_review_checks as crc  # noqa: E402

WB_ID = "addendum-04-05-tsfm"
ADD = os.path.join(REPO_ROOT, "workbooks", WB_ID)
MODULES = {
    "01": "01-model-inputs",
    "02": "02-context-channels-covariates-horizons",
    "03": "03-architecture-families-and-horizon-filling",
    "04": "04-outputs-and-losses",
    "05": "05-pretraining-data-adaptation-and-leakage",
    "06": "06-reading-a-tsfm-release",
}
QUESTION_COUNTS = {"01": 6, "02": 6, "03": 6, "04": 6, "05": 6, "06": 4}
CITE_RE = re.compile(r"@src-\d+")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def chapter(n):
    return read(os.path.join(ADD, "chapters", MODULES[n] + ".qmd"))


def solutions(n):
    return read(os.path.join(ADD, "solutions", MODULES[n] + "-solutions.qmd"))


def learner_text(text):
    """Strip citation keys, which render as author-year citations."""
    return CITE_RE.sub("", text)


class TestScaffold(unittest.TestCase):
    def test_required_files_and_directories_exist(self):
        for rel in ["index.qmd", "includes/front-matter.qmd", "questions.yaml", "claim-ledger.yaml",
                    "figure-plan.yaml", "page-budget.yaml", "data/synthesis-map.yaml"]:
            self.assertTrue(os.path.exists(os.path.join(ADD, rel)), msg=rel)
        for rel in ["chapters", "solutions", "includes", "data/worked-examples", "figures/source", "figures/rendered", "chapter-contracts"]:
            self.assertTrue(os.path.isdir(os.path.join(ADD, rel)), msg=rel)
        for n, slug in MODULES.items():
            self.assertTrue(os.path.exists(os.path.join(ADD, "chapters", slug + ".qmd")))
            self.assertTrue(os.path.exists(os.path.join(ADD, "solutions", slug + "-solutions.qmd")))
            self.assertTrue(os.path.exists(os.path.join(ADD, "chapter-contracts", f"ch{n}.yaml")))

    def test_index_includes_all_six_modules_in_order(self):
        idx = read(os.path.join(ADD, "index.qmd"))
        positions = [idx.index(f"chapters/{slug}.qmd") for slug in MODULES.values()]
        self.assertEqual(positions, sorted(positions))
        sol_positions = [idx.index(f"solutions/{slug}-solutions.qmd") for slug in MODULES.values()]
        self.assertEqual(sol_positions, sorted(sol_positions))
        self.assertLess(positions[-1], sol_positions[0])

    def test_no_generated_files_in_source_directories(self):
        for root, _dirs, files in os.walk(ADD):
            for fn in files:
                self.assertFalse(fn.endswith((".pdf", ".png")), msg=os.path.join(root, fn))
        self.assertFalse(os.path.exists(os.path.join(ADD, "index.pdf")))

    def test_no_canonical_release_or_rc_artifacts_exist(self):
        out = os.path.join(REPO_ROOT, "outputs")
        self.assertFalse(os.path.exists(os.path.join(out, "addendum-04-05-tsfm.pdf")))
        # Release Candidate 1 is the only permitted release-area artifact
        rel = os.path.join(out, "_releases", WB_ID)
        if os.path.isdir(rel):
            names = [n for n in os.listdir(rel) if ".prev-" not in n]
            self.assertEqual(names, [f"{WB_ID}-rc1.pdf"])

    def test_exactly_six_modules_and_no_depth_diagnostics_module(self):
        files = sorted(os.listdir(os.path.join(ADD, "chapters")))
        self.assertEqual(len(files), 6)
        for fn in files:
            self.assertNotIn("diagnostic", fn)
            self.assertNotIn("depth", fn)
        full = " ".join(chapter(n) for n in MODULES)
        self.assertNotIn("Moirai-MoE", full)
        self.assertNotIn("MoE", full.replace("mixture-of-experts", ""))

    def test_every_module_starts_with_quick_recap_and_labels_the_analogue(self):
        for n in MODULES:
            text = chapter(n)
            first_h3 = re.search(r"^### (.+)$", text, re.MULTILINE).group(1)
            self.assertEqual(first_h3, "Quick recap from LLMs", msg=n)
            recap = text.split("### Quick recap from LLMs")[1].split("\n### ")[0]
            self.assertIn("**Same idea:**", recap, msg=n)
            self.assertIn("**Adapted idea:**", recap, msg=n)
            self.assertIn("**Time-series-specific idea:**", recap, msg=n)
            words = len(re.findall(r"\w+", recap))
            self.assertGreater(words, 120, msg=f"module {n} recap too thin to stand alone ({words} words)")
            self.assertLess(words, 420, msg=f"module {n} recap over budget ({words} words)")

    def test_markdown_lists_are_preceded_by_a_blank_line(self):
        # A list glued to the previous paragraph renders inline ("- Same idea")
        # in the PDF; this pins the defect found during page inspection.
        for n in MODULES:
            lines = chapter(n).splitlines() + solutions(n).splitlines()
            for i, line in enumerate(lines):
                if re.match(r"^(- |\d+\. )", line) and i > 0:
                    prev = lines[i - 1]
                    is_item = re.match(r"^(- |\d+\. |\s+)", prev) is not None
                    self.assertTrue(prev == "" or is_item, msg=f"module {n}, line {i + 1}: list not preceded by blank line")

    def test_module_three_marks_new_families_as_not_in_the_llm_workbooks(self):
        self.assertIn("Not in the LLM workbooks", chapter("03"))

    def test_frozen_workbooks_report_no_working_tree_changes(self):
        r = subprocess.run(["git", "status", "--porcelain", "workbooks/04-llm-architecture", "workbooks/05-llm-training"],
                           cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "")

    def test_published_workbook_pdfs_match_the_registry_checksums(self):
        reg = safe_load_path(os.path.join(REPO_ROOT, "config", "chapter-status-registry.yaml"))
        for key in ("workbook-04", "workbook-05"):
            rec = reg["publications"][key]
            path = os.path.join(REPO_ROOT, rec["canonical_path"])
            if not os.path.exists(path):
                self.skipTest("canonical PDF absent on this clone")
            h = hashlib.sha256()
            with open(path, "rb") as f:
                h.update(f.read())
            self.assertEqual(h.hexdigest(), rec["sha256"])
            self.assertEqual(rec["status"], "published")


class TestRegistration(unittest.TestCase):
    def test_project_registry_and_status_registry_agree(self):
        project = safe_load_path(os.path.join(REPO_ROOT, "config", "project.yaml"))
        self.assertIn(WB_ID, [w["id"] for w in project["workbooks"]])
        reg = safe_load_path(os.path.join(REPO_ROOT, "config", "chapter-status-registry.yaml"))
        entry = reg["workbooks"][WB_ID]
        self.assertEqual(entry["status"], "accepted_frozen")
        self.assertEqual(entry["acceptance_date"], "2026-10-06")
        self.assertEqual(entry["accepted_source_commit"], "aea2e38673556a8701c68fdb0fecddaab1a91d02")
        self.assertEqual(entry["accepted_review_pdf_sha256"], "d2fcd1cff746cbeeb154de0143d4996c6238f6fe715748ef713d8c589c4e3319")
        self.assertEqual(entry["accepted_review_pdf_page_count"], 18)
        self.assertEqual(sorted(str(k).zfill(2) for k in entry["chapters"]), sorted(MODULES))
        for ch in entry["chapters"].values():
            self.assertEqual(ch["status"], "accepted_frozen")
        self.assertNotEqual(reg["publications"][WB_ID]["status"], "published")
        self.assertEqual(reg["publications"]["workbook-04"]["status"], "published")
        self.assertEqual(reg["publications"]["workbook-05"]["status"], "published")

    def test_registered_sources_are_complete_and_documentation_is_labeled(self):
        registry = safe_load_path(os.path.join(REPO_ROOT, "sources", "registry.yaml"))
        by_id = {s["id"]: s for s in registry["sources"]}
        for i in range(56, 69):
            s = by_id[f"src-{i}"]
            self.assertEqual(s["workbook_categories"], [WB_ID])
            self.assertEqual(s["last_verified"], "2026-10-06")
        for i in range(65, 69):
            self.assertEqual(by_id[f"src-{i}"]["authority_type"], "implementation_guide")
            self.assertIn("documentation", by_id[f"src-{i}"]["topic_tags"][1])
        for i in range(56, 65):
            self.assertEqual(by_id[f"src-{i}"]["authority_type"], "primary_technical")
        self.assertNotIn("2410.10469", " ".join(s["url"] for s in registry["sources"]))

    def test_bibliography_keys_cover_every_citation_in_the_addendum(self):
        bib = read(os.path.join(REPO_ROOT, "shared", "bibliography.bib"))
        keys = set(re.findall(r"@\w+\{([^,]+),", bib))
        texts = [read(os.path.join(ADD, "index.qmd")), read(os.path.join(ADD, "includes", "front-matter.qmd"))]
        texts += [chapter(n) for n in MODULES] + [solutions(n) for n in MODULES]
        for t in texts:
            for cite in re.findall(r"@(src-\d+)", t):
                self.assertIn(cite, keys, msg=cite)


class TestSourcesAndClaimLedger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = safe_load_path(os.path.join(ADD, "claim-ledger.yaml"))
        reg = safe_load_path(os.path.join(REPO_ROOT, "sources", "registry.yaml"))
        cls.known = {s["id"] for s in reg["sources"]}
        cls.entries = cls.ledger["entries"]

    def test_schema_fields_ids_and_source_ids(self):
        schema = safe_load_path(os.path.join(REPO_ROOT, "shared", "claim-ledger-schema.yaml"))
        fields = {f["name"]: f for f in schema["fields"]}
        seen = set()
        for e in self.entries:
            for name, f in fields.items():
                if f.get("required"):
                    self.assertIn(name, e, msg=e.get("id"))
            self.assertRegex(e["id"], fields["id"]["pattern"])
            self.assertNotIn(e["id"], seen)
            seen.add(e["id"])
            self.assertEqual(e["workbook"], WB_ID)
            self.assertIn(e["verification_status"], fields["verification_status"]["allowed_values"])
            for sid in e["source_ids"] or []:
                self.assertIn(sid, self.known, msg=e["id"])
            self.assertTrue(e["note"], msg=e["id"] + " lacks a note (kind, generation, time-sensitivity)")

    def test_every_module_has_ledger_entries_with_its_prefix(self):
        for n, slug in MODULES.items():
            tag = f"ch{int(n)}"
            mine = [e for e in self.entries if e["chapter"] == tag]
            self.assertGreaterEqual(len(mine), 5, msg=tag)
            contract = safe_load_path(os.path.join(ADD, "chapter-contracts", f"ch{n}.yaml"))
            prefix = contract["claims"]["required_claim_prefix"]
            for e in mine:
                self.assertTrue(e["id"].startswith(prefix), msg=e["id"])

    def test_every_source_cited_in_a_module_has_a_ledger_entry_for_that_module(self):
        for n in MODULES:
            cited = set(re.findall(r"@(src-\d+)", chapter(n)))
            tag = f"ch{int(n)}"
            ledgered = set()
            for e in self.entries:
                if e["chapter"] == tag:
                    ledgered.update(e["source_ids"] or [])
            self.assertEqual(cited - ledgered, set(), msg=f"module {n}: cited but not in ledger")

    def test_contract_required_sources_cover_prose_citations(self):
        for n in MODULES:
            cited = set(re.findall(r"@(src-\d+)", chapter(n) + solutions(n)))
            contract = safe_load_path(os.path.join(ADD, "chapter-contracts", f"ch{n}.yaml"))
            self.assertEqual(cited - set(contract["sources"]["required_source_ids"]), set(), msg=n)

    def test_documentation_sources_never_back_a_paper_claim(self):
        doc = {"src-65", "src-66", "src-67", "src-68"}
        for e in self.entries:
            if set(e["source_ids"] or []) & doc:
                self.assertRegex(e["note"], r"(?i)documentation|vendor|search-based|restates|source-type|restated|name collision|source disagreement|table|classification|unresolved",
                                 msg=e["id"] + ": documentation-sourced claim must say so")

    def test_unverified_items_are_not_presented_as_verified_values(self):
        text = " ".join(chapter(n) for n in MODULES)
        self.assertIsNone(re.search(r"PatchTST[^.]{0,80}(336|L ?= ?512)", text))
        self.assertIn("the ablation statements behind these were not verified", chapter("05"))
        # the Moirai cap is now verified: stated, attributed to the original Moirai only, with its form
        ch5 = chapter("05")
        self.assertNotIn("could not be verified, so none", ch5)
        self.assertIn("\\epsilon=0.001", ch5)
        self.assertIn("\\omega_j=\\min", ch5)
        self.assertIn("[@src-61]", ch5.split("\\epsilon=0.001")[1].split("\n")[0])
        self.assertNotIn("0.001", " ".join(chapter(n) for n in MODULES if n != "05"))

    def test_moirai_cap_ledger_entry_cites_the_existing_source_only(self):
        entry = [e for e in self.entries if e["id"] == "claim-tsfm-data-014"][0]
        self.assertEqual(entry["source_ids"], ["src-61"])
        self.assertIn("0.001", entry["statement"])
        self.assertEqual(entry["verification_status"], "verified_full_text")
        self.assertNotIn("garbled", " ".join(e["statement"] for e in self.entries))
        # no new source was registered for it
        self.assertIn("src-61", self.known)
        self.assertNotIn("src-69", self.known)

    def test_scoped_reading_boundaries_hold(self):
        full = " ".join(chapter(n) for n in MODULES)
        self.assertNotIn("Chronos-2 patch length", full)
        self.assertNotIn("1.1", " ".join(re.findall(r"TiRex[^.]*", full)))


class TestQuestionsAndAnswers(unittest.TestCase):
    def test_validator_passes(self):
        r = subprocess.run([sys.executable, os.path.join(REPO_ROOT, "scripts", "validate_questions.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, msg=r.stdout)

    def test_counts_agree_between_chapter_answers_records_and_contract(self):
        qs = safe_load_path(os.path.join(ADD, "questions.yaml"))["questions"]
        self.assertEqual(len(qs), 34)
        for n, slug in MODULES.items():
            expected = QUESTION_COUNTS[n]
            check = chapter(n).split("### Check your understanding")[1]
            self.assertEqual(len(re.findall(r"^\d+\. \*\*", check, re.MULTILINE)), expected, msg=n)
            self.assertEqual(len(re.findall(r"^\*\*\d+\.\*\*", solutions(n), re.MULTILINE)), expected, msg=n)
            records = [q for q in qs if q["chapter"] == slug[3:]]
            self.assertEqual(len(records), expected, msg=n)
            contract = safe_load_path(os.path.join(ADD, "chapter-contracts", f"ch{n}.yaml"))
            self.assertEqual(contract["content"]["question_count"], expected)
            self.assertEqual(contract["content"]["answer_count"], expected)

    def test_every_module_has_a_calculation_or_diagnosis_and_an_interview_question(self):
        qs = safe_load_path(os.path.join(ADD, "questions.yaml"))["questions"]
        for n, slug in MODULES.items():
            mine = [q for q in qs if q["chapter"] == slug[3:]]
            self.assertTrue(any(q["prompt"].startswith("Interview-style") for q in mine), msg=n)

    def test_answer_key_cross_references_point_at_the_check_section(self):
        for n, slug in MODULES.items():
            cpath = os.path.join(ADD, "chapters", slug + ".qmd")
            spath = os.path.join(ADD, "solutions", slug + "-solutions.qmd")
            res = crc.check_answer_key_cross_reference(cpath, spath)
            self.assertTrue(res["ok"], msg=f"{n}: {res}")
            self.assertEqual(res["check_your_understanding_anchor"], f"sec-ch{int(n)}-check")

    def test_calculation_answers_match_the_scripts(self):
        # independent recomputation of the numeric answers
        self.assertEqual((20 - 5) // 2 + 2, 9)
        self.assertEqual(20 // 5, 4)
        self.assertEqual(3 * 10 * 9, 270)
        self.assertEqual(3 * 10 * 500, 15000)
        self.assertEqual((5 * 8) ** 2 // (5 * 8 ** 2), 5)
        self.assertEqual((5 * 8 ** 2, (5 * 8) ** 2), (320, 1600))
        self.assertEqual(-(-96 // 32), 3)
        self.assertEqual(-(-100 // 32), 4)
        self.assertEqual(4 * 32 - 100, 28)
        self.assertAlmostEqual(0.9 * 4, 3.6)
        self.assertAlmostEqual(0.1 * 4, 0.4)
        self.assertAlmostEqual(0.5 * 4, 2.0)
        prop = [6 / 10, 3 / 10, 1 / 10]
        omega = [min(p, 0.4) for p in prop]
        self.assertEqual([round(w / sum(omega), 6) for w in omega], [0.5, 0.375, 0.125])
        a = solutions("01") + solutions("02") + solutions("03") + solutions("04") + solutions("05")
        for needle in ["$N_p=\\lfloor(20-5)/2\\rfloor+2=7+2=9$", "$3\\times10\\times9=270$", "$(5\\times8)^2=40^2=1600$",
                       "$\\lceil96/32\\rceil=3$", "$0.9\\times4=3.6$", "$0.1\\times4=0.4$", "so the shares are 0.5, 0.375 and 0.125"]:
            self.assertIn(needle, a, msg=needle)


class TestLearnerFacingText(unittest.TestCase):
    def test_no_leakage_in_learner_facing_source_text(self):
        parts = {"index": read(os.path.join(ADD, "index.qmd")), "front": read(os.path.join(ADD, "includes", "front-matter.qmd"))}
        for n in MODULES:
            parts["ch" + n] = chapter(n)
            parts["sol" + n] = solutions(n)
        for name, text in parts.items():
            body = learner_text(text)
            if name == "index":
                body = body.split("---", 2)[2]  # skip YAML front matter
                body = re.sub(r"\{\{<[^>]*>\}\}", "", body)  # include directives
                body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
            # "placeholder" is a legitimate technical term here (placeholder
            # inputs for the horizon); the shared checker's case-insensitive
            # PLACEHOLDER pattern would flag it. Exempt only that word; TODO,
            # TBD, FIXME, XXX, lorem ipsum and "[insert" are still caught.
            body = re.sub(r"(?i)\bplaceholders?\b", "stand-in", body)
            res = crc.check_text_leakage(body)
            self.assertTrue(res["ok"], msg=f"{name}: {res}")

    def test_no_revision_history_or_scaffold_language(self):
        for n in MODULES:
            text = chapter(n) + solutions(n)
            self.assertIsNone(re.search(r"(?i)\bearlier (draft|version)|previous version|this revision|scope report|release candidate", text), msg=n)

    def test_time_sensitive_release_facts_carry_an_as_of_qualifier(self):
        self.assertIn("as of October 2026", read(os.path.join(ADD, "includes", "front-matter.qmd")))
        self.assertIn("as of October 2026", chapter("06"))
        self.assertIn("as of October 2026", chapter("05"))

    def test_no_benchmark_ranking_language(self):
        for n in MODULES:
            self.assertIsNone(re.search(r"(?i)state[- ]of[- ]the[- ]art|\btop-ranked\b|outperforms|best model", chapter(n)), msg=n)


class TestSynthesisTable(unittest.TestCase):
    def _chapter_rows(self):
        text = chapter("06")
        lines = [l for l in text.splitlines() if l.startswith("|")]
        start = next(i for i, l in enumerate(lines) if l.startswith("| Model |"))
        rows = []
        for l in lines[start:]:
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            if cells[0] == "Model" or set(cells[0]) <= set(":-"):
                continue  # header and separator rows of either table
            rows.append(cells)
        return rows

    def test_chapter_table_equals_the_data_file_cell_for_cell(self):
        data = safe_load_path(os.path.join(ADD, "data", "synthesis-map.yaml"))
        rows = [r for r in self._chapter_rows() if r[1] != ""]
        self.assertEqual(len(rows), len(data["rows"]))
        self.assertLessEqual(len(rows), 8)
        for cells, rec in zip(rows, data["rows"]):
            name = re.sub(r"\s*\[.*\]$", "", cells[0])
            self.assertEqual(name, rec["model"])
            cited = sorted(re.findall(r"@(src-\d+)", cells[0]))
            self.assertEqual(cited, sorted(rec["source_ids"]))
            self.assertEqual(cells[1:], [rec[c] for c in data["columns"]], msg=rec["model"])

    def test_documentation_rows_state_only_documented_facts(self):
        data = safe_load_path(os.path.join(ADD, "data", "synthesis-map.yaml"))
        doc_ids = {"src-65", "src-66", "src-67", "src-68"}
        for rec in data["rows"]:
            is_doc = bool(set(rec["source_ids"]) & doc_ids)
            self.assertEqual(is_doc, rec["group"] == "documentation", msg=rec["model"])
            for c in data["columns"]:
                if is_doc:
                    self.assertTrue(rec[c].startswith("doc:") or rec[c] == "not covered here", msg=f"{rec['model']}/{c}")

    def test_documentation_group_is_separated_and_unranked(self):
        text = chapter("06")
        self.assertIn("{#tbl-synthesis}", text)
        self.assertIn("{#tbl-synthesis-docs}", text)
        self.assertLess(text.index("| Lag-Llama"), text.index("{#tbl-synthesis}"))
        self.assertLess(text.index("{#tbl-synthesis}"), text.index("| TimesFM 3.0"))
        self.assertLess(text.index("| TimesFM 3.0"), text.index("{#tbl-synthesis-docs}"))
        self.assertEqual(text.count("Not a ranking"), 2)


class TestTechnicalQualifications(unittest.TestCase):
    """Pins the wording corrections made after independent review."""

    def test_attention_cost_distinguishes_total_work_from_per_token_work(self):
        text = chapter("01")
        self.assertIn("total attention interaction work by about $k^2$", text)
        self.assertIn("attention interaction work per token by about $k$", text)
        self.assertIn("not every component of model FLOPs or wall-clock time", text)
        self.assertNotIn("total work done per token", text)
        ans = solutions("01").split("**6.**")[1]
        self.assertIn("total attention interaction work, shrink about fourfold ($k^2$)", ans)
        self.assertIn("attention interaction work per token about twofold ($k$)", ans)
        self.assertIn("not total FLOPs or wall-clock time", ans)

    def test_forward_pass_statement_is_qualified(self):
        recap = chapter("03").split("### Three ways to fill a horizon")[0]
        self.assertNotIn("at least $N$ forward passes", recap)
        self.assertIn("conventional token-by-token autoregressive decoding", recap)
        self.assertIn("$N$ sequential decoding steps", recap)
        self.assertIn("do not remove the causal dependency across accepted output positions", recap)
        # consistent with Workbook 05: heads discarded by default, speculative reuse is separate
        self.assertIn("separate, optional technique", recap)

    def test_samples_and_quantiles_are_not_called_the_same_distribution(self):
        for n in ("02",):
            text = chapter(n) + solutions(n)
            self.assertNotRegex(text, r"(?i)represent the same distribution|of one distribution")
            self.assertIn("alternative representations of predictive uncertainty", text)
        qs = read(os.path.join(ADD, "questions.yaml"))
        self.assertNotIn("of one distribution", qs)

    def test_status_vocabulary_is_valid_and_consistent(self):
        schema = safe_load_path(os.path.join(REPO_ROOT, "shared", "chapter-contract-schema.yaml"))
        enum = [f for s in schema["sections"] if s["name"] == "identity" for f in s["fields"] if f["name"] == "status"][0]["allowed_values"]
        self.assertIn("accepted_frozen", enum)
        project = safe_load_path(os.path.join(REPO_ROOT, "config", "project.yaml"))
        entry = [w for w in project["workbooks"] if w["id"] == WB_ID][0]
        self.assertEqual(entry["status"], "accepted_frozen")
        reg = safe_load_path(os.path.join(REPO_ROOT, "config", "chapter-status-registry.yaml"))
        self.assertEqual(reg["workbooks"][WB_ID]["status"], "accepted_frozen")
        for n in MODULES:
            contract = safe_load_path(os.path.join(ADD, "chapter-contracts", f"ch{n}.yaml"))
            self.assertIn(contract["identity"]["status"], enum)
            self.assertEqual(contract["identity"]["status"], "accepted_frozen")
            # frozen convention: nothing is allowed to change, and the contract says so
            self.assertEqual(contract["scope"]["allowed_paths"], [])
            self.assertTrue(any("chapters/" + n in p for p in contract["scope"]["frozen_paths"]))
            self.assertEqual(contract["acceptance"]["visual_review"], "pass")
        # the publication lifecycle stays at its valid pre-publication value
        self.assertEqual(reg["publications"][WB_ID]["status"], "review_pending")
        report = read(os.path.join(REPO_ROOT, "reports", "addendum_04_05_tsfm_internal_audit.md"))
        self.assertIn("`drafted_pending_human_review`", report)  # historical record of the draft stage


class TestProjectWideValidators(unittest.TestCase):
    def test_registry_validator(self):
        r = subprocess.run([sys.executable, os.path.join(REPO_ROOT, "scripts", "validate_registry.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)

    def test_contract_validator(self):
        r = subprocess.run([sys.executable, os.path.join(REPO_ROOT, "scripts", "validate_chapter_contract.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)

    def test_publication_hygiene_offline(self):
        r = subprocess.run([sys.executable, os.path.join(REPO_ROOT, "scripts", "validate_publication_hygiene.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
