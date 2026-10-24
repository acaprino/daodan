# senior-review eval harness

Measures whether the senior-review architecture actually produces a more senior reviewer, and which components pay for themselves. Each case declares its review basis and **known ground truth**: bugs that were really there, established either by a production post-mortem, by the fix commit that later landed, or by deliberate injection. A run reviews the materialized target or facts packet and scores what it found. Diff cases replay the pre-fix state.

This directory is a development asset of the marketplace repository. It is not part of the `senior-review` plugin, is not registered in `marketplace.json`, and is never shipped.

## Diff review protocol

For each diff case in `cases/`:

1. **Prepare the target.** Check out the case's `repo` at `review_rev` in a scratch worktree (`git worktree add <tmp> <review_rev>`). The bugs listed in the case are present at that revision.
2. **Run one command per scorecard row**, scoped as the case specifies:
   - `/daodan:review-changes` (scope per the case's `review_scope`)
   - `/daodan:review-branch <review_scope>`
   - Claude Code's built-in `/code-review` as the vanilla baseline
   Run each in a FRESH session so no context leaks between runs, and never in the same session that is scoring.
3. **Score against the ground truth.** For every bug in the case's table: `found` (a finding matches the defect, regardless of wording), `partial` (the right location or mechanism but the wrong conclusion), `missed`. Matching is by mechanism, not by phrasing.

   A case may also carry a `must_not_report` block. Each entry is a claim the review must NOT produce at that revision, because it is false at the system level even though a plausible local reading supports it. Scoring an entry: `avoided` (no finding matches the claim), `reported` (a finding matching the claim survived the pipeline's own verification), `caught` (a finding matching the claim was produced but killed by the verification panel, and the record names the lens that killed it). Only `reported` is a failure. `caught` is the outcome the panel exists to produce, and the case notes which lens did it.
4. **Count false positives.** Findings that survive the pipeline's own verification but do not correspond to a real defect at that revision. Pre-existing findings correctly tagged `[PRE-EXISTING]` are excluded from the FP count.
5. **Record whole-run cost**: preparation, context loading, tool calls and reads, review, verification, retries, dispatch count and wall-clock time; record input/output tokens where exposed. Keep measured values distinct from estimates. Unobservable costs stay `not measured`, never zero.
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

## Specialist qualification

Use the [specialist cases and leaf template](specialist-cases.md) for T1–T7.
This is a manual application of the existing protocol and scorecards, with no
new runner, runtime registry or result schema. Catalog membership, successful
rendering, prompt keywords and fixture existence do not establish effectiveness.

1. **Fix an independent oracle before authoring.** Link each covered T0 control
   to a reachable defect and a correct countercase, with requirements, trigger,
   violated mechanism, observable consequence and `must_not_report` claims.
   Reuse a fixture when its setup actually establishes that mechanism. A separate
   scorer checks the oracle against source and requirements; the new reviewer
   body cannot define its own expected answer.
2. **Bind each run.** Record specialist/provider identity, host/version, model,
   effort, permissions, review basis, conclusion paths and admitted read scope.
   Materialize and retain the target file list and hashes, base/candidate commits
   where relevant, and any dirty or untracked candidate bytes. Hash the actual
   reviewer body, common conventions, required references and assigned knowledge;
   record catalog bindings and output path. For facts-only cases hash the packet.
   A commit ID alone does not describe a dirty candidate. Full/dir cases use
   current content; doc/spec/plan cases judge claims under their own method.
3. **Dispatch a fresh reviewer.** Give only the materialized target/packet,
   authorized brief, registered role or method, common conventions and assigned
   knowledge. Exclude the case oracle, expected outcomes, scorecard, prior runs
   and peer findings from its context and supplied workspace. Do not inherit the
   author/scorer conversation. Preserve the exact input and session identity;
   record isolation limits. A contaminated or unverifiable setup cannot qualify
   a specialist. Keep the scorer in a different context from the reviewer.
4. **Preserve the actual delivery.** Save the native report and existing
   reviewer-result fields, including scope/check coverage, findings, gaps and
   knowledge usage. Keep tool outcomes and whole-run cost alongside the
   scorecard, referencing artifacts instead of copying source. A complete
   no-findings run has `findings: []` and coverage; an empty response is not a
   delivery. Missing required input/checks makes the assignment failed while
   retaining partial evidence. Input, tool and delivery failures are review
   failures or gaps, never synthetic product defects.
5. **Score separately.** Copy [scorecard-template.md](scorecard-template.md),
   identifying the specialist invocation in Command run and the bindings,
   coverage and limitations in Setup attestation/Observations; investigation
   cases keep their own scorecard. Match mechanisms, use `found/partial/missed`
   and `avoided/reported/caught`, and inspect other findings for false positives.
   An external scorer rejecting a leaf's false finding does not earn `caught`:
   that outcome requires the reviewed pipeline's own recorded verification.
6. **Accept only the evidenced scope.** Required defects must be found, required
   correct alternatives must not remain reported, and required deliveries and
   coverage must pass. Partial recall, an untested control or unavailable required
   capability leaves qualification open. Record actual outcomes, failures and
   gaps in the scorecard and link them from the migration matrix. Changes to the
   body, references, knowledge or target invalidate the affected result binding;
   retain previous records and rerun affected cases, never relabel old scores.

Record static reading and runtime exercise separately. A source-derived result
can qualify a static check; it cannot attest execution. Run only authorized
checks in the disposable target and retain the actual command/output/candidate.
Tests of catalog dispatch, knowledge accounting and delivery gates establish
those specific mechanical contracts. Detection of an arbitrary missing domain
input, truthful coverage and causal correctness still require reviewer and
coordinator checks; do not claim a universal runtime enforcer.

For comparisons, keep target, scope, permissions, model/effort and required
knowledge equivalent across the broad reviewer, leaves and composition. Compare
required defects, anti-findings, gaps and cost together. Fewer prompt words alone
prove neither token savings nor preserved effectiveness. Dispatch of one shared
worker type cannot satisfy a different method binding or scope.

Existing cases and the 22 October smoke runs are evidence to inspect, not
qualification of new leaves. The [T0 migration findings](../../docs/superpowers/reports/2026-10-23-reviewer-specialist-migration.md)
identify two setups needing correction before affected scores count:

- `synthetic-payment-double-insert`, bug 3: the shown retry encounters the
  persisted row and raises before the gateway call. Establish a reachable
  duplicate-charge path or correct that oracle before qualifying remote effects.
- `synthetic-retry-storm`, bug 1: lack of backoff/cap alone is insufficient.
  Supply the actual workload/progress requirement and a valid bounded or
  otherwise safe retry countercase; a derived daily count proves no harm alone.

Preserve historical scorecards and RESULTS entries. Record an oracle correction
with its reason and affected runs, then create new results on the corrected
snapshot; do not rewrite old outcomes as if they used the new setup.

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
