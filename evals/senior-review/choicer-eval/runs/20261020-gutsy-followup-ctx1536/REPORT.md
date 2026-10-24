# Gutsy input and question follow-up

## Observed results

| Case | Split | Input | Questions | Recall hits/support | Explicit negatives activated/support | Calls | Seconds | Complete |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | historical | truncated | v2 | 0/2 | 0/0 | 8 | 50.8 | True |
| C01 | historical | windowed | v2 | 1/2 | 0/0 | 24 | 102.9 | True |
| C07 | historical | truncated | v2 | 3/5 | 0/0 | 8 | 57.1 | True |
| C07 | historical | windowed | v2 | 4/5 | 0/0 | 312 | 1387.1 | True |
| E01 | development | windowed | candidate | 0/2 | 0/3 | 8 | 26.5 | True |
| E01 | development | windowed | v2 | 0/2 | 0/3 | 8 | 25.7 | True |
| E02 | development | windowed | candidate | 1/1 | 0/3 | 8 | 16.7 | True |
| E02 | development | windowed | v2 | 0/1 | 0/3 | 8 | 16.9 | True |
| E03 | development | windowed | candidate | 2/3 | 0/2 | 16 | 43.9 | True |
| E03 | development | windowed | v2 | 1/3 | 0/2 | 16 | 46.5 | True |
| E04 | development | windowed | candidate | 0/0 | 0/6 | 8 | 19.8 | True |
| E04 | development | windowed | v2 | 0/0 | 0/6 | 8 | 16.0 | True |
| E05 | verification | windowed | candidate | 2/3 | 0/2 | 8 | 20.3 | True |
| E05 | verification | windowed | v2 | 3/3 | 0/2 | 8 | 20.0 | True |
| E06 | verification | windowed | candidate | 0/0 | 0/6 | 8 | 20.3 | True |
| E06 | verification | windowed | v2 | 0/0 | 0/6 | 8 | 19.0 | True |
| E07 | verification | windowed | candidate | 1/1 | 0/4 | 8 | 29.8 | True |
| E07 | verification | windowed | v2 | 0/1 | 0/4 | 8 | 28.8 | True |
| E08 | verification | windowed | candidate | 1/1 | 0/4 | 8 | 16.9 | True |
| E08 | verification | windowed | v2 | 1/1 | 0/4 | 8 | 17.8 | True |

## Boundaries

- Historical input packing changes only; handwritten V2 context is fixed, not authenticated map evidence.
- All full-window source characters are retained. Windows may split functions and lose cross-window context.
- New cases are real pinned source snippets, not independently verified production defects. Applicability labels are partial and authored by the coordinator.
- Development and verification use distinct files in one project; neither establishes cross-project generalization.
- Candidate wording and Yes/No options are one joint prompt treatment, frozen before outcomes. No claim isolates individual wording changes.
- Model selections and inherited filename-based baseline selections are recorded separately. No added static cleanup rule.
- A is activation, B is negative, Z is abstention; missing or invalid output is incomplete coverage.
- Raw vocabulary probabilities are uncalibrated diagnostics. No top-k omission is interpreted as zero.
- Union can improve recall by activating more reviewers. Excess against partial labels is not a measured false-positive rate.
- No semantic citation validation, map integration, full-catalog, premise-positive or live downstream reviewer test was performed.
- Sampled combined runner/server peak RSS: 977641472 bytes. OS caches and host are excluded; sampling is not a hard OS memory cap.
- Exact prompts, raw responses, token counts, server timing/cache diagnostics, source hashes and memory samples are retained.
