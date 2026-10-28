# Browser reading site

A small static site (no framework, no JavaScript) that lets readers open
the published study guides in the browser's built-in PDF viewer, with a
visible download link beside each one. It mirrors the README catalog and
includes only published editions.

Status as of 2026-10-28: **prepared, not deployed.** GitHub Pages is not
enabled for this repository (`GET /repos/amartya-mitra/ml-llm-study-workbooks/pages`
returns 404). The registry records this as
`browser_reading: {status: prepared, verified: false}` in
`config/chapter-status-registry.yaml`. While `verified` is false, the
publication-hygiene validator rejects any `github.io` link in the README.

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

## Activation (remaining steps)

1. Push the commit that contains the workflow (requires explicit user
   authorization).
2. In the repository on GitHub: **Settings → Pages → Build and
   deployment → Source: GitHub Actions.**
3. In **Settings → Environments → github-pages**, confirm the deployment
   branch rule allows only `main` (GitHub creates the environment on
   first use).
4. Run the workflow from **Actions → Browser reading site → Run
   workflow**, or let the push trigger it once Pages is enabled.
5. Verify the deployed site at
   <https://amartya-mitra.github.io/ml-llm-study-workbooks/>: each "Read
   in browser" link opens; each served PDF's SHA-256 matches
   [editions-and-verification.md](editions-and-verification.md), for
   example with
   `curl -sL <url> | sha256sum`; check on a phone-width screen.
6. Only after that check, set `browser_reading.verified: true` (and
   `status: "deployed"`) in the registry, and add "Read online" links to
   the README catalog under the base URL. The validator allows
   `github.io` links only in that state.

If step 1 happens before step 2, the first workflow run fails at the
deploy step without side effects; enable Pages and re-run it.
