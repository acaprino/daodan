<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Claude binding: repository read, file discovery and content search use Read, Glob
and Grep; repository write and repository edit use Write and Edit; shell execution
uses Bash; network fetch uses WebFetch and network search uses WebSearch; a user
question uses AskUserQuestion. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

# Logic Integrity Defects

Reference for the `logic-integrity-auditor` review dimension. Derive contracts, invariants and assumptions from an interconnect map or prepared scoped semantic context, bound to the candidate with provenance. Missing or stale evidence requires re-derivation or a failed-coverage gap. Section names below are semantic anchors, not a mandatory file layout. The common evidence rules govern these pattern leads and suggested fixes.

Scope: violations of contracts, invariants, domain rules, ordering, idempotency, and state machines. Distinct from pure concurrency (see `concurrency-state.md`), pure security (see `security.md`), and pure distributed-integration (see `distributed-integration.md`); overlap exists at boundaries.

---

## Category L1: Contract Violations

### L1.1 Unenforced Precondition
- **CWE**: 573 (Improper Following of Specification)
- **Pattern**: Function assumes input has property P (non-empty, validated, normalized, authenticated) but does not assert or verify P. Any caller path that bypasses the enforcing entry point corrupts state.
- **Detection**: Cross-reference contract/precondition anchors in the supplied map or scoped context; trace every relevant caller and verify its guarantee.
- **Fix**: Add boundary validation (assert, type guard, defensive check). Prefer making the precondition impossible to violate via the type system.
- **Difficulty**: Medium
- **Signature**: Docstring or comment says "expects X to be Y" but no runtime check; function body crashes/misbehaves when Y is false.

### L1.2 Unkept Postcondition
- **CWE**: 710 (Improper Adherence to Coding Standards)
- **Pattern**: Function's declared or assumed postcondition (e.g., "returns non-null", "DB row is committed", "cache is populated") is not guaranteed on all paths. Early returns, exception paths, or partial branches skip the postcondition.
- **Detection**: For each `## Contracts` row claiming a postcondition, trace all return paths and exception paths; verify postcondition holds on each.
- **Fix**: Use `try/finally`, refactor to single exit, or encode the postcondition in the return type (Option/Result).
- **Difficulty**: Medium
- **Signature**: Function has 3+ exit points and the "success artifact" (committed tx, set field, sent message) is only produced on the primary happy-path exit.

### L1.3 Exception Contract Mismatch
- **CWE**: 755 (Improper Handling of Exceptional Conditions)
- **Pattern**: Callers catch specific exception types but the callee raises a broader or different type (or leaks an unexpected wrapped exception). Or: callee silently catches an exception the caller would have handled correctly.
- **Detection**: For each `## Call Graph` callee, grep both ends: what does the caller `catch`/`except`? What can the callee raise (including via its own callees)?
- **Fix**: Re-raise with documented types, or wrap/translate to the caller's contract, or update caller to handle the broader type.
- **Difficulty**: Medium
- **Signature**: `try: caller_fn()` with specific `except ValueError`, but `caller_fn` internally calls a library that raises `RuntimeError`.

### L1.4 Silent Contract Widening
- **CWE**: 436 (Interpretation Conflict)
- **Pattern**: A public/exported function changes its contract (accepts broader input, returns nullable, changes side-effect order) without versioning. Callers relying on the old contract break silently.
- **Detection**: Compare current signature/behavior with call sites in `## Call Graph -> External callers`. Flag if callers appear to assume the older contract.
- **Fix**: Version the API, deprecate old contract, add runtime warning, or update all call sites atomically.
- **Difficulty**: Hard (cross-module)
- **Signature**: Recent edits to function signature or body; callers not updated in same changeset.

---

## Category L2: Invariant Violations

### L2.1 Class Invariant Break in Method
- **CWE**: 665 (Improper Initialization)
- **Pattern**: Constructor establishes invariant I. Some method mutates state in a way that breaks I (e.g., sets a field to None that `__init__` guarantees non-None, changes a list length that another method assumes stable).
- **Detection**: For each class in `## Invariants`, inspect all methods that mutate `self.*`; verify they preserve each declared invariant on every path.
- **Fix**: Make invariant-bearing fields immutable (`@property` without setter, frozen dataclass); use assertions in methods; move mutation through a single audited channel.
- **Difficulty**: Medium
- **Signature**: `@property` returns a value another method sets to None; `__init__` guarantees list non-empty, `pop()` method does not check.

### L2.2 Temporal Invariant Break
- **CWE**: 362 (related, but non-concurrent case)
- **Pattern**: An attribute documented as "set once, never modified" or "monotonically increasing" is modified or decremented somewhere. E.g., `created_at` overwritten, `version` decremented, a terminal state (`status='completed'`) mutated back.
- **Detection**: For each temporal invariant in `## Invariants`, Grep for every assignment site of that field; verify each is the initial one or a monotonic update.
- **Fix**: Freeze the field after initial set (property, database CHECK constraint, or application-level guard).
- **Difficulty**: Easy to Medium
- **Signature**: `self.created_at = ...` appears in a method that is not `__init__` or a migration path.

### L2.3 Cross-Component Invariant Drift
- **CWE**: 20 (broadly: improper input validation between components)
- **Pattern**: Invariant spans components: "if X exists in DB, Y exists in cache", "event published implies row committed", "file on disk corresponds to record in index". One side updated without the other.
- **Detection**: Cross-reference `## Invariants -> Cross-component` with `## Integration Hot-Spots`. For each hot-spot, verify both sides are updated atomically or with compensating logic.
- **Fix**: Atomic transaction spanning both sides; outbox pattern; reconciliation job; or redesign to single source of truth.
- **Difficulty**: Hard
- **Signature**: Code writes to DB, then publishes event; failure between the two commits leaves system with half-updated state and no recovery.

### L2.4 Loop Invariant Weakness
- **CWE**: 835 (Loop with Unreachable Exit Condition) / 129 (Improper Validation of Array Index)
- **Pattern**: Loop body mutates a variable the termination condition depends on, but the mutation can fail to decrease/increase the condition variable (stuck loop, or off-by-one).
- **Detection**: For each loop, identify the invariant implied by the condition and verify each iteration advances toward termination.
- **Fix**: Make the progress explicit (`i += 1` at top of body); add a max-iteration guard; convert to `for` with bounded range.
- **Difficulty**: Medium
- **Signature**: `while not done:` with `done` set inside the body through conditional logic.

---

## Category L3: Assumption Failures

### L3.1 Unverified Caller Guarantee
- **CWE**: 20 (Improper Input Validation)
- **Pattern**: Code assumes input has already been validated/sanitized by the caller ("this is internal, so input is trusted") but the assumption is not declared, and an unchecked path exists where the caller does not validate.
- **Detection**: For each `## Assumptions -> status: unverified`, trace all call sites; verify the guarantee holds on each path, including error/retry/alternate entry points.
- **Fix**: Add inner validation (defense-in-depth), or document + test the boundary, or move the logic behind a single entry point.
- **Difficulty**: Medium
- **Signature**: Comment `# assumes X is already validated` (or no comment at all) in a helper called from multiple entry points with inconsistent pre-validation.

### L3.2 Unchecked Initialization Precondition
- **CWE**: 908 (Use of Uninitialized Resource)
- **Pattern**: Function requires global state to be initialized (DB pool, logger, singleton, cache warmed) but does not check. First call before init fails or corrupts state.
- **Detection**: Cross-reference `## Assumptions` entries about initialization against `## Integration Hot-Spots -> Env/config` and startup sequences. Check that every caller path runs after init.
- **Fix**: Initialize lazily with idempotent setup, or assert initialization at function entry, or use a dependency-injection pattern.
- **Difficulty**: Medium
- **Signature**: Module-level `_pool = None; def use(): return _pool.acquire()` where `init_pool` is called elsewhere.

### L3.3 Tacit Config/Env Assumption
- **CWE**: 453 (Insecure Default Variable Initialization) / 1188 (Insecure Default Initialization of Resource)
- **Pattern**: Code reads `os.environ["X"]`, `config.get("y")`, or a flag without handling the missing/invalid case. Happy-path works only when the deployer knows to set it.
- **Detection**: For each `## Integration Hot-Spots -> Env/config`, verify missing-key handling. Also Grep `os.environ\[`, `getenv(`, similar patterns in the target.
- **Fix**: Explicit default with type coercion, or fail-loud at startup with a clear error, or schema-validated config loader.
- **Difficulty**: Easy
- **Signature**: `os.environ["API_KEY"]` without default; `int(os.environ["TIMEOUT"])` with no try/except.

### L3.4 Protocol Version Assumption
- **CWE**: 20 (Improper Input Validation) / 1039 (Automated Recognition Mechanism with Inadequate Detection)
- **Pattern**: Code assumes external API/message/schema is at a specific version but does not negotiate, check, or tolerate version drift.
- **Detection**: Review `## Integration Hot-Spots -> HTTP/queue/third-party` entries; check if version headers, schema IDs, or capability negotiation exist.
- **Fix**: Version-aware parsing, graceful unknown-field handling, schema registry, or capability probe at connect time.
- **Difficulty**: Medium-Hard
- **Signature**: `response.json()["price"]` directly, no check for missing field or type mismatch.

---

## Category L4: Domain Rule Violations

### L4.1 Bypass Path to Business Rule
- **CWE**: 284 (Improper Access Control) / 693 (Protection Mechanism Failure)
- **Pattern**: A business rule ("orders cannot be modified after payment", "withdrawals blocked for unverified accounts") is enforced in the primary entry point but a secondary path (admin API, webhook, batch job, import tool) bypasses it.
- **Detection**: For each rule in `## Domain Rules`, identify the enforcement site; Grep for every mutation of the relevant state; verify each mutation path applies the rule.
- **Fix**: Push enforcement down to the data layer (DB trigger, constraint, or repository method) so every path goes through it; or centralize mutations through a single domain service.
- **Difficulty**: Medium-Hard
- **Signature**: `UserRepository.update` (unchecked) exists alongside `UserService.update_profile` (checked); admin tool uses the repo directly.

### L4.2 Inconsistent Rule Enforcement
- **CWE**: 358 (Improperly Implemented Security Check for Standard)
- **Pattern**: Same rule enforced differently in different places -- e.g., validation in `POST /api/x` requires email lowercase, but `PATCH /api/x` does not; or form validation is stricter than API validation.
- **Detection**: Cluster rule-enforcing code by rule (`email_valid`, `max_len=140`, `must_be_active`); check all clusters have the same implementation.
- **Fix**: Extract the rule to a single function or validator and use everywhere; or enforce at the model layer so it cannot be bypassed.
- **Difficulty**: Medium
- **Signature**: `if len(title) > 140` in one handler, `if len(title) >= 140` in another.

### L4.3 Rule Encoded in Names but Not Logic
- **CWE**: 710 (Improper Adherence to Coding Standards)
- **Pattern**: A function named `is_active_user`, `can_withdraw`, `is_eligible` suggests a business rule but implements only part of it (or trivially returns True/a single field check).
- **Detection**: For each predicate function, compare name vs body; check if body reflects the full rule as described in docs or `## Domain Rules`.
- **Fix**: Rename to reflect actual behavior, or expand the check to match the name.
- **Difficulty**: Easy
- **Signature**: `def can_withdraw(user): return user.status == "active"` (ignores balance, limits, account flags).

---

## Category L5: Ordering and Sequence Violations

### L5.1 Required Call Order Not Enforced
- **CWE**: 666 (Operation on Resource in Wrong Phase of Lifetime)
- **Pattern**: Callee X must be invoked only after Y (`connect` before `send`, `open` before `read`, `authenticate` before `authorize`, `begin_tx` before mutations). Nothing in X's signature or runtime enforces this; a caller can and will eventually call X first.
- **Detection**: Cross-reference `## Contracts -> Implicit -> Ordering constraints`. For each, Grep call sites; verify each follows the order.
- **Fix**: Express the sequence as a state machine or typestate (methods only callable in certain phases), or embed the precondition in the called method (`assert self._connected`).
- **Difficulty**: Medium
- **Signature**: README says "always call setup() first"; `use()` method has no check.

### L5.2 Reentrancy Violation
- **CWE**: 663 (Use of a Non-reentrant Function in Concurrent Context) -- also applies non-concurrent
- **Pattern**: A function assumes it is not called recursively (from its own callee chain), or is not called while it holds mutable state. Recursion, event handlers, or callbacks violate.
- **Detection**: For each function with mutable instance/module state, trace its call graph for loops back to itself (including via observers/callbacks).
- **Fix**: Make the function pure (return new state instead of mutating), or add a reentrancy guard flag, or use a queue for deferred self-invocation.
- **Difficulty**: Hard
- **Signature**: `on_change` handler mutates state which triggers another `on_change`.

### L5.3 Cleanup-Before-Use
- **CWE**: 416 (Use After Free) / 672 (Operation on Resource after Expiration or Release)
- **Pattern**: Resource released/closed in one path, but another path uses it afterward (cached reference, callback captured the resource, sibling task still running).
- **Detection**: For each `Closeable`/`Disposable`/FD/connection, trace close site vs all usages; verify no path uses after close.
- **Fix**: Ownership semantics (only one closer), cancellation propagation, or resource tokens that become invalid after close.
- **Difficulty**: Medium-Hard
- **Signature**: `finally: session.close()` followed by a background task that holds `session` in a closure.

---

## Category L6: Idempotency Violations

### L6.1 Non-Idempotent Retry-Exposed Operation
- **CWE**: 840 (Business Logic Errors)
- **Pattern**: Operation is exposed to retries (HTTP client with retry, queue consumer with redelivery, workflow step with replay) but is not idempotent (second execution has different effect: double charge, duplicate row, double event).
- **Detection**: Cross-reference `## Integration Hot-Spots -> in` (queue consumers, HTTP endpoints mutating state) against `## Assumptions` about at-least-once semantics.
- **Fix**: Idempotency key (dedup by request ID / event ID), UPSERT instead of INSERT, stateful guard (if already done, skip).
- **Difficulty**: Medium-Hard
- **Signature**: `POST /charge` that creates a new Charge row on every call; `on_message` that increments a counter.

### L6.2 Double-Commit on Partial Failure
- **CWE**: 754 (Improper Check for Unusual or Exceptional Conditions)
- **Pattern**: Two side effects in sequence (DB commit + external API call + event publish). First succeeds, second fails, retry re-executes first -> duplicate. Outbox/saga missing.
- **Detection**: For each multi-effect handler, identify the ordering and the retry policy; verify recovery does not duplicate completed effects.
- **Fix**: Transactional outbox, two-phase commit where available, or idempotent downstream effects keyed on upstream ID.
- **Difficulty**: Hard
- **Signature**: `db.commit(); requests.post(...)` inside a retried handler.

---

## Category L7: State Machine Drift

### L7.1 Illegal Transition Allowed
- **CWE**: 841 (Improper Enforcement of Behavioral Workflow)
- **Pattern**: Domain object has implicit state machine (draft -> published -> archived) but transitions are not enforced. Code allows published -> draft, archived -> published.
- **Detection**: From `## Domain Rules` and field values (enums), draw the state graph; cross-check every setter/updater for disallowed transitions.
- **Fix**: Explicit state machine library, guard in setter (`raise if not allowed`), or database CHECK constraint.
- **Difficulty**: Medium
- **Signature**: `status` field with free assignment; no central transition method; multiple setters in different modules.

### L7.2 Terminal State Mutation
- **CWE**: 837 (Improper Enforcement of a Single, Unique Action)
- **Pattern**: A "final" state (refunded, archived, completed, cancelled) is still mutable through some path. Business rule says terminal but code does not enforce.
- **Detection**: Identify terminal states from `## Domain Rules`; Grep for assignments/mutations of entities in those states.
- **Fix**: Validate state at the mutation site (`raise if instance.status == 'completed'`) or move to event-sourcing.
- **Difficulty**: Medium
- **Signature**: `order.total = new_total` without a check that `order.status != 'paid'`.

---

## Category L8: Serialization Boundary Drift

### L8.1 Persisted Shape vs Code Shape
- **CWE**: 502 (Deserialization of Untrusted Data, broader interpretation)
- **Pattern**: DB column, cache payload, or serialized file assumes a shape (v1) but code has been updated to write/read v2 without migration. Old rows in DB fail to load, new rows fail with old readers.
- **Detection**: For each persisted artifact in `## Integration Hot-Spots -> DB/cache/FS`, compare current code's serialization vs sample stored values (if available) or migrations history.
- **Fix**: Schema version field with forward/backward compatible parsing; migrations to normalize; or feature-flagged rollout.
- **Difficulty**: Hard
- **Signature**: `pickle.loads(cached)` with no version check; `json.loads(row['payload'])['new_field']` without default.

### L8.2 Cache Key Encodes Stale Logic
- **CWE**: 567 (Unsynchronized Access to Shared Data, via cache)
- **Pattern**: Cache key derived from inputs in a way that does not reflect a new input dimension (e.g., key is `f"{user_id}:{page}"` but logic now also depends on `tenant_id`). Cross-tenant cache pollution.
- **Detection**: For each cache get/set in `## Integration Hot-Spots`, check that every input the computation depends on is encoded in the key.
- **Fix**: Include all inputs in the key (normalize, hash if long), or version-bump cache prefix when logic changes.
- **Difficulty**: Medium
- **Signature**: `@cache(key=lambda user_id: ...)` but function body reads `tenant_id` from context.

---

## Detection Strategy Summary

Use the supplied snapshot-bound interconnect map or scoped semantic context as a fallible index:

1. Confirm candidate, provenance and relevant contract/invariant/assumption anchors. Missing required context remains failed coverage.
2. Apply the matching category to its evidence; a sparse map does not make other categories inapplicable.
3. Trace source callers, mutators and persistence boundaries; seek counterexamples and independently derive omitted rules.
4. Cite the used context anchor and source location. Mark independently derived rules `[MAP-GAP]`; re-derive stale premises rather than treating them as current evidence.

## Severity Calibration

| Severity | Criterion |
|----------|-----------|
| CRITICAL | Data corruption, silent financial error, terminal state mutation on live data, cross-component invariant drift with no reconciliation |
| HIGH | Bypass path to business rule, non-idempotent retry-exposed operation, unenforced precondition leading to crash/wrong output |
| MEDIUM | Inconsistent rule enforcement, unchecked initialization precondition with fail-loud default, reentrancy guard missing but no known trigger yet |
| LOW | Predicate named after rule but partial implementation, missing default on env var with sensible fallback, loop invariant unclear but no observed bug |

## Anti-Patterns for the Reviewer

- Do NOT flag every `os.environ[]` as L3.3 -- only those without defaults AND on a critical path.
- Do NOT invent assumptions the code does not actually make.
- Do NOT escalate L4.3 (name mismatch) to CRITICAL; it is documentation debt at worst.
- Do NOT duplicate findings from `security-auditor` (CWE-20 injection) or `distributed-flow-auditor` (saga compensation) -- cross-reference instead.
