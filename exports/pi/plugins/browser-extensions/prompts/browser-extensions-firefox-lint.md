---
description: 'Runs `web-ext lint` plus static checks for forbidden APIs, permission bloat, remote-hosted code and Manifest V3 migration issues. TRIGGER WHEN: linting, validating or checking a Firefox extension, before an AMO submission or a git push on an extension project.'
---

<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

# firefox-lint

<!-- Generated by the Daodan compiler for pi. Edit the kernel, never this file. -->

## Execution harness

Selected topology: **parallel-subagents**, with role delivery by **inline-prompt**, and declared
isolation **required**. Dispatch one worker per entry in the plan below with the `subagent`
tool supplied by the `pi-subagents` package, each in its own context. Role delivery here is
`inline-prompt`: paste that role's Markdown body into the dispatch prompt verbatim, because the
worker must receive the whole role rather than a summary of it.

Pi's core ships no subagent tool. If none is available in this session, the declared isolation
above decides what happens, and the two cases are not interchangeable:

- **`required`**: stop, and tell the user to run `pi install npm:pi-subagents`. Running the phases
  serially in this one context is the loss of isolation rather than a lesser form of it, so a
  report produced that way would claim a contract it did not meet.
- **`shared`**: run the phases in order in this context, and say in the report that no worker was
  isolated.

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
- Workers may write only intermediate reports explicitly assigned by the coordinator.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `scope`: runs in the orchestrating context; produces `artifact:scope`.
2. `review`: one `firefox-extension-dev-agent` in an isolated context; needs `scope`; consumes `artifact:scope`; produces `artifact:firefox-lint-report`.

Role body bindings (load the complete body only for the selected worker):

- `firefox-extension-dev-agent`: read `skills/browser-extensions-firefox-extension-dev-agent/SKILL.md` inside this package and pass its complete body verbatim.

The phase graph and record-schema references are in `contracts/firefox-lint.workflow.toml`.

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
