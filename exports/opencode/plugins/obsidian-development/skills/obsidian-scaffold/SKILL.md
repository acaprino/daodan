---
name: obsidian-scaffold
description: >
  Generate the layout, manifest, tsconfig, esbuild config, and a minimal class that passes automated review.
  TRIGGER WHEN: the user asks to start, create, bootstrap, scaffold, or initialize a new Obsidian community plugin.
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

# Obsidian Plugin Scaffold

Scaffold a new Obsidian community plugin project that is review-compliant from day one.

## Usage

This is a skill, not a slash command. Invoke it by asking to scaffold a new Obsidian plugin, or by its skill name `obsidian-development:obsidian-scaffold`, then answer the prompts for plugin ID, name, author, and description.

## What It Creates

```
my-plugin/
  src/
    main.ts           # Plugin class with onload/onunload
  styles.css          # Empty, scoped styles
  manifest.json       # Valid manifest (review-compliant)
  package.json        # Dependencies: obsidian, typescript, esbuild, @types/node
  tsconfig.json       # strict: true, target ES2018, moduleResolution node
  esbuild.config.mjs  # CJS bundle, externalizes obsidian + electron
  eslint.config.mjs   # eslint-plugin-obsidianmd + eslint-comments flat config
  LICENSE             # MIT with current year
  README.md           # Minimal description
  .gitignore          # node_modules, main.js, data.json
```

## Procedure

1. **Ask the user** for:
   - Plugin ID (alphanumeric + dashes, no "obsidian", no "plugin" suffix)
   - Plugin name (no "Obsidian", no "Plugin" suffix)
   - Author name
   - Description (no "Obsidian", no "This plugin", must end with `. ? ! )`, under 250 chars)
   - Author URL (optional)
   - Desktop only? (default: false)

2. **Validate inputs** against Obsidian automated review rules:
   - ID: `/^[a-z0-9-]+$/`, not containing "obsidian", not ending with "plugin"
   - Name: not containing "Obsidian", not ending with "Plugin"
   - Description: not starting with "This plugin", not containing "Obsidian", ending with `.?!)`

3. **Create all files** using the templates below.

4. **Run** `npm install` to install dependencies.

5. **Verify** `npx tsc --noEmit` passes with zero errors.

## Templates

### manifest.json
```json
{
  "id": "{{ID}}",
  "name": "{{NAME}}",
  "version": "1.0.0",
  "minAppVersion": "1.0.0",
  "description": "{{DESCRIPTION}}",
  "author": "{{AUTHOR}}",
  "authorUrl": "{{AUTHOR_URL}}",
  "isDesktopOnly": {{IS_DESKTOP_ONLY}}
}
```

### package.json
```json
{
  "name": "{{ID}}",
  "version": "1.0.0",
  "description": "{{DESCRIPTION}}",
  "main": "main.js",
  "scripts": {
    "dev": "node esbuild.config.mjs",
    "build": "tsc -noEmit -skipLibCheck && node esbuild.config.mjs production",
    "lint": "eslint src/ package.json"
  },
  "devDependencies": {
    "@eslint-community/eslint-plugin-eslint-comments": "^4.0.0",
    "@eslint/js": "^9.0.0",
    "@types/node": "^22.0.0",
    "esbuild": "^0.24.0",
    "eslint": "^9.0.0",
    "eslint-plugin-obsidianmd": "latest",
    "obsidian": "latest",
    "typescript": "^5.5.0",
    "typescript-eslint": "^8.0.0"
  }
}
```

### tsconfig.json
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "inlineSourceMap": true,
    "inlineSources": true,
    "module": "ESNext",
    "target": "ES2018",
    "allowJs": true,
    "noImplicitAny": true,
    "moduleResolution": "node",
    "importHelpers": true,
    "isolatedModules": true,
    "strictNullChecks": true,
    "strict": true,
    "lib": ["DOM", "ES2018", "ES2021.String"]
  },
  "include": ["src/**/*.ts"]
}
```

### esbuild.config.mjs
```javascript
import esbuild from "esbuild";
import process from "process";
import { builtinModules as builtins } from "node:module";

const prod = process.argv[2] === "production";

esbuild.build({
  entryPoints: ["src/main.ts"],
  bundle: true,
  external: [
    "obsidian",
    "electron",
    "@codemirror/autocomplete",
    "@codemirror/collab",
    "@codemirror/commands",
    "@codemirror/language",
    "@codemirror/lint",
    "@codemirror/search",
    "@codemirror/state",
    "@codemirror/view",
    "@lezer/common",
    "@lezer/highlight",
    "@lezer/lr",
    ...builtins,
  ],
  format: "cjs",
  target: "es2018",
  logLevel: "info",
  sourcemap: prod ? false : "inline",
  treeShaking: true,
  outfile: "main.js",
  minify: prod,
}).catch(() => process.exit(1));
```

### src/main.ts
```typescript
import { Plugin } from 'obsidian';

export default class {{CLASS_NAME}} extends Plugin {
  onload(): void {
    // Plugin initialization here
  }

  onunload(): void {
    // Cleanup here (Obsidian handles leaf detachment automatically)
  }
}
```

### .gitignore
```
node_modules/
main.js
data.json
```

### eslint.config.mjs (ESLint 9+ flat config)

The eslint-comments block mirrors checks that Obsidian's review platform adds on top of the obsidianmd recommended config.

```javascript
import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import obsidianmd from 'eslint-plugin-obsidianmd';
import comments from '@eslint-community/eslint-plugin-eslint-comments/configs';

export default [
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...obsidianmd.configs.recommended,
  comments.recommended,
  {
    rules: {
      '@eslint-community/eslint-comments/require-description': 'error',
      '@eslint-community/eslint-comments/no-restricted-disable': [
        'error',
        'obsidianmd/no-static-styles-assignment',
        'obsidianmd/ui/sentence-case',
      ],
    },
  },
  {
    languageOptions: {
      parserOptions: {
        project: './tsconfig.json',
      },
    },
  },
];
```

## Post-Scaffold

After creation, remind the user:
- Run `npm run dev` for watch mode during development
- Run `npm run build` for production build
- Run `npm run lint` to check against the automated review rules locally
- Create a GitHub release with `main.js`, `manifest.json`, and `styles.css` as individual assets
- Release tag must match version in manifest.json exactly (no `v` prefix)
- Submit the new plugin on community.obsidian.md: sign in with an Obsidian account, link GitHub, then "Plugins" > "New plugin" with the repo URL. The old PR workflow to `obsidianmd/obsidian-releases` was retired in May 2026
- Updates need no dashboard action: every new GitHub release is scanned automatically by the review system
