# dependency-usage-auditor qualification case

Status: authored; no reviewer behavior has been scored.

## Coverage and target

- Reviewer: `senior-review:dependency-usage-auditor`. Content basis; review one variant in a fresh context.
- Focused T0 probes: `CL06`, `CL07`, `CL19`. Other assigned controls remain to qualify.
- Target and conclusion paths: supplied `subject.json`, copied from exactly one variant below. Admitted read scope is that target; its requirement and inventory are complete for this fixture.
- Setup: copy `defect.json` or `correct.json` to an isolated disposable directory as `subject.json`. Supply the canonical role, common conventions, report path and content basis. Never supply this case, sibling variant, prior findings or scorecard to the reviewer.
- Checks: source/configuration inspection only. No network, application execution, database, deployment, installation or removal. Report source derivations separately from runtime evidence.

## Defect oracle (scorer only)

formatkit is declared in app while shared alone imports it, so independently installed shared fails. Recommend declaring it in its consumer and verify app usage before removal.

A found result must establish the reachable trigger, violated requirement and consequence from the target. Naming the pattern without its causal path is partial.

## Correct countercase and must_not_report

Proper owner declares formatkit; lintkit is consumed by build script and lockfile is retained, not unused runtime content.

Expect a complete no-findings result for this bounded mechanism; unrelated speculative recommendations are false positives.

## Other outcomes

Record completed applicable checks, source-only coverage and unexercised runtime. Missing required fixture or common/binding is a failed assignment with an explicit gap; do not infer a product defect. Persist the native reviewer-result with numeric confidence and `knowledge_usage: []` when no knowledge was assigned. Missing report/empty answer is not delivery. Scoring, candidate/source hashes, actual model/effort, measured cost where available and gaps belong to the run scorecard. This case does not certify every T0 control or any installed host.

## Additional independent scenarios (scorer only)

Review `additional-defect.json` and `additional-correct.json` separately, each copied as `subject.json` in a fresh context. JSON targets are complete supplied operational/configuration snapshots: declared handlers, asset/consumer inventory and effective rules are inputs, not newly executed observations. Each scenario states its own contract. Exclude this oracle and all sibling variants.

- **CL06, CL07, CL19**. Defect: Runtime codec is installed only as development dependency and unavailable to standalone runtime; unused_runtime has no consumer in complete inventory. Countercase: Runtime codec declared correctly, dynamic_driver config/loader and compiler build command prove use; neither dev tools nor lockfile is cruft.
