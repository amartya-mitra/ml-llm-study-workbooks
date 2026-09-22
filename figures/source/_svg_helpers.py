"""Tiny dependency-free SVG builder shared by figures/source/*.py scripts.

No external plotting/diagram library is available in this environment
(no pip — see reports/bootstrap_environment.md), so figures are emitted as
hand-built SVG strings. This module exists only to avoid repeating SVG
boilerplate (arrow markers, text, rounded boxes) in every figure script,
and to make every figure read `config/visual-style.yaml` instead of
hardcoding colors.
"""
from __future__ import annotations

import html
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from _yaml_lite import safe_load_path  # noqa: E402

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def load_visual_style():
    path = os.path.join(_REPO_ROOT, "config", "visual-style.yaml")
    return safe_load_path(path)


def palette_hex(style: dict) -> dict:
    """Return {semantic_name: hex} e.g. {'stored_information': '#0072B2'}."""
    return {k: v["hex"] for k, v in style["palette"].items()}


DASH_PATTERNS = {
    "solid": None,
    "dashed": "6,4",
    "dotted": "2,3",
}


class SVGCanvas:
    def __init__(self, width: int, height: int, title: str = ""):
        self.width = width
        self.height = height
        self.title = title
        self._body = []
        self._markers = set()
        self._marker_defs = []

    # -- primitives ---------------------------------------------------
    def add_rect(self, x, y, w, h, fill="#ffffff", stroke="#333333",
                 stroke_width=1.5, rx=6, dash: str | None = None):
        dash_attr = f' stroke-dasharray="{DASH_PATTERNS.get(dash) or dash}"' if dash else ""
        self._body.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"{dash_attr}/>'
        )

    def add_text(self, x, y, text, size=12, weight="normal", color="#111111",
                 anchor="start", family="Helvetica, Arial, sans-serif", mono=False):
        fam = "Menlo, Consolas, monospace" if mono else family
        self._body.append(
            f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}">'
            f'{html.escape(str(text))}</text>'
        )

    def _ensure_marker(self, color: str) -> str:
        marker_id = "arrow-" + color.replace("#", "")
        if marker_id not in self._markers:
            self._markers.add(marker_id)
            self._marker_defs.append(
                f'<marker id="{marker_id}" viewBox="0 0 10 10" refX="8" refY="5" '
                f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                f'<path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker>'
            )
        return marker_id

    def add_arrow(self, x1, y1, x2, y2, style="solid", color="#333333", stroke_width=2):
        marker_id = self._ensure_marker(color)
        dash = DASH_PATTERNS.get(style)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self._body.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{stroke_width}"{dash_attr} marker-end="url(#{marker_id})"/>'
        )

    def add_raw(self, svg_fragment: str):
        self._body.append(svg_fragment)

    # -- output ---------------------------------------------------------
    def to_string(self) -> str:
        defs = "".join(self._marker_defs)
        title_el = f"<title>{html.escape(self.title)}</title>" if self.title else ""
        body = "\n  ".join(self._body)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" '
            f'height="{self.height}" viewBox="0 0 {self.width} {self.height}">\n'
            f"  {title_el}\n"
            f"  <defs>{defs}</defs>\n"
            f'  <rect x="0" y="0" width="{self.width}" height="{self.height}" fill="#ffffff"/>\n'
            f"  {body}\n"
            f"</svg>\n"
        )

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_string())
