<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
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

# Abstraction audit method

Audit a codebase for structural entropy: duplicated domain knowledge, competing sources of truth, redundant representations, duplicated or derivable state, missed unification, prior art that already exists, and abstractions that are fighting their callers. Report-only.

A coordinator that already holds a run loads this method. `/daodan:check-health` prepares the auditor's inputs through this procedure for its structure dimension. The reviews of `/daodan:review-changes` and `/daodan:review-branch` prepare the same diff-mode inputs themselves and hand them to the auditor; this procedure states what those inputs are.

## Existing analysis compatibility

Coordinators load `codebase-map:map-method` and apply `references/migration.md`
before root lookup or dispatch. Workers never migrate roots: use only its
`migrate_root.py resolve` for supplied bindings. Propagate returned paths.
Failed migration/resolution or a still-legacy `.codebase-xray` path blocks the
dependent operation; preserve archives and run IDs.

## Inputs

### TARGET

The caller passes one free-text target. Read it by form:

| Form | Reading |
|---|---|
| Empty, or text naming no path or ref | The current working directory is the codebase root. Global mode. |
| A path | The codebase root (`codebase_path`) and the Codebase Map target. Global mode. |
| A commit or a branch | Diff mode, with that ref as the base ref: the change under review is `TARGET...HEAD` plus uncommitted work in the current worktree. |
| A PR | Diff mode, with the PR's base branch as the base ref. The PR head must be the checked-out work. |

Free text beside a path or ref is read for the focus and scope signals below.

### Decisions and signals

- **Mode.** Decided by the target form above. Global audits the whole codebase. Diff runs diff-anchored instead of a whole-codebase audit and asks the same seven questions as "introduced or aggravated by this change". A caller that asks for diff mode with no ref gets the default base ref: the merge base with the default branch, falling back to `HEAD` for uncommitted work.
- **Scope.** Default: the whole target. When the caller names a subtree inside the target, limit findings to that subtree. The Codebase Map still runs on the full codebase.
- **Severity floor.** Default `medium`. Use `low` or `high` only when the caller passes it.
- **Focus.** Default `all`. Signal from the free text: knowledge-track concerns (duplicated domain knowledge, competing sources of truth, redundant representation, duplicated or derivable state) select `knowledge`, D1 to D4; form-track concerns (missed unification, prior art, wrong abstraction) select `form`, D5 to D7; a single dimension id (`D1` to `D7`) selects that dimension.
- **Concept index use.** Default: read the concept index and, in global mode, rewrite it. Signal: when TARGET is not a Git repository, do not read or write `concept-index.json` (pass `concept_index_path` as `none`). A caller measuring what the audit finds without a seed passes `none` as well.
- **Index rebuild** (global mode only). Default: reuse the existing index at its reported freshness. Rebuild, that is ignore any existing index and census the codebase from scratch, after a large refactor or a history rewrite: the signals are the freshness check reporting `unusable` for an unreachable baseline or rewritten history, or the free text naming a large refactor.

### Authorizations

None. The method edits no source and asks for no authorization. Its only write outside the run directory is the concept index in global mode, the persistent seed described in `references/concept-index-protocol.md`.

## Procedure

1. **Resolve the target path.** Defaults to the current working directory.

2. **Resolve the diff (diff mode only).** Run `git diff --name-only <base-ref>...HEAD` plus `git diff --name-only` for uncommitted work, and pass the union as `changed_files`. Abort with a clear message when the path is not a git repository.

3. **Acquire bound static context.** Follow the global or diff branch below, retaining the exact run directory, `run_id`, target, controls and the exact snapshot path from `snapshot.py resolve <bound-run-dir>`, never the mirror. The optional `08-interconnect-map.md` is read only from the same bound run; without it, knowledge-track findings carry `Bounded-context exception: unverified`.

4. **Resolve the concept index.** Unless the index is not used, check `<path>/.abstraction-architect/concept-index.json` and run the freshness script. Report the state to the user before spawning, so a `delta-stale` index is visible rather than silent:

   ```
   Concept index: delta-stale (baseline a13fe2, HEAD 92ac10, 4 concepts to revalidate)
   ```

   An absent or unusable index is not an error. The audit proceeds and declares the reduced coverage in its Gaps section.

5. **Dispatch `abstraction-architect:abstraction-architect-agent`** through its declared isolated host harness with the actual rendered role and immutable input binding. Supply `codebase_path`, `mode`, bound `xray_path`, `map_run_id`, `map_snapshot_path`, `map_changes_path`, `map_outside_diff_changed_files`, `concept_index_path`, `changed_files` in diff mode, `report_path`, `scope`, `severity_floor` and `focus`. Include the caller's working discipline, permissions, resolved provider root and native report conventions below once, not another detection checklist. Each canonical member must deliver its findings or explicit gaps in the one report. A missing/failed member prevents a clean completion.

6. **Verify delivery and maintain the index.** The reviewer writes `<run directory>/findings.md`, or `findings-diff.md` in diff mode. It never overwrites the persistent index. When global mode uses an index, request its full source-confirmed census as `<run directory>/concept-index-candidate.json`, using the existing `concept-index-protocol.md` schema and `concept-census.md` method. Include healthy single-representation concepts, not only findings. This is the existing global census delivery, not a new review schema. The coordinator validates it with `concept_index.py validate`, verifies the candidate/scope and examined territory, and alone publishes it to `concept_index_path`. Preserve the old index if delivery, provenance, validation or required census coverage is incomplete. A narrower scope must never overwrite a broader index. Record the actual commit/tree and dirty-state limitations; never label uncommitted evidence as a verified clean tree. `concept_index_path: none` disables both index read and publication. **Diff mode never writes the index.**

7. **Report to the user:** the report path, summary counts, the concept index state, and the top three findings as one-line previews.

The full report stays in the file so the user opens it deliberately.

### Global acquisition

After the migration preflight, inspect `.codebase-map/runs/*/state.json`, not just
`runs.json -> latest_completed`. Select the newest run by its recorded start time
that holds nonempty `01-structure.md`, `02-interfaces.md`, `03-flows.md` and
`04-semantics.md`. Validate `run_id` against the run directory, the snapshot's
`root` against this worktree and its `target` against the resolved audit target.
Exclude active or failed runs and broken bindings. A stopped partial run with all
four delivered files is eligible; its later phases need not exist.

Load the provider's `references/snapshot.md` and `references/reading.md` through
`codebase-map:map-method`. Check the selected run against the current worktree:

```bash
python "<codebase-map script directory>/snapshot.py" diff \
  <bound-run-dir> <target> --out <audit-check-dir> --verify
```

`<audit-check-dir>` is a directory under the run directory, owned by this audit,
outside the Map store and analyzed source. Preserve the parent snapshot and phase
files. A current run has no added, modified or removed files, no stale claims in
`01` to `04`, and a valid parser/root/target binding. Read it as is. Partial
publication status by itself does not make its delivered first four phases stale;
`recommendation` alone is not the currentness check. Parser mismatch or other
invalid evidence requires fresh context, never an assumption of freshness.

For a stale eligible run, execute the canonical analyze method of
`codebase-map:map-method` (`references/entry-analyze.md`) with its exact
`parent_run` supplied as an internal caller binding and the parent run's original
controls:

```text
target:          TARGET
update:          yes, from parent_run
stop after:      phase 4
run name:        <new-audit-run-name>
other controls:  the parent run's original controls
```

The child keeps the parent's identity in its lineage, preserves its source
snapshot, and re-derives stale claims through phase 4. Keep the new child's
returned run binding, not the old run or `latest_completed`. Do not inherit an
`08-interconnect-map.md` that the bounded child did not regenerate.

When no eligible run exists, obtain the first four phases with the same method:

```text
target:          TARGET
update:          no
stop after:      phase 4
run name:        <new-audit-run-name>
depth:           full
```

Execute only the canonical entry's preflight, answerable scope checkpoints,
dispatch, delivery gate and publication decision here. Dispatch its
`codebase-map:map-analyst` through the coordinator's declared harness in an isolated
context; loading the role as a skill executes no analysis. The partial Map stays
in its run and never publishes. Require the gate's valid delivered `01` to `04`
and bound snapshot before auditing. Missing or failed delivery stops the audit
with its diagnostic path; do not substitute the mirror.

### Diff acquisition

In diff mode, this method never launches a Map. Bind the newest target-bound
run with `01-structure.md` and `02-interfaces.md` when one exists, using the same
root, target and identity checks. Run the verified snapshot diff into this
audit's check directory. Compute the union of `files.added`, `files.modified`
and `files.removed`, subtract the resolved `changed_files` under review, and pass
every remaining path as `map_outside_diff_changed_files`. The auditor reports
every path in Gaps as changed since that bound snapshot outside the review diff.
Do not present the stale Map as current; read current source before promoting a
finding. An invalid snapshot, parser mismatch or failed check is a named gap.
With no valid run, continue on the concept index and independent discovery at
reduced confidence and state the missing Map and freshness evidence in Gaps.

### Auditor delivery

The worker consumes only the supplied immutable binding and never acquires a
new Map. The coordinator retains the native report owner and delivery checks.

## Output location

`<run directory>/findings.md`, or `<run directory>/findings-diff.md` in diff mode, passed to the auditor as `report_path`.

The concept index stays at `<path>/.abstraction-architect/concept-index.json`, where the coordinator publishes the verified global census and review workers read it across runs, following `references/concept-index-protocol.md`. Its directory is created automatically if missing.

## Prerequisites

- The `codebase-map` plugin must be installed (a hard dependency declared in this plugin's `plugin.toml`). Diff mode degrades gracefully without Codebase Map output and reports the reduced confidence in its Gaps section.
- Diff mode requires the target path to be a git repository.
- For monorepos large enough to benefit from partitioned analysis, obtain a partitioned Codebase Map first (the team analyze method of `codebase-map:map-method`, `references/entry-team-analyze.md`; the user starts a map with `/daodan:map-code`) to produce `08-interconnect-map.md`; the auditor will then include bounded-context fusion findings.

## Related methods

- The analyze method of `codebase-map:map-method` (`references/entry-analyze.md`) produces the bound run this method consumes; acquisition stops after phase 4 when context is missing or stale.
- The team analyze method of `codebase-map:map-method` (`references/entry-team-analyze.md`) is the partitioned Codebase Map for monorepos; it adds `08-interconnect-map.md` to the output.
- The reviews of `/daodan:review-changes` and `/daodan:review-branch` both run this agent in diff mode as their abstraction dimension, so a review already answers the "was this already available?" question for the changed code. Diff mode of this method serves a caller that wants that check on its own, without the rest of the review.
- `clean-code:readability-method` is style and readability cleanup. Different concern.

## Out of scope

This method does not produce a refactoring plan. The `suggested direction` field in each finding names the target layer or refactoring move in one sentence.


## Native report conventions

The coordinator supplies this format to all assigned members. Report current source evidence, causal impact and counterevidence; discovery counts are coverage facts, not severity. Keep knowledge selection/usage and required member_results in the same report. Missing required inputs remain failed coverage. Do not claim runtime verification from static analysis.

Both modes use the same section letters so consolidation is uniform. Omit an empty section.

````markdown
# Abstraction-architect findings[ (diff-anchored)]

**Generated:** <ISO timestamp>
**Mode:** global | diff
**Scope:** <codebase_path[/scope]>
**Codebase Map source:** <xray_path | none>
**Concept index:** <path> (<fresh | delta-stale | unusable: reason>)
**Severity floor:** <low | medium | high>
**Focus:** <all | knowledge | form | Dn>

## Summary
- N findings (H high, M medium, L low)
- Concepts censused: <n>  |  with more than one representation: <n>
- Top three findings, one line each

## A. Competing sources of truth (D2)
## B. Duplicated or derivable state (D4)
## C. Redundant representation (D3)
## D. Duplicated domain knowledge (D1)
## E. Prior art available (D6)
## F. Missed unification (D5)
## G. Abstraction fitness (D7)

### <Section letter><n>. <one-line title> (<severity>)

- **Dimension:** <Dn name>
- **Confidence:** <0-100, with unresolved premises stated>
- **Pattern:** <catalog id and name, or `uncatalogued`>
- **Evidence:**
  - <path/file.ext>:<line-range>: <role: candidate_owner | implementation | parameter | ...>
  - <path/file.ext>:<line-range>: <role>
- **Why this is a problem:** <one or two sentences naming the force that makes these change together>
- **Change amplification (L1):** <count> sites must change when this concept changes
- **Suggested direction:** <target layer or move, one sentence, per the remediation table>

```
Evidence track: KNOWLEDGE            Evidence track: FORM
Semantic identity: proven            Occurrences: 4
Occurrences: 2                       Independent implementations: yes
Must remain consistent: yes          Shared lifecycle: yes
Bounded-context exception: none      Rule of Three: satisfied
Canonical owner: ambiguous           Index-seeded: no
Index-seeded: <yes|no>
```

## H. Second occurrences noted, not flagged

One line per pair, exempt from `severity_floor`, so the next occurrence is recognisable. Form-track pairs only: a knowledge-track pair that passed its gate is a finding above, not a note here.

## I. Confidence and Gaps

- **Coverage:** concepts censused, representations read, searches run per concept
- **Concept index:**
  ```
  Concept index baseline: <sha>      Current HEAD: <sha>
  Delta determined: <yes|no>         Indexed concepts revalidated: <n>
  Unindexed changed concepts discovered: <n>
  ```
  Or, when degraded, the specific condition and what coverage was lost.
- **Index contradictions:** entries the source disproved, with what the source says
- **Gaps:** Codebase Map files missing, directories not covered, units skipped and why; every path changed since the bound Map snapshot outside the review diff, plus failed currentness checks
````
