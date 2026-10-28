---
name: knip
description: >
  Run Knip to find unused files, dependencies, exports and types in TypeScript and JavaScript projects.
  TRIGGER WHEN: cleaning up TypeScript/JavaScript dead code, finding unused npm dependencies or exports, or configuring knip.json/knip.ts.
  DO NOT TRIGGER WHEN: the target is a Python codebase (use python-dead-code).
---

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

# Knip Dead Code Detection

Knip finds unused files, dependencies, exports, types, and enum/class members across JavaScript and TypeScript repositories (including monorepos), backed by 80+ framework and tool plugins.

## Reference router

| Task | Reference |
|---|---|
| Framework/test-runner plugin overrides, monorepo workspace config, JSDoc/`@public` ignores, CI pipelines, or troubleshooting false positives | `references/plugins-ci-and-troubleshooting.md` |

## 1. Installation and CLI Usage

> Examples use `npx`; equivalent commands work with `pnpm dlx`, `bunx`, or `yarn dlx`.

```bash
npm install --save-dev knip

# Scan entire project
npx knip

# Focused scans
npx knip --dependencies
npx knip --exports
npx knip --files

# Production mode (production entry points and dependencies only)
npx knip --production

# Exclude exports used within the same file
npx knip --exclude-exports-used-in-file

# Machine-readable JSON output or config debugging
npx knip --reporter json
npx knip --debug
```

## 2. Configuration

Knip works zero-config on standard projects by reading `package.json` (`main`, `exports`, `bin`, `scripts`) and framework/test configs (`next.config.*`, `vite.config.*`, `vitest.config.*`, `tsconfig.json`).

### `knip.json` or `knip.ts` (Explicit Configuration)

```typescript
// knip.ts
import type { KnipConfig } from 'knip';

const config: KnipConfig = {
  entry: ['src/index.ts', 'src/cli.ts', 'scripts/**/*.ts'],
  project: ['src/**/*.{ts,tsx}', 'scripts/**/*.ts'],
  ignore: [
    '**/*.test.ts',
    '**/*.spec.ts',
    '**/__tests__/**',
    '**/__mocks__/**',
    'dist/**',
    'build/**',
    'coverage/**',
    '.next/**',
  ],
  ignoreDependencies: [
    '@types/*',
    'typescript',
    'tslib',
  ],
  ignoreBinaries: ['npm-check-updates', 'semantic-release'],
  ignoreExportsUsedInFile: true,
};

export default config;
```

## 3. Interpreting Results and Adoption Order

| Issue Type | Meaning | Action |
|---|---|---|
| Unused file | File not reachable from any entry point | Delete file or add to `entry` |
| Unused dependency | Package in `package.json` never imported | Remove from `package.json` |
| Unused export | Exported value never imported externally | Remove `export` keyword or delete |
| Unused type | Exported type/interface never imported | Make internal or delete |
| Unused enum/class member | Member never referenced | Remove member |
| Duplicate export | Same symbol re-exported multiple ways | Consolidate exports |

Recommended adoption sequence on an existing codebase:
1. `npx knip --dependencies --max-issues 0` (highest signal, lowest false-positive rate)
2. `npx knip --exports --exclude-exports-used-in-file`
3. `npx knip --files` and full `npx knip --production`
