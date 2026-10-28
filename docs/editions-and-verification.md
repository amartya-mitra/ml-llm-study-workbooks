# Editions and verification

Every released edition of every study guide, with the identity needed to
confirm that a downloaded PDF is exactly the file that was released.
Each PDF is distributed as the single asset of an immutable, versioned
GitHub Release. Released files are never replaced: a correction is
published as a new edition under a new tag, and the earlier edition
stays available at its own release page.

The source of truth is the `publications:` section of
`config/chapter-status-registry.yaml`. This table is checked against it
by `scripts/validate_publication_hygiene.py` (every published edition,
current and previous, must appear with its tag, page count and SHA-256).
Byte sizes were read from the GitHub Releases API on 2026-10-28.

## Released editions

| Guide | Edition | Release tag | Pages | Bytes | SHA-256 | Released |
|---|---|---|---|---|---|---|
| Modern LLM Architecture | 1.0.0 (current) | `workbook-04-v1.0.0` | 69 | 1,366,516 | `12bcc6c115e4a7279162efd06c5e13f44a808a36fd92d6e3153cb43aac95c33b` | 2026-10-06 |
| LLM Pretraining and Distributed Training | 1.0.0 (current) | `workbook-05-v1.0.0` | 64 | 1,152,681 | `25a393bb6b1bb1c42c836f08b4375e9e1a451792f4397665f63b69e1c1072a0c` | 2026-10-06 |
| From Language Models to Time-Series Foundation Models (addendum) | 1.1.0 (current) | `addendum-04-05-tsfm-v1.1.0` | 23 | 508,386 | `68467ffb62bbf7734bb97e4387d5956349811d6d211b5d12501c5166b87d6ea2` | 2026-10-28 |
| From Language Models to Time-Series Foundation Models (addendum) | 1.0.0 (previous) | `addendum-04-05-tsfm-v1.0.0` | 18 | 425,777 | `b7096e9b9291dc4319f8f3740303b42dcf784d3ec80bb2fb63cc66f7ac242b65` | 2026-10-06 |

Release pages (release notes and the asset):

- Modern LLM Architecture 1.0.0:
  <https://github.com/amartya-mitra/ml-llm-study-workbooks/releases/tag/workbook-04-v1.0.0>
- LLM Pretraining and Distributed Training 1.0.0:
  <https://github.com/amartya-mitra/ml-llm-study-workbooks/releases/tag/workbook-05-v1.0.0>
- Time-series addendum 1.1.0:
  <https://github.com/amartya-mitra/ml-llm-study-workbooks/releases/tag/addendum-04-05-tsfm-v1.1.0>
- Time-series addendum 1.0.0:
  <https://github.com/amartya-mitra/ml-llm-study-workbooks/releases/tag/addendum-04-05-tsfm-v1.0.0>

What changed in addendum 1.1.0: it adds Mistral Timestral (Decoupled
Horizon Forecasting, covariate roles, and evidence from its pinned
inference code), growing the guide from 18 to 23 pages. Edition 1.0.0 is
unchanged at its release page. Both editions use the same file name,
`addendum-04-05-tsfm.pdf`, under different release tags, so check the
tag (or the checksum) to know which one you have.

## Verifying a download

Compute the SHA-256 of the downloaded file and compare it with the table:

```bash
sha256sum 04-modern-llm-architecture-workbook.pdf     # Linux
shasum -a 256 04-modern-llm-architecture-workbook.pdf # macOS
```

On Windows PowerShell: `Get-FileHash .\04-modern-llm-architecture-workbook.pdf -Algorithm SHA256`
(PowerShell prints the hash in upper case; compare it ignoring case).

If the checksum differs, the file is not the released edition: download
it again from the release page, and
[open an issue](https://github.com/amartya-mitra/ml-llm-study-workbooks/issues)
if it still differs.

## Provenance

Each registry record also holds the 40-character source commit the PDF
was built from, the build command that reproduces it, and the date and
note of its human acceptance. `python3 scripts/validate_publication_hygiene.py --remote`
re-downloads every current release asset (read-only) and checks its
SHA-256 against the registry. The browser-reading site checks the same
checksums before it includes any PDF (see
[browser-reading.md](browser-reading.md)).

Unreleased work, such as LLM Inference Engineering, has no entry here
until it is released; its draft and review PDFs are never published.
