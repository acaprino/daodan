---
name: obsidian-plugin-development
description: >
  Comply with the automated gate on first submission: eslint-plugin-obsidianmd rules plus the official guidelines.
  TRIGGER WHEN: writing, reviewing, or fixing Obsidian community plugin code.
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

# Obsidian Plugin Development

## Overview

Write Obsidian plugin code that passes Obsidian's automated plugin review on first submission. Since May 2026, plugins are submitted and reviewed through the Community hub at community.obsidian.md (the old PR workflow to `obsidianmd/obsidian-releases`, gated by ObsidianReviewBot, is retired); every GitHub release is scanned automatically. All rules below are enforced via `eslint-plugin-obsidianmd` and `@typescript-eslint`. Violations labeled "Required" block approval, and a failing version of an already-listed plugin is removed from directory search within 24 hours.

## When to Use

- Writing or editing TypeScript in an Obsidian plugin
- Preparing a plugin submission on the community.obsidian.md dashboard
- Fixing automated review violations
- Adding UI text, commands, settings tabs, or DOM manipulation

## Quick Reference: Required Rules

### 1. Sentence Case for All UI Text

Every user-visible string: sentence case only.

```typescript
// NO
'Block Settings'
'Add Block'
'Recent Files'

// YES
'Block settings'
'Add block'
'Recent files'
```

Applies to: `Setting.setName()`, `Setting.setDesc()`, `createEl()` text, button labels, modal titles, notices, menu items, tooltips. Proper nouns and acronyms (e.g. "API", "GitHub", "Obsidian") keep their casing.

### 2. No Inline Styles

Never assign `element.style.*` directly. Use CSS classes.

```typescript
// NO
el.style.display = 'flex';
el.style.transform = 'scale(0.9)';
el.style.opacity = '0';

// YES -- use CSS classes
el.addClass('hp-flex-container');
el.toggleClass('hp-scaled', true);
el.toggleClass('hp-hidden', true);

// For dynamic CSS custom properties, use setCssProps or setCssStyles:
el.setCssStyles({ '--my-var': value });
```

Flagged properties include: `display`, `transform`, `opacity`, `width`, `height`, `margin`, `padding`, `cursor`, `fontSize`, `fontFamily`, `flexDirection`, `alignItems`, `flexShrink`, `borderRadius`, `backdropFilter`, `background`, `borderWidth`, `borderStyle`, `transition`, `gridTemplateRows`, `transformOrigin`, and all others.

### 3. No Unnecessary Type Assertions

Don't `as Type` when it doesn't change the type.

```typescript
// NO -- assertion is redundant with ?? fallback
draft.url as string ?? ''
draft.showDate as boolean ?? true

// YES
String(draft.url ?? '')
Boolean(draft.showDate ?? true)
// or just
(draft.url ?? '') as string   // assertion AFTER coalescing
```

### 4. Promises Must Be Handled

Every Promise must be: `await`ed, `.catch()`ed, `.then()` with rejection handler, or `void`ed.

```typescript
// NO
someAsyncFn();
this.app.vault.read(file).then(text => { ... });

// YES
await someAsyncFn();
void someAsyncFn();
this.app.vault.read(file).then(text => { ... }, err => console.error(err));
this.app.vault.read(file).then(text => { ... }).catch(console.error);
```

### 5. No Async Without Await

Remove `async` from methods that don't use `await`.

```typescript
// NO
async onOpen() { this.render(); }

// YES
onOpen() { this.render(); }
```

### 6. No Promise Where Void Expected

Don't return a Promise in callbacks expecting `void`.

```typescript
// NO -- event callback expects void
this.registerEvent(this.app.vault.on('modify', async (file) => {
  await this.reload();
}));

// YES
this.registerEvent(this.app.vault.on('modify', (file) => {
  void this.reload();
}));
```

### 7. No Object Stringification

Ensure values won't stringify as `[object Object]`.

```typescript
// NO -- if draft is Record<string,unknown>, draft.mode could be an object
`Value: ${draft.mode ?? 'default'}`

// YES
`Value: ${String(draft.mode ?? 'default')}`
```

### 8. Settings Headings: Use Setting API

Don't create HTML headings. Use `Setting.setHeading()`.

```typescript
// NO
contentEl.createEl('h2', { text: 'My settings' });

// YES
new Setting(contentEl).setName('My settings').setHeading();
```

### 9. No Detach Leaves in onunload

Obsidian handles leaf cleanup. Detaching resets user's layout.

```typescript
// NO
onunload() {
  this.app.workspace.detachLeavesOfType(VIEW_TYPE);
}

// YES
onunload() {
  // Obsidian cleans up leaves automatically
}
```

### 10. No TFile/TFolder Cast

Use `instanceof` instead of type casting.

```typescript
// NO
const file = abstractFile as TFile;

// YES
if (abstractFile instanceof TFile) { ... }
```

### 11. No Forbidden DOM Elements

Don't create `<style>` or `<link>` elements dynamically.

### 12. No Plugin as Component

Don't pass `this` (plugin) to `MarkdownRenderer.render()`. Use a `Component` instance.

```typescript
// NO
MarkdownRenderer.render(this.app, md, el, '', this);

// YES -- use a Component subclass or this view/block
MarkdownRenderer.render(this.app, md, el, '', this.component);
```

### 13. No View References in Plugin

Don't store view references in plugin properties (memory leak).

### 14. Use Vault.configDir

Don't hardcode `.obsidian`. Use `this.app.vault.configDir`.

### 15. Platform Detection

Use `Platform` API, not `navigator.userAgent`.

```typescript
// NO
if (navigator.userAgent.includes('Mac')) { ... }

// YES
import { Platform } from 'obsidian';
if (Platform.isMacOS) { ... }
```

### 16. No Regex Lookbehind

Lookbehinds break on some iOS versions. Avoid unless `isDesktopOnly: true`.

### 17. Commands

- No word "command" in command ID or name
- No plugin ID in command ID
- No plugin name in command name
- No default hotkeys

### 18. File Operations

- Use `FileManager.trashFile()` instead of `Vault.trash()`/`Vault.delete()`
- Don't iterate all files to find by path -- use `getAbstractFileByPath()`
- Use `normalizePath()` for user-provided paths

### 19. No Sample/Template Code

Remove `MyPlugin`, `SampleModal`, template code from obsidian-sample-plugin.

### 20. Object.assign

Don't use `Object.assign(this.settings, data)` to mutate defaults.

### 21. Manifest & License

- `manifest.json` must have valid structure
- `LICENSE` must have correct copyright holder and current year
- Plugin ID: alphanumeric + dashes, no "obsidian", no "plugin" suffix
- Description: no "Obsidian", no "This plugin", must end with `. ? ! )`

### 22. Popout Window Compatibility

Use the popout-safe globals. Bare `document` and global timers target the main window only and break in popout windows.

```typescript
// NO
document.body.appendChild(el);
const t = setTimeout(cb, 500);
clearTimeout(t);
globalThis.myFlag = true;

// YES
activeDocument.body.appendChild(el);
const t = activeWindow.setTimeout(cb, 500);
activeWindow.clearTimeout(t);
```

Rules: `obsidianmd/prefer-active-doc` (warn), `obsidianmd/prefer-window-timers` (error, also covers `setInterval` and `requestAnimationFrame`), `obsidianmd/no-global-this` (error).

### 23. API Availability vs minAppVersion

Every API the code calls must exist in the Obsidian version declared as `minAppVersion`. `obsidianmd/no-unsupported-api` cross-checks usage against the manifest.

```typescript
// NO -- revealLeaf needs v1.7.2 but manifest says minAppVersion 1.5.0
await this.app.workspace.revealLeaf(leaf);

// YES -- raise minAppVersion to 1.7.2, or gate the call behind a version check
```

### 24. Use createEl Helpers

```typescript
// NO
document.createElement('iframe');
document.createDocumentFragment();
el.createEl('span', { text: file.path });

// YES
createEl('iframe');
createFragment();
el.createSpan({ text: file.path });
```

Rule `obsidianmd/prefer-create-el`. The review platform enforces it, but the rule is not yet in the npm release, so local ESLint misses it: check these patterns manually.

### 25. ESLint Directive Comments

Every `eslint-disable` directive needs a description, and some rules cannot be disabled at all (`obsidianmd/no-static-styles-assignment`, `obsidianmd/ui/sentence-case`).

```typescript
// NO
// eslint-disable-next-line obsidianmd/prefer-active-doc

// YES
// eslint-disable-next-line obsidianmd/prefer-active-doc -- main-window-only startup code
```

Enforced platform-side via `@eslint-community/eslint-comments/require-description` and `no-restricted-disable`; add the same plugin locally to catch them before release.

## Optional (Non-blocking)

- Remove unused variables and imports
- Use `AbstractInputSuggest` instead of copied `TextInputSuggest`
- Don't persist data in `localStorage` or `sessionStorage`. Use `Plugin.loadData()`/`saveData()` for plugin data (stored in the plugin's `data.json`, synced with the vault). For device-specific per-vault values (window positions, device caches), use `App.loadLocalStorage()`/`App.saveLocalStorage()`, which scope keys to the current vault. Raw `localStorage` is shared across all vaults on the device and never synced; `sessionStorage` does not survive a restart.

## Additional Best Practices

| Practice | Details |
|----------|---------|
| No `innerHTML`/`outerHTML` | Use `createEl`, `setText`, `sanitizeHTMLToDom` |
| Use `requestUrl()` | Instead of `fetch()` for network requests |
| CSS variables for theming | `--background-secondary`, `--text-muted`, etc. |
| Scope CSS | All plugin CSS scoped to plugin containers |
| Accessibility | `aria-label` on icon buttons, keyboard nav, focus indicators |
| Touch targets | Min 44x44px on mobile |
| Auto-cleanup | `registerEvent()`, `registerInterval()`, `register()` |
| No production logging | No `console.log` in `onload()`/`onunload()` |

## API Reference

See `references/obsidian-api-reference.md` in this skill directory for a condensed TypeScript API reference covering all key classes: Plugin, App, Vault, Workspace, MetadataCache, FileManager, Component, View, Modal, Setting, Menu, MarkdownRenderer, Platform, DOM helpers, and more.

For the full type definitions, read `node_modules/obsidian/obsidian.d.ts` in the project.

## Running Checks Locally

```bash
npm install --save-dev eslint-plugin-obsidianmd @eslint-community/eslint-plugin-eslint-comments
```

Configure ESLint with the obsidianmd recommended config plus the eslint-comments rules (`require-description`, `no-restricted-disable`). Lint `src/` AND `package.json` (the dependency rules only fire when `package.json` is linted). Run before publishing a release: the platform scans every GitHub release automatically.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Title Case in UI text | Sentence case everything |
| `el.style.display = 'none'` | `el.addClass('hp-hidden')` |
| `as string ?? ''` | `String(x ?? '')` |
| `createEl('h2', ...)` in modal | `new Setting(el).setName(...).setHeading()` |
| Async onOpen without await | Remove `async` keyword |
| Unhandled promise | Add `void`, `await`, or `.catch()` |
| `detachLeavesOfType` in onunload | Remove -- Obsidian handles it |
| `abstractFile as TFile` | `if (x instanceof TFile)` |
| `setTimeout(cb, ms)` | `activeWindow.setTimeout(cb, ms)` |
| `document.body` | `activeDocument.body` |
| `el.createEl('span', {...})` | `el.createSpan({...})` |
| Bare `// eslint-disable-next-line` | Append ` -- reason` description |
| New API with old `minAppVersion` | Raise `minAppVersion` to the API's version |
| `localStorage.setItem('key', v)` | `this.app.saveLocalStorage('key', v)` or `this.saveData(...)` |
