# Stack dimensions

Use candidate-grounding's basis, scope and evidence rules. Inspect the affected
package/configuration at the candidate snapshot; unrelated monorepo dependencies
do not activate dimensions. Resolve computed identities through these bindings:
one dispatch round and ledger, no extra roles or clean skips for unknown signals.

| Dimension ID | Automatic activation evidence | Role to dispatch |
|---|---|---|
| react | React in the relevant package and target includes JSX/TSX or affected React runtime | unavailable in the imported two-owner baseline until senior-review owns equivalent React micro skills; record activation evidence and leave the specialist coverage as a declared gap |
| typescript | Relevant TypeScript configuration and target includes TS/TSX/type contracts | unavailable in the imported two-owner baseline until senior-review owns equivalent TypeScript micro skills; record activation evidence and leave the specialist coverage as a declared gap |
| platform | Roster evidence for browser/PWA storage, service workers, client security policy, mobile capabilities or Electron/Tauri shell integration | unavailable in the imported two-owner baseline until senior-review owns equivalent platform/Tauri micro skills; record activation evidence and leave the specialist coverage as a declared gap |
| python | Target includes `.py` or `.pyi` files, or the relevant package declares `pyproject.toml`, `setup.py`, `uv.lock` or `requirements*.txt` | `senior-review:code-auditor` through the host isolated-worker binding when Python-specific evidence is needed; former python-development methods are unavailable and remain declared gaps |
| dependencies | The candidate changes a manifest or lockfile: `pyproject.toml`, `uv.lock`, `poetry.lock`, `requirements*.txt`, `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock`, `Cargo.toml`, `Cargo.lock`, `go.mod`, `go.sum`, `Gemfile.lock`, `composer.lock`, `pom.xml`, `build.gradle*`, `*.csproj` | `senior-review:dependency-usage-auditor`; ecosystem-specific audit tooling from former providers is unavailable and remains a declared gap |

Dependencies bind through `senior-review:dependency-usage-auditor`. Python and
any future stack specialist use the host isolated-worker binding when available.
Carry skill identities, audit-only mode, evidence-pack paths and the report
path in its brief, as for other inline lenses.

Select each dimension once. False signals need code-based skip reasons;
unreadable/ambiguous signals remain gaps. Required providers supply roles
regardless of selection. An unavailable selected role is a failed delivery,
never a skip or generic substitute.

Composition uses the existing catalog and `required_specialists`
with scope/evidence. Merge identical member/scope obligations only. Requirements
and sources identify canonical specialists; unknown applicability, missing
prerequisites and graph omissions remain gaps. Light permits one discovery;
obligations that cannot fit stay incomplete and require branch review.

Record explicit specialist requests and compare them with the computed roster;
requests cannot remove its floor or bypass allowed dispatch. Normalize legacy
`react-perf`/`react-performance` to `react` and `ts-safety`/`type-safety` to
`typescript`. General performance belongs to `senior-review:performance-auditor`,
including query and algorithm cost in a React application. React's optimizer
retains component/render work; both may run when each is selected. Platform
reviews client capabilities and cross-platform behavior. Service operation,
deployment and recovery belong to `senior-review:operability-auditor`.

--no-context removes shared context from these workers
as it does from other reviewers; it does not remove the dimensions. --fast can reduce optional verification work, never the required roster or gates.

The canonical roles retain their own knowledge, analysis method and native output.
Before dispatch, load review-consolidation's `references/stack-findings.md` inside
that skill. Include its native review field requirements and severity mapping in
the brief, alongside the role's own report format. Preserve the original report;
the existing evidenced-finding envelope carries the fields required by this review.
Supply the prepared target, diff, intent, project instructions, run identity,
snapshot and assigned intermediate report path. Add the variant's shared intent
and scope instructions from review-method; finding fields arrive with the job's
`common` binding. Include context paths only when context is enabled. Quantitative performance
claims need the evidence required by review-quality-gates. Missing runtime
measurements remain gaps, not invented results.

Include these members in the validated jobs with the other selected dimensions.
Dispatch each job once in its isolated context, preserving each member's native method.
Do not run their standalone workflows, repeat preparation or publish another
report. Consolidation waits for every selected reviewer to deliver or fail, and
preserves source role, severity, evidence and premise provenance in the same native
finding set. Independent reviewers do not receive peer findings before delivery.
