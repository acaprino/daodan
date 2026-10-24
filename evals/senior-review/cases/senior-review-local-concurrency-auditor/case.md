# local-concurrency-auditor qualification case

Status: authored; no reviewer behavior has been scored.

## Coverage and target

- Reviewer: `senior-review:local-concurrency-auditor`. Content basis; review one variant in a fresh context.
- Focused T0 probes: `EX029`, `EX137`, `EX139`, `RC031`. Other assigned controls remain to qualify.
- Target and conclusion paths: supplied `subject.py`, copied from exactly one variant below. Admitted read scope is that target; its requirement and inventory are complete for this fixture.
- Setup: copy `defect.py` or `correct.py` to an isolated disposable directory as `subject.py`. Supply the canonical role, common conventions, report path and content basis. Never supply this case, sibling variant, prior findings or scorecard to the reviewer.
- Checks: source/configuration inspection only. No network, application execution, database, deployment, installation or removal. Report source derivations separately from runtime evidence.

## Defect oracle (scorer only)

Both tasks read one seat before suspension and both return true; read/check/write contract is not atomic.

A found result must establish the reachable trigger, violated requirement and consequence from the target. Naming the pattern without its causal path is partial.

## Correct countercase and must_not_report

One shared lock encloses check and decrement. Do not invent parallelism within a suspension-free asyncio section or require per-call locks.

Expect a complete no-findings result for this bounded mechanism; unrelated speculative recommendations are false positives.

## Other outcomes

Record completed applicable checks, source-only coverage and unexercised runtime. Missing required fixture or common/binding is a failed assignment with an explicit gap; do not infer a product defect. Persist the native reviewer-result with numeric confidence and `knowledge_usage: []` when no knowledge was assigned. Missing report/empty answer is not delivery. Scoring, candidate/source hashes, actual model/effort, measured cost where available and gaps belong to the run scorecard. This case does not certify every T0 control or any installed host.

## Additional independent scenarios (scorer only)

Review `additional-defect.json` and `additional-correct.json` separately, each copied as `subject.json` in a fresh context. JSON targets are complete supplied operational/configuration snapshots: declared handlers, asset/consumer inventory and effective rules are inputs, not newly executed observations. Each scenario states its own contract. Exclude this oracle and all sibling variants.

- **EX134, EX135, EX136, EX138, EX139, EX140, RC015, RC018, RC031, RC032, RC033**. Defect: Independent lock-cycle, distinct-lock shared mutation, relaxed publication, path replacement, starvation/livelock and shared strategy interleavings violate stated local contracts. Countercase: Global order, common owner lock, release/acquire, bound descriptor, fairness and per-call state prevent the corresponding paths; no preferred synchronization primitive is mandatory.

## Strategy contract correction and separate probes

Original b7dc41dfeab1 LC-7 is a false positive: its target supplies an overwrite/read ordering but no per-call isolation requirement, so intentionally current global configuration is a valid interpretation. Root independently confirmed that judgment. Original bytes, report and score are preserved. The intended positive strategy case now explicitly binds per-invocation discount ownership for A=0.5/B=0; new primary trials must use new snapshots.

Two separate probes have independent packets and expected behavior fixed before dispatch. probe-missing-strategy-contract.json omits exactly the discount ownership requirement: expect an explicit required-contract gap and failed assignment, no invented product defect. probe-global-setting.json explicitly requires current shared global value and supplies atomic sequential consistency: A reading B's completed value0 is correct; expect findings:[] and completed applicable checks. A singleton, mutable value or interleaving alone must not imply per-call isolation. Runtime remains none. These probes do not replace the primary defect/correct pair.

## Unmarked missing-contract probe in the original mixed packet

probe-mixed-original/ is byte-identical to original b7dc41dfeab1/target, including its seven supported defects and strategy ordering without a per-call ownership requirement. A fresh reviewer must identify the seven supported mechanisms and mark the strategy ownership check as blocked by unavailable contract, with failed assignment and no LC-7 product defect. Omitting the strategy check silently also fails truthful coverage. This preserves the originally observed false-positive trigger alongside all neighboring defects; it is separate from the deliberately isolated null-contract probe and explicit global-setting countercase. No answer or probe label is supplied in the reviewer brief/binding.
