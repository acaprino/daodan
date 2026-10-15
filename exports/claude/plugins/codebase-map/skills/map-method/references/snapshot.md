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

# Snapshot

**Every run writes a snapshot.** After scope confirmation and before Phase 0,
the coordinator writes the initial current manifest with the commands below.
Classic snapshot ownership then transfers to the isolated analyst for required
refreshes. Team snapshot ownership remains with the coordinator; partition
workers and the mapper report refresh gaps rather than changing its manifest.

The snapshot records the tree this run is about to read: every file with its size, mtime and content hash, every symbol with its span and a hash of its body, and the git commit as metadata. It is what makes this run a possible parent for the next one. A full run writes it too.

When a same-target candidate parent exists, add
`--reuse .codebase-map/runs/<parent-id>/snapshot/manifest.json` to this write,
including when full analysis was selected. Reuse checks current bytes and parser
identity before retaining structure; it still scans and hashes the inventory.
Preserve the parent manifest.
For every path that reads source, perform this current write after the verified
diff even when it reports `none` or only LF/CRLF bytes changed. That result can
support the parent's claims without making its recorded source bytes current.

Immediately copy the manifest's own `git` field into the run's state. Its parent,
base snapshot time and incremental counts already carry preflight's real values.
Never infer current source bytes from a normalized diff or change a parent snapshot.

## Incremental Update Commands

### 14. Count the scope, then write a structural snapshot

```bash
# what a run would analyze, and what its perimeter leaves out; parses nothing
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" scope <target>

python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" write <target> \
  --out <run-dir>/snapshot/manifest.json
```

`scope` prints the file count by set and by language, and the `scope` block the manifest will carry. `write` records the tree a run analyzed. Every run writes one, which is what makes it a possible parent.

For a subsequent snapshot of the same target, reuse the previous manifest:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" write <target> \
  --out <run-dir>/snapshot/manifest.json \
  --reuse <parent-run-dir>/snapshot/manifest.json
```

Write the current manifest in the owned run; preserve the parent snapshot.
`--reuse` verifies bytes even when size and mtime match. A fingerprint, root or
target mismatch rebuilds structure safely; malformed reuse input fails without
replacing the output. Bind the recorded root, target and run before reuse.

### 15. Diff and carry an update

```bash
# what changed since a parent run, and which of its claims that affects
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" diff \
  <parent-run-dir> <target> --out <run-dir> --verify [--threshold 0.4] [--flags '{"depth":"full"}']

# copy the parent's phase files, renumber citations, mark the stale claims
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" carry <parent-run-dir> <run-dir>

```

`--verify` hashes every file instead of trusting size and mtime. Use it when
checking whether current inputs still support a bound analysis. `--threshold`
is the affected-file ratio above which a full run is recommended instead.
This check uses normalized line endings. Always follow it with a current
`snapshot.py write --reuse` before source-block reading, even when the result
is `none` or only line-ending bytes differ. Returning the supported parent
analysis without reading source does not require a new full analysis.

The coordinator carries an accepted parent after the initial current snapshot
and before delivery preparation. `carry.json` records source/copied hashes and
parent provenance. A composed caller's bounded classic child sets
`state.json -> parent_phases: [1,2,3,4]` to carry only those canonical files from
a bound partial or team parent. Classic children never carry a team's `08`.

### 16. Prepare, check and publish every mode

```bash
# after initializing state, register or refresh only this run's active entry
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" register $RUN_DIR

# effective mode/flags are in state.json; add applicable invocation controls
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" prepare $RUN_DIR \
  [--phase N] [--stop-after N]

# continue the named interrupted run, preserving its mode and flags
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" prepare $RUN_DIR \
  --resume-from [N] --run-name <exact-id> [--mode classic|team] [--flags '<JSON>']

# the single native-delivery gate for full, lite, updates and partial modes
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" check $RUN_DIR --json

# only the coordinator calls this after native and requested-view gates
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" publish $RUN_DIR

# on cancellation, partial delivery or failure; preserves the latest pointer
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/snapshot.py" unregister $RUN_DIR
```

`prepare` writes `state.json -> delivery` with schema 1, immutable mode/flags,
artifact declarations and invocation controls (`run_phases`, `stop_after`,
`resume_from`). Each artifact is produced, inherited with parent/carry or same-run
provenance, or skipped with a reason. Knowledge requires both Phase 0 files.
The helper owns the mode table; callers do not invent expected files.
Only the coordinator prepares declarations. Workers read them and write results.

`--phase N` accepts 1 through 6 and selects Phase 0 plus N; 7 is refused.
Docs-only selects 0 and 6. Both stay in their run. `--stop-after N` accepts
1 through 6, conflicts with docs/single-phase modes and leaves later work pending.
It is not a mode flag. Resume requires the exact run name, verifies earlier
artifacts/current source and keeps the same mode/flags. It drops the stop and
starts at N (1 through 7), or the first incomplete produced phase when omitted.
Missing inherited provenance never silently becomes fresh work.

`check --json` reports `missing`, `empty`, `unexpected`, `invalid_inherited`,
`stale`, `undocumented_added`, `not_yet_produced`, `first_incomplete_phase`,
`complete`, `may_publish` and errors. Exit 0 means this invocation delivered,
including an intentional stop; it does not mean publishable. Exit 1 reports
delivery gaps; exit 2 reports an invalid binding. Skipped and verified inherited
artifacts are never missing produced work. On a stop, later artifacts remain
`not_yet_produced` and stale markers there are pending, not completed.

Only a complete publishing mode with no remaining stale marker may publish.
Team `08-interconnect-map.md` is legitimate when declared; its absence is a gap
unless the mode skipped it. With comments and full-depth Phase 6, classic requires
`comment_health.md`; team requires each partition's Comment Quality section in
`06-documentation.md`. The entry also verifies requested human views.
`publish` rechecks delivery and replaces all known mirror phase files plus state
with locked rollback protection, updates only its registry entry/latest pointer,
and preserves run archives and unrelated root files. Never hand-copy a partial
set over a previous mirror.

## Prerequisites

The scripts require Python >= 3.10 and work **out of the box** with just the stdlib. Tree-sitter is optional and improves accuracy for Java / JavaScript / TypeScript / Rust:

```bash
# Optional: install for higher-fidelity parsing
pip install -r "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/requirements.txt"
# or
uv pip install -r "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/requirements.txt"
```

What changes when tree-sitter is installed:

- **Java**: nested classes, generic type parameters, annotations, multi-line declarations parsed correctly. Without it, the regex fallback still finds top-level classes, methods, imports, and constants.
- **JavaScript / TypeScript**: arrow functions in object/class properties, decorators, template literals, JSX elements parsed correctly. Without it, the regex fallback handles top-level declarations, ES6 `import`/`export`, and CommonJS `require`.
- **Rust**: lifetimes, generic bounds (`where` clauses), impl blocks with trait bounds, attribute macros parsed correctly. Without it, the regex fallback still finds top-level fns, structs/enums/traits/impls/mods, use declarations, and UPPER_CASE constants.
- **Java / JavaScript / TypeScript / Rust**: every symbol carries the parser's reported end line, preserving its definition's line endpoints. A regex fallback gives start lines only, and the snapshot then ends each symbol where the next one begins.

Exact end lines remain line-granular. Minified or shared-line definitions can
require whole-file reading even with exact parser endpoints, because a line can
also hold another definition, class declaration or static field.
- **Python / SQL / PL-SQL / CSS**: no change. Python always uses stdlib `ast`; SQL/PL-SQL always use the regex DDL extractor; CSS, SCSS and LESS always use the stylesheet tokenizer.

The active parser is reported in `ParseResult.notes` and in the CLI output: `parser=stdlib-ast`, `parser=tree-sitter`, `parser=regex-fallback`, or `parser=stylesheet`. Installed is not the same as working: when the pack is installed but hands back no parser (a grammar download that failed, a version mismatch), the regex fallback runs and the notes add `tree-sitter unavailable: <error>`.

### Capabilities

**Mechanical Analysis (Scripts):**
- Extract code structure (classes, functions, imports)
- Map dependencies (internal/external)
- Find symbol usages across the codebase
- Classify files by criticality

**Semantic Analysis:**
- Recognize architectural and design patterns
- Identify red flags and anti-patterns
- Trace data and control flows
- Document contracts and invariants
- Assess quality and maintainability

**Documentation Diagnosis:**
- Inspect documentation drift and broken links (Phase 6)
- Report stale indexes and references
- Analyze comment quality and propose changes; analysis does not apply them

**Use this skill when:**
- Analyzing a codebase you're unfamiliar with
- Generating documentation that explains WHY, not just WHAT
- Identifying architectural patterns and anti-patterns
- Building technical ground truth before a code review
- Onboarding to a new project
