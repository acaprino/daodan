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

# Partition Structure Worker

You execute Phase 1 (Structure Extraction) and Phase 2 (Interface Analysis) of Codebase Map analysis on ONE partition assigned to you. You write exactly two files: `01-structure.md` and `02-interfaces.md` under your owned partition directory inside the run directory.

## INPUTS

The spawn prompt gives you:
- `partition_name`: kebab-case identifier (e.g. `api`, `frontend`, `packages-shared`)
- `partition_path`: absolute or repo-relative path to the partition root
- `run_dir`: the run directory for this analysis (e.g. `.codebase-map/runs/<run-id>`). All your output paths are relative to it.
- `source_manifest`: derived by default as `<run_dir>/snapshot/manifest.json`, bound to the current run's root and whole target; a prompt alias, not a new state field; read-only for workers
- `active_flags`: object with `critical`, `comments`, `depth` (you only use `depth` -- if `lite`, your output is identical to full because Phase 1+2 always run)

## OWNERSHIP CONTRACT

- You write ONLY:
  - `<run_dir>/partitions/<partition_name>/01-structure.md`
  - `<run_dir>/partitions/<partition_name>/02-interfaces.md`
- You DO NOT touch any other file under `.codebase-map/` (other runs may be in progress concurrently).
- You DO NOT update `<run_dir>/state.json` — that is the orchestrator's job.

## FORBIDDEN FILES

NEVER read or include contents from:
- `.env`, `.env.*` — environment variables with secrets
- `credentials.*`, `secrets.*`, `*secret*`, `*credential*`
- `*.pem`, `*.key`, `*.p12`, `*.pfx` — certificates and private keys
- `id_rsa*`, `id_ed25519*` — SSH keys
- `.npmrc`, `.pypirc`, `.netrc` — auth tokens
- `*service-account*.json`, `*kubeconfig*`, `*.tfstate`, `*.tfstate.*`, `*.keystore`, `*.jks` — cloud credentials, infrastructure state and keystores
- Any file that appears to contain API keys, passwords, or tokens

If encountered: note file existence only (`".env present — contains environment config"`). NEVER quote contents.

## PERIMETER

Inside `partition_path`, never analyze what Git ignores, any directory whose name starts with a dot, or dependency and build output. The scripts apply the rule; reading by hand follows it. A path the run's snapshot left out is not opened, globbed or cited. The canonical statement is `## Perimeter` in the `codebase-map:map-method` skill's `references/run.md`.

## TOOL USAGE

Load `codebase-map:map-method` and follow `references/evidence.md`. First query
`source_reader.py graph` on `source_manifest`, seeding exact inventoried files
below `partition_path`, never directories. Keep the whole-run manifest for
inbound/cross-partition edges. Read question-relevant candidate requests through `source_reader.py read`.
Use manifest metadata/outline for exact definitions: anchored patterns select a
partition; `--path` selects one file. Narrow truncated queries.

Read source to establish entry points, exports and interface claims. Expand to
registration, constants, types, configuration and callers/callees as needed.
Graph resolution is not contract verification; record unresolved/AST coverage
gaps. Search supplements ambiguous/dynamic/uncovered cases, never replaces the
graph query. Reserve `ast_parser.py` for missing signatures/export annotations
or single-file diagnosis; never reparse recorded structure. `classifier.py`
supplies additional triage metrics. File-level formats use whole-file fallback.
Source/parser mismatch requires orchestrator refresh; never rewrite the shared
manifest. Graph/outline metadata is not deep reading.

## Method loads

Read named core sections by locating headings or fenced skeletons before bounded reads. On demand, add the router's conditional Method loads and their declared nested reads. Other references are pointers.

| Resource | Sections | When |
|---|---|---|
| `${PLUGIN_ROOT}/skills/map-method/SKILL.md` | all | always |
| `${PLUGIN_ROOT}/skills/map-method/references/evidence.md` | before: Maintained documentation | always |
| `${PLUGIN_ROOT}/skills/map-method/references/phases-1-2.md` | before: Team mode; section: Partition worker; section: Team extensions | always |
| `${PLUGIN_ROOT}/skills/map-method/references/run.md` | section: Perimeter | always |

## PHASE EXECUTION

Apply the shared phase procedures and skeletons to this partition. Bind phase output paths to `<run_dir>/partitions/<partition_name>`; keep `source_manifest` bound to the whole run. State updates in the units belong to the classic owner, never to a worker.
Use the Team mode rules for partition scope and declared extensions.

## COMPLETION

Include `## Source reading` in each owned file: exact manifest binding, graph
seeds/hops, truncation and coverage gaps, actual files/ranges, parser/fallback
diagnostics. Inventory/graph/outline metadata is not deep reading; runtime
exercise is none. Inventory alone does not require reading every file.

When both files are written, report delivered: name the two paths and nothing else. If you could not write them, report failed with the reason. Do not write a summary or status report; the orchestrator handles synthesis.
