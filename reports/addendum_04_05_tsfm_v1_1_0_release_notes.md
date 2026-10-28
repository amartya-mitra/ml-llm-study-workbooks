Addendum 04–05, Time-Series Foundation Models — **version 1.1.0** (Final Edition, 23 pages).

**What's new.** Mistral's Timestral (released 15 October 2026) is integrated into all six modules: causal per-patch scaling and missing-value flags (Module 1); target, past-only and known-future covariate roles and the variate-attention firewall (Module 2); Decoupled Horizon Forecasting — learned forecast tokens instead of masked placeholders — and block-by-block long-horizon rollout, with a new figure (Module 3); 21 non-crossing quantiles (Module 4); the synthetic-first, two-stage training recipe and its leakage limits (Module 5); and reading a release from its pinned inference code (Module 6). Each module keeps its *Quick recap from LLMs*, adapted where Timestral connects to it (for example, teacher forcing as an explicitly labeled analogy for DHF).

**Evidence discipline.** Timestral has no paper yet. Vendor claims (training recipe, benchmark standing) are labeled as such and were not independently verified; documentation facts come from the model cards and configuration files; mechanisms are code-verified for **inference only**, against `mistralai/timestral` pinned to commit `a534bdbd244d64f3d9d743f46c7bf6fc330ed4ff`. Source disagreements (categorical covariates, a metric label) are kept open. The inference code is Apache-2.0; the weights carry a separate "Modified MIT" license, quoted without interpretation.

- Pages: 23
- SHA-256 of the attached PDF: `68467ffb62bbf7734bb97e4387d5956349811d6d211b5d12501c5166b87d6ea2`
- Source commit: `00f3bb63185114f0c2231703cd2ea93394f77ac2`
- Previous edition: [v1.0.0](https://github.com/amartya-mitra/ml-llm-study-workbooks/releases/tag/addendum-04-05-tsfm-v1.0.0) (18 pages), unchanged.
