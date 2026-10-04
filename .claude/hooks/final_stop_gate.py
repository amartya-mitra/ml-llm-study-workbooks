#!/usr/bin/env python3
"""Stop hook: final chapter-acceptance gate.

STAGED, NOT ACTIVE by default -- see .claude/hooks.staged.json and
docs/chapter-factory-operator-guide.md for the exact activation step,
and read that guide's warning about this specific hook before ever
activating it: of the three staged hooks, this is the one actually
capable of trapping a session (a Stop hook that always blocks would
make Claude unable to ever finish a turn). The two safety properties
below exist specifically to prevent that.

**Safety property 1 -- marker-gated, not global.** This hook is a
no-op (exits 0 immediately) unless a marker file at
.claude/.active-chapter-task.json exists. That marker is written by
the draft-workbook-chapter / review-workbook-chapter skills when they
begin chapter-factory work, and removed once the chapter gate
genuinely passes. An ordinary turn with no such marker is completely
unaffected by this hook, no matter what it does.

**Safety property 2 -- bounded retries, fail-open.** Each time this
hook blocks a Stop, it increments an attempt counter in the marker.
Once attempts reach MAX_ATTEMPTS, it stops blocking -- it allows the
stop anyway and reports that human intervention is required, rather
than blocking forever. A second correction cycle requires explicit
human direction (see docs/chapter-review-checklist.md and
.claude/skills/review-workbook-chapter/SKILL.md); this hook enforces
that same one-bounded-cycle policy at the infrastructure level.

Any error reading/parsing the marker, or running the gate itself
(including a timeout), fails OPEN (allows the stop) rather than
trapping the session -- an unenforced check is recoverable later; a
hook that can never let Claude stop is not.
"""
import json
import os
import subprocess
import sys

REPO_ROOT = os.environ.get(
    "CHAPTER_GATE_REPO_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
)
MARKER_PATH = os.path.join(REPO_ROOT, ".claude", ".active-chapter-task.json")
MAX_ATTEMPTS = 2
GATE_TIMEOUT_SECONDS = 180


def main():
    try:
        json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        pass  # the Stop event payload isn't needed beyond confirming the hook fired correctly

    if not os.path.exists(MARKER_PATH):
        sys.exit(0)

    try:
        with open(MARKER_PATH, encoding="utf-8") as f:
            marker = json.load(f)
    except (OSError, json.JSONDecodeError):
        sys.exit(0)

    workbook = marker.get("workbook")
    chapter = marker.get("chapter")
    attempts = marker.get("attempts", 0)
    if not workbook or not chapter:
        sys.exit(0)

    if attempts >= MAX_ATTEMPTS:
        print(json.dumps({"systemMessage": (
            f"chapter-factory stop gate: {workbook} chapter {chapter} still failing after "
            f"{attempts} attempt(s) -- allowing stop anyway per the one-bounded-cycle policy; "
            f"human intervention required. Remove "
            f"{os.path.relpath(MARKER_PATH, REPO_ROOT)} once resolved."
        )}))
        sys.exit(0)

    gate_dir = os.path.join(REPO_ROOT, "outputs", "_development", workbook, "chapter-gate")
    cmd = [sys.executable, os.path.join(REPO_ROOT, "scripts", "chapter_gate.py"),
           "--workbook", workbook, "--chapter", chapter]
    review_pdf = marker.get("review_pdf")
    if review_pdf:
        cmd += ["--review-pdf", review_pdf]
    for flag, fname in [
        ("--source-audit-json", f"ch{chapter}-source-audit.json"),
        ("--numerical-audit-json", f"ch{chapter}-numerical-audit.json"),
        ("--figure-audit-json", f"ch{chapter}-figure-audit.json"),
        ("--learner-pdf-audit-json", f"ch{chapter}-learner-pdf-audit.json"),
    ]:
        candidate = os.path.join(gate_dir, fname)
        if os.path.exists(candidate):
            cmd += [flag, candidate]

    try:
        r = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=GATE_TIMEOUT_SECONDS)
    except (subprocess.TimeoutExpired, OSError):
        sys.exit(0)  # never hang or crash the session over a slow/broken gate run

    if r.returncode == 0:
        try:
            os.remove(MARKER_PATH)
        except OSError:
            pass
        sys.exit(0)

    marker["attempts"] = attempts + 1
    try:
        with open(MARKER_PATH, "w", encoding="utf-8") as f:
            json.dump(marker, f, indent=2)
    except OSError:
        sys.exit(0)  # can't persist the retry count -- fail open rather than block unboundedly

    tail = "\n".join(r.stdout.splitlines()[-15:])
    print(json.dumps({"systemMessage": (
        f"chapter-factory stop gate BLOCKED completion for {workbook} chapter {chapter} "
        f"(attempt {attempts + 1}/{MAX_ATTEMPTS}): the chapter gate did not pass. Fix the "
        f"reported blocker/required findings, rebuild, and try again. Gate output tail:\n{tail}"
    )}))
    sys.exit(2)


if __name__ == "__main__":
    main()
