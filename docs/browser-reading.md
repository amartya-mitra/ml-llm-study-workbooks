# Browser reading site

A small static site (no framework, no JavaScript) that lets readers open
the published study guides in the browser's built-in PDF viewer, with a
visible download link beside each one. It mirrors the README catalog and
includes only published editions.

Live site: <https://amartya-mitra.github.io/ml-llm-study-workbooks/>

Status as of 2026-10-28: **deployed and verified.** The first deployment
was from commit `9aa3fa3` (workflow run 40775205298, deployment
7398229289). All four served PDFs matched their recorded SHA-256, and a
human reader confirmed that the site works and the PDFs open in the
browser. The registry records this as
`browser_reading: {status: deployed, verified: true}` in
`config/chapter-status-registry.yaml`.

The README catalog gives each published guide a **Read in browser** link
(the site's versioned PDF path,
`<base_url>editions/<release_tag>/<release_asset>`) beside its **Download
PDF** link (the GitHub release asset). The validator checks both
against the registry. `github.io` links are allowed only while
`verified` is true, and a "Read in browser" link must open the same
current edition that its row downloads.

## How the site is built

`scripts/build_site.py` (tests: `tests/test_build_site.py`):

1. Reads the `publications:` registry and takes every `published`
   edition, current and previous (`previous_releases`). Drafts and
   in-progress guides contribute only an "In progress" line with their
   chapter progress from the status registry, never a file.
2. Downloads each edition's exact release asset from its versioned URL,
   `https://github.com/<owner>/<repo>/releases/download/<tag>/<asset>`,
   into a temporary directory beside the output. These are unauthenticated
   public GET requests; no token is read or sent.
3. Checks each file's SHA-256 (and byte size, where recorded) against
   the registry. Any mismatch, missing checksum, unsafe name or failed
   download aborts the build before the output directory is touched.
4. Writes `index.html`, `style.css` and `editions.json` (the verified
   manifest) and stores each PDF at `editions/<release_tag>/<asset>`.
   Versioned paths mean a new edition never overwrites an older one.
   Guide titles and descriptions come from the README catalog, so the
   two stay in step.

PDFs are never rebuilt for the site, and neither PDFs nor the generated
site are committed: `_site/` is git-ignored and deployed as a Pages
artifact.

Build and inspect locally:

```bash
python3 scripts/build_site.py --out _site
python3 -m http.server --directory _site 8000   # then open http://localhost:8000/
```

Local inspection on 2026-10-28 (headless Chromium, widths 1280, 390 and
320 px): no horizontal overflow at any width (document `scrollWidth`
equal to `clientWidth`), smallest text 15.2 px, every link relative to
its versioned edition path, and every link with a descriptive label.

## PDF viewing

"Read in browser" is a plain link to the PDF, opened by the browser's
built-in viewer; "Download PDF" is the same file with the `download`
attribute. Some browsers, mobile devices and user settings download PDFs
instead of displaying them, and the page says so. PDF.js is not used: no
test has yet shown a need for it. Revisit only if a concrete browser
fails to show the files.

## Deployment workflow

`.github/workflows/pages.yml` follows GitHub's documentation for custom
Pages workflows ("Using custom workflows with GitHub Pages", checked
2026-10-28), which uses `actions/checkout@v6`,
`actions/upload-pages-artifact@v4` and `actions/deploy-pages@v4`.
(Newer major versions of these actions exist on their release pages;
upgrade deliberately, not as part of activation.)

- Runs on `workflow_dispatch` and on pushes to `main` that change the
  registry, the README, the editions document, or the site and
  validator scripts.
- Top-level `permissions: {}`. The `build` job gets `contents: read`
  only. The `deploy` job gets exactly the two permissions GitHub
  documents as the minimum for a Pages deployment, `pages: write` and
  `id-token: write`.
- `actions/configure-pages` is omitted. GitHub documents it as optional
  (it enables Pages and gathers metadata for site generators), and this
  site uses only relative paths.
- The build job first runs `validate_publication_hygiene.py`, then
  `build_site.py`, so a registry inconsistency or a checksum mismatch
  stops the deployment.
- The only token is the automatic, job-scoped `GITHUB_TOKEN`; checkout
  uses `persist-credentials: false`. No personal or provisioned token is
  referenced.
- Deploys to the `github-pages` environment, one deployment at a time
  (`concurrency: pages`).

## Activation (completed 2026-10-28)

1. Pushed the commit containing the workflow (user-authorized).
2. **Settings → Pages → Build and deployment → Source: GitHub Actions**,
   with the `github-pages` environment limited to deployments from
   `main`.
3. The push triggered the workflow, which built and deployed the site.
4. Verified the deployment: each served PDF's SHA-256 matched
   [editions-and-verification.md](editions-and-verification.md)
   (`curl -sL <url> | sha256sum`), and a human reader checked it in a
   browser.
5. Set `browser_reading.verified: true` and added the README's "Read in
   browser" links.

## When a new edition is released

The site rebuilds whenever the registry or the README changes on
`main`. After a release is published and recorded:

1. Point the README row's "Read in browser" link at the new edition's
   versioned site path, in the same commit that updates its "Download
   PDF" link.
2. After the deployment, check that the new path serves the recorded
   checksum.

The old edition's path stays on the site.
