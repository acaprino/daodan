# authorization-auditor qualification pack

Authored fixtures; no behavioral outcome asserted.

- Reviewer: `senior-review:authorization-auditor`; content basis.
- Authored control family: SD002-005, SD009, SD024. Scenario mappings below identify independently observable mechanisms, not an assertion that each protocol permutation ran.
- Target: supply only one variant copied to neutral `target.py` in a fresh isolated directory. Its source and requirement docstring form admitted read/conclusion scope. Supply no case/oracle, counterpart or prior report.
- Effective dependency guarantees are explicit in the target. The coordinator binds target hash and scope in the brief; for logic-integrity these requirements/call paths are the scoped semantic context linked to that hash.
- Checks: source inspection required. Runtime is not required for these causal source fixtures. Execute only explicitly authorized safe pure/in-memory scenes; never invoke interpreter adapters, live network, production data or unknown callbacks.

## primary (scorer only)

Controls: SD002-003, SD024.

Defect: export({"tenant":"north"}, [8]) exposes the south row because the batch route bypasses invoice authorization. Qualifying finding identifies the caller ID, alternate route and cross-tenant read.

Correct / must_not_report: Do not demand RLS or duplicate guards inside export: the effective invoice guard covers every batch item. Authorized ID 7 remains readable.

## privileged_fields (scorer only)

Controls: SD003, SD009.

Requirement: Self-service profile updates may change display only. Stored role and tenant are server controlled.

Defect: update_profile(row,{"role":"admin"}) promotes caller-controlled authority.

Correct / must_not_report: Changing display is allowed; rejecting privileged fields centrally is sufficient.

## pooled_rls (scorer only)

Controls: SD004-005.

Requirement: Connection tenant is the effective RLS scope for rows. A pooled connection may carry the prior caller tenant; checkout must bind the new authenticated tenant before query.

Defect: A south caller checks out a connection retaining north and reads north rows. RLS exists but uses stale authority.

Correct / must_not_report: Binding server-established tenant before query closes this sequential connection-reuse path; no client-supplied identity is used.

## Delivery and limits

Use the existing envelope and explicit inspected boundaries, applicable completed checks and gaps. A correct pack has no product findings when supplied assumptions hold. Missing required policy/source/assigned knowledge produces failed coverage with precise gaps and preserved partial findings. Missing dispatch/delivery and stale knowledge are shared protocol probes, never product defects.

Static source traces are derived evidence, not runtime reproduction. Cases, structural validity and successful rendering do not establish behavioral qualification. Save fresh outputs, independent scores, model/effort, candidate/body/reference hashes and observable cost in the run. Unobserved token cost remains unknown.

## Direct public action (PR098)

Materialize `server-action-defect.py` / `server-action-correct.py` as `server-action.py` with the same variant. The effective host contract in the source makes PUBLIC_ACTIONS directly callable independently of PAGE_LOADERS. Defect: a request without a trusted session invokes delete_invoice through dispatch_action and deletes tenant north's row, even though the page loader rejects the same request. A signed-in south principal can use that path too. Cite the public registry/dispatcher, absent action guard and mutation; the page guard is counterevidence only for page loading.

Correct / must_not_report: the action obtains the server-established session and checks the row tenant before mutation. Anonymous and wrong-tenant action calls are denied; the page remains independently guarded. No particular route middleware, schema format or duplicate guard inside the server-owned store is mandatory. These are supplied host semantics, not live Next.js or server execution.

## Client authority at the mutation boundary (PR175)

Materialize `client-authority-defect.py` / `client-authority-correct.py` as `client-authority.py`. Defect: after a trusted session authenticates a north caller, its caller-controlled tenant and can_export fields select and release south rows. The client UI hiding Export cannot constrain a direct request. Cite the client-controlled fields, authoritative tenant policy and returned rows.

Correct / must_not_report: the server policy independently grants export and selects the trusted principal tenant, so forged client booleans/tenant names are inert. Client fields may remain in the request for display without authority. This authorization fixture intentionally does not test independent price/domain rules; do not mark all PR175 logic-integrity mechanisms qualified from it.
