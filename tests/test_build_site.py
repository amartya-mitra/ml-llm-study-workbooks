"""Deterministic, network-free tests for scripts/build_site.py."""
import hashlib
import json
import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import build_site as b  # noqa: E402
import validate_publication_hygiene as v  # noqa: E402
from _yaml_lite import safe_load_path  # noqa: E402

SLUG = v.DEFAULT_REPO_SLUG
NEW, OLD = b"%PDF-1.7 new edition", b"%PDF-1.7 old edition"
NEW_SHA, OLD_SHA = hashlib.sha256(NEW).hexdigest(), hashlib.sha256(OLD).hexdigest()
URL_NEW = v.asset_url(SLUG, "guide-v1.1.0", "guide.pdf")
URL_OLD = v.asset_url(SLUG, "guide-v1.0.0", "guide.pdf")

REGISTRY = f"""schema_version: 1
workbooks:
  06-draft:
    chapters:
      01:
        status: "accepted_frozen"
      02:
        status: "scaffold_only"
publications:
  guide:
    title: "Fixture Guide"
    status: "published"
    version: "1.1.0"
    page_count: 20
    bytes: {len(NEW)}
    sha256: "{NEW_SHA}"
    release_tag: "guide-v1.1.0"
    release_asset: "guide.pdf"
    previous_releases:
      - version: "1.0.0"
        status: "published"
        page_count: 18
        sha256: "{OLD_SHA}"
        release_tag: "guide-v1.0.0"
        release_asset: "guide.pdf"
  draft:
    title: "Draft Guide"
    workbook_id: "06-draft"
    status: "drafting"
    release_tag: "draft-v1.0.0"
    release_asset: "draft.pdf"
"""

README = f"""# Fixture
{v.README_START}
| Study guide | What you will learn | Read |
|---|---|---|
| **Fixture Guide** | Things <b>& more</b> | [Download PDF]({URL_NEW}) (20 pages) |
{v.README_END}

{v.IN_PROGRESS_START}
- **Draft Guide**: In progress, 1 of 2 chapters accepted.
{v.IN_PROGRESS_END}
"""


def fixture_root(registry=REGISTRY, readme=README):
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "config"))
    with open(os.path.join(root, "config", "chapter-status-registry.yaml"), "w") as f:
        f.write(registry)
    with open(os.path.join(root, "README.md"), "w") as f:
        f.write(readme)
    return root


class FakeFetch:
    def __init__(self, files):
        self.files, self.calls = files, []

    def __call__(self, url):
        self.calls.append(url)
        if url not in self.files:
            raise OSError(f"404 {url}")
        return self.files[url]


class BuildSiteTests(unittest.TestCase):
    def setUp(self):
        self.root = fixture_root()
        self.out = os.path.join(self.root, "_site")
        self.fetch = FakeFetch({URL_NEW: NEW, URL_OLD: OLD})

    def test_builds_versioned_verified_site(self):
        eds = b.build(self.root, self.out, SLUG, self.fetch)
        self.assertEqual(sorted(self.fetch.calls), sorted([URL_NEW, URL_OLD]))
        self.assertEqual([e["path"] for e in eds], ["editions/guide-v1.1.0/guide.pdf", "editions/guide-v1.0.0/guide.pdf"])
        for rel, data in (("editions/guide-v1.1.0/guide.pdf", NEW), ("editions/guide-v1.0.0/guide.pdf", OLD)):
            with open(os.path.join(self.out, rel), "rb") as f:
                self.assertEqual(f.read(), data)
        with open(os.path.join(self.out, "index.html"), encoding="utf-8") as f:
            page = f.read()
        self.assertIn('href="editions/guide-v1.1.0/guide.pdf">Read in browser', page)
        self.assertIn('href="editions/guide-v1.1.0/guide.pdf" download>Download PDF', page)
        self.assertIn("Some browsers or settings download PDFs", page)
        self.assertIn('name="viewport"', page)
        self.assertIn("Draft Guide</strong>: in progress, 1 of 2 chapters accepted", page)
        self.assertNotIn("draft.pdf", page)
        self.assertIn("&lt;b&gt;&amp; more&lt;/b&gt;", page)  # README text is escaped, not injected
        self.assertNotIn('href="/', page)  # relative paths only, so a project-site prefix works
        with open(os.path.join(self.out, "editions.json")) as f:
            manifest = json.load(f)
        self.assertEqual({m["sha256"] for m in manifest}, {NEW_SHA, OLD_SHA})
        self.assertEqual(sorted(os.listdir(self.out)), ["editions", "editions.json", "index.html", "style.css"])

    def test_checksum_mismatch_fails_and_writes_nothing(self):
        bad = FakeFetch({URL_NEW: NEW, URL_OLD: b"%PDF tampered"})
        with self.assertRaisesRegex(b.SiteBuildError, "SHA-256 mismatch"):
            b.build(self.root, self.out, SLUG, bad)
        self.assertFalse(os.path.exists(self.out))
        self.assertEqual([d for d in os.listdir(self.root) if d.startswith(".site-build-")], [])

    def test_checksum_mismatch_keeps_previous_output_untouched(self):
        b.build(self.root, self.out, SLUG, self.fetch)
        with self.assertRaises(b.SiteBuildError):
            b.build(self.root, self.out, SLUG, FakeFetch({URL_NEW: b"x", URL_OLD: OLD}))
        with open(os.path.join(self.out, "editions/guide-v1.1.0/guide.pdf"), "rb") as f:
            self.assertEqual(f.read(), NEW)

    def test_main_reports_failure_with_exit_status(self):
        orig = b.fetch_url
        b.fetch_url = FakeFetch({URL_NEW: b"tampered", URL_OLD: OLD})
        try:
            self.assertEqual(b.main(["--root", self.root, "--out", self.out]), 1)
        finally:
            b.fetch_url = orig

    def test_size_mismatch_and_download_failure_fail(self):
        reg = REGISTRY.replace(f"bytes: {len(NEW)}", f"bytes: {len(NEW) + 1}")
        with self.assertRaisesRegex(b.SiteBuildError, "size mismatch"):
            b.build(fixture_root(reg), None, SLUG, self.fetch)
        with self.assertRaisesRegex(b.SiteBuildError, "download failed"):
            b.build(self.root, self.out, SLUG, FakeFetch({URL_NEW: NEW}))

    def test_unpublished_and_unsafe_records_never_become_files(self):
        reg = REGISTRY.replace('status: "published"\n    version', 'status: "canonical_built"\n    version')
        with self.assertRaisesRegex(b.SiteBuildError, "no published editions"):
            b.build(fixture_root(reg), None, SLUG, self.fetch)
        for tag in ("../x", ".hidden"):
            reg = REGISTRY.replace('release_tag: "guide-v1.1.0"', f'release_tag: "{tag}"')
            with self.assertRaisesRegex(b.SiteBuildError, "unsafe"):
                b.build(fixture_root(reg), None, SLUG, self.fetch)
        reg = REGISTRY.replace(f'sha256: "{OLD_SHA}"', 'sha256: null')
        with self.assertRaisesRegex(b.SiteBuildError, "valid sha256"):
            b.build(fixture_root(reg), None, SLUG, self.fetch)

    def test_current_edition_needs_readme_description(self):
        root = fixture_root(readme=README.replace(URL_NEW, "https://example.com/x.pdf"))
        with self.assertRaisesRegex(b.SiteBuildError, "no description"):
            b.build(root, None, SLUG, self.fetch)


class RealRepositoryTests(unittest.TestCase):
    def test_every_current_published_edition_has_a_readme_description(self):
        pubs = safe_load_path(os.path.join(REPO_ROOT, "config", "chapter-status-registry.yaml"))["publications"]
        with open(os.path.join(REPO_ROOT, "README.md"), encoding="utf-8") as f:
            desc = b.catalog_descriptions(f.read(), pubs, SLUG)
        current = {e["id"] for e in v.editions(pubs) if e["current"]}
        self.assertEqual(set(desc), current)
        self.assertNotIn("workbook-06", desc)

    def test_real_registry_build_rejects_wrong_bytes_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "site")
            with self.assertRaisesRegex(b.SiteBuildError, "SHA-256 mismatch"):
                b.build(REPO_ROOT, out, SLUG, lambda url: b"%PDF not the release")
            self.assertFalse(os.path.exists(out))

    def test_site_build_output_is_ignored_by_git(self):
        with open(os.path.join(REPO_ROOT, ".gitignore")) as f:
            self.assertIn("_site/", f.read().split())


if __name__ == "__main__":
    unittest.main()
