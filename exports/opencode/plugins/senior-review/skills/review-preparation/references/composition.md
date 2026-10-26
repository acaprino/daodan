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

# Bind specialist jobs

This is the composition step of preparation, including light's distinct preparation; it
does not select another roster, run a worker or replace the native review method.

## Prepare once

Preserve the generalist's boundary floor through canonical members. To narrow a
computed family, preparation records `applicability` rows: `specialist_id`,
`scope_id`, exact `candidate`, `status: not-applicable`, and `evidence` entries
with a source `path` and concrete `reason`. The coordinator reads that evidence;
the helper validates its binding, not its truth. Missing, unknown, conflicting or
stale decisions retain the obligation. Explicit required/source obligations and
the core local checks cannot be removed this way. Preserve exclusions in the
grounding record rather than treating lexical silence as proof.

Turn an evidenced cross-provider handoff into a required receiving specialist
through existing source/configuration/requirement rows or `required_specialists`.
For example: direct React Server Actions require authorization at the action;
offline conflict policy requires transaction integrity; client-declared authority
requires authoritative authorization and any implicated domain invariant. A note
without the receiving obligation and its source/policy cannot close coverage.

Use the compiled `reviewer-catalog.json` from this installed skill and the
candidate-bound context supplied to `review_roster.py`. Include that catalog in
the context. Resolve every required member through the verified installed
provider inventory. Missing providers, changed files, unknown applicability or
unmet prerequisites remain explicit failures or gaps. A preset expands its
canonical members; a method binding also retains its audit-only method task.

Satisfy the expanded members' prerequisites before binding jobs. Testing members
reuse `testing:test-preparation` in audit mode with the assigned scope and run
permission, including light. Reuse settled D1/D9 evidence once; record missing
inputs and stale/unmeasured metrics. This prepares inputs without another reviewer,
standalone workflow or repeated settled checks.

Build one bindings object from verified values:

- `host`, `candidate`: the catalog host and exact roster grounding candidate.
- `knowledge_selection`: fingerprint of the once-prepared selection, including an
  explicit empty selection. Changes invalidate the job; do not select again per member.
- `common`: file and SHA-256 pairs for `reviewer-common.md` of
  `senior-review:review-quality-gates` and the brief's working discipline.
- `roles`: keyed by required canonical ID. Copy `provider`, `provider_version`,
  `source_hashes` and `host_binding.file` from the verified catalog entry; `root`
  is that installed provider's actual path. Method bindings also carry `skills`.
  Do not copy role prose into this object. Different content requires a new
  catalog binding, never a caller-supplied replacement digest.
- `scopes`: keyed by `scope_id`. Supply `input_mode`, the actual scoped
  `permissions` grant and `output_dir` relative to the owned run. Modes and grants
  must agree with the member brief. Independent modes never share a job.
- Optional `max_body_chars`: measured context limit, not permission to drop checks.

The helper reads the installed bodies, checks their fingerprints, preserves each
member's operation restrictions and supplies common instructions once per job.
Session permissions and the read-only review contract still govern every operation.

With `SENIOR_ROOT` the verified installed senior-review provider:

```text
python "${SENIOR_ROOT}/skills/review-preparation/scripts/composition.py" --roster ROSTER.json --catalog CATALOG.json --bindings BINDINGS.json --out PREPARED-REVIEW.json
```

The result preserves the roster and adds validated `jobs`. Validate before
dispatch and append that complete review to the run's immutable `reviews`; an
empty raw `jobs` list from the roster is not an executable plan. Record pending
deliveries with the review ID, job ID, role and assigned path. Keep one canonical
body artifact; plans, selection tables and logs reference its binding. Historical
records retain their original contract. Continuing a stale/unprepared review
requires a fresh prepared entry, never mutation of the immutable old entry.

## Execute and account

Each job carries its role, canonical `specialist_ids`, scope, input mode,
candidate, knowledge and source fingerprints, body digest and output path.
Dispatch `work-controller:isolated-worker` through the consuming workflow's
declared isolated inline binding with the complete actual worker role and exact
job body supplied once through the active host mechanism, plus the native variant's
prepared inputs. Supply body-free job metadata for accounting; do not make a worker
reload a task body already injected in its initial prompt. Bind the worker role's
verified provider/root separately from each member's provider/root. A job ID is a
delivery identity, never an invented agent type.
Do not load a role as a skill. Qualified named presets and single specialists
remain invocable through their registered host bindings.

Discovery jobs with compatible scope, mode and permissions may unite members;
the same member on different scopes remains distinct. Premise derivation,
verification lenses and critic keep independent contexts, inputs, delivery IDs
and output files. A discovery delivery cannot also satisfy a verification check.
Reusing same-candidate blind derivation is allowed only under its existing method
contract, without supplying peer conclusions to it.

Light requires exactly one discovery job. An insufficient budget fails or asks
the caller to use branch review; no silent member omission or hidden fan-out.
Budget splitting in branch review retains every obligation and its evidence.

At delivery, bind job ID, role, members, scope, candidate and body digest. Each
`member_results` row declares specialist ID, delivered/failed status,
complete/incomplete coverage, canonical finding IDs and gaps. Write a finding
once and reference it from all relevant members. A clean member still reports
completed checks; silence, an empty file or a worker stopping is not delivery.
Failed mandatory coverage prevents completion even when all workers have stopped.

The coordinator checks expected jobs and member outcomes, then the native
blind/critic/verification requirements through work-controller. Lens results
have separate files, candidate bindings and evidence. Required checks survive
fast/no-context options. Consolidation retains finding provenance and every
coverage limitation; the existing final writer alone publishes the report.
