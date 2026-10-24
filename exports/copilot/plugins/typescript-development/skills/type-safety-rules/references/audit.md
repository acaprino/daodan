<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

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

# TypeScript Type-Safety Audit

Audit type soundness and typed runtime boundaries. The coordinator prepares evidence, dispatches the declared reviewer and writes the native final report below. Canonical member roles own detection; do not copy their checklists into a second worker prompt.

Caller: `/daodan:check-health`. Senior-review supplies its own prepared scope and native format when it dispatches `typescript-development:type-safety-auditor`; do not also run this method for that assignment.

## Inputs and scope

Use the caller's target, candidate/snapshot, requirements, run directory and permissions. A project uses full scope; a path uses that directory/file scope; a caller-resolved diff uses changeset scope with both sides, staged/unstaged work, untracked paths, removals and renames. Follow implicated callers, configuration and unchanged counterparts within admitted read scope. Do not infer that a preexisting content defect was introduced by the change.

Include TypeScript modules, first-party declarations, boundary producers/consumers and the effective tsconfig closure, including extends and project references. Preserve runtime schemas and serialization evidence; compiler success alone does not prove boundary validity.

Keep a complete scoped inventory and the paths read in depth separately. Prioritize entrypoints and consequential paths, then finish the assigned checks or report the unexamined scope. Sampling or a read limit never proves full coverage. If no applicable source exists, record the inspected inventory and reason.

## Prepare evidence

Inspect relevant source and project configuration before dispatch. Collect the project-configured type check (including referenced projects) and linting when available and authorized. Use existing local tooling, preserve the actual command, exit status, candidate and output, and report unavailable tooling rather than hiding errors or treating it as a clean run. Do not install tools implicitly.

Bind supplied performance profiles, budgets, compiler/linter output and product requirements to their source and conditions. Source reasoning is not a measured runtime result. Resolve the installed provider root and assigned knowledge once; an unknown target, missing mandatory input or stale binding remains a gap.

## Step 3: Run Review Agent

Dispatch `typescript-development:type-safety-auditor` in its required isolated context through the host harness. Supply the full prepared scope, source/evidence paths, provider root, snapshot, requirements, working discipline, permissions and intermediate report path `<run>/ts-review/worker-findings.md`. Use the actual rendered role, including each canonical member; loading a role as a skill is not dispatch.

The reviewer returns its findings and a delivered or failed outcome; it does not write the final report. Record that outcome before the report phase. A failed or missing delivery leaves the review incomplete and must be reported.

Supply the native report fields below as the assignment's common review conventions, once. Findings carry severity, current file:line evidence, the required behavior or budget, causal impact, counterevidence, numeric confidence and a concrete correction. Preserve rejected candidates, coverage/gaps, assigned knowledge usage and any required member_results in the one intermediate report. No automatic violation follows merely from an absent optimization, new API, compiler flag or preferred technique.

The coordinator verifies delivery and every assigned member before consolidation. Deduplicate the same cause without hiding independent failure modes. Keep all mandatory gaps open. Scores use evidenced category judgments and explicitly mark unassessed categories; do not derive a score from file counts or API adoption alone.

## Step 4: Generate Markdown Report

After the agent completes, create the `<run>/ts-review/` directory and write `report.md`.

Order findings by severity, then file name.

**Output file:** `<run>/ts-review/report.md`

```markdown
# TypeScript Type-Safety Review: [date]

[Mode, scoped inventory, paths read in depth, runtime paths exercised and remaining gaps]

## Ground Truth

[tsc error count and eslint summary, or "Compiler/linter unavailable: static source analysis only; unverified checks and impact listed below."]

## Scores

| Category | Score |
|----------|-------|
| Any Hygiene | X/10 |
| Cast Discipline | X/10 |
| Config Strictness | X/10 |
| Boundary Validation | X/10 |
| **Overall** | **X/10** |

Critical: X | High: X | Medium: X | Low: X

## Files Audited

- `tsconfig.json`, `api/client.ts`, ...

---

## Critical & High Issues

### [rule-id]

#### `file.ts:42` [issue title]
- **Severity**: Critical
- **Confidence**: 90
- **Issue**: [what breaks at runtime]
- **Fix**: [fix instruction with code]
- [ ] Fixed

## Medium & Low Issues

[same structure, compact]

## Positives

- [what is done well]
```

Present the report summary to the user with the top findings and the report path.
