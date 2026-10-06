#!/usr/bin/env python3
"""GitHub Release helper for the TSFM addendum (REST API, no gh CLI).

    python3 scripts/publish_addendum_release.py check
    python3 scripts/publish_addendum_release.py create
    python3 scripts/publish_addendum_release.py verify

The token is read from the GH_TOKEN (or GITHUB_TOKEN) environment variable
only; it is never printed, logged, written to a file or placed in a command
argument. One foreground process, sequential requests.

  check   - authenticated repo access with push permission; the tag and the
            release do not exist yet.
  create  - create a public (non-draft, non-prerelease) release for the
            ALREADY PUSHED tag and upload exactly one asset, the canonical
            PDF. Refuses if the tag is missing, a release exists, or the
            local PDF does not match the recorded SHA-256.
  verify  - read-only: release is public, not draft/prerelease, exactly one
            asset with the expected name/size, the tag resolves to the
            expected commit, and a fresh download matches the local PDF
            (SHA-256, size, page count, "Final Edition" on the title page).
Never edits or replaces an existing release or asset.
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

REPO = "amartya-mitra/ml-llm-study-workbooks"
TAG = "addendum-04-05-tsfm-v1.0.0"
TITLE = "Addendum 04–05 v1.0.0 — Time-Series Foundation Models"
ASSET = "addendum-04-05-tsfm.pdf"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PDF = os.path.join(REPO_ROOT, "outputs", ASSET)
EXPECTED_SHA = "b7096e9b9291dc4319f8f3740303b42dcf784d3ec80bb2fb63cc66f7ac242b65"
EXPECTED_BYTES = 425777
EXPECTED_PAGES = 18
API = "https://api.github.com"
BODY = ("Addendum 04–05, Time-Series Foundation Models, version 1.0.0 (Final Edition, 18 pages). "
        f"SHA-256 of the attached PDF: {EXPECTED_SHA}.")


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


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def local_gate():
    if not os.path.exists(PDF):
        sys.exit("BLOCKED: canonical PDF missing")
    if sha(PDF) != EXPECTED_SHA or os.path.getsize(PDF) != EXPECTED_BYTES:
        sys.exit("BLOCKED: canonical PDF does not match the recorded SHA-256/size")


def tag_state():
    code, body = call("GET", f"{API}/repos/{REPO}/git/ref/tags/{TAG}")
    return code, (json.loads(body) if code == 200 else None)


def release_state():
    code, body = call("GET", f"{API}/repos/{REPO}/releases/tags/{TAG}")
    return code, (json.loads(body) if code == 200 else None)


def cmd_check():
    code, body = call("GET", f"{API}/repos/{REPO}")
    if code != 200:
        sys.exit(f"BLOCKED: repository access returned HTTP {code}")
    info = json.loads(body)
    perms = info.get("permissions") or {}
    print("repository:", info.get("full_name"), "| private:", info.get("private"),
          "| push permission:", perms.get("push"))
    if not perms.get("push"):
        sys.exit("BLOCKED: the token cannot push (needed to create releases and upload assets)")
    tc, _ = tag_state()
    rc, _ = release_state()
    print("remote tag exists:", tc == 200, "| release exists:", rc == 200)
    if tc == 200 or rc == 200:
        sys.exit("BLOCKED: tag or release already exists; never replace one")
    local_gate()
    print("local canonical PDF matches the recorded SHA-256 and size")
    print("CHECK OK")


def cmd_create():
    local_gate()
    tc, _ = tag_state()
    if tc != 200:
        sys.exit("BLOCKED: the tag has not been pushed")
    rc, _ = release_state()
    if rc == 200:
        sys.exit("BLOCKED: a release for this tag already exists")
    code, body = call("POST", f"{API}/repos/{REPO}/releases", {
        "tag_name": TAG, "name": TITLE, "body": BODY, "draft": False, "prerelease": False})
    if code != 201:
        sys.exit(f"BLOCKED: release creation returned HTTP {code}: {body[:300].decode(errors='replace')}")
    rel = json.loads(body)
    upload = rel["upload_url"].split("{")[0] + f"?name={ASSET}"
    with open(PDF, "rb") as f:
        data = f.read()
    code, body = call("POST", upload, data, content_type="application/pdf")
    if code != 201:
        sys.exit(f"UPLOAD FAILED: HTTP {code}: {body[:300].decode(errors='replace')} "
                 "(the release exists without its asset; do not publish; report)")
    print("release created:", rel["html_url"])
    print("asset uploaded:", ASSET)


def cmd_verify(expected_commit=None):
    code, rel = release_state()
    problems = []
    if code != 200:
        sys.exit("FAIL: release not found")
    if rel.get("draft"):
        problems.append("release is a draft")
    if rel.get("prerelease"):
        problems.append("release is a prerelease")
    if rel.get("name") != TITLE:
        problems.append(f"release title is {rel.get('name')!r}")
    assets = rel.get("assets") or []
    names = [a["name"] for a in assets]
    if names != [ASSET]:
        problems.append(f"assets are {names}, expected exactly [{ASSET!r}]")
    print("release:", rel.get("html_url"), "| draft:", rel.get("draft"), "| prerelease:", rel.get("prerelease"))
    print("assets:", [(a["name"], a["size"], a["state"]) for a in assets])
    if assets:
        a = assets[0]
        if a["size"] != EXPECTED_BYTES:
            problems.append(f"asset size {a['size']} != {EXPECTED_BYTES}")
        url = a["browser_download_url"]
        print("direct asset URL:", url)
        req = urllib.request.Request(url, headers={"User-Agent": "tsfm-addendum-publisher"})
        with urllib.request.urlopen(req, timeout=120) as r:  # public download, no token
            data = r.read()
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, ASSET)
            with open(p, "wb") as f:
                f.write(data)
            got = hashlib.sha256(data).hexdigest()
            info = subprocess.run(["pdfinfo", p], capture_output=True, text=True).stdout
            pages = int(re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE).group(1))
            first = subprocess.run(["pdftotext", "-f", "1", "-l", "1", p, "-"], capture_output=True, text=True).stdout
        print("downloaded:", len(data), "bytes | sha256", got, "| pages", pages, "| 'Final Edition' on p.1:", "Final Edition" in first)
        if got != EXPECTED_SHA or got != sha(PDF):
            problems.append("downloaded SHA-256 differs from the canonical local PDF")
        if len(data) != os.path.getsize(PDF):
            problems.append("downloaded size differs from the local PDF")
        if pages != EXPECTED_PAGES:
            problems.append(f"downloaded page count {pages} != {EXPECTED_PAGES}")
        if "Final Edition" not in first:
            problems.append("title page lacks 'Final Edition'")
    tcode, tref = tag_state()
    if tcode != 200:
        problems.append("tag ref not found")
    else:
        obj = tref["object"]
        commit = obj["sha"]
        if obj["type"] == "tag":  # annotated: dereference
            c2, b2 = call("GET", f"{API}/repos/{REPO}/git/tags/{obj['sha']}")
            commit = json.loads(b2)["object"]["sha"]
            print("tag type: annotated")
        print("tag", TAG, "->", commit)
        if expected_commit and commit != expected_commit:
            problems.append(f"tag target {commit} != expected {expected_commit}")
    print("VERIFY", "OK" if not problems else "FAILED: " + "; ".join(problems))
    sys.exit(0 if not problems else 1)


if __name__ == "__main__":
    cmds = {"check": cmd_check, "create": cmd_create}
    if len(sys.argv) < 2 or sys.argv[1] not in ("check", "create", "verify"):
        sys.exit(__doc__)
    if sys.argv[1] == "verify":
        cmd_verify(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        cmds[sys.argv[1]]()
