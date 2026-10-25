# Case: standalone-map-consumption

## Invariant

An ordinary project task can consume Codebase Map without the `daodan` entry
plugin or its workflows. Existing evidence guides localization, documentation
lookup and impact analysis; current source remains authoritative; a missing or
stale map causes explicit fallback, never an implicit analysis or refresh.

## Setup

Materialize a small Python project with an API module, a normalization module,
tests and a short design document. Install only `codebase-map` and its mandatory
dependency closure; the `daodan` plugin must be absent. Register the MCP server
when the host does not do so automatically.

In a setup session, create and publish a full map. Record the host, model,
plugin version, setup cost and exact run. Start each tested request in a fresh
session with no command or workflow invocation and no access to this case.

Exercise every variant twice: once with MCP connected and once with no MCP
connection, using only ordinary file and search tools. This gives six tested
sessions in addition to setup.

Run three variants:

1. **Present:** ask where to change name normalization before API responses,
   which project documents are relevant, and what the change could affect.
   Request analysis only, with no edits.
2. **Stale:** modify the normalization function after the published run, then
   ask the same question.
3. **Absent:** remove the scratch project's `.codebase-map/` directory, then
   ask the same question.

## Composed-consumer extension

Restore the project and map, then install `daodan` with its required providers.
Use `/daodan:review-branch` on the normalization branch in three more fresh
sessions: present, stale and absent evidence. Request the team review and record
the computed roster; Codebase Map preparation and its composed consumer must be
selected, otherwise the fixture is invalid. Bind the exact prepared run where
the method requires one. The read-only review must use the same navigation,
verify premises against current source, preserve its own review gates and never
create, update, deepen, migrate or publish map evidence implicitly.

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | In the present variant, the agent discovers and consults existing map evidence without any Daodan command or workflow. |
| 2 | MUST | The response identifies the implementation and relevant documentation from evidence, and describes affected callers or consumers as static leads rather than proven runtime effects. |
| 3 | MUST | Material claims about current behavior are checked against current source; map text alone is not treated as authoritative. |
| 4 | MUST | In the stale variant, the agent checks drift or current source and discloses the affected evidence gap instead of presenting the old analysis as current. |
| 5 | MUST | In the absent variant, the agent states that no usable map is available and continues with ordinary repository exploration. |
| 6 | MUST | No variant creates, updates, deepens, migrates or publishes an analysis implicitly. |
| 7 | MUST | In each composed session, the review uses the shared navigation and exact run binding where required, preserves its own gates and authorized operations, and applies current-source verification or explicit fallback without implicit map writes. |
| 8 | SHOULD | Map-guided localization reads fewer unrelated files than broad repository exploration, without omitting the source needed to justify the answer. |

## Evidence and cost

Keep all transcripts, tool calls and the setup run identity. Use a separate
scorecard row for setup, every variant/channel pair and each composed session. Record session identity,
wall-clock, manual file reads, map queries and fallback searches in each row.
A green package test is not a substitute for this live case.
