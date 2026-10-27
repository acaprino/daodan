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

# Locating code for a change

The measured loop for finding the code a request is about, before any edit.
On 23 private tasks it solved as many as any other access path and cost the
least per solved task (map plus lexical search 21, hybrid search 19, a pre-built
packet 19; the differences are within noise), and search results are leads:
`codebase_map_read` verifies the bytes you act on.

## The loop

1. **Names first.** Pull every concrete name out of the request: identifiers,
   file names, error text, traceback frames, the domain nouns it uses. Keep
   them as one list; the failures of the measurement were half-read requests.
2. **Search by name group.** `codebase_map_search(run_id, query)`; without an
   MCP server, `snapshot.py search MANIFEST --query Q`. An exact symbol
   (`path::Name` or a bare identifier) and a traceback frame rank first; other
   words match by subtoken, so `InvoiceTotal` finds `invoice_total`. One query
   per name group, not the whole request pasted at once. A `gaps` entry naming
   `codebase_map_index` means the index is missing, stale or failed: run that
   (with `break_lock` after a crashed build), then search again.
3. **Expand only what is pertinent.** `codebase_map_outline` on the hit's file
   shows its other symbols; `codebase_map_graph` with `hops=1` shows callers and
   callees. Stop at one hop unless a hit is a thin wrapper.
4. **Read by symbol.** `codebase_map_read` with the entity ids you keep; a whole
   file only when it is short. Every hit you read is verified against the
   snapshot; a file edited since the snapshot makes the read fail with
   "source changed; refresh the manifest", which the search does not detect.
5. **Bound the edit.** `codebase_map_edit_impact` on the symbols you will change
   lists callers, tests and obligations.
6. **Reproduce, then fix.** Before the first edit, write one test that fails for
   the reason the request states. Edit, run the tests, stop.

## Budgets from the measurement

- About 6 searches and 10 symbol reads per task; more usually means the names
  came from the wrong half of the request.
- An empty search is reworded once (synonym, the file name, a caller's name);
  the second time, reread the request.
- `grep` over the tree only when no map exists, or to confirm a string literal.
- A search costs no model tokens; its results do enter the context, so keep
  `limit` at 20 and read the top hits rather than widening the list.

## Perimeter

Measured on Python projects, a strong model and precise requests, one
replicate. Vague requests, weak models, large repositories and other languages
are unmeasured; the index covers every parsed language, since subtokens are
language-agnostic. One hypothesis, untested: listing every requirement of the
request before the first edit, and reproducing each, since 9 of the 10 measured
failures had the right file open and did half of the request.
