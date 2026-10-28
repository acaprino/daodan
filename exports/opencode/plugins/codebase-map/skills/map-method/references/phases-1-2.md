<daodan_host_binding host="opencode">
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

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network fetch uses webfetch, network search uses
websearch, and a user question uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

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

Reuse inventory; never rebuild per file.
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
