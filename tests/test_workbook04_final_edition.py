"""Guard the learner-facing Final Edition metadata of Workbook 04.

The canonical final PDF is built by scripts/build_final.py, which swaps the
RC scope note for includes/final-scope-note.qmd and regenerates the build
note. These tests keep release-candidate wording out of those two includes.
"""
import os
import re
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INCLUDES = os.path.join(REPO_ROOT, "workbooks", "04-llm-architecture", "includes")
FINAL_SCOPE = os.path.join(INCLUDES, "final-scope-note.qmd")
BUILD_NOTE = os.path.join(INCLUDES, "build-version-note.qmd")
BUILD_FINAL = os.path.join(REPO_ROOT, "scripts", "build_final.py")

BANNED = [
    r"release candidate",
    r"\bRC\d",
    r"not the final edition",
    r"review artifact",
    r"copy-edited",
    r"\.py\b",
    r"\.qmd\b",
    r"\.yaml\b",
    r"src-\d+",
    r"/mnt/",
    r"AGENTS\.md",
    r"CLAUDE\.md",
]

# Internal filenames / paths that must never appear in rendered chapter or
# answer-key prose (citation keys like [@src-NN] are resolved to numbers by
# the bibliography and are deliberately not matched here).
PROSE_BANNED = [
    r"AGENTS\.md",
    r"CLAUDE\.md",
    r"/mnt/",
    r"/home/",
    r"\.qmd\b",
    r"\.py\b",
    r"build_final",
    r"generate_build_note",
    r"release[- ]candidate",
]


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class FinalEditionMetadataTests(unittest.TestCase):
    def test_final_scope_note_is_final_edition_and_clean(self):
        text = read(FINAL_SCOPE)
        self.assertIn("Final", text)
        for pattern in BANNED:
            self.assertIsNone(re.search(pattern, text, re.I), msg=f"final-scope-note matches {pattern!r}")

    def test_build_note_is_final_edition_and_clean(self):
        text = read(BUILD_NOTE)
        self.assertIn("Final Edition", text)
        for pattern in BANNED:
            self.assertIsNone(re.search(pattern, text, re.I), msg=f"build note matches {pattern!r}")

    def test_chapter_and_solution_prose_has_no_internal_references(self):
        wb = os.path.join(REPO_ROOT, "workbooks", "04-llm-architecture")
        files = []
        for sub in ("chapters", "solutions"):
            d = os.path.join(wb, sub)
            files += [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith(".qmd")]
        files.append(os.path.join(INCLUDES, "notation-summary.qmd"))
        self.assertTrue(files)
        for path in files:
            text = read(path)
            for pattern in PROSE_BANNED:
                m = re.search(pattern, text, re.I)
                self.assertIsNone(m, msg=f"{os.path.relpath(path, REPO_ROOT)} matches {pattern!r}: "
                                         f"{text[max(0, m.start()-40):m.end()+40]!r}" if m else "")

    def test_build_final_swaps_in_final_scope_note(self):
        text = read(BUILD_FINAL)
        self.assertIn("includes/final-scope-note.qmd", text)
        self.assertNotIn("RC1–RC7 were release-candidate drafts", text)


if __name__ == "__main__":
    unittest.main()
