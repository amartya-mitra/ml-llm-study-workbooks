"""Deterministic, network-free tests for scripts/validate_publication_hygiene.py."""
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import validate_publication_hygiene as v  # noqa: E402

SLUG = v.DEFAULT_REPO_SLUG
PDF_BYTES = b"%PDF-1.7 fixture bytes"
PDF_SHA = hashlib.sha256(PDF_BYTES).hexdigest()


def record(n="04", status="published", **over):
    rec = {
        "title": f"Workbook {n}",
        "status": status,
        "canonical_path": f"outputs/{n}-fixture-workbook.pdf",
        "page_count": 12,
        "sha256": PDF_SHA,
        "source_commit": "a" * 40,
        "release_tag": f"workbook-{n}-v1.0.0",
        "release_title": f"Workbook {n} v1.0.0",
        "release_asset": f"{n}-fixture-workbook.pdf",
        "release_url": v.release_page_url(SLUG, f"workbook-{n}-v1.0.0"),
        "publication_date": "2026-10-06" if status == "published" else None,
        "reproduction_command": "python3 scripts/build_final.py",
        "human_acceptance": {"accepted": True, "date": "2026-10-05", "note": "fixture"},
    }
    rec.update(over)
    return rec


def readme_for(pubs, overrides=None):
    rows = []
    for aid, rec in pubs.items():
        st = rec["status"]
        label = v.STATUS_LABEL[st]
        link = (v.asset_url(SLUG, rec["release_tag"], rec["release_asset"])
                if st == "published" else "not yet released")
        row = f"| `{aid}` | {aid} | scope | {label} | {rec['page_count']} | `{rec['release_tag']}` | {link} |"
        rows.append((overrides or {}).get(aid, row))
    return f"intro\n{v.README_START}\n| ID | W | S | Status | P | V | D |\n|---|---|---|---|---|---|---|\n" \
           + "\n".join(rows) + f"\n{v.README_END}\n"


class RegistryValidationTests(unittest.TestCase):
    def test_valid_published_records_pass(self):
        pubs = {"workbook-04": record("04"), "workbook-05": record("05")}
        self.assertEqual(v.validate_registry(pubs, slug=SLUG), [])
        self.assertEqual(v.validate_readme(readme_for(pubs), pubs, SLUG), [])

    def test_published_with_missing_metadata_fails(self):
        for field in ("sha256", "source_commit", "release_tag", "release_asset", "release_url",
                      "publication_date", "reproduction_command", "page_count", "human_acceptance"):
            rec = record()
            rec[field] = None
            errs = v.validate_registry({"workbook-04": rec}, slug=SLUG)
            self.assertTrue(errs, msg=f"missing {field} must fail")

    def test_published_without_human_acceptance_marker_fails(self):
        rec = record(human_acceptance={"accepted": False, "date": "2026-10-05"})
        self.assertTrue(any("human_acceptance" in e for e in v.validate_registry({"a": rec}, slug=SLUG)))

    def test_malformed_checksum_and_commit_and_pages_fail(self):
        for bad in ("abc", "G" * 64, "A" * 64, "a" * 63):
            errs = v.validate_registry({"a": record(sha256=bad)}, slug=SLUG)
            self.assertTrue(any("sha256" in e for e in errs), msg=bad)
        self.assertTrue(any("source_commit" in e for e in v.validate_registry({"a": record(source_commit="0de73f5")}, slug=SLUG)))
        self.assertTrue(any("page_count" in e for e in v.validate_registry({"a": record(page_count=0)}, slug=SLUG)))
        self.assertTrue(any("page_count" in e for e in v.validate_registry({"a": record(page_count="69")}, slug=SLUG)))

    def test_duplicate_tag_asset_and_id_fail(self):
        a, b = record("04"), record("05", release_tag="workbook-04-v1.0.0",
                                    release_url=v.release_page_url(SLUG, "workbook-04-v1.0.0"))
        self.assertTrue(any("duplicates" in e and "release_tag" in e for e in v.validate_registry({"x": a, "y": b}, slug=SLUG)))
        c = record("05", release_asset="04-fixture-workbook.pdf", canonical_path="outputs/04-fixture-workbook.pdf")
        self.assertTrue(any("release_asset" in e and "duplicates" in e for e in v.validate_registry({"x": a, "y": c}, slug=SLUG)))
        raw = "publications:\n  workbook-04:\n    status: x\n  workbook-04:\n    status: y\nother: 1\n"
        self.assertEqual(v.duplicate_artifact_ids(raw), ["workbook-04"])

    def test_rc_and_development_assets_rejected(self):
        for name in ("04-workbook-rc7.pdf", "04-workbook-superseded.pdf", "04-chapter-review.pdf", "04-dev-build.pdf"):
            rec = record(release_asset=name, canonical_path=f"outputs/{name}")
            self.assertTrue(v.validate_registry({"a": rec}, slug=SLUG), msg=name)
        for path in ("outputs/_releases/04/x.pdf", "outputs/_development/x.pdf", "workbooks/04/x.pdf"):
            rec = record(canonical_path=path)
            self.assertTrue(v.validate_registry({"a": rec}, slug=SLUG), msg=path)

    def test_release_url_and_tag_conventions(self):
        self.assertTrue(v.validate_registry({"a": record(release_url="https://example.com/x")}, slug=SLUG))
        self.assertTrue(v.validate_registry({"a": record(release_tag="v1")}, slug=SLUG))

    def test_accepted_frozen_is_not_published(self):
        rec = {"title": "X", "status": "accepted_frozen"}
        self.assertEqual(v.validate_registry({"a": rec}, slug=SLUG), [])  # no release metadata needed yet
        # ...but it must never be shown as Published, and must not carry a publication date
        pubs = {"workbook-04": rec | {"release_tag": "workbook-04-v1.0.0", "page_count": 1}}
        text = readme_for(pubs).replace("Accepted (frozen)", "Published")
        self.assertTrue(v.validate_readme(text, pubs, SLUG))
        self.assertTrue(v.validate_registry({"a": rec | {"publication_date": "2026-10-06"}}, slug=SLUG))

    def test_canonical_built_requires_prepared_values_but_not_publication(self):
        ok = record(status="canonical_built")
        self.assertEqual(v.validate_registry({"a": ok}, slug=SLUG), [])
        self.assertTrue(v.validate_registry({"a": record(status="canonical_built", sha256=None)}, slug=SLUG))
        self.assertTrue(v.validate_registry({"a": record(status="bogus")}, slug=SLUG))


class ReadmeConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.pubs = {"workbook-04": record("04"), "workbook-05": record("05")}

    def test_stale_status_fails(self):
        text = readme_for(self.pubs).replace("Published", "Release pending", 1)
        self.assertTrue(any("status must read" in e for e in v.validate_readme(text, self.pubs, SLUG)))

    def test_stale_or_wrong_link_fails(self):
        url = v.asset_url(SLUG, "workbook-04-v1.0.0", "04-fixture-workbook.pdf")
        text = readme_for(self.pubs).replace(url, url.replace("v1.0.0", "v0.9.0"))
        errs = v.validate_readme(text, self.pubs, SLUG)
        self.assertTrue(any("direct release-asset link" in e for e in errs))
        self.assertTrue(any("not backed by a published record" in e for e in errs))

    def test_link_before_publication_fails(self):
        pubs = {"workbook-04": record("04", status="canonical_built")}
        row = "| `workbook-04` | x | s | Release pending | 12 | `workbook-04-v1.0.0` | " \
              + v.asset_url(SLUG, "workbook-04-v1.0.0", "04-fixture-workbook.pdf") + " |"
        errs = v.validate_readme(readme_for(pubs, {"workbook-04": row}), pubs, SLUG)
        self.assertTrue(errs)

    def test_missing_row_or_catalog_fails(self):
        self.assertTrue(v.validate_readme("no catalog here", self.pubs, SLUG))
        text = readme_for({"workbook-04": self.pubs["workbook-04"]})
        self.assertTrue(any("missing from README" in e for e in v.validate_readme(text, self.pubs, SLUG)))

    def test_readme_rejects_rc_artifact_links(self):
        text = readme_for(self.pubs) + "\nsee [rc](outputs/_releases/04/x-rc7.pdf)\n"
        self.assertTrue(any("RC/development" in e for e in v.validate_readme(text, self.pubs, SLUG)))
        # naming the directories in policy prose is allowed
        prose = readme_for(self.pubs) + "\nRC artifacts stay in outputs/_releases/ and are never published.\n"
        self.assertEqual(v.validate_readme(prose, self.pubs, SLUG), [])


class TrackedPdfTests(unittest.TestCase):
    def test_tracked_canonical_pdf_rejected(self):
        self.assertEqual(v.tracked_canonical_pdfs(["outputs/.gitkeep"]), [])
        self.assertEqual(v.tracked_canonical_pdfs(["outputs/.gitkeep", "outputs/04-x.pdf"]), ["outputs/04-x.pdf"])
        self.assertEqual(v.tracked_canonical_pdfs(["outputs/_releases/04/x-rc1.pdf"]), ["outputs/_releases/04/x-rc1.pdf"])


class LocalArtifactTests(unittest.TestCase):
    def test_absent_local_pdf_is_fine_on_clean_clone(self):
        with tempfile.TemporaryDirectory() as root:
            errs, warns = v.check_local_artifact(record(), root)
            self.assertEqual(errs, [])
            self.assertTrue(warns)
            errs, _ = v.check_local_artifact(record(), root, require=True)
            self.assertTrue(errs)

    def test_local_checksum_and_page_mismatch_detected(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "outputs"))
            path = os.path.join(root, "outputs", "04-fixture-workbook.pdf")
            with open(path, "wb") as f:
                f.write(PDF_BYTES)
            self.assertEqual(v.check_local_artifact(record(), root, page_fn=lambda p: 12), ([], []))
            errs, _ = v.check_local_artifact(record(sha256="0" * 64), root, page_fn=lambda p: 12)
            self.assertTrue(any("SHA-256 mismatch" in e for e in errs))
            errs, _ = v.check_local_artifact(record(), root, page_fn=lambda p: 13)
            self.assertTrue(any("page count mismatch" in e for e in errs))


class RemoteParsingTests(unittest.TestCase):
    def release(self, **over):
        rec = record()
        rel = {"tag_name": rec["release_tag"], "draft": False, "prerelease": False,
               "assets": [{"name": rec["release_asset"], "size": len(PDF_BYTES),
                           "browser_download_url": v.asset_url(SLUG, rec["release_tag"], rec["release_asset"])}]}
        rel.update(over)
        return rel

    def test_valid_payload_passes(self):
        self.assertEqual(v.verify_release_payload(self.release(), record(), SLUG, lambda u: PDF_BYTES), [])

    def test_bad_payloads_fail(self):
        rec = record()
        self.assertTrue(v.verify_release_payload(self.release(draft=True), rec, SLUG, lambda u: PDF_BYTES))
        self.assertTrue(v.verify_release_payload(self.release(prerelease=True), rec, SLUG, lambda u: PDF_BYTES))
        self.assertTrue(v.verify_release_payload(self.release(tag_name="other"), rec, SLUG, lambda u: PDF_BYTES))
        self.assertTrue(v.verify_release_payload(self.release(assets=[]), rec, SLUG, lambda u: PDF_BYTES))
        extra = self.release()
        extra["assets"].append({"name": "notes.txt", "browser_download_url": "x"})
        self.assertTrue(v.verify_release_payload(extra, rec, SLUG, lambda u: PDF_BYTES))
        self.assertTrue(any("SHA-256" in e for e in v.verify_release_payload(self.release(), rec, SLUG, lambda u: b"tampered")))

    def test_remote_check_with_fake_get_never_needs_network(self):
        pubs = {"workbook-04": record(), "workbook-05": record("05", status="canonical_built")}
        calls = []

        def fake_get(url, accept=None):
            calls.append(url)
            if "/releases/tags/" in url:
                return json.dumps(self.release()).encode()
            return PDF_BYTES
        errors, notes = v.remote_check(pubs, SLUG, get=fake_get)
        self.assertEqual(errors, [])
        self.assertTrue(any("not required yet" in n for n in notes))
        self.assertTrue(all(c.startswith("https://") for c in calls))

    def test_remote_404_is_reported_as_failure(self):
        def fake_get(url, accept=None):
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, io.BytesIO(b""))
        errors, _ = v.remote_check({"workbook-04": record()}, SLUG, get=fake_get)
        self.assertTrue(any("404" in e for e in errors))


class RealRepositoryTests(unittest.TestCase):
    def test_repository_registry_and_readme_validate_offline(self):
        self.assertEqual(v.main(["--root", REPO_ROOT]), 0)

    def test_no_canonical_pdf_is_tracked_in_this_repository(self):
        tracked = v.git_tracked_files(REPO_ROOT)
        if tracked is not None:
            self.assertEqual(v.tracked_canonical_pdfs(tracked), [])


if __name__ == "__main__":
    unittest.main()
