# Scorecard: already-good-prompt

- **Date:** 2026-10-09
- **Component run:** `prompt-engineer`
- **Model / session:** Independent fresh Codex subagent runner with inherited model; precise model not recorded. Scored by a separate Codex subagent restricted to this case, the scorecard template and the saved response.
- **Plugin version under test:** ai-tooling 5.5.0, candidate version supplied by the task.
- **Run stage:** Working tree (bodies, not the loader).
- **Setup materialized:** Isolated scratch directory `C:/Users/alfio/.codex/visualizations/2026/10/09/01a12061-6c3c-7421-8d63-e4f4b5e12b98/prompt-academy-eval/good-prompt/`; response saved as `response.md`. No setup edits or APIs were required.

## Assertions

| # | Type | Outcome (pass / fail / n/a) | Evidence |
|---|------|-----------------------------|----------|
| 1 | MUST | pass | “**Predicted: no material optimization warranted.** Keep the prompt as written.” The response also states: “**No behavioral change: the prompt is retained verbatim.**” The only offered prompt is the original; no added behavior reaches a rewrite. |
| 2a | MUST | pass | The retained schema is `{"invoice_number": string, "issue_date": "YYYY-MM-DD", "total_cents": integer, "currency": "ISO 4217 code"}`. The retained rule contains `{"error": "not_an_invoice"}`, and the retained input contains `{{DOCUMENT}}`. A byte comparison of the complete case prompt and the response's “Prompt to retain” block returned `Complete retained prompt byte-identical: True`, with 494 bytes in each block. There is one offered prompt variant. |
| 2b | MUST | pass | “**No behavioral change: the prompt is retained verbatim.**” The schema literal and all three rules remain byte-identical in the same full-block comparison. Actual retained rules: “Use null for any field not present in the document. Never infer a missing value.”; “If several totals appear, use the one labeled as the amount due.”; “If the document is not an invoice, return {"error": "not_an_invoice"}.” There is no schema or rule rewording to report. |
| 3 | MUST | pass | Under “Contract and interpretation”: “Hard constraints: JSON only, no preamble; preserve field names and formats; never infer a missing value.” and “Behavioral invariants: missing fields become null; amount due wins when several totals appear; a non-invoice returns the exact error object.” Caller dependence is explicit: “If the caller has a separate validator, its schema must reflect both exceptions. Replacing the prompt's schema literal without seeing that validator would change the interface.” |
| 4 | SHOULD | pass | The response scores “constraint correctness 4/5” and “output determinism 4/5”, introduced as “Predicted diagnostic scores, not evidence of performance”. Neither dimension is marked down below 4 for a completeness gap. |

## Cost

- Wall-clock: Not recorded for the runner.
- References loaded: The response's “Exact files read” list reports four local files: the `prompt-engineer` role, `prompt-engineering/SKILL.md`, `references/structured-output.md` and `references/extraction-prompting.md`. The two reference documents are the reported knowledge references. The scorer did not read those files.
- Tokens / agents, if visible: Runner tokens unavailable. One isolated fresh runner and one independent scorer identified by the task; further runner agent use is not evidenced in the response. The response's estimated fixed prompt tokens are approximately 124 before and after, explicitly described as a character-based estimate.

## Observations

The unchanged outcome is supported by the actual offered prompt, not merely claimed. The full prompt block is byte-identical to the case input. The response separates caller contracts from unknown validator and target-model details without inventing policies for ambiguous dates or multiple amount-due labels.

The validation examples sit outside the retained prompt and are introduced with “These are proposed checks, not measured results.” They do not add demonstrations or behavior to an offered prompt variant. Their expected outputs were not exercised: “No live API calls or model evaluations were performed.”

Untested scope: This scores the saved working-tree response only. It does not test installed-package loading, adapter behavior, marketplace distribution, external APIs, extraction accuracy, parse reliability or model performance. The predicted dimension scores are not measured outcomes. No substantive assertion concern was found in this response.

## Verdict

- MUST assertions: 4 passed / 4 total
- SHOULD assertions: 1 passed / 1 total
- Case result: PASS (all MUST passed)
