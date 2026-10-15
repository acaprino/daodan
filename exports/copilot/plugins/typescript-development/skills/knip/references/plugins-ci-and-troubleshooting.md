<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

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

# Knip Plugins, CI/CD, Monorepos, and Troubleshooting

On-demand reference for `typescript-development:knip`.

## 1. Plugin System

Knip auto-detects and configures 80+ framework, test runner, and build tool plugins:

| Category | Tool | Auto-detected by | Entry Points |
|---|---|---|---|
| Framework | Next.js | `next.config.js` | `pages/`, `app/`, `middleware.ts` |
| Framework | Vite | `vite.config.ts` | `index.html`, config plugins |
| Framework | Remix | `remix.config.js` | `app/root.tsx`, `app/entry.*` |
| Framework | Astro | `astro.config.mjs` | `src/pages/`, config integrations |
| Framework | SvelteKit | `svelte.config.js` | `src/routes/`, `src/app.html` |
| Framework | Nuxt | `nuxt.config.ts` | `app.vue`, `pages/`, `layouts/` |
| Test Runner | Vitest | `vitest.config.ts` | `**/*.test.ts`, config files |
| Test Runner | Jest | `jest.config.js` | `**/*.test.js`, setup files |
| Test Runner | Playwright | `playwright.config.ts` | `tests/**/*.spec.ts` |
| Test Runner | Cypress | `cypress.config.ts` | `cypress/e2e/**/*.cy.ts` |
| Build Tool | TypeScript | `tsconfig.json` | Files in `include` |
| Build Tool | ESLint / PostCSS / Tailwind | Tool config files | Config plugins and content paths |

### Overriding Plugin Configuration

```typescript
import type { KnipConfig } from 'knip';

const config: KnipConfig = {
  eslint: false,
  prettier: false,
  vitest: {
    entry: ['vitest.config.ts', 'test/setup.ts'],
    config: ['vitest.config.ts'],
  },
  next: {
    entry: ['next.config.js', 'pages/**/*.tsx', 'app/**/*.tsx', 'middleware.ts', 'instrumentation.ts'],
  },
};

export default config;
```

## 2. Ignoring Issues and Public API Whitelists

### Config-level Ignores

```typescript
const config: KnipConfig = {
  ignore: ['legacy/**', 'vendor/**'],
  ignoreDependencies: ['@types/*', 'some-peer-dependency'],
  ignoreExportsUsedInFile: {
    interface: true,
    type: true,
  },
  ignoreWorkspaces: ['packages/deprecated/**'],
  exports: {
    include: ['src/index.ts'], // Only these exports may remain unused internally
  },
};
```

### JSDoc / Inline Directives

```typescript
/** @public */
export const publicApiFunction = () => {};

// @knip-ignore-export
export const unusedFunction = () => {};
```

## 3. Monorepo Workflows

```typescript
const config: KnipConfig = {
  workspaces: {
    '.': {
      entry: ['scripts/**/*.ts'],
      ignoreDependencies: ['@org/internal-package'],
    },
    'packages/web': {
      entry: ['src/index.ts', 'src/App.tsx'],
      ignoreDependencies: ['react', 'react-dom'],
    },
    'packages/api': {
      entry: ['src/server.ts'],
    },
  },
};
```

Run across all workspaces with `npx knip`, or scope to one workspace with `npx knip --workspace packages/web`.

## 4. CI/CD Integration

```yaml
# GitHub Actions
name: Knip
on:
  push:
    branches: [main]
  pull_request:

jobs:
  knip:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 'lts/*'
      - run: npm ci
      - run: npx knip --production --max-issues 0
```

## 5. Troubleshooting and Incremental Checks

- **False positives on side-effect imports**: set `ignoreExportsUsedInFile: true` or add side-effect modules to `entry`.
- **Inspect resolved configuration and entry points**: run `npx knip --debug`.
- **Changed files only**: run `npx knip --changed` or `npx knip --changed --base main`.
- **Memory ceiling on large monorepos**: run `NODE_OPTIONS=--max-old-space-size=4096 npx knip --include-libs false`.
- **Type-only imports**: set `includeTypeImports: true` and `types: true` in `knip.ts`.
