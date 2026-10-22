# Scorecard: <case> / <command>

- **Date:**
- **Command run:** `/daodan:review-changes` | `/daodan:review-branch` | vanilla `/code-review`
- **Model / session:**
- **Review scope given:**
- **Setup attestation (synthetic inline cases):** base commit, `review_rev`, materialized file list with hashes, fresh session yes/no, case file never exposed to the reviewer yes/no. A missing or negative attestation invalidates the scores.

## Ground-truth bugs

| # | Known bug | Expected dimension | Outcome (found / partial / missed) | Found by dimension | Notes |
|---|-----------|--------------------|------------------------------------|--------------------|-------|

## False positives

| # | Reported finding | Why it is not real | Survived verification panel? |
|---|------------------|--------------------|------------------------------|

## Anti-findings (must_not_report)

| # | Claim that must not be reported | Status in case (false / unverifiable) | Outcome (avoided / reported / caught) | Lens that caught it (if caught) |
|---|----------------------------------|----------------------------------------|----------------------------------------|----------------------------------|

## Metrics

- Recall: X / N (partial = 0.5)
- Anti-finding rate: reported / total must_not_report entries
- False-positive rate: FP / total findings
- Quantitative claims: measured N, derived N, unlabeled N
- Cost: wall-clock, agents spawned, tokens if visible

## Observations

[What the pipeline did well or badly on this case: dimension routing, verification kills, critic gaps, delivery discipline.]
