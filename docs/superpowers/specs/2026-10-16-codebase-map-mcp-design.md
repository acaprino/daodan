# Codebase Map MCP

## Approved intent

Expose Codebase Map as a reusable local service for native Tri-Tech Code
integration. The user approved a shared deterministic core, native application
orchestration and UI, and an MCP interface for agents, then requested the Daodan
implementation. Tri-Tech application changes are outside this change.

## Ownership and implementation

Keep parsing, verified source reading, delivery gates and publication in their
existing owners. Add a standard-library service under `map-method/scripts/` and
a thin stdio transport using the official MCP Python SDK 2.x, already used by
peer-review. The server binds once to `--project` (default startup directory).
Client arguments identify relative targets and exact run IDs, never arbitrary
output paths, executable commands or client-supplied manifests.

The native application may import the same service or call MCP. It owns worker
dispatch, models, authorization decisions, interruption and continuation.
The server starts no model, autonomous workflow, network listener or scheduler.
Existing shell workflows remain usable.

## Initial interface

- Scope and create a prepared classic run, with canonical mode flags and an
  optional stop-after control. Reuse snapshot creation and delivery preparation.
- Read run status, declared artifacts, verified source blocks, outlines and
  graph packets. Compare a run snapshot with current source without mutating it.
- Resume the exact unchanged run through the existing freshness and delivery
  controls; register, unregister and publish through existing helpers.
- Accept explicit phase-started, phase-completed and blocked checkpoints from
  the host. A completed checkpoint requires that phase's real declared outputs.
  Only canonical publication can complete and publish a full run.
- Retrieve a persisted, ordered per-run event journal with a cursor and limit.
  MCP calls emit request-scoped progress where supported. Event history records
  operations through this service; direct CLI or worker writes remain observable
  through status, without a promise that they emitted an event.

## Data and boundaries

Canonical state and evidence remain in `.codebase-map/runs/<run-id>/`. Events are
derived history inside that run, never another source of completion truth.
Validate traversal, symlinks and Windows junctions before reads and writes.
Validate state and manifest bindings against the configured project, including
existing runs. Refuse overwriting another run, malformed flags and incomplete
publication. Preserve the project-bound legacy migration contract.

Run mutations and event sequence assignment serialize across service processes.
Emit events after successful persisted changes. Status remains authoritative
after a crash or an event-write failure. Source emission is not proof of model
comprehension; inventory, deep-reading and supplied runtime evidence stay separate.

## Distribution and acceptance

Declare the server in the kernel, ship every local import under the skill, and
use existing compiler mechanisms for all five hosts. Keep SDK dependencies out of
the build and standard-library unit suite. Document command, tools, events,
host responsibilities and the native consumer boundary.

Acceptance requires service tests for real snapshots, source identity, lifecycle,
event replay and path confinement; a real SDK stdio handshake, tool listing,
successful/failed tool calls and progress notifications; all five rendered host
contracts and unsupported capability rejection; existing repository checks,
documentation/instruction parity and version bumps. A local wire exercise does
not assert installed-host or Tri-Tech runtime verification.
