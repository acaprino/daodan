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
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
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

<!-- Source: SpillwaveSolutions/mastering-typescript-skill - mastering-typescript/references/generics.md -->
# Generics Reference

> **Load when:** User asks about generics, mapped types, conditional types, template literal types, or reusable type patterns.

Advanced generics and type-level programming patterns.

## Contents

- [Generic Fundamentals](#generic-fundamentals)
- [Generic Constraints](#generic-constraints)
- [Mapped Types](#mapped-types)
- [Conditional Types](#conditional-types)
- [Template Literal Types](#template-literal-types)
- [Variadic Tuple Types](#variadic-tuple-types)

---

## Generic Fundamentals

### Basic Generic Function

```typescript
// Type parameter T can be any type
function identity<T>(value: T): T {
  return value;
}

const str = identity("hello");   // string
const num = identity(42);        // number
const obj = identity({ x: 1 });  // { x: number }

// Explicit type argument (rarely needed)
const explicit = identity<string>("hello");
```

### Generic Interfaces

```typescript
interface Container<T> {
  value: T;
  getValue(): T;
  setValue(value: T): void;
}

interface Repository<T, ID = string> {
  findById(id: ID): Promise<T | null>;
  findAll(): Promise<T[]>;
  save(entity: T): Promise<T>;
  delete(id: ID): Promise<boolean>;
}

// Implementation
class UserRepository implements Repository<User> {
  async findById(id: string): Promise<User | null> {
    // implementation
  }
  // ... other methods
}
```

### Generic Classes

```typescript
class Stack<T> {
  private items: T[] = [];

  push(item: T): void {
    this.items.push(item);
  }

  pop(): T | undefined {
    return this.items.pop();
  }

  peek(): T | undefined {
    return this.items[this.items.length - 1];
  }

  isEmpty(): boolean {
    return this.items.length === 0;
  }
}

const numberStack = new Stack<number>();
numberStack.push(1);
numberStack.push(2);
const top = numberStack.pop(); // number | undefined
```

---

## Generic Constraints

### extends Constraint

```typescript
// T must have a length property
interface HasLength {
  length: number;
}

function logLength<T extends HasLength>(item: T): T {
  console.log(`Length: ${item.length}`);
  return item;
}

logLength("hello");        // OK: string has length
logLength([1, 2, 3]);      // OK: array has length
logLength({ length: 10 }); // OK: object has length
logLength(42);             // Error: number has no length
```

### keyof Constraint

```typescript
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

interface Person {
  name: string;
  age: number;
}

const person: Person = { name: "Alice", age: 30 };

const name = getProperty(person, "name"); // string
const age = getProperty(person, "age");   // number
const bad = getProperty(person, "email"); // Error: "email" not in Person
```

### Multiple Constraints

```typescript
interface Printable {
  print(): void;
}

interface Loggable {
  log(): string;
}

// T must satisfy both interfaces
function process<T extends Printable & Loggable>(item: T): void {
  item.print();
  console.log(item.log());
}
```

### Default Type Parameters

```typescript
interface ApiResponse<T = unknown, E = Error> {
  data?: T;
  error?: E;
  status: number;
}

// Uses defaults
const response1: ApiResponse = { status: 200 };

// Override data type only
const response2: ApiResponse<User> = { data: user, status: 200 };

// Override both
const response3: ApiResponse<User, ValidationError> = {
  error: new ValidationError(),
  status: 400
};
```

---

## Mapped Types

### Basic Mapped Types

```typescript
// Transform all properties to optional
type Partial<T> = {
  [K in keyof T]?: T[K];
};

// Transform all properties to required
type Required<T> = {
  [K in keyof T]-?: T[K];
};

// Transform all properties to readonly
type Readonly<T> = {
  readonly [K in keyof T]: T[K];
};

// Remove readonly modifier
type Mutable<T> = {
  -readonly [K in keyof T]: T[K];
};
```

### Practical Mapped Types

```typescript
// Make all properties nullable
type Nullable<T> = {
  [K in keyof T]: T[K] | null;
};

// Make all properties async getters
type AsyncGetters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => Promise<T[K]>;
};

interface User {
  name: string;
  email: string;
}

type UserGetters = AsyncGetters<User>;
// {
//   getName: () => Promise<string>;
//   getEmail: () => Promise<string>;
// }
```

### Key Remapping (as clause)

```typescript
// Filter keys by type
type FilterByType<T, U> = {
  [K in keyof T as T[K] extends U ? K : never]: T[K];
};

interface Mixed {
  name: string;
  age: number;
  active: boolean;
  score: number;
}

type StringProps = FilterByType<Mixed, string>;
// { name: string }

type NumberProps = FilterByType<Mixed, number>;
// { age: number; score: number }

// Prefix all keys
type Prefixed<T, P extends string> = {
  [K in keyof T as `${P}${Capitalize<string & K>}`]: T[K];
};

type PrefixedUser = Prefixed<User, "user">;
// { userName: string; userEmail: string }
```

---

## Conditional Types

### Basic Conditional Types

```typescript
// T extends U ? X : Y
type IsString<T> = T extends string ? true : false;

type A = IsString<string>;  // true
type B = IsString<number>;  // false
type C = IsString<"hello">; // true

// Practical: Extract non-nullable type
type NonNullable<T> = T extends null | undefined ? never : T;

type D = NonNullable<string | null>;     // string
type E = NonNullable<number | undefined>; // number
```

### Distributive Conditional Types

```typescript
// Conditional types distribute over unions
type ToArray<T> = T extends unknown ? T[] : never;

type StringOrNumberArray = ToArray<string | number>;
// string[] | number[] (not (string | number)[])

// Prevent distribution with tuple
type ToArrayNonDist<T> = [T] extends [unknown] ? T[] : never;

type Mixed = ToArrayNonDist<string | number>;
// (string | number)[]
```

### infer Keyword

```typescript
// Extract return type
type ReturnType<T> = T extends (...args: any[]) => infer R ? R : never;

type FnReturn = ReturnType<() => string>; // string

// Extract array element type
type ArrayElement<T> = T extends (infer E)[] ? E : never;

type Element = ArrayElement<number[]>; // number

// Extract Promise result
type Awaited<T> = T extends Promise<infer R> ? Awaited<R> : T;

type Result = Awaited<Promise<Promise<string>>>; // string

// Extract function first parameter
type FirstParam<T> = T extends (first: infer F, ...rest: any[]) => any ? F : never;

type First = FirstParam<(name: string, age: number) => void>; // string
```

### Practical Conditional Types

```typescript
// API response helper
type ApiResult<T> =
  | { success: true; data: T }
  | { success: false; error: string };

// Extract data type from result
type ExtractData<T> = T extends { success: true; data: infer D } ? D : never;

type UserResult = ApiResult<User>;
type UserData = ExtractData<UserResult>; // User

// Type-safe event handlers
type EventHandler<T> = T extends `on${infer Event}`
  ? (event: Event) => void
  : never;

type ClickHandler = EventHandler<"onClick">; // (event: "Click") => void
```

---

## Template Literal Types

### Basic Template Literals

```typescript
type Greeting = `Hello, ${string}!`;

const valid: Greeting = "Hello, World!";   // OK
const invalid: Greeting = "Hi, World!";    // Error

// Combine with unions
type Size = "small" | "medium" | "large";
type Color = "red" | "blue" | "green";

type ColoredSize = `${Color}-${Size}`;
// "red-small" | "red-medium" | "red-large" |
// "blue-small" | "blue-medium" | "blue-large" |
// "green-small" | "green-medium" | "green-large"
```

### String Manipulation Types

```typescript
// Built-in string manipulation types
type Upper = Uppercase<"hello">;     // "HELLO"
type Lower = Lowercase<"HELLO">;     // "hello"
type Cap = Capitalize<"hello">;      // "Hello"
type Uncap = Uncapitalize<"Hello">; // "hello"

// Practical: Generate event names
type Event = "click" | "hover" | "focus";
type EventHandler = `on${Capitalize<Event>}`;
// "onClick" | "onHover" | "onFocus"

// CSS property with vendor prefixes
type CSSProp = "transform" | "transition";
type Prefixed = `-webkit-${CSSProp}` | `-moz-${CSSProp}` | CSSProp;
```

### Advanced Template Patterns

```typescript
// Parse dot-notation paths
type PathSegment<T> = T extends `${infer Head}.${infer Tail}`
  ? Head | PathSegment<Tail>
  : T;

type Segments = PathSegment<"user.profile.name">;
// "user" | "profile" | "name"

// HTTP methods with paths
type Method = "GET" | "POST" | "PUT" | "DELETE";
type Endpoint = "/users" | "/posts" | "/comments";

type Route = `${Method} ${Endpoint}`;
// "GET /users" | "GET /posts" | "GET /comments" |
// "POST /users" | ... etc

// Type-safe SQL column references
type Table = "users" | "posts";
type Column<T extends Table> = T extends "users"
  ? "id" | "name" | "email"
  : T extends "posts"
  ? "id" | "title" | "content"
  : never;

type UserColumn = `users.${Column<"users">}`;
// "users.id" | "users.name" | "users.email"
```

---

## Variadic Tuple Types

### Basic Variadic Tuples

```typescript
// Spread tuple types
type Concat<T extends unknown[], U extends unknown[]> = [...T, ...U];

type Combined = Concat<[1, 2], [3, 4]>;
// [1, 2, 3, 4]

// Prepend element
type Prepend<T, U extends unknown[]> = [T, ...U];

type WithFirst = Prepend<0, [1, 2, 3]>;
// [0, 1, 2, 3]

// Append element
type Append<T extends unknown[], U> = [...T, U];

type WithLast = Append<[1, 2, 3], 4>;
// [1, 2, 3, 4]
```

### Practical Variadic Patterns

```typescript
// Typed curry function
type Curry<F> = F extends (...args: infer A) => infer R
  ? A extends [infer First, ...infer Rest]
    ? (arg: First) => Curry<(...args: Rest) => R>
    : R
  : never;

declare function curry<F extends (...args: any[]) => any>(fn: F): Curry<F>;

function add(a: number, b: number, c: number): number {
  return a + b + c;
}

const curriedAdd = curry(add);
const add1 = curriedAdd(1);     // (arg: number) => Curry<...>
const add1and2 = add1(2);       // (arg: number) => number
const result = add1and2(3);     // number (6)

// Typed pipe function
type Pipe<T extends unknown[], R> = T extends [infer First, ...infer Rest]
  ? First extends (arg: R) => infer Next
    ? Pipe<Rest, Next>
    : never
  : R;

function pipe<T extends ((arg: any) => any)[]>(
  ...fns: T
): (arg: Parameters<T[0]>[0]) => Pipe<T, Parameters<T[0]>[0]> {
  return (arg) => fns.reduce((acc, fn) => fn(acc), arg);
}

const process = pipe(
  (n: number) => n * 2,
  (n: number) => n.toString(),
  (s: string) => s.length
);

const length = process(5); // number (2 - length of "10")
```

---

## Built-in Utility Types Reference

| Utility | Purpose | Example |
|---------|---------|---------|
| `Partial<T>` | All properties optional | `Partial<User>` |
| `Required<T>` | All properties required | `Required<Partial<User>>` |
| `Readonly<T>` | All properties readonly | `Readonly<User>` |
| `Pick<T, K>` | Select properties | `Pick<User, "id" \| "name">` |
| `Omit<T, K>` | Exclude properties | `Omit<User, "password">` |
| `Record<K, V>` | Create object type | `Record<string, User>` |
| `Exclude<T, U>` | Remove union members | `Exclude<"a" \| "b", "a">` |
| `Extract<T, U>` | Keep union members | `Extract<"a" \| "b", "a">` |
| `NonNullable<T>` | Remove null/undefined | `NonNullable<string \| null>` |
| `Parameters<F>` | Function parameters | `Parameters<typeof fn>` |
| `ReturnType<F>` | Function return | `ReturnType<typeof fn>` |
| `ConstructorParameters<C>` | Constructor params | `ConstructorParameters<typeof Date>` |
| `InstanceType<C>` | Instance type | `InstanceType<typeof Date>` |
| `Awaited<T>` | Unwrap Promise | `Awaited<Promise<User>>` |
| `NoInfer<T>` | Prevent inference | `NoInfer<T>` (TS 5.4+) |
