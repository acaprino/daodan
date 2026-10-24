---
name: type-safety-rules
description: >
  20 rules across 7 categories, each with detection and fix guidance.
  TRIGGER WHEN: reviewing or hardening TypeScript against type-system erosion: `any` leakage, unsound casts, missing boundary validation, assertion abuse, tsconfig strictness, exhaustiveness and generics soundness.
  DO NOT TRIGGER WHEN: style and naming review (use typescript-write), or dead-code detection (use knip).
---

# TypeScript Type-Safety Rules

Review-oriented rule set for hunting type-system erosion in TypeScript codebases. 20 rules across 7 categories, prioritized by blast radius. Used as the audit checklist by the `type-safety-auditor` agent and usable standalone while writing or hardening TypeScript.

## Review evidence

Rule examples, grep hits and priority labels nominate candidates. Promote only a reachable type/runtime mismatch or a violated explicit project contract, after checking equivalent guards and effective inherited configuration. Missing preferred syntax, schema library or config flag alone is not a defect. Use impact-based severity and the caller’s report; no universal score. See [TypeScript configuration inheritance](https://www.typescriptlang.org/tsconfig/#extends).

## Rule Categories by Priority

| Priority | Category | Impact | Prefix |
|----------|----------|--------|--------|
| 1 | Any Erosion | CRITICAL | `any-` |
| 2 | Unsound Casts | CRITICAL | `cast-` |
| 3 | Boundary Validation | CRITICAL | `boundary-` |
| 4 | Assertion Abuse | HIGH | `assert-` |
| 5 | Compiler Configuration | HIGH | `config-` |
| 6 | Exhaustiveness | MEDIUM-HIGH | `exhaust-` |
| 7 | Generics Soundness | MEDIUM | `generics-` |

## Quick Reference

### 1. Any Erosion (CRITICAL)

- `any-explicit` - Replace explicit `any` with `unknown` plus narrowing
- `any-implicit-boundary` - Type the results of `JSON.parse`, `response.json()`, and `catch` immediately
- `any-generic-default` - Never default a type parameter to `any`

### 2. Unsound Casts (CRITICAL)

- `cast-as-unsound` - An `as` cast that changes the shape needs a runtime check instead
- `cast-double` - `as unknown as X` is a type-system bypass; write a guard or converter
- `cast-const-assertion` - Use `as const` for literal narrowing instead of widening annotations

### 3. Boundary Validation (CRITICAL)

- `boundary-http` - Parse HTTP payloads with a schema at the edge
- `boundary-queue` - Validate queue and event messages before processing
- `boundary-storage` - Validate and version storage reads (localStorage, files, DB JSON)
- `boundary-env` - Access environment variables through one validated config module

### 4. Assertion Abuse (HIGH)

- `assert-non-null` - `!` needs an adjacent invariant justification or a fail-fast check
- `assert-ts-expect-error` - Use `@ts-expect-error` with a reason, never `@ts-ignore`

### 5. Compiler Configuration (HIGH)

- `config-strict` - `"strict": true` is the baseline
- `config-unchecked-index` - Enable `noUncheckedIndexedAccess`
- `config-exact-optional` - Enable `exactOptionalPropertyTypes`
- `config-skiplibcheck` - `skipLibCheck` may speed up third-party types, never hide first-party errors

### 6. Exhaustiveness (MEDIUM-HIGH)

- `exhaust-switch-never` - Discriminated unions get a `never` assertion in the default branch
- `exhaust-satisfies-record` - Use `satisfies Record<K, V>` for complete lookup tables

### 7. Generics Soundness (MEDIUM)

- `generics-constraint` - Constrain type parameters on public APIs
- `generics-type-guards` - A type predicate must verify the whole shape it claims

## How to Use

Read individual rule files in the `rules/` directory for detailed explanations and code examples. Each rule file contains a brief explanation, an incorrect example, a correct example, and a detection hint for reviewers.

## Load map

| Read | When |
|------|------|
| `rules/<rule-id>.md` | Confirming or fixing one rule's violation |
| `references/audit.md` | Running the type-safety audit as a procedure (the TypeScript stack audit of `/daodan:check-health`): scope detection, tsc and ESLint ground truth, the isolated `type-safety-auditor` review and the scored report under the run directory |
