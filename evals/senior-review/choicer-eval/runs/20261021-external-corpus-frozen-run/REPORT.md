# Gutsy input and question follow-up

Prefix mode: slot-restore.

## Observed results

| Case | Split | Input | Questions | Recall hits/support | Explicit negatives activated/support | Calls | Seconds | Complete |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F01 | development | windowed | candidate | 0/1 | 0/7 | 8 | 4.1 | True |
| F01 | development | windowed | v2 | 0/1 | 3/7 | 8 | 4.2 | True |
| F02 | development | windowed | candidate | 0/1 | 1/7 | 8 | 4.0 | True |
| F02 | development | windowed | v2 | 0/1 | 1/7 | 8 | 4.1 | True |
| F03 | development | windowed | candidate | 0/1 | 0/7 | 8 | 4.2 | True |
| F03 | development | windowed | v2 | 0/1 | 0/7 | 8 | 4.4 | True |
| F04 | development | windowed | candidate | 0/1 | 0/7 | 8 | 4.4 | True |
| F04 | development | windowed | v2 | 0/1 | 0/7 | 8 | 4.5 | True |
| F05 | development | windowed | candidate | 0/0 | 0/1 | 16 | 10.3 | True |
| F05 | development | windowed | v2 | 0/0 | 0/1 | 16 | 11.2 | True |
| F06 | development | windowed | candidate | 0/1 | 0/0 | 8 | 5.7 | True |
| F06 | development | windowed | v2 | 0/1 | 0/0 | 8 | 5.6 | True |
| F07 | development | windowed | candidate | 0/0 | 0/1 | 16 | 10.9 | True |
| F07 | development | windowed | v2 | 0/0 | 0/1 | 16 | 11.2 | True |
| F08 | development | windowed | candidate | 0/1 | 0/0 | 8 | 5.7 | True |
| F08 | development | windowed | v2 | 0/1 | 0/0 | 8 | 5.0 | True |
| F09 | development | windowed | candidate | 0/1 | 0/0 | 8 | 5.1 | True |
| F09 | development | windowed | v2 | 0/1 | 0/0 | 8 | 5.3 | True |
| F10 | development | windowed | candidate | 0/0 | 0/1 | 16 | 11.1 | True |
| F10 | development | windowed | v2 | 0/0 | 0/1 | 16 | 11.7 | True |
| F11 | development | windowed | candidate | 0/1 | 0/5 | 16 | 9.5 | True |
| F11 | development | windowed | v2 | 1/1 | 1/5 | 16 | 9.4 | True |
| F12 | development | windowed | candidate | 1/1 | 0/5 | 16 | 8.4 | True |
| F12 | development | windowed | v2 | 1/1 | 0/5 | 16 | 8.9 | True |
| F13 | development | windowed | candidate | 0/1 | 0/5 | 8 | 4.5 | True |
| F13 | development | windowed | v2 | 0/1 | 0/5 | 8 | 4.6 | True |
| F14 | development | windowed | candidate | 0/1 | 0/4 | 16 | 9.9 | True |
| F14 | development | windowed | v2 | 0/1 | 0/4 | 16 | 9.6 | True |
| F15 | development | windowed | candidate | 0/1 | 0/5 | 56 | 32.5 | True |
| F15 | development | windowed | v2 | 0/1 | 2/5 | 56 | 34.5 | True |
| F16 | development | windowed | candidate | 0/1 | 0/4 | 48 | 31.9 | True |
| F16 | development | windowed | v2 | 1/1 | 1/4 | 48 | 32.1 | True |
| F17 | development | windowed | candidate | 0/2 | 0/4 | 8 | 5.9 | True |
| F17 | development | windowed | v2 | 0/2 | 0/4 | 8 | 5.7 | True |
| F18 | development | windowed | candidate | 0/1 | 0/7 | 8 | 5.5 | True |
| F18 | development | windowed | v2 | 0/1 | 0/7 | 8 | 6.0 | True |
| F19 | development | windowed | candidate | 0/1 | 0/7 | 8 | 5.9 | True |
| F19 | development | windowed | v2 | 0/1 | 0/7 | 8 | 5.5 | True |
| F20 | development | windowed | candidate | 1/4 | 0/2 | 8 | 4.8 | True |
| F20 | development | windowed | v2 | 0/4 | 0/2 | 8 | 5.0 | True |
| F21 | development | windowed | candidate | 0/2 | 0/3 | 8 | 5.4 | True |
| F21 | development | windowed | v2 | 0/2 | 0/3 | 8 | 5.3 | True |
| F22 | development | windowed | candidate | 0/1 | 0/5 | 8 | 4.8 | True |
| F22 | development | windowed | v2 | 0/1 | 0/5 | 8 | 5.2 | True |
| F23 | development | windowed | candidate | 0/2 | 0/4 | 8 | 4.3 | True |
| F23 | development | windowed | v2 | 0/2 | 0/4 | 8 | 4.3 | True |
| F24 | development | windowed | candidate | 1/2 | 0/4 | 8 | 4.8 | True |
| F24 | development | windowed | v2 | 0/2 | 0/4 | 8 | 4.8 | True |
| F25 | development | windowed | candidate | 0/1 | 0/5 | 8 | 4.4 | True |
| F25 | development | windowed | v2 | 0/1 | 0/5 | 8 | 4.6 | True |
| F26 | development | windowed | candidate | 0/1 | 0/4 | 8 | 4.3 | True |
| F26 | development | windowed | v2 | 0/1 | 0/4 | 8 | 5.4 | True |
| F27 | development | windowed | candidate | 0/2 | 0/4 | 8 | 4.5 | True |
| F27 | development | windowed | v2 | 0/2 | 1/4 | 8 | 5.0 | True |
| F28 | verification | windowed | candidate | 0/1 | 2/7 | 16 | 10.6 | True |
| F28 | verification | windowed | v2 | 0/1 | 1/7 | 16 | 11.0 | True |
| F29 | verification | windowed | candidate | 0/1 | 0/6 | 8 | 4.8 | True |
| F29 | verification | windowed | v2 | 1/1 | 0/6 | 8 | 5.5 | True |
| F30 | verification | windowed | candidate | 0/1 | 0/7 | 8 | 6.1 | True |
| F30 | verification | windowed | v2 | 0/1 | 0/7 | 8 | 5.7 | True |
| F31 | verification | windowed | candidate | 0/1 | 0/7 | 8 | 5.0 | True |
| F31 | verification | windowed | v2 | 0/1 | 0/7 | 8 | 5.3 | True |
| F32 | verification | windowed | candidate | 0/1 | 1/7 | 16 | 9.5 | True |
| F32 | verification | windowed | v2 | 0/1 | 1/7 | 16 | 11.4 | True |
| F33 | verification | windowed | candidate | 0/1 | 0/0 | 16 | 11.8 | True |
| F33 | verification | windowed | v2 | 0/1 | 0/0 | 16 | 13.2 | True |
| F34 | verification | windowed | candidate | 0/0 | 0/1 | 8 | 5.1 | True |
| F34 | verification | windowed | v2 | 0/0 | 0/1 | 8 | 5.8 | True |
| F35 | verification | windowed | candidate | 0/0 | 0/1 | 8 | 6.3 | True |
| F35 | verification | windowed | v2 | 0/0 | 0/1 | 8 | 6.2 | True |
| F36 | verification | windowed | candidate | 0/0 | 0/1 | 8 | 6.6 | True |
| F36 | verification | windowed | v2 | 0/0 | 0/1 | 8 | 6.7 | True |
| F37 | verification | windowed | candidate | 1/2 | 0/4 | 8 | 5.2 | True |
| F37 | verification | windowed | v2 | 0/2 | 0/4 | 8 | 5.0 | True |
| F38 | verification | windowed | candidate | 0/1 | 0/3 | 8 | 6.1 | True |
| F38 | verification | windowed | v2 | 0/1 | 0/3 | 8 | 5.0 | True |
| F39 | verification | windowed | candidate | 0/1 | 0/5 | 24 | 14.3 | True |
| F39 | verification | windowed | v2 | 0/1 | 0/5 | 24 | 15.6 | True |
| F40 | verification | windowed | candidate | 0/2 | 0/4 | 32 | 18.6 | True |
| F40 | verification | windowed | v2 | 1/2 | 0/4 | 32 | 22.8 | True |
| F41 | verification | windowed | candidate | 1/2 | 0/6 | 8 | 4.8 | True |
| F41 | verification | windowed | v2 | 0/2 | 0/6 | 8 | 6.1 | True |
| F42 | verification | windowed | candidate | 0/1 | 0/4 | 40 | 26.6 | True |
| F42 | verification | windowed | v2 | 1/1 | 1/4 | 40 | 30.3 | True |
| F43 | verification | windowed | candidate | 1/2 | 0/4 | 8 | 5.0 | True |
| F43 | verification | windowed | v2 | 0/2 | 0/4 | 8 | 5.2 | True |
| F44 | verification | windowed | candidate | 0/1 | 0/3 | 8 | 9.9 | True |
| F44 | verification | windowed | v2 | 0/1 | 0/3 | 8 | 7.0 | True |
| F45 | verification | windowed | candidate | 0/2 | 0/4 | 8 | 6.4 | True |
| F45 | verification | windowed | v2 | 1/2 | 0/4 | 8 | 5.3 | True |
| F46 | verification | windowed | candidate | 0/2 | 0/4 | 8 | 4.6 | True |
| F46 | verification | windowed | v2 | 0/2 | 0/4 | 8 | 6.0 | True |
| F47 | verification | windowed | candidate | 0/1 | 0/3 | 8 | 6.1 | True |
| F47 | verification | windowed | v2 | 0/1 | 0/3 | 8 | 6.6 | True |
| F48 | verification | windowed | candidate | 0/1 | 0/5 | 16 | 10.1 | True |
| F48 | verification | windowed | v2 | 0/1 | 0/5 | 16 | 10.7 | True |
| F49 | verification | windowed | candidate | 0/1 | 0/5 | 8 | 5.5 | True |
| F49 | verification | windowed | v2 | 0/1 | 0/5 | 8 | 6.2 | True |
| F50 | verification | windowed | candidate | 1/3 | 0/5 | 8 | 6.0 | True |
| F50 | verification | windowed | v2 | 0/3 | 0/5 | 8 | 7.8 | True |
| F51 | verification | windowed | candidate | 0/1 | 1/6 | 8 | 7.9 | True |
| F51 | verification | windowed | v2 | 0/1 | 0/6 | 8 | 6.7 | True |
| F52 | verification | windowed | candidate | 0/2 | 0/4 | 8 | 5.4 | True |
| F52 | verification | windowed | v2 | 0/2 | 0/4 | 8 | 6.9 | True |

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
- Sampled combined runner/server peak RSS: 972275712 bytes. OS caches and host are excluded; sampling is not a hard OS memory cap.
- Exact prompts, raw responses, token counts, server timing/cache diagnostics, source hashes and memory samples are retained.
- Seconds count question calls only; prefix encoding, slot saves and restores are timed in COMPARISON.md.
