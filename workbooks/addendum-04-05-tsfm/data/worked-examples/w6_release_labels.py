#!/usr/bin/env python3
"""Module 6 worked example: classify each statement about one documented
release (TimesFM 3.0) by source type, and record the two pairs of
statements whose relationship the documentation does not settle.

Evidence labels:
  - REPORTED: every statement below is restated from the vendor blog or
    the model card (as of October 2026); neither is a paper, and no paper
    describing this release was found.
  - DERIVED: the source-type classification and the counts.
  - No reconciliation of the parameter-count and layer/width statements
    is attempted; none is supported by the documentation.

Source types: "documentation" (model card / README: configuration facts as
the page states them), "vendor claim" (blog statements about size,
mechanism or capability), "paper-backed" (a paper for THIS release).

Pure standard library. Run: python3 w6_release_labels.py  (writes w6_release_labels.json)
"""
import json
import os

STATEMENTS = [
    {"id": "S1", "text": "The model has 330 million parameters.", "where": "vendor blog", "type": "vendor claim"},
    {"id": "S2", "text": "The model has 20 layers, model dimension 1280 and 16 heads.", "where": "model card", "type": "documentation"},
    {"id": "S3", "text": "The context patch length is 32 and the forecast-horizon patch length is 64.", "where": "model card", "type": "documentation"},
    {"id": "S4", "text": "Patches are 32 time steps long.", "where": "vendor blog", "type": "vendor claim"},
    {"id": "S5", "text": "The whole horizon is decoded in one forward pass using placeholder tokens that the blog calls Contiguous Patch Masking.", "where": "vendor blog", "type": "vendor claim"},
    {"id": "S6", "text": "The stack alternates causal temporal attention with full variate attention.", "where": "vendor blog", "type": "vendor claim"},
    {"id": "S7", "text": "The architecture is labeled 'Stacked Mixing Transformer with Variate Attention and CPM Iterative RevIN'; the card does not define these terms.", "where": "model card", "type": "documentation"},
    {"id": "S8", "text": "The card's pointers to 'the paper' lead to the 2023 TimesFM paper, which predates this release.", "where": "model card", "type": "documentation"},
]

# Pairs the documentation leaves open; no explanation is asserted.
UNRESOLVED = [
    {"pair": ["S1", "S2"], "issue": "330 million parameters versus 20 layers, width 1280 and 16 heads: the pages do not state how, or whether, the two relate."},
    {"pair": ["S4", "S3"], "issue": "32-step patches (blog) versus context patch 32 and horizon patch 64 (card): the pages do not state how the 64 relates to the blog's description."},
    {"pair": ["S5", "S6"], "issue": "The blog says it builds on predecessors' decoder-only design and also describes whole-horizon single-pass decoding with placeholders: a documented hybrid, not plain autoregression."},
]


def main():
    types = {}
    for s in STATEMENTS:
        types[s["type"]] = types.get(s["type"], 0) + 1
    result = {
        "labels": {"statements": "reported (restated from documentation)", "classification": "derived"},
        "statements": STATEMENTS,
        "unresolved": UNRESOLVED,
        "counts_by_type": types,
        "paper_backed_count": types.get("paper-backed", 0),
        "reconciliation_attempted": False,
    }
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "w6_release_labels.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
