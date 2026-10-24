# Gutsy input and question follow-up

Prefix mode: slot-restore.

## Observed results

| Case | Split | Input | Questions | Recall hits/support | Explicit negatives activated/support | Calls | Seconds | Complete |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | historical | truncated | v2 | 0/2 | 0/0 | 8 | 5.3 | True |
| C01 | historical | windowed | v2 | 1/2 | 0/0 | 24 | 17.3 | True |
| C07 | historical | truncated | v2 | 3/5 | 0/0 | 8 | 4.8 | True |
| C07 | historical | windowed | v2 | 4/5 | 0/0 | 312 | 208.2 | True |
| E01 | development | windowed | candidate | 0/2 | 0/3 | 8 | 5.4 | True |
| E01 | development | windowed | v2 | 0/2 | 0/3 | 8 | 5.4 | True |
| E02 | development | windowed | candidate | 1/1 | 0/3 | 8 | 5.0 | True |
| E02 | development | windowed | v2 | 0/1 | 0/3 | 8 | 5.3 | True |
| E03 | development | windowed | candidate | 2/3 | 0/2 | 16 | 12.0 | True |
| E03 | development | windowed | v2 | 1/3 | 0/2 | 16 | 11.5 | True |
| E04 | development | windowed | candidate | 0/0 | 0/6 | 8 | 5.5 | True |
| E04 | development | windowed | v2 | 0/0 | 0/6 | 8 | 6.3 | True |
| E05 | verification | windowed | candidate | 2/3 | 0/2 | 8 | 5.9 | True |
| E05 | verification | windowed | v2 | 3/3 | 0/2 | 8 | 5.7 | True |
| E06 | verification | windowed | candidate | 0/0 | 0/6 | 8 | 4.7 | True |
| E06 | verification | windowed | v2 | 0/0 | 0/6 | 8 | 5.0 | True |
| E07 | verification | windowed | candidate | 1/1 | 0/4 | 8 | 5.6 | True |
| E07 | verification | windowed | v2 | 0/1 | 0/4 | 8 | 4.9 | True |
| E08 | verification | windowed | candidate | 1/1 | 0/4 | 8 | 4.9 | True |
| E08 | verification | windowed | v2 | 1/1 | 0/4 | 8 | 4.7 | True |

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
- Sampled combined runner/server peak RSS: 968966144 bytes. OS caches and host are excluded; sampling is not a hard OS memory cap.
- Exact prompts, raw responses, token counts, server timing/cache diagnostics, source hashes and memory samples are retained.
- Seconds count question calls only; prefix encoding, slot saves and restores are timed in COMPARISON.md.
