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

# Scope Boundaries and Non-Goals

This file exists so that exclusions are written down rather than merely omitted. An omitted exclusion gets re-added by a well-meaning future pass; a written one has to be argued with.

## The goal is not a finding category

> **Structural simplification is the desired outcome of the audit, not a finding category.**

Without this rule, every D1 to D7 finding can be restated as a "structural simplification opportunity" that carries no new information, and the report doubles in length while saying the same things twice.

## Excluded dimensions and their owners

Five structural concerns are deliberately outside this plugin. Each has an owner that already covers it, and each has a permitted role here as supporting evidence.

| Excluded | Owner | Permitted role here |
|---|---|---|
| Dependency structure: cycles, missed inversions, depth | `senior-review:code-auditor` for coupling, `senior-review:chicken-egg-detector` for initialization cycles | A dependency may be cited as supporting evidence for D1 to D7. "This dependency is wrong" is never an autonomous finding here. |
| Responsibility cohesion inside a module | `senior-review:code-auditor` | Two modules owning the same policy is evidence of D2. "This class has too many responsibilities" is not ours. |
| API surface size and contract drift | `senior-review:api-contract-auditor`, `senior-review:cleanup-auditor` D3 for barrel and unused-export bloat | May appear incidentally inside a D7 remediation. Never a category. |
| Indirection cost | absorbed as lens L2 | Contributes to D7. "Too much indirection" never opens a finding alone. |
| Structural simplification | none, it is the goal | See the rule above. |

## Dedup with `senior-review:code-auditor`

Both agents run as dimensions of the same review, so the boundary is load-bearing rather than theoretical.

- **Inside one file** belongs to `code-auditor`: god functions, stringly-typed code, a leaky signature, an interface with one implementation, all judged on what the file under review shows on its own.
- **Across files** belongs here: this already exists elsewhere, this is the occurrence that justifies unifying, this fact has two owners, this layer is bypassed by callers that live somewhere else.

Do not re-flag a smell that is fully visible inside one file without reference to another site.

## Other neighbours

- **Dead code, unused exports, orphan assets**: `senior-review:cleanup-auditor`. **Workspace hygiene** (tracked build output, `.gitignore`, scratch directories, git state): `repo-hygiene:workspace-auditor`. A duplicated representation that is simply unused is a cleanup finding, not a D3.
- **Style and readability**: `clean-code:clean-code`. Renaming for clarity is not a structural finding.
- **Contract violations against a documented invariant**: `senior-review:logic-integrity-auditor`. That agent hunts code that *breaks* a documented rule. This one hunts a rule that has *two authoritative statements*. The two are complementary and neither subsumes the other.
- **Persistence semantics**: `senior-review:data-integrity-auditor`. A derivable column with no constraint backing it is theirs. The same column with four repair functions around it is D4 here. When both apply, report D4 and note the overlap in Cross-Reviewer Notes.

## This plugin does not

- Produce a refactoring plan. `Suggested direction` names the target layer or the move in one sentence.
- Edit any file other than its own report and, in global mode, its own concept index.
- Score the codebase. `senior-review:code-auditor` owns the Code Quality Score.
