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

## Step 2: Behavior inventory (always, before any code)

Read every test in scope and produce the inventory table. Track behavior and observable contract together with the distinct failure mode, oracle source and bugfix history. Similar test names and equal counts do not establish duplication.

| Behavior / contract | Failure mode | Oracle source | Bugfix provenance | file:line | Duplicate of | Value (high/low/none) | Reason |
|---|---|---|---|---|---|---|---|

Flag separately, each with evidence:

- **Contradictory pairs**: tests asserting incompatible outcomes for the same input/state.
- **Implementation-coupling candidates**: internal mocks, call-echo asserts, private access. Confirm the actual boundary or diagnostic purpose before declaring these defects; preserve justified protection.
- **Never-failing**: no asserts, tautologies, everything mocked.
- **Quarantined entries** for this module, each with a keep (behavior worth preserving in the rewrite) or drop proposal. A drop proposal cites evidence beyond age: feature removed, replacement coverage, temporary origin, no bug-fix provenance.

Under `--dry-run`, save this inventory as the native coordinator report at
`<output-root>/consolidation.md`, reusing the run's already-declared final Markdown
path. Bind it to the existing `test-consolidate-report` artifact. Include scope,
snapshot, protected failure modes, oracle/bugfix provenance, unavailable metrics
and the explicit dry-run status: acceptance, rewrites, removals and mutation gates
were not executed. Print the inventory. For requested HTML or useful
navigation/comparison, read `references/human-view.md` before delivery and closure.
Stop here without entering Steps 3 through 7 or applying any quarantine change.

## Step 3: Safety-net check

Determine critical flows and failure modes from the project contract and existing evidence. Where meaningful protection is missing, use `testing:test-writer` to add the justified checks at the lowest sufficient layer before deletion. No fixed test quota or universal e2e prerequisite proves safety. Browser checks use the `developer-essentials:e2e-testing-patterns` skill, a required upstream dependency; check that the current host can load it before accepting a browser lane. Missing upstream capability leaves that lane open, without substituting an improvised method or forcing browser tests for non-browser behavior.

## Step 4: Approval gate

Present the inventory as a user question, grouped per owner (source file for unit tests, behavioral scope above that layer): the keep-list (behaviors the rewrite will cover) and the delete-list (duplicates, never-failing, dropped quarantine entries). Unanswered rows default to KEEP. No flag bypasses this gate. Contradictory pairs need an explicit ruling: which behavior is the correct one (check the authorized product contract, historical bugfix evidence and independent oracle before proposing; the current implementation cannot declare itself correct).

## Step 5: Rewrite

One primary file per owner at the correct layer, covering exactly the approved behaviors plus any evident gaps the user approved, with justified scope splits documented. Follow the established mirrored or colocated convention at unit; use behavioral ownership at integration, contract, and e2e. Follow the prevention rules of the test-hygiene skill; write test content behavior-first per the `mattpocock-skills:tdd` skill (upstream mattpocock/skills, a hard dependency of this plugin; if unavailable, stop and recover mattpocock-skills@mattpocock through the active host as specified by test-hygiene; verify the actual skill is loadable before continuing).

## Step 6: Replace originals atomically

Capture `pre_phase_sha` and the owned file snapshot before rewriting/removing any
original. Preserve bugfix provenance in the inventory. Rewrite and remove only
approved duplicate/retired files in the same candidate; do not leave parallel
suites. Do not erase unresolved ledger entries or historical proof before the
replacement has been validated. Both changes belong to the same authorized commit.

## Step 7: Verify before commit

Use `work-controller:work-record` to bind the required checks to the exact
candidate snapshot, required command/configuration and job identity. Map each
approved protected behavior and distinct failure mode to a surviving check with
an independent oracle. A bugfix regression survives unless its behavior is
explicitly retired or its exact failure mode has justified replacement protection.
Coverage and test counts are descriptive supporting evidence, never the gate.
Required lanes that cannot execute locally await authorized same-snapshot remote
results; an old green job, different configuration or collection-only run is open.

On a failed gate restore the owned pre-edit snapshot or `pre_phase_sha` through the
protocol, verify originals and earlier successful phases survive, then halt.
Hard reset is available only in an exclusively owned clean isolated worktree.
After successful gate commit only with authorization. If an already published
owned commit needs recovery, use an authorized revert rather than rewriting shared
history, and gate the recovery snapshot too.

## Step 8: Report

Write the native coordinator report to `<output-root>/consolidation.md`, reusing
the run's already-declared final Markdown path when present. Bind that report to
the existing `test-consolidate-report` artifact and project-result envelope;
operational JSON remains state, not report content. Include:

- Before/after table: files, test cases, runtime, coverage.
- Existing checks reused, updated or consolidated, with each added check's
  distinct protected failure mode. Zero additions is valid; lower counts alone
  are not an objective or proof of preserved protection.
- Behaviors dropped, each with the user's recorded reason from Step 4.
- Quarantine entries processed and entries remaining for other modules.
- Suggested next module by the latest audit's remediation ranking, when a `TEST_AUDIT.md` exists.

Preserve approved behavior/failure-mode mappings, independent oracles, bugfix
provenance, exact candidate gate results and unavailable or unknown measurements.
For requested HTML or useful navigation/comparison, the coordinator reads
`references/human-view.md` in this skill after the native report and required
gates are final, before run closure. Workers deliver native findings only.
