---
title: A non-null assertion needs an invariant justification or a fail-fast check
impact: MEDIUM
impactDescription: each unjustified ! is a deferred TypeError with no context
tags: assert, non-null
---

## A non-null assertion needs an invariant justification or a fail-fast check

**Impact: MEDIUM (each unjustified ! is a deferred TypeError with no context)**

`!` erases the compiler's warning that a value may be absent. When the invariant is real, state it in an adjacent comment. When it is not provable, replace the assertion with a check that throws a described error at the site instead of an anonymous TypeError later.

**Incorrect (the assertion hides the failure mode):**

```typescript
const user = users.get(id)!
notify(user.email) // TypeError far from the cause when id is stale
```

**Correct (fail fast with context, or justify the invariant):**

```typescript
const user = users.get(id)
if (!user) throw new Error(`unknown user id: ${id}`)
notify(user.email)
```

**Detection:** Locate non-null assertions; prove a reachable absent value and its consumer consequence. An effective invariant can be established by code, not only an adjacent comment.
