# application-reachability-auditor qualification case

Status: authored; no reviewer behavior has been scored.

## Coverage and target

- Reviewer: `senior-review:application-reachability-auditor`. Content basis; review one variant in a fresh context.
- Focused T0 probes: `CL01`, `CL02`, `CL08`, `PR271`. Other assigned controls remain to qualify.
- Target and conclusion paths: supplied `subject.py`, copied from exactly one variant below. Admitted read scope is that target; its requirement and inventory are complete for this fixture.
- Setup: copy `defect.py` or `correct.py` to an isolated disposable directory as `subject.py`. Supply the canonical role, common conventions, report path and content basis. Never supply this case, sibling variant, prior findings or scorecard to the reviewer.
- Checks: source/configuration inspection only. No network, application execution, database, deployment, installation or removal. Report source derivations separately from runtime evidence.

## Defect oracle (scorer only)

obsolete has no reachable entry or consumer within the declared closed private application; identify that bounded removal candidate.

A found result must establish the reachable trigger, violated requirement and consequence from the target. Naming the pattern without its causal path is partial.

## Correct countercase and must_not_report

live is reached through dynamic lookup despite no syntactic call; do not flag it or remove anything during review.

Expect a complete no-findings result for this bounded mechanism; unrelated speculative recommendations are false positives.

## Other outcomes

Record completed applicable checks, source-only coverage and unexercised runtime. Missing required fixture or common/binding is a failed assignment with an explicit gap; do not infer a product defect. Persist the native reviewer-result with numeric confidence and `knowledge_usage: []` when no knowledge was assigned. Missing report/empty answer is not delivery. Scoring, candidate/source hashes, actual model/effort, measured cost where available and gaps belong to the run scorecard. This case does not certify every T0 control or any installed host.

## Additional independent scenarios (scorer only)

Review `additional-defect.py` and `additional-correct.py` separately, each copied as `subject.py` in a fresh context. JSON targets are complete supplied operational/configuration snapshots: declared handlers, asset/consumer inventory and effective rules are inputs, not newly executed observations. Each scenario states its own contract. Exclude this oracle and all sibling variants.

- **CL01, CL02, CL08, PR267, PR268, PR270, PR271, PR273, PR244, PR266**. Defect: Only retired_migration is unreachable under complete framework/public-entry contract. Require scope-aware consumer analysis. Countercase: Decorator registry, string route and exported public_entry are legitimate uses despite missing direct call sites; side effects are preserved. Other framework-specific variants remain unexecuted.

## Additional bindings scenarios (scorer only)

Copy exactly one of `bindings-defect.json` / `bindings-correct.json` as neutral `subject.json`; the same source-only review and isolation rules apply.

- **CL03, RC022, PR269, PR272**. Defect: Only unused.svg has no asset consumer; permanently disabled old_only is unreachable. Empty scanner result is incomplete because owned src is excluded. Countercase: CSS and glob assets plus pytest convention fixture remain used; approved generated/environment exclusions do not hide owned source. No false dead-code from absence of explicit function calls.
