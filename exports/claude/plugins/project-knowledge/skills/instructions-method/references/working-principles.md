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
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
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

# Working principles

Principles 1-4 derive from multica-ai/andrej-karpathy-skills (MIT), snapshot
2026-05-17. Their sub-bullets and principle 5 are local adaptations.

Use this block when creating instructions if the project has no equivalent
working guidance. Preserve equivalent project-specific guidance when maintaining
an existing file. Missing headings or different wording alone are not defects.

The original local execution wording below is owned by
`work-controller:work-record` (already required). Equivalent guidance
in existing target projects remains valid.

```markdown
## Working Principles

### 1. Think Before Coding
Working assumptions: State material assumptions and unresolved alternatives before dependent work. Ask only for an essential decision that existing instructions or authorization cannot resolve; continue independent authorized work.
- Read related code before editing; understand the call sites
- Isolate the root cause; don't patch symptoms
- Surface unknowns instead of guessing

### 2. Simplicity First
Working simplicity: Choose the simplest design that satisfies approved requirements and existing contracts. Prefer, in order, suitable project code and conventions, platform or standard-library facilities, dependencies already available, then the least new code. Explain an exception when an earlier option cannot meet the requirement or is more complex overall. Reuse existing owners; add no speculative features, abstractions or configuration. Preserve boundary validation, data-loss prevention, security and accessibility. Before recommending or adopting a dependency, verify maintenance and support status, fit, compatibility, license, security and total integration cost using current official sources. Disclose unverified status; do not recommend discontinued or unverified libraries by default.
- One responsibility per function or module
- Remove preexisting code only with evidence, within the approved task authorization and any required checks or approvals.
- Prefer composition over premature inheritance
- Before building a common capability, check existing project implementations, standard-library facilities and dependencies already in use. Evaluate established libraries when those do not meet the requirement; honor project dependency constraints.
- Before recommending or adopting a library, check current official sources for archival, deprecation, supported releases and meaningful maintenance. Record the source and check date instead of relying on model memory. If verification is unavailable, state the gap and do not present the library as a verified recommendation. A stable library need not release frequently; recent commits or popularity alone do not prove suitability.
- Compare the total cost of reuse, including transitive dependencies, adaptation, upgrades and long-term ownership. Prefer custom code when it is simpler overall or no suitable solution exists, and record the concrete reason.

### 3. Surgical Changes
Working scope: Limit edits to the task and owned files, match existing style and preserve unrelated work. Remove code made unused by your changes; remove preexisting code only when its removal is explicitly authorized and any required checks or approvals are satisfied.
- No drive-by refactors outside the task scope
- Preserve public APIs unless the task requires a change
- Keep diffs small and reviewable

### 4. Goal-Driven Execution
Working verification: Define observable success criteria from approved requirements. Run meaningful checks on the actual candidate and preserve independent protection. Report unavailable checks; missing required checks or deliveries keep the task open. Finish when the criteria are met.
- Write tests against behavior, not internals (evergreen tests)
- Verify with real evidence: run the code, read the output
- Stop when the criteria are met; don't gold-plate

### 6. Redesign Instead of Patching
Working redesign: Fix the cause, never the symptom. When a defect shows that a script, skill, contract or workflow is shaped wrong for its problem, redesign that unit from the ground up so it solves the whole problem, instead of patching the case at hand. A patch that leaves the design wrong is debt, not a fix; record the redesign decision and its reason.
- A fix that only special-cases the failing input leaves the next input to fail the same way
- When a unit needs a second patch for the same class of defect, redesign the unit
- Keep the redesign within the task's authorization and verify it against the original failure

### 5. Centralize Shared Logic
Give each shared concept an explicit owner within its domain. Before adding an external call or cross-cutting concern, find and extend the existing client or method when it represents the same concept. Keep unrelated domains separate; similar syntax alone does not justify a common abstraction.
```
