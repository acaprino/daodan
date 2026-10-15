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

# Example: Good CLAUDE.md File

This is a hypothetical `CLAUDE.md` for a small task-management project. Versions,
paths, commands, thresholds and product policies illustrate structure; none is a
default for another project. Derive the target's facts before applying the example.
Its filename suits the illustrated host only when discovery/configuration confirms
it; ordinary Markdown links below do not establish automatic imports or loading.

The original local execution wording below is owned by
`project-protocol:project-protocol` (already required). Equivalent guidance
in existing target projects remains valid.

## Key Characteristics

- **Single entry point**: Structure and overview in one file, references existing docs for deep dives
- **Evergreen structure shape**: top-level layout + repeating patterns + role per category. File-by-file annotation is used here for *specific* reasons (see note below), not as the default
- **Grounded**: A real project's claims must be verified against its sources
- **Proportional**: Length scales with project complexity and necessary guidance
- **Pointers not copies**: References files, doesn't duplicate code
- **Universal applicability**: Only always-relevant guidance

## A note on the file-by-file detail shown below

The structure block in the example annotates every file. **This is not the default.** The level of detail is justified here because:

- Sibling files have overlapping naming patterns that do not self-disambiguate (e.g., `ItemList.tsx`, `TaskCard.tsx`, `TaskForm.tsx` are three distinct components whose roles cannot be inferred from the name alone)
- Some files are key entry points with non-obvious behavior (e.g., `client.ts` carries auth interceptors; `useApi.ts` is the React Query wrapper consumers must follow)
- The project is small enough that the full enumeration fits in the evergreen budget without ballooning the file

In a project with self-explanatory names, no naming collisions among siblings, or a directory count that would make full enumeration churn-prone, the same shape would be documented **categorically only**: top-level dirs + the structural pattern + the role of each category, with no per-file annotation. Example of the categorical-only style for the same project:

```
src/
  components/       # React UI components (functional + hooks). Naming: <Domain><Role>.tsx
  hooks/            # Custom React hooks (ALWAYS follow patterns here)
  store/            # Zustand state slices, one file per slice
  api/              # API client (axios) + endpoint definitions
  utils/            # Pure helpers, no React dependencies
```

The principle is **evergreen shape, not exhaustive enumeration**. File-by-file annotation belongs where name alone is ambiguous, where the file is a key entry point with non-obvious behavior, or to disambiguate siblings: never as the default for every project.

---

````markdown
# Project Context

This is a React 18 + TypeScript web application for task management.

**Tech Stack:**
- React 18.2 with functional components + hooks (see `package.json:12-13`)
- TypeScript 5.3 (see `tsconfig.json`)
- Vite 5.x for build tooling (see `vite.config.ts`)
- Zustand for state management (see `src/store/`)
- React Query for data fetching (see `src/hooks/useApi.ts`)
- Tailwind CSS for styling (see `tailwind.config.js`)
- Caching: verify the configured backend before documenting it

## Project Structure

```
src/
  components/               # React components (functional + hooks)
    ItemList.tsx             # Main task list with drag-and-drop reordering
    TaskCard.tsx             # Individual task card component
    TaskForm.tsx             # Create/edit task modal form
    Layout.tsx               # App shell: sidebar nav, header, content area
    ErrorBoundary.tsx        # Top-level error boundary wrapper
  hooks/                    # Custom hooks (ALWAYS follow patterns here)
    useApi.ts                # React Query wrapper for all API calls
    useAuth.ts               # Auth state, login/logout actions
    useTasks.ts              # Task CRUD operations via React Query
    useDebounce.ts           # Debounce hook for search input
  store/                    # Zustand state slices
    tasks.ts                 # Task filters, sorting, selected task
    ui.ts                    # Sidebar open/closed, active modal, theme
  api/                      # API client and endpoints
    client.ts                # Axios instance with auth interceptors
    endpoints.ts             # All REST endpoint definitions
  types/                    # TypeScript type definitions
    task.ts                  # Task, TaskStatus, TaskFilter, TaskSort
    user.ts                  # User, AuthState, LoginCredentials
    api.ts                   # ApiResponse<T>, PaginatedResponse<T>
  utils/                    # Shared utilities
    date.ts                  # Date formatting and relative time helpers
    validation.ts            # Zod schemas for form validation
tests/
  e2e/                      # Playwright E2E tests (user flows)
  unit/                     # Vitest unit tests (components + hooks)
public/                     # Static assets
docs/
  architecture.md           # Architecture decisions and rationale
  testing-guide.md          # Testing patterns and conventions
  api-patterns.md           # API integration patterns
  components.md             # Component guidelines
  deployment.md             # Environment variables and deploy config
```

## Development Workflow

**Start dev server:**
```bash
npm run dev
```

**Run tests:**
Run from the repository root after the lockfile installation with `npm ci` and
the Node version declared by this project's toolchain file. E2E additionally needs
the configured Playwright browsers, the test application and the disposable test
API described in `docs/testing-guide.md`; use its fixture reset and cleanup rules.
Do not substitute production credentials or claim a production check from a local
test run.
```bash
npm test              # Unit tests with Vitest
npm run test:e2e      # E2E tests with Playwright
```

**Linting/Formatting:**
We use Biome for linting and formatting (see `biome.json`).
DO NOT suggest code style changes: Biome handles this automatically.

**Before committing:**
Pre-commit hooks run Biome and type checking automatically.

## Important Patterns

**Custom Hooks:**
- ALWAYS follow patterns in `src/hooks/` directory
- Use React Query for all data fetching
- Example: `useApi.ts`, `useAuth.ts`

**State Management:**
- Use Zustand slices (see `src/store/`)
- Keep state minimal and derived
- Example: `src/store/tasks.ts`

**Component Patterns:**
- Functional components only
- Props interface in same file
- Extract complex logic to custom hooks

**API Conventions:**
- All API calls through React Query hooks
- Error handling via error boundaries
- Loading states via query.isLoading

## Testing

**Unit tests:** Vitest for components and utilities
**E2E tests:** Playwright for user flows
**Coverage:** This example assumes a locally approved 80% target configured in the
project's coverage gate (`npm run coverage`); it is not a default for other projects
or evidence that individual behaviors are protected.

Expected results come from approved product requirements or independently checked
contracts. A wrong expectation may be corrected with that evidence; a product
regression retains its active failing check until the code is repaired. Unit tests
may control IO boundaries; the E2E lane exercises its configured real test services.
Deterministic clocks, isolated state and resource cleanup follow the testing guide.

See `docs/testing-guide.md` for detailed testing patterns.

## Deployment

CI/CD via GitHub Actions (see `.github/workflows/`)
Deploys to Vercel automatically on merge to main.

See `docs/deployment.md` for environment variables and configuration.

## Common Tasks

**Add new feature:**
1. Create component in `src/components/`
2. Add state slice in `src/store/` if needed
3. Add API hook in `src/hooks/` if data fetching required
4. Add tests
5. Update types in `src/types/`

**Add new API endpoint:**
1. Add to `src/api/endpoints.ts`
2. Create React Query hook in `src/hooks/`
3. Add TypeScript types
4. Add tests

## Test-Suite Rules

Test ownership: source at unit; behavior at integration, contract and e2e.
Assertion protection: Preserve assertions for approved behavior; correct a wrong oracle only with independent authority and evidence, while keeping valid product protection active.
Test retirement: Retire tests only for retired behavior or verified equivalent replacement protection in the same candidate; counts, coverage, age and refactoring alone are insufficient.

1. Search before writing: find the existing owner for the intended layer and behavioral scope, and extend it. A parallel file for the same owner requires a justified scope split.
2. Unit tests mirror source ownership (for example `src/foo/bar.py` maps to `tests/unit/foo/test_bar.py`), following this project's convention. Integration, contract and e2e tests belong to a flow, endpoint or contract and may span several source modules.
3. Keep layers explicit through established directories, colocated paths or runner markers. Use measured runtime budgets. Choose the lowest layer that protects the required behavior; unit coverage does not replace a distinct integration or contract check.
4. Prefer observable contracts. Internal access, interaction/order assertions and boundary doubles require a meaningful boundary or diagnostic regression purpose; a repository-owned IO adapter may be such a boundary. A mocked adapter does not verify real persistence or wire behavior.
5. Classify product defects, wrong oracles, environment failures and intermittence before suppressing a test. Do not skip or weaken checks to make CI pass. Legitimate platform/feature conditions and quarantine follow the project's tracked policy, with active protection and restoration obligations preserved.
6. Derive expected results from independent approved authority. Follow Assertion protection when correcting an expectation; changing code and its oracle together cannot establish correctness.
7. Follow Test retirement before consolidation or removal. Refactors, renames and migrations preserve and retarget meaningful outcomes and independent failure modes.
8. Resource-dependent tests control incidental time, randomness and environment, isolate mutable filesystem/database state and release fixtures, async work and handles on every exit. The project's testing guide records permitted real services, setup and cleanup.

## Working Principles

### 1. Think Before Coding
Working assumptions: State material assumptions and unresolved alternatives before dependent work. Ask only for an essential decision that existing instructions or authorization cannot resolve; continue independent authorized work.
- Read related code before editing; understand the call sites
- Isolate the root cause; don't patch symptoms
- Surface unknowns instead of guessing

### 2. Simplicity First
Working simplicity: Choose the simplest design that satisfies approved requirements. Reuse existing owners and conventions; add no speculative features, abstractions or configuration. Prefer suitable existing code, standard-library facilities and maintained libraries over reimplementing solved problems. Before recommending or adopting a dependency, verify maintenance and support status, fit, compatibility, license, security and total integration cost using current official sources. Disclose unverified status; do not recommend discontinued or unverified libraries by default. Justify custom code when reuse is unsuitable or more complex.
- One responsibility per function or module
- Remove preexisting code only with evidence, within the approved task authorization and any required checks or approvals.
- Prefer composition over premature inheritance

### 3. Surgical Changes
Working scope: Limit edits to the task and owned files, match existing style and preserve unrelated work. Remove code made unused by your changes; remove preexisting code only when its removal is explicitly authorized and any required checks or approvals are satisfied.
- No drive-by refactors outside the task scope
- Preserve public APIs unless the task requires a change
- Keep diffs small and reviewable

### 4. Goal-Driven Execution
Working verification: Define observable success criteria from approved requirements. Run meaningful checks on the actual candidate and preserve independent protection. Report unavailable checks; missing required checks or deliveries keep the task open. Finish when the criteria are met.
- Write tests against behavior, not internals (evergreen tests)
- Verify with real evidence: run the code, read the output
- Stop when the criteria are met; don't gold-plate

### 5. Centralize Shared Logic
Give each shared concept an explicit owner within its domain. Before adding an external call or cross-cutting concern, find and extend the existing client or method when it represents the same concept. Keep unrelated domains separate; similar syntax alone does not justify a common abstraction.

## Key Principles

- **TypeScript strict mode enabled**: Fix type errors, don't use `any`
- **Accessibility matters**: Use semantic HTML, ARIA when needed
- **Performance conscious**: Lazy load routes, memoize expensive ops
- **Error boundaries**: Wrap risky components
- **Loading states**: Show feedback for async operations

## Additional Resources

- Architecture decisions: `docs/architecture.md`
- API patterns: `docs/api-patterns.md`
- Component guidelines: `docs/components.md`
- Testing guide: `docs/testing-guide.md`
- Deployment guide: `docs/deployment.md`
````

## Why This Works

### ✅ Best Practices Applied

1. **Detailed Structure as Single Entry Point**
   - File-by-file mapping lets Claude navigate directly to relevant code
   - References existing docs/ for deep dives on complex topics
   - Length follows necessary project guidance, not an arbitrary cap or quota

2. **Sources to Verify**
   - "React 18.2" → verifiable in package.json:12-13
   - "Vite 5.x" → verifiable in vite.config.ts
   - "Zustand" → verifiable in src/store/
   - Verify every illustrated path against the target's current locations

3. **Progressive Disclosure**
   - "See `docs/architecture.md`" instead of embedding architecture
   - "See `docs/testing-guide.md`" instead of full testing docs
   - Use the target's actual equivalent of `src/hooks/useApi.ts`

4. **Pointers Not Copies**
   - "ALWAYS follow patterns in `src/hooks/`" → points to code
   - "Use patterns in `src/store/tasks.ts`" → example reference
   - Doesn't duplicate code snippets that will go stale

5. **Delegates to Tools**
   - "DO NOT suggest code style changes: Biome handles this"
   - Doesn't embed linting rules in CLAUDE.md
   - Lets pre-commit hooks enforce standards

6. **Universal Applicability**
   - Custom hooks pattern: always relevant
   - API conventions: always relevant
   - Component patterns: always relevant
   - Doesn't include task-specific details

7. **WHAT/WHY/HOW Structure**
   - WHAT: Tech stack, structure
   - WHY: Project purpose (task management app)
   - HOW: Development workflow, testing, deployment

### ❌ Anti-Patterns Avoided

- No code duplication from README
- No embedded type definitions
- No detailed formatting rules (delegates to Biome)
- No vague guidance ("write clean code")
- No invented features
- No outdated dependencies
- No over-instruction

### Verification for a real project

Check the target's current paths, dependencies and configured commands before
publishing. Record permitted commands actually run and unavailable prerequisites;
an illustrative command or a manifest entry is not execution evidence. Verify the
selected root/nested instruction scopes and canonical-copy parity separately from
host loading or enforcement. Keep the evidence in the owned run, with unresolved
checks visible.

## Contrast: Bad CLAUDE.md Example

Here's what NOT to do:

````markdown
# Bad Example (450 lines)

## Code Style

- Use 2 spaces for indentation
- Single quotes for strings
- Semicolons required
- Max line length 80
- [... 100 more lines of style rules that Biome should handle ...]

## Component Template

```tsx
// Copy this template for every component
import React from 'react';

interface Props {
  // ...
}

export const Component: React.FC<Props> = ({ ... }) => {
  return <div>...</div>;
};
```
[PROBLEM: Code will go stale, use file reference instead]

## API Endpoints

POST /api/users
GET /api/users/:id
PUT /api/users/:id
DELETE /api/users/:id
[... 50 more lines duplicating what's in OpenAPI spec ...]

## File Structure

src/utils/helpers.ts contains utility functions
[PROBLEM: File was moved to src/lib/helpers.ts months ago]

## Testing

We plan to use Jest for testing
[PROBLEM: No approved intention is attributed, and the reader cannot distinguish planned tooling from the runner actually configured]
````

**Problems:**
- Detailed catalogs obscure the instructions and their authoritative owners
- Style rules duplicate Biome config
- Code templates that go stale
- Duplicates OpenAPI spec
- Obsolete file reference (utils → lib)
- Presents planned tooling without attribution or an implementation status
- Competing directives have no clear scope or owner

## Verification Checklist

Before accepting a CLAUDE.md, verify:

- [ ] Length proportional to project complexity (no padding or duplication)
- [ ] Project structure documents the evergreen shape (top-level layout + structural patterns + role per category); file-by-file annotation only where names alone are ambiguous, where the file is a key entry point, or to disambiguate siblings: no exhaustive trees
- [ ] All file paths exist
- [ ] Commands match their configured sources; permitted execution and unperformed checks are distinguished
- [ ] Test commands have actual prerequisites and isolation rules; project-approved thresholds and real versus controlled-boundary lanes are clear
- [ ] Instruction discovery, imports, scopes, canonical-copy synchronization and activation are verified for the actual host or labelled unknown
- [ ] Markdown guidance is distinguished from measured hook, permission, sandbox or CI enforcement
- [ ] All dependencies are accurate
- [ ] No code duplication
- [ ] No style policing
- [ ] Uses progressive disclosure
- [ ] References actual files
- [ ] No invented features
- [ ] Delegates formatting to tools
- [ ] Unverifiable claims retain their unknown status; removal requires evidence or an authorized migration that preserves the information
- [ ] Parenthetical asides use sentences or parentheses rather than clauses bracketed by dashes
