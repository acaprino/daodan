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

# Snapshot

**Every run writes a snapshot.** Right after scope confirmation, before Phase 0:

```bash
python "<plugin-root>/skills/xray-method/scripts/snapshot.py" write \
  <target> --out $RUN_DIR/snapshot/manifest.json
```

The snapshot records the tree this run is about to read: every file with its size, mtime and content hash, every symbol with its span and a hash of its body, and the git commit as metadata. It is what makes this run a possible parent for the next one. A full run writes it too.

When a same-target candidate parent exists, add
`--reuse .codebase-xray/runs/<parent-id>/snapshot/manifest.json` to this write,
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
python "<plugin-root>/skills/xray-method/scripts/snapshot.py" scope <target>

python "<plugin-root>/skills/xray-method/scripts/snapshot.py" write <target> \
  --out <run-dir>/snapshot/manifest.json
```

`scope` prints the file count by set and by language, and the `scope` block the manifest will carry. `write` records the tree a run analyzed. Every run writes one, which is what makes it a possible parent.

For a subsequent snapshot of the same target, reuse the previous manifest:

```bash
python "<plugin-root>/skills/xray-method/scripts/snapshot.py" write <target> \
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
python "<plugin-root>/skills/xray-method/scripts/snapshot.py" diff \
  <parent-run-dir> <target> --out <run-dir> --verify [--threshold 0.4] [--flags '{"depth":"full"}']

# copy the parent's phase files, renumber citations, mark the stale claims
python "<plugin-root>/skills/xray-method/scripts/snapshot.py" carry <parent-run-dir> <run-dir>

# publication gate: no marker left, no undocumented new symbol
python "<plugin-root>/skills/xray-method/scripts/snapshot.py" check <run-dir>
```

`--verify` hashes every file instead of trusting size and mtime. Use it when
checking whether current inputs still support a bound analysis. `--threshold`
is the affected-file ratio above which a full run is recommended instead.
This check uses normalized line endings. Always follow it with a current
`snapshot.py write --reuse` before source-block reading, even when the result
is `none` or only line-ending bytes differ. Returning the supported parent
analysis without reading source does not require a new full analysis.
