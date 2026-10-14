> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

**Every run writes a snapshot.** Right after scope confirmation, before Phase 0:

```bash
python "<plugin-root>/skills/map-method/scripts/snapshot.py" write \
  <target> --out $RUN_DIR/snapshot/manifest.json
```

The snapshot records the tree this run is about to read: every file with its size, mtime and content hash, every symbol with its span and a hash of its body, and the git commit as metadata. It is what makes this run a possible parent for the next one. A full run writes it too.

When a same-target candidate parent exists, add
`--reuse .codebase-map/runs/<parent-id>/snapshot/manifest.json` to this write,
including when full analysis was selected. Reuse checks current bytes and parser
identity before retaining structure; it still scans and hashes the inventory.
Preserve the parent manifest.
For every path that reads source, perform this current write after the verified
diff even when it reports `none` or only LF/CRLF bytes changed. That result can
support the parent's claims without making its recorded source bytes current.

Immediately after, copy the manifest's own `git` field into `$RUN_DIR/state.json`'s `git` field. This is the only new `state.json` field this step fills: `parent_run`, `base_snapshot_created_at` and `incremental` were already written with their real values when `state.json` was created, in pre-flight step 2 of the `analyze` workflow, because its step 1b change set already existed by then.

## Incremental Update Commands

### 14. Count the scope, then write a structural snapshot

```bash
# what a run would analyze, and what its perimeter leaves out; parses nothing
python "<plugin-root>/skills/map-method/scripts/snapshot.py" scope <target>

python "<plugin-root>/skills/map-method/scripts/snapshot.py" write <target> \
  --out <run-dir>/snapshot/manifest.json
```

`scope` prints the file count by set and by language, and the `scope` block the manifest will carry. `write` records the tree a run analyzed. Every run writes one, which is what makes it a possible parent.

For a subsequent snapshot of the same target, reuse the previous manifest:

```bash
python "<plugin-root>/skills/map-method/scripts/snapshot.py" write <target> \
  --out <run-dir>/snapshot/manifest.json \
  --reuse <parent-run-dir>/snapshot/manifest.json
```

Write the current manifest in the owned run; preserve the parent snapshot.
`--reuse` verifies bytes even when size and mtime match. A fingerprint, root or
target mismatch rebuilds structure safely; malformed reuse input fails without
replacing the output. Bind the recorded root, target and run before reuse.

### 15. Diff, carry and check an update

```bash
# what changed since a parent run, and which of its claims that affects
python "<plugin-root>/skills/map-method/scripts/snapshot.py" diff \
  <parent-run-dir> <target> --out <run-dir> --verify [--threshold 0.4] [--flags '{"depth":"full"}']

# copy the parent's phase files, renumber citations, mark the stale claims
python "<plugin-root>/skills/map-method/scripts/snapshot.py" carry <parent-run-dir> <run-dir>

# publication gate: no marker left, no undocumented new symbol
python "<plugin-root>/skills/map-method/scripts/snapshot.py" check <run-dir>
```

`--verify` hashes every file instead of trusting size and mtime. Use it when
checking whether current inputs still support a bound analysis. `--threshold`
is the affected-file ratio above which a full run is recommended instead.
This check uses normalized line endings. Always follow it with a current
`snapshot.py write --reuse` before source-block reading, even when the result
is `none` or only line-ending bytes differ. Returning the supported parent
analysis without reading source does not require a new full analysis.

## Prerequisites

The scripts require Python >= 3.10 and work **out of the box** with just the stdlib. Tree-sitter is optional and improves accuracy for Java / JavaScript / TypeScript / Rust:

```bash
# Optional: install for higher-fidelity parsing
pip install -r "<plugin-root>/skills/map-method/scripts/requirements.txt"
# or
uv pip install -r "<plugin-root>/skills/map-method/scripts/requirements.txt"
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
