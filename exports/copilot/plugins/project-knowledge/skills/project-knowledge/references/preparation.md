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
   the exact snapshot path from `snapshot.py resolve <bound-run-dir>` to workers. Select symbols from its outline, read
   validated blocks, and expand to callers, callees, invariants, configuration
   and CSS/markup pertinent to each claim. An outline is discovery metadata;
   retained file/class context is not proof that omitted bodies are irrelevant.
   Record files/ranges actually read separately from inventory and runtime evidence.
   A supplied lifecycle receipt or context packet binds by digest: its fresh cards
   and verified source blocks evidence implemented behavior; stale or unread cards
   are leads; its gaps are documented limits.
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
