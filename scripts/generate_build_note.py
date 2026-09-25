#!/usr/bin/env python3
"""Generate the build/version note included at the end of a review PDF.

Writes a small .qmd fragment recording the generation date, a
learner-facing source-verification date range, and a fixed release-
status line. Run this immediately before rendering a review build --
never hand-edit the generated file, since it will be silently
overwritten.

This template is deliberately learner-facing and repository-internal-
path-free: it must never contain a raw commit SHA (a PDF cannot name
the commit that includes its own build -- see git_commit_or_precommit's
docstring below) or any raw .yaml/.qmd/script/include/data path. The
exact source commit and any internal-path provenance belong in a
maintainer-facing repo report (e.g. reports/04_release_candidate_N_report.md),
not in the rendered book. git_commit_or_precommit() below is still
computed and printed to stdout for whoever is running this build to
copy into that report -- it is intentionally never interpolated into
`content`.

Usage:
    python3 scripts/generate_build_note.py \\
        --output workbooks/04-llm-architecture/includes/build-version-note.qmd \\
        --pilot-status "Two-chapter pilot (Chapters 1-2 of 8)" \\
        --source-verification-note "Primary and roadmap sources for Chapters 1-2 last verified 2026-09-22." \\
        --provenance-note "Tied-embeddings usage has no dedicated primary source; sandwich-norm leans on a secondary source." \\
        --provenance-note "Worked-example numbers (attention weights, parameter counts) are computed by version-controlled project scripts and checked by the project's automated test suite, not hand-derived."
"""
import argparse
import datetime
import os
import subprocess


def git_commit_or_precommit(repo_root: str) -> str:
    """Report the source commit honestly, without implying a build-time
    guarantee that cannot exist: a PDF that will itself be committed
    afterward can never name the commit that includes it. If the tree
    has uncommitted changes at render time, say so plainly rather than
    using an alarming-sounding "pre-commit" label -- this is a normal,
    expected state mid-revision, not an error. This value is printed to
    stdout only, for a maintainer report -- never written into the
    learner-facing template below."""
    status = subprocess.run(["git", "status", "--porcelain"], cwd=repo_root, capture_output=True, text=True)
    dirty = bool(status.stdout.strip())
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True)
    sha = head.stdout.strip()
    if dirty:
        return f"{sha} (this build was rendered with additional, not-yet-committed changes on top of this commit)"
    return sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--pilot-status", required=True)
    verification_group = parser.add_mutually_exclusive_group(required=True)
    verification_group.add_argument("--source-verification-note",
                         help="Learner-facing sentence describing when sources were last verified -- "
                              "no raw registry IDs or file paths.")
    verification_group.add_argument("--registry-note",
                         help="Deprecated alias for --source-verification-note, kept so RC1/RC2's "
                              "frozen build scripts keep working unmodified; new callers should use "
                              "--source-verification-note with learner-facing, path-free text.")
    parser.add_argument("--provenance-note", action="append", default=[],
                         help="One bullet for the Provenance subsection; may be repeated.")
    args = parser.parse_args()
    verification_note = args.source_verification_note or args.registry_note

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    commit = git_commit_or_precommit(repo_root)
    print(f"source commit for the maintainer report: {commit}")
    today = datetime.date.today().isoformat()

    provenance_bullets = "\n".join(f"- {note}" for note in args.provenance_note)

    content = f"""## Build and Version Note {{.unnumbered}}

- **Generated:** {today}
- **Source verification:** {verification_note}
- **Release status:** {args.pilot_status}

### Provenance {{.unnumbered}}

{provenance_bullets}
"""
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        f.write(content)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
