---
description: 'Runs `web-ext lint` plus static checks for forbidden APIs, permission bloat, remote-hosted code and Manifest V3 migration issues. TRIGGER WHEN: linting, validating or checking a Firefox extension, before an AMO submission or a git push on an extension project.'
---

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

# firefox-lint

<!-- Generated by the Daodan compiler for opencode. Edit the kernel, never this file. -->

## Execution harness

Selected topology: **parallel-subagents**, with role delivery by **named-agent**, and declared
isolation **required**.

Dispatch one worker per entry in the plan below with the `subagent` tool. Name the role as the
agent, using the qualified identity in the bindings below, and give it a short `description` and the full
task as `prompt`. Each agent runs in a fresh child session, so isolation is native here.
For a local role the qualified form is `agent: "browser-extensions:<role>"`; external roles
use their owner's prefix from the bindings, never the coordinator's prefix.

Under `parallel-subagents`, dispatch every worker of one phase with `background: true`, then wait
for every completion notice before the phase closes; do not poll. Under `serial-isolated`, dispatch
them one at a time in the foreground.

Every role below is registered as an agent by this package. A `subagent` call that answers with an
unknown agent means the install is broken: stop and report it, never continue with a shorter
report.

Coordinator completion ownership: keep the method's owned run and delivery ledger,
including each expected worker, attempt, report path and required check evidence.
Validate report artifacts before recording delivered. An empty final message or
worker stop remains missing delivery: inspect or resume when permitted, otherwise
record failed with the uncovered scope. Follow the declared join and phase gates;
a recorded failure is accounted for, never converted into a successful delivery.
Continue authorized work and recovery until the requested result and its checks
exist or a concrete blocker is recorded. Preserve the exclusive final report owner
and the ledger schema; a tool exit or a promise cannot satisfy completion.

Harness obligations, none of them optional:

- Every dispatched worker runs in its own context and reads only coordinator-declared inputs.
  Independent reviewers never read peer results before their own delivery.
- Follow the dispatch plan below in phase order. A phase starts only after every phase it needs has
  closed, and a phase closes only when every worker it dispatched is recorded `delivered` or
  `failed`. A worker reports delivered or failed in its final message; there is no shared task
  list, so the coordinator keeps that record itself.
- Dispatch only roles from this set, as the phase graph or loaded method requires: `firefox-extension-dev-agent`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `scope`: runs in the orchestrating context; produces `artifact:scope`.
2. `review`: one `firefox-extension-dev-agent` in an isolated context; needs `scope`; consumes `artifact:scope`; produces `artifact:firefox-lint-report`.

Role bindings:

- `firefox-extension-dev-agent`: dispatch the installed `browser-extensions:firefox-extension-dev-agent` agent by its qualified identity.

The phase graph and the record schemas are in `contracts/firefox-lint.workflow.toml`.

## Method

# Firefox Extension Lint

Comprehensive pre-publish lint for a Firefox WebExtension.

## CRITICAL RULES

1. **Run `web-ext lint` first** -- Mozilla's official linter catches AMO-blocking issues (remote code, missing icons, invalid manifest).
2. **Then scan source for anti-patterns** that `web-ext lint` misses: eval/Function, remote script injection, wildcards in host_permissions, stored tokens in non-session storage.
3. **Report results grouped by severity** matching AMO's own review criteria.

## Procedure

### 1. Run web-ext lint

```bash
cd "$TARGET"
npx web-ext lint --pretty
```

Parse the output. If `--json` flag set, use `--output=json` and parse JSON.

### 2. Static checks beyond web-ext lint

Run these greps / AST checks against `src/`:

**Forbidden / high-risk APIs (AMO review often rejects)**
- `eval(`, `new Function(` -- AMO blocks unless justified
- `document.write(` -- CSP violation
- `innerHTML =` with user-controlled input -- XSS risk
- Remote script loading: `<script src="https://...">` in extension pages
- `browser.tabs.executeScript` with dynamic code strings (MV2)

**Permission bloat**
- `<all_urls>` in `host_permissions` -- AMO reviewers ask "why?"
- `"tabs"` permission without reading tab URL/title/favIcon (often over-requested)
- `"storage"` permission without any `browser.storage.*` call (dead permission)
- `"webNavigation"` without `onBeforeNavigate` / `onCompleted` listeners

**Auth / storage anti-patterns**
- Tokens / API keys in `localStorage` (persists, shared with content scripts if `all_frames`)
- Secrets hardcoded in source
- `browser.storage.local` for secrets -- acceptable but document the trust boundary

**Manifest V3 migration issues (if MV3)**
- `browser.webRequest.onBeforeRequest` with `["blocking"]` -- MV3 removed blocking webRequest on Chrome; Firefox still supports it but discourage for cross-browser
- Service worker / event page confusion -- Firefox MV3 uses event pages (DOM access OK), Chrome MV3 uses service workers
- Missing `declarativeNetRequest` rules when webRequest is being deprecated

**Code quality**
- `console.log` in production code
- No `"strict_min_version"` in `browser_specific_settings.gecko` (makes update channel unclear)
- Extension ID collisions / placeholder IDs

### 3. Output format

```markdown
# Firefox Extension Lint -- <extension-name> -- <date>

## Summary
- [BLOCKER] (AMO will reject): N
- [WARNING]: N
- [INFO]: N

## Blockers
- <file:line> <issue> -- <AMO rule or CVE> -- <fix>
- ...

## Warnings
- ...

## Informational
- ...

## Permissions audit
| Permission | Declared | Used | Recommendation |
|-----------|----------|------|----------------|
| `<all_urls>` | yes | <file:line>... | Narrow to specific domains |
| `tabs` | yes | - | Remove (unused) |
| ... |

## Next steps
1. Fix blockers
2. Run `npm run build` to produce the signed .zip
3. Run `/browser-extensions:firefox-publish` to sign + upload via AMO API
```

With `--strict`, treat all warnings as blockers (exit code 1).

## Synergies

- Full API / manifest details -> `browser-extensions:firefox-extension-dev-agent` agent
- Pre-AMO publishing workflow -> `/browser-extensions:firefox-publish`
- New extension scaffolding -> `/browser-extensions:firefox-scaffold`
