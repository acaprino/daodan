# local-correctness-auditor qualification case

Status: authored; no reviewer behavior has been scored.

## Coverage and target

- Reviewer: `senior-review:local-correctness-auditor`. Content basis; review one variant in a fresh context.
- Focused T0 probes: `EX025`, `EX026`, `EX129`. Other assigned controls remain to qualify.
- Target and conclusion paths: supplied `subject.py`, copied from exactly one variant below. Admitted read scope is that target; its requirement and inventory are complete for this fixture.
- Setup: copy `defect.py` or `correct.py` to an isolated disposable directory as `subject.py`. Supply the canonical role, common conventions, report path and content basis. Never supply this case, sibling variant, prior findings or scorecard to the reviewer.
- Checks: source/configuration inspection only. No network, application execution, database, deployment, installation or removal. Report source derivations separately from runtime evidence.

## Defect oracle (scorer only)

Partial write result is ignored; full count is reported despite lost suffix.

A found result must establish the reachable trigger, violated requirement and consequence from the target. Naming the pattern without its causal path is partial.

## Correct countercase and must_not_report

Loop respects accepted prefix and fails on no progress; empty input returns zero validly.

Expect a complete no-findings result for this bounded mechanism; unrelated speculative recommendations are false positives.

## Other outcomes

Record completed applicable checks, source-only coverage and unexercised runtime. Missing required fixture or common/binding is a failed assignment with an explicit gap; do not infer a product defect. Persist the native reviewer-result with numeric confidence and `knowledge_usage: []` when no knowledge was assigned. Missing report/empty answer is not delivery. Scoring, candidate/source hashes, actual model/effort, measured cost where available and gaps belong to the run scorecard. This case does not certify every T0 control or any installed host.

## Additional independent scenarios (scorer only)

Review `additional-defect.mjs` and `additional-correct.mjs` separately, each copied as `subject.mjs` in a fresh context. JSON targets are complete supplied operational/configuration snapshots: declared handlers, asset/consumer inventory and effective rules are inputs, not newly executed observations. Each scenario states its own contract. Exclude this oracle and all sibling variants.

- **EX024, EX025, EX028, EX143, EX144, EX145, EX146, EX147, EX148, EX149, EX151, EX152, EX153, EX156, EX157, EX159, RC003, RC017, EX141, RC002, RC035, RC038, RC039, RC040, EX034, EX155**. Defect: Retain independent incorrect predicate, concatenation, units/narrowing, absent address, fencepost, skipped validation, uninitialized/shadowed state, late closure, shared default, reference equality, missing completion await/double callback, iterator skip, stale config cache and missing required builder name with concrete inputs. Countercase: Every corresponding valid implementation satisfies its stated local contract; callbacks may be used without mandatory promises style, native empty values remain valid.
- **RC019, EX027, EX030, EX031, EX128, EX131, EX150, EX154**. Defect: Deletion before failed write loses previous output; construction snapshot hides later shared setting; broad catch suppresses unexpected errors; abort kills serving process for supported invalid input; floating equality misses cents; boolean-before-bitmask computes wrong predicate; missing terminal returns no required rejection. Countercase: Atomic replace, shared current owner, scoped catch, error result, integer units, proper mask grouping and explicit rejection preserve independent contracts.

## Additional language scenarios (scorer only)

Copy exactly one of `language-defect.java` / `language-correct.java` as neutral `subject.java`; the same source-only review and isolation rules apply.

- **RC001, EX123, EX158, EX160, EX161, EX162**. Defect: Overload fails polymorphic fee contract; equal keys lack matching hash; oversized copy fails supported shorter target; integer wrap bypasses range bound; unchecked cast rejects supported integer; raw alias pollutes typed list; covariant String[] rejects allowed integer store. Countercase: Correct override/hash, actual bounds, nonoverflow range check, accepted-value conversion, typed writes and actual Object[] copy satisfy the independent contracts. Source review cannot claim Java execution.
