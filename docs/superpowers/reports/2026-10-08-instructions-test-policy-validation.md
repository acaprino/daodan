# Instruction and test-policy validation

Validation on 2026-10-08 for marketplace 32.1.0: testing 3.1.0,
project-knowledge 1.1.0 and project-lifecycle 1.2.0. Source baseline:
`b586afc4b8fcae22130df43135318a38a4fbb6b4`. The candidate includes the kernels,
the portable README prompt and research note, generated packages for all five
hosts, development eval cases and mechanical policy-drift regressions.

## Mechanical verification

- Full standard-library suite: 504 tests passed, with one expected skip for POSIX
  executable-state behavior on Windows. Node 24.14.1 was available; the OpenCode
  loader tests ran through the Python suite.
- Copilot write-confinement implementation: 36/36 cases passed.
- Dependency declarations, bundled paths, component registration, fact anchors
  and neutral host vocabulary passed their consistency checks.
- All five packages were regenerated. Deterministic build parity and plugin-doc
  and Codex-instruction parity passed. Generated output is mechanical distribution
  evidence, not proof of installed-host behavior.
- Three policy-anchor regressions exercise changed independent copies, a missing
  owner and harmless value normalization. They do not test model compliance or
  semantic equivalence of arbitrary paraphrases.

The sandbox initially denied default temporary directories, a generated catalog
under protected `.agents`, and an asyncio event-loop initialization. Temporary
verification files used the owned project scratch area; authorized build/test
execution outside the sandbox supplied the required local mechanisms. These
environment failures were not classified as product defects in Daodan.

## Independent source review

A separate reviewer inspected the changed canonical methods, condensed instruction
copies, lifecycle composition, drift tests, evals and documentation. Two low-severity
description inconsistencies remained: source-file ownership advertised for every
consolidation layer, and quarantine/consolidation advertised as every audit remedy.
Both descriptions were corrected and independently reread; zero findings remained.
The review checked the research note's 21 distinct external primary URLs and
targeted instruction-loading claims. It did not execute a complete installed-host
senior-review workflow.

## Fresh source-context audit probes

Two agents received separate synthetic fixtures and canonical source instructions
without the eval scoring assertions. Fixtures remained unchanged. These were
audit-only decision probes; their deliberately defective applications were not
repaired. Operational reports preserve commands, input hashes and unavailable
checks in the owned run. Model identity was not exposed by the dispatch interface.

| Probe | Observed evidence and decision | Unexercised scope |
|---|---|---|
| Testing | Flat shipping authority specifies 1200 cents while a test expects 1100. A controlled two-debit barrier leaves 90 instead of the approved 80. Three comparable bounded runs retain both failures; SQLite asserts persistence then errors during cleanup because a database handle remains open. The service check with a controlled I/O adapter passes. The audit separates wrong oracle, product race and resource-lifecycle failure; preserves real integration and unit protection, established colocation and a valid boundary double; an equivalent `+ 0` mutant does not justify removal. | No test/product edits, accepted replacement, quarantine, recovery or real installed-host dispatch. The integration lane has a cleanup failure and is not a clean pass. |
| Instructions | Canonical CLAUDE and generated AGENTS bytes agree; the supplied synthetic session still holds older root instructions and loaded neither the applicable handwritten nested policy nor linked guide. Fixture configuration supplies no runtime guard. The audit disproves runner/layout/coverage/oracle/import claims from approved project and host evidence, preserves nested ownership, and keeps activation/enforcement/production gaps explicit. A single wrong-expectation unit test fails. | No generator write, corrected candidate, restart, actual host loading/precedence probe, guard exercise or credentialed production verification. |

The fixture host is explicitly synthetic. Supplied discovery/configuration/session
evidence establishes only fixture conclusions. These probes partially exercise the
decision invariants specified in [testing evals](../../../evals/testing/README.md)
and [project-knowledge evals](../../../evals/project-knowledge/README.md); they do
not mark every case passed. Lifecycle's new global-rationalization case remains
specified without a complete workflow execution.

## Distribution limits

Claude Code, Codex, Copilot, Pi and OpenCode packages reproduce from their canonical
sources. No fresh installed-host probe of the complete workflow or external upstream
method availability was performed on all five hosts. Users must resolve the actual
host's dependencies and instruction activation; a missing mandatory runtime check
continues to prevent downstream completion. These limits are separate from the
completed source, compiler and scoped decision checks above.
