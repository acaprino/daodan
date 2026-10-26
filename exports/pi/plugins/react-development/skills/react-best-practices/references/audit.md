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

# React Performance Audit

Audit React effects, dataflow, rendering and bundle behavior. The coordinator prepares evidence, dispatches the declared reviewer and writes the native final report below. Canonical member roles own detection; do not copy their checklists into a second worker prompt.

Caller: `/daodan:check-health`. Senior-review supplies its own prepared scope and native format when it dispatches `react-development:react-performance-optimizer`; do not also run this method for that assignment.

## Inputs and scope

Use the caller's target, candidate/snapshot, requirements, run directory and permissions. A project uses full scope; a path uses that directory/file scope; a caller-resolved diff uses changeset scope with both sides, staged/unstaged work, untracked paths, removals and renames. Follow implicated callers, configuration and unchanged counterparts within admitted read scope. Do not infer that a preexisting content defect was introduced by the change.

Include components, stores, server/client entrypoints, relevant stylesheets, assets, bundler configuration and dependencies needed to trace the React mechanism. Visual design remains outside this method; a stylesheet affecting React-owned rendering work is evidence, not an automatic exclusion.

Keep a complete scoped inventory and the paths read in depth separately. Prioritize entrypoints and consequential paths, then finish the assigned checks or report the unexamined scope. Sampling or a read limit never proves full coverage. If no applicable source exists, record the inspected inventory and reason.

## Prepare evidence

Inspect relevant source and project configuration before dispatch. Collect project-configured React/JavaScript linting when available and authorized. Use existing local tooling, preserve the actual command, exit status, candidate and output, and report unavailable tooling rather than hiding errors or treating it as a clean run. Do not install tools implicitly.

Bind supplied performance profiles, budgets, compiler/linter output and product requirements to their source and conditions. Source reasoning is not a measured runtime result. Resolve the installed provider root and assigned knowledge once; an unknown target, missing mandatory input or stale binding remains a gap.

## Step 3: Run Review Agent

Dispatch `react-development:react-performance-optimizer` in its required isolated context through the host harness. Supply the full prepared scope, source/evidence paths, provider root, snapshot, requirements, working discipline, permissions and intermediate report path `<run>/react-review/worker-findings.md`. Use the actual rendered role, including each canonical member; loading a role as a skill is not dispatch.

The reviewer returns its findings and a delivered or failed outcome; it does not write the final report. Record that outcome before the report phase. A failed or missing delivery leaves the review incomplete and must be reported.

Supply the native report fields below as the assignment's common review conventions, once. Findings carry severity, current file:line evidence, the required behavior or budget, causal impact, counterevidence, numeric confidence and a concrete correction. Preserve rejected candidates, coverage/gaps, assigned knowledge usage and any required member_results in the one intermediate report. No automatic violation follows merely from an absent optimization, new API, compiler flag or preferred technique.

The coordinator verifies delivery and every assigned member before consolidation. Deduplicate the same cause without hiding independent failure modes. Keep all mandatory gaps open. Scores use evidenced category judgments and explicitly mark unassessed categories; do not derive a score from file counts or API adoption alone.

## Step 4: Generate Markdown Report

After the agent completes, create the `<run>/react-review/` directory and write `report.md`.

Order findings by severity, then file name.

**Output file:** `<run>/react-review/report.md`

```markdown
# React Performance Review: [date]

[Mode, scoped inventory, paths read in depth, runtime paths exercised and remaining gaps]

## Product Brief Context

[If a product brief was found, summarize performance budget and stack info. If not, note "No product brief found: reviewed against general best practices."]

## Scores

| Category | Score |
|----------|-------|
| Re-render Control | X/10 |
| State Management | X/10 |
| Bundle Optimization | X/10 |
| React 19 Adoption | X/10 |
| **Overall** | **X/10** |

Critical: X | High: X | Medium: X | Low: X

## Files Audited

- `Component.tsx`, `Store.ts`, ...

---

## Critical & High Issues

### Re-render Control

#### `Store.ts`: [issue title]
- **Severity**: Critical
- **Issue**: [description]
- **Fix**: [fix instruction with code]
- [ ] Fixed

### State Management

#### `Context.tsx`: [issue title]
- **Severity**: High
- **Issue**: [description]
- **Fix**: [fix instruction]
- [ ] Fixed

### Bundle Optimization

#### `index.ts`: [issue title]
- **Severity**: High
- **Issue**: [description]
- **Fix**: [fix instruction]
- [ ] Fixed

---

## Medium & Low Issues

[Same format as above]

---

## What's Working Well

- [positive observation]
- [another positive]

---

## Action Plan

1. [ ] [top priority fix, from critical findings]
2. [ ] [second priority]
3. [ ] [third priority]
4. [ ] [fourth priority]
5. [ ] [fifth priority]
```

**Print a short summary** in the conversation:

```
React performance review complete.

Report: <run>/react-review/report.md

Overall Score: X/10
Re-renders: X/10 | State: X/10 | Bundle: X/10 | React 19: X/10

Critical: X | High: X | Medium: X | Low: X

Top 3 issues:
1. [critical issue summary]
2. [high issue summary]
3. [high issue summary]
```

When Critical findings exist, end the summary with the strict line:
```
STRICT MODE: X critical React performance issues found. Recommend addressing before shipping.
```
