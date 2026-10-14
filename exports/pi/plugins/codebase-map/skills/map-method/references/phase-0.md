<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
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

Runs in **every depth, including `--depth=lite`**, and runs first, in the orchestrating context: reading project instructions and globbing for index files is cheap, and what it finds shapes what every later phase looks for.

Phases 1 through 7 keep their numbers. `--phase N` is a user-facing flag and renumbering would break every invocation that names a phase.

**Phase 0 is a preamble, not a selectable analysis phase.** It runs before every invocation, `--phase 5` and `--docs-only` included, and it does not change the numbering semantics of phases 1 to 7. `--phase 5` still means "run phase 5 and nothing else from the analysis set", with the preamble in front of it. `--phase 0` runs the preamble alone, which is a legitimate way to ask only "how does this repository document itself".

This phase owns discovery of **how the repository documents itself**. It does not evaluate whether the documentation is accurate, which is Phase 6.

1. Read `CLAUDE.md`, `AGENTS.md` and any equivalent project instruction file at the repository root and in the target's ancestors. Record any navigation instruction they give, especially a statement of the form "look here first to find where a concept lives".
2. Locate the canonical indexes the project actually uses. Glob for, at minimum: `**/SEARCH_INDEX.md`, `**/INDEX.md`, `docs/README.md`, `README.md`, `**/BY_DOMAIN.md`, `**/adr/**`, `**/decisions/**`, `**/architecture/**`, `**/domains/**`. Record what exists, not what you expected to exist. The perimeter applies here as everywhere: an index under a dot directory, or one Git ignores, is not a lead.
3. For each concept, symbol and subsystem in the analysis scope, search the located documents for an entry. Record the concept, the document, and the anchor or heading that matched.
4. Write both output files. Every row is a lead with status `documented` or `unverified`. Nothing here is `verified`, because this phase reads no code.

`$RUN_DIR` below is the active run directory, `.codebase-map/runs/<run-id>/`, per the Concurrent Runs Model in `references/run.md`.

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
[How this repository organizes its knowledge, in prose. Name the file the project treats as its semantic index, if it has one.]

## Not found
[Index kinds searched for and absent. An absent index is a fact worth recording.]
```

**Output file:** `$RUN_DIR/knowledge/documentation-leads.md`

```markdown
# Documentation Leads

> Leads, not truth. Every row is a pointer to where the project claims a concept lives.
> Status is `documented` or `unverified`. No row here is `verified`: this phase reads no code.

| Concept / symbol | Document | Anchor | Status |
|------------------|----------|--------|--------|

## Concepts in scope with no lead
[Concepts the scope touches for which no document was found. This list is what a
downstream consumer must discover independently.]
```

This unit is the only copy of Phase 0. `/codebase-map:analyze` runs it before its first analysis phase, and `/codebase-map:team-analyze` runs it once for the whole run. `/senior-review:team-review` reaches this phase through the `analyze` workflow, and its Phase 1d consumes `knowledge/documentation-leads.md` from whichever path produced the run.
