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

# Incremental update

## Incremental Updates

A second Codebase Map of the same target rebuilds from nothing only if nobody asked what changed. The mechanism that asks is `scripts/snapshot.py`, and every part of it runs outside the model.

**The snapshot** (`snapshot/manifest.json`, written by every run) records each file with its size, mtime and content hash, and each symbol with its line span and a hash of its body, plus the git commit as metadata. A class span encloses its methods, so editing a method moves both hashes. Inventory categories, file-level formats and exclusions are defined in `references/phases-1-2.md`, Phase 1.

The manifest is also the single source-reading index. `snapshot.py write --reuse`
may reuse an unchanged file's parsed structure after checking its content hash,
the recorded root/target, helper/runtime fingerprint and effective parser profile.
It still walks the current perimeter and hashes every inventoried file. Missing
legacy fingerprints or a changed identity force parsing again. Reuse saves
repeated parsing; it does not establish that the model read or understood a file.

**The change set** (`changes.json`, written by `snapshot.py diff`) compares that manifest with the current worktree. Its default content check trusts equal size and mtime; `--verify` hashes every file and is required when binding source evidence for reuse. A changed helper/runtime fingerprint or parser profile invalidates cached structure. It classifies files and symbols, resolves the one-hop blast radius from the manifest's import edges, and scans the parent's phase files for every claim citing anything it touched. It recommends `incremental`, `full` (with reasons: too much changed, no parent manifest, an incomplete parent, flags differing from the parent's) or `none`.

Diff hashes normalize line endings to classify analysis changes, including with
`--verify`. A result of `none` can therefore retain the parent's analysis while
the source bytes changed from LF to CRLF. Before passing a manifest to source
readers after a verified diff, always write or obtain a current owned snapshot
with `snapshot.py write --reuse <previous-manifest>`. The reader checks exact
bytes. Keep the parent evidence and its provenance; do not modify its manifest
or infer byte freshness from unchanged normalized claims.

**The carry** (`snapshot.py carry`) copies the parent's phase files, except the final report, which is never carried and is always regenerated. It renumbers every citation whose symbol survived, and marks every affected claim with `<!-- xray:stale reason=... cites=... -->`. The model then reads only the affected files and re-derives only the marked claims.

**The gate** (`snapshot.py check`) checks every mode's declared delivery and the update's stale markers and added symbols. Only a complete publishing mode with no stale marker left may publish. A stop leaves later work pending, never skipped. Inherited claims retain their carry provenance.

Two things this deliberately does not do. It never uses a git range as the source of truth, because the tree a developer wants re-analyzed is usually dirty and sometimes not in a repository at all; git is metadata. And it never widens the blast radius past one hop, because the transitive closure of imports is, on most codebases, the whole tree.

### Incremental depth (an update accepted at the checkpoint)

The phases and their numbering are unchanged. What changes is that most claims are already on disk and only the affected ones are re-derived.

The entry already wrote the current snapshot, carried the accepted parent and
prepared delivery (`references/snapshot.md`). The analyst owns any subsequent
snapshot refresh; it never repeats carry or prepares new mode declarations.

1. **Phase 0 runs in full** when selected, overwriting carried `knowledge/`.
   A resume inherits confirmed earlier knowledge rather than rerunning it.
2. **Selected produced phases 1 to 6 run in order, only where work exists.** For
   each marked claim re-derive it through source blocks from this run's manifest,
   then delete its marker. A `symbol-removed` or `file-removed` marker retires the
   claim: delete both. Write claims for added symbols assigned to this phase
   (`01` and `02` always, `03` to `06` at full depth). **A phase with no marker
   and no added symbol is inherited and not opened at all.** Missing parent
   files are produced obligations; create them when their phase is selected.
3. **Read only affected files** from `changes.json -> affected_files`. A flow or
   contract requiring an extra file logs it under `## Extra reads` in `changes.md`,
   naming the claim that required it. **A flow citing one affected symbol is
   re-derived whole.** Flows cite every step; changed steps can affect later ones.
4. **Regenerate Phase 7** when selected, from the mode's phase files. Never
   carry the parent's final report. A stop bounds only this invocation; leave
   later claims marked until resume completes them, including in inherited files.
5. **Write the completion sections of `changes.md`**: `## Claims confirmed`,
   `## Claims revised` (old and new text, one row each), `## Claims retired`,
   `## Claims added`, `## Extra reads`. Report pending phases on an intentional stop.
6. **Check delivery** using the snapshot unit. Report its gaps and complete
   selected work. Passing an invocation's gate does not itself authorize
   publication; only the entry applies `complete`, `may_publish` and requested
   view gates and publishes the whole mirror.

Single-phase and docs-only requests are fresh partial runs. Resuming preserves
the original mode/flags and parent; a changed mode is a new run.
