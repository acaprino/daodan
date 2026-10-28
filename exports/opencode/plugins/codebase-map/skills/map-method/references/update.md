<daodan_host_binding host="opencode">
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

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network fetch uses webfetch, network search uses
websearch, and a user question uses the registered question tool. shell takes command, optional workdir, timeout
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

# Incremental update

## Incremental Updates

`scripts/snapshot.py` mechanically prepares snapshot, change-set, carry and gate
inputs. Snapshots record file size/mtime/content hashes, symbol
spans/body hashes and git metadata. A method edit also changes its enclosing
class hash. Phase 1 in `references/phases-1-2.md` owns inventory categories,
file-level formats and exclusions.

`snapshot.py write --reuse` still walks the current perimeter and hashes every
inventoried file. Structural reuse requires matching content, recorded root/target,
helper/runtime fingerprint and effective parser profile; missing legacy identity
or a mismatch reparses. Reuse proves neither model reading nor understanding.

`changes.json`, from `snapshot.py diff`, compares the parent manifest with the
current worktree, classifies files/symbols, resolves the one-hop import blast radius
and finds every affected claim in parent phase files. Default checks trust equal
size/mtime; `--verify` hashes every file and is
required for evidence reuse. Changed helper/runtime fingerprints or parser profiles
invalidate cached structure. Recommendations are `incremental`, `none`, or `full`
with reasons: too much changed, no parent manifest, incomplete parent or changed
flags. The current tree is authoritative, never a Git range; git is metadata.
The blast radius never exceeds one hop.

Diff normalizes line endings even with `--verify`: `none` can support parent claims
despite LF/CRLF byte changes. Before source reading after a verified diff, write or
obtain a current owned manifest with `snapshot.py write --reuse <previous-manifest>`.
Readers check exact bytes. Preserve parent evidence, provenance and manifest;
never infer byte freshness from unchanged normalized claims.

`snapshot.py carry` copies parent phase files except the final report, renumbers
surviving-symbol citations and marks affected claims with
`<!-- xray:stale reason=... cites=... -->`. Unmarked claims remain inherited.
`snapshot.py check` checks every mode's declared delivery, stale markers and added
symbols. Only a complete publishing mode without stale markers may publish.
Stops leave later work pending, never skipped; inherited claims retain carry
provenance.

### Incremental depth (an update accepted at the checkpoint)

The entry already wrote the current snapshot, carried the accepted parent and
prepared delivery (`references/snapshot.md`). The analyst owns subsequent snapshot
refreshes; never repeat carry or prepare mode declarations. Phase numbering stays
unchanged.

1. **Run Phase 0 in full when selected**, overwriting carried `knowledge/`.
   Resume inherits confirmed earlier knowledge instead of rerunning it.
2. **Process selected produced phases 1 to 6 in order, only where work exists.**
   Re-derive each marked claim through this run's manifest/source blocks, then
   delete its marker. `symbol-removed` or `file-removed` retires both claim and
   marker. Write added-symbol claims assigned to this phase (`01` and `02` always; `03` to `06` at full
   depth). Leave unmarked claims unchanged. **A phase without markers or added
   symbols is inherited and never opened.** Missing parent files are produced
   obligations when their phase is selected.
3. **Read only `changes.json -> affected_files`.** Log an extra file required by
   a flow/contract under `## Extra reads` in `changes.md`, naming the claim that
   required it. **Re-derive a whole flow if it cites one affected symbol.** Flows
   cite every step; changed steps can affect later ones.
4. **Regenerate selected Phase 7** from the mode's phase files; never carry the
   parent's final report. A stop bounds this invocation only: later claims stay
   marked until resume, including claims in inherited files.
5. **Write `changes.md` completion sections:** `## Claims confirmed`,
   `## Claims revised` (old/new text, one row each), `## Claims retired`,
   `## Claims added`, `## Extra reads`. Report pending phases on an intentional
   stop.
6. **Check delivery** through the snapshot unit, report gaps and complete selected
   work. An invocation's passing gate does not authorize publication: only the
   entry applies `complete`, `may_publish` and requested-view gates and publishes
   the whole mirror.

Single-phase/docs-only requests are fresh partial runs. Resume preserves the
original mode/flags and parent; a changed mode requires a new run.
