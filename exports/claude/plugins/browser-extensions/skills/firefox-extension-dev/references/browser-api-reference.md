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

# WebExtension JavaScript APIs

The full API surface lives on MDN -- this file is the navigation index plus the Firefox-only APIs and MV2/MV3 differences worth memorizing. For per-method deep-links, see `mdn-api-urls.md`.

## When to use

Picking which API to use, knowing whether it's Firefox-only, and knowing what permission to declare. For per-API method/event listings, hit MDN directly.

## API namespace pattern

All APIs accessed via `browser.*` (Firefox returns Promises for all async methods; Chrome's `chrome.*` uses callbacks unless polyfilled). For cross-browser code, use the `webextension-polyfill` package and continue calling `browser.*`.

## Firefox-only APIs (don't write code expecting Chrome to support these)

- `browserSettings` -- global browser settings
- `captivePortal` -- detect captive portal
- `contextualIdentities` -- container tabs (also requires `cookies` permission)
- `dns` -- DNS resolution
- `find` -- find text in pages
- `pkcs11` -- security modules
- `sidebarAction` -- sidebar panel (Chrome has its own side-panel API, different shape)
- `tabHide` -- experimental, Firefox-only
- `webRequestFilterResponse` -- response body filtering

Plus: Firefox keeps **blocking `webRequest` in MV3** (Chrome dropped it), and supports both `declarativeNetRequest` AND blocking `webRequest` simultaneously -- this is the headline reason ad-blockers prefer Firefox MV3.

## MV2 → MV3 API renames (the gotchas)

| MV2 | MV3 |
|-----|-----|
| `browserAction` (manifest `browser_action`) | `action` (manifest `action`) |
| `tabs.executeScript` / `tabs.insertCSS` / `tabs.removeCSS` | `scripting.executeScript` / `scripting.insertCSS` / `scripting.removeCSS` |
| `contentScripts` API | `scripting.registerContentScripts` |
| `user_scripts` (manifest) | `userScripts` API (MV3 needs optional permission) |
| `background.scripts` + `persistent` | `background.scripts` (event page in Firefox) / `service_worker` (Chrome) |
| `web_accessible_resources` (string array) | `web_accessible_resources` (object array with `resources`+`matches`+`extension_ids`) |

Firefox keeps `pageAction` in MV3; Chrome dropped it.

## Storage areas (the only API where Firefox-vs-Chrome differs in limits)

| Area | Limit | Persistence |
|------|-------|-------------|
| `storage.local` | 10 MB | On disk |
| `storage.sync` | 100 KB | Synced across devices (requires sign-in) |
| `storage.session` | 10 MB | In-memory only, lost on restart |
| `storage.managed` | Read-only | Set by domain admin |

**Never use `window.localStorage` in extensions** -- Firefox clears it during privacy cleanup. Use `browser.storage.local` instead.

## Permission cheat sheet (the most common ones)

| Permission | Use |
|------------|-----|
| `activeTab` | Temporary access to active tab on user action -- prefer over `<all_urls>` |
| `tabs` | Read URL/title/favIconUrl on Tab objects (different from access) |
| `storage` | `browser.storage` API |
| `cookies` | Cookie management (+ host perms required) |
| `webRequest` | Listen to HTTP requests |
| `webRequestBlocking` | Modify/block HTTP requests (Firefox keeps this in MV3) |
| `scripting` | MV3 script/CSS injection |
| `declarativeNetRequest` | Declarative network filtering |
| `notifications` | OS notifications |
| `clipboardWrite` / `clipboardRead` | System clipboard |
| `unlimitedStorage` | Skip the 10 MB `storage.local` limit |
| `nativeMessaging` | `runtime.connectNative()` / `sendNativeMessage()` |

## Gotchas

- **Firefox returns Promises for everything.** Chrome's older callback API still works in Chrome MV3 alongside Promises. Cross-browser code: use `webextension-polyfill`.
- **`browser.tabs.executeScript` is MV2-only.** In MV3 use `browser.scripting.executeScript({ target: { tabId }, func: () => {...} })`.
- **`chrome.action` exists in Chrome MV3, but `browser.action` may need polyfill** for older Firefox versions -- check `strict_min_version` in `browser_specific_settings`.
- **`runtime.onInstalled` fires for both `install` and `update`** -- check `reason` to differentiate. The `reason` value `browser_update` and `chrome_update` differ between browsers.
- **`runtime.setUninstallURL`** is the cleanest way to drive a feedback survey -- works in both MV2/MV3.

## Quick API recipes (the few worth keeping local)

```javascript
// Active tab (the safe pattern)
const [tab] = await browser.tabs.query({ active: true, currentWindow: true });

// Storage with default fallback
const { settings } = await browser.storage.local.get({
  settings: { theme: "light", fontSize: 14 }
});

// Listen for storage changes across pages
browser.storage.onChanged.addListener((changes, areaName) => {
  for (const [key, { oldValue, newValue }] of Object.entries(changes)) {
    console.log(`${areaName}.${key}: ${oldValue} -> ${newValue}`);
  }
});

// Install vs update branch
browser.runtime.onInstalled.addListener(({ reason }) => {
  if (reason === "install") initializeDefaults();
  if (reason === "update") migrateData();
});
```

## Official docs

- WebExtension API index (MDN): https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API
- Browser compatibility per API: each MDN page has a "Browser compatibility" table
- Permissions reference: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/permissions
- Firefox vs Chrome incompatibilities: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Chrome_incompatibilities
- MV2 → MV3 migration guide: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Manifest_V3_migration_guide
- `webextension-polyfill`: https://github.com/mozilla/webextension-polyfill

## Related

- `mdn-api-urls.md` -- direct deep-links per API method/event
- `manifest-schema.md` -- which manifest key enables which API
- `amo-publishing.md` -- which permissions trigger AMO manual review
- `best-practices.md` -- the MV3 footgun catalog (must-read for production extensions)
