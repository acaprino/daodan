# Working principles

Principles 1-4 derive from multica-ai/andrej-karpathy-skills (MIT), snapshot
2026-05-17. Their sub-bullets and principle 5 are local adaptations.

Use this block when creating instructions if the project has no equivalent
working guidance. Preserve equivalent project-specific guidance when maintaining
an existing file. Missing headings or different wording alone are not defects.

The original local execution wording below is owned by
`project-protocol:project-protocol` (already required). Equivalent guidance
in existing target projects remains valid.

```markdown
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
- Before building a common capability, check existing project implementations, standard-library facilities and dependencies already in use. Evaluate established libraries when those do not meet the requirement; honor project dependency constraints.
- Before recommending or adopting a library, check current official sources for archival, deprecation, supported releases and meaningful maintenance. Record the source and check date instead of relying on model memory. If verification is unavailable, state the gap and do not present the library as a verified recommendation. A stable library need not release frequently; recent commits or popularity alone do not prove suitability.
- Compare the total cost of reuse, including transitive dependencies, adaptation, upgrades and long-term ownership. Prefer custom code when it is simpler overall or no suitable solution exists, and record the concrete reason.

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
```
