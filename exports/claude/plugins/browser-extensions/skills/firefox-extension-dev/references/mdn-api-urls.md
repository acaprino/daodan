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

# MDN WebExtensions API URL Index

Quick-lookup index for official Mozilla documentation. Use these URLs with host page-fetch binding for detailed API info.

## Base URLs

- **API root:** `https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API`
- **Examples repo:** `https://github.com/mdn/webextensions-examples`
- **Extension Workshop:** `https://extensionworkshop.com`
- **Manifest keys:** `https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json`

## browser.* API URLs

| API | MDN URL |
|---|---|
| `action` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/action |
| `alarms` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/alarms |
| `bookmarks` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/bookmarks |
| `browserAction` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/browserAction |
| `browserSettings` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/browserSettings |
| `browsingData` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/browsingData |
| `captivePortal` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/captivePortal |
| `clipboard` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/clipboard |
| `commands` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/commands |
| `contentScripts` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/contentScripts |
| `contextualIdentities` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/contextualIdentities |
| `cookies` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/cookies |
| `declarativeNetRequest` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/declarativeNetRequest |
| `devtools.inspectedWindow` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/devtools/inspectedWindow |
| `devtools.network` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/devtools/network |
| `devtools.panels` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/devtools/panels |
| `dns` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/dns |
| `dom` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/dom |
| `downloads` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/downloads |
| `events` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/events |
| `extension` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/extension |
| `extensionTypes` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/extensionTypes |
| `find` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/find |
| `history` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/history |
| `i18n` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/i18n |
| `identity` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/identity |
| `idle` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/idle |
| `management` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/management |
| `menus` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/menus |
| `notifications` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/notifications |
| `omnibox` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/omnibox |
| `pageAction` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/pageAction |
| `permissions` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/permissions |
| `pkcs11` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/pkcs11 |
| `privacy` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/privacy |
| `proxy` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/proxy |
| `runtime` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/runtime |
| `scripting` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/scripting |
| `search` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/search |
| `sessions` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/sessions |
| `sidebarAction` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/sidebarAction |
| `storage` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/storage |
| `tabGroups` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabGroups |
| `tabs` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs |
| `theme` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/theme |
| `topSites` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/topSites |
| `types` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/types |
| `userScripts` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/userScripts |
| `webNavigation` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/webNavigation |
| `webRequest` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/webRequest |
| `windows` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/windows |

## Manifest Key URLs

| Key | MDN URL |
|---|---|
| `action` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/action |
| `background` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/background |
| `browser_specific_settings` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/browser_specific_settings |
| `commands` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/commands |
| `content_scripts` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/content_scripts |
| `content_security_policy` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/content_security_policy |
| `declarative_net_request` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/declarative_net_request |
| `devtools_page` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/devtools_page |
| `host_permissions` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/host_permissions |
| `icons` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/icons |
| `omnibox` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/omnibox |
| `optional_permissions` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/optional_permissions |
| `options_ui` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/options_ui |
| `permissions` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/permissions |
| `protocol_handlers` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/protocol_handlers |
| `sidebar_action` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/sidebar_action |
| `web_accessible_resources` | https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/web_accessible_resources |

## Extension Workshop URLs

| Topic | URL |
|---|---|
| Getting started | https://extensionworkshop.com/documentation/develop/getting-started-with-web-ext/ |
| Porting Chrome extension | https://extensionworkshop.com/documentation/develop/porting-a-google-chrome-extension/ |
| MV3 migration guide | https://extensionworkshop.com/documentation/develop/manifest-v3-migration-guide/ |
| Testing | https://extensionworkshop.com/documentation/develop/testing-persistent-and-restart-features/ |
| Debugging | https://extensionworkshop.com/documentation/develop/debugging/ |
| Publishing | https://extensionworkshop.com/documentation/publish/ |
| Review policies | https://extensionworkshop.com/documentation/publish/add-on-policies/ |
| Source code submission | https://extensionworkshop.com/documentation/publish/source-code-submission/ |
| Recommended extensions | https://extensionworkshop.com/documentation/publish/recommended-extensions/ |
| Security best practices | https://extensionworkshop.com/documentation/develop/build-a-secure-extension/ |
| Request permissions | https://extensionworkshop.com/documentation/develop/request-the-right-permissions/ |
| User experience | https://extensionworkshop.com/documentation/develop/user-experience-best-practices/ |
| Temporary installation | https://extensionworkshop.com/documentation/develop/temporary-installation-in-firefox/ |
| web-ext reference | https://extensionworkshop.com/documentation/develop/web-ext-command-reference/ |
