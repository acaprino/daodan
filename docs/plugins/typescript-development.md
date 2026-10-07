# TypeScript Development Plugin

> Build production TypeScript with a hands-on engineer agent plus deep standards and mastery skills, then review it with an adversarial type-safety auditor and a 20-rule review layer. Covers architecture + implementation, Knip dead code detection, Metabase coding patterns, and enterprise-grade TypeScript with type-safe patterns, modern tooling, and framework integration.

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## Agents

### `typescript-engineer`

Hands-on TypeScript 5.x engineer. Designs architecture AND writes production code using modern tooling (pnpm/bun, Vite/tsup, Vitest, ESLint 9 flat config, Zod/Valibot). Type-safe, strict-mode, well-tested. Parallel to `python-engineer`.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Planning new TypeScript projects, designing architecture, making tech-stack decisions, implementing TS features, migrating JavaScript to TypeScript, setting up monorepos |

**Invocation:**
```
Use the typescript-engineer agent to [design/implement/migrate] [feature]
```

**Expertise:**
- Language: TS 5.10+ (const type parameters, `using` / `await using`, `satisfies`, template-literal types, discriminated unions, conditional/mapped types)
- Tooling: pnpm / bun, Vite / tsup / rollup, Vitest / Jest, ESLint 9 flat config, Biome, oxlint
- Web: Fastify / Hono / Nest 10+, React 19 SSR + RSC, tRPC for end-to-end type safety
- Data: Zod / Valibot runtime validation, Drizzle ORM / Prisma, SQLite / PostgreSQL, Redis
- Monorepo: Turborepo / Nx, pnpm workspaces, shared TS config via `tsconfig-base`
- Infra: Docker multi-stage (oven/bun or node:22-alpine), ESBuild-based production builds

**Conventions:** strict mode only (`noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`), no `any` without comment, runtime validation at boundaries, `satisfies` over annotation where inference wins, discriminated unions with exhaustive `switch` + `never` assertion, Result<T, E> pattern at module boundaries.

---

### `type-safety-auditor`

Adversarial TypeScript type-safety reviewer. Hunts type-system erosion: any leakage, unsound casts, missing runtime validation at boundaries, assertion abuse, tsconfig strictness drift, exhaustiveness gaps, and unsound generics or type guards. Dispatched by [review-plus](review-plus.md)'s code-review, team-review and pr-review variants when the target contains TypeScript files or type contracts and the relevant package has TypeScript configuration. Review Plus declares this plugin as a mandatory provider; a nonmatching codebase signal skips the dimension, while a missing matched specialist is a delivery failure. The standalone TypeScript review and [frontend-review](frontend-review.md) also use this role.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Type-safety review of TypeScript changes or codebases, strict-mode compliance audits, pre-release soundness checks |

**Invocation:**
```
Use the type-safety-auditor agent to audit [path] for type-safety issues
```

---

## Skills

### `typescript-write`

Write TypeScript and JavaScript following Metabase coding standards and best practices.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | TypeScript/JavaScript development, code refactoring, coding standards |

### `knip`

Find unused files, dependencies, exports, and types in JavaScript/TypeScript projects with Knip. Plugin system covers frameworks (React, Next.js, Vite), test runners (Vitest, Jest), and build tools.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Dead code detection, unused dependency cleanup, bundle size optimization, CI dependency hygiene |

### `mastering-typescript`

Master enterprise-grade TypeScript development with type-safe patterns, modern tooling, and framework integration. Upstream-synced from SpillwaveSolutions/mastering-typescript-skill.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | TypeScript 5.9+ development, type system fundamentals (generics, mapped types, conditional types, satisfies operator), enterprise patterns (error handling, Zod validation), React integration, NestJS APIs, LangChain.js AI apps, JavaScript migration, modern toolchain configuration (Vite 7, pnpm, ESLint, Vitest) |

**Reference files:**
| File | Content |
|------|---------|
| type-system.md | Type system fundamentals, utility types, type guards |
| generics.md | Generic patterns, constraints, inference |
| enterprise-patterns.md | Error handling, validation, architecture patterns |
| react-integration.md | Type-safe React components, hooks, state management |
| nestjs-integration.md | NestJS scalable API patterns |
| toolchain.md | Vite 7, pnpm, ESLint, Vitest configuration |

### `type-safety-rules`

20 review-oriented type-safety rules across 7 categories (any erosion, unsound casts, boundary validation, assertion abuse, compiler configuration, exhaustiveness, generics soundness), one file per rule with incorrect/correct examples and detection hints. The audit checklist of `type-safety-auditor`; also usable standalone.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Type-safety review checklists, hardening existing TypeScript, rule-by-rule guidance |

---

## Commands

### `/typescript-development:review-typescript`

Type-safety review with deterministic ground truth: detects diff vs full scope, runs `tsc --noEmit` and ESLint when available, spawns `type-safety-auditor` with the 20-rule checklist, and writes an actionable report to `.ts-review/report.md`.

Arguments: `[src-path] [--full]`

---

**Related:** [review-plus](review-plus.md) (TypeScript correctness dimension) | [senior-review](senior-review.md) (lite Knip detection and gated dead-code removal under `/senior-review:code-review --commit`) | [react-development](react-development.md) (React-specific optimization)

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `2.3.0`. **Source:** [plugin.toml](<../../plugins/typescript-development/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | None |
| Direct external | None |
| Local closure (1) | [typescript-development](<typescript-development.md>) |
| External closure (0) | None |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `shell.execute`, `repository.write`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** `execution.parallel`.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `typescript-development:knip` | Run Knip to find unused files, exports and types, with per-framework and per-test-runner plugins. TRIGGER WHEN: cleaning up TypeScript/JavaScript codebases, optimizing bundle size, or enforcing strict dependency hygiene in CI. DO NOT TRIGGER WHEN: the target is a Python codebase (use python-dead-code). | [knip](<../../plugins/typescript-development/skills/knip/SKILL.md>) |
| Skill | `typescript-development:mastering-typescript` | Deep reference for advanced TypeScript. TRIGGER WHEN: migrating JavaScript to TypeScript, bootstrapping a TS project (strict tsconfig, ESLint, Vite/Vitest, pnpm), writing generics, mapped or conditional types, `satisfies`, branded types, discriminated unions or template literal types, designing Zod schemas for runtime validation, building type-safe NestJS APIs, deep React and TypeScript typing, typing LangChain.js, or comparing TS with Java/Python enterprise approaches. DO NOT TRIGGER WHEN: routine TS/JS (use typescript-development:typescript-write), React performance (use react-development:review-react), or dead-code detection (use typescript-development:knip). | [mastering-typescript](<../../plugins/typescript-development/skills/mastering-typescript/SKILL.md>) |
| Skill | `typescript-development:type-safety-rules` | 20 rules across 7 categories, each with detection and fix guidance. TRIGGER WHEN: reviewing or hardening TypeScript against type-system erosion: `any` leakage, unsound casts, missing boundary validation, assertion abuse, tsconfig strictness, exhaustiveness and generics soundness. DO NOT TRIGGER WHEN: style and naming review (use typescript-write), or dead-code detection (use knip). | [type-safety-rules](<../../plugins/typescript-development/skills/type-safety-rules/SKILL.md>) |
| Skill | `typescript-development:typescript-write` | Apply house coding standards to everyday application work. TRIGGER WHEN: writing or reviewing TypeScript/JavaScript code, including types, generics, async patterns, module boundaries, and style conventions. DO NOT TRIGGER WHEN: React performance (use react-development), or advanced type-system depth (use mastering-typescript). | [typescript-write](<../../plugins/typescript-development/skills/typescript-write/SKILL.md>) |
| Role | `typescript-development:type-safety-auditor` | Adversarial reviewer that assumes the annotations are lying. TRIGGER WHEN: auditing TypeScript changes or codebases for type safety, `any` leakage, unsound casts, missing runtime validation at boundaries, assertion abuse, strict-mode and tsconfig drift, non-exhaustive handling, or unsound generics and type guards before a release. DO NOT TRIGGER WHEN: style and naming review (use typescript-write), React performance (use react-development:react-performance-optimizer), or dead-code detection (use knip). | [type-safety-auditor](<../../plugins/typescript-development/roles/type-safety-auditor.md>) |
| Role | `typescript-development:typescript-engineer` | Hands-on TypeScript 5.x engineer. Ships strict-mode, tested code with pnpm/bun, Vite, Vitest and Zod. TRIGGER WHEN: planning a new TS project, designing architecture, making tech-stack decisions, implementing features, migrating JavaScript to TypeScript, or setting up a monorepo. DO NOT TRIGGER WHEN: the task is React-specific performance optimization (use react-development:react-performance-optimizer). | [typescript-engineer](<../../plugins/typescript-development/roles/typescript-engineer.md>) |
| Workflow | `typescript-development:review-typescript` | Audit a codebase for type-system erosion and write a markdown report. TRIGGER WHEN: the user asks to review TypeScript for type safety, `any` leakage, unsound casts, tsconfig strictness, exhaustiveness, generics soundness, or missing runtime validation at boundaries. DO NOT TRIGGER WHEN: style review (use typescript-write), React performance (use /react-development:review-react), or dead-code detection (use knip). | [review-typescript](<../../plugins/typescript-development/workflows/review-typescript.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `typescript-development:review-typescript`

**Arguments:** `[src-path] [--full]`

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `review-typescript-completed` |
| Artifacts | `review-typescript-report` |
| Schemas | None declared |
| Declared workers | None |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [review-typescript.toml](<../../plugins/typescript-development/workflows/review-typescript.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `run` | None | None | `shared` | None declared | `preferred` |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/typescript-development](<../../exports/claude/plugins/typescript-development>) | `native` | `review-typescript: native-team` |
| copilot | [exports/copilot/plugins/typescript-development](<../../exports/copilot/plugins/typescript-development>) | `native` | `review-typescript: parallel-subagents` |
| codex | [exports/codex/plugins/typescript-development](<../../exports/codex/plugins/typescript-development>) | `adapted` | `review-typescript: parallel-subagents` |
| pi | [exports/pi/plugins/typescript-development](<../../exports/pi/plugins/typescript-development>) | `adapted` | `review-typescript: parallel-subagents` |
| opencode | [exports/opencode/plugins/typescript-development](<../../exports/opencode/plugins/typescript-development>) | `native` | `review-typescript: parallel-subagents` |

<!-- daodan:reference:end -->
