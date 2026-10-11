---
name: typescript-write
description: >
  Apply house coding standards to everyday application work.
  TRIGGER WHEN: writing or reviewing TypeScript/JavaScript code, including types, generics, async patterns, module boundaries, and style conventions.
  DO NOT TRIGGER WHEN: React performance (use react-development), or advanced type-system depth (use mastering-typescript).
---

<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
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

# TypeScript/JavaScript Development Skill

## When to Invoke

- Writing new TypeScript or JavaScript files
- Refactoring existing TS/JS code
- Reviewing code for type safety and best practices
- Converting JavaScript to TypeScript
- Designing module APIs and type interfaces
- Fixing type errors or improving type coverage

## Code Style

### Naming Conventions
- `camelCase` for variables, functions, parameters
- `PascalCase` for types, interfaces, classes, enums, React components
- `UPPER_SNAKE_CASE` for constants and enum members
- Prefix interfaces with `I` only if project convention requires it - otherwise plain `PascalCase`
- Boolean variables: use `is`, `has`, `should`, `can` prefixes (`isLoading`, `hasPermission`)
- Event handlers: `handleClick`, `onSubmit` pattern

### File Organization
- One primary export per file when possible
- Group related types with their implementation
- Barrel exports (`index.ts`) for public module APIs only - avoid deep barrel re-exports
- File naming: `kebab-case.ts` for utilities, `PascalCase.tsx` for React components

### Import Ordering
1. Node built-in modules (`node:fs`, `node:path`)
2. External packages (`react`, `lodash`)
3. Internal aliases (`@/utils`, `@/components`)
4. Relative imports (`./helpers`, `../types`)
5. Type-only imports (`import type { Foo }`)
- Blank line between each group

## TypeScript Patterns

### Strict Mode
- Enable `strict: true` in `tsconfig.json` - never disable individual strict checks
- No `// @ts-ignore` or `// @ts-expect-error` without an explanatory comment
- Prefer `unknown` over `any` - narrow with type guards

### Proper Typing
- Avoid `any` - use `unknown` and narrow, or define a proper type
- Prefer `interface` for object shapes that may be extended
- Prefer `type` for unions, intersections, mapped types, and utility types
- Use `readonly` for properties that should not be mutated
- Use `as const` for literal type inference on objects and arrays

### Discriminated Unions
```typescript
type Result<T> =
  | { success: true; data: T }
  | { success: false; error: Error };

function handle<T>(result: Result<T>) {
  if (result.success) {
    // result.data is T here
    return result.data;
  }
  // result.error is Error here
  throw result.error;
}
```

### Type Guards
```typescript
// User-defined type guard
function isString(value: unknown): value is string {
  return typeof value === "string";
}

// Assertion function
function assertDefined<T>(value: T | undefined, name: string): asserts value is T {
  if (value === undefined) {
    throw new Error(`Expected ${name} to be defined`);
  }
}
```

### Generic Constraints
```typescript
// Constrain generics to what you actually need
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

// Use defaults for common cases
type ApiResponse<T = unknown> = {
  data: T;
  status: number;
  timestamp: string;
};
```

### Utility Types
- `Partial<T>` - all properties optional (use for update/patch operations)
- `Required<T>` - all properties required
- `Pick<T, K>` - select subset of properties
- `Omit<T, K>` - exclude properties
- `Record<K, V>` - typed key-value map
- `Extract<T, U>` / `Exclude<T, U>` - filter union members
- Prefer built-in utility types over manual type manipulation

### Enums vs Union Types
- Prefer string union types for simple sets: `type Status = "active" | "inactive"`
- Use `const enum` only if you need numeric values and tree-shaking
- Use regular `enum` when you need runtime reverse mapping or iteration

## React Patterns

### Component Typing
```typescript
// Function components - type props inline or with interface
interface ButtonProps {
  label: string;
  variant?: "primary" | "secondary";
  onClick: () => void;
  children?: React.ReactNode;
}

function Button({ label, variant = "primary", onClick, children }: ButtonProps) {
  return <button className={variant} onClick={onClick}>{children ?? label}</button>;
}
```

### Hooks Rules
- Call hooks at the top level only - never inside conditions, loops, or nested functions
- Custom hooks must start with `use` prefix
- Specify dependency arrays accurately - never suppress exhaustive-deps lint
- Use `useCallback` for functions passed as props to memoized children
- Use `useMemo` for expensive computations - not for every variable

### State Management
- Colocate state as close to where it is used as possible
- Lift state up only when siblings need to share it
- Use `useReducer` for complex state with multiple sub-values or transitions
- Context for truly global state (theme, auth, locale) - not for frequently changing data

### Event Handling
```typescript
// Type event handlers properly
function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
  setValue(e.target.value);
}

function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
  e.preventDefault();
  // ...
}
```

## Testing

### File Naming
- Test files: `*.test.ts` or `*.spec.ts` alongside the source file
- Or in `__tests__/` directory mirroring the source structure
- Test utilities: `test-utils.ts` or `testing/` directory

### Test Structure
```typescript
describe("calculateTotal", () => {
  it("returns 0 for empty cart", () => {
    expect(calculateTotal([])).toBe(0);
  });

  it("sums item prices with quantities", () => {
    const items = [
      { price: 10, quantity: 2 },
      { price: 5, quantity: 1 },
    ];
    expect(calculateTotal(items)).toBe(25);
  });

  it("throws for negative quantities", () => {
    expect(() => calculateTotal([{ price: 10, quantity: -1 }])).toThrow();
  });
});
```

### Assertion Patterns
- Use `toBe` for primitives, `toEqual` for objects/arrays
- Use `toThrow` for error cases - wrap in arrow function
- Use `toHaveBeenCalledWith` for spy/mock assertions
- Prefer specific matchers over generic `toBeTruthy`/`toBeFalsy`
- Type test fixtures and mocks - avoid `as any` in tests

### Mocking
- Mock external dependencies, not internal implementation
- Use `vi.fn()` (Vitest) or `jest.fn()` for function mocks
- Use `vi.spyOn` / `jest.spyOn` to mock methods while preserving type safety
- Reset mocks in `beforeEach` or use `afterEach(() => vi.restoreAllMocks())`

## Common Anti-Patterns

### Using `any` Instead of Proper Types
```typescript
// BAD
function parse(data: any) { return data.name; }

// GOOD
function parse(data: unknown): string {
  if (typeof data === "object" && data !== null && "name" in data) {
    return String((data as { name: unknown }).name);
  }
  throw new Error("Invalid data");
}
```

### Non-Null Assertion Overuse
```typescript
// BAD
const name = user!.name!;

// GOOD
if (!user?.name) throw new Error("User name required");
const name = user.name;
```

### Barrel File Performance Issues
```typescript
// BAD - importing everything through deep barrel
import { Button } from "@/components";  // pulls entire component tree

// GOOD - direct import
import { Button } from "@/components/Button";
```

### Ignoring Return Types
```typescript
// BAD - return type inferred as complex union
function getData(id: string) {
  if (!id) return null;
  return fetch(`/api/${id}`).then(r => r.json());
}

// GOOD - explicit return type
async function getData(id: string): Promise<ApiResponse | null> {
  if (!id) return null;
  const r = await fetch(`/api/${id}`);
  return r.json() as Promise<ApiResponse>;
}
```

### Mutating Function Parameters
```typescript
// BAD
function addItem(items: Item[], item: Item) {
  items.push(item);  // mutates input
  return items;
}

// GOOD
function addItem(items: readonly Item[], item: Item): Item[] {
  return [...items, item];
}
```

## Error Handling

### Result Pattern
```typescript
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

async function fetchUser(id: string): Promise<Result<User>> {
  try {
    const res = await fetch(`/api/users/${id}`);
    if (!res.ok) return { ok: false, error: new Error(`HTTP ${res.status}`) };
    const user = await res.json();
    return { ok: true, value: user };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e : new Error(String(e)) };
  }
}
```

### Async Error Handling
- Always `try/catch` around `await` calls that can fail
- Never use `.catch()` and `await` on the same promise chain
- Prefer returning error results over throwing in library code
- Throw only for programmer errors (assertion failures, invariant violations)
- Log errors at the boundary, not at every level

### Error Boundaries (React)
- Wrap major UI sections in error boundaries
- Provide meaningful fallback UI - not blank screens
- Log errors to monitoring service in `componentDidCatch`
- Reset error boundary state on navigation changes

### Typed Errors
```typescript
class NotFoundError extends Error {
  readonly code = "NOT_FOUND" as const;
  constructor(resource: string, id: string) {
    super(`${resource} ${id} not found`);
    this.name = "NotFoundError";
  }
}

class ValidationError extends Error {
  readonly code = "VALIDATION" as const;
  constructor(public readonly fields: Record<string, string>) {
    super("Validation failed");
    this.name = "ValidationError";
  }
}
```
