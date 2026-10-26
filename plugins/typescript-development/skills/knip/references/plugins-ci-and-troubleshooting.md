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
