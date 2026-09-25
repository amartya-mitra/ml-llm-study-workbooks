"""Regression tests for the RC3 acceptance-fix pass: Chapter 1's fresh
page break, the redundant chapter-title numbering ("N Chapter N: ..."),
the notation reference's M_KV/M_MLA/W symbols, and the Build and
Version Note's repository-internal-path sanitization.

Source-level checks run offline against the qmd files. Rendered-PDF
checks are skipped automatically when the RC3 PDF has not been built
in the current environment.
"""
import os
import re
import subprocess
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WB04 = os.path.join(REPO_ROOT, "workbooks", "04-llm-architecture")
CHAPTERS_DIR = os.path.join(WB04, "chapters")
INDEX_QMD = os.path.join(WB04, "index.qmd")
NOTATION_QMD = os.path.join(WB04, "includes", "notation-summary.qmd")
BUILD_NOTE_QMD = os.path.join(WB04, "includes", "build-version-note.qmd")
RC3_PDF = os.path.join(REPO_ROOT, "outputs", "04-modern-llm-architecture-workbook-rc3.pdf")

CHAPTER_FILES = sorted(f for f in os.listdir(CHAPTERS_DIR) if f.endswith(".qmd"))

BANNED_INTERNAL_PATH_PATTERNS = [
    r"\.yaml",
    r"\.qmd",
    r"src-\d",
    r"scripts/",
    r"includes/",
    r"figures/source",
    r"data/worked-examples",
]

DUPLICATED_CHAPTER_NUMBER_PATTERN = r"^\s*[1-8]\s+Chapter\s+[1-8]"


class TestChapter1FreshPageBreak(unittest.TestCase):
    """Acceptance finding 1: Chapter 1 must start on its own page,
    consistent with Chapters 2-8, not share a page with Table 3."""

    def test_index_has_pagebreak_between_notation_and_chapter1(self):
        with open(INDEX_QMD) as f:
            text = f.read()
        m = re.search(
            r"\{\{< include includes/notation-summary\.qmd >\}\}(.*?)\{\{< include chapters/01-transformer-refresher\.qmd >\}\}",
            text, re.DOTALL,
        )
        self.assertIsNotNone(m, msg="could not find the notation-summary -> chapter-1 include span in index.qmd")
        self.assertIn("#pagebreak()", m.group(1), msg="no explicit pagebreak between the notation reference and Chapter 1")

    @unittest.skipUnless(os.path.exists(RC3_PDF), "RC3 PDF not built -- run scripts/build_release_candidate_v3.py first")
    def test_chapter1_starts_on_different_page_than_table3(self):
        result = subprocess.run(["pdftotext", "-layout", RC3_PDF, "-"], capture_output=True, text=True)
        pages = result.stdout.split("\f")
        table3_page = None
        chapter1_page = None
        for i, page in enumerate(pages, start=1):
            if "Table 3:" in page and table3_page is None:
                table3_page = i
            # Anchor on the bare heading line (no trailing dot-leader/page
            # number), so the TOC's "1  Transformer Refresher .... 8"
            # entry is not mistaken for the actual chapter opening.
            if re.search(r"^1\s+Transformer Refresher\s*$", page, re.MULTILINE) and chapter1_page is None:
                chapter1_page = i
        self.assertIsNotNone(table3_page, msg="Table 3 not found in rendered PDF text")
        self.assertIsNotNone(chapter1_page, msg="Chapter 1's heading not found in rendered PDF text")
        self.assertNotEqual(table3_page, chapter1_page, msg="Chapter 1 still shares a page with the final notation table")
        self.assertGreater(chapter1_page, table3_page, msg="Chapter 1 should start strictly after Table 3's page")


class TestNoDuplicatedChapterTitleNumbering(unittest.TestCase):
    """Acceptance finding 2: each instructional chapter title must
    render with exactly one leading number, never 'N Chapter N: ...'."""

    def test_chapter_heading_source_does_not_repeat_chapter_prefix(self):
        for i, fname in enumerate(CHAPTER_FILES, start=1):
            with open(os.path.join(CHAPTERS_DIR, fname)) as f:
                first_line = f.readline()
            self.assertNotIn(f"Chapter {i}:", first_line, msg=f"{fname} still has a literal 'Chapter {i}:' prefix in its heading text")
            self.assertRegex(first_line, r"^## \S", msg=f"{fname}'s heading is missing or malformed")

    @unittest.skipUnless(os.path.exists(RC3_PDF), "RC3 PDF not built -- run scripts/build_release_candidate_v3.py first")
    def test_rendered_body_text_has_no_duplicated_numbering(self):
        result = subprocess.run(["pdftotext", "-layout", RC3_PDF, "-"], capture_output=True, text=True)
        matches = re.findall(DUPLICATED_CHAPTER_NUMBER_PATTERN, result.stdout, re.MULTILINE)
        self.assertEqual(matches, [], msg=f"found duplicated chapter-number pattern(s) in body text: {matches}")

    @unittest.skipUnless(os.path.exists(RC3_PDF), "RC3 PDF not built -- run scripts/build_release_candidate_v3.py first")
    def test_toc_has_no_duplicated_numbering(self):
        result = subprocess.run(["pdftotext", "-layout", RC3_PDF, "-"], capture_output=True, text=True)
        pages = result.stdout.split("\f")
        toc_text = "\n".join(pages[:3])  # title page + TOC spans the first few pages
        matches = re.findall(DUPLICATED_CHAPTER_NUMBER_PATTERN, toc_text, re.MULTILINE)
        self.assertEqual(matches, [], msg=f"found duplicated chapter-number pattern(s) in the TOC: {matches}")

    @unittest.skipUnless(os.path.exists(RC3_PDF), "RC3 PDF not built -- run scripts/build_release_candidate_v3.py first")
    def test_each_chapter_renders_with_single_leading_number(self):
        result = subprocess.run(["pdftotext", "-layout", RC3_PDF, "-"], capture_output=True, text=True)
        text = result.stdout
        expected_titles = {
            1: "Transformer Refresher",
            2: "Anatomy of a Modern Decoder",
            3: "Attention Head Structure and Cache-Efficient Variants",
        }
        for i, title in expected_titles.items():
            self.assertRegex(text, re.compile(rf"^{i}\s+{re.escape(title)}", re.MULTILINE),
                              msg=f"Chapter {i}'s rendered heading does not match the expected single-number format")


class TestNotationReferenceMKvMMla(unittest.TestCase):
    """Acceptance finding 3: the notation reference must name M_KV and
    M_MLA (the symbols the equations actually use), retire the unused
    KV_bytes entry, and add the sliding-window width W."""

    def test_m_kv_and_m_mla_present(self):
        with open(NOTATION_QMD) as f:
            text = f.read()
        self.assertIn("M_{KV}", text)
        self.assertIn("M_{\\text{MLA}}", text)
        self.assertIn("$W$", text)

    def test_kv_bytes_removed(self):
        with open(NOTATION_QMD) as f:
            text = f.read()
        self.assertNotIn("KV_bytes", text)
        self.assertNotIn("KV\\_bytes", text)

    def test_kv_bytes_not_used_anywhere_in_chapters(self):
        """If KV_bytes were still used by an equation, removing it from
        the notation reference would itself be a bug; confirm it truly
        is dead notation before celebrating its removal."""
        for fname in CHAPTER_FILES:
            with open(os.path.join(CHAPTERS_DIR, fname)) as f:
                text = f.read()
            self.assertNotIn("KV_bytes", text, msg=f"{fname} still uses KV_bytes -- should not have been removed from the notation reference")

    def test_notation_table_still_fits_within_safe_row_count(self):
        with open(NOTATION_QMD) as f:
            text = f.read()
        tables = []
        current_rows = 0
        in_table = False
        for line in text.splitlines():
            if line.startswith("| Symbol | Name | Meaning |"):
                in_table = True
                current_rows = 0
            elif in_table and line.startswith("|"):
                current_rows += 1
            elif in_table and not line.startswith("|"):
                tables.append(current_rows - 1)
                in_table = False
        if in_table:
            tables.append(current_rows - 1)
        for i, row_count in enumerate(tables, start=1):
            self.assertLessEqual(row_count, 10, msg=f"notation table part {i} has {row_count} rows, exceeding the empirically-safe limit")

    @unittest.skipUnless(os.path.exists(RC3_PDF), "RC3 PDF not built -- run scripts/build_release_candidate_v3.py first")
    def test_notation_table_pages_render_without_kv_bytes(self):
        result = subprocess.run(["pdftotext", "-layout", RC3_PDF, "-"], capture_output=True, text=True)
        self.assertNotIn("KV_bytes", result.stdout)
        self.assertIn("KV-cache size", result.stdout)


class TestBuildNoteSanitization(unittest.TestCase):
    """Acceptance finding 4: the learner-facing build note must not
    leak repository-internal paths, registry IDs, or a raw commit SHA."""

    def test_build_note_source_has_no_banned_patterns(self):
        with open(BUILD_NOTE_QMD) as f:
            text = f.read()
        for pattern in BANNED_INTERNAL_PATH_PATTERNS:
            self.assertIsNone(re.search(pattern, text), msg=f"build-version-note.qmd contains banned pattern {pattern!r}")

    def test_build_note_retains_useful_learner_facing_fields(self):
        with open(BUILD_NOTE_QMD) as f:
            text = f.read()
        self.assertIn("Generated:", text)
        self.assertIn("Source verification:", text)
        self.assertIn("Release status:", text)
        self.assertIn("Provenance", text)

    def test_generator_never_interpolates_commit_into_template(self):
        with open(os.path.join(REPO_ROOT, "scripts", "generate_build_note.py")) as f:
            text = f.read()
        template_start = text.index('content = f"""')
        template_text = text[template_start:]
        self.assertNotIn("commit", template_text.lower())

    @unittest.skipUnless(os.path.exists(RC3_PDF), "RC3 PDF not built -- run scripts/build_release_candidate_v3.py first")
    def test_rendered_pdf_text_has_no_banned_internal_path_patterns(self):
        result = subprocess.run(["pdftotext", RC3_PDF, "-"], capture_output=True, text=True)
        text = result.stdout
        for pattern in BANNED_INTERNAL_PATH_PATTERNS:
            matches = re.findall(pattern, text)
            self.assertEqual(matches, [], msg=f"rendered PDF text contains banned pattern {pattern!r}: {matches[:5]}")


@unittest.skipUnless(os.path.exists(RC3_PDF), "RC3 PDF not built -- run scripts/build_release_candidate_v3.py first")
class TestRc3PageCount(unittest.TestCase):
    def test_page_count_at_or_below_72(self):
        result = subprocess.run(["pdfinfo", RC3_PDF], capture_output=True, text=True)
        m = re.search(r"Pages:\s+(\d+)", result.stdout)
        self.assertIsNotNone(m)
        pages = int(m.group(1))
        self.assertLessEqual(pages, 72, msg=f"RC3 has grown to {pages} pages, exceeding the 72-page hard ceiling")


if __name__ == "__main__":
    unittest.main()
