#!/usr/bin/env python3
"""Validate publication metadata for workbooks and addenda.

Source of truth: the `publications:` section of
config/chapter-status-registry.yaml. See docs/publication-hygiene.md.

Modes
-----
default (offline, side-effect free)
    Checks registry metadata, README consistency and that no canonical
    PDF is tracked by Git. Needs no network and no local PDFs, so a fresh
    clone passes.
--check-local
    Additionally verifies page count and SHA-256 of each canonical PDF that
    is present on disk. Absence is a warning, unless --require-local.
--remote
    Read-only GitHub checks (GET only) for the release, its single asset
    and the downloaded asset's SHA-256. Reported separately from offline
    results. Creates, modifies and deletes nothing.

Exit status: 0 all requested checks passed; 1 offline/local failure;
2 remote failure (only when offline checks passed).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from _yaml_lite import safe_load_path  # noqa: E402

DEFAULT_REPO_SLUG = "amartya-mitra/ml-llm-study-workbooks"
LIFECYCLE = ["planned", "drafting", "review_pending", "accepted_frozen",
             "canonical_built", "published"]
STATUS_LABEL = {  # exact README status text for each lifecycle state
    "planned": "Planned",
    "drafting": "Drafting",
    "review_pending": "Review pending",
    "accepted_frozen": "Accepted (frozen)",
    "canonical_built": "Release pending",
    "published": "Published",
}
PREPARED_FIELDS = ["title", "canonical_path", "page_count", "sha256", "source_commit",
                   "release_tag", "release_asset", "release_url", "reproduction_command"]
PUBLISHED_EXTRA = ["publication_date", "human_acceptance"]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
TAG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-v\d+\.\d+\.\d+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FORBIDDEN_NAME_RE = re.compile(r"(?:^|[-_.])(rc\d*|review|draft|superseded|dev|development|pages?)(?:[-_.]|$)", re.I)
README_START, README_END = "<!-- publication-catalog:start -->", "<!-- publication-catalog:end -->"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pdf_page_count(path):
    try:
        out = subprocess.run(["pdfinfo", path], capture_output=True, text=True, check=True).stdout
        m = re.search(r"^Pages:\s+(\d+)", out, re.M)
        if m:
            return int(m.group(1))
    except (OSError, subprocess.CalledProcessError):
        pass
    with open(path, "rb") as f:  # crude fallback: count page objects
        return len(re.findall(rb"/Type\s*/Page[^s]", f.read()))


def asset_url(slug, tag, asset):
    return f"https://github.com/{slug}/releases/download/{tag}/{asset}"


def release_page_url(slug, tag):
    return f"https://github.com/{slug}/releases/tag/{tag}"


def duplicate_artifact_ids(raw_text):
    """Duplicate keys under `publications:` (a YAML loader would silently keep the last)."""
    ids, in_pub = [], False
    for line in raw_text.splitlines():
        if re.match(r"^publications:\s*(#.*)?$", line):
            in_pub = True
            continue
        if in_pub and re.match(r"^\S", line) and not line.startswith("#"):
            in_pub = False
        if in_pub:
            m = re.match(r"^  ([A-Za-z0-9._-]+):\s*$", line)
            if m:
                ids.append(m.group(1))
    return sorted({i for i in ids if ids.count(i) > 1})


def validate_registry(pubs, raw_text="", slug=DEFAULT_REPO_SLUG):
    errors = []
    if not isinstance(pubs, dict) or not pubs:
        return ["registry has no `publications:` records"]
    for dup in duplicate_artifact_ids(raw_text):
        errors.append(f"duplicate artifact id: {dup}")
    tags, assets = {}, {}
    for aid, rec in pubs.items():
        p = f"[{aid}]"
        if not isinstance(rec, dict):
            errors.append(f"{p} record is not a mapping")
            continue
        status = rec.get("status")
        if status not in LIFECYCLE:
            errors.append(f"{p} status {status!r} not in {LIFECYCLE}")
            continue
        published = status == "published"
        prepared = LIFECYCLE.index(status) >= LIFECYCLE.index("canonical_built")
        required = (PREPARED_FIELDS if prepared else []) + (PUBLISHED_EXTRA if published else [])
        for field in required:
            if rec.get(field) in (None, "", [], {}):
                errors.append(f"{p} status {status!r} requires metadata field {field!r}")
        if rec.get("sha256") is not None and not SHA256_RE.match(str(rec["sha256"])):
            errors.append(f"{p} sha256 must be 64 lowercase hex characters")
        pc = rec.get("page_count")
        if pc is not None and (isinstance(pc, bool) or not isinstance(pc, int) or pc <= 0):
            errors.append(f"{p} page_count must be a positive integer")
        sc = rec.get("source_commit")
        if sc is not None and not COMMIT_RE.match(str(sc)):
            errors.append(f"{p} source_commit must be a full 40-hex commit SHA")
        tag, asset = rec.get("release_tag"), rec.get("release_asset")
        if tag is not None:
            if not TAG_RE.match(str(tag)):
                errors.append(f"{p} release_tag {tag!r} must look like <name>-vMAJOR.MINOR.PATCH")
            if tag in tags:
                errors.append(f"{p} release_tag {tag!r} duplicates {tags[tag]}")
            tags.setdefault(tag, aid)
        if asset is not None:
            if not str(asset).endswith(".pdf") or "/" in str(asset):
                errors.append(f"{p} release_asset must be a bare .pdf filename")
            if FORBIDDEN_NAME_RE.search(str(asset)):
                errors.append(f"{p} release_asset {asset!r} looks like an RC/review/development artifact")
            if asset in assets:
                errors.append(f"{p} release_asset {asset!r} duplicates {assets[asset]}")
            assets.setdefault(asset, aid)
        cp = rec.get("canonical_path")
        if cp is not None:
            cps = str(cp)
            if not re.fullmatch(r"outputs/[^/]+\.pdf", cps) or FORBIDDEN_NAME_RE.search(os.path.basename(cps)):
                errors.append(f"{p} canonical_path {cps!r} must be outputs/<canonical>.pdf (no RC/dev/_releases paths)")
            if asset is not None and os.path.basename(cps) != str(asset):
                errors.append(f"{p} canonical_path filename must equal release_asset")
        if tag is not None and rec.get("release_url") is not None:
            if rec["release_url"] != release_page_url(slug, tag):
                errors.append(f"{p} release_url must be {release_page_url(slug, tag)}")
        pd = rec.get("publication_date")
        if published and pd is not None and not DATE_RE.match(str(pd)):
            errors.append(f"{p} publication_date must be YYYY-MM-DD")
        if not published and pd not in (None, ""):
            errors.append(f"{p} publication_date set but status is {status!r}, not 'published'")
        ha = rec.get("human_acceptance")
        if published or (prepared and ha is not None):
            if not isinstance(ha, dict) or ha.get("accepted") is not True or not ha.get("date"):
                errors.append(f"{p} human_acceptance must record accepted: true and a date")
    return errors


def parse_readme_catalog(text):
    if README_START not in text or README_END not in text:
        return None
    block = text.split(README_START, 1)[1].split(README_END, 1)[0]
    rows = {}
    for line in block.splitlines():
        m = re.search(r"`((?:workbook|addendum)[A-Za-z0-9._-]*)`", line)
        if line.strip().startswith("|") and m:
            rows[m.group(1)] = line
    return rows


def validate_readme(text, pubs, slug=DEFAULT_REPO_SLUG):
    errors = []
    rows = parse_readme_catalog(text)
    if rows is None:
        return [f"README lacks the {README_START} ... {README_END} catalog block"]
    for aid, rec in pubs.items():
        status = rec.get("status")
        row = rows.get(aid)
        if row is None:
            errors.append(f"[{aid}] missing from README catalog")
            continue
        label = STATUS_LABEL.get(status)
        cells = [c.strip().strip("*") for c in row.strip().strip("|").split("|")]
        if label is None or label not in cells:
            errors.append(f"[{aid}] README status must read {label!r} (registry status {status!r}); row: {row.strip()[:120]}")
        direct = asset_url(slug, rec.get("release_tag", ""), rec.get("release_asset", ""))
        if status == "published":
            if direct not in row:
                errors.append(f"[{aid}] README row lacks the direct release-asset link {direct}")
            if str(rec.get("page_count")) not in row:
                errors.append(f"[{aid}] README row lacks page count {rec.get('page_count')}")
            if str(rec.get("release_tag")) not in row:
                errors.append(f"[{aid}] README row lacks release tag {rec.get('release_tag')}")
        else:
            if "releases/download/" in row:
                errors.append(f"[{aid}] README links a release asset but registry status is {status!r}")
    for aid in rows:
        if aid not in pubs:
            errors.append(f"README catalog row [{aid}] has no registry record")
    published_urls = {asset_url(slug, r.get("release_tag", ""), r.get("release_asset", ""))
                      for r in pubs.values() if r.get("status") == "published"}
    for url in re.findall(r"https://github\.com/[^\s)>\]]+/releases/download/[^\s)>\]]+", text):
        if url not in published_urls:
            errors.append(f"README contains a release-download link not backed by a published record: {url}")
    # Prose may *name* these directories (output policy); links to them are rejected.
    if re.search(r"\]\([^)]*outputs/_(?:releases|development)/", text) or \
            re.search(r"https?://\S*(?:rc\d+|_releases|_development)\S*\.pdf", text):
        errors.append("README links RC/development artifacts")
    return errors


def tracked_canonical_pdfs(tracked_files):
    return [f for f in tracked_files if re.fullmatch(r"outputs/.*\.pdf", f)]


def git_tracked_files(root):
    try:
        out = subprocess.run(["git", "-C", root, "ls-files", "outputs"], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return [l for l in out.splitlines() if l]


def check_local_artifact(rec, root, require=False, page_fn=pdf_page_count):
    """Returns (errors, warnings)."""
    path = os.path.join(root, rec.get("canonical_path", ""))
    if not os.path.isfile(path):
        msg = f"local canonical PDF absent: {rec.get('canonical_path')}"
        return ([msg], []) if require else ([], [msg + " (ignored build product; fine on a clean clone)"])
    errs = []
    got = sha256_file(path)
    if got != rec.get("sha256"):
        errs.append(f"local SHA-256 mismatch for {rec.get('canonical_path')}: {got} != {rec.get('sha256')}")
    pages = page_fn(path)
    if pages != rec.get("page_count"):
        errs.append(f"local page count mismatch for {rec.get('canonical_path')}: {pages} != {rec.get('page_count')}")
    return errs, []


def verify_release_payload(release, rec, slug, download_fn):
    """Pure parsing/verification of a GitHub release JSON payload (no I/O of its own)."""
    errs = []
    if release.get("tag_name") != rec["release_tag"]:
        errs.append(f"release tag_name {release.get('tag_name')!r} != {rec['release_tag']!r}")
    if release.get("draft"):
        errs.append("release is a draft")
    if release.get("prerelease"):
        errs.append("release is a prerelease")
    assets = release.get("assets") or []
    names = [a.get("name") for a in assets]
    if names != [rec["release_asset"]]:
        errs.append(f"release must carry exactly one asset {rec['release_asset']!r}; found {names}")
        return errs
    expected_url = asset_url(slug, rec["release_tag"], rec["release_asset"])
    if assets[0].get("browser_download_url") != expected_url:
        errs.append(f"asset download URL {assets[0].get('browser_download_url')!r} != {expected_url!r}")
    data = download_fn(assets[0].get("browser_download_url"))
    got = hashlib.sha256(data).hexdigest()
    if got != rec["sha256"]:
        errs.append(f"downloaded asset SHA-256 {got} != recorded {rec['sha256']}")
    if assets[0].get("size") is not None and assets[0]["size"] != len(data):
        errs.append(f"asset size field {assets[0]['size']} != downloaded bytes {len(data)}")
    return errs


def _http_get(url, accept=None):
    req = urllib.request.Request(url, headers={"User-Agent": "publication-hygiene-validator",
                                               **({"Accept": accept} if accept else {})})
    with urllib.request.urlopen(req, timeout=60) as r:  # GET only
        return r.read()


def remote_check(pubs, slug, get=_http_get):
    """Read-only. Returns (errors, notes)."""
    errors, notes = [], []
    for aid, rec in pubs.items():
        if rec.get("status") != "published":
            notes.append(f"[{aid}] status {rec.get('status')!r}: remote release not required yet")
            continue
        api = f"https://api.github.com/repos/{slug}/releases/tags/{rec['release_tag']}"
        try:
            release = json.loads(get(api, "application/vnd.github+json"))
        except urllib.error.HTTPError as e:
            errors.append(f"[{aid}] release lookup failed: HTTP {e.code} for {api}")
            continue
        except (urllib.error.URLError, ValueError) as e:
            errors.append(f"[{aid}] release lookup failed: {e}")
            continue
        try:
            errs = verify_release_payload(release, rec, slug, get)
        except (urllib.error.URLError, ValueError) as e:
            errs = [f"asset download failed: {e}"]
        errors.extend(f"[{aid}] {e}" for e in errs)
        if not errs:
            notes.append(f"[{aid}] remote release, single asset and SHA-256 verified")
    return errors, notes


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", default=REPO_ROOT)
    ap.add_argument("--repo-slug", default=DEFAULT_REPO_SLUG)
    ap.add_argument("--check-local", action="store_true", help="verify local canonical PDFs when present")
    ap.add_argument("--require-local", action="store_true", help="with --check-local: absence is a failure")
    ap.add_argument("--remote", action="store_true", help="read-only GitHub verification (network)")
    args = ap.parse_args(argv)

    reg_path = os.path.join(args.root, "config", "chapter-status-registry.yaml")
    with open(reg_path, encoding="utf-8") as f:
        raw = f.read()
    pubs = (safe_load_path(reg_path) or {}).get("publications")
    with open(os.path.join(args.root, "README.md"), encoding="utf-8") as f:
        readme = f.read()

    offline = validate_registry(pubs, raw, args.repo_slug)
    if isinstance(pubs, dict):
        offline += validate_readme(readme, pubs, args.repo_slug)
    tracked = git_tracked_files(args.root)
    if tracked is not None:
        offline += [f"canonical/RC PDF is tracked by Git (must stay untracked): {p}" for p in tracked_canonical_pdfs(tracked)]
    warnings = []
    if args.check_local and isinstance(pubs, dict):
        for aid, rec in pubs.items():
            if rec.get("status") not in LIFECYCLE or \
                    LIFECYCLE.index(rec["status"]) < LIFECYCLE.index("canonical_built"):
                continue  # nothing built yet
            e, w = check_local_artifact(rec, args.root, require=args.require_local)
            offline += [f"[{aid}] {x}" for x in e]
            warnings += [f"[{aid}] {x}" for x in w]

    print("== OFFLINE VALIDATION ==")
    for w in warnings:
        print("  warn:", w)
    for e in offline:
        print("  FAIL:", e)
    print("  result:", "FAIL" if offline else "OK", f"({len(pubs or {})} publication record(s))")
    if offline:
        return 1
    if args.remote:
        errors, notes = remote_check(pubs, args.repo_slug)
        print("== REMOTE VERIFICATION (read-only) ==")
        for n in notes:
            print("  note:", n)
        for e in errors:
            print("  FAIL:", e)
        print("  result:", "FAIL" if errors else "OK")
        return 2 if errors else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
