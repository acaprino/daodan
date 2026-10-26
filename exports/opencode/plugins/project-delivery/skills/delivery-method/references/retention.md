> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/`, `agents/` and `commands/`. The loader substitutes it in every body it registers; in any other file, resolve it once from where that file was loaded.

<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
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

# Retention of a run's output

A concluded run's own output is reduced to verified knowledge and then
quarantined, on request and only through the helper below. Nothing here
touches project files that the run did not create.

## Evidence

Reduce experiments and run output into verified knowledge before disposing
of data. For each attempt preserve goal, source snapshot, conditions, exact
command, inputs, outcome, errors, measurements, decision, limits and
reproduction instructions. Compare the proposed summary with the original
evidence, failed attempts included; contradictory results remain visible.
Past results do not replace executable regression tests. Durable conclusions
go through project-knowledge; temporary status stays in the run, never in
`AGENTS.md` or `CLAUDE.md`.

## Retention records

Write artifacts.json: schema daodan/artifacts/v1, run_id and artifacts entries
{path, owned_by, sha256, classification, status, reproduce}. Paths are relative to
this run and files exclusively created/owned by this run. Concluded disposable
classes are reproducible-output and completed-output; reproduction conditions are
mandatory for the former. Unknown ownership, cache, resume data and unresolved
evidence remain retained.

Write summary.json: schema daodan/evidence-summary/v1, run_id, summary,
verification {status:verified, by:<coordinator>}, retained_evidence [{path,sha256}],
required_artifacts and unresolved. Semantic verification requires reading sources;
writing a verified flag is not the verification. Keep a nonempty evidence subset.
Outstanding evidence blocks retention until explicitly resolved and retained.

Run the installed helper:
python "<plugin-root>/skills/delivery-method/scripts/artifacts.py" plan --run RUN --manifest artifacts.json --report summary.json
This writes retention-plan.json. Show every proposed path/reason and potential
byte total; default planning makes no removal.

After authorization, apply quarantine with:
python "<plugin-root>/skills/delivery-method/scripts/artifacts.py" apply --run RUN --plan retention-plan.json
This moves data within the run and reports zero bytes deleted.

Permanent deletion is a separate explicit --purge grant, not implied by --fix.
Write authorization.json {run_id, operation:purge, paths:[exact relative paths],
source:{kind:user,reference:<actual permission>}} and invoke apply with --purge
--authorization authorization.json. Never fabricate permission from a generic
cleanup request. Only concluded owned outputs in the original manifest are eligible.

The helper rejects traversal, symlinks/reparse points, hardlinks, changed files,
changed summary/evidence, unresolved references and quarantine collisions. It
writes a receipt before mutation and resumes prepared operations idempotently.
A stale retention lock requires proving the owning process stopped before recovery;
do not delete a live session's lock. Artifact fingerprints and confinement are
mechanical; truth of the summary and of human permission remains the coordinator's
responsibility.

repo-hygiene:repo-hygiene handles separate filesystem/Git hygiene and preserves
untracked quarantine. It does not interpret lifecycle state or purge its artifacts.
Record content bytes moved/deleted, retained evidence, result and remaining limits.
Measure filesystem free-space changes separately when needed; deleted file sizes
do not prove physical space recovered on a compressed or concurrently used volume.
