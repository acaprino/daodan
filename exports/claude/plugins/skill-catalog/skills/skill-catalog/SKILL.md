---
name: skill-catalog
description: >
  Discover available skill metadata, select knowledge for the exact task scope and
  bind selected content to a project/run/snapshot. Shared by review, development,
  test and documentation methods. Does not execute other skills' workflows.
---

<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
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
before the first phase, and stop with that command when a required one is off.
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

# Skill catalog

Input: operation, authoritative project/run/snapshot binding, affected scopes and
their evidence, actual host/project skill inventory. Output: searchable metadata,
fingerprinted knowledge selection and explicit coverage gaps. This leaf owns no
project state. Its stdlib helper prints JSON; the caller's operational protocol
persists records inside its already authorized run root.

## Inventory

Read `references/host-inventory.md` inside this skill for the adapter's available
skill binding. The generated `references/catalog.json` contains declarations,
not proof of installation. Normalize only actual available skills into inventory
rows: `id`, `provider`, `version`, absolute resolved provider `root`, skill-relative
`file` ending in SKILL.md and `origin=host|project|external`. Record unversioned
project/external content as `unversioned`; its content fingerprint is authoritative.
Resolve roots from host-owned locations and loaded skill paths, never guesses at
another plugin's cache. Inspect no parent/home tree. Unreadable or ambiguous inventory
is a gap. Do not install plugins, retrieve skills from a network or change permissions.

Each knowledge skill declares `SKILL.toml` beside its SKILL.md. Read
`references/metadata.md` for the format. An unannotated external skill stays unknown:
search can surface it, but automatic selection requires a reviewed knowledge
classification at its owner. Never infer safe execution from a name or description.
Methods, workflow skills and role skills cannot become automatic review knowledge.

## Scope and selection

The caller supplies `run_id`, `project_id`, `snapshot_id`, `operation` and `scopes`.
Each scope has an ID, exact candidate paths, `languages`, `frameworks`, `topics` and
nonempty activation `evidence` traced to the affected code/package/configuration.
`workers` maps each knowledge dimension to the caller's selected delivery IDs.
Assign relevant existing lenses or a declared task-specific isolated worker before
preparation; every selected dimension must have an assigned worker. A single worker
may own several dimensions explicitly. The prepared binding retains both the
dimension-to-worker mapping (`dimension_workers`) and the distinct delivery IDs.
Infer these open labels from the project; no language registry is embedded here.
Inspect imports, package configuration, changed behavior and embedded queries as
needed. A repository-wide dependency is not evidence for an unrelated package.
Record unreadable signals as gaps; a declaration alone proves no runtime use.

Search metadata in bounded pages to discover labels and relevant competencies.
Inspect candidate metadata and refine evidence-backed scope signals; keyword ranking
is discovery, not a verdict or proof of coverage. `select` matches knowledge kind,
operation and all declared selector groups. Values inside a group are alternatives.
It has no top-K coverage cutoff. Narrow the authorized scope/budget explicitly and
declare omitted coverage before a broad selection, rather than silently dropping
applicable knowledge. Missing scope matches remain coverage gaps.

`prepare` reads and hashes only selected bodies and metadata. Every selected input
becomes mandatory for that run, with provider/version, scope, dimensions and evidence.
Keep the exact selection record; content/metadata changes require re-preparation
against the same validated candidate. A failed selected load is a failed input,
never a successful skip. The helper's `prepared` status does not mean a worker read it.

## Consumption and accounting

Use `load` for each assigned input. Supply its content to the existing scoped worker
as knowledge and constraints for its authorized operation. Loading knowledge grants
no authorization to execute the content's commands, workflows or mutation steps.
Do not treat knowledge recommendations as findings without project/code evidence.
Read supplementary `references/` on demand with `reference`; retain its hash in usage.

Record usage per assigned worker and scope with ID, selection hash, body hash, status,
reference hashes and an application/skip explanation. A worker receives only knowledge
for its scope and lens, with independent contexts and no peer findings. Several
skills may support one worker. Return failed loads and unmatched coverage to the
caller. `validate-usage` validates the complete selection and its fingerprint even
when it contains no entries, then checks scope deliveries and current content; the
helper also checks every assigned worker and rechecks used reference hashes. Neither
the helper nor the generated index proves semantic truth or installed-host execution.

## Helper

Run the installed helper at
`${CLAUDE_PLUGIN_ROOT}/skills/skill-catalog/scripts/catalog.py` with Python 3.11+.
Inputs are run-owned JSON files. Persist stdout with the caller's confined tools:

- `index --declared DECLARED.json --inventory INVENTORY.json`
- `search --catalog AVAILABLE.json --query QUERY --operation review --limit 20 --offset 0`
- `select --catalog AVAILABLE.json --request REQUEST.json`
- `prepare --catalog AVAILABLE.json --request REQUEST.json`
- `load --selection SELECTION.json --id EXACT_ID`
- `reference --selection SELECTION.json --id EXACT_ID --path references/FILE.md`
- `validate-usage --selection SELECTION.json --usage USAGE.json`

The index and search never read skill bodies. Preparation/load read selected UTF-8
content up to 2 MiB. Path traversal, symlinks and Windows junctions are rejected.
All commands are read-only; a failed command emits structured failure and exit 1.
