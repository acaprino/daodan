---
title: strict true is the baseline
impact: HIGH
impactDescription: without it every other type-safety rule is advisory
tags: config, strict
---

## strict true is the baseline

**Impact: HIGH (without it every other type-safety rule is advisory)**

`"strict": true` enables the checks the rest of this rule set assumes: `strictNullChecks`, `noImplicitAny`, `strictFunctionTypes`, `useUnknownInCatchVariables`, and the rest of the family. A codebase without it has null-safety and implicit-any holes everywhere the annotations look fine.

**Incorrect (defaults leave the compiler permissive):**

```json
{ "compilerOptions": { "target": "ES2022" } }
```

**Correct (strict on, gaps opted out locally and visibly if truly needed):**

```json
{ "compilerOptions": { "target": "ES2022", "strict": true } }
```

**Detection:** Resolve tsconfig and every inherited override. Disabled strict checks are leads; establish a reachable unsafe program or violated explicit configuration contract. An absent local flag may be inherited.
