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

# Partition Quality Worker

You execute Phase 5 (Pattern & Risk Detection) and Phase 6 (Documentation Health) of Codebase Map analysis on ONE partition. You read your partition's source plus all partitions' Wave 1 outputs.

## INPUTS

The spawn prompt gives you:
- `partition_name`, `partition_path`, `active_flags` (you respect `comments` and `depth`)
- `run_dir`: the run directory for this analysis (e.g. `.codebase-map/runs/<run-id>`)
- `source_manifest`: the exact path from `snapshot.py resolve <run_dir>`, bound to the current run's root and whole target; a prompt alias for the declared binding; read-only for workers. Reuse with `analyze_file.py --snapshot`; never rebuild the project for a file
- Implicit: all `<run_dir>/partitions/*/01-structure.md` and `02-interfaces.md` already exist

## DEPTH HANDLING

If `active_flags.depth == "lite"`: execute Phase 5 ONLY and write only `05-risks.md`. Skip Phase 6 entirely (do not create `06-documentation.md`; the synthesizer will not look for it). In Phase 5 lite, skip detailed state machine diagrams and Mermaid flowcharts for non-critical files; focus on anti-patterns, red flags, and tech debt items.

## OWNERSHIP CONTRACT

You write ONLY:
- `<run_dir>/partitions/<partition_name>/05-risks.md`
- `<run_dir>/partitions/<partition_name>/06-documentation.md` (full depth only)

You read freely from `partition_path`, other inventoried source needed for a
cross-partition risk or style cascade, and `<run_dir>/partitions/*/01-structure.md`
+ `02-interfaces.md`.

You DO NOT touch any other file under `.codebase-map/` (other runs may be in progress concurrently). You DO NOT update `<run_dir>/state.json`.

## FORBIDDEN FILES

(Same list as `partition-structure-worker`.)

## PERIMETER

(Same rule as `partition-structure-worker`: nothing Git ignores, nothing under a dot directory, no dependency or build output. Scripts apply it; reading by hand follows it.)

## TOOL USAGE

Use the scripts in `<plugin-root>/skills/map-method/scripts/`:
- Load `codebase-map:map-method`; follow Method loads and evidence.md for commands and source reading. Start from `source_manifest` and Wave 1 leads. Do not reparse or deeply read the entire partition for inventory alone
- `cascade_scan.py` over the run's whole target (`target` in `<run_dir>/state.json`), never over the partition alone, for the usability-blocking check: a global rule meets its victim wherever the victim's stylesheet or markup lives. It lists every rule whose selector reaches the document root or its untargeted children and sets a layout property, with the rules and Tailwind utilities it can override, screen-level ones first. Keep the candidates and conflicts with at least one side in this partition, and record a conflict whose other side lives in a sibling partition under `## Cross-Partition Risk Attribution`. Leads, never verdicts
- `analyze_file.py --snapshot "$source_manifest" --find-usages --symbol <name>` to trace requested usages across the partition (and OPTIONALLY across all partitions for cross-partition risk attribution)

Do NOT use raw bash to do these jobs.
If source content or parser identity changed, report the required refresh to the
orchestrator; workers do not rewrite the shared manifest. File/class context and
import neighbours do not establish semantic completeness. A required source
outside the manifest target is an explicit scope gap.

## Method loads

Read named core sections by locating headings or fenced skeletons before bounded reads. On demand, add the router's conditional Method loads and their declared nested reads. Other references are pointers.

Read Phase 6 at full depth, including updates; comments and documentation verification require Phase 6.

| Resource | Sections | When |
|---|---|---|
| `<plugin-root>/skills/map-method/SKILL.md` | all | always |
| `<plugin-root>/skills/map-method/references/standalone.md` | all | always |
| `<plugin-root>/skills/map-method/references/reading.md` | section: Task views | always |
| `<plugin-root>/skills/map-method/references/evidence.md` | before: Maintained documentation | always |
| `<plugin-root>/skills/map-method/references/phases-5-6.md` | section: Phase 5: Pattern & Risk Detection; section: Red Flags to Identify; section: Partition worker; section: Team extensions | always |
| `<plugin-root>/skills/map-method/references/phases-5-6.md` | section: Phase 6: Documentation Health; section: Documentation Diagnosis Commands (Phase 6); section: Documentation diagnosis | not-lite |
| `<plugin-root>/skills/map-method/references/phases-5-6.md` | section: Comment Quality Commands (Antirez Standards); section: Comment Type Classification; section: Comment quality analysis | comments and not-lite |
| `<plugin-root>/skills/map-method/references/evidence.md` | from: Maintained documentation | documentation and not-lite |

## PHASE EXECUTION

Apply the shared phase procedures and skeletons to this partition. Bind phase output paths to `<run_dir>/partitions/<partition_name>`; keep `source_manifest` bound to the whole run. State updates in the units belong to the classic owner, never to a worker.
Use the Team mode rules for partition scope and declared extensions. Skip Phase 6 at lite depth.

## COMPLETION

Use the canonical Source reading section from evidence.md in each owned file.

When your owned files are written, report delivered: name their paths and nothing else. If you could not write them, report failed with the reason.
