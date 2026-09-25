"""Regression tests for the RC2 whole-book editorial/visual-production
pass: the notation-table overflow, the Chapter 4 orphan page, the
Chapter 4 title line-break, and the document-numbering scheme (chapter
headings numbered 1-8, front matter/answer-keys/build-note unnumbered,
no stale "Section N" cross-references to unnumbered headings).

Most checks here operate on the qmd SOURCE files (fast, offline, no
Quarto/Typst render required). A few checks that can only be verified
against the actual rendered PDF text are marked skippable when that
PDF hasn't been built in the current environment.
"""
import os
import re
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WB04 = os.path.join(REPO_ROOT, "workbooks", "04-llm-architecture")
CHAPTERS_DIR = os.path.join(WB04, "chapters")
SOLUTIONS_DIR = os.path.join(WB04, "solutions")
INDEX_QMD = os.path.join(WB04, "index.qmd")
NOTATION_QMD = os.path.join(WB04, "includes", "notation-summary.qmd")
DRAFT_SCOPE_QMD = os.path.join(WB04, "includes", "draft-scope-note.qmd")
BUILD_NOTE_GENERATOR = os.path.join(REPO_ROOT, "scripts", "generate_build_note.py")
RC2_PDF = os.path.join(REPO_ROOT, "outputs", "04-modern-llm-architecture-workbook-rc2.pdf")

CHAPTER_FILES = sorted(f for f in os.listdir(CHAPTERS_DIR) if f.endswith(".qmd"))
SOLUTION_FILES = sorted(f for f in os.listdir(SOLUTIONS_DIR) if f.endswith(".qmd"))


class TestDocumentHierarchyNumbering(unittest.TestCase):
    """Stage 3: chapters unambiguously numbered 1-8; front matter,
    answer keys, and the build note are unnumbered."""

    def test_eight_chapter_files_present(self):
        self.assertEqual(len(CHAPTER_FILES), 8, msg=f"expected 8 chapter files, found {CHAPTER_FILES}")

    def test_eight_solution_files_present(self):
        self.assertEqual(len(SOLUTION_FILES), 8, msg=f"expected 8 solution files, found {SOLUTION_FILES}")

    def test_each_chapter_heading_matches_its_file_number(self):
        for i, fname in enumerate(CHAPTER_FILES, start=1):
            with open(os.path.join(CHAPTERS_DIR, fname)) as f:
                first_line = f.readline()
            self.assertIn(f"#sec-ch{i}", first_line, msg=f"{fname}'s heading is missing its #sec-ch{i} anchor")
            # RC3: the heading text itself must NOT repeat "Chapter N:" --
            # Typst's auto-numbering already prepends the leading numeral,
            # so a literal "Chapter N:" in the title text would render as
            # a duplicated "N Chapter N: ..." (the RC3 acceptance finding).
            self.assertNotIn(f"Chapter {i}:", first_line, msg=f"{fname}'s heading still repeats 'Chapter {i}:' -- would double-render the number")
            # Chapter headings themselves must NOT be marked unnumbered --
            # they are exactly the headings Typst should number 1-8.
            self.assertNotIn(".unnumbered", first_line, msg=f"{fname}'s chapter heading must stay numbered")

    def test_each_answer_key_heading_is_unnumbered(self):
        for i, fname in enumerate(SOLUTION_FILES, start=1):
            with open(os.path.join(SOLUTIONS_DIR, fname)) as f:
                first_line = f.readline()
            self.assertIn(f"Answer Key: Chapter {i}", first_line)
            self.assertIn(".unnumbered", first_line, msg=f"{fname}'s Answer Key heading must be unnumbered")

    def test_how_to_use_heading_is_unnumbered(self):
        with open(INDEX_QMD) as f:
            text = f.read()
        m = re.search(r"^## How to use this workbook.*$", text, re.MULTILINE)
        self.assertIsNotNone(m, msg="'How to use this workbook' heading not found")
        self.assertIn(".unnumbered", m.group(0))

    def test_notation_heading_is_unnumbered(self):
        with open(NOTATION_QMD) as f:
            first_line = f.readline()
        self.assertIn("#sec-notation", first_line)
        self.assertIn(".unnumbered", first_line)

    def test_build_note_generator_emits_unnumbered_headings(self):
        """The build/version note is generated, not hand-edited (Stage
        5) -- so this regression check targets the GENERATOR script,
        which is the only place that can legitimately be fixed."""
        with open(BUILD_NOTE_GENERATOR) as f:
            text = f.read()
        # The generator is an f-string, so literal braces are escaped
        # as {{ }} in the .py source -- check for that escaped form.
        self.assertIn("## Build and Version Note {{.unnumbered}}", text)
        self.assertIn("### Provenance {{.unnumbered}}", text)

    def test_no_numbered_crossref_to_answer_keys_in_chapters(self):
        """Chapters must not reference the answer key via the
        auto-numbered @sec-solutions-chN crossref syntax (which would
        render as a stale 'Section N') -- they must use a literal-text
        link instead."""
        pattern = re.compile(r"\(@sec-solutions-ch\d+\)")
        for fname in CHAPTER_FILES:
            path = os.path.join(CHAPTERS_DIR, fname)
            with open(path) as f:
                text = f.read()
            self.assertFalse(pattern.search(text), msg=f"{fname} still uses a numbered crossref to the answer key")
            self.assertIn("#sec-solutions-ch", text, msg=f"{fname} lost its answer-key link entirely")

    def test_no_numbered_crossref_to_notation_in_index(self):
        with open(INDEX_QMD) as f:
            text = f.read()
        self.assertNotIn("(@sec-notation)", text)
        self.assertIn("#sec-notation", text, msg="index.qmd lost its notation-reference link entirely")

    def test_answer_key_link_text_is_literal_not_numbered(self):
        """Each chapter's 'Full solutions are in ...' sentence must
        name the answer key by chapter number in literal text, not via
        an auto-numbered section reference."""
        for i, fname in enumerate(CHAPTER_FILES, start=1):
            path = os.path.join(CHAPTERS_DIR, fname)
            with open(path) as f:
                text = f.read()
            self.assertIn(f"[Answer Key: Chapter {i}](#sec-solutions-ch{i})", text)


class TestNotationTableStructure(unittest.TestCase):
    """Stage 2A: the notation table overflow regression check. The
    original bug was one 18-row pipe table overflowing/overlapping on
    a single page; the fix splits it into multiple shorter tables. This
    test bounds each table's row count well below the size that broke,
    and confirms no single-table regression."""

    MAX_SAFE_ROWS_PER_TABLE = 10  # empirically verified safe (8 rows rendered cleanly); the original 18-row table did not.

    def _parse_tables(self, text):
        """Return a list of row-counts, one per pipe-table block."""
        tables = []
        current_rows = 0
        in_table = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                if re.match(r"^\|[\s:|-]+\|$", stripped):
                    continue  # the |---|---|---| separator row
                if not in_table:
                    in_table = True
                    current_rows = 0
                current_rows += 1
            else:
                if in_table:
                    tables.append(current_rows - 1)  # subtract the header row
                    in_table = False
        if in_table:
            tables.append(current_rows - 1)
        return tables

    def test_notation_symbols_split_across_multiple_safe_sized_tables(self):
        with open(NOTATION_QMD) as f:
            text = f.read()
        tables = self._parse_tables(text)
        self.assertGreaterEqual(len(tables), 2, msg="notation table must be split into multiple tables, not one long table")
        for i, row_count in enumerate(tables, start=1):
            self.assertLessEqual(
                row_count, self.MAX_SAFE_ROWS_PER_TABLE,
                msg=f"notation table part {i} has {row_count} rows, exceeding the empirically-safe {self.MAX_SAFE_ROWS_PER_TABLE}",
            )

    def test_all_notation_symbols_still_present(self):
        """No symbol may be dropped while fixing the layout. RC3 replaced
        the unused KV_bytes entry with M_KV/M_MLA (the symbols the
        equations actually use) and added the sliding-window width W."""
        with open(NOTATION_QMD) as f:
            text = f.read()
        expected_symbols = [
            "$B$", "$S$", "$T_q$", "$V$", "$d_{\\text{model}}$", "$H_q$", "$H_{kv}$", "$d_{\\text{head}}$",
            "$L$", "$d_{\\text{ff}}$", "bytes\\_per\\_elem", "$d_c$", "$d_{\\text{rope}}$",
            "$M_{KV}$", "$M_{\\text{MLA}}$", "$W$", "$E$", "$k$",
            "$p_e$", "$p_s$", "$p_{\\text{base}}$", "$P_{\\text{total}}$", "$P_{\\text{active}}$",
            "$L_{\\text{distinct}}$", "$T_{\\text{passes}}$", "$L_{\\text{effective}}$",
        ]
        for sym in expected_symbols:
            self.assertIn(sym, text, msg=f"notation symbol {sym!r} missing from notation-summary.qmd")

    def test_kv_bytes_symbol_fully_retired(self):
        """RC3 fix: KV_bytes was defined but never used by any equation
        or prose in Chapters 1-8 -- it must not reappear anywhere in the
        notation reference now that M_KV/M_MLA replace it."""
        with open(NOTATION_QMD) as f:
            text = f.read()
        self.assertNotIn("KV\\_bytes", text)
        self.assertNotIn("KV_bytes", text)

    def test_notation_tables_have_repeated_column_headers(self):
        with open(NOTATION_QMD) as f:
            text = f.read()
        header_count = text.count("| Symbol | Name | Meaning |")
        self.assertGreaterEqual(header_count, 2, msg="each notation table part must repeat the column header")


class TestChapter4OrphanAndTitleFixes(unittest.TestCase):
    """Stage 2B/2C regression checks."""

    CH4_PATH = os.path.join(CHAPTERS_DIR, "04-reducing-attention-cost.qmd")

    def test_chapter4_title_has_no_stale_chapter_prefix(self):
        """RC3 removed the 'Chapter 4: ' prefix from the heading text
        (Typst's auto-numbering supplies the leading '4' instead), which
        avoided RC2's "La-tent" break -- but RC3's own render still
        hyphenated "Representations" as "Rep-/resentations" at the
        line wrap, a defect not caught at the time. RC4 reintroduced an
        explicit #linebreak() after "Sparsity," to fix it -- see
        tests/test_release_candidate_rc4.py for that regression
        coverage."""
        with open(self.CH4_PATH) as f:
            first_line = f.readline()
        self.assertNotIn("Chapter 4:", first_line)
        self.assertIn("Latent KV Representations", first_line)

    def test_chapter4_sources_paragraph_is_reasonably_short(self):
        """A crude proxy for 'fits on the same page as the recap':
        the Sources paragraph must stay under a word budget. This does
        not replace visual inspection, but catches an obvious future
        regression (someone re-lengthening the paragraph back past the
        point that caused the orphan page)."""
        with open(self.CH4_PATH) as f:
            text = f.read()
        m = re.search(r"### Sources and further reading\s*\n+(.+)", text, re.DOTALL)
        self.assertIsNotNone(m, msg="Chapter 4's Sources section not found")
        word_count = len(m.group(1).split())
        self.assertLessEqual(word_count, 45, msg=f"Chapter 4's Sources paragraph has grown to {word_count} words -- re-check for the page-37 orphan-page regression")


class TestReleaseStatusLanguage(unittest.TestCase):
    """Stage 5: the draft-scope note and title must describe RC2's
    actual status, not silently carry over RC1's 'not yet happened'
    language once the editorial pass is complete."""

    def test_index_subtitle_says_release_candidate_4(self):
        with open(INDEX_QMD) as f:
            text = f.read()
        self.assertIn("Release Candidate 4", text)
        self.assertNotIn("Release Candidate 1", text)
        self.assertNotIn("Release Candidate 2", text)
        self.assertNotIn("Release Candidate 3", text)

    def test_draft_scope_note_does_not_claim_qa_not_yet_happened(self):
        with open(DRAFT_SCOPE_QMD) as f:
            text = f.read()
        self.assertNotIn("has NOT yet happened", text)
        self.assertNotIn("has not yet happened", text.lower())

    def test_build_note_generator_does_not_overclaim_clean_state(self):
        with open(BUILD_NOTE_GENERATOR) as f:
            text = f.read()
        # RC3: the commit SHA moved out of the learner-facing template
        # entirely (a PDF can't name the commit that includes its own
        # build); git_commit_or_precommit's honest dirty-tree wording
        # must still exist in the SOURCE, just no longer embedded in
        # `content`.
        self.assertIn("this build was rendered with additional, not-yet-committed changes", text)
        # The maintainer-facing docstring may still say "do not hand-edit"
        # (that instruction is for whoever edits this script); the
        # LEARNER-FACING generated template (the f-string literal
        # assigned to `content`) must not repeat it, per Stage 5, and
        # per RC3 must not contain a raw commit SHA reference either.
        template_start = text.index('content = f"""')
        template_text = text[template_start:]
        self.assertNotIn("hand-edit", template_text)
        self.assertNotIn("scripts/generate_build_note.py", template_text)
        self.assertNotIn("commit", template_text.lower())


@unittest.skipUnless(os.path.exists(RC2_PDF), "RC2 PDF not built in this environment -- run scripts/build_release_candidate_v2.py first")
class TestRenderedPdfNumberingPatterns(unittest.TestCase):
    """Stage 8: search the actual rendered PDF text for the exact
    stale-numbering patterns this task was created to eliminate."""

    @classmethod
    def setUpClass(cls):
        import subprocess
        result = subprocess.run(["pdftotext", RC2_PDF, "-"], capture_output=True, text=True)
        cls.text = result.stdout

    def test_no_mismatched_chapter_number_prefixes(self):
        for bad_pattern in [r"\b3 Chapter 1\b", r"\b10 Chapter 8\b", r"\b6 Chapter 4\b", r"\b7 Chapter 5\b"]:
            self.assertIsNone(re.search(bad_pattern, self.text), msg=f"found stale numbering pattern {bad_pattern!r}")

    def test_no_stale_section_references_11_through_18(self):
        for n in range(11, 19):
            self.assertNotIn(f"Section {n}", self.text, msg=f"found stale 'Section {n}' reference (should be an Answer Key reference)")

    def test_chapter_headings_numbered_1_through_8(self):
        for i in range(1, 9):
            self.assertIn(f"{i} Chapter {i}:", self.text, msg=f"Chapter {i}'s heading is not numbered {i}")


if __name__ == "__main__":
    unittest.main()
