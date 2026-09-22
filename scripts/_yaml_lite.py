"""Minimal, dependency-free YAML-subset reader.

This project's environment has no `pip`/`ensurepip`, so PyYAML is not
installable without a network-based bootstrap step outside the scope of
routine validation. All YAML files in this repo are authored by hand and
kept within a deliberately restricted subset (see AGENTS.md / bootstrap
report for the tradeoff), so a small hand-rolled loader is sufficient and
avoids a hidden runtime dependency.

Supported subset:
    - block mappings ("key: value") and block sequences ("- item")
    - nesting via 2-space indentation
    - scalars: null/~, true/false, int, float, single/double-quoted
      strings, plain (unquoted) strings
    - inline flow sequences: [a, b, "c d"]
    - comments starting with '#' outside of quotes
    - blank lines

NOT supported: anchors/aliases, block scalars (| or >), flow mappings,
multi-document streams, tabs. If you need one of these, install PyYAML
in a user-local virtualenv instead of extending this file.
"""
from __future__ import annotations

import re

__all__ = ["safe_load", "safe_load_path", "YamlLiteError"]


class YamlLiteError(ValueError):
    pass


def _strip_comment(line: str) -> str:
    out = []
    in_single = False
    in_double = False
    for ch in line:
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            break
        out.append(ch)
    return "".join(out).rstrip()


def _parse_scalar(text: str):
    text = text.strip()
    if text == "" or text in ("null", "~", "Null", "NULL"):
        return None
    if text in ("true", "True", "TRUE"):
        return True
    if text in ("false", "False", "FALSE"):
        return False
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        return text[1:-1].replace('\\"', '"')
    if len(text) >= 2 and text[0] == "'" and text[-1] == "'":
        return text[1:-1].replace("''", "'")
    if text.startswith("[") and text.endswith("]"):
        return _parse_flow_list(text)
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if re.fullmatch(r"-?\d+\.\d+", text):
        return float(text)
    return text


def _parse_flow_list(text: str):
    inner = text[1:-1].strip()
    if inner == "":
        return []
    items = []
    depth = 0
    in_single = in_double = False
    current = []
    for ch in inner:
        if ch == "'" and not in_double:
            in_single = not in_single
            current.append(ch)
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            current.append(ch)
            continue
        if not in_single and not in_double:
            if ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1
            elif ch == "," and depth == 0:
                items.append("".join(current))
                current = []
                continue
        current.append(ch)
    if current:
        items.append("".join(current))
    return [_parse_scalar(i) for i in items]


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _preprocess(text: str):
    lines = []
    for raw in text.splitlines():
        if "\t" in raw:
            raise YamlLiteError("tabs are not supported in yaml-lite files")
        stripped = _strip_comment(raw)
        if stripped.strip() == "":
            continue
        lines.append(stripped)
    return lines


def _parse_block(lines, start, indent):
    """Parse a block (mapping or sequence) starting at lines[start] with
    the given indent. Returns (value, next_index)."""
    if start >= len(lines):
        return None, start
    first = lines[start]
    if _indent_of(first) != indent:
        raise YamlLiteError(f"unexpected indent at line: {first!r}")
    if first.lstrip().startswith("- "):
        return _parse_sequence(lines, start, indent)
    return _parse_mapping(lines, start, indent)


def _parse_sequence(lines, start, indent):
    items = []
    i = start
    while i < len(lines):
        line = lines[i]
        if _indent_of(line) != indent or not line.lstrip().startswith("-"):
            break
        content = line.lstrip()[1:]
        if content.startswith(" "):
            content = content[1:]
        item_indent = indent + 2
        if content.strip() == "":
            value, i = _parse_block(lines, i + 1, item_indent)
            items.append(value)
            continue
        if re.match(r"^[A-Za-z0-9_\-]+:\s*", content) and (
            ":" in content
        ) and not content.strip().startswith(("[", '"', "'")):
            key, _, rest = content.partition(":")
            key = key.strip()
            rest = rest.strip()
            entry = {}
            if rest == "":
                nested, i = _parse_block(lines, i + 1, item_indent + 2)
                entry[key] = nested
            else:
                entry[key] = _parse_scalar(rest)
                i += 1
            while i < len(lines) and _indent_of(lines[i]) == item_indent and not lines[i].lstrip().startswith("-"):
                k2, v2, i = _parse_mapping_line(lines, i, item_indent)
                entry[k2] = v2
            items.append(entry)
            continue
        items.append(_parse_scalar(content))
        i += 1
    return items, i


def _parse_mapping_line(lines, i, indent):
    line = lines[i]
    content = line.lstrip()
    key, _, rest = content.partition(":")
    key = key.strip()
    rest = rest.strip()
    if rest == "":
        value, i2 = _parse_block(lines, i + 1, indent + 2)
        return key, value, i2
    return key, _parse_scalar(rest), i + 1


def _parse_mapping(lines, start, indent):
    result = {}
    i = start
    while i < len(lines) and _indent_of(lines[i]) == indent and not lines[i].lstrip().startswith("-"):
        key, value, i = _parse_mapping_line(lines, i, indent)
        result[key] = value
    return result, i


def safe_load(text: str):
    lines = _preprocess(text)
    if not lines:
        return None
    value, i = _parse_block(lines, 0, 0)
    if i != len(lines):
        raise YamlLiteError(f"trailing unparsed content at line: {lines[i]!r}")
    return value


def safe_load_path(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return safe_load(f.read())
