"""Regression test for the RC4 one-defect finalization fix: Chapter 4's
title hyphenated "Representations" across its line wrap
("Rep-/resentations"). The same check found an identical defect in
Chapter 7's title ("Com-/munication"), so both were fixed, and the
same protection (an explicit phrase-level #linebreak() instead of
automatic hyphenation) was applied to every chapter title that wraps
to two lines (Chapters 4, 6, 7, 8).

Source-level checks run offline against the qmd files. Rendered-PDF
checks are skipped automatically when the RC4 PDF has not been built
in the current environment.
"""
import os
import re
import subprocess
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WB04 = os.path.join(REPO_ROOT, "workbooks", "04-llm-architecture")
CHAPTERS_DIR = os.path.join(WB04, "chapters")
RC4_PDF = os.path.join(REPO_ROOT, "outputs", "04-modern-llm-architecture-workbook-rc4.pdf")

TWO_LINE_CHAPTERS = {
    4: os.path.join(CHAPTERS_DIR, "04-reducing-attention-cost.qmd"),
    6: os.path.join(CHAPTERS_DIR, "06-case-studies.qmd"),
    7: os.path.join(CHAPTERS_DIR, "07-architecture-to-systems-behavior.qmd"),
    8: os.path.join(CHAPTERS_DIR, "08-emerging-directions-and-synthesis.qmd"),
}


def _normalize_heading_text(page_text, chapter_number):
    """Extract the chapter's rendered heading (its first line/lines)
    and normalize away the line wrap, so a title split across two
    physical lines reads back as one continuous phrase for comparison."""
    lines = page_text.strip().splitlines()
    heading_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            break
        heading_lines.append(stripped)
        if len(heading_lines) >= 3:
            break
    return " ".join(heading_lines)


def _find_chapter_opening_page(pages, chapter_number, title_start):
    """Find the page where a chapter actually opens, not the Table of
    Contents entry. Long titles wrap in the TOC at the same phrase
    point as the real heading, and the TOC also lists "N.1 Learning
    objectives" as its own line, so neither alone disambiguates. Only
    the real chapter-opening page has the objectives' intro sentence
    immediately below that subsection heading."""
    marker = "By the end of this chapter you should be able to:"
    for page in pages:
        if re.search(rf"^{chapter_number}\s+{re.escape(title_start)}", page, re.MULTILINE) and marker in page:
            return page
    return None


class TestChapter4TitleNoHyphenation(unittest.TestCase):
    """The specific acceptance finding: Chapter 4's title must never
    split "Representations" (or any word) with a hyphen across the
    line wrap."""

    CH4_PATH = TWO_LINE_CHAPTERS[4]

    def test_chapter4_heading_has_explicit_linebreak_after_sparsity(self):
        with open(self.CH4_PATH) as f:
            first_line = f.readline()
        self.assertIn("Sparsity, `#linebreak()`{=typst}and Latent KV Representations", first_line,
                      msg="Chapter 4's heading should force a break right after 'Sparsity,' per the task's example")

    def test_chapter4_heading_source_has_no_manual_hyphen(self):
        with open(self.CH4_PATH) as f:
            first_line = f.readline()
        self.assertNotIn("Rep-", first_line)
        self.assertIn("Representations", first_line)

    @unittest.skipUnless(os.path.exists(RC4_PDF), "RC4 PDF not built -- run scripts/build_release_candidate_v4.py first")
    def test_rendered_chapter4_heading_normalizes_to_complete_title(self):
        result = subprocess.run(["pdftotext", "-layout", RC4_PDF, "-"], capture_output=True, text=True)
        pages = result.stdout.split("\f")
        heading_page = _find_chapter_opening_page(pages, 4, "Reducing Attention Cost")
        self.assertIsNotNone(heading_page, msg="Chapter 4's heading not found in the rendered PDF text")
        normalized = _normalize_heading_text(heading_page, 4)
        # No hyphenated or line-broken "Representations": neither a
        # trailing "Rep-" fragment nor a stray "resentations" remainder.
        self.assertNotRegex(normalized, r"Rep-\s*resentations")
        self.assertNotIn("Rep-", normalized)
        self.assertIn(
            "4 Reducing Attention Cost: Windows, Sparsity, and Latent KV Representations",
            normalized,
        )


class TestAllTwoLineChapterTitlesProtected(unittest.TestCase):
    """Extending the same protection to every chapter title that wraps
    to two lines (Chapters 4, 6, 7, 8), since the same defect was also
    found live in Chapter 7's title."""

    def test_each_two_line_chapter_heading_uses_explicit_linebreak(self):
        for i, path in TWO_LINE_CHAPTERS.items():
            with open(path) as f:
                first_line = f.readline()
            self.assertIn("#linebreak()", first_line, msg=f"Chapter {i}'s heading no longer forces an explicit break")

    @unittest.skipUnless(os.path.exists(RC4_PDF), "RC4 PDF not built -- run scripts/build_release_candidate_v4.py first")
    def test_no_hyphenated_word_break_in_any_chapter_heading(self):
        """A generic detector: no chapter heading's rendered lines may
        end with a hyphen (Typst's automatic-hyphenation marker) --
        every wrap must be an explicit, whole-word phrase break."""
        result = subprocess.run(["pdftotext", "-layout", RC4_PDF, "-"], capture_output=True, text=True)
        pages = result.stdout.split("\f")
        chapter_titles = {
            1: "Transformer Refresher",
            2: "Anatomy of a Modern Decoder",
            3: "Attention Head Structure and Cache-Efficient Variants",
            4: "Reducing Attention Cost",
            5: "Mixture of Experts",
            6: "Reading Modern LLM Architectures",
            7: "From Architecture to Systems Behavior",
            8: "Emerging Directions and Architecture Synthesis",
        }
        for i, title_start in chapter_titles.items():
            heading_page = _find_chapter_opening_page(pages, i, title_start)
            self.assertIsNotNone(heading_page, msg=f"Chapter {i}'s heading not found in the rendered PDF text")
            lines = heading_page.strip().splitlines()
            # The heading may span up to 3 physical lines (long titles);
            # check the first few lines for a trailing hyphen.
            for line in lines[:3]:
                stripped = line.rstrip()
                if not stripped:
                    break
                self.assertFalse(
                    re.search(r"[A-Za-z]-$", stripped),
                    msg=f"Chapter {i}'s heading line {stripped!r} ends with a hyphen -- possible mid-word break",
                )

    @unittest.skipUnless(os.path.exists(RC4_PDF), "RC4 PDF not built -- run scripts/build_release_candidate_v4.py first")
    def test_chapter7_communication_not_hyphenated(self):
        result = subprocess.run(["pdftotext", "-layout", RC4_PDF, "-"], capture_output=True, text=True)
        pages = result.stdout.split("\f")
        heading_page = _find_chapter_opening_page(pages, 7, "From Architecture to Systems Behavior")
        self.assertIsNotNone(heading_page, msg="Chapter 7's heading not found in the rendered PDF text")
        normalized = _normalize_heading_text(heading_page, 7)
        self.assertNotIn("Com-", normalized)
        self.assertIn("Communication", normalized)


@unittest.skipUnless(os.path.exists(RC4_PDF), "RC4 PDF not built -- run scripts/build_release_candidate_v4.py first")
class TestRc4PageCount(unittest.TestCase):
    def test_page_count_at_or_below_72(self):
        result = subprocess.run(["pdfinfo", RC4_PDF], capture_output=True, text=True)
        m = re.search(r"Pages:\s+(\d+)", result.stdout)
        self.assertIsNotNone(m)
        pages = int(m.group(1))
        self.assertLessEqual(pages, 72, msg=f"RC4 has grown to {pages} pages, exceeding the 72-page hard ceiling")


if __name__ == "__main__":
    unittest.main()
