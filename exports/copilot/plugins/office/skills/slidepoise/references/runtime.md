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

# External SlidePoise runtime

This is a locally authored integration, not a vendored SlidePoise distribution.
Upstream source: https://github.com/henryhyw/slidepoise. License: MIT. The inspected
integration reference is version `0.8.2`, revision
`4250ba14d5d673a3215e7707b5d52f67cdf1154e`. A future upstream revision needs its
interfaces and reconstruction behavior inspected before changing this pin.

## Prerequisites and installation

Use Python 3.10+, Node.js 18+ and npm 9+. Editable reconstruction needs the upstream
Python packages (including OpenCV) and its Node/PptxGenJS runtime. Visual review
needs a compatible PPTX renderer; upstream setup supports LibreOffice and Poppler.
Image generation, image inspection and required fonts come from the current host.

When runtime installation is within the user's authorized task, run:

```text
npx --yes github:henryhyw/slidepoise#4250ba14d5d673a3215e7707b5d52f67cdf1154e setup --skip-skill
```

`--skip-skill` installs the framework without adding another registered skill
beside Daodan's integration. The framework includes its own skill resources; the
bridge discovers them through `framework.paths.SKILL_ROOT`. The pin fixes the
upstream source, while upstream's dependency ranges still govern its Python and
Node packages. Record the installed versions for reproducibility.

Setup writes under `SLIDEPOISE_HOME` when set, otherwise `~/.slidepoise`, and can
install missing preview applications through the system package manager. Read the
installer's output and respect the host's permissions for system installation.
Use `--skip-preview` only when a compatible renderer already exists or the
user accepts an explicitly unreviewed output. Check `doctor` after setup; skipped
preview setup is not evidence of visual verification.

The bridge never downloads, installs, registers skills or changes host settings.
It selects `<home>/python/Scripts/python.exe` on Windows and
`<home>/python/bin/python` on other systems. A `--home` override also sets the
child runtime's `SLIDEPOISE_HOME`. It validates the discovered external skill and
reconstruction entry point before forwarding commands.

## Host portability

Daodan ships this integration on Claude, Codex, Copilot, Pi and OpenCode. All five
must be able to execute the external local runtime, read its resources and inspect
images. The upstream installer registers skills only for Codex, Claude and Qoder;
the Daodan bridge avoids relying on that host-specific registration.

Codex is upstream's primary tested presentation environment. The availability of
Daodan packages on other hosts is compiled support, not evidence of a completed
presentation on those hosts. Discover capabilities in the active session and
report a missing runtime, generator, font or renderer precisely.

Use the upstream Console or session panel only when useful and supported by the
current host. Use the host's normal browser/file opening interface. Do not rely
on a Codex-only notification connection to resume work on other hosts. Apply the
upstream runtime's durable session-change checkpoints between operations.

## Runtime commands

Use bridge `cli` for `doctor`, `profile list`, `profile show`, profile selection
and other supported framework commands. Use bridge `script` for upstream skill
scripts, including `slidepoise_runtime.py`. Read the installed method and the
specific command's help before constructing its input contracts. Preserve
external exit codes and report objective command failures with their evidence.

Keep all generated slide evidence within the presentation's work directory. Keep
user-owned Profiles and Library Sets in the external framework home. Changes to
one presentation must not silently change the shared Profile for future work.
