<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
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

# AI-Powered Code Analysis Methodology

## Method loads

| Resource | Sections | When |
|---|---|---|
| `SKILL.md` | all | always |
| `references/reading.md` | all | always |

---

## Core Principle: Understanding Over Extraction

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                         THE SEMANTIC ANALYSIS MANDATE                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Scripts extract STRUCTURE:  "This file has class Foo with method bar()"    ║
║  Claude extracts MEANING:    "Foo implements the Repository pattern for     ║
║                               caching user sessions with TTL expiration"    ║
║                                                                              ║
║  NEVER stop at structure. ALWAYS pursue understanding.                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## The Five Layers of Code Understanding

### Layer 1: WHAT (Structural) - Scripts handle this
- Classes, functions, imports
- Line counts, dependencies
- AST-extractable information

### Layer 2: HOW (Mechanical) - Claude's first pass
- Algorithm implementation details
- Data flow through functions
- State transformations

### Layer 3: WHY (Intent) - Claude's deep analysis
- Business purpose of the code
- Problem being solved
- Design decisions made

### Layer 4: WHEN (Temporal) - Claude's behavioral analysis
- Execution conditions and triggers
- Lifecycle and state transitions
- Concurrency and timing

### Layer 5: CONSEQUENCES (Impact) - Claude's systems thinking
- Side effects and mutations
- Downstream dependencies
- Failure modes and edge cases

---

## Semantic Analysis Questions

When analyzing ANY code unit, Claude must answer these questions:

### Identity Questions
```
□ What is this code's single responsibility?
□ What abstraction does it represent?
□ What would break if this code didn't exist?
```

### Behavior Questions
```
□ What are ALL possible inputs?
□ What are ALL possible outputs (including side effects)?
□ What state does it read? What state does it mutate?
□ What are the preconditions for correct operation?
□ What are the postconditions guaranteed after execution?
```

### Integration Questions
```
□ Who calls this code? Under what circumstances?
□ What does this code call? Why those specific dependencies?
□ What contracts/interfaces does it fulfill?
□ What would need to change if this code's signature changed?
```

### Quality Questions
```
□ What could go wrong? How is failure handled?
□ Are there implicit assumptions that could break?
□ Is there hidden coupling to global state or external systems?
□ Are there race conditions or timing dependencies?
```

---

## Analysis Patterns by Code Type

### Pattern: Service/Manager Class
```
RECOGNIZE BY:
- Name ends in Service, Manager, Handler, Controller
- Has multiple public methods
- Coordinates between other components

ANALYZE FOR:
1. What domain concept does this service own?
2. What operations does it expose? (CRUD? Commands? Queries?)
3. What resources does it manage? (connections, state, caches)
4. What is the lifecycle? (singleton? per-request? pooled?)
5. What are the thread-safety guarantees?

DOCUMENT:
- Primary responsibility (one sentence)
- Key operations with preconditions
- Resource management strategy
- Error handling approach
- Integration points
```

### Pattern: Data Model/Entity
```
RECOGNIZE BY:
- Name is a noun (User, Order, Transaction)
- Primarily contains fields/attributes
- May have validation logic

ANALYZE FOR:
1. What real-world concept does this represent?
2. What are the invariants? (fields that must always be valid)
3. What are the valid state transitions?
4. What is the identity? (which fields make it unique)
5. What are the relationships to other entities?

DOCUMENT:
- Domain meaning
- Field semantics (not just types)
- Validation rules
- State machine (if applicable)
- Relationship cardinality
```

### Pattern: Algorithm/Processor
```
RECOGNIZE BY:
- Name contains process, calculate, compute, transform
- Takes input, produces output
- May be stateless

ANALYZE FOR:
1. What transformation does this perform?
2. What is the algorithmic complexity? (time/space)
3. What are the edge cases?
4. Are there numerical stability concerns?
5. Is it deterministic?

DOCUMENT:
- Input → Output transformation description
- Algorithm explanation (for non-trivial cases)
- Complexity analysis
- Edge case handling
- Example inputs and outputs
```

### Pattern: Adapter/Integration
```
RECOGNIZE BY:
- Name contains Adapter, Client, Gateway, Connector
- Wraps external system
- Handles serialization/deserialization

ANALYZE FOR:
1. What external system does this wrap?
2. What is the retry/resilience strategy?
3. How are credentials managed?
4. What is the connection lifecycle?
5. How are errors from the external system translated?

DOCUMENT:
- External system and protocol
- Authentication mechanism
- Retry and timeout configuration
- Error mapping strategy
- Connection pooling details
```

### Pattern: Event Handler/Callback
```
RECOGNIZE BY:
- Name contains on_, handle_, process_
- Takes event/message as parameter
- Often async

ANALYZE FOR:
1. What event triggers this handler?
2. What is the expected event frequency?
3. What happens if handling fails?
4. Is ordering guaranteed?
5. Is idempotency required/implemented?

DOCUMENT:
- Triggering event/condition
- Expected behavior
- Failure handling
- Ordering and idempotency guarantees
- Side effects produced
```

### Pattern: Factory/Builder
```
RECOGNIZE BY:
- Name contains Factory, Builder, Creator
- Returns instances of other classes
- May have configuration methods

ANALYZE FOR:
1. What does this create?
2. Why is direct construction not used?
3. What configuration options exist?
4. Are created objects cached or always new?
5. What validation happens during creation?

DOCUMENT:
- What is being created and why factory pattern
- Configuration options and defaults
- Lifecycle of created objects
- Validation performed
```

### Pattern: State Machine
```
RECOGNIZE BY:
- Enum of states
- Transition methods
- State-dependent behavior

ANALYZE FOR:
1. What are ALL valid states?
2. What are ALL valid transitions?
3. What triggers each transition?
4. What side effects occur on transition?
5. What is the terminal state(s)?

DOCUMENT:
- State diagram (Mermaid)
- Transition table with triggers
- Side effects per transition
- Error/recovery states
```

---

## Flow Tracing Methodology

When tracing a flow through the system:

### Step 1: Identify Entry Point
```
□ Where does this flow begin? (API endpoint, message handler, timer, etc.)
□ What triggers it? (user action, external event, scheduled task)
□ What data enters at this point?
```

### Step 2: Trace Data Transformations
```
□ How is input data validated?
□ What transformations occur?
□ Where is data enriched with additional information?
□ Where is data persisted?
```

### Step 3: Identify Decision Points
```
□ Where are conditional branches?
□ What determines which branch is taken?
□ Are there early returns or short-circuits?
```

### Step 4: Map Side Effects
```
□ What external systems are called?
□ What state is mutated?
□ What events are emitted?
□ What logs are produced?
```

### Step 5: Document Exit Points
```
□ What are the success outcomes?
□ What are the failure outcomes?
□ What cleanup occurs?
```

---

## Red Flags to Identify

Claude should actively look for and document these issues:

### Architecture Red Flags
```
⚠ GOD CLASS: Class with >10 public methods or >500 LOC
⚠ FEATURE ENVY: Method that uses more of another class than its own
⚠ SHOTGUN SURGERY: Change requires touching many files
⚠ CIRCULAR DEPENDENCY: A → B → C → A
⚠ LEAKY ABSTRACTION: Implementation details exposed in interface
```

### Reliability Red Flags
```
⚠ SWALLOWED EXCEPTION: except: pass or empty catch blocks
⚠ MISSING TIMEOUT: Network/IO calls without timeout
⚠ UNBOUNDED GROWTH: Collections that grow without limit
⚠ RACE CONDITION: Shared mutable state without synchronization
⚠ RESOURCE LEAK: Opened resources not closed
```

### Security Red Flags
```
⚠ HARDCODED SECRET: Passwords, API keys in code
⚠ SQL INJECTION: String concatenation in queries
⚠ MISSING VALIDATION: User input used without sanitization
⚠ OVERLY PERMISSIVE: Catch-all permissions or access
⚠ SENSITIVE LOGGING: Passwords, tokens in log output
```

### Maintainability Red Flags
```
⚠ MAGIC NUMBER: Unexplained numeric constants
⚠ DEAD CODE: Unreachable or unused code
⚠ COPY-PASTE: Duplicated logic blocks
⚠ DEEP NESTING: >4 levels of indentation
⚠ LONG METHOD: >50 lines without clear sections
```

---

## Documentation Output Standards

### For Each Code Unit, Produce:

```markdown
## {ClassName/FunctionName}

**Purpose:** {One sentence explaining WHY this exists}

**Responsibility:** {What this code OWNS in the system}

### Behavior

{Description of what this code DOES, not HOW it does it}

### Inputs
| Parameter | Type | Semantic Meaning | Constraints |
|-----------|------|------------------|-------------|
| ... | ... | ... | ... |

### Outputs
| Return/Effect | Type | Semantic Meaning | Conditions |
|---------------|------|------------------|------------|
| ... | ... | ... | ... |

### Dependencies
- **{Dependency}**: {WHY this dependency is needed}

### State Changes
- {What state is mutated and why}

### Error Conditions
| Condition | Behavior | Recovery |
|-----------|----------|----------|
| ... | ... | ... |

### Usage Example
```python
# Concrete example showing typical usage
```

### Notes
- {Any non-obvious insights, edge cases, or gotchas}
```

---

## Incremental Understanding Protocol

As analysis progresses through the codebase:

### Build Mental Model
```
1. Start with entry points (main, API handlers, event listeners)
2. Trace primary flows to understand core behavior
3. Map shared utilities and how they're used
4. Identify cross-cutting concerns (logging, auth, error handling)
5. Document architectural patterns in use
```

### Cross-Reference Continuously
```
1. When analyzing File B, reference findings from File A
2. Update earlier documentation when new insights emerge
3. Build glossary of domain terms as they appear
4. Map acronyms and abbreviations to full meanings
```

### Validate Understanding
```
1. After analyzing a subsystem, summarize it in one paragraph
2. Predict what a function does before reading it (from name/context)
3. If prediction is wrong, document the surprising behavior
4. Look for inconsistencies between similar components
```

---

## Integration with Scripts

The mechanical scripts support AI analysis:

| Script | Provides | Semantic Reading Adds |
|--------|----------|-------------|
| `snapshot.py write --reuse` | Current inventory and verified reuse of unchanged structure | Which questions require source evidence |
| `source_reader.py outline` | Bounded symbol/path metadata from the run manifest | Autonomous selection of relevant definitions |
| `source_reader.py read` | Validated source blocks and shared file/class context | Contracts, invariants and behavior supported by those blocks |
| `classifier.py` | Complexity metrics | Semantic complexity assessment |
| `ast_parser.py` | Extra structural details absent from the manifest or single-file diagnosis | Interpretation checked against source |
| `analyze_file.py --snapshot "$source_manifest" --find-usages` | Where symbols are used | Why they're used there |
| `doc_review.py` | Documentation health | Documentation accuracy |

**Workflow:**
1. Follow Method loads and bind the exact current run's
   snapshot path from `snapshot.py resolve`. After every verified diff, the coordinator always
   writes or obtains this current owned manifest with `snapshot.py write --reuse`
   before block reading, even for `none` or LF/CRLF-only differences. Diff's
   normalized claims and the reader's exact source bytes have separate identity
   requirements. Readers preserve the current manifest and parent evidence lineage.
2. Use its inventory/import metadata and `source_reader.py outline` for structure
   already available. Narrow truncated outlines and select exact symbols from
   the source question; this step is metadata, not source read in depth.
3. Use `source_reader.py read` for selected implementations, then expand to
   callers/callees, gates, constants, types, invariants, configuration and relevant
   CSS/markup until the claim is supported. Retained context and import neighbours
   do not define semantic completeness. Read full files when the question needs it.
4. Run additional single-file parsing or diagnostic scripts only for required
   details absent from the manifest. Keep whole-scope cascade scanning for entry
   paths; source blocks verify its candidate relationships.
5. Produce claims with source citations and actual files/ranges examined,
   diagnostics and gaps. Distinguish inventory, deep source reading and runtime
   evidence. No obligation to read every file comes from the inventory.

---
