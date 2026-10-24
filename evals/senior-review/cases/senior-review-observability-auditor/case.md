# observability-auditor qualification case

Status: authored; no reviewer behavior has been scored.

## Coverage and target

- Reviewer: `senior-review:observability-auditor`. Content basis; review one variant in a fresh context.
- Focused T0 probes: `EX039`, `EX040`, `EX041`, `EX130`. Other assigned controls remain to qualify.
- Target and conclusion paths: supplied `subject.py`, copied from exactly one variant below. Admitted read scope is that target; its requirement and inventory are complete for this fixture.
- Setup: copy `defect.py` or `correct.py` to an isolated disposable directory as `subject.py`. Supply the canonical role, common conventions, report path and content basis. Never supply this case, sibling variant, prior findings or scorecard to the reviewer.
- Checks: source/configuration inspection only. No network, application execution, database, deployment, installation or removal. Report source derivations separately from runtime evidence.

## Defect oracle (scorer only)

Reachable job exception is swallowed without required diagnostic event or correlation.

A found result must establish the reachable trigger, violated requirement and consequence from the target. Naming the pattern without its causal path is partial.

## Correct countercase and must_not_report

Equivalent event channel fulfills contract without a logger vendor, stack dump, PII or rethrow.

Expect a complete no-findings result for this bounded mechanism; unrelated speculative recommendations are false positives.

## Other outcomes

Record completed applicable checks, source-only coverage and unexercised runtime. Missing required fixture or common/binding is a failed assignment with an explicit gap; do not infer a product defect. Persist the native reviewer-result with numeric confidence and `knowledge_usage: []` when no knowledge was assigned. Missing report/empty answer is not delivery. Scoring, candidate/source hashes, actual model/effort, measured cost where available and gaps belong to the run scorecard. This case does not certify every T0 control or any installed host.

## Additional independent scenarios (scorer only)

Qualification correction: the original exporter packet declared buffering and
no shutdown flush but did not establish loss (periodic export or durable replay
could still deliver). The defective variant now declares the sole volatile export
path, an event pending at termination before the periodic export, and no replay.
This makes the five-minute delivery violation reachable. The original trial and
its explicit uncertainty remain preserved; only a fresh run on these bytes may
qualify this mechanism. The correct flush-enabled counterpart is unchanged.

Review `additional-defect.json` and `additional-correct.json` separately, each copied as `subject.json` in a fresh context. JSON targets are complete supplied operational/configuration snapshots: declared handlers, asset/consumer inventory and effective rules are inputs, not newly executed observations. Each scenario states its own contract. Exclude this oracle and all sibling variants.

- **EX039, EX040, EX041, EX042, EX130, RC027**. Defect: Cause/correlation loss, early completion accounting, no flush and permanent suppression break required signals; configuration does not prove reception. Countercase: Cause/correlation, separate metrics, flush and active equivalent route satisfy source contract. Reception is honestly unexercised.
