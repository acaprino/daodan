---
name: firefox-lint-workflow
description: 'Runs `web-ext lint` plus static checks for forbidden APIs, permission bloat, remote-hosted code and Manifest V3 migration issues. TRIGGER WHEN: linting, validating or checking a Firefox extension, before an AMO submission or a git push on an extension project.'
---

> Arguments: `[path] [--strict] [--json]`. Wherever `<arguments>` appears below, substitute the text the user typed after the skill name.

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

# firefox-lint

<!-- Generated by the Daodan compiler for codex. Edit the kernel, never this file. -->

## Execution harness

Selected topology: **parallel-subagents**, with role delivery by **inline-prompt**. Start one isolated
runtime subagent per dispatched worker. When role delivery is `inline-prompt`, paste that role's
Markdown body into the dispatch prompt verbatim: the worker must receive the whole role, not a
summary of it.
Declared worker isolation: **required**.

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

- Every dispatched worker runs in its own subagent context and reads only coordinator-declared inputs.
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

Role body bindings (load the complete body only for the selected worker):

- `firefox-extension-dev-agent`: read `roles/firefox-extension-dev-agent.md` inside this package and pass its complete body verbatim.

The phase graph and record-schema references ship under `contracts/firefox-lint.workflow.toml`.

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
