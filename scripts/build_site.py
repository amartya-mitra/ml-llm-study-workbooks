#!/usr/bin/env python3
"""Build the static browser-reading site for the published study guides.

Source of truth: the `publications:` section of
config/chapter-status-registry.yaml (only `published` editions are
included) and the README catalog (guide descriptions). See
docs/browser-reading.md.

For every published edition, current and previous, the exact release
asset is downloaded from its versioned GitHub Release URL into a
temporary build directory and its SHA-256 is checked against the
registry. Any mismatch, missing checksum or failed download aborts the
build before anything is written to the output directory. Published
PDFs are never rebuilt here.

Output (default `_site/`, git-ignored):

    index.html, style.css, editions.json
    editions/<release_tag>/<release_asset>

Versioned paths mean a later edition never replaces an earlier one.
Only public, unauthenticated GET requests are made; no token is read.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.request

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from _yaml_lite import safe_load_path  # noqa: E402
from validate_publication_hygiene import (  # noqa: E402
    DEFAULT_REPO_SLUG, IN_PROGRESS_STATES, SHA256_RE, asset_url, chapter_progress,
    editions, parse_readme_catalog, release_page_url)

MAX_BYTES = 100 * 1024 * 1024
ISSUES_PATH = "issues"


class SiteBuildError(Exception):
    pass


def fetch_url(url):
    """Public GET with a size cap. Sends no credentials."""
    req = urllib.request.Request(url, headers={"User-Agent": "ml-llm-study-workbooks-site-build"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise SiteBuildError(f"{url}: larger than {MAX_BYTES} bytes")
    return data


def _inline_md(text):
    """Escape, then render the two inline forms the catalog uses: **bold** and (addendum)."""
    out = html.escape(text.strip(), quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)


def catalog_descriptions(readme_text, pubs, slug):
    """Map artifact id -> (title, description) from the README catalog rows."""
    rows = parse_readme_catalog(readme_text) or []
    current = {asset_url(slug, r.get("release_tag", ""), r.get("release_asset", "")): aid
               for aid, r in pubs.items() if isinstance(r, dict) and r.get("status") == "published"}
    out = {}
    for row in rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        for url, aid in current.items():
            if url in row and len(cells) >= 2:
                out[aid] = (re.sub(r"\*\*", "", cells[0]).strip(), cells[1])
    return out


def collect(root, slug, fetch, workdir):
    """Download and verify every published edition into workdir. Returns edition dicts."""
    registry = safe_load_path(os.path.join(root, "config", "chapter-status-registry.yaml")) or {}
    pubs = registry.get("publications") or {}
    eds = editions(pubs)
    if not eds:
        raise SiteBuildError("no published editions in the registry")
    seen = set()
    for ed in eds:
        tag, asset, sha = ed.get("release_tag"), ed.get("release_asset"), ed.get("sha256")
        if not (tag and asset and isinstance(sha, str) and SHA256_RE.match(sha)):
            raise SiteBuildError(f"[{ed['id']}] edition lacks release_tag, release_asset or a valid sha256")
        if "/" in tag or "/" in asset or tag.startswith(".") or asset.startswith(".") or not asset.endswith(".pdf"):
            raise SiteBuildError(f"[{ed['id']}] unsafe release tag or asset name: {tag}/{asset}")
        rel = f"editions/{tag}/{asset}"
        if rel in seen:
            raise SiteBuildError(f"duplicate edition path {rel}")
        seen.add(rel)
        url = asset_url(slug, tag, asset)
        try:
            data = fetch(url)
        except SiteBuildError:
            raise
        except Exception as exc:  # network errors abort the whole build
            raise SiteBuildError(f"[{ed['id']}] download failed for {url}: {exc}") from exc
        got = hashlib.sha256(data).hexdigest()
        if got != sha:
            raise SiteBuildError(f"[{ed['id']}] SHA-256 mismatch for {url}: expected {sha}, got {got}")
        if ed.get("bytes") is not None and int(ed["bytes"]) != len(data):
            raise SiteBuildError(f"[{ed['id']}] size mismatch for {url}: expected {ed['bytes']}, got {len(data)}")
        dest = os.path.join(workdir, "editions", tag)
        os.makedirs(dest, exist_ok=True)
        with open(os.path.join(dest, asset), "wb") as f:
            f.write(data)
        ed.update(path=rel, size=len(data), download_url=url, release_page=release_page_url(slug, tag))
    return registry, pubs, eds


def _mb(n):
    return f"{n / 1e6:.1f} MB"


def render_index(registry, pubs, eds, descriptions, slug):
    current = [e for e in eds if e["current"]]
    previous = [e for e in eds if not e["current"]]
    cards = []
    for ed in current:
        title, desc = descriptions.get(ed["id"], (ed.get("title") or ed["id"], ""))
        cards.append(f"""      <article class="guide">
        <h3>{html.escape(title)}</h3>
        <p>{_inline_md(desc)}</p>
        <p class="meta">Edition {html.escape(str(ed.get('version') or ed['release_tag'].rsplit('-v', 1)[-1]))} · {ed.get('page_count')} pages · PDF, {_mb(ed['size'])}</p>
        <p class="actions">
          <a class="button" href="{html.escape(ed['path'])}">Read in browser<span class="visually-hidden">: {html.escape(title)}</span></a>
          <a class="button secondary" href="{html.escape(ed['path'])}" download>Download PDF<span class="visually-hidden">: {html.escape(title)}</span></a>
        </p>
      </article>""")
    progress = []
    for aid, rec in pubs.items():
        if isinstance(rec, dict) and rec.get("status") in IN_PROGRESS_STATES:
            prog = chapter_progress(registry.get("workbooks"), rec.get("workbook_id"))
            note = f", {prog[0]} of {prog[1]} chapters accepted so far" if prog else ""
            progress.append(f"        <li><strong>{html.escape(str(rec.get('title') or aid))}</strong>: in progress{note}. "
                            "It will appear here once the complete guide is released.</li>")
    prev_items = [f"""        <li>{html.escape(descriptions.get(e['id'], (e.get('title') or e['id'],))[0])}, edition {html.escape(str(e.get('version')))}
          ({e.get('page_count')} pages):
          <a href="{html.escape(e['path'])}">Read in browser<span class="visually-hidden">: edition {html.escape(str(e.get('version')))}</span></a> ·
          <a href="{html.escape(e['path'])}" download>Download PDF<span class="visually-hidden">: edition {html.escape(str(e.get('version')))}</span></a></li>"""
                  for e in previous]
    repo = f"https://github.com/{slug}"
    prev_html = ("""
    <section aria-labelledby="earlier">
      <h2 id="earlier">Earlier editions</h2>
      <p>Released editions are never replaced. Earlier ones stay available here and on GitHub.</p>
      <ul>
""" + "\n".join(prev_items) + """
      </ul>
    </section>
""") if prev_items else ""
    prog_html = ("""
    <section aria-labelledby="progress">
      <h2 id="progress">In progress</h2>
      <ul>
""" + "\n".join(progress) + """
      </ul>
    </section>
""") if progress else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ML/LLM Study Workbooks</title>
  <meta name="description" content="Study guides on modern LLM architecture, training, and time-series foundation models, with diagrams, worked examples, and questions with answers.">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <main>
    <header>
      <h1>ML/LLM Study Workbooks</h1>
      <p>Study guides on how modern large language models are built and trained, and how those ideas carry over to time-series forecasting. Each guide combines original diagrams, worked numerical examples, and questions with full answers.</p>
    </header>
    <section aria-labelledby="guides">
      <h2 id="guides">Study guides</h2>
      <p>New to the topic? Read them in this order: architecture, then training, then the time-series addendum.</p>
{chr(10).join(cards)}
      <p class="note"><strong>Read in browser</strong> opens the PDF in your browser's built-in viewer. Some browsers or settings download PDFs instead of showing them; if that happens, open the downloaded file, or use <strong>Download PDF</strong>.</p>
    </section>
{prog_html}{prev_html}
    <footer>
      <p>Each PDF here is the exact file attached to its GitHub Release, checked against its recorded SHA-256 checksum when this site was built. Checksums: <a href="{repo}/blob/main/docs/editions-and-verification.md">editions and verification</a>.</p>
      <p>Found an error? <a href="{repo}/{ISSUES_PATH}">Open an issue on GitHub</a>. Source: <a href="{repo}">GitHub repository</a>.</p>
    </footer>
  </main>
</body>
</html>
"""


STYLE = """*, *::before, *::after { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; font: 1.0625rem/1.6 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
       color: #1b1f24; background: #fff; overflow-wrap: break-word; }
main { max-width: 46rem; margin: 0 auto; padding: 1.5rem 1rem 3rem; }
h1 { font-size: 1.9rem; line-height: 1.2; margin: 0.5rem 0 0.75rem; }
h2 { font-size: 1.35rem; margin: 2rem 0 0.75rem; }
h3 { font-size: 1.15rem; margin: 0 0 0.5rem; }
a { color: #0b5cad; }
a:focus-visible { outline: 3px solid #f0a020; outline-offset: 2px; }
.guide { border: 1px solid #d0d7de; border-radius: 8px; padding: 1rem; margin: 0 0 1rem; }
.guide p { margin: 0 0 0.6rem; }
.meta { color: #57606a; font-size: 0.95rem; }
.actions { display: flex; flex-wrap: wrap; gap: 0.6rem; margin: 0.25rem 0 0; }
.button { display: inline-block; padding: 0.55rem 1rem; border-radius: 6px; background: #0b5cad;
          color: #fff; text-decoration: none; font-weight: 600; }
.button.secondary { background: #fff; color: #0b5cad; border: 2px solid #0b5cad; padding: 0.45rem 0.9rem; }
.note { background: #f6f8fa; border-left: 4px solid #57606a; padding: 0.75rem 1rem; font-size: 0.95rem; }
footer { margin-top: 2.5rem; border-top: 1px solid #d0d7de; padding-top: 1rem; font-size: 0.95rem; color: #57606a; }
.visually-hidden { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0);
                   clip-path: inset(50%); white-space: nowrap; }
@media (prefers-color-scheme: dark) {
  body { color: #e6edf3; background: #0d1117; }
  a { color: #6cb6ff; }
  .guide, footer { border-color: #30363d; }
  .meta, footer { color: #9da7b3; }
  .button { background: #2f81f7; color: #fff; }
  .button.secondary { background: transparent; color: #6cb6ff; border-color: #6cb6ff; }
  .note { background: #161b22; border-left-color: #9da7b3; }
}
"""


def build(root=REPO_ROOT, out=None, slug=DEFAULT_REPO_SLUG, fetch=None):
    fetch = fetch or fetch_url
    out = os.path.abspath(out or os.path.join(root, "_site"))
    parent = os.path.dirname(out)
    os.makedirs(parent, exist_ok=True)
    work = tempfile.mkdtemp(prefix=".site-build-", dir=parent)
    try:
        registry, pubs, eds = collect(root, slug, fetch, work)
        with open(os.path.join(root, "README.md"), encoding="utf-8") as f:
            descriptions = catalog_descriptions(f.read(), pubs, slug)
        missing = [e["id"] for e in eds if e["current"] and e["id"] not in descriptions]
        if missing:
            raise SiteBuildError(f"README catalog has no description for: {', '.join(missing)}")
        with open(os.path.join(work, "index.html"), "w", encoding="utf-8") as f:
            f.write(render_index(registry, pubs, eds, descriptions, slug))
        with open(os.path.join(work, "style.css"), "w", encoding="utf-8") as f:
            f.write(STYLE)
        manifest = [{k: e.get(k) for k in ("id", "title", "version", "current", "release_tag", "release_asset",
                                            "page_count", "size", "sha256", "path", "download_url", "release_page")}
                    for e in eds]
        with open(os.path.join(work, "editions.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
            f.write("\n")
        if os.path.exists(out):
            shutil.rmtree(out)
        os.replace(work, out)
        return eds
    except BaseException:
        shutil.rmtree(work, ignore_errors=True)
        raise


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", default=REPO_ROOT)
    ap.add_argument("--out", default=None, help="output directory (default: <root>/_site)")
    ap.add_argument("--repo-slug", default=DEFAULT_REPO_SLUG)
    args = ap.parse_args(argv)
    try:
        eds = build(args.root, args.out, args.repo_slug)
    except SiteBuildError as exc:
        print("SITE BUILD FAILED:", exc, file=sys.stderr)
        return 1
    for e in eds:
        print(f"  ok  {e['path']}  {e['size']} bytes  sha256 {e['sha256']}")
    print(f"site built: {len(eds)} verified edition(s) -> {os.path.abspath(args.out or os.path.join(args.root, '_site'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
