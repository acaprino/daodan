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

<!-- Source: SpillwaveSolutions/mastering-typescript-skill - mastering-typescript/references/toolchain.md -->
# Modern Toolchain Reference

> **Load when:** User asks about Vite, pnpm, ESLint, Vitest, tsconfig, build tools, or project configuration.

Modern TypeScript toolchain configuration for 2025.

## Contents

- [TypeScript Configuration](#typescript-configuration)
- [Package Manager (pnpm)](#package-manager-pnpm)
- [Build Tool (Vite)](#build-tool-vite)
- [Linting (ESLint 9)](#linting-eslint-9)
- [Testing (Vitest)](#testing-vitest)
- [Formatting (Prettier)](#formatting-prettier)

---

## TypeScript Configuration

### Strict Enterprise Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    // Language and Environment
    "target": "ES2024",
    "lib": ["ES2024"],
    "module": "ESNext",
    "moduleResolution": "bundler",

    // Strict Type Checking
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,

    // Module Handling
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "isolatedModules": true,
    "verbatimModuleSyntax": true,

    // Output
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "./dist",
    "rootDir": "./src",

    // Path Aliases
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    },

    // Performance
    "skipLibCheck": true,
    "incremental": true,
    "tsBuildInfoFile": "./node_modules/.cache/tsbuildinfo"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

### React Project Configuration

```json
// tsconfig.json for React
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",

    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,

    "esModuleInterop": true,
    "isolatedModules": true,
    "skipLibCheck": true,

    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@components/*": ["./src/components/*"],
      "@hooks/*": ["./src/hooks/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### Node.js Backend Configuration

```json
// tsconfig.json for Node.js/NestJS
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],

    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,

    "esModuleInterop": true,
    "isolatedModules": true,
    "skipLibCheck": true,

    "outDir": "./dist",
    "rootDir": "./src",
    "declaration": true,
    "sourceMap": true,

    "experimentalDecorators": true,
    "emitDecoratorMetadata": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.spec.ts"]
}
```

---

## Package Manager (pnpm)

### Why pnpm

| Feature | npm | pnpm |
|---------|-----|------|
| Disk usage | Duplicates packages | Shared store, symlinks |
| Install speed | Slower | 2-3x faster |
| Strictness | Allows phantom deps | Strict by default |
| Monorepo support | Basic workspaces | First-class support |

### Basic Commands

```bash
# Install dependencies
pnpm install

# Add packages
pnpm add typescript
pnpm add -D vitest @types/node

# Run scripts
pnpm run build
pnpm test

# Update packages
pnpm update
pnpm update --interactive

# List packages
pnpm list
pnpm why lodash

# Clean install
pnpm install --frozen-lockfile
```

### Workspace Configuration

```yaml
# pnpm-workspace.yaml
packages:
  - 'packages/*'
  - 'apps/*'
```

```json
// package.json (root)
{
  "name": "my-monorepo",
  "private": true,
  "scripts": {
    "build": "pnpm -r run build",
    "test": "pnpm -r run test",
    "lint": "pnpm -r run lint"
  }
}
```

---

## Build Tool (Vite)

### Vite Configuration

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tsconfigPaths from 'vite-tsconfig-paths';

export default defineConfig({
  plugins: [
    react(),
    tsconfigPaths()
  ],
  server: {
    port: 3000,
    host: true
  },
  build: {
    target: 'es2022',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          utils: ['lodash-es', 'date-fns']
        }
      }
    }
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts']
  }
});
```

### Library Mode

```typescript
// vite.config.ts for library
import { defineConfig } from 'vite';
import dts from 'vite-plugin-dts';

export default defineConfig({
  build: {
    lib: {
      entry: './src/index.ts',
      name: 'MyLibrary',
      fileName: 'my-library',
      formats: ['es', 'cjs']
    },
    rollupOptions: {
      external: ['react', 'react-dom'],
      output: {
        globals: {
          react: 'React',
          'react-dom': 'ReactDOM'
        }
      }
    }
  },
  plugins: [
    dts({ insertTypesEntry: true })
  ]
});
```

---

## Linting (ESLint 9)

### Flat Config Format

```javascript
// eslint.config.js
import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactPlugin from 'eslint-plugin-react';
import reactHooksPlugin from 'eslint-plugin-react-hooks';

export default tseslint.config(
  // Base ESLint recommendations
  eslint.configs.recommended,

  // TypeScript strict type-checking
  ...tseslint.configs.strictTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,

  // TypeScript parser options
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname
      }
    }
  },

  // React configuration
  {
    files: ['**/*.tsx'],
    plugins: {
      react: reactPlugin,
      'react-hooks': reactHooksPlugin
    },
    rules: {
      ...reactPlugin.configs.recommended.rules,
      ...reactHooksPlugin.configs.recommended.rules,
      'react/react-in-jsx-scope': 'off'
    },
    settings: {
      react: { version: 'detect' }
    }
  },

  // Custom rules
  {
    rules: {
      '@typescript-eslint/no-unused-vars': ['error', {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_'
      }],
      '@typescript-eslint/consistent-type-imports': ['error', {
        prefer: 'type-imports'
      }],
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/await-thenable': 'error'
    }
  },

  // Ignore patterns
  {
    ignores: ['dist/**', 'node_modules/**', '*.config.js']
  }
);
```

### Common Rules Explained

```javascript
// Important TypeScript ESLint rules
{
  rules: {
    // Enforce type imports for better tree-shaking
    '@typescript-eslint/consistent-type-imports': 'error',

    // Prevent unhandled promises
    '@typescript-eslint/no-floating-promises': 'error',
    '@typescript-eslint/no-misused-promises': 'error',

    // Prevent awaiting non-promises
    '@typescript-eslint/await-thenable': 'error',

    // Require return types on functions
    '@typescript-eslint/explicit-function-return-type': ['error', {
      allowExpressions: true
    }],

    // Prefer nullish coalescing
    '@typescript-eslint/prefer-nullish-coalescing': 'error',

    // Prefer optional chaining
    '@typescript-eslint/prefer-optional-chain': 'error',

    // No any type
    '@typescript-eslint/no-explicit-any': 'error',

    // Enforce strict boolean expressions
    '@typescript-eslint/strict-boolean-expressions': 'error'
  }
}
```

---

## Testing (Vitest)

### Vitest Configuration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import tsconfigPaths from 'vite-tsconfig-paths';

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['**/*.d.ts', '**/*.config.*', '**/test/**']
    },
    typecheck: {
      enabled: true
    }
  }
});
```

### Test Setup

```typescript
// src/test/setup.ts
import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeAll, afterAll, vi } from 'vitest';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock environment variables
beforeAll(() => {
  vi.stubEnv('API_URL', 'http://localhost:3000');
});

afterAll(() => {
  vi.unstubAllEnvs();
});
```

### Example Tests

```typescript
// src/utils/format.test.ts
import { describe, it, expect } from 'vitest';
import { formatCurrency, formatDate } from './format';

describe('formatCurrency', () => {
  it('formats USD correctly', () => {
    expect(formatCurrency(1234.56, 'USD')).toBe('$1,234.56');
  });

  it('handles zero', () => {
    expect(formatCurrency(0, 'USD')).toBe('$0.00');
  });
});

// src/components/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Button } from './Button';

describe('Button', () => {
  it('renders with label', () => {
    render(<Button label="Click me" onClick={() => {}} />);
    expect(screen.getByRole('button')).toHaveTextContent('Click me');
  });

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<Button label="Click" onClick={handleClick} />);

    fireEvent.click(screen.getByRole('button'));

    expect(handleClick).toHaveBeenCalledOnce();
  });
});
```

---

## Formatting (Prettier)

### Prettier Configuration

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "bracketSpacing": true,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

### Integration with ESLint

```javascript
// eslint.config.js
import eslintConfigPrettier from 'eslint-config-prettier';

export default tseslint.config(
  // ... other configs
  eslintConfigPrettier // Must be last to disable conflicting rules
);
```

### Package Scripts

```json
// package.json
{
  "scripts": {
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "lint": "eslint .",
    "lint:fix": "eslint --fix .",
    "typecheck": "tsc --noEmit"
  }
}
```

---

## Complete Project Setup

### Quick Start Script

```bash
#!/bin/bash
# setup-ts-project.sh

PROJECT_NAME=${1:-my-app}

# Create project with Vite
pnpm create vite@latest $PROJECT_NAME --template react-ts
cd $PROJECT_NAME

# Install dependencies
pnpm install

# Add development dependencies
pnpm add -D \
  typescript-eslint \
  @eslint/js \
  eslint-plugin-react \
  eslint-plugin-react-hooks \
  eslint-config-prettier \
  prettier \
  vitest \
  @vitest/coverage-v8 \
  @testing-library/react \
  @testing-library/jest-dom \
  vite-tsconfig-paths

echo "Project setup complete! Run: cd $PROJECT_NAME && pnpm dev"
```
