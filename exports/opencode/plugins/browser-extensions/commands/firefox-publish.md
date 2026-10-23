---
description: 'Lints, signs and uploads a build on the listed or unlisted channel, then walks the user through the review workflow. TRIGGER WHEN: publishing, releasing, submitting, uploading or signing a Firefox extension, or preparing an addons.mozilla.org (AMO) submission.'
---

<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
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

# firefox-publish

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
2. `review`: one `firefox-extension-dev-agent` in an isolated context; needs `scope`; consumes `artifact:scope`; produces `artifact:firefox-publish-report`.

Role bindings:

- `firefox-extension-dev-agent`: dispatch the installed `browser-extensions:firefox-extension-dev-agent` agent by its qualified identity.

The phase graph and the record schemas are in `contracts/firefox-publish.workflow.toml`.

## Method

# Firefox Extension Publish

Signed publication to AMO. Covers pre-flight validation, signing via `web-ext sign`, and post-submission follow-up.

## CRITICAL RULES

1. **Run lint first**. Never submit unlinted -- Mozilla's AMO reviewers reject submissions for issues `web-ext lint` catches in 30 seconds.
2. **Never commit API credentials**. Credentials live in env vars or a gitignored `.env`; refuse to proceed if they appear in the repo.
3. **Choose the right channel**:
   - `listed` -- public AMO listing, goes through Mozilla review (1-14 days, sometimes longer)
   - `unlisted` -- self-distribution, auto-signed in seconds, not shown on AMO
4. **Bump version before submission**. AMO rejects resubmissions with the same version string.
5. **Confirm with the user before upload**. Signing is fast to revert; a listed review that starts is annoying to withdraw.

## Procedure

### 1. Pre-flight

```bash
# Check credentials
test -n "$WEB_EXT_API_KEY" || fail "WEB_EXT_API_KEY not set"
test -n "$WEB_EXT_API_SECRET" || fail "WEB_EXT_API_SECRET not set"

# Check .env or credential files are gitignored
git check-ignore -v .env || fail ".env is not gitignored"
```

If credentials are missing, guide the user to https://addons.mozilla.org/en-US/developers/addon/api/key/ to generate them.

### 2. Run lint

Invoke `/browser-extensions:firefox-lint` first. If any blockers, stop.

### 3. Bump version

Read current version from `manifest.json`. If `--version` is supplied, use it; otherwise ask the user for:
- patch (`0.1.0` -> `0.1.1`) -- bug fixes
- minor (`0.1.0` -> `0.2.0`) -- new features
- major (`0.1.0` -> `1.0.0`) -- breaking change (first public release is traditionally `1.0.0`)

Update both `manifest.json` and `package.json`. Stage these edits but DO NOT commit automatically -- the user may want to do a final review.

### 4. Build

```bash
cd "$TARGET"
npx web-ext build --overwrite-dest
# Artifact: .web-ext-artifacts/<name>-<version>.zip
```

Verify the artifact exists and is reasonably sized (warn if > 10 MB -- large extensions get slower AMO review).

### 5. Sign / upload

**Listed channel (public review):**
```bash
npx web-ext sign \
  --api-key="$WEB_EXT_API_KEY" \
  --api-secret="$WEB_EXT_API_SECRET" \
  --channel=listed
```

**Unlisted channel (self-distribution, auto-signed):**
```bash
npx web-ext sign \
  --api-key="$WEB_EXT_API_KEY" \
  --api-secret="$WEB_EXT_API_SECRET" \
  --channel=unlisted
```

With `--dry-run`, stop before signing and print the command the user would run.

### 6. Post-submission

**For listed:**
- Tell the user the submission ID
- Link to the AMO developer dashboard: `https://addons.mozilla.org/en-US/developers/addon/<slug>/versions`
- Review typically takes 1-14 days; expect extra time for extensions with broad host_permissions or native messaging
- If rejected, Mozilla emails a reason; common causes: obfuscated code, remote-hosted code, unjustified permissions, missing source code submission (required for bundlers)

**For unlisted:**
- Signed XPI is written to `.web-ext-artifacts/`; user hosts it themselves
- For auto-update, add an `updates.json` or `update_url` in `manifest.json` pointing to a signed update feed

### 7. Tag release

Suggest (do not auto-execute):
```bash
git tag v<new-version>
git push origin v<new-version>
```

Optionally open a GitHub release with the signed XPI attached.

### 8. Source code submission reminder (listed only)

If the project uses a bundler (webpack, Vite, Rollup, esbuild), Mozilla requires the original source code plus build instructions to be submitted alongside the signed XPI. `web-ext sign --channel=listed` will prompt; otherwise manually attach via the AMO dashboard.

Minimum source-upload contents:
- Original source (src/, package.json, lockfile)
- Build config (webpack.config.js, vite.config.ts, etc.)
- README.md explaining how to reproduce the build from source
- No node_modules/ or build artifacts

## Synergies

- Scaffolding a new extension -> `/browser-extensions:firefox-scaffold`
- Pre-submission lint -> `/browser-extensions:firefox-lint`
- API / manifest / MDN lookups -> `browser-extensions:firefox-extension-dev-agent` agent
