# senior-review eval harness

Measures whether the senior-review architecture actually produces a more senior reviewer, and which components pay for themselves. Each case is a diff with a **known ground truth**: bugs that were really there, established either by a production post-mortem, by the fix commit that later landed, or by deliberate injection. A run replays the review against the pre-fix state and scores what it found.

This directory is a development asset of the marketplace repository. It is not part of the `senior-review` plugin, is not registered in `marketplace.json`, and is never shipped.

## Protocol

For each case in `cases/`:

1. **Prepare the target.** Check out the case's `repo` at `review_rev` in a scratch worktree (`git worktree add <tmp> <review_rev>`). The bugs listed in the case are present at that revision.
2. **Run one command per scorecard row**, scoped as the case specifies:
   - `/daodan:review-changes` (scope per the case's `review_scope`)
   - `/daodan:review-branch <review_scope>`
   - Claude Code's built-in `/code-review` as the vanilla baseline
   Run each in a FRESH session so no context leaks between runs, and never in the same session that is scoring.
3. **Score against the ground truth.** For every bug in the case's table: `found` (a finding matches the defect, regardless of wording), `partial` (the right location or mechanism but the wrong conclusion), `missed`. Matching is by mechanism, not by phrasing.

   A case may also carry a `must_not_report` block. Each entry is a claim the review must NOT produce at that revision, because it is false at the system level even though a plausible local reading supports it. Scoring an entry: `avoided` (no finding matches the claim), `reported` (a finding matching the claim survived the pipeline's own verification), `caught` (a finding matching the claim was produced but killed by the verification panel, and the record names the lens that killed it). Only `reported` is a failure. `caught` is the outcome the panel exists to produce, and the case notes which lens did it.
4. **Count false positives.** Findings that survive the pipeline's own verification but do not correspond to a real defect at that revision. Pre-existing findings correctly tagged `[PRE-EXISTING]` are excluded from the FP count.
5. **Record cost**: wall-clock time and, where visible, token spend or agent count.
6. Fill a copy of `scorecard-template.md` into the case directory (`scorecard-<command>-<date>.md`) and add one row to `RESULTS.md`.

### Deterministic setup for synthetic inline cases

A case that carries its buggy code inline is materialized the same way by every operator:

1. Create an empty scratch repository and make one empty base commit.
2. Materialize exactly the files the case lists, verbatim, in a second commit. That commit is the case's `review_rev`.
3. The review scope is the literal file list the case states, reviewed as the diff of base to `review_rev`.

A reviewer receives the materialized files and diff only, never the case file. A setup that exposes more or fewer files is a protocol violation by the coordinator, and its scores do not count.

### Investigation variant

A case may declare `Mode: investigation` instead of a diff. It has no repository target and no `review_rev`. The reviewer receives exactly the facts packet the case states, verbatim, in a fresh session, and investigates the observed behaviour through `senior-review`'s investigation method. The scored output is the investigation report (`investigation.md`): ground-truth rows are expected outcomes, scored `found` / `partial` / `missed` by the same mechanism matching, and `must_not_report` rows keep the `avoided` / `reported` / `caught` scoring, with the killing lens recorded when the investigation's own verification produced and then killed the claim. Score it with `scorecard-investigation-template.md`. Running an investigation case as a diff review, or scoring it with the diff scorecard, is a failed setup whose results do not count.

Packet-only binding: when the case states no code target, the packet is the whole perimeter. Investigation steps that require named symbols or a current codebase (map perimeter, reproduction test, bisection) do not apply and are not scored; the case states what replaces them, normally the decisive external evidence for each open hypothesis. In this variant `measured` in the case and the scorecard is the investigation method's `observed` (a fact from a log or a run), and reviewer-computed numbers are `derived` under both names. Conclusions the report asserts as established beyond the packet and its own derivations are false conclusions for the scorecard's precision section, whether or not a `must_not_report` row names them.

## Metrics

- **Recall** = found / total known bugs (partial counts 0.5).
- **FP rate** = false positives / total findings reported.
- **Dimension attribution**: which dimension found each true positive. This is the metric that says which auditors earn their keep.
- **Evidence discipline**: fraction of quantitative claims labeled `measured` vs `derived` vs unlabeled.
- **Anti-finding rate** = `reported` / total `must_not_report` entries. This measures precision against known-plausible falsehoods, which recall cannot see. A pipeline that finds every real bug and also reports a confident falsehood is not a better reviewer.

## Rules

- Never fix anything during a run. The review is observational; the worktree is discarded afterwards.
- Never tell the reviewer what the known bugs are. The case file is for the scorer, not for the reviewed session.
- A case whose ground truth turns out wrong (the "bug" was not real at that revision) gets corrected in the case file, with a note, before its runs count.

## Case sources

| Source | Cases |
|---|---|
| Jupiter updater post-mortem (2026-08-10, production ground truth) | `jupiter-updater` |
| Jupiter fix-commit history (bug = what the later fix commit repaired) | `jupiter-market-state-tristate`, `jupiter-economic-events-upsert`, `jupiter-cache-convergence`, `jupiter-trade-failure-drop`, `jupiter-position-notice-owner` |
| Synthetic, bug injected by construction (targets the newest dimensions) | `synthetic-payment-double-insert`, `synthetic-cache-stale-read`, `synthetic-connection-pool-leak`, `synthetic-retry-storm` |
| Synthetic, from the 2026-10-20 stuck session analysis (shared coordinator epoch, single-turn frontier, log-driven latency) | `synthetic-shared-coordinator-epoch`, `synthetic-single-turn-frontier`, `synthetic-session-log-latency` |
| Jupiter false-positive incident (2026-08-10, precision ground truth) | `jupiter-credential-refill` |

Synthetic cases carry their buggy code inline in the case file; materialize it into a scratch repo before running (instructions per case).
