#!/usr/bin/env python3
"""Best-effort link check for sources/registry.yaml URLs.

This performs a live HTTP check (HEAD, falling back to GET) and is
therefore network-dependent and not part of the default test suite
(tests/ only checks URL *shape*, not reachability — see
tests/test_registry.py). Run this manually:

    python3 scripts/check_links.py

It does not modify registry.yaml; it only reports. Updating
`last_verified` after a real check is a manual, deliberate edit (see
AGENTS.md: only record a verification date after actually checking).
"""
import os
import sys
import urllib.error
import urllib.request

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from _yaml_lite import safe_load_path  # noqa: E402

TIMEOUT_SECONDS = 10
USER_AGENT = "ml-llm-study-workbooks-linkcheck/0.1 (+see AGENTS.md)"


def check_url(url: str):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            return resp.status, None
    except urllib.error.HTTPError as e:
        if e.code == 405:  # some servers reject HEAD; retry with GET
            try:
                req2 = urllib.request.Request(url, method="GET", headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req2, timeout=TIMEOUT_SECONDS) as resp:
                    return resp.status, None
            except Exception as e2:  # noqa: BLE001
                return None, str(e2)
        return e.code, str(e)
    except Exception as e:  # noqa: BLE001
        return None, str(e)


def main():
    reg = safe_load_path(os.path.join(REPO_ROOT, "sources", "registry.yaml"))
    results = []
    for entry in reg["sources"]:
        status, err = check_url(entry["url"])
        results.append((entry["id"], entry["url"], status, err))

    failures = 0
    for sid, url, status, err in results:
        ok = status is not None and 200 <= status < 400
        marker = "OK " if ok else "FAIL"
        if not ok:
            failures += 1
        print(f"[{marker}] {sid}  {status}  {url}" + (f"  ({err})" if err else ""))

    print(f"\n{len(results) - failures}/{len(results)} reachable")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
