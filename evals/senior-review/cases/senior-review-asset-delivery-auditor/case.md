# asset-delivery-auditor qualification case

Status: authored; no reviewer behavior has been scored.

## Coverage and target

- Reviewer: `senior-review:asset-delivery-auditor`. Content basis; review one variant in a fresh context.
- Focused T0 probes: `CL04`, `CL09`, `EX067`. Other assigned controls remain to qualify.
- Target and conclusion paths: supplied `subject.json`, copied from exactly one variant below. Admitted read scope is that target; its requirement and inventory are complete for this fixture.
- Setup: copy `defect.json` or `correct.json` to an isolated disposable directory as `subject.json`. Supply the canonical role, common conventions, report path and content basis. Never supply this case, sibling variant, prior findings or scorecard to the reviewer.
- Checks: source/configuration inspection only. No network, application execution, database, deployment, installation or removal. Report source derivations separately from runtime evidence.

## Defect oracle (scorer only)

Initial eager manifest sends 300000 measured asset bytes although only logo is required, exceeding the 100000-byte contract.

A found result must establish the reachable trigger, violated requirement and consequence from the target. Naming the pattern without its causal path is partial.

## Correct countercase and must_not_report

Lazy lookup loads only selected 100000-byte asset. No timing or blacklist-based claim.

Expect a complete no-findings result for this bounded mechanism; unrelated speculative recommendations are false positives.

## Other outcomes

Record completed applicable checks, source-only coverage and unexercised runtime. Missing required fixture or common/binding is a failed assignment with an explicit gap; do not infer a product defect. Persist the native reviewer-result with numeric confidence and `knowledge_usage: []` when no knowledge was assigned. Missing report/empty answer is not delivery. Scoring, candidate/source hashes, actual model/effort, measured cost where available and gaps belong to the run scorecard. This case does not certify every T0 control or any installed host.

## Additional independent scenarios (scorer only)

Review `additional-defect.json` and `additional-correct.json` separately, each copied as `subject.json` in a fresh context. JSON targets are complete supplied operational/configuration snapshots: declared handlers, asset/consumer inventory and effective rules are inputs, not newly executed observations. Each scenario states its own contract. Exclude this oracle and all sibling variants.

- **CL04, CL09, EX067**. Defect: Emitted optional chart violates zero-optional-byte entry requirement; CSS is gated on unrelated reports call and logo is duplicated. Countercase: Actual lazy boundary/early CSS discovery/shared transfer satisfy declared delivery requirements. No package-name blacklist or inferred page timing.
