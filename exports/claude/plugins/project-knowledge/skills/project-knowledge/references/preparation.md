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



## Existing analysis compatibility

Coordinators load `codebase-map:map-method` and apply `references/migration.md`
before root lookup or dispatch. Workers never migrate roots: use only its
`migrate_root.py resolve` for supplied bindings. Propagate returned paths.
Failed migration/resolution or a still-legacy `.codebase-xray` path blocks the
dependent operation; preserve archives and run IDs.

# Knowledge input preparation

1. Bind the project root, worktree, run and snapshot. Read durable project
   instructions before executing tooling; honor locally forbidden test commands.
2. Inventory existing README, AGENTS.md, CLAUDE.md, nested instruction files,
   docs, ADRs, product requirements, generated references and documentation config.
   Record owners and intended readers; preserve generated-file boundaries.
   For instruction work, use instructions-method's loading preflight to bind
   actual host/version/configuration, applicable scopes and imports. Distinguish
   present, configured and loaded files; preserve unresolved precedence or
   activation claims rather than certifying them from an inventory.
3. Read manifests, entry points and pertinent source. Use the named
   `codebase-map:map-method` to consume an identified analysis when supplied.
   Bind its exact run and revision; retain claim status and premise provenance.
   Resolve the supplied run directory under `.codebase-map/runs/`, verify its
   recorded target, depth and completed state, and compare its snapshot with the
   relevant current inputs. A latest mirror is not a substitute for that binding.
   Stale or incomplete evidence cannot authorize a factual correction.
   Follow the named owner's source-reading commands; do not resolve its helpers
   through this plugin's package root. Use `snapshot.py diff --verify` to check
   analysis changes with normalized line endings. After every such diff, always
   write or obtain a current manifest in the owned run using
   `snapshot.py write --reuse <previous-manifest>` before passing it to source
   readers, including `none` or LF/CRLF-only differences. Supported parent claims
   do not establish current source bytes. Preserve the parent snapshot and its
   evidence lineage, and pass the exact current
   `snapshot/manifest.json` to workers. Select symbols from its outline, read
   validated blocks, and expand to callers, callees, invariants, configuration
   and CSS/markup pertinent to each claim. An outline is discovery metadata;
   retained file/class context is not proof that omitted bodies are irrelevant.
   Record files/ranges actually read separately from inventory and runtime evidence.
4. Profile the audience from supplied intent and observable project signals.
   Record inference/confidence rather than inventing rationale. Ask only for an
   unresolved choice that materially changes the deliverable and cannot be derived.
5. Produce the file/audience plan: path, existing owner, readers, purpose,
   keep/update/create/merge candidate, source of facts, input report and writer.
   Prefer extending existing files. Create a new document only when the current
   owners cannot serve the requested purpose. Explicitly request authorization
   only for decisions outside the scope already given.
6. Set a proportional scope and budget before dispatch. Pass unchanged findings
   and metadata to audit methods; never turn a copied inference into a verified
   requirement. Writer and reviewer output paths belong to the owned run unless
   the plan authorizes specific durable documents.
