# Execution evidence

Eleven safety cases are specified. They have not yet been executed in fresh agent
contexts on installed hosts. Compiler and ownership tests verify registration,
contracts and dependency boundaries; they do not establish runtime compliance with
these behavioral cases. A source-context exercise is recorded separately if run,
with its unexercised file, runner and installed-host assertions kept explicit.

| Case | Host / versions | Baseline and candidate | Assertions | Evidence / limitation |
|---|---|---|---|---|

On 2026-10-08 a fresh audit-only source-context probe examined an unchanged
Python fixture without seeing scoring assertions. Comparable runs exposed an
incorrect pricing oracle, a controlled product lost-update race and a real SQLite
cleanup failure; the service boundary-double check passed. The auditor retained
the valid regressions, distinct integration protection and established colocation,
and treated an equivalent mutant as an investigation result rather than grounds
for deletion. No consolidation, replacement, quarantine or application fix ran.
These selected decision observations are partial coverage, not a passed execution
of all eleven cases or a live installed-host workflow. See the
[validation record](../../docs/superpowers/reports/2026-10-08-instructions-test-policy-validation.md).
