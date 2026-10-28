<daodan_host_binding host="codex">
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

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. Network search and network fetch
use the runtime's registered web search tool when the Codex configuration enables
it. A user question uses the runtime's registered question tool when one exists;
otherwise ask it in the reply and wait for the answer. In particular, a shell example's
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

# Supply-chain signals: verifiable only

Supply-chain review deals in signals, not verdicts. Every finding in this dimension is a pointer that a human must verify, and is phrased that way ("signal, verify by ..."). Two bans up front:

- **No toy typosquat detection.** Computing name distance against a hardcoded list of famous packages is theater: real typosquat detection needs registry-scale tooling. If a name looks suspicious, verify it directly against the registry (publish date, download counts, linked repository, maintainer history) instead of scoring string similarity. If the user wants systematic typosquat screening, point them at dedicated tooling rather than improvising one.
- **No behavioral claims without reading code.** "Package X exfiltrates data" is never a finding unless the flagged code was actually read. The signal is "declares a postinstall script fetching a remote URL"; the verdict belongs to the human who inspects it.

## Signal catalog

### 1. Lifecycle / install scripts

Packages executing code at install time are the highest-leverage attack surface.

- npm: list dependencies declaring `preinstall` / `install` / `postinstall`. On recent npm, `npm query ":attr(scripts, [postinstall])"` does this; otherwise grep the installed packages' `package.json` files.
- Python: `setup.py`-based sdists execute at build/install time by design; flag only unusual constructs (network fetches, subprocess calls in `setup.py`).
- Signal escalates when a **diff** introduces a new install script in a patch/minor update, or an existing script starts fetching remote content. Verification: read the script.

### 2. Registry metadata

Query the registry, report what it returns (TOOL-REPORTED):

- Package age and publish history (`npm view <pkg> time --json`, PyPI JSON API, crates.io API). Signals: brand-new package pulled in as a new transitive dependency; long-dormant package that suddenly published right before your resolved version.
- Maintainer roster (`npm view <pkg> maintainers`). Signal: maintainer change shortly before the resolved release. Verification: the project's release notes, repository transfer announcements.
- Repository link present and pointing at the claimed source. Signal when absent or mismatched.

### 3. Lockfile integrity

Review the lockfile (and its diff, when auditing a change):

- Resolved URLs pointing off the default registry: `git+http(s)` deps, tarball URLs on unknown hosts, registry mirrors nobody configured deliberately.
- Integrity hash changes without a version change in the diff.
- Dependencies resolved from `file:` or workspace paths that are not part of the repo.

Verification: explain each anomaly from the project's own config (`.npmrc`, mirror settings) or flag it.

### 4. Dependency confusion

For organizations with internal packages: check whether internal package names (scoped or not) also exist on the public registry, and whether the resolver could prefer the public one (missing scope registry pinning in `.npmrc` / `pip.conf` index configuration). Signal: public package shadowing an internal name, especially with an inflated version number. Verification: resolver config plus a dry-run install log showing the source registry per package.

### 5. Advisory and provenance databases

Primary sources to query, never to paraphrase from memory:

- OSV.dev (via `osv-scanner` or the HTTP API) for known malicious-package advisories (`MAL-` ids) alongside vulnerabilities.
- deps.dev API for cross-registry metadata (dependents, OpenSSF Scorecard results) when reachable.
- npm provenance attestations (`npm view <pkg> dist.attestations`) where the ecosystem supports them: presence is a positive signal, absence is neutral (most packages lack them), a failing verification is a finding.

## Reporting rule

Each signal reports: what was observed (TOOL-REPORTED), why it is a signal (one sentence), and the exact verification step for a human. Signals never aggregate into an invented "supply-chain risk score".
