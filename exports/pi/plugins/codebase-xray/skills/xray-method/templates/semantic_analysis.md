<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

# Semantic Analysis: {FILE_PATH}

> AI-powered deep analysis generated on {DATE}
> Classification: {CRITICAL|HIGH_COMPLEXITY|STANDARD|UTILITY}

---

## Executive Summary

**Purpose:** {One sentence: WHY does this code exist?}

**Responsibility:** {What does this code OWN in the system?}

**Pattern(s):** {Repository, Service, State Machine, etc.}

---

## Semantic Understanding

### What Problem Does This Solve?

{2-3 sentences describing the business/technical problem this code addresses.
Not what it DOES, but what problem would exist WITHOUT it.}

### Key Insight

{The single most important thing to understand about this code.
What would a new developer be surprised by? What's non-obvious?}

---

## Component Analysis

### Primary Abstractions

| Name | Type | Responsibility | Why It Exists |
|------|------|----------------|---------------|
| {Name} | class/function | {What it owns} | {Why not inline} |

### Behavioral Analysis

#### Core Behavior

```
TRIGGER: {What causes this code to run}
    │
    ▼
PRECONDITIONS: {What must be true before execution}
    │
    ▼
PROCESSING: {What transformations occur}
    │
    ▼
SIDE EFFECTS: {What changes in the world}
    │
    ▼
POSTCONDITIONS: {What is guaranteed after execution}
```

#### State Transitions (if applicable)

```mermaid
stateDiagram-v2
    {STATE_DIAGRAM}
```

#### Decision Points

| Condition | True Path | False Path | Impact |
|-----------|-----------|------------|--------|
| {condition} | {behavior} | {behavior} | {what_changes} |

---

## Dependency Analysis

### Why Each Dependency?

| Dependency | Category | Purpose | Replaceable? |
|------------|----------|---------|--------------|
| {import} | internal/external | {why needed} | {yes/no + why} |

### Data Flow

```
INPUTS                    PROCESSING                 OUTPUTS
────────────────────────────────────────────────────────────────
{source} ──────┐
               │
{source} ──────┼──────► {this_component} ──────► {destination}
               │              │
{source} ──────┘              │
                              ▼
                         {side_effect}
```

### Integration Points

| External System | Operation | Protocol | Failure Mode |
|-----------------|-----------|----------|--------------|
| {system} | {what_we_do} | {http/amqp/etc} | {what_if_fails} |

---

## Quality Assessment

### Strengths

- {What this code does well}
- {Good patterns applied}
- {Clear design decisions}

### Concerns

| Issue | Severity | Location | Recommendation |
|-------|----------|----------|----------------|
| {issue} | HIGH/MEDIUM/LOW | {file::symbol} | {fix} |

### Red Flags Found

```
{NONE | List of identified anti-patterns or risks}
```

---

## Contract Documentation

### Public Interface

#### `{function_or_method_name}()`

**Purpose:** {What this does at business level}

**Signature:**
```python
def {name}({params}) -> {return_type}:
```

**Semantics:**

| Parameter | Meaning | Valid Range | What If Invalid |
|-----------|---------|-------------|-----------------|
| {param} | {semantic_meaning} | {constraints} | {error_behavior} |

**Returns:**

| Condition | Return Value | Meaning |
|-----------|--------------|---------|
| success | {type} | {what_it_represents} |
| failure | {exception/none} | {why_and_when} |

**Side Effects:**
- {What changes beyond return value}

**Example:**
```python
# Typical usage
result = {function}({typical_args})

# Edge case
result = {function}({edge_case_args})
```

---

## Flow Tracing

### Primary Flow: {FLOW_NAME}

```
1. Entry: {where_flow_starts}
   │
   ├── Validation: {what_is_checked}
   │
   ├── Processing Step 1: {description}
   │   └── Calls: {other_components}
   │
   ├── Processing Step 2: {description}
   │   └── Side Effect: {what_changes}
   │
   └── Exit: {what_is_returned/emitted}
```

### Error Flow: {ERROR_SCENARIO}

```
1. Error Occurs: {where_and_why}
   │
   ├── Caught By: {handler}
   │
   ├── Recovery Action: {what_happens}
   │
   └── Final State: {system_state_after}
```

---

## Contextual Understanding

### Relationship to System

```
                    ┌─────────────────┐
                    │   {upstream}    │
                    └────────┬────────┘
                             │ {what_it_provides}
                             ▼
┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│ {peer_left}  │◄──►│  THIS COMPONENT │◄──►│ {peer_right} │
└──────────────┘    └────────┬────────┘    └──────────────┘
                             │ {what_it_provides}
                             ▼
                    ┌─────────────────┐
                    │  {downstream}   │
                    └─────────────────┘
```

### Who Calls This?

| Caller | When | Why |
|--------|------|-----|
| {module} | {trigger} | {purpose} |

### What Does This Call?

| Callee | When | Why |
|--------|------|-----|
| {module} | {condition} | {purpose} |

---

## Testing Implications

### What Must Be Tested

| Scenario | Input | Expected Outcome | Why Critical |
|----------|-------|------------------|--------------|
| {happy_path} | {input} | {output} | {business_value} |
| {edge_case} | {input} | {output} | {risk_if_broken} |
| {error_case} | {input} | {exception} | {security/stability} |

### Test Doubles Needed

| Dependency | Mock Strategy | Behavior to Simulate |
|------------|---------------|---------------------|
| {dep} | {mock/stub/fake} | {what_to_return} |

---

## Maintenance Notes

### Change Impact Analysis

If modifying this code, also check:
- [ ] {related_file_1} - {why}
- [ ] {related_file_2} - {why}
- [ ] {test_file} - {update_fixtures}

### Known Limitations

| Limitation | Reason | Workaround |
|------------|--------|------------|
| {what} | {why_it_exists} | {how_to_handle} |

### Future Considerations

{What might need to change? What assumptions might break?}

---

## Verification Status

| Aspect | Status | Evidence |
|--------|--------|----------|
| Structure | VALIDATED | AST parsing |
| Behavior | {VERIFIED/UNVERIFIED} | {file.py::Class.method or "needs review"} |
| Integration | {VERIFIED/UNVERIFIED} | {file:line of the call site, or "unverified: no caller found"} |

---

## Links

- **Run report:** `.codebase-xray/runs/{run_id}/07-final-report.md`
- **Callers:** {list_of_files_that_import_this}
- **Callees:** {list_of_files_this_imports}

---

*Analysis generated following AI_ANALYSIS_METHODOLOGY.md*
