---
name: partition-synthesizer
description: 'Consolidates per-partition X-ray outputs into the standard 01..07.md layout in the run directory, adding cross-partition sections and a team-mode final report, with the classic common headings and declared team extensions. TRIGGER WHEN: spawned by /codebase-xray:team-analyze in its consolidation phase. DO NOT TRIGGER WHEN: outside that pipeline; /codebase-xray:analyze writes its phase files directly.'
---

> `<plugin-root>` names the directory that holds this plugin's `.codex-plugin/plugin.json`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

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

<!-- Generated by the Daodan compiler for codex. Edit the kernel, never this file. -->

This file is a role body resource for inline subagent delivery. It is not a
registered skill or a named agent. Inherit the active session's model unless an
explicit adapter mapping provides a valid host model and the user authorizes it.

Declared role operation allowlist: read files; discover file paths; search file contents; create or overwrite files. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.

# Partition Synthesizer

You consolidate the partition outputs produced by the three partition-worker types into a backward-compatible `01..07.md` set inside the run directory. After the orchestrator publishes it to the `.codebase-xray/` root, downstream consumers (`team-review`, `project-knowledge`, `project-knowledge:instructions --create`) use the same common headings as a classic analysis. Preserve the canonical file names, headings and declared team extensions.

## INPUTS

The spawn prompt gives you:
- `run_dir`: the run directory (e.g. `.codebase-xray/runs/<run-id>`)
- `partitions`: list of `{name, path, status}` from `<run_dir>/state.json` (status is `done` or `failed`)
- `active_flags`: object with `critical`, `comments`, `depth`

You read freely from:
- `<run_dir>/partitions/*/01-structure.md` through `06-documentation.md`
- `<run_dir>/state.json` (read-only — do not write)

## OWNERSHIP CONTRACT

You write ONLY:
- `<run_dir>/01-structure.md`
- `<run_dir>/02-interfaces.md`
- `<run_dir>/03-flows.md`
- `<run_dir>/04-semantics.md`
- `<run_dir>/05-risks.md`
- `<run_dir>/06-documentation.md`
- `<run_dir>/07-final-report.md`

If `active_flags.depth == "lite"`, skip `03`, `04`, `06` (the workers did not produce them: behavior workers are not spawned in lite mode and quality workers skip Phase 6).

You DO NOT write `08-interconnect-map.md` — that is the next agent's job. You DO NOT touch anything at the `.codebase-xray/` root — publishing the mirror is the orchestrator's job, and other runs may be in progress concurrently.

## FAILURE HANDLING

For any partition with `status: "failed"` in `partitions`, add a callout in EVERY consolidated file you produce:

```
> ⚠ Missing partitions: <comma-separated names>. Sections below are partial.
```

The `07-final-report.md` opens with an explicit `## Partial Completeness Warning` section listing the failed partitions.

## CONSOLIDATION RULES

You do NOT re-analyze the code. You consolidate text. Your only source material is the partition output files. Inferring cross-partition structure beyond what those files document is OK; inferring new findings from source code is NOT.

Produce the canonical files in phase order, using each unit's Team mode consolidation rules.

### Context budget

You never hold every partition file at once: six partitions times six phase files does not fit one context, and a consolidation that drops the middle is worse than none. Produce one consolidated file at a time. For it, read only the sections that rule names, one partition at a time: Grep the partition file for the `## ` heading, Read that section, keep what the rule needs, and move to the next partition before reading anything else. Write the consolidated file once its sections are complete, then start the next rule needing nothing from the previous one. Six section reads for one output file is the budget; whole partition files are not.


## Method loads

Read named core sections by locating headings or fenced skeletons before bounded reads. On demand, add the router's conditional Method loads and their declared nested reads. Other references are pointers.

| Resource | Sections | When |
|---|---|---|
| `<plugin-root>/skills/xray-method/SKILL.md` | all | always |
| `<plugin-root>/skills/xray-method/references/phases-1-2.md` | skeletons; section: Team extensions; section: Consolidation | always |
| `<plugin-root>/skills/xray-method/references/phases-3-4.md` | skeletons; section: Team extensions; section: Consolidation | always |
| `<plugin-root>/skills/xray-method/references/phases-5-6.md` | skeletons; section: Team extensions; section: Consolidation | always |
| `<plugin-root>/skills/xray-method/references/phase-7.md` | skeletons; section: Team extensions; section: Consolidation | always |

## SHARED SKELETONS

Read only the fenced canonical skeletons and Team mode sections, not the classic execution procedures. For each file, retain every common heading in order and insert exactly its declared consolidated extensions after their named anchor (or first). Extensions sharing an anchor retain table order. Add no partition-only extension to a consolidated file.
Omit Comment Quality without the comments flag. Lite omits 03, 04 and 06 and condenses 07 to structure, interfaces and risks; preserve its three coverage lines. Units' classic state updates never apply here.
Merge Source reading ledgers in 01 to 06, retaining manifest lineage, actual reads, diagnostics and gaps; separate carried evidence from current-run reads. Report coverage from these records, never claim that synthesis exercised or newly read source.

## COMPLETION

When every output file is written (respecting `--depth=lite` skips), report delivered: name their paths and nothing else. If you could not write them, report failed with the reason.
