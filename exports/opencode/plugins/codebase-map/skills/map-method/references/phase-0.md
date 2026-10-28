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

# Phase 0

## Phase 0: Project Knowledge Discovery

Run first on every fresh run at every depth, including `--depth=lite`, `--phase N` (N from 1 to 6) and `--docs-only`. For `references/entry-analyze.md`, the isolated analyst runs Phase 0; for `references/entry-team-analyze.md`, the entry runs it once globally. A resume can inherit confirmed knowledge files. Phase 0 is a nonselectable preamble; phases 1 to 7 retain their numbers. Refuse `--phase 0` and `--phase 7`.

Discover how the repository documents itself to guide phases; leave accuracy evaluation to Phase 6.

1. Read `CLAUDE.md`, `AGENTS.md` and any equivalent project instruction file at the repository root and in the target's ancestors. Record navigation instructions, especially where to look first for a concept.
2. Find the canonical indexes actually used. Glob at minimum: `**/SEARCH_INDEX.md`, `**/INDEX.md`, `docs/README.md`, `README.md`, `**/BY_DOMAIN.md`, `**/adr/**`, `**/decisions/**`, `**/architecture/**`, `**/domains/**`. Record existing and absent index kinds. Apply the perimeter: indexes under dot directories or ignored by Git are not leads.
3. For every scoped concept, symbol and subsystem, search those documents; record the concept, document and matching anchor or heading.
4. Write both files below. Every row is a `documented` or `unverified` lead, never `verified`; this phase reads no code.

`$RUN_DIR` is the active `.codebase-map/runs/<run-id>/` directory, per the Concurrent Runs Model in `references/run.md`.

**Output file:** `$RUN_DIR/knowledge/navigation.md`

```markdown
# Project Knowledge Navigation

## Project instructions read
| File | Navigation rule it states |
|------|---------------------------|

## Canonical indexes found
| Index | Path | What it indexes |
|-------|------|-----------------|

## Conventions observed
[Describe knowledge organization in prose; name the semantic-index file, if any.]

## Not found
[Searched-for index kinds that are absent.]
```

**Output file:** `$RUN_DIR/knowledge/documentation-leads.md`

```markdown
# Documentation Leads

> Discovery leads, never verified facts: pointers to where the project claims a concept lives.
> Status: `documented` or `unverified`, never `verified`; this phase reads no code.

| Concept / symbol | Document | Anchor | Status |
|------------------|----------|--------|--------|

## Concepts in scope with no lead
[List scoped concepts with no document, which downstream consumers must discover independently.]
```

This unit is Phase 0's only copy. `team-review` reaches it through `references/entry-analyze.md`; Phase 1d consumes `knowledge/documentation-leads.md` from whichever path produced the run.
