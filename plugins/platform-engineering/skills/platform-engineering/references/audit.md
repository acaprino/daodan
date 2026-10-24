# Platform audit

The platform portion of `/daodan:check-health` verifies supported browser, PWA,
mobile, Electron and Tauri mechanisms. The same `platform-reviewer` participates
in senior-review with its prepared inputs; never run both paths for one assignment.

## Input and scope

Use the caller's target, snapshot, declared platforms/versions, required behavior
and run directory. A file, directory or diff retains that scope. Detect platforms
from the relevant manifests, configuration and runtime entrypoints when the caller
has not named them; distinguish installed dependencies from mechanisms actually
used. Unknown support targets remain gaps.

A security, architecture or performance focus narrows platform-specific concerns.
Generic security, performance and operational coverage belongs to the caller's
other review dimensions; report adjacent leads without claiming their completion.

## Execute

1. Inspect effective platform configuration, native interfaces, packaging and
   lifecycle paths. Read only reference sections required by those mechanisms;
   verify historical advice against actual requirements and target versions.
2. Dispatch `platform-engineering:platform-reviewer` in an isolated context through
   the caller's declared host harness. Supply target/snapshot, detected or declared
   platform scope, instructions, evidence, permissions and
   `<run>/platform-review/REPORT.md`. Multiple platforms can share one assignment
   when their implementation is shared; each supported target must be accounted for.
3. Preserve application files. Supplied browser/device results count only for their
   recorded build and conditions. Running a new app, device or probe requires the
   caller's corresponding authorization and an owned disposable environment.
4. Verify the assigned report exists and identifies examined targets, findings,
   evidence, gaps and assigned knowledge usage. Missing delivery or required input
   is failure, not a clean audit.

## Output

Use the reviewer's compact native report at `<run>/platform-review/REPORT.md`.
Include supported target/version, required operation, effective mechanism, source
location, observable impact, counterevidence and correction for each finding.
Separate static reasoning from measured behavior. Add a concise coverage/gap list
and the actual commands/results of any authorized probes. Do not manufacture a
compliance certificate or mandatory hardening checklist.

A report grants no fix, installation, signing, deployment or publication authority.
The caller consolidates platform findings with other dimensions once.
