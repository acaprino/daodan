# abstraction-architect:abstraction-fit-auditor

## Scope and setup

Static content review. Supply only one variant directory, the reviewer body, common conventions and the assigned report path. The target file contains the product requirement and source/configuration or an explicitly supplied evidence packet. Do not supply this oracle, the other variant, peer output or scorecard to the worker. No installs, application execution, edits or external services are permitted.

T0 coverage: PR180–188, PR193–197, PR198–227 form track, PR325–326 (initial pair: canonical parser bypass). This focused pair probes the mechanism below, not every referenced rule. Remaining controls need their own exercised evidence before comprehensive qualification.

## Defect oracle

The declared canonical MoneyParser already handles required spaces and decimal cents, but checkout.py reimplements conversion using float, bypassing its accepted contract. D6 needs this one bypass, not three copies. Mention the actual whitespace/value behavior only if supported by source.

## Correct countercase

checkout delegates to the canonical parser. A tax percentage parser has a separately declared input contract and is not competing prior art. Do not claim D5 from two unrelated mechanisms.

## Delivery and limits

Expected: causal source citations, examined controls, no invented runtime execution, report persisted at the assigned path. Correct variant: no finding for the repaired mechanism. Missing a required target or requirement must remain an explicit gap, never a clean result. Exclude unrelated advice. Score independently by mechanism using the existing scorecard; this file records expectations, not a pass.

## Additional independent scenarios

Supply `scenarios.md` from the selected variant along with its target. These are explicit synthetic source/evidence packets; commands/results are supplied facts, not executions by the reviewer.

- **third-mechanism (PR180, PR188)**: D5 admits the three independent repeated mechanisms after A1–A5; state sites and change cost. Countercase: Two copies alone do not meet D5 and must not be mislabeled D6.
- **caller-friction (PR182, PR198–209)**: D7 is the cross-file caller bypass/contract friction, independent of copy count. Countercase: One implementation can define a useful boundary; do not flag it or demand three implementations.

## Required map preparation

Before dispatch, the coordinator resolves the project-bound map root using the canonical map-method migration contract and prepares a distinct run for the selected variant. Generate an actual manifest with `python plugins/codebase-map/skills/map-method/scripts/snapshot.py write <selected-variant-directory> --out <owned-map-run>/source-manifest.json --format json`. Bind that run, resolved root, exact variant target and manifest digest in the assignment. Supply source-confirmed inventory/context only, without this oracle or conclusions from the other variant. Current manifest plus the variant files permit independent semantic discovery; no preexisting concept index is required. If the provider/root/run cannot be established, record failed input coverage; do not treat a synthetic index, another variant’s manifest or inventory alone as a complete semantic map. The stale/foreign-index scenario is a separate negative-input probe and must not contaminate the valid primary run binding.

## Correct context completion before dispatch

Correct third-mechanism said three modules exist and then only two exist. Replace the retained defect preamble with the actual declared two-copy boundary; a future third remains hypothetical. No code or intended D5 gate changed. Old preparations remain unexecuted and byte-preserved. Fresh correct context receives its own actual partial static map, never a peer/old map. No reviewer body, common or runtime claim changed.
