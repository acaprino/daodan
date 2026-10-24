# ui-race-auditor qualification case

Status: authored; no reviewer behavior has been scored.

## Coverage and target

- Reviewer: `senior-review:ui-race-auditor`. Content basis; review one variant in a fresh context.
- Focused T0 probes: `EX115`, `EX118`, `EX122`. Other assigned controls remain to qualify.
- Target and conclusion paths: supplied `subject.mjs`, copied from exactly one variant below. Admitted read scope is that target; its requirement and inventory are complete for this fixture.
- Setup: copy `defect.mjs` or `correct.mjs` to an isolated disposable directory as `subject.mjs`. Supply the canonical role, common conventions, report path and content basis. Never supply this case, sibling variant, prior findings or scorecard to the reviewer.
- Checks: source/configuration inspection only. No network, application execution, database, deployment, installation or removal. Report source derivations separately from runtime evidence.

## Defect oracle (scorer only)

A starts, B starts, B resolves/renders, then A resolves/renders stale result; latest-result contract fails.

A found result must establish the reachable trigger, violated requirement and consequence from the target. Naming the pattern without its causal path is partial.

## Correct countercase and must_not_report

Generation check rejects A after B is issued; no requirement to cancel billing/network activity for display correctness.

Expect a complete no-findings result for this bounded mechanism; unrelated speculative recommendations are false positives.

## Other outcomes

Record completed applicable checks, source-only coverage and unexercised runtime. Missing required fixture or common/binding is a failed assignment with an explicit gap; do not infer a product defect. Persist the native reviewer-result with numeric confidence and `knowledge_usage: []` when no knowledge was assigned. Missing report/empty answer is not delivery. Scoring, candidate/source hashes, actual model/effort, measured cost where available and gaps belong to the run scorecard. This case does not certify every T0 control or any installed host.

## Additional independent scenarios (scorer only)

Review `additional-defect.mjs` and `additional-correct.mjs` separately, each copied as `subject.mjs` in a fresh context. JSON targets are complete supplied operational/configuration snapshots: declared handlers, asset/consumer inventory and effective rules are inputs, not newly executed observations. Each scenario states its own contract. Exclude this oracle and all sibling variants.

- **EX116, EX117, EX118, EX119, EX120, EX121, EX122**. Defect: Delayed focus ignores closure, resize captures old geometry, sticky action misses later layout, independent hook owners diverge, queued IPC reaches destroyed view. Each needs its own ordering and user effect. Countercase: Lifetime token, current measurement, content observer respecting user scroll, shared subscriber state and destroyed-view guard prevent those precise interleavings. Static CSS barriers must not be invented.
