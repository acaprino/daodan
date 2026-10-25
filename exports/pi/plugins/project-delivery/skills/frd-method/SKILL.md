---
name: frd-method
description: >
  Extract, validate, reconcile, approve, version and verify evidence-bound functional requirements documents in docs/frd/.
  TRIGGER WHEN: the user asks for an evidence-bound FRD, requirements and domain references must be extracted from project sources, a fresh extraction must be reconciled with manual review, or an FRD needs approval, revision or verification.
  DO NOT TRIGGER WHEN: recording an architecture or technical decision (use project-delivery:adr-method), writing general project documentation without evidence spans, or treating current implementation as an automatically approved requirement.
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

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

# Evidence-bound functional requirements

Load `work-controller:work-record` for run ownership and authorization. Read
`references/frd-schema.md` before constructing or changing extraction data.
The helper is
`python "<plugin-root>/skills/frd-method/scripts/frd_tool.py"`.
It writes only the FRD records and their generated index.

## Grounded extraction

1. Establish the requested product behavior, actors and scope from the user's request and interview. Current behavior, documentation and requested behavior remain distinct.
2. Inspect current code and documents. Use Codebase Map inventory, symbols and links to find evidence, then read the cited current source. The map is static navigation evidence, never a correctness oracle or a source of runtime proof.
3. Record requirements, `PERSON`, `ORGANIZATION` and `LOCATION` entities, and relationships with exact Unicode source spans. Report contradictions and runtime gaps instead of inventing certainty.
4. Write extraction JSON and run `propose`. Generated records and items remain `Proposed` and `extracted`; extraction never constitutes approval or verification.

Evidence must point to a project-relative file and match its current byte digest
and exact `[start,end)` excerpt. Do not cite an inaccessible, stale or inferred
span. Do not put secrets in excerpts.

## Load map

| Step | Run |
|---|---|
| Before using records | `validate --project ROOT` |
| New FRD | `propose --project ROOT --title T --slug S --task TASK --sha SHA --data FILE` |
| Revise Accepted | `propose --project ROOT --revise FRD-NNNN --task TASK --sha SHA --data FILE --expect-digest D` |
| Reconcile extraction | `merge --project ROOT --frd FRD-NNNN --data FILE --expect-digest D` |
| Review or correct an item | `resolve --project ROOT --frd FRD-NNNN --item ID --status verified\|corrected\|rejected --expect-digest D [--data FILE]` |
| Resolve a disagreement | the same `resolve`, adding `--conflict CONFLICT-NNNN` |
| Exact text approved by user | `promote --project ROOT --frd FRD-NNNN --sha SHA --expect-digest D` |
| Reviewer confirmed conformance | `verify --project ROOT --frd FRD-NNNN --sha SHA --expect-digest D` |
| Repair a stale index | `index --project ROOT` |

Use `validate --frd FRD-NNNN` to obtain the current Proposed and Accepted
versions and their digests. Every mutation of an existing record is optimistic:
read the exact record, then pass its digest. A mismatch means read and review
the new bytes rather than retrying blindly.

## Reconciliation and approval

`merge` never deletes missing items or overwrites semantic changes. It unions
new evidence, preserves `verified`, `corrected` and `rejected` review states,
and opens conflicts when extraction disagrees with an existing item. Resolve
each conflict explicitly. A manual correction uses complete item JSON and fresh
valid evidence. Promotion refuses unresolved conflicts.

Show the exact candidate and digest to the user. Call `promote` only after the
user explicitly approves that candidate. Never auto-approve because validation
passed, sources agree, a map contains a claim, or an implementation already
exists. Promotion accepts the FRD and supersedes its previous version; it does
not verify implementation. Only a separate reviewer conformance check justifies
`verify` and `last_verified_sha`.
