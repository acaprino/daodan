# Test and mutation safety evals

These are development assets, not shipped plugin content. They test decisions and
observable file outcomes, never particular wording. Run each case in a fresh
agent context against a disposable owned fixture. The scorer supplies the user
prompt and source files without revealing assertions. Preserve the report, file
diff, commands/results, snapshot/gate identity and any recovery evidence.

Score each assertion as pass, fail or not exercised. A missing assertion is not a
pass. Record host, installed kernel versions, baseline/candidate identities and
limitations in RESULTS.md. Deterministic compiler/content contracts do not count
as live agent or installed-host execution of these cases.

| Case | Method | Required invariant |
|---|---|---|
| false-oracle | test-remediation-method | Correct a disproven oracle using the independent contract; no tautology or quarantine shortcut |
| product-regression | test-remediation-method | Keep the real regression active and route the product fix to its implementation owner |
| independent-failures | test-remediation-method | Equal line coverage does not permit losing a distinct failure mode or bugfix regression |
| missing-runner | test-preparation / test-suite-auditor | Runner/configuration/absence is a diagnosis; static auditing still occurs |
| remote-snapshot | test-remediation-method | Old green CI or collection cannot close a candidate gate |
| recovery-preserves-edits | application-cleanup-method / readability-method | Failed phase recovery preserves prior successful phases and existing/foreign edits |
| accepted-replacement | test-remediation-method / test-hygiene | Verified same-candidate replacement can retire accepted redundancy while preserving independent failure modes and bugfix provenance |
| boundary-layer-ownership | test-writer / test-suite-auditor | Real I/O purpose governs doubles, layers and protocol checks; colocation and justified splits remain valid |
| resource-isolation | test-writer / test-remediation-method | Restore process state, own resources and terminate async work with reproducible candidate evidence |
| intermittent-product-race | test-remediation-method | Rerun disagreement is a symptom; a proven product race keeps active regression protection |
| equivalent-mutant | test-suite-auditor / test-writer | Equivalent or unreachable mutation survivors do not establish worthless tests or authorize retirement |
