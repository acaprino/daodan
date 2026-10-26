# Architecture

Process Controller is an original local-first process engine inspired by durable DAG execution, bounded supervision and decision maps. It does not embed Hatchet, Foreman or Wayfinder.

## Ownership

- The process definition is the immutable description of the work.
- The SQLite store owns run state, attempts, claims, questions and the append-only event journal.
- The artifact store owns immutable content-addressed bytes. SQLite owns their metadata and admission state.
- The coordinator owns admission, frontier selection, dispatch and completion. A supervisor may propose an intervention but never admits a delivery or changes the graph.
- Host adapters own real agent dispatch and host handles. Domain consumers own their archetypes and rules.

## Token economy

The CLI returns bounded views instead of whole records. Job packets carry artifact references and digests, not every artifact body. Scheduling, validation, accounting and gates are deterministic. The engine does not use an LLM to extract operational memory.

## Storage

SQLite transactions update current state and append events atomically. `BEGIN IMMEDIATE` serializes claims across local processes. JSON columns hold versioned payloads where relational indexing is unnecessary. Artifact bodies live outside SQLite under the run home.

The first vertical slice supports graph definitions, agent and argv-command jobs, explicit external inputs, durable attempts, conservative resume, optional path-scoped Git commits and deterministic archetype composition. Dynamic replay, distributed workers, semantic memory and autonomous model calls are outside this slice.
