<daodan_host_binding host="claude">
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

Claude binding: repository read, file discovery and content search use Read, Glob
and Grep; repository write and repository edit use Write and Edit; shell execution
uses Bash; network fetch uses WebFetch and network search uses WebSearch; a user
question uses AskUserQuestion. Pass the executable string in Bash's
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

## Phase 2: Adversarial Review (parallel)

1. There is no team-creation step. The host harness dispatches each reviewer as this phase requires and records every one as `delivered` or `failed`.
2. Dispatch every validated job exactly once under preparation's
   `references/composition.md`, using its bound worker role and canonical member
   bodies in an isolated context. The roster supplies required coverage. The mapping
   below names owners, not extra activation rules. Resolve catalog entries even
   when a future registered identity has no example row here. A missing binding
   is a failed delivery, never permission to omit that reviewer.
3. Account for Phase 1c's same-snapshot blind premise report as the selected premise
   discovery delivery, rather than launching a second discovery pass. Later
   verification tasks keep their separate inputs, contexts and delivery records.

### Dimension-to-agent mapping

| Dimension | Agent |
|-----------|---------------|
| Security | `senior-review:security-auditor` |
| General correctness and local design | `senior-review:code-auditor` |
| **Logic integrity (contracts/invariants/domain rules)** | `senior-review:logic-integrity-auditor` |
| **Structural entropy (duplicated knowledge, competing owners, redundant representation, derivable state, missed unification, prior art, abstraction fitness)** | `abstraction-architect:abstraction-architect-agent` |
| Codebase hygiene (full pass: dead code, assets, deps, docs, lifecycle archaeology) | `senior-review:cleanup-auditor` |
| Workspace hygiene (garbage, tracked build output, .gitignore, scratch, doc-assets, git state) | `repo-hygiene:workspace-auditor` |
| UI race conditions | `senior-review:ui-race-auditor` |
| Accessibility and usable interaction paths | `senior-review:accessibility-auditor` |
| General performance and cost | `senior-review:performance-auditor` |
| Service operability, rollout and recovery | `senior-review:operability-auditor` |
| Distributed flows | `senior-review:distributed-flow-auditor` |
| Circular dependencies | `senior-review:chicken-egg-detector` |
| Temporal resilience (failure-over-time) | `senior-review:temporal-resilience-auditor` |
| Data integrity (persistence semantics) | `senior-review:data-integrity-auditor` |
| Resource lifecycle (ownership and release) | `senior-review:resource-lifecycle-auditor` |
| Testing quality | `testing:test-suite-auditor` |
| API contracts | `senior-review:api-contract-auditor` |
| Migration data validity | `senior-review:data-integrity-auditor` (same delivery as data integrity) |
| Premise discovery or document claim check | `senior-review:premise-auditor` (declared mode) |
| React rendering | `react-development:react-performance-optimizer` |
| TypeScript/type contracts | `typescript-development:type-safety-auditor` |
| Browser, mobile and desktop compatibility | `platform-engineering:platform-reviewer` |
| Python / dependencies | Catalog method bindings through `work-controller:isolated-worker`; see preparation's stack bindings |

### Reviewer prompt template (context-aware)

The validated jobs also contain applicable stack dimensions from
review-preparation's `references/stack-dimensions.md`. Their canonical member
methods use the shared template below within those jobs and enter the same
Phase 3 delivery barrier and downstream verification panel.

Build one concise brief per job. Supply its member identities, target, run identity,
snapshot, scope, applicable instructions, evidence/knowledge paths and a unique
intermediate report path. Reference prepared artifacts rather than pasting them
repeatedly. Include only context artifacts that exist and that this worker may
read; independent discovery receives no peer findings. The canonical role owns
its detection method and native output; the shared envelope adds provenance.

```
You are reviewing for the {dimension} dimension.

## Target
[Insert contents of .team-review/00-scope.md]

## Diff
{diff content}

## Context files (read these before analyzing code)
- Codebase Map output: $XRAY_RUN_DIR (see 01-structure.md, 02-interfaces.md, 05-risks.md)
- Interconnect map: .team-review/02-interconnect.md
- Knowledge provenance: .team-review/01-knowledge-provenance.md

### Epistemic status of the shared context

The shared context is NOT ground truth. It is an index of hypotheses produced by
one upstream observer.

- Claims marked `verified` guide source reading; confirm the premise against
  current source before using it in a finding.
- Claims marked `documented`, `unverified` or `disputed` are hypotheses. You MUST
  independently re-derive any such claim before using it as the premise of a finding.
- Actively search for code paths, tests or documents that contradict the context.
  Finding one is a result, not a failure.
- Silence in the context is not evidence of absence. A concern the map does not
  mention may still be real; look anyway.

Per `## Reviewer Hints` in the interconnect map, focus your reading on these anchors:
{anchors-for-this-dimension from the map's Reviewer Hints section}

## Instructions
Follow your agent definition's analysis phases, knowledge-base loading, output format, and severity classification. Cite file:line for every finding.

## Premise declaration (required on every finding)

Every finding carries two extra fields:

- **Load-bearing premise:** the single proposition whose falsity collapses this
  finding. It must be minimal, falsifiable and scoped.
    Bad:  "The implementation is broken."
    Bad:  "Heartbeat handling is incorrect."   (a paraphrase of your finding)
    Good: "No credential-bearing response path exists after registration."
- **premise_provenance:** one of `independent`, `shared-context`, `mixed`.
  This records CAUSAL DEPENDENCE, not citation. If you absorbed the premise from
  the Codebase Map output or the interconnect map, it is `shared-context`, even if
  your finding never cites an anchor. `mixed` means part of the premise rests on
  shared context and part on evidence you derived yourself. Declare `independent`
  only when you re-derived the whole premise from code, tests or documents you
  read yourself.

Write the one report to the prepared job.output_path using the native structured format, retaining every assigned member's findings and coverage.
```

If `--no-context` was set, omit shared analytical context and reviewer hints.
Keep the required roster and provide source-derived scoped semantic context to a
selected logic reviewer. Missing required inputs remain an explicit incomplete
delivery; they do not authorize dropping that role.

**Structural entropy dimension addendum.** Dispatch selected members of `abstraction-architect:abstraction-architect-agent` through their validated jobs. Append this native input contract once per job:

```
mode: diff
codebase_path: {target root}
xray_path: {$XRAY_RUN_DIR when Phase 1a ran and produced output, otherwise "none"}
concept_index_path: {target root}/.abstraction-architect/concept-index.json
changed_files: {the same file list used to build the diff above}
report_path: {prepared job.output_path}
severity_floor: medium
```

Four things about this reviewer, because they invert the default reviewer contract:

- Its search space is the **whole codebase**, not the diff. The diff is only the anchor; the existing representation it is hunting for is by definition in files that did not change. Do not scope it to the changed files.
- It runs fine on `--depth=lite` output, since it consumes only `01-structure.md` and `02-interfaces.md`. Do not force `--deep` on its account.
- `--no-context` does not skip it. It runs with `xray_path: none` and uses source discovery, reporting the missing map evidence in its Gaps section.
- It reads a **concept index** at `.abstraction-architect/concept-index.json` when one exists, which is what makes its knowledge-track dimensions (duplicated domain knowledge, competing sources of truth, redundant representation, duplicated state) worth running on a diff. The index is produced by the audit of `abstraction-architect:abstraction-architect` in global mode (`/daodan:check-health`). When it is absent or stale the reviewer degrades to diff-anchored discovery and declares the reduced coverage; it never blocks. This reviewer never writes the index.

**Testing dimension addendum.** `testing:test-suite-auditor` partly inverts the default reviewer contract. Append this to its prompt:

```
Scope: run D2 to D8 only on tests owned by the changed modules; keep D1/D9
statistics suite-wide for context. Do NOT run the full suite inside this
review (no-run semantics): reuse metrics from CI history or existing report
artifacts, and mark anything unmeasured as such. Findings in this command's
severity format within the one report at the prepared job.output_path.
```

Two notes on why: a review is diff-anchored, so a whole-suite execution would dominate the phase's wall clock for findings mostly outside the diff; and suite-wide inventory statistics still matter because parallel-file and cross-layer-duplicate findings are invisible when only the changed test file is read.

### The workspace-hygiene dimension

This dimension is not a `senior-review` agent. Dispatch the `repo-hygiene:workspace-auditor`
member within its assigned isolated job. It owns every check the filesystem and git
decide without reading a symbol.

```
You are auditing workspace hygiene for a team review of {target}.

Load the repo-hygiene:repo-hygiene skill and run its catalog at the FULL
profile: C1 filesystem garbage, C2 generated artifacts tracked in git,
C3 .gitignore completeness, C4 .gitignore archaeology, C5 scratch and
pipeline-output directories, C6 orphan doc-assets, C7 git auxiliary state.

Report only. Remove nothing, and never run a destructive git command: C7 is
detection-only because a dropped stash or a removed worktree leaves no diff
for any commit to revert.

Anything that needs source comprehension is not yours. Put it under "Not
mine" and name senior-review:cleanup-auditor. The two dimensions are disjoint
by construction, so a finding either of you could have raised means one of
you widened.

Return this member's findings and coverage in the one report at the prepared job.output_path.
```

Its perimeter and `cleanup-auditor`'s do not overlap, so Phase 4 consolidation
has nothing to deduplicate between them. A finding appearing in both reports is
a boundary violation to investigate, not an `echo` to fold.

### Dispatch

Dispatch validated jobs under preparation's
`references/composition.md`. They are the expected delivery set, retaining every
computed member/scope obligation and its canonical method. Do not also dispatch
the roster's thematic identities. The role-oriented handoff below applies to each
member within its assigned job.

Dispatch each job with:

- name: the prepared job ID
- agent: the job's bound worker role, resolved through the active host mechanism
- task: the prepared job body once, with the scoped template inputs above and each member's assigned anchors

The validated jobs and their member/scope obligations are the expected set that
Phase 3's delivery barrier waits on. Record each expected job and assigned output before dispatch. A dispatch
failure or missing output cannot shrink that set; a completed turn alone is not
a delivered result.

Mark `phase_2_review` as `in_progress`.

## Phase 3: Monitor and Collect

1. Hold the delivery barrier: wait until every dispatched reviewer is recorded `delivered` or `failed`.
2. As each job delivers, verify its assigned report exists and accounts for every expected member. If a worker returned the complete report without saving it, preserve that exact output at the assigned path; missing member coverage still fails the delivery gate.
3. Track progress: "{completed}/{total} reviews complete".
4. **Delivery gate** (per the `senior-review:review-quality-gates` skill, section `## Delivery Gate`): consolidation does not start until every spawned reviewer has either delivered its findings file or delivered an explicit no-findings report. A reviewer that has not delivered by a reasonable deadline gets one reminder, through whatever channel the host offers to a running worker. If it stays silent, record it `failed`, take whatever output it returned, save it to the findings path marked `[undelivered -- collected by orchestrator]`, and record the dimension as degraded in the report. A silently missing dimension is never presented as a clean one.
5. Mark `phase_2_review` complete, `phase_3_consolidation` in_progress.


## Raw inputs (`--no-context`)

Withhold shared analytical artifacts while preserving the required roster,
independent derivation and verification gates. Workers read the actual target
and permitted source evidence; they declare the provenance they used rather
than being labelled independent by a flag. Missing required inputs or blocked
support work leave the affected coverage incomplete. Preserve the same report
and delivery contracts. The light shape remains the single-reviewer method in
`references/light.md`; file size alone never selects or removes reviewers.

`--skip-interconnect` was removed in senior-review 9.0.0.
