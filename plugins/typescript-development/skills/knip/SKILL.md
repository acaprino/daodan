---
name: knip
description: >
  Run Knip to find unused files, dependencies, exports and types in TypeScript and JavaScript projects.
  TRIGGER WHEN: cleaning up TypeScript/JavaScript dead code, finding unused npm dependencies or exports, or configuring knip.json/knip.ts.
  DO NOT TRIGGER WHEN: the target is a Python codebase (use python-dead-code).
---

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
