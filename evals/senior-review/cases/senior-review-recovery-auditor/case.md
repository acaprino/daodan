# recovery-auditor qualification case

Status: authored; no reviewer behavior has been scored.

## Coverage and target

- Reviewer: `senior-review:recovery-auditor`. Content basis; review one variant in a fresh context.
- Focused T0 probes: `EX051`, `EX052`, `EX054`, `EX055`. Other assigned controls remain to qualify.
- Target and conclusion paths: supplied `subject.json`, copied from exactly one variant below. Admitted read scope is that target; its requirement and inventory are complete for this fixture.
- Setup: copy `defect.json` or `correct.json` to an isolated disposable directory as `subject.json`. Supply the canonical role, common conventions, report path and content basis. Never supply this case, sibling variant, prior findings or scorecard to the reviewer.
- Checks: source/configuration inspection only. No network, application execution, database, deployment, installation or removal. Report source derivations separately from runtime evidence.

## Defect oracle (scorer only)

Region loss removes the only key; restoring ciphertext cannot produce readable orders.

A found result must establish the reachable trigger, violated requirement and consequence from the target. Naming the pattern without its causal path is partial.

## Correct countercase and must_not_report

Surviving key, recovery identity and relevant read exercise cover the declared scenario. No invented RTO or requirement to execute disaster recovery.

Expect a complete no-findings result for this bounded mechanism; unrelated speculative recommendations are false positives.

## Other outcomes

Record completed applicable checks, source-only coverage and unexercised runtime. Missing required fixture or common/binding is a failed assignment with an explicit gap; do not infer a product defect. Persist the native reviewer-result with numeric confidence and `knowledge_usage: []` when no knowledge was assigned. Missing report/empty answer is not delivery. Scoring, candidate/source hashes, actual model/effort, measured cost where available and gaps belong to the run scorecard. This case does not certify every T0 control or any installed host.

## Additional independent scenarios (scorer only)

Review `additional-defect.json` and `additional-correct.json` separately, each copied as `subject.json` in a fresh context. JSON targets are complete supplied operational/configuration snapshots: declared handlers, asset/consumer inventory and effective rules are inputs, not newly executed observations. Each scenario states its own contract. Exclude this oracle and all sibling variants.

- **EX052, EX053, EX054, EX055, EX056, EX057**. Defect: Expired/inconsistent/missing assets and lost replay prevent declared recovery; failback loses secondary writes; wrong-version upload exercise proves no restore objective. Countercase: Surviving consistent assets, retained replay/config, fenced failback and relevant timed service exercise support exact objectives.

## Input clarification before attempt 2

The original defect native assignment correctly failed for unavailable configuration/dependency, access and restore version/schema/validation bindings. Original bytes and its partial report remain in the run. The oracle's missing-configuration consequence was underdetermined by config=false alone. The revised fixtures explicitly bind c1 as the sole required routing configuration, its surviving backup semantics, identities, compatible immutable restore image/schemas, logical runbook and integrity validation. Retention is now explicitly measured from fresh disaster-time snapshots with no later replacement. Both variants receive equivalent operational premises; original failure transitions and correct guards are unchanged. These supplied records are source evidence, never a newly executed restore. No production reviewer body changed.

The independent encrypted-order correct scenario binds its immutable restore image to v1, matching its preexisting v1 regional-loss exercise record. The additional independent order/blob scenario uses candidate-v1. A prepared but unexecuted correct attempt2 carried the wrong label; it is retained superseded, and correct attempt3 supplies the matching label. No native reviewer saw the mismatched correct attempt.
