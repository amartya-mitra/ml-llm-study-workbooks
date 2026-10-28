#!/usr/bin/env python3
"""GitHub Release helper for the TSFM addendum (REST API, no gh CLI).

    python3 scripts/publish_addendum_release.py check   [--version 1.1.0]
    python3 scripts/publish_addendum_release.py draft   [--version 1.1.0]
    python3 scripts/publish_addendum_release.py publish [--version 1.1.0]
    python3 scripts/publish_addendum_release.py verify  [--version 1.1.0] [EXPECTED_COMMIT]

The token is read from the GH_TOKEN (or GITHUB_TOKEN) environment variable
only; it is never printed, logged, written to a file or placed in a command
argument. One foreground process, sequential requests.

Expected identity (tag, title, SHA-256, page count) comes from the
`publications.addendum-04-05-tsfm` record of config/chapter-status-registry.yaml
for the current edition; v1.0.0 values are kept here only for read-only
verification of the earlier release.

  check   - authenticated repo access with push permission; reports whether
            the tag and a release for it exist; local PDF matches the record.
  draft   - for the ALREADY PUSHED tag: create a DRAFT release (or reuse an
            existing draft with this exact tag/title and no conflicting
            asset), upload exactly one asset (the canonical PDF) if absent,
            then download the draft asset with authentication and confirm it
            matches the local PDF (SHA-256, size). Never touches a published
            release.
  publish - flip the verified draft to a public, non-prerelease release.
            Refuses unless the draft carries exactly the expected asset.
  verify  - read-only: release is public, not draft/prerelease, exactly one
            asset with the expected name/size, the tag is annotated and
            resolves to EXPECTED_COMMIT, and a fresh anonymous download
            matches the local PDF (SHA-256, size, page count, edition line).
Never edits, replaces or deletes an existing published release or asset.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from _yaml_lite import safe_load_path  # noqa: E402

REPO = "amartya-mitra/ml-llm-study-workbooks"
WB = "addendum-04-05-tsfm"
ASSET = f"{WB}.pdf"
PDF = os.path.join(REPO_ROOT, "outputs", ASSET)
API = "https://api.github.com"
V1_0_0 = {  # historical, read-only verification of the earlier release
    "tag": f"{WB}-v1.0.0", "title": "Addendum 04–05 v1.0.0 — Time-Series Foundation Models",
    "sha256": "b7096e9b9291dc4319f8f3740303b42dcf784d3ec80bb2fb63cc66f7ac242b65",
    "bytes": 425777, "pages": 18, "edition_line": "Final Edition",
    "pdf": os.path.join(REPO_ROOT, "outputs", "_development", WB, "v1.0.0-canonical-archive", f"{WB}-v1.0.0.pdf"),
}
NOTES_FILE = os.path.join(REPO_ROOT, "reports", "addendum_04_05_tsfm_v1_1_0_release_notes.md")


def edition(version):
    if version == "1.0.0":
        return dict(V1_0_0)
    rec = safe_load_path(os.path.join(REPO_ROOT, "config", "chapter-status-registry.yaml"))["publications"][WB]
    if rec.get("version") != version:
        sys.exit(f"BLOCKED: the registry's current edition is {rec.get('version')!r}, not {version!r}")
    for field in ("release_tag", "release_title", "sha256", "page_count", "source_commit"):
        if not rec.get(field):
            sys.exit(f"BLOCKED: registry record lacks {field!r} (record canonical_built metadata first)")
    return {"tag": rec["release_tag"], "title": rec["release_title"], "sha256": rec["sha256"],
            "bytes": None, "pages": rec["page_count"], "edition_line": f"Final Edition, version {version}",
            "pdf": PDF, "source_commit": rec["source_commit"]}


def token():
    t = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not t:
        sys.exit("BLOCKED: no GH_TOKEN or GITHUB_TOKEN in the environment")
    return t


def call(method, url, data=None, content_type="application/json", accept="application/vnd.github+json"):
    headers = {"Authorization": "Bearer " + token(), "Accept": accept, "User-Agent": "tsfm-addendum-publisher",
               "X-GitHub-Api-Version": "2022-11-28"}
    body = None
    if data is not None:
        body = data if isinstance(data, bytes) else json.dumps(data).encode()
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    with open(path, "rb") as f:
        return sha_bytes(f.read())


def local_gate(ed):
    if not os.path.exists(ed["pdf"]):
        sys.exit("BLOCKED: local PDF missing")
    if sha(ed["pdf"]) != ed["sha256"] or (ed["bytes"] is not None and os.path.getsize(ed["pdf"]) != ed["bytes"]):
        sys.exit("BLOCKED: local PDF does not match the recorded SHA-256/size")


def tag_state(tag):
    code, body = call("GET", f"{API}/repos/{REPO}/git/ref/tags/{tag}")
    return code, (json.loads(body) if code == 200 else None)


def releases_for(tag):
    """All releases (including drafts, which /releases/tags/ does not return) for a tag."""
    code, body = call("GET", f"{API}/repos/{REPO}/releases?per_page=100")
    if code != 200:
        sys.exit(f"BLOCKED: listing releases returned HTTP {code}")
    return [r for r in json.loads(body) if r.get("tag_name") == tag]


def cmd_check(ed):
    code, body = call("GET", f"{API}/repos/{REPO}")
    if code != 200:
        sys.exit(f"BLOCKED: repository access returned HTTP {code}")
    info = json.loads(body)
    perms = info.get("permissions") or {}
    print("repository:", info.get("full_name"), "| private:", info.get("private"),
          "| push permission:", perms.get("push"))
    if not perms.get("push"):
        sys.exit("BLOCKED: the token cannot push (needed to create releases and upload assets)")
    tc, _ = tag_state(ed["tag"])
    rels = releases_for(ed["tag"])
    print("remote tag exists:", tc == 200, "| releases for tag:",
          [(r["id"], r["draft"], r["prerelease"], [a["name"] for a in r.get("assets", [])]) for r in rels])
    local_gate(ed)
    print("local PDF matches the recorded SHA-256")
    print("CHECK OK")


def download_asset_authenticated(asset):
    code, data = call("GET", asset["url"], accept="application/octet-stream")
    if code != 200:
        sys.exit(f"BLOCKED: authenticated asset download returned HTTP {code}")
    return data


def cmd_draft(ed):
    local_gate(ed)
    tc, _ = tag_state(ed["tag"])
    if tc != 200:
        sys.exit("BLOCKED: the tag has not been pushed")
    rels = releases_for(ed["tag"])
    if any(not r["draft"] for r in rels):
        sys.exit("BLOCKED: a published release for this tag already exists; never modify it")
    if len(rels) > 1:
        sys.exit("BLOCKED: more than one draft exists for this tag; resolve by hand")
    if rels:
        rel = rels[0]
        if rel.get("name") != ed["title"]:
            sys.exit(f"BLOCKED: existing draft has a different title {rel.get('name')!r}")
        print("reusing existing draft release", rel["id"])
    else:
        with open(NOTES_FILE, encoding="utf-8") as f:
            notes = f.read()
        code, body = call("POST", f"{API}/repos/{REPO}/releases", {
            "tag_name": ed["tag"], "name": ed["title"], "body": notes, "draft": True, "prerelease": False})
        if code != 201:
            sys.exit(f"BLOCKED: draft creation returned HTTP {code}: {body[:300].decode(errors='replace')}")
        rel = json.loads(body)
        print("draft release created:", rel["id"])
    assets = rel.get("assets") or []
    if any(a["name"] != ASSET for a in assets):
        sys.exit(f"BLOCKED: draft carries unexpected assets {[a['name'] for a in assets]}")
    if not assets:
        upload = rel["upload_url"].split("{")[0] + f"?name={ASSET}"
        with open(PDF, "rb") as f:
            data = f.read()
        code, body = call("POST", upload, data, content_type="application/pdf")
        if code != 201:
            sys.exit(f"UPLOAD FAILED: HTTP {code}: {body[:300].decode(errors='replace')} (draft kept; report)")
        asset = json.loads(body)
        print("asset uploaded:", asset["name"], asset["size"], "bytes")
    else:
        asset = assets[0]
        print("asset already present on draft:", asset["name"], asset["size"], "bytes")
    got = download_asset_authenticated(asset)
    ok = sha_bytes(got) == ed["sha256"] == sha(PDF) and len(got) == os.path.getsize(PDF) == asset["size"]
    print("draft asset download:", len(got), "bytes | sha256", sha_bytes(got), "| matches local:", ok)
    if not ok:
        sys.exit("FAIL: draft asset does not match the local canonical PDF; draft left unpublished")
    print("DRAFT OK (release id", rel["id"], ")")


def cmd_publish(ed):
    rels = releases_for(ed["tag"])
    if any(not r["draft"] for r in rels):
        sys.exit("ALREADY PUBLISHED: a public release exists for this tag; nothing changed")
    if len(rels) != 1:
        sys.exit(f"BLOCKED: expected exactly one draft, found {len(rels)}")
    rel = rels[0]
    names = [a["name"] for a in rel.get("assets") or []]
    if names != [ASSET] or rel.get("name") != ed["title"]:
        sys.exit(f"BLOCKED: draft title/assets do not match ({rel.get('name')!r}, {names})")
    code, body = call("PATCH", f"{API}/repos/{REPO}/releases/{rel['id']}", {"draft": False, "prerelease": False})
    if code != 200:
        sys.exit(f"BLOCKED: publishing returned HTTP {code}: {body[:300].decode(errors='replace')}")
    out = json.loads(body)
    print("published:", out["html_url"], "| draft:", out["draft"], "| prerelease:", out["prerelease"])


def cmd_verify(ed, expected_commit=None):
    code, body = call("GET", f"{API}/repos/{REPO}/releases/tags/{ed['tag']}")
    if code != 200:
        sys.exit("FAIL: public release not found")
    rel = json.loads(body)
    problems = []
    if rel.get("draft"):
        problems.append("release is a draft")
    if rel.get("prerelease"):
        problems.append("release is a prerelease")
    if rel.get("name") != ed["title"]:
        problems.append(f"release title is {rel.get('name')!r}")
    assets = rel.get("assets") or []
    names = [a["name"] for a in assets]
    if names != [ASSET]:
        problems.append(f"assets are {names}, expected exactly [{ASSET!r}]")
    print("release:", rel.get("html_url"), "| draft:", rel.get("draft"), "| prerelease:", rel.get("prerelease"),
          "| published_at:", rel.get("published_at"))
    print("assets:", [(a["name"], a["size"], a["state"]) for a in assets])
    if assets:
        a = assets[0]
        url = a["browser_download_url"]
        print("direct asset URL:", url)
        req = urllib.request.Request(url, headers={"User-Agent": "tsfm-addendum-publisher"})
        with urllib.request.urlopen(req, timeout=120) as r:  # anonymous public download, no token
            data = r.read()
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, ASSET)
            with open(p, "wb") as f:
                f.write(data)
            got = sha_bytes(data)
            info = subprocess.run(["pdfinfo", p], capture_output=True, text=True).stdout
            pages = int(re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE).group(1))
            first = re.sub(r"\s+", " ", subprocess.run(["pdftotext", "-f", "1", "-l", "1", p, "-"],
                                                       capture_output=True, text=True).stdout)
        print("downloaded:", len(data), "bytes | sha256", got, "| pages", pages,
              f"| {ed['edition_line']!r} on p.1:", ed["edition_line"] in first)
        if got != ed["sha256"] or got != sha(ed["pdf"]):
            problems.append("downloaded SHA-256 differs from the local canonical PDF")
        if len(data) != os.path.getsize(ed["pdf"]) or a["size"] != len(data):
            problems.append("downloaded size differs from the local PDF or the asset size field")
        if pages != ed["pages"]:
            problems.append(f"downloaded page count {pages} != {ed['pages']}")
        if ed["edition_line"] not in first:
            problems.append(f"title page lacks {ed['edition_line']!r}")
    tcode, tref = tag_state(ed["tag"])
    if tcode != 200:
        problems.append("tag ref not found")
    else:
        obj = tref["object"]
        commit = obj["sha"]
        if obj["type"] == "tag":  # annotated: dereference
            _, b2 = call("GET", f"{API}/repos/{REPO}/git/tags/{obj['sha']}")
            commit = json.loads(b2)["object"]["sha"]
            print("tag type: annotated")
        else:
            problems.append("tag is lightweight, not annotated")
        print("tag", ed["tag"], "->", commit)
        if expected_commit and commit != expected_commit:
            problems.append(f"tag target {commit} != expected {expected_commit}")
    print("VERIFY", "OK" if not problems else "FAILED: " + "; ".join(problems))
    sys.exit(0 if not problems else 1)


def main(argv):
    if not argv or argv[0] not in ("check", "draft", "publish", "verify"):
        sys.exit(__doc__)
    cmd, rest = argv[0], argv[1:]
    version = "1.1.0"
    if rest[:1] == ["--version"]:
        version, rest = rest[1], rest[2:]
    ed = edition(version)
    if cmd == "verify":
        cmd_verify(ed, rest[0] if rest else ed.get("source_commit"))
    elif version == "1.0.0":
        sys.exit("BLOCKED: v1.0.0 is published; only read-only verify is allowed")
    else:
        {"check": cmd_check, "draft": cmd_draft, "publish": cmd_publish}[cmd](ed)


if __name__ == "__main__":
    main(sys.argv[1:])
