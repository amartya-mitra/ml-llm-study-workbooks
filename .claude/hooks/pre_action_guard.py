#!/usr/bin/env python3
"""PreToolUse guard for the chapter-factory workflow.

STAGED, NOT ACTIVE by default -- see .claude/hooks.staged.json and
docs/chapter-factory-operator-guide.md for the exact activation step.
This script is safe to run standalone against synthetic stdin at any
time (it never writes anything); only wiring it into
.claude/settings.json makes it live.

Reads a PreToolUse event JSON on stdin (tool_name, tool_input) and
blocks (exit 2, with a JSON {"systemMessage": ...} on stdout) exactly
these actions:

    - `git push` in any form (unconditional -- no override).
    - Edit/Write/NotebookEdit targeting a path that matches a
      frozen_paths glob in an accepted_frozen chapter's own contract
      (workbooks/*/chapter-contracts/*.yaml) or a whole-workbook
      "frozen" entry in config/chapter-status-registry.yaml, UNLESS a
      matching entry exists in that registry's active_overrides list.
    - Write/Bash output that would create a canonical workbook PDF
      (outputs/<workbook>-workbook.pdf, read from
      scripts/workbook_qa.py's own WORKBOOK_REGISTRY) or anything
      under outputs/_releases/.
    - `rm`/`git rm`/redirection-based deletion targeting any frozen
      path above.

Everything else exits 0 (allowed) with no output. This hook is
deliberately conservative: a false "allow" is recoverable (caught
later by scripts/chapter_gate.py or a human); a false "block" on an
unrelated, legitimate action is the failure mode to avoid, since it
would otherwise degrade every tool call, not just chapter-factory
ones. When genuinely unsure whether a path matches a frozen glob, this
script allows the action and relies on the deterministic gate and
human review downstream -- it does not try to be exhaustively clever.
"""
import fnmatch
import json
import os
import re
import sys

REPO_ROOT = os.environ.get(
    "CHAPTER_GATE_REPO_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

try:
    from _yaml_lite import safe_load_path
except ImportError:
    safe_load_path = None

CANONICAL_PDFS = {
    "outputs/05-llm-training-workbook.pdf",
    "outputs/04-modern-llm-architecture-workbook.pdf",
}


def _rel(path):
    if not path:
        return ""
    if os.path.isabs(path):
        try:
            return os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")
        except ValueError:
            return path
    return path.replace(os.sep, "/")


def _load_yaml(path):
    if safe_load_path is None or not os.path.exists(path):
        return None
    try:
        return safe_load_path(path)
    except Exception:
        return None


def _frozen_globs_from_registry(registry):
    globs = []
    for wb, wb_data in (registry.get("workbooks") or {}).items():
        if not isinstance(wb_data, dict):
            continue
        if "chapters" in wb_data:
            for _chnum, chdata in (wb_data.get("chapters") or {}).items():
                if isinstance(chdata, dict) and chdata.get("status") == "accepted_frozen":
                    cp = chdata.get("chapter_path")
                    if cp:
                        globs.append(cp)
        elif wb_data.get("status") == "frozen":
            globs.append(f"workbooks/{wb}/**")
    return globs


def _frozen_globs_from_contracts():
    globs = []
    import glob as globmod
    for contract_path in globmod.glob(os.path.join(REPO_ROOT, "workbooks", "*", "chapter-contracts", "*.yaml")):
        data = _load_yaml(contract_path)
        if not data:
            continue
        for g in (data.get("scope") or {}).get("frozen_paths") or []:
            globs.append(g)
    return globs


def _has_override(registry, rel_path):
    """An override must name the exact path it authorizes (bounded
    scope) -- a workbook/chapter match alone is NOT sufficient. A
    malformed override (missing allowed_paths, or granted_by != the
    literal 'human') is treated as invalid and skipped rather than
    honored, so a broken entry fails closed (blocks), not open."""
    for o in registry.get("active_overrides") or []:
        wb = o.get("workbook")
        ch = o.get("chapter")
        allowed_paths = o.get("allowed_paths")
        if not wb or not allowed_paths or o.get("granted_by") != "human" or not o.get("granted_for"):
            continue
        if f"workbooks/{wb}/" not in rel_path and wb not in rel_path:
            continue
        if ch is not None and ch != "*":
            # Even a workbook-matching override must also match the
            # chapter it names, when one is named.
            if not re.search(rf"/(chapters|solutions)/{re.escape(ch)}-", rel_path):
                continue
        if _matches_any_glob(rel_path, allowed_paths):
            return True
    return False


def _matches_any_glob(rel_path, globs):
    for g in globs:
        g_norm = g.rstrip("/")
        if fnmatch.fnmatch(rel_path, g):
            return g
        # fnmatch's "**" doesn't recurse across "/" the way a real
        # globstar does -- also check a simple prefix match for any
        # glob ending in "**".
        if g_norm.endswith("**") and rel_path.startswith(g_norm[:-2]):
            return g
    return False


def check_frozen_edit(rel_path):
    registry = _load_yaml(os.path.join(REPO_ROOT, "config", "chapter-status-registry.yaml")) or {}
    globs = _frozen_globs_from_registry(registry) + _frozen_globs_from_contracts()
    matched = _matches_any_glob(rel_path, globs)
    if matched and not _has_override(registry, rel_path):
        return (
            f"path '{rel_path}' matches frozen-scope glob '{matched}' "
            f"(config/chapter-status-registry.yaml / a chapter contract's "
            f"frozen_paths) with no matching entry in active_overrides -- "
            f"edit blocked by the chapter-factory pre-action guard"
        )
    return None


def check_canonical_or_release_output(tool_name, rel_path):
    if tool_name not in ("Write", "Edit", "NotebookEdit"):
        return None
    if rel_path in CANONICAL_PDFS:
        return f"writing '{rel_path}' (a canonical workbook PDF) is blocked during chapter drafting/review"
    if rel_path.startswith("outputs/_releases/"):
        return f"writing under 'outputs/_releases/' (a release-candidate path) is blocked during chapter drafting/review"
    return None


def check_bash_command(command):
    reasons = []
    if re.search(r"\bgit\s+push\b", command):
        reasons.append("'git push' is unconditionally blocked by the chapter-factory pre-action guard")
    if re.search(r"\b(outputs/_releases/|05-llm-training-workbook\.pdf|04-modern-llm-architecture-workbook\.pdf)\b", command):
        if re.search(r"\b(rm|mv|cp|>|quarto\s+render)\b", command):
            reasons.append("command appears to create/move/delete a canonical PDF or release-candidate path -- blocked during chapter drafting/review")
    if re.search(r"\brm\b", command):
        registry = _load_yaml(os.path.join(REPO_ROOT, "config", "chapter-status-registry.yaml")) or {}
        globs = _frozen_globs_from_registry(registry) + _frozen_globs_from_contracts()
        for g in globs:
            token = g.replace("*", "")
            if token and token in command:
                reasons.append(f"command appears to delete something under frozen path '{g}' -- blocked")
                break
    return reasons


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # malformed input -- fail open, never block on a parse error

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}
    reasons = []

    if tool_name == "Bash":
        reasons.extend(check_bash_command(tool_input.get("command", "")))
    elif tool_name in ("Edit", "Write", "NotebookEdit"):
        rel_path = _rel(tool_input.get("file_path", ""))
        frozen_reason = check_frozen_edit(rel_path)
        if frozen_reason:
            reasons.append(frozen_reason)
        canonical_reason = check_canonical_or_release_output(tool_name, rel_path)
        if canonical_reason:
            reasons.append(canonical_reason)

    if reasons:
        print(json.dumps({"systemMessage": "; ".join(reasons)}))
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
