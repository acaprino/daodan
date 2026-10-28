---
name: obsidian-check
description: >
  Report every automated-review violation with its file location and fix.
  TRIGGER WHEN: preparing an Obsidian plugin for submission or before pushing code.
---

<daodan_host_binding host="claude">
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

Claude binding: repository read, file discovery and content search use Read, Glob
and Grep; repository write and repository edit use Write and Edit; shell execution
uses Bash; network fetch uses WebFetch and network search uses WebSearch; a user
question uses AskUserQuestion. Pass the executable string in Bash's
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

# Obsidian Check

Review code against all Obsidian automated plugin review rules before pushing. Since May 2026 the review runs on the Community hub (community.obsidian.md) and scans every GitHub release; a failing version is removed from directory search within 24 hours. Reports violations grouped by severity with exact file locations and fixes.

## Usage

This is a skill, not a slash command. Invoke it by asking to check an Obsidian plugin before submission, or by its skill name `obsidian-development:obsidian-check`. It scans the current Obsidian plugin project for all automated review violations.

## Procedure

### Step 1: Verify project structure

Check that `manifest.json`, `package.json`, and `src/` exist. If not, abort with message.

### Step 2: Ensure eslint-plugin-obsidianmd is installed

Check if `eslint-plugin-obsidianmd` and `@eslint-community/eslint-plugin-eslint-comments` are in `package.json` devDependencies. If NOT installed:

1. Install them and the peer dependencies:

```bash
npm install --save-dev eslint eslint-plugin-obsidianmd @eslint-community/eslint-plugin-eslint-comments @typescript-eslint/parser typescript-eslint @eslint/js
```

2. If no ESLint config file exists (`eslint.config.mjs`, `.eslintrc.*`), create `eslint.config.mjs`. The eslint-comments block mirrors checks that Obsidian's review platform adds on top of the obsidianmd recommended config:

```javascript
import tsparser from "@typescript-eslint/parser";
import { defineConfig } from "eslint/config";
import obsidianmd from "eslint-plugin-obsidianmd";
import comments from "@eslint-community/eslint-plugin-eslint-comments/configs";

export default defineConfig([
  ...obsidianmd.configs.recommended,
  comments.recommended,
  {
    rules: {
      "@eslint-community/eslint-comments/require-description": "error",
      "@eslint-community/eslint-comments/no-restricted-disable": [
        "error",
        "obsidianmd/no-static-styles-assignment",
        "obsidianmd/ui/sentence-case",
      ],
    },
  },
  {
    files: ["**/*.ts"],
    languageOptions: {
      parser: tsparser,
      parserOptions: { project: "./tsconfig.json" },
    },
  },
]);
```

3. Inform the user that the ESLint plugins were installed and configured.

### Step 3: Run TypeScript check

```bash
npx tsc --noEmit
```

Report any type errors.

### Step 4: Run eslint-plugin-obsidianmd

```bash
npx eslint src/ package.json 2>&1
```

Lint `package.json` too, not just `src/`: the recommended config runs `depend/ban-dependencies` on it (flags deprecated packages like `builtin-modules`, replaced by `node:module`'s `builtinModules`).

This covers sentence case (`ui/sentence-case`), inline styles, command rules, manifest validation, TFile/TFolder casts, forbidden elements, popout-window compatibility (`prefer-active-doc`, `prefer-window-timers`, `no-global-this`), API availability vs `minAppVersion` (`no-unsupported-api`), undescribed or forbidden `eslint-disable` directives, and more. Report all ESLint errors and warnings.

### Step 5: Manual checks (scan all .ts files in src/)

These checks catch issues NOT covered by eslint-plugin-obsidianmd. Run by reading the source code:

#### Required (blocking)

| # | Check | How to detect |
|---|-------|---------------|
| 1 | **No unnecessary type assertions** | Search for `as Type` where `??` fallback makes it redundant |
| 2 | **Promises handled** | Search for async function calls without `await`, `void`, `.catch()`, or `.then()` with rejection |
| 3 | **No async without await** | Search for `async` methods with no `await` inside |
| 4 | **No promise where void expected** | Search for async callbacks in event handlers that expect void |
| 5 | **No object stringification** | Search for template literals with `??` where left side could be an object |
| 6 | **Setting.setHeading()** | Search for `createEl('h1')`, `createEl('h2')`, `createEl('h3')` in settings/modals |

#### Optional (warnings)

| # | Check | How to detect |
|---|-------|---------------|
| 1 | **Unused imports** | TypeScript check catches these |
| 2 | **Unused variables** | TypeScript check catches these |
| 3 | **console.log in lifecycle** | Search for `console.log` in `onload()`/`onunload()` |
| 4 | **createEl helpers** | Search for `document.createElement(`, `document.createDocumentFragment(`, `createEl('span'`, `createEl('div'` -- replace with `createEl()`, `createFragment()`, `createSpan()`, `createDiv()`. Covers `obsidianmd/prefer-create-el`: the review platform enforces it, but the rule is not yet in the npm release, so local ESLint misses it |
| 5 | **Local storage** | Search for `localStorage` and `sessionStorage` -- persist plugin data with `Plugin.loadData()`/`saveData()`; for device-specific per-vault values use `App.loadLocalStorage()`/`App.saveLocalStorage()`. Raw `localStorage` is shared across all vaults on the device and `sessionStorage` does not survive a restart |

### Step 6: Check manifest.json

- `id`: alphanumeric + dashes, no "obsidian", no "plugin" suffix
- `name`: no "Obsidian", no "Plugin" suffix
- `description`: no "Obsidian", no "This plugin", must end with `. ? ! )`, under 250 chars
- All required fields present: `id`, `name`, `version`, `minAppVersion`, `description`, `author`
- `version` matches latest git tag (if any)
- `minAppVersion` covers every API the code calls (`obsidianmd/no-unsupported-api` flags APIs newer than it, e.g. `Workspace.revealLeaf` needs 1.7.2)

### Step 7: Check LICENSE

- File exists
- Copyright year is current year
- Copyright holder is not placeholder

### Step 8: Report

Output a structured report:

```
## Obsidian Lint Report

### TypeScript: [PASS/FAIL]
[errors if any]

### ESLint: [PASS/FAIL]
[errors if any]

### Required Violations: [count]
[grouped by rule, with file:line and suggested fix]

### Optional Warnings: [count]
[grouped by rule]

### Manifest: [PASS/FAIL]
[issues if any]

### License: [PASS/FAIL]
[issues if any]

---
**Result: [READY TO PUSH / FIX REQUIRED ISSUES FIRST]**
[count] required issues, [count] warnings
```

### Step 9: Offer to fix

If violations are found, ask:
1. Fix all automatically
2. Fix only required violations
3. Show me the details, I'll fix manually

For auto-fix, apply changes following the obsidian-plugin-development skill rules (move styles to CSS classes, fix sentence case, remove unnecessary assertions, void unhandled promises, etc.).
