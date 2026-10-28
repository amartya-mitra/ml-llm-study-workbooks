#!/usr/bin/env python3
"""Validate publication metadata for workbooks and addenda.

Source of truth: the `publications:` section of
config/chapter-status-registry.yaml. See docs/publication-hygiene.md.

Modes
-----
default (offline, side-effect free)
    Checks registry metadata, README consistency (learner catalog and
    in-progress block), the edition/checksum verification document
    (docs/editions-and-verification.md) and that no canonical PDF is
    tracked by Git. Needs no network and no local PDFs, so a fresh
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


IN_PROGRESS_START, IN_PROGRESS_END = "<!-- in-progress:start -->", "<!-- in-progress:end -->"
VERIFICATION_DOC = os.path.join("docs", "editions-and-verification.md")
IN_PROGRESS_STATES = ("drafting", "review_pending", "accepted_frozen", "canonical_built")
DOWNLOAD_RE = re.compile(r"https://github\.com/[^\s)>\]]+/releases/download/[^\s)>\]]+")


def _block(text, start, end):
    if start not in text or end not in text:
        return None
    return text.split(start, 1)[1].split(end, 1)[0]


def editions(pubs):
    """Every published edition: the current one per record plus published previous_releases."""
    out = []
    for aid, rec in (pubs or {}).items():
        if not isinstance(rec, dict) or rec.get("status") != "published":
            continue
        out.append({"id": aid, "current": True, **{k: rec.get(k) for k in (
            "title", "version", "release_tag", "release_asset", "sha256", "page_count", "bytes", "release_url")}})
        for prev in rec.get("previous_releases") or []:
            if prev.get("status") == "published":
                out.append({"id": aid, "current": False, "title": rec.get("title"),
                            **{k: prev.get(k) for k in ("version", "release_tag", "release_asset", "sha256",
                                                         "page_count", "bytes", "release_url")}})
    return out


def parse_readme_catalog(text):
    """Learner catalog body rows (header and separator removed) between the catalog markers."""
    block = _block(text, README_START, README_END)
    if block is None:
        return None
    rows = [l for l in block.splitlines() if l.strip().startswith("|")]
    return [r for r in rows[2:] if not re.fullmatch(r"\|[\s:|-]*", r.strip())]


def chapter_progress(workbooks, workbook_id):
    """(accepted_frozen chapters, total chapters) for a workbook in the status registry, or None."""
    wb = (workbooks or {}).get(workbook_id)
    chapters = wb.get("chapters") if isinstance(wb, dict) else None
    if not isinstance(chapters, dict) or not chapters:
        return None
    done = sum(1 for c in chapters.values() if isinstance(c, dict) and c.get("status") == "accepted_frozen")
    return done, len(chapters)


def validate_readme(text, pubs, slug=DEFAULT_REPO_SLUG, workbooks=None, browser=None):
    """README integrity for the learner-facing layout.

    The catalog table lists published guides only, each with its exact
    current-edition release-asset link labelled "Download PDF" and no
    repository ids, tags or checksums; unpublished work appears only in the
    in-progress block, labelled "In progress", with chapter progress taken
    from the status registry; no README link points to an unpublished,
    previous, RC or development artifact; and browser-reading links appear
    only after the site is recorded as verified.
    """
    errors = []
    rows = parse_readme_catalog(text)
    if rows is None:
        return [f"README lacks the {README_START} ... {README_END} catalog block"]
    catalog = _block(text, README_START, README_END)
    current = {asset_url(slug, r.get("release_tag", ""), r.get("release_asset", "")): aid
               for aid, r in pubs.items() if isinstance(r, dict) and r.get("status") == "published"}
    seen = {}
    for row in rows:
        urls = [u for u in DOWNLOAD_RE.findall(row) if u in current]
        if not urls:
            errors.append("README catalog row has no current published download link "
                          f"(unpublished work belongs in the in-progress section): {row.strip()[:100]}")
        for url in urls:
            seen.setdefault(current[url], []).append(row)
            if not re.search(r"\[Download PDF[^\]]*\]\(" + re.escape(url) + r"\)", row):
                errors.append(f"[{current[url]}] catalog link must be labelled 'Download PDF': {url}")
    for url, aid in current.items():
        n = len(seen.get(aid, []))
        if n == 0:
            errors.append(f"[{aid}] missing from README catalog (needs the direct release-asset link {url})")
        elif n > 1:
            errors.append(f"[{aid}] appears in {n} README catalog rows")
    shown = DOWNLOAD_RE.sub("", catalog)
    if re.search(r"\b[0-9a-f]{64}\b", shown) or re.search(r"`(?:workbook|addendum)[A-Za-z0-9._-]*`", shown):
        errors.append("README catalog must not show checksums or repository ids (they belong in the verification document)")
    for aid, rec in pubs.items():
        tag = rec.get("release_tag") if isinstance(rec, dict) else None
        if tag and re.search(r"(?<![\w/-])" + re.escape(tag) + r"(?![\w-])", shown):
            errors.append(f"[{aid}] README catalog shows release tag {tag} outside its download link")
    for url in DOWNLOAD_RE.findall(text):
        if url not in current:
            errors.append(f"README contains a release-download link not backed by a current published record: {url}")
    progress = _block(text, IN_PROGRESS_START, IN_PROGRESS_END)
    for aid, rec in pubs.items():
        if not isinstance(rec, dict) or rec.get("status") not in IN_PROGRESS_STATES:
            continue
        title = str(rec.get("title") or "")
        if title and title in catalog:
            errors.append(f"[{aid}] unpublished guide {title!r} appears in the published catalog")
        if progress is None:
            errors.append(f"README lacks the {IN_PROGRESS_START} ... {IN_PROGRESS_END} block for unpublished work")
            continue
        lines = [l for l in progress.splitlines() if title and title in l]
        if not lines:
            errors.append(f"[{aid}] {title!r} missing from the README in-progress block")
            continue
        line = " ".join(lines)
        if "In progress" not in line or "Published" in line:
            errors.append(f"[{aid}] in-progress entry must read 'In progress', not published: {line[:100]}")
        prog = chapter_progress(workbooks, rec.get("workbook_id"))
        if prog is not None and f"{prog[0]} of {prog[1]} chapters" not in line:
            errors.append(f"[{aid}] in-progress entry must state '{prog[0]} of {prog[1]} chapters' "
                          f"(from the status registry); got: {line[:120]}")
    if progress is not None and "releases/download/" in progress:
        errors.append("README in-progress block links a release asset")
    # Prose may *name* these directories (output policy); links to them are rejected.
    if re.search(r"\]\([^)]*outputs/_(?:releases|development)/", text) or \
            re.search(r"https?://\S*(?:rc\d+|_releases|_development)\S*\.pdf", text):
        errors.append("README links RC/development artifacts")
    verified = isinstance(browser, dict) and browser.get("verified") is True and browser.get("base_url")
    for url in re.findall(r"\]\((https?://[^)\s]*github\.io[^)\s]*)\)", text):
        if not verified:
            errors.append(f"README shows a browser-reading link before browser reading is verified: {url}")
        elif not url.startswith(str(browser["base_url"])):
            errors.append(f"README browser-reading link {url} is outside the verified site {browser['base_url']}")
    if verified:
        # A catalog "Read in browser" link must open the same current edition
        # its row downloads, at the site's versioned path.
        base = str(browser["base_url"]).rstrip("/") + "/"
        for row in rows:
            reads = re.findall(r"\[Read in browser[^\]]*\]\(([^)\s]+)\)", row)
            for url in [u for u in DOWNLOAD_RE.findall(row) if u in current]:
                rec = pubs[current[url]]
                want = f"{base}editions/{rec['release_tag']}/{rec['release_asset']}"
                if reads and reads != [want]:
                    errors.append(f"[{current[url]}] 'Read in browser' must link {want}; got {reads}")
            for url in re.findall(r"https?://[^)\s]*github\.io[^)\s]*\.pdf", row):
                if not reads or url not in reads:
                    errors.append(f"README catalog links a site PDF without the 'Read in browser' label: {url}")
    return errors


def validate_verification_doc(text, pubs, slug=DEFAULT_REPO_SLUG):
    """Every published edition (current and previous) keeps its release tag,
    SHA-256, page count and release page in the verification document."""
    if text is None:
        return [f"{VERIFICATION_DOC} is missing"]
    errors = []
    for ed in editions(pubs):
        tag, sha = ed.get("release_tag"), ed.get("sha256")
        line = next((l for l in text.splitlines() if tag and sha and tag in l and sha in l), None)
        if line is None:
            errors.append(f"[{ed['id']}] {VERIFICATION_DOC} lacks a row with release tag {tag} and its SHA-256")
            continue
        if f"| {ed.get('page_count')} |" not in line:
            errors.append(f"[{ed['id']}] {VERIFICATION_DOC} row for {tag} lacks page count {ed.get('page_count')}")
        if release_page_url(slug, tag) not in text:
            errors.append(f"[{ed['id']}] {VERIFICATION_DOC} lacks the release page {release_page_url(slug, tag)}")
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
    registry = safe_load_path(reg_path) or {}
    pubs = registry.get("publications")
    with open(os.path.join(args.root, "README.md"), encoding="utf-8") as f:
        readme = f.read()
    vpath = os.path.join(args.root, VERIFICATION_DOC)
    vdoc = None
    if os.path.isfile(vpath):
        with open(vpath, encoding="utf-8") as f:
            vdoc = f.read()

    offline = validate_registry(pubs, raw, args.repo_slug)
    if isinstance(pubs, dict):
        offline += validate_readme(readme, pubs, args.repo_slug, registry.get("workbooks"),
                                   registry.get("browser_reading"))
        offline += validate_verification_doc(vdoc, pubs, args.repo_slug)
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
