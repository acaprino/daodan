# Phases 1 and 2

## Phase 1: Structure Extraction

Build the structural map from the current manifest. Inventory covers parsed
languages, stylesheets (one symbol per rule; minified stays file-level),
configuration/documentation and unparsed presentation (markup, single-file
components, indented Sass; file-level without symbols). Other extensions are
absent from every derived count; state that limit in the final report. The
manifest's `scope` declares perimeter exclusions: Git-ignored paths and dot
directories never enter inventory.

First query `source_reader.py graph` on `source_manifest` for the mapped files
(exact-file seeds, never directories; omit seeds for whole scope). Consume its
imports/calls; read question-relevant candidate requests before claims. Preserve unresolved edges,
AST coverage gaps and truncation; supplement with usage search only where needed.

A minified stylesheet has any line over 10,000 characters. Configuration/documentation entries have no symbols; presentation formats include HTML, HTM, Vue, Svelte and indented Sass. Forbidden files never enter the manifest, even as hashes.

For each inventoried file, report recorded metadata and read source only for
additional claims required by the phase:
- Module/file name and path
- Language and framework
- Imports and dependencies
- Exported symbols (functions, classes, constants)
- File size and complexity indicators (line count, function count)

**Output file:** `$RUN_DIR/01-structure.md`

```markdown
# Phase 1: Structure Extraction

## File Inventory
| File | Language | Lines | Functions | Classes | Imports |
|------|----------|-------|-----------|---------|---------|
| ... | ... | ... | ... | ... | ... |

## Dependency Graph
[Mermaid diagram of module dependencies]

## Entry Points
[Main files, API routes, CLI handlers]

## Key Observations
[Notable structural patterns or concerns]

## Where to Add New Code
[For each major directory, describe what belongs there]
- New feature module: `[path]`
- New API endpoint: `[path]`
- New utility: `[path]`
- New tests: `[path]`

## Naming Conventions
[Prescriptive: "Use X" not "X is used"]
- Files: [pattern]
- Functions: [pattern]
- Classes: [pattern]

## Source reading
[Manifest binding, graph seeds/hops/coverage/truncation, actual files/ranges, parser/fallback diagnostics and gaps]
```

Classic owner: add phase 1 to `$RUN_DIR/state.json -> completed_phases`.

---

## Phase 2: Interface Analysis

For each module, document the public interface:

Use graph-discovered definitions; verify public contracts through source blocks,
types, validators and configuration. Resolution alone is not verification.

- Function signatures with parameter types and return types
- Class hierarchies and method signatures
- API endpoints with request/response shapes
- Configuration interfaces
- Event/signal contracts

**Output file:** `$RUN_DIR/02-interfaces.md`

```markdown
# Phase 2: Interface Analysis

## Public APIs
[Organized by module]

## Contracts
[Interface definitions, type shapes, schemas]

## External Dependencies
[Third-party libraries and how they're used]

## How to Add a New Module
[Step-by-step guide based on existing patterns]
1. Create file at `[path]`
2. Follow interface pattern from `[example file]`
3. Register in `[registration point]`
4. Add tests at `[test path]`

## Source reading
[Manifest binding, graph seeds/hops/coverage/truncation, actual files/ranges, parser/fallback diagnostics and gaps]
```

## Team mode

### Team extensions

| Heading | File | Mode | Writer | After | Aggregation |
|---|---|---|---|---|---|
| Cross-Partition Outgoing References | 01-structure.md | partition | partition-structure-worker | Dependency Graph | List sibling imports as <other-partition>::<symbol>; distinguish internal, cross-partition and external imports. |
| Cross-Partition Inbound References | 02-interfaces.md | partition | partition-structure-worker | External Dependencies | Find consumers in available sibling 01 files; otherwise state pending reconciliation. |
| Partition Map | 01-structure.md | consolidated | partition-synthesizer | first | One row per partition: name, path, language, file count, done or failed. |
| Cross-Partition Reference Summary | 01-structure.md | consolidated | partition-synthesizer | Entry Points | From partition, to partition, symbol, caller file and direction. |
| Cross-Partition Exports | 02-interfaces.md | consolidated | partition-synthesizer | Public APIs | Reconcile outgoing references against sibling exporters; list exporter, symbol and consumer partitions. |

### Partition worker

Partition imports distinguish internal, cross-partition and external references. Follow the extensions assigned to partition-structure-worker; keep reconciliation pending when sibling outputs are not available.

### Consolidation

| File | Common heading | Rule |
|---|---|---|
| 01-structure.md | File Inventory | Concatenate inventories, prefix rows with partition, sort by partition and file. |
| 01-structure.md | Dependency Graph | flowchart LR; one subgraph per partition; outgoing cross-edges carry (cross:<from>-><to>). |
| 01-structure.md | Entry Points | Union entries, prefix each with partition. |
| 01-structure.md | Key Observations | Aggregate partition observations and inventory exclusions. |
| 01-structure.md | Where to Add New Code | Concatenate guidance; add cross-partition concerns as a nested subsection. |
| 01-structure.md | Naming Conventions | Concatenate conventions; identify cross-partition style conflicts. |
| 02-interfaces.md | Public APIs | Concatenate under ### Partition: <name>. |
| 02-interfaces.md | Contracts | Concatenate partition contracts. |
| 02-interfaces.md | External Dependencies | Deduplicate packages; expose version divergences. |
| 02-interfaces.md | How to Add a New Module | Concatenate partition guidance. |
