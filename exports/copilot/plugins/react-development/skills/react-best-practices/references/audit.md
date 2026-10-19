<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

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

# React Performance Audit

Audit React code for performance, state management, bundle optimization, and modern API adoption, and produce a scored markdown report with fix instructions. Covers re-renders, bundle size, state management, React 19 API adoption and the Vercel best-practices checklist. Shape: detect scope, run the linters, dispatch the plugin's reviewer in an isolated context, write the report.

Caller: `/daodan:check-health`, which runs this audit when the project has React. Inside `/daodan:review-changes` and `/daodan:review-branch`, senior-review dispatches `react-development:react-performance-optimizer` with inputs it prepares, not through this procedure: never run both on the same target.

Act as a senior React performance auditor.

## Inputs

- **TARGET**: what the caller passes.
  - The project, or nothing: full mode over the default frontend roots.
  - A path (file or directory): full mode restricted to that path.
  - A diff (uncommitted changes, or a commit, range or branch the caller resolved to a revision range): diff mode over the React files it changes.
  - Free text that names no path and no diff: full mode over the default frontend roots.
- **Mode**: method decision. Full mode when called by `/daodan:check-health`; diff mode only when the caller passes a diff.
- **Strict line**: method decision. When Critical findings exist, the summary always ends with the strict line of Step 4.
- **Run directory**: the caller's run directory, written `<run>` below. Everything this audit writes goes under `<run>/react-review/`; it edits no project file.

## CRITICAL RULES

1. **React-only scope.** Ignore CSS, layout, visual polish. Focus on components, state management, bundle, and React patterns.
2. **Run the declared reviewer.** Dispatch `react-development:react-performance-optimizer` in its required isolated context through the host harness with the full prepared scope.
3. **Write markdown report.** Output is `<run>/react-review/report.md`: an actionable checklist with scores, findings, and fix instructions.
4. **Never enter plan mode.** Execute immediately.

## Step 1: Detect Scope

### Decision tree

**Full mode** (the default; the caller passes no diff, as `/daodan:check-health` does):
- Scan entire frontend: `src/`, `app/`, `components/`, `pages/`, or the TARGET path

**Diff mode** (the caller passes a diff):
- Review only the changed React files
- Get the diff: `git diff HEAD -- <react files>` for uncommitted changes, `git diff <range> -- <react files>` for a revision range

### Check for React files (diff mode only)

For uncommitted changes:

```bash
# Check for changed React files in git diff
git diff HEAD --name-only | grep -E '\.(tsx|jsx)$' || true
git diff --name-only | grep -E '\.(tsx|jsx)$' || true
git diff --cached --name-only | grep -E '\.(tsx|jsx)$' || true
```

For a revision range: `git diff <range> --name-only | grep -E '\.(tsx|jsx)$' || true`.

### Discover React files (full mode only)

```bash
find src -type f \( -name "*.tsx" -o -name "*.jsx" \) | head -80
```

Or use the TARGET path in place of `src` when the caller names one.

If no React files are found, stop and say so.

## Step 1.5: Run Deterministic Linters (if available)

```bash
# React/JS linting (if eslint is configured)
npx eslint --format json "src/**/*.{tsx,jsx}" 2>/dev/null || true
```

Pass ESLint output to the agent for ground truth.

## Step 2: Sample Key Files & Gather Context

Read a representative cross-section:
- Entry layout files (e.g., `App.tsx`, `Layout.tsx`, `_app.tsx`, `root.tsx`)
- 3-5 core components
- State management files (stores, contexts, atoms)
- Config files (vite.config, next.config, tsconfig)

## Step 3: Run Review Agent

The host harness binds the declared `react-development:react-performance-optimizer` role. Give it the
following task, the exact scope, relevant files, authorization and an owned
intermediate report path `<run>/react-review/worker-findings.md`. The reviewer
returns its findings and a delivered or failed outcome; it does not write
the final report. Record that outcome before the report phase. A failed or
missing delivery leaves the review incomplete and must be reported.

````text
Audit the React performance, state management, and bundle optimization of this frontend codebase.

## Scope
[list of key files sampled]

## File Contents
[paste sampled components, state management files, and config (NOT stylesheets)]

## Product Brief (if available)
[paste brief content (especially performance budget and stack info) or "No product brief found"]

## Linter Output (if available)
[paste ESLint JSON report if captured in Step 1.5, or "No linter output available"]

## Vercel React Best Practices Checklist (70 rules; flag violations)

**1. Eliminating Waterfalls (CRITICAL):** async-defer-await (move await into branches), async-parallel (Promise.all for independent ops), async-dependencies (better-all for partial deps), async-api-routes (start promises early, await late), async-suspense-boundaries (stream with Suspense)
**2. Bundle Size (CRITICAL):** bundle-barrel-imports (import directly, avoid barrels), bundle-dynamic-imports (next/dynamic for heavy components), bundle-defer-third-party (load analytics after hydration), bundle-conditional (load modules only when activated), bundle-preload (preload on hover/focus)
**3. Server-Side (HIGH):** server-auth-actions, server-cache-react (React.cache per-request), server-cache-lru (cross-request LRU), server-dedup-props, server-hoist-static-io, server-serialization (minimize client data), server-parallel-fetching, server-after-nonblocking
**4. Client-Side Data (MEDIUM-HIGH):** client-swr-dedup, client-event-listeners (deduplicate global), client-passive-event-listeners (passive for scroll), client-localstorage-schema (version and minimize)
**5. Re-render Optimization (MEDIUM):** rerender-defer-reads, rerender-memo (extract expensive work), rerender-memo-with-default-value, rerender-dependencies (primitive deps), rerender-derived-state (subscribe to derived booleans), rerender-derived-state-no-effect, rerender-functional-setstate, rerender-lazy-state-init, rerender-simple-expression-in-memo, rerender-move-effect-to-event, rerender-transitions (startTransition), rerender-use-ref-transient-values, rerender-no-inline-components
**6. Rendering (MEDIUM):** rendering-animate-svg-wrapper, rendering-content-visibility, rendering-hoist-jsx, rendering-svg-precision, rendering-hydration-no-flicker, rendering-hydration-suppress-warning, rendering-activity, rendering-conditional-render (ternary not &&), rendering-usetransition-loading, rendering-resource-hints, rendering-script-defer-async
**7. JS Performance (LOW-MEDIUM):** js-batch-dom-css, js-index-maps (Map for lookups), js-cache-property-access, js-cache-function-results, js-cache-storage, js-combine-iterations, js-length-check-first, js-early-exit, js-hoist-regexp, js-min-max-loop, js-set-map-lookups, js-tosorted-immutable, js-flatmap-filter
**8. Advanced (LOW):** advanced-event-handler-refs, advanced-init-once, advanced-use-latest

## Instructions
Use the checklist above as your primary audit framework. Flag any violations you find in the reviewed code, citing the specific rule ID (e.g. "Violates bundle-barrel-imports").

Evaluate (in addition to the rules above):
1. **React Compiler readiness**: Is `babel-plugin-react-compiler` configured? Identify patterns the compiler can auto-optimize vs patterns requiring manual intervention (external store reads, non-React state mutations, dynamic property access)
2. **External store selector audit (CRITICAL)**:
   - Selectors returning objects/arrays without `useShallow`: causes re-renders on every store update
   - Selectors with `.filter()` / `.map()` / `.reduce()` creating new references every render
   - `useStore()` with no selector: subscribes to entire store
   - Component receiving store-derived object as prop without memoization
3. **React 19 API adoption**: Are newer APIs used where beneficial?
   - `use()` for conditional data fetching and context
   - `useOptimistic()` for optimistic UI updates
   - `useFormStatus()` for form submission state
   - `useActionState()` for server action results
   - `useDeferredValue()` for separating critical vs deferrable updates
4. **State management**: Zustand/Jotai/Redux selector patterns, prop drilling, state duplication, useEffect chains
5. **Bundle optimization**: Heavy imports, missing code splitting, lazy loading opportunities, tree-shaking blockers
6. **Virtualization check**: Large lists/tables not using TanStack Virtual or similar, index as key in virtualized lists
7. **Context-aware caching**: TanStack Query config appropriate for app type? CRUD apps need short stale times, real-time apps need WebSocket invalidation, static content can use long cache
8. **useEffect/useCallback infinite loop detection (CRITICAL)**:
   - `useCallback` that updates state listed in its own dependency array, called from a `useEffect` that depends on the callback: creates infinite re-trigger cycle
   - `useEffect` with no ref guard calling state-updating functions on mount
   - Unstable callback references (object/array deps) in `useEffect` dependency arrays causing continuous re-firing
   - Symptom: repeated identical network requests, 429 rate limit errors, CPU spike on component mount
9. **useEffect cleanup audit**:
   - Missing `AbortController` on fetch calls
   - `Channel.onmessage` not nulled on unmount
   - WebSocket connections not closed
   - Missing `clearInterval` / `clearTimeout`
   - Missing `removeEventListener`
10. **Stale closure detection (CRITICAL)**:
   - Variables derived from state/props captured in `useEffect(..., [])` closures without ref indirection
   - Event handlers registered at mount time reading state that changes after mount
   - Interval/timeout callbacks reading stale captured values
   - Symptom: handler uses outdated state value, decisions based on stale data, no crash or warning
11. **Performance budget** (if brief provided): Does the current state meet the stated Core Web Vitals or performance targets?

For each finding: severity (Critical/High/Medium/Low), file, issue, specific fix with code example.
Note what's done well.

Return structured JSON at the end:
```json
{
  "findings": [
    { "severity": "Critical", "category": "Re-renders", "file": "...", "issue": "...", "fix": "..." }
  ],
  "positives": ["..."],
  "score": { "re_render_control": 6, "state_management": 7, "bundle": 8, "overall": 7 }
}
```
````

## Step 4: Generate Markdown Report

After the agent completes, create the `<run>/react-review/` directory and write `report.md`.

Order findings by severity, then file name.

**Output file:** `<run>/react-review/report.md`

```markdown
# React Performance Review: [date]

Full React audit: [N] components, [M] state files

## Product Brief Context

[If a product brief was found, summarize performance budget and stack info. If not, note "No product brief found: reviewed against general best practices."]

## Scores

| Category | Score |
|----------|-------|
| Re-render Control | X/10 |
| State Management | X/10 |
| Bundle Optimization | X/10 |
| React 19 Adoption | X/10 |
| **Overall** | **X/10** |

Critical: X | High: X | Medium: X | Low: X

## Files Audited

- `Component.tsx`, `Store.ts`, ...

---

## Critical & High Issues

### Re-render Control

#### `Store.ts`: [issue title]
- **Severity**: Critical
- **Issue**: [description]
- **Fix**: [fix instruction with code]
- [ ] Fixed

### State Management

#### `Context.tsx`: [issue title]
- **Severity**: High
- **Issue**: [description]
- **Fix**: [fix instruction]
- [ ] Fixed

### Bundle Optimization

#### `index.ts`: [issue title]
- **Severity**: High
- **Issue**: [description]
- **Fix**: [fix instruction]
- [ ] Fixed

---

## Medium & Low Issues

[Same format as above]

---

## What's Working Well

- [positive observation]
- [another positive]

---

## Action Plan

1. [ ] [top priority fix, from critical findings]
2. [ ] [second priority]
3. [ ] [third priority]
4. [ ] [fourth priority]
5. [ ] [fifth priority]
```

**Print a short summary** in the conversation:

```
React performance review complete.

Report: <run>/react-review/report.md

Overall Score: X/10
Re-renders: X/10 | State: X/10 | Bundle: X/10 | React 19: X/10

Critical: X | High: X | Medium: X | Low: X

Top 3 issues:
1. [critical issue summary]
2. [high issue summary]
3. [high issue summary]
```

When Critical findings exist, end the summary with the strict line:
```
STRICT MODE: X critical React performance issues found. Recommend addressing before shipping.
```
