---
title: An as cast that changes the shape needs a runtime check instead
impact: CRITICAL
impactDescription: the cast asserts what only a check can know
tags: cast, as, validation
---

## An as cast that changes the shape needs a runtime check instead

**Impact: CRITICAL (the cast asserts what only a check can know)**

`value as T` tells the compiler to trust you without evidence. For data that originates outside the current module (API responses, deserialized payloads, DOM values), the honest options are a schema parse or a type guard. Reserve `as` for directions the compiler already knows are safe (widening to a supertype, `as const`).

**Incorrect (the response shape is asserted, never checked):**

```typescript
const user = (await res.json()) as User
sendEmail(user.email) // email may be missing entirely
```

**Correct (the schema proves the shape the type claims):**

```typescript
const user = UserSchema.parse(await res.json())
sendEmail(user.email)
```

**Detection:** Read casts in context; establish that an admitted runtime value lacks the claimed shape. Existing guard/converter evidence can make an assertion safe.
