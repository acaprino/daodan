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
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
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

# Deepen an area

Cards record a symbol's purpose, contracts, effects and failures in the analysis
root's `cards.sqlite`. Stored digests determine freshness against each snapshot.
Deepen only the requested area; reuse complete fresh cards. `semantic-map.md`
projects this evidence, exposing unread, stale and incomplete cards for this method.

## Coordinator

1. Bind the latest complete run; verify the area with `snapshot.py diff --verify`.
   Update stale paths incrementally first. Without analysis, create the target's
   base snapshot; never default to full analysis.
2. Resolve the area. A task's area is the symbols it names and their one-hop
   callers and callees from `snapshot.py edit-impact`; an area given as a path
   is every symbol under it; no area is the whole target.
3. Run `semantic_map.py MANIFEST --path AREA`. Read its JSON `reading_requests`,
   including incomplete fresh cards. Nothing listed: dispatch nothing.
4. Dispatch `codebase-map:map-analyst` with mode `cards`, the manifest, the
   list and an expected delivery, in batches of at most 100 symbols.
5. Regenerate the view. Verify every listed symbol has a fresh, complete card
   or the analyst's reason for remaining gaps.
6. Keep the view's provenance beside it; preserve finished phase reports.

## Analyst in cards mode

For each listed symbol read its verified source and its neighbours through
`snapshot.py edit-impact MANIFEST --target SYMBOL`; a stale card is a lead,
never the answer. Reuse a fresh card's fields and fill its gaps; submit the complete
merged card because upsert replaces its payload. Write one card per symbol:

- `purpose`: one or two sentences on what it is for.
- `preconditions`, `postconditions`, `invariants`: what callers must hold and
  what it guarantees, each from the source.
- `side_effects`: writes, I/O, network, global state, time.
- `failure_modes`: what it raises or returns on failure, and what it leaves
  behind.
- `confidence`: `high` when read in full with its callers, `medium` when a
  neighbour was unresolved, `low` otherwise; `notes` for anything unverified.

Write JSON batches through `snapshot.py meta-upsert MANIFEST --input -`.
Deliver cards written, absent symbols and refused cards with reasons, plus
observed LLM tokens or `unavailable`; never estimate them as measured.
Only the card store is writable in cards mode; source and finished runs stay untouched.
