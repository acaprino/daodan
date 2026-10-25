# Reintegrate the complete existing engine into Daodan

The sole source and distribution owner is `work-controller@daodan`. The source
engine formerly stored in `D:/Projects/deadly-brain` is transferred here; Daodan,
Shinatama and other consumers need no separate engine repository or installed
`process-controller` package. The controller remains independent of consumer
plugins. Repository ownership does not introduce a dependency cycle.

## Requirement and authorization

The attached conversation supplies the objective: the engine belongs entirely
in Daodan, followed by retirement of the separate repository. Its assistant's
five-step plan is context, not an approved specification. The current request
to resume authorizes continuation; the subsequent `rfesume, skip tests`
authorizes implementation while explicitly skipping further tests. This document
records the implementation choices; it does not promote an ADR or authorize
commits, push or permanent deletion.

The earlier external-owner direction in ADR-0002 and specification section 13
is superseded as an ownership target. ADR-0002 retains Proposed status until
its exact text is approved. Keep its historical rationale and the distinction
between ownership, implemented behavior and future capabilities.

## Approaches and chosen boundary

One source transfer into the existing work-controller plugin meets the objective
with the fewest owners. A separate repository conflicts with the stated intent.
A second engine plugin or a copied standalone Python project inside the
repository would preserve competing entry points, packaging and ownership.
Replacing the JSON work protocol with the imported SQLite store would lose
existing candidate gates and run history. The chosen implementation instead
gives graph scheduling and attempts to the engine and keeps domain admission
with the established work record.

The coordinator chooses to retain `model-routing` as its existing independent
Daodan provider. No external routing package or second router is introduced.
The public Python package is `work_controller`; source modules, console assets
and the original MIT notice live under the declared work-record skill so every
host package contains them. A small PEP 723 launcher declares the existing YAML
runtime dependency. The compiler remains standard-library only.

## Runtime and compatibility

All 15 existing Python modules, three console assets, CLI operations, graph
validation, SQLite journal, content-addressed artifacts, supervision advice,
decision tickets, console and stdio MCP move together. Preserve the 103 original
behavioral tests with namespaced imports and a bundled-runtime bootstrap.

New YAML uses `work-controller/process/v1`; both old schema identifiers remain
accepted with their original normalized values and source bytes. Stored hashes
and immutable definitions are never rewritten by a rename. Existing token
headers, storage keys and MCP `process_*` tool identities remain compatible.
Preserve copyright and inspiration provenance.

The engine uses the main checkout's dedicated `.daodan/processes` home, resolved
by the existing work-record helper. JSON runs and their agenda retain their
current paths. Old `.process-controller` and `.deadly-brain` directories require
explicit `--home` selection rather than silent competition, adoption or merging.
Existing process.db/brain.db compatibility remains for an explicit old home.
Validation creates no store. Console/MCP bootstrap may initialize an empty
dedicated store; their tools expose only read models.

## Record integration

New execution consumers set `process_required: true`. Before dispatch they
admit the approved YAML and bind its process ID, definition digest and native
worker-output mapping through `run_state.py bind-process`. The binding cannot
be replaced. Every graph agent maps to a declared native work delivery. Other
domain reviews remain separately accounted for in the existing ledger.

The bridge reuses the store's readers through a read-only SQLite connection.
It checks the workspace, immutable definition, job/output declarations,
successful producer, admitted artifact, stored content digest and native report
bytes. Process success becomes an additional completion condition. Questions,
candidate snapshots, independent reviews, gates and grants retain their existing
authority. A graph result never supplies a missing domain review or user answer.

Native reports in linked worktrees still belong to the main checkout's record
home; the coordinator retains identical admitted bytes there before marking the
work delivery delivered. Bound process graphs omit engine commit jobs; domain
commits remain in the reviewed wave method. Generic explicit CLI Git support
is retained for separately authorized processes. Old unbound JSON records do
not acquire fabricated graph history.

## Distribution and evidence

Declare the read-only MCP launcher in plugin.toml with the mcp.servers capability
and isolated uv invocation. Regenerate all five host exports, catalogs, plugin
references and canonical instruction adaptations. Preserve the preexisting
codebase-map changes; a combined rebuild does not authorize staging another
session's work. Keep compiler checks separate from installed-host evidence.

Acceptance examples:

1. A new bound analysis delivers identical report bytes to the engine and native
   ledger; its graph and existing domain checks must both finish before closure.
2. An old unbound JSON record resumes without rewriting its schema or history;
   a changed graph requires a new record and explicit bindings.
3. Missing artifacts, a different workspace/digest, a replaced binding or a
   required process missing at dispatch/completion are rejected. Engine success
   cannot hide an open question or stale candidate gate.

These are acceptance requirements, not claims of executed tests. At the user's
request, tests and runtime smoke checks on the migrated candidate are skipped.
The original source suite passed 103 tests before that instruction; those
results verify only the earlier source. Build, syntax, packaging, parity and
independent source review provide their own narrower evidence.

Real host dispatch adapters, observed model identity, parallel execution,
dynamic loops, selective replan and semantic memory were absent from the source
slice. Reintegration transfers the complete existing engine without claiming
those future requirements are implemented. No token-saving percentage is claimed.

## Retirement boundary

Retirement is a separate destructive action after the migration is reviewable.
Identify the exact remote and local path, preserve needed history/runtime data,
and obtain explicit confirmation before deletion. The original folder remains
untouched during implementation. Missing Git metadata or an unverified remote
is a concrete unresolved retirement prerequisite.

## YAML runtime dependency

The source already uses PyYAML through a restricted SafeLoader with duplicate-key,
tag and resource checks. Python has no standard-library YAML parser; retaining
that existing dependency avoids a second parser and preserves semantics. The
[maintainer's package metadata](https://pypi.org/project/PyYAML/) identifies 6.0.3,
MIT licensing, Python compatibility and release files; the
[canonical repository](https://github.com/yaml/pyyaml) supplies maintenance and
security-policy links. The launcher retains >=6.0.3,<7. Compiler use remains
dependency-free. No independent advisory-database audit or new installation was
performed in this run; retaining SafeLoader and resource bounds is mandatory.
