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

# Mermaid Diagram Patterns

Reference templates for diagrams used in project-knowledge output documents.

## Editorial figures: the Diagram Design provider

Mermaid patterns stay the default for schemas that live and change beside the
code. When a guide is going to be published and needs an editorial figure
(architecture, sequence, data model, timeline, quadrant, or another of the
types in the upstream list), load the `diagram-design:diagram-design` skill and
follow its method, applying the project's brand; export SVG or PNG when the
document needs a portable figure.

```bash
/plugin marketplace add cathrynlavery/diagram-design
/plugin install diagram-design@diagram-design
```

Diagram Design is a required external provider of project-knowledge, installed
by hand from its own marketplace; no upstream source is copied into this
repository, and the upstream Install section lists the command for every host.
A figure restates verified content only: it never invents a relationship, a
component or a quantity that the evidence does not carry. When the provider is
unavailable, stop that figure and report it as a broken install with the
commands above; do not substitute Mermaid or a hand-built SVG for a figure that
was planned as editorial.

## 1. Mindmap (01-overview.md)

Project concept map showing high-level structure and relationships.

```mermaid
mindmap
  root((Project Name))
    Core Purpose
      Primary function
      Target users
    Features
      Feature group A
        Specific capability
        Specific capability
      Feature group B
        Specific capability
    Tech Stack
      Frontend
        Framework
        Key libraries
      Backend
        Language/runtime
        Database
    Key Concepts
      Domain term 1
      Domain term 2
```

### Guidelines
- Root node: project name in double parentheses `(( ))`
- Max 3 levels deep
- Group by functional areas, not file structure
- Use plain language, not technical identifiers

## 2. Component/Layer Diagram (04-architecture.md)

Shows how the codebase is organized into layers or modules.

```mermaid
flowchart TB
    subgraph Presentation["Presentation Layer"]
        UI[UI Components]
        Pages[Page Routes]
    end

    subgraph Business["Business Logic"]
        Services[Services]
        Validators[Validation]
    end

    subgraph Data["Data Layer"]
        Repos[Repositories]
        Models[Models]
    end

    subgraph External["External"]
        DB[(Database)]
        API[Third-party APIs]
    end

    UI --> Services
    Pages --> Services
    Services --> Validators
    Services --> Repos
    Repos --> DB
    Services --> API
```

### Guidelines
- Use subgraphs for layers/boundaries
- Label subgraphs with human-readable names
- Show data flow direction with arrows
- Use shape conventions: `[Rectangle]` for components, `[(Cylinder)]` for databases, `([Stadium])` for external services
- Include file path annotations as comments where helpful

## 3. Flowchart (05-workflows.md)

User or system workflows showing decision points and outcomes.

```mermaid
flowchart TD
    A[User action] --> B{Decision point?}
    B -->|Yes| C[Process A]
    B -->|No| D[Process B]
    C --> E[Outcome]
    D --> E
    E --> F[Final state]
```

### Guidelines
- Start with the trigger (user action or system event)
- Use `{ }` for decision diamonds
- Label all edges, especially from decision nodes
- Keep linear: avoid complex crossing lines
- One workflow per diagram: split complex flows into multiple diagrams

## 4. Sequence Diagram (05-workflows.md)

Interactions between components over time for key operations.

```mermaid
sequenceDiagram
    actor User
    participant UI as Frontend
    participant API as API Server
    participant DB as Database

    User->>UI: Performs action
    UI->>API: POST /endpoint
    API->>DB: Query data
    DB-->>API: Results
    API-->>UI: JSON response
    UI-->>User: Updated view
```

### Guidelines
- Name participants with readable aliases: `participant API as API Server`
- Use `actor` for human users
- Solid arrows `->>`  for requests, dashed `-->>` for responses
- Add `Note over` for important context
- Keep to 5-8 interactions per diagram: split if longer
- Show the happy path first, mention error paths in text

## 5. ER Diagram (06-data-model.md)

Entity relationships showing data structures and their connections.

```mermaid
erDiagram
    USER {
        string id PK
        string email
        string name
        datetime created_at
    }

    ORDER {
        string id PK
        string user_id FK
        decimal total
        string status
        datetime created_at
    }

    ORDER_ITEM {
        string id PK
        string order_id FK
        string product_id FK
        int quantity
    }

    PRODUCT {
        string id PK
        string name
        decimal price
    }

    USER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_ITEM : contains
    PRODUCT ||--o{ ORDER_ITEM : "included in"
```

### Guidelines
- Include PK/FK annotations
- Use standard cardinality notation: `||--o{` (one-to-many), `||--||` (one-to-one), `}o--o{` (many-to-many)
- Label relationships with verbs
- Include key fields only: not every column
- Group related entities visually

## General Rules

- Keep diagrams under 15-20 nodes
- Use consistent naming across all diagrams in a guide
- Test that syntax renders correctly in standard Mermaid renderers
- Prefer clarity over completeness: a readable subset beats a cluttered whole
- Add a brief text introduction before each diagram explaining what it shows
