# RC Report Template — Workbook 05

This is a **template**, not a specific release candidate's report.
Copy it to `reports/05_release_candidate_N_report.md` for each actual
RC, filling in every field. Do not leave a field as the placeholder
text below — an unfilled field is a QA failure in itself (see
`scripts/workbook_qa.py`'s `unresolved_placeholders` check, which would
correctly flag a copy of this template committed unfilled).

---

## RC report — Workbook 05, RC<N>

- **Commit SHA:** `<full sha>`
- **Branch:** `main` (or the experiment branch, if one was used)
- **Fixed QA command:** `python3 scripts/workbook_qa.py --workbook 05-llm-training`
- **QA result:** `<pass|fail>` — full JSON at
  `outputs/_development/05-llm-training/qa-runs/<short-sha>/qa-summary.json`
- **RC PDF path:** `outputs/_releases/05-llm-training/05-llm-training-workbook-rc<N>.pdf`
- **Page count:** `<n>`
- **Word count:** `<n>`
- **Rendered pages:** `outputs/_development/05-llm-training/qa-runs/<short-sha>/pages/`
- **Contact sheet:** `outputs/_development/05-llm-training/qa-runs/<short-sha>/contact-sheet.html`

## What changed since the prior RC

<one paragraph or a short list — what this RC fixes or adds, and why>

## QA findings

<copy the relevant fields from qa-summary.json's `steps.text_checks` and
`steps.tests` here, or state "none" if clean>

## Full-document visual inspection

<record what was actually opened and checked — which pages, at what
resolution, and what was confirmed. "Not yet performed" is an honest
and acceptable value here; do not claim an inspection that did not
happen>

## Findings fixed in this RC (carried from the prior RC's report)

<list, or "none carried forward">

## Findings deferred to a later RC

<list with reasoning, or "none">

## Disposition

`<accepted | needs another RC | rejected>` — if accepted, state
explicitly that this RC is now frozen and will not be edited; any
further fix becomes the next RC's commit, not an edit to this one.
