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

# Obsidian TypeScript API - Quick Reference

The Obsidian API surface is fully typed in `node_modules/obsidian/obsidian.d.ts`. The official reference lives at https://docs.obsidian.md/Reference/TypeScript+API. This file is just the navigation index plus the few quirks worth knowing locally.

## When to use

Looking up a class, method, or event signature while writing a plugin. For deeper API behavior (lifecycle, threading, when each event fires), the `.d.ts` source is authoritative -- read it.

## The classes you'll touch in 95% of plugins

- `Plugin` (extends `Component`) -- `onload()`, `onunload()`, `addCommand()`, `addSettingTab()`, `addRibbonIcon()`, `registerView()`, `registerMarkdownPostProcessor()`, `loadData()`/`saveData()`, plus `app: App` and `manifest: PluginManifest`
- `App` -- the root: `vault`, `workspace`, `metadataCache`, `fileManager`, `keymap`, `scope`, `isDarkMode()`, `loadLocalStorage(key)`/`saveLocalStorage(key, data)` (device-local key-value store scoped to the current vault; use instead of raw `localStorage`)
- `Vault` (extends `Events`) -- file operations: `read()`/`cachedRead()`, `create()`, `modify()`, `process()` (the safer modify), `delete()`/`trash()`, plus events `create`/`delete`/`rename`/`modify`
- `Workspace` (extends `Events`) -- panes/leaves: `getLeaf()`, `getActiveFile()`, `openLinkText()`, `onLayoutReady()`, plus events `active-leaf-change`, `file-open`, `layout-change`
- `MetadataCache` -- `getFileCache()`, `resolvedLinks`, `unresolvedLinks`, plus events `changed`, `resolve`, `resolved`
- `Component` -- the lifecycle base: `addChild()`, `register()`, `registerEvent()`, `registerDomEvent()`, `registerInterval()`
- `View` / `ItemView` -- custom panes
- `Modal` / `SuggestModal<T>` / `AbstractInputSuggest<T>` -- dialogs and pickers
- `Setting` -- the settings tab builder (`addToggle`, `addText`, `addDropdown`, `addSlider`, `addColorPicker`, `addProgressBar`, `then`, ...)
- `Menu` / `MenuItem` -- context menus
- `Notice` -- toast messages

## File types

- `TAbstractFile` -- base (path, name, parent)
- `TFile` -- adds `stat: { ctime, mtime, size }`, `basename`, `extension`
- `TFolder` -- adds `children: TAbstractFile[]`, `isRoot()`

## Helper functions worth knowing

- `requestUrl(...)` -- HTTP client that bypasses CORS (the right way to fetch from a plugin)
- `sanitizeHTMLToDom(html)` -- safe HTML insertion
- `normalizePath(path)` -- normalize cross-platform paths
- `requireApiVersion('1.4.0')` -- gate features by Obsidian version
- `addIcon(id, svg)` / `getIcon(id)` -- custom icon registration
- `moment` -- the global moment.js instance (use this, don't bundle your own)

## HTMLElement extensions (Obsidian augments DOM)

Obsidian adds methods to `HTMLElement.prototype`. Use these instead of vanilla DOM where they exist:
- `createEl()`, `createDiv()`, `createSpan()`, `createSvg()` -- typed element creation with `DomElementInfo` shorthand (`cls`, `text`, `attr`, `parent`)
- `setText()`, `getText()` -- text content
- `addClass()` / `removeClass()` / `toggleClass()` / `hasClass()` -- class manipulation
- `setAttr()` / `setAttrs()` / `getAttr()` -- attribute manipulation
- `show()` / `hide()` / `toggle()` -- visibility
- `setCssStyles()` / `setCssProps()` / `getCssPropertyValue()` -- CSS

## Platform detection

Static `Platform` namespace: `isDesktop`, `isMobile`, `isDesktopApp`, `isMobileApp`, `isIosApp`, `isAndroidApp`, `isPhone`, `isTablet`, `isMacOS`, `isWin`, `isLinux`, `isSafari`. Useful for gating `addStatusBarItem()` (desktop-only) and similar.

## Gotchas (the few worth memorizing)

- **`vault.read()` always re-reads from disk; `vault.cachedRead()` reads from Obsidian's cache.** For UI/preview/quick lookups use `cachedRead()`; only use `read()` when you need bytes-on-disk freshness (e.g. before editing).
- **`vault.process()` is safer than `read()` + `modify()`** -- it's atomic and prevents lost-write races when multiple plugins edit the same file.
- **`vault.trash(file, system)` honors the user's "Files and links → Deleted files" setting** when `system: false`. Use it instead of `delete()` for user-initiated deletions.
- **Use `Component`'s `register*` methods** (`registerEvent`, `registerDomEvent`, `registerInterval`) -- they auto-cleanup on `unload`. Manual `addEventListener` without registering = leak.
- **`onLayoutReady(callback)`** is the right place for code that needs the workspace populated -- not `onload()`. Vault iteration in `onload()` will miss files until layout is ready.
- **`requestUrl()`, NOT `fetch()`**, for HTTP from a plugin -- `fetch` is subject to web CORS, `requestUrl` is the desktop/mobile API that bypasses it.
- **`addStatusBarItem()` is desktop-only** -- gate with `Platform.isDesktopApp`.
- **`processFrontMatter(file, fn)`** is the right way to edit YAML frontmatter -- don't regex-edit the file content.

## Official docs

- TypeScript API reference: https://docs.obsidian.md/Reference/TypeScript+API
- Plugin developer docs: https://docs.obsidian.md/Plugins/Getting+started/Build+a+plugin
- Sample plugin (the canonical starter): https://github.com/obsidianmd/obsidian-sample-plugin
- API source (.d.ts): https://github.com/obsidianmd/obsidian-api/blob/master/obsidian.d.ts
- Plugin guidelines (review checklist): https://docs.obsidian.md/Plugins/Releasing/Plugin+guidelines
- Releasing a plugin: https://docs.obsidian.md/Plugins/Releasing/Submit+your+plugin
- Community hub (submission dashboard, replaces the PR workflow since May 2026): https://community.obsidian.md
- Workflow change announcement: https://obsidian.md/blog/future-of-plugins/

## Related

- The plugin's main `SKILL.md` -- automated review rules consolidated as a checklist with bad/good code examples
