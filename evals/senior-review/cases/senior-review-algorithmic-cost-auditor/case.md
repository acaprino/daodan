# algorithmic-cost-auditor qualification case

Status: authored; no reviewer behavior has been scored.

## Coverage and target

- Reviewer: `senior-review:algorithmic-cost-auditor`. Content basis; review one variant in a fresh context.
- Focused T0 probes: `EX035`, `EX064`, `EX069`. Other assigned controls remain to qualify.
- Target and conclusion paths: supplied `subject.py`, copied from exactly one variant below. Admitted read scope is that target; its requirement and inventory are complete for this fixture.
- Setup: copy `defect.py` or `correct.py` to an isolated disposable directory as `subject.py`. Supply the canonical role, common conventions, report path and content basis. Never supply this case, sibling variant, prior findings or scorecard to the reviewer.
- Checks: source/configuration inspection only. No network, application execution, database, deployment, installation or removal. Report source derivations separately from runtime evidence.

## Defect oracle (scorer only)

Two disjoint lists of length 10000 cause 100 million equality comparisons in list membership.

A found result must establish the reachable trigger, violated requirement and consequence from the target. Naming the pattern without its causal path is partial.

## Correct countercase and must_not_report

Set preparation and lookups use the declared integer domain; do not assert measured milliseconds or demand an unrelated optimization.

Expect a complete no-findings result for this bounded mechanism; unrelated speculative recommendations are false positives.

## Other outcomes

Record completed applicable checks, source-only coverage and unexercised runtime. Missing required fixture or common/binding is a failed assignment with an explicit gap; do not infer a product defect. Persist the native reviewer-result with numeric confidence and `knowledge_usage: []` when no knowledge was assigned. Missing report/empty answer is not delivery. Scoring, candidate/source hashes, actual model/effort, measured cost where available and gaps belong to the run scorecard. This case does not certify every T0 control or any installed host.

## Additional independent scenarios (scorer only)

Review `additional-defect.py` and `additional-correct.py` separately, each copied as `subject.py` in a fresh context. JSON targets are complete supplied operational/configuration snapshots: declared handlers, asset/consumer inventory and effective rules are inputs, not newly executed observations. Each scenario states its own contract. Exclude this oracle and all sibling variants.

- **EX065, EX124**. Defect: Buffer list plus joined output doubles 100 MiB; deep supported chain exceeds stated stack limit. Countercase: Streaming preserves bounded peak; iterative traversal handles supported depth.
- **EX066, EX127, EX133**. Defect: Synchronous fetch blocks loop beyond declared bound and disabled logs still serialize/allocate per item. Countercase: Off-loop callback and disabled-level guard avoid the specified work; no inferred user milliseconds or GC pause claims.
- **EX068, EX126**. Defect: Summed free memory selects impossible contiguous allocation; per-item parsing amplifies non-React frame work beyond one-parse contract. Countercase: Largest-block check chooses streaming, and frame-local shared parse preserves unchanged model semantics.
