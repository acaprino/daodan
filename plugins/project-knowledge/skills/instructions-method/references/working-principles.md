# Working principles

Principles 1-4 derive from multica-ai/andrej-karpathy-skills (MIT), snapshot
2026-05-17. Their sub-bullets and principle 5 are local adaptations.

Use this block when creating instructions if the project has no equivalent
working guidance. Preserve equivalent project-specific guidance when maintaining
an existing file. Missing headings or different wording alone are not defects.

The original local execution wording below is owned by
`work-controller:work-record` (already required). Equivalent guidance
in existing target projects remains valid.

```markdown
## Working Principles

### 1. Think Before Coding
Working assumptions: State material assumptions and unresolved alternatives before dependent work. Ask only for an essential decision that existing instructions or authorization cannot resolve; continue independent authorized work.
- Read related code before editing; understand the call sites
- Isolate the root cause; don't patch symptoms
- Surface unknowns instead of guessing

### 2. Simplicity First
Working simplicity: Choose the simplest design that satisfies approved requirements and existing contracts. Prefer, in order, suitable project code and conventions, platform or standard-library facilities, dependencies already available, then the least new code. Explain an exception when an earlier option cannot meet the requirement or is more complex overall. Reuse existing owners; add no speculative features, abstractions or configuration. Preserve boundary validation, data-loss prevention, security and accessibility. Before recommending or adopting a dependency, verify maintenance and support status, fit, compatibility, license, security and total integration cost using current official sources. Disclose unverified status; do not recommend discontinued or unverified libraries by default.
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

### 6. Redesign Instead of Patching
Working redesign: Fix the cause, never the symptom. When a defect shows that a script, skill, contract or workflow is shaped wrong for its problem, redesign that unit from the ground up so it solves the whole problem, instead of patching the case at hand. A patch that leaves the design wrong is debt, not a fix; record the redesign decision and its reason.
- A fix that only special-cases the failing input leaves the next input to fail the same way
- When a unit needs a second patch for the same class of defect, redesign the unit
- Keep the redesign within the task's authorization and verify it against the original failure

### 5. Centralize Shared Logic
Give each shared concept an explicit owner within its domain. Before adding an external call or cross-cutting concern, find and extend the existing client or method when it represents the same concept. Keep unrelated domains separate; similar syntax alone does not justify a common abstraction.
```
