<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Claude binding: repository read, file discovery and content search use Read, Glob
and Grep; repository write and repository edit use Write and Edit; shell execution
uses Bash; network fetch uses WebFetch and network search uses WebSearch; a user
question uses AskUserQuestion. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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

# Comparison & Logic Errors + Type & Conversion Errors

Reference for defect taxonomy categories 3 and 4.

---

## Category 3: Comparison and Logic Errors

### 3.1 Wrong Comparison Operators
- **CWE**: 597
- **Pattern**: Identity vs equality confusion
  - Java: `==` on objects (compares reference) vs `.equals()` (compares value)
  - JS: `==` (coercing) vs `===` (strict)
  - Python: `is` (identity) vs `==` (equality)
- **Detection**: ESLint `eqeqeq`, SpotBugs `EC_UNRELATED_TYPES`, `RC_REF_COMPARISON`
- **Fix**: Always `.equals()` for objects, `===` in JS, `==` in Python (reserve `is` for `None`/singletons)
- **Difficulty**: Low

### 3.2 Floating-Point Comparison
- **CWE**: 1339
- **Pattern**: `0.1 + 0.2 !== 0.3` due to IEEE 754 representation
- **Detection**: Static analysis for `==`/`!=` on floats, ESLint custom rule
- **Fix**: Epsilon comparison `Math.abs(a - b) < 1e-9`, `BigDecimal` (Java), `decimal` module (Python), integer cents for currency
- **Difficulty**: Medium
- **Signature**: `if (total == 0.3)`, `price1 == price2` on doubles

### 3.3 Off-by-One in Conditions
- **CWE**: 193 (related)
- **Pattern**: `<` vs `<=` errors in loop bounds, pagination, tree traversal, fence-post
- **Detection**: Boundary-value tests, mutation testing (changing `<` to `<=`)
- **Fix**: Half-open intervals `[start, end)`, explicit boundary test cases, property-based testing
- **Difficulty**: Medium

### 3.4 Boolean Logic Errors
- **CWE**: N/A
- **Pattern**: De Morgan violations, redundant conditions, contradictory predicates, tautologies
- **Detection**: Satisfiability checking, tautology/contradiction detection, code review
- **Fix**: Truth tables for complex expressions, extract named boolean methods, simplify with De Morgan
- **Difficulty**: Medium
- **Signature**: `if (!a && !b)` intended as `if (!(a && b))` -- De Morgan confusion

### 3.5 Short-Circuit Evaluation Misuse
- **CWE**: N/A
- **Pattern**: Side effects in `&&`/`||` second operand, null-check ordering bugs
- **Detection**: AST analysis for side-effect expressions in short-circuit positions
- **Fix**: Separate side effects from conditions, null checks always on left side
- **Difficulty**: Medium
- **Signature**: `if (process() && validate())` -- `validate()` skipped when `process()` false

### 3.6 Operator Precedence Errors
- **CWE**: 783
- **Pattern**: `&` vs `&&` confusion in C/Java, `flags & MASK == 0` parsed as `flags & (MASK == 0)`
- **Detection**: `-Wparentheses` (GCC/Clang), SpotBugs `BIT_AND_ZZ`
- **Fix**: Explicit parentheses always, `(flags & MASK) == 0`
- **Difficulty**: Low-Medium
- **Signature**: `if (a & b == 0)`, `x << 1 + y` parsed as `x << (1 + y)`

### 3.7 Negation Errors
- **CWE**: N/A
- **Pattern**: Double negation obscuring intent, negating wrong part of compound expression
- **Detection**: Mutation testing (inverting conditions), code review for `!(!x)`
- **Fix**: Positive naming (`isValid` not `isNotInvalid`), extract predicate methods
- **Difficulty**: Medium
- **Signature**: `if (!list.isEmpty() == false)`, `if (!(a > b && c < d))` intended scope unclear

### 3.8 Boundary Condition Errors
- **CWE**: N/A
- **Pattern**: `MAX_VALUE + 1` overflow, empty collection edge, null vs empty string, zero-element
- **Detection**: Property-based testing, boundary-value analysis, fuzzing
- **Fix**: Explicit boundary checks, handle empty/null/zero/max as first-class cases
- **Difficulty**: Medium
- **Signature**: Missing check for empty list before `.get(0)`, `Integer.MAX_VALUE + 1`

---

## Category 4: Type and Conversion Errors

### 4.1 Implicit Type Coercion
- **CWE**: N/A
- **Pattern**: JS `"5" + 3 = "53"` but `"5" - 3 = 2`, C integer promotion widening/narrowing
- **Detection**: TypeScript strict mode, Flow, `-Wconversion` (GCC/Clang), `-Wimplicit-int-conversion`
- **Fix**: Explicit conversions (`Number()`, `parseInt()`), TypeScript, type annotations
- **Difficulty**: Medium
- **Signature**: `"" + number` for string conversion, implicit bool-to-int

### 4.2 Integer Overflow / Underflow
- **CWE**: 190, 191
- **Pattern**: C/C++ undefined behavior, Java silent wrapping, Rust panics (debug) or wraps (release)
- **Detection**: `-ftrapv`, UBSan (`-fsanitize=undefined`), `Math.addExact()` (Java), Clippy
- **Fix**: Checked arithmetic, wider types, `Math.addExact`/`Math.multiplyExact`, Rust `checked_add`
- **Difficulty**: Medium-Hard
- **Signature**: `int total = price * quantity` -- can overflow, `array[offset + len]` -- offset+len wraps

### 4.3 Truncation Errors
- **CWE**: 197
- **Pattern**: Float-to-int loses precision, long-to-int loses high bits, currency rounding
- **Detection**: `-Wconversion`, `-Wfloat-conversion`, Coverity `MISRA_CAST`
- **Fix**: `BigDecimal` for currency, explicit casts with range checks, `Math.toIntExact()` (Java)
- **Difficulty**: Medium
- **Signature**: `int price = (int) calculateTotal()`, `short s = (short) largeInt`

### 4.4 Unsafe Casts / Downcasts
- **CWE**: 704
- **Pattern**: `ClassCastException`, C-style casts hiding errors, `as` keyword misuse
- **Detection**: SpotBugs `BC_UNCONFIRMED_CAST`, `-Wold-style-cast` (C++)
- **Fix**: `instanceof`/pattern matching (Java 17+), `dynamic_cast` + null check (C++), generics, type guards (TS)
- **Difficulty**: Medium
- **Signature**: `(SpecificType) genericObject` without prior `instanceof` check

### 4.5 Generic Type Erasure (JVM)
- **CWE**: N/A
- **Pattern**: `List<String>` becomes raw `List` at runtime, heap pollution, unchecked casts
- **Detection**: `-Xlint:unchecked`, SpotBugs, IntelliJ inspections
- **Fix**: Never mix raw/parameterized types, `Collections.checkedList()`, super type tokens
- **Difficulty**: Medium
- **Signature**: `List rawList = typedList;`, `(List<String>) object` -- unchecked cast

### 4.6 Variance Errors
- **CWE**: N/A
- **Pattern**: `List<Dog>` is NOT a subtype of `List<Animal>` (invariant), TS covariant method params (unsound)
- **Detection**: Compiler errors (Java), TypeScript `--strictFunctionTypes`
- **Fix**: PECS principle (Producer-Extends, Consumer-Super), `? extends T`/`? super T`, `@covariant`/`@contravariant`
- **Difficulty**: Medium-Hard
- **Signature**: `List<Animal> animals = dogs;` -- compile error, `void process(List<Animal>)` won't accept `List<Dog>`

### 4.7 Serialization Type Mismatches
- **CWE**: 502
- **Pattern**: JSON/Protobuf schema evolution breaking clients, field rename/removal, type changes
- **Detection**: Schema validation, consumer-driven contract testing, compatibility checkers
- **Fix**: Schema registries with compatibility rules, never remove required fields, additive-only changes, field numbering (Protobuf)
- **Difficulty**: Medium-Hard
- **Signature**: Server adds required field, old clients send without it -- deserialization fails
