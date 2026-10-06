# Publication hygiene

Mandatory closing phase for **every** workbook or addendum. It exists so
that a locally built PDF is never mistaken for a published one, and so a
published binary can always be traced to a source commit and verified.

Source of truth: the `publications:` section of
`config/chapter-status-registry.yaml`. Checked by
`scripts/validate_publication_hygiene.py` (tests:
`tests/test_publication_hygiene.py`). The README catalog between the
`publication-catalog` markers must agree with the registry.

## Lifecycle

```
planned -> drafting -> review_pending -> accepted_frozen -> canonical_built -> published
```

- `accepted_frozen` — content is accepted and frozen (chapter-factory
  meaning, unchanged). Public distribution is not implied.
- `canonical_built` — the canonical PDF exists, is human-accepted, and its
  page count, SHA-256 and source commit are recorded. Release fields hold
  **prepared** values, not claims. README status reads "Release pending".
- `published` — only when **all** hold:
  1. human acceptance is recorded (`human_acceptance.accepted: true` + date);
  2. the canonical PDF's page count and SHA-256 are recorded;
  3. the source commit (40-hex) is recorded;
  4. an annotated, versioned Git tag exists at that commit;
  5. a GitHub Release exists for the tag (not draft, not prerelease);
  6. the canonical PDF is its one attached asset;
  7. the downloaded remote asset reproduces the recorded SHA-256;
  8. the README links the direct release-asset URL;
  9. the registry records the release URL and publication date.

A work is never `published` merely because its PDF exists locally, nor
because upload "seemed to work".

## Required metadata per artifact

`title`, `status`, `canonical_path` (`outputs/<name>.pdf`), `page_count`,
`sha256`, `source_commit`, `release_tag` (`<name>-vMAJOR.MINOR.PATCH`),
`release_asset` (bare `.pdf` filename equal to the canonical file name),
`release_url` (`https://github.com/<owner>/<repo>/releases/tag/<tag>`),
`publication_date`, `reproduction_command`, `human_acceptance`.
The artifact id is the registry key. Ids, tags and asset names must be
unique across the registry.

## Closing sequence (no step may be skipped or reordered)

1. Content acceptance and freeze.
2. Reproducible canonical final build (established final-build script).
3. Independent PDF visual acceptance of every page.
4. Page count and SHA-256 capture.
5. Publication metadata update in the registry (`canonical_built`).
6. README catalog update (status "Release pending").
7. Run `python3 scripts/validate_publication_hygiene.py --check-local`.
8. Local documentation commit.
9. Push of the source/publication commit (explicit user authorization).
10. Create an annotated tag at the recorded source commit and push it,
    then create a **unique, versioned** GitHub Release (explicit user
    authorization).
11. Upload **only** the canonical final PDF.
12. Remote verification: tag target, asset name, downloadable URL, size and
    SHA-256 of a freshly downloaded copy
    (`validate_publication_hygiene.py --remote` after step 13's metadata is
    set, plus a manual download check before it).
13. Set `status: published`, `publication_date`, README status and direct
    link; re-run offline and `--remote` validation.
14. Final publication commit and push. Only now is the artifact published.

Compressed form: human acceptance → canonical build → complete visual
inspection → freeze metadata → publication-hygiene validation → push
source → immutable version tag → GitHub Release with canonical PDF →
remote checksum verification → README and registry synchronization →
final publication commit.

## Rules

- Publication (push, tag, release) is an explicit, user-authorized
  external action; approval for one release does not carry to the next.
- Never overwrite or move an existing tag; never edit, replace or delete a
  release asset. Corrections after publication use a **new patch version**
  and a new immutable asset.
- Never publish RC, review, superseded, page-image, contact-sheet or
  development artifacts; the asset is exactly the canonical PDF.
- Canonical PDFs are not committed to Git and Git LFS is not used for them
  (they are small; the release asset is the distribution channel). The
  validator rejects any tracked `outputs/*.pdf`.
- A failed or partial upload leaves the status at `canonical_built`
  (or `accepted_frozen`), never `published`. A release is not complete
  until the remote asset has been downloaded (or otherwise verified)
  against the expected checksum.
- Local canonical PDFs may be absent on a fresh clone; default validation
  must not require them (`--check-local` checks them when present;
  `--require-local` makes absence fatal).

## Validator usage

```bash
python3 scripts/validate_publication_hygiene.py                 # offline, no network
python3 scripts/validate_publication_hygiene.py --check-local   # + page count/SHA-256 of local PDFs when present
python3 scripts/validate_publication_hygiene.py --remote        # + read-only GitHub release/asset/checksum check
```

Offline failures exit 1; remote failures (reported separately) exit 2.
`--remote` performs GET requests only and never creates, modifies or
deletes anything.
