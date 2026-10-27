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

# DOCX content projection

`office:content` owns the ledger, strategy, transformations and logical sequence.
Use `structure.md` to select the document type serving that strategy, then
project real content into `CONTENT.md`'s DOCX `sections` with stable IDs, titles
and `unit_ids`, bound to its revision. Do not add a competing claim schema.

Create/derive needs a full section projection. Expand/revise needs a delta;
retain accepted units/sections and identify changes, moves, additions and
approved exclusions. Preserve inherited type, tone and sequence unless the
brief changes them. Restyle/edit/review/export does not reopen global content.
For a combined delivery reuse the same facts and content identity; a section need
not correspond to one slide. Include only requested format projections.

Give headings their selected type's voice, preserve source conditions and
evidence, and budget depth/extent for continuous reading or reference. A short
text can remain deep; longer text does not authorize filler. Required core claims
reach sections or carry authorized exclusions. Record optional omissions and
real gaps. New sources that conflict require an explicit authority decision;
dates alone do not settle them.

The document designer consumes the validated working or final projection and
assigned proposal or selected DESIGN.md under `office:design`'s
`references/art-direction.md` mode contract,
then finalizes page types, native styles, table/figure treatment, flow and growth
under `layout-patterns.md`. Page overflow can redistribute content; substantive
cuts, rewrites or changed priorities return to the content owner. Never shrink
body text to force an editorial budget.

Before composition explicitly load and validate the assigned working or final CONTENT record under
`office:content`'s `references/records.md`; compare its project/revision/formats
with DESIGN.md. Preserve literal coverage for unchanged/locked source blocks;
authorized free transformations also require independent comparison of facts,
conditions, uncertainty and claim strength. A generated mapping alone proves no
semantic conservation.
