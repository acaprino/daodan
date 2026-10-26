---
description: Generates manifest.json (V3 default), directory layout, content and background scripts, web-ext config and a working popup. TRIGGER WHEN: creating, bootstrapping or scaffolding a new Firefox extension, WebExtension or browser add-on. DO NOT TRIGGER WHEN: features are added to an existing extension (use the firefox-extension-dev-agent agent).
---

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
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
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

# firefox-scaffold

<!-- Generated by the Daodan compiler for claude. Edit the kernel, never this file. -->

## Execution harness

Selected topology: **native-team**. Use native Agent Teams when they are enabled in this session;
otherwise dispatch the same roles as isolated subagents. Both paths satisfy the same contract, and
which one answered changes nothing a reader of the report can observe.
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

- Every dispatched worker runs in its own context and reads only coordinator-declared inputs.
  Independent reviewers never read peer results before their own delivery; no worker runs in the coordinator's context.
- Follow the dispatch plan below in phase order. A phase starts only after every phase it needs has
  closed, and a phase closes only when every worker it dispatched is recorded `delivered` or
  `failed`. A missing result is a recorded failure, never a silently shorter report.
- Dispatch only roles from this set, as the phase graph or loaded method requires: `firefox-extension-dev-agent`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `scope`: runs in the orchestrating context; produces `artifact:scope`.
2. `review`: one `firefox-extension-dev-agent` in an isolated context; needs `scope`; consumes `artifact:scope`; produces `artifact:firefox-scaffold-report`.

Role bindings:

- `firefox-extension-dev-agent`: dispatch the installed `browser-extensions:firefox-extension-dev-agent` agent by its qualified identity.

The phase graph, the isolation and join policies and the record schemas are in
`contracts/firefox-scaffold.workflow.toml`, which ships with this package.

## Method

# Firefox Extension Scaffold

Scaffold a production-ready Firefox WebExtension with Manifest V3 defaults, `web-ext` CLI integration, and AMO-compatible structure.

## CRITICAL RULES

1. **Default to Manifest V3**. Firefox MV3 supports both `background.scripts` (event pages with DOM access, unlike Chrome) and `declarativeNetRequest`. Only use V2 when the user has an explicit reason (ESR Firefox target, specific APIs not in V3).
2. **Generate a working "Hello World"** the user can load immediately via `web-ext run`. No `TODO` placeholders as the only content of any file.
3. **Match AMO submission requirements** from day one: no binary blobs without source, no obfuscated code, valid semver, unique `id` in `browser_specific_settings`.
4. **Never hardcode user identity**. If the user does not specify `--author` or `--id`, prompt them.

## Procedure

### 1. Parse arguments

- `extension-name`: required, kebab-case (becomes directory name + manifest `name` slugified)
- `--mv V2 | V3`: manifest version (default V3)
- `--sidebar`: include sidebar_action
- `--content-script`: include content script template (default: include)
- `--options-page`: include options UI template
- `--author NAME`: manifest `author`; if absent, ask the user
- `--id GECKO-ID`: `browser_specific_settings.gecko.id`; if absent, ask the user for their preferred format (`{extension-name}@example.com` or email-style), because AMO requires a unique ID

### 2. Directory layout

```
<extension-name>/
  manifest.json
  src/
    background.js            (or background.ts if --ts)
    content.js               (if --content-script)
    popup/
      index.html
      popup.js
      popup.css
    options/                 (if --options-page)
      index.html
      options.js
    sidebar/                 (if --sidebar)
      index.html
      sidebar.js
  icons/
    icon-48.png
    icon-96.png
  web-ext-config.js
  .web-ext-artifacts/        (gitignored, build output)
  .gitignore
  package.json
  README.md
```

### 3. Write manifest.json (MV3)

```json
{
  "manifest_version": 3,
  "name": "{{Extension Name}}",
  "version": "0.1.0",
  "description": "{{One-line description}}",
  "author": "{{Author from prompt}}",
  "icons": {
    "48": "icons/icon-48.png",
    "96": "icons/icon-96.png"
  },
  "browser_specific_settings": {
    "gecko": {
      "id": "{{extension-id from prompt}}",
      "strict_min_version": "128.0"
    }
  },
  "permissions": [],
  "host_permissions": [],
  "background": {
    "scripts": ["src/background.js"]
  },
  "action": {
    "default_popup": "src/popup/index.html",
    "default_title": "{{Extension Name}}"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["src/content.js"]
    }
  ]
}
```

If `--sidebar`, add:
```json
"sidebar_action": {
  "default_title": "{{Extension Name}}",
  "default_panel": "src/sidebar/index.html",
  "default_icon": "icons/icon-48.png"
}
```

If `--options-page`, add:
```json
"options_ui": {
  "page": "src/options/index.html",
  "open_in_tab": false
}
```

Always start with empty `permissions` / `host_permissions` arrays -- users add only what they need. AMO reviewers reject extensions requesting permissions they don't use.

### 4. Write web-ext-config.js

```javascript
module.exports = {
  verbose: false,
  sourceDir: './',
  artifactsDir: './.web-ext-artifacts',
  ignoreFiles: [
    'package-lock.json',
    'yarn.lock',
    'README.md',
    'web-ext-config.js',
    '.git',
    'node_modules',
    '.web-ext-artifacts',
  ],
  run: {
    startUrl: ['about:debugging#/runtime/this-firefox'],
    firefox: process.env.FIREFOX_BIN || 'firefox',
    browserConsole: true,
  },
  lint: {
    pretty: true,
    warningsAsErrors: false,
  },
  build: {
    overwriteDest: true,
  },
};
```

### 5. Write package.json

```json
{
  "name": "{{extension-name}}",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "start": "web-ext run",
    "build": "web-ext build",
    "lint": "web-ext lint",
    "sign": "web-ext sign --api-key=$WEB_EXT_API_KEY --api-secret=$WEB_EXT_API_SECRET"
  },
  "devDependencies": {
    "web-ext": "^8.0.0"
  }
}
```

### 6. Seed background.js with a working event

```javascript
// src/background.js
browser.runtime.onInstalled.addListener(({ reason }) => {
  if (reason === 'install') {
    console.log('{{Extension Name}} installed');
  }
});

browser.action.onClicked.addListener((tab) => {
  console.log('Action clicked on tab', tab.id, tab.url);
});
```

### 7. Seed popup with working HTML + JS

Popup renders "{{Extension Name}} -- click to greet", wires a button that calls `browser.tabs.query` and displays the active tab's URL. User sees something real in under 60 seconds.

### 8. Seed content.js (if --content-script) as a no-op that proves injection

```javascript
// src/content.js
console.log('{{Extension Name}} content script loaded on', window.location.href);
```

### 9. Write README with first-run instructions

```markdown
# {{Extension Name}}

## Develop

    npm install
    npm start    # launches Firefox with the extension loaded

## Lint

    npm run lint

## Build

    npm run build    # output: .web-ext-artifacts/{{name}}-{{version}}.zip

## Publish to AMO

1. Get API credentials from https://addons.mozilla.org/en-US/developers/addon/api/key/
2. Export `WEB_EXT_API_KEY` and `WEB_EXT_API_SECRET`
3. Run `npm run sign`
```

### 10. Report

Show created files, tell the user to run:
```
cd <extension-name>
npm install
npm start
```
and to replace placeholder icons (48x48 and 96x96 PNG) before publishing.

## Synergies

- Full API / manifest / AMO docs -> `browser-extensions:firefox-extension-dev-agent` agent or `firefox-extension-dev` skill
- Pre-publish lint -> `/browser-extensions:firefox-lint`
- Publishing flow -> `/browser-extensions:firefox-publish`
