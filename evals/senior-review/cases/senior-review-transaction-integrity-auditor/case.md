# transaction-integrity-auditor qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:transaction-integrity-auditor`; content basis.
- Authored control family: SD065-078, SD093. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## primary (scorer only)

Controls: SD065-066, SD068, SD075.

Defect: Calling http_create then import_create with the same tenant/reference creates two rows; a serial alternate writer already proves the violated uniqueness requirement. A concurrent check/insert is another path, but need not be fabricated.

Correct / must_not_report: The effective NOT NULL composite uniqueness and conflict handling protect both routes. Same reference across different tenants is intentional, not a duplicate violation.

## atomic_unit (scorer only)

Controls: SD069-071.

Requirement: A transfer must debit and credit together. transaction() creates the scoped tx handle; all tx.write operations roll back together on exception. db.write uses a separate autocommit connection and commits immediately even while that transaction context is active. credit may reject after debit.

Defect: Debit uses the outer autocommit connection; later credit failure rolls back only credit and leaves a committed partial transfer.

Correct / must_not_report: Both writes use propagated transaction; rollback protects the invariant on failure.

Fixture clarification after native attempt3: the old phrase "db.write outside it commits immediately" did not establish whether db.write lexically inside the context could participate through ambient transaction state. Attempt3 correctly withheld that oracle claim. Original case/variant bytes and both target bindings are preserved; new attempt4 states the intended separate-connection contract explicitly. No behavior or production reviewer changed.

## write_skew (scorer only)

Controls: SD072, SD074-075.

Requirement: At least one on-call operator must remain. Unprotected transactions observe their own snapshots; two concurrent operators may request leave. lock_all acquires the predicate lock across all processes and establishes a fresh committed snapshot for the enclosed count and write before either executes; that lock serializes all on-call predicate updates.

Defect: Two snapshot transactions each count2 and turn distinct operators off, leaving0. Row-local independent writes do not protect the shared predicate.

Correct / must_not_report: Shared predicate lock serializes the count and write across processes. Do not demand SERIALIZABLE by name when the effective lock suffices.

## retry_decision (scorer only)

Controls: SD073.

Requirement: A serialization conflict aborts the transaction. The price must be re-read for each successful transaction attempt; transaction() supplies a new current view and raises Conflict when aborted.

Defect: Retry reuses price derived before the failed transaction despite a changed current price, violating required decision freshness.

Correct / must_not_report: Retry rederives the whole decision in its transaction; no retry of an already committed side effect is modeled.

## dedup_commit (scorer only)

Controls: SD076-078.

Requirement: The owner is serial; abrupt process failure is outside this scene. A successful debit and its receipt must be observable together on return. Debit may raise before mutation; a completed key binds amount and must reject a different amount on replay.

Defect: A debit failure leaves done marked completed, causing retry to skip required debit; repeated key with different amount also returns an unrelated receipt. This scenario is serial and debit failure precedes mutation.

Correct / must_not_report: Under the declared serial/pre-mutation-failure semantics, mutate then mark correctly preserves retry; amount comparison rejects changed intent. Do not invent a crash-after-debit guarantee not supplied here.

## orm_orphans (scorer only)

Controls: SD067, SD093.

Requirement: Children require a present parent and must be deleted with it. The effective mapping is application-enforced in a single atomic owner; all relevant writers use delete_parent.

Defect: Deleting parent leaves prohibited child rows; source declaration of a relationship alone provides no cascade.

Correct / must_not_report: The sole atomic owner removes children and parent; a DB-level cascade is not mandatory by name.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.

## Offline concurrent merge (PR172)

The existing materializer copies `offline-merge-defect.py` / `offline-merge-correct.py` to neutral `offline-merge.py`, alongside the same variant's other sources. Keep this oracle outside the target.

Defect: replicas A and B independently acknowledge one increment, producing snapshots {A:1,B:0} and {A:0,B:1}. Sequential arrival in either order followed by replay must retain total 2; dictionary replacement/update instead overwrites one replica component with stale zero, and a delayed replay can regress the result. Cite the required accepted updates, merge assignment and derived total. This is distinct from a database transaction/isolation scene.

Correct / must_not_report: per-replica maxima preserve both increments under all stated order/replay sequences, with validation and origin ownership explicitly guaranteed before merge. Convergence does not independently prove authorization; do not claim that it does. The separate label path intentionally uses the greatest logical rank, with concurrent lower-ranked labels superseded by approved LWW policy in both variants. Do not report that explicitly permitted label loss as the counter defect; the add-only counter has a different requirement. No CRDT library, global clock, remote transaction or live replication exercise is required or claimed.
