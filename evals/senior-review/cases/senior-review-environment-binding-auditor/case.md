# environment-binding-auditor qualification case

Status: authored; no reviewer behavior has been scored.

## Coverage and target

- Reviewer: `senior-review:environment-binding-auditor`. Content basis; review one variant in a fresh context.
- Focused T0 probes: `EX050`, `RC008`, `RC023`. Other assigned controls remain to qualify.
- Target and conclusion paths: supplied `subject.py`, copied from exactly one variant below. Admitted read scope is that target; its requirement and inventory are complete for this fixture.
- Setup: copy `defect.py` or `correct.py` to an isolated disposable directory as `subject.py`. Supply the canonical role, common conventions, report path and content basis. Never supply this case, sibling variant, prior findings or scorecard to the reviewer.
- Checks: source/configuration inspection only. No network, application execution, database, deployment, installation or removal. Report source derivations separately from runtime evidence.

## Defect oracle (scorer only)

The supplied staging environment resolves production data, violating environment isolation.

A found result must establish the reachable trigger, violated requirement and consequence from the target. Naming the pattern without its causal path is partial.

## Correct countercase and must_not_report

Distinct intended endpoints bind correctly; no requirement for identical configs or a new staging topology.

Expect a complete no-findings result for this bounded mechanism; unrelated speculative recommendations are false positives.

## Other outcomes

Record completed applicable checks, source-only coverage and unexercised runtime. Missing required fixture or common/binding is a failed assignment with an explicit gap; do not infer a product defect. Persist the native reviewer-result with numeric confidence and `knowledge_usage: []` when no knowledge was assigned. Missing report/empty answer is not delivery. Scoring, candidate/source hashes, actual model/effort, measured cost where available and gaps belong to the run scorecard. This case does not certify every T0 control or any installed host.

## Qualification correction

The original defective timezone packet specified host-local interpretation without
an effective host timezone. Host-local can be UTC, so that packet could not prove
the declared violation. The corrected defect supplies effective UTC+02:00 with no
override. The original failed report and bytes remain preserved; only a fresh
bound trial may qualify the timezone mechanism. Correct UTC counterpart unchanged.

## Additional independent scenarios (scorer only)

Review `additional-defect.json` and `additional-correct.json` separately, each copied as `subject.json` in a fresh context. JSON targets are complete supplied operational/configuration snapshots: declared handlers, asset/consumer inventory and effective rules are inputs, not newly executed observations. Each scenario states its own contract. Exclude this oracle and all sibling variants.

- **RC008, RC010, RC021, RC023, RC042, EX050**. Defect: Misspelled placeholder remains literal, stage secret/routing select production and locale/timezone violate contract. Countercase: Validated resolution, stage binding, and explicit locale/UTC satisfy contract; intended production differences remain valid.
