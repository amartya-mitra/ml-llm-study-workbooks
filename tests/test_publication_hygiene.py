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


def readme_for(pubs, overrides=None, progress=None):
    """A README in the learner layout: published guides in the catalog,
    unpublished ones in the in-progress block (``progress`` maps id -> text)."""
    rows, items = [], []
    for aid, rec in pubs.items():
        if rec["status"] == "published":
            url = v.asset_url(SLUG, rec["release_tag"], rec["release_asset"])
            row = f"| **{rec['title']}** | what you learn | [Download PDF]({url}) ({rec['page_count']} pages) |"
            rows.append((overrides or {}).get(aid, row))
        elif rec["status"] in v.IN_PROGRESS_STATES:
            items.append(f"- **{rec['title']}**: " + (progress or {}).get(aid, "In progress."))
    return (f"intro\n{v.README_START}\n| Study guide | What you will learn | Read |\n|---|---|---|\n"
            + "\n".join(rows) + f"\n{v.README_END}\n\n{v.IN_PROGRESS_START}\n"
            + "\n".join(items) + f"\n{v.IN_PROGRESS_END}\n")


def verification_for(pubs):
    lines = ["| Guide | Edition | Tag | Pages | Bytes | SHA-256 | Released |", "|---|---|---|---|---|---|---|"]
    for ed in v.editions(pubs):
        lines.append(f"| {ed['title']} | x | `{ed['release_tag']}` | {ed['page_count']} | 1 | `{ed['sha256']}` | d |")
    lines += [v.release_page_url(SLUG, ed["release_tag"]) for ed in v.editions(pubs)]
    return "\n".join(lines) + "\n"


WORKBOOKS = {"06-fixture": {"chapters": {"01": {"status": "accepted_frozen"},
                                         "02": {"status": "accepted_frozen"},
                                         "03": {"status": "scaffold_only"}}}}


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
        self.assertEqual(v.validate_readme(readme_for(pubs), pubs, SLUG), [])
        text = readme_for(pubs).replace("In progress.", "Published.")
        self.assertTrue(any("not published" in e for e in v.validate_readme(text, pubs, SLUG)))
        self.assertTrue(v.validate_registry({"a": rec | {"publication_date": "2026-10-06"}}, slug=SLUG))

    def test_canonical_built_requires_prepared_values_but_not_publication(self):
        ok = record(status="canonical_built")
        self.assertEqual(v.validate_registry({"a": ok}, slug=SLUG), [])
        self.assertTrue(v.validate_registry({"a": record(status="canonical_built", sha256=None)}, slug=SLUG))
        self.assertTrue(v.validate_registry({"a": record(status="bogus")}, slug=SLUG))


class ReadmeConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.pubs = {"workbook-04": record("04"), "workbook-05": record("05")}

    def test_learner_layout_passes(self):
        self.assertEqual(v.validate_readme(readme_for(self.pubs), self.pubs, SLUG), [])

    def test_stale_or_wrong_link_fails(self):
        url = v.asset_url(SLUG, "workbook-04-v1.0.0", "04-fixture-workbook.pdf")
        text = readme_for(self.pubs).replace(url, url.replace("v1.0.0", "v0.9.0"))
        errs = v.validate_readme(text, self.pubs, SLUG)
        self.assertTrue(any("direct release-asset link" in e for e in errs))
        self.assertTrue(any("not backed by a current published record" in e for e in errs))

    def test_previous_edition_link_is_not_a_current_download(self):
        rec = record("04", previous_releases=[{"status": "published", "version": "0.9.0",
                                               "release_tag": "workbook-04-v0.9.0",
                                               "release_asset": "04-fixture-workbook.pdf"}])
        pubs = {"workbook-04": rec}
        old = v.asset_url(SLUG, "workbook-04-v0.9.0", "04-fixture-workbook.pdf")
        text = readme_for(pubs) + f"\nOld: [Download PDF]({old})\n"
        self.assertTrue(any("not backed by a current published record" in e for e in v.validate_readme(text, pubs, SLUG)))

    def test_download_link_must_be_labelled(self):
        url = v.asset_url(SLUG, "workbook-04-v1.0.0", "04-fixture-workbook.pdf")
        text = readme_for(self.pubs).replace(f"[Download PDF]({url})", f"[here]({url})")
        self.assertTrue(any("labelled 'Download PDF'" in e for e in v.validate_readme(text, self.pubs, SLUG)))

    def test_catalog_hides_ids_tags_and_checksums(self):
        for extra in (f"`{PDF_SHA}`", PDF_SHA, "`workbook-04`", "workbook-04-v1.0.0"):
            row = f"| **Workbook 04** {extra} | x | [Download PDF]({v.asset_url(SLUG, 'workbook-04-v1.0.0', '04-fixture-workbook.pdf')}) |"
            errs = v.validate_readme(readme_for(self.pubs, {"workbook-04": row}), self.pubs, SLUG)
            self.assertTrue(errs, msg=extra)

    def test_duplicate_catalog_row_fails(self):
        url = v.asset_url(SLUG, "workbook-04-v1.0.0", "04-fixture-workbook.pdf")
        row = f"| **Workbook 04** | x | [Download PDF]({url}) |\n| **Again** | x | [Download PDF]({url}) |"
        errs = v.validate_readme(readme_for(self.pubs, {"workbook-04": row}), self.pubs, SLUG)
        self.assertTrue(any("appears in 2" in e for e in errs))

    def test_link_before_publication_fails(self):
        pubs = {"workbook-04": record("04", status="canonical_built")}
        url = v.asset_url(SLUG, "workbook-04-v1.0.0", "04-fixture-workbook.pdf")
        # in the catalog...
        text = readme_for(pubs).replace("|---|---|---|\n", f"|---|---|---|\n| **Workbook 04** | x | [Download PDF]({url}) |\n")
        self.assertTrue(v.validate_readme(text, pubs, SLUG))
        # ...or in the in-progress block
        text = readme_for(pubs, progress={"workbook-04": f"In progress. [Download PDF]({url})"})
        errs = v.validate_readme(text, pubs, SLUG)
        self.assertTrue(any("in-progress block links a release asset" in e for e in errs))

    def test_unpublished_guide_must_not_appear_in_catalog(self):
        pubs = {"workbook-04": record("04"), "workbook-06": record("06", status="drafting")}
        row = f"| **Workbook 06** | soon | not yet |"
        text = readme_for(pubs).replace(f"{v.README_END}", f"{row}\n{v.README_END}")
        errs = v.validate_readme(text, pubs, SLUG)
        self.assertTrue(any("appears in the published catalog" in e for e in errs))
        self.assertTrue(any("no current published download link" in e for e in errs))

    def test_in_progress_entry_states_registry_chapter_progress(self):
        pubs = {"workbook-04": record("04"),
                "workbook-06": record("06", status="drafting", workbook_id="06-fixture")}
        good = readme_for(pubs, progress={"workbook-06": "In progress, 2 of 3 chapters accepted."})
        self.assertEqual(v.validate_readme(good, pubs, SLUG, WORKBOOKS), [])
        stale = readme_for(pubs, progress={"workbook-06": "In progress, 1 of 3 chapters accepted."})
        self.assertTrue(any("2 of 3 chapters" in e for e in v.validate_readme(stale, pubs, SLUG, WORKBOOKS)))
        missing = readme_for({"workbook-04": pubs["workbook-04"]})
        self.assertTrue(any("missing from the README in-progress block" in e
                            for e in v.validate_readme(missing, pubs, SLUG, WORKBOOKS)))
        self.assertEqual(v.chapter_progress(WORKBOOKS, "06-fixture"), (2, 3))
        self.assertIsNone(v.chapter_progress(WORKBOOKS, "absent"))

    def test_browser_links_only_after_verification(self):
        text = readme_for(self.pubs) + "\n[Read online](https://amartya-mitra.github.io/ml-llm-study-workbooks/)\n"
        self.assertTrue(any("before browser reading is verified" in e for e in v.validate_readme(text, self.pubs, SLUG)))
        prepared = {"verified": False, "base_url": "https://amartya-mitra.github.io/ml-llm-study-workbooks/"}
        self.assertTrue(v.validate_readme(text, self.pubs, SLUG, None, prepared))
        verified = dict(prepared, verified=True)
        self.assertEqual(v.validate_readme(text, self.pubs, SLUG, None, verified), [])
        other = readme_for(self.pubs) + "\n[Read online](https://someone.github.io/x/)\n"
        self.assertTrue(any("outside the verified site" in e for e in v.validate_readme(other, self.pubs, SLUG, None, verified)))

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


class VerificationDocTests(unittest.TestCase):
    def setUp(self):
        prev = {"status": "published", "version": "0.9.0", "page_count": 10, "sha256": "b" * 64,
                "release_tag": "workbook-04-v0.9.0", "release_asset": "04-fixture-workbook.pdf"}
        self.pubs = {"workbook-04": record("04", previous_releases=[prev]),
                     "workbook-05": record("05", status="drafting")}

    def test_every_published_edition_listed(self):
        self.assertEqual([e["release_tag"] for e in v.editions(self.pubs)],
                         ["workbook-04-v1.0.0", "workbook-04-v0.9.0"])
        self.assertEqual(v.validate_verification_doc(verification_for(self.pubs), self.pubs, SLUG), [])

    def test_missing_doc_edition_checksum_or_page_count_fails(self):
        doc = verification_for(self.pubs)
        self.assertTrue(v.validate_verification_doc(None, self.pubs, SLUG))
        dropped = "\n".join(l for l in doc.splitlines() if "v0.9.0`" not in l)
        self.assertTrue(any("workbook-04-v0.9.0" in e for e in v.validate_verification_doc(dropped, self.pubs, SLUG)))
        self.assertTrue(v.validate_verification_doc(doc.replace(PDF_SHA, "c" * 64), self.pubs, SLUG))
        self.assertTrue(any("page count" in e for e in v.validate_verification_doc(doc.replace("| 12 |", "| 13 |"), self.pubs, SLUG)))
        no_page = doc.replace(v.release_page_url(SLUG, "workbook-04-v1.0.0") + "\n", "")
        self.assertTrue(any("release page" in e for e in v.validate_verification_doc(no_page, self.pubs, SLUG)))


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

    def test_repository_readme_shows_registry_progress_and_no_unverified_site_links(self):
        from _yaml_lite import safe_load_path
        reg = safe_load_path(os.path.join(REPO_ROOT, "config", "chapter-status-registry.yaml"))
        with open(os.path.join(REPO_ROOT, "README.md"), encoding="utf-8") as f:
            readme = f.read()
        done, total = v.chapter_progress(reg["workbooks"], reg["publications"]["workbook-06"]["workbook_id"])
        block = v._block(readme, v.IN_PROGRESS_START, v.IN_PROGRESS_END)
        self.assertIn(f"{done} of {total} chapters", block)
        if not reg.get("browser_reading", {}).get("verified"):
            self.assertNotIn("github.io", readme)

    def test_no_canonical_pdf_is_tracked_in_this_repository(self):
        tracked = v.git_tracked_files(REPO_ROOT)
        if tracked is not None:
            self.assertEqual(v.tracked_canonical_pdfs(tracked), [])


if __name__ == "__main__":
    unittest.main()
