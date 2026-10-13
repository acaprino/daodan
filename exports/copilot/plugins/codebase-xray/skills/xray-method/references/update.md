> `${PLUGIN_ROOT}` is this plugin's install directory, the one that holds its `plugin.json`. If the host has not expanded it, resolve it from where this file was loaded.

<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

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

A second X-ray of the same target rebuilds from nothing only if nobody asked what changed. The mechanism that asks is `scripts/snapshot.py`, and every part of it runs outside the model.

**The snapshot** (`snapshot/manifest.json`, written by every run) records each file with its size, mtime and content hash, and each symbol with its line span and a hash of its body, plus the git commit as metadata. A class span encloses its methods, so editing a method moves both hashes. Three sets of files enter it: source in the parsed languages, with symbols, where CSS, SCSS and LESS carry one symbol per applied rule, except a minified stylesheet (any line over 10,000 characters), which stays file-level; configuration and documentation (`.json`, `.yaml`, `.toml`, `.md` and their kin), as file-level entries with no symbols; and presentation files no adapter parses (`.html`, `.htm`, `.vue`, `.svelte`, indented `.sass`), also file-level, because markup decides whether a screen renders, scrolls and can be completed, and a run that drops it can neither cite it nor notice that it changed. Any other extension is absent from the manifest and from every count derived from it, and the final report says so. Forbidden files never enter it, not even as a hash. Nor does anything outside the perimeter (see `## Perimeter` in `references/run.md`): what Git ignores, and whatever sits under a directory whose name starts with a dot. The manifest's `scope` block records what that rule left out.

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

**The gate** (`snapshot.py check`) fails if any marker survives or any added symbol went undocumented. An incremental run does not publish until it passes. That gate is the whole reason an incremental result can be trusted the way a full one is: the claims it kept were not re-checked, so what it did not carry must be provably finished.

Two things this deliberately does not do. It never uses a git range as the source of truth, because the tree a developer wants re-analyzed is usually dirty and sometimes not in a repository at all; git is metadata. And it never widens the blast radius past one hop, because the transitive closure of imports is, on most codebases, the whole tree.

### Incremental depth (an update accepted at the checkpoint)

The phases and their numbering are unchanged. What changes is that most claims are already on disk and only the affected ones are re-derived.

1. **Write the snapshot** for this run, as `references/snapshot.md` says.

2. **Carry the parent forward**, mechanically:

   ```bash
   python "${PLUGIN_ROOT}/skills/xray-method/scripts/snapshot.py" carry \
     .codebase-xray/runs/<parent-id> $RUN_DIR
   ```

   This copies the parent's `01` to `06` and `knowledge/` into the run, renumbers every carried `file:line` citation whose symbol survived the edit, and inserts an `<!-- xray:stale reason=... cites=... -->` marker above every claim the change set affects. Phase 7 is never carried: it is regenerated.

3. **Phase 0 runs in full**, exactly as in a fresh run, overwriting the carried `knowledge/`. It is the cheap discovery pass and what it finds shapes what the re-derivation looks for.

4. **Phases 1 to 6, in order, only where work exists.** For each phase file: open it, and for every `xray:stale` marker re-derive that claim through source blocks from this run's manifest, then delete the marker. A marker whose reason is `symbol-removed` or `file-removed` means the claim is retired: delete the claim with the marker. Then write claims for the symbols listed under `## Added symbols` in `changes.md` that belong to this phase file (`01` and `02` always, `03` to `06` at full depth). **A phase file with no marker and no added symbol is not opened at all.**

5. **Read only the affected files.** `changes.json` lists them under `affected_files`. When re-deriving a flow or a contract genuinely requires a file outside that set, read it and log it under `## Extra reads` in `changes.md`, naming the claim that needed it. That log is the evidence a future threshold gets tuned from.

6. **A flow that cites even one affected symbol is re-derived whole.** Flows cite every step, and a step that changed can change the steps after it.

7. **Phase 7 is regenerated** from the phase files, as in a full run.

8. **Gate publication:**

   ```bash
   python "${PLUGIN_ROOT}/skills/xray-method/scripts/snapshot.py" check $RUN_DIR
   ```

   Exit `0` means clean: proceed to publish. Exit `1` means a claim is still marked stale or an added symbol was never documented: do not publish, report what the check named, and finish the work. Exit `2` means `changes.json` is missing, which should not happen this late in an incremental run: do not publish, and treat it as a bug in the run rather than in the code under analysis. This gate is what makes an incremental run worth trusting.

9. **Write the completion sections of `changes.md`**: `## Claims confirmed`, `## Claims revised` (old and new text, one row each), `## Claims retired`, `## Claims added`, `## Extra reads`.

10. **Publish** exactly as a full run does.

`--phase N` and `--docs-only` are full-run flags. They change this run's flags, so the change set already recommends a full run.
