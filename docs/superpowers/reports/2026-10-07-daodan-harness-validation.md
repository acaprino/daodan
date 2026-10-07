# Coherent harness validation

Candidate release: Daodan 30.0.1. Baseline: e9157e98. The initial 30.0.0 candidate
was pushed and failed CI before release publication.

The marketplace now exposes five complete project paths and canonical owners for
operational records, durable knowledge, universal review, extended review and tests.
Three knowledge kernels are replaced by project-knowledge; Python's duplicate test
writer is retired. Useful language, framework and domain extras remain available.

## Dependency cost

Counts include the entry plugin itself and all required local dependencies.

| Entry | Local plugins | External plugin bundles |
|---|---:|---:|
| project-lifecycle | 10 | 3 |
| project-knowledge | 8 | 2 |
| senior-review | 6 | 2 |
| review-plus | 10 | 2 |
| python-development | 3 | 2 |

The external bundles are mattpocock-skills@mattpocock,
developer-essentials@claude-code-workflows and, for lifecycle development,
superpowers@claude-plugins-official. These counts do not measure token use or
guarantee upstream availability on a particular host. Methods require preflight.

## Evidence and final gates

Baseline deterministic suite: 367 tests passed, 2 skipped. The first baseline run
used an unwritable system temporary directory; it was rerun with the bundled
Python and a dedicated ignored workspace temporary directory. Environment failures
were not treated as product defects.

Initial frozen-source suite: 464 tests, 459 passed and 5 skipped, in 210.903 seconds.
The two hardlink cases skipped by the sandbox were then rerun with filesystem
permission on exclusively owned temporary fixtures; both passed. Three cases
remain unavailable here: the POSIX executable-bit scenario and two optional
tree-sitter language parsers. The POSIX regression is retained for Linux CI, and
the parser fallback paths were exercised.

All five host packages rebuild and reproduce at marketplace 30.0.1. There are 41
kernels and 41 packages per host, with no retired knowledge package directory.
Support binding reports no unsupported required component. Dependency validation
accounts for 250 cross-plugin runtime references. Registration, bundled paths,
23 fact anchors and host vocabulary pass. Codex instruction parity passes.
Copilot's guard regression suite passes 36/36; this does not mean its hook is wired
in an installed host. Local documentation links pass in 48 documents.

Intermediate failures found obsolete generated directories, a stale fixed
plugin-count assertion, unsynchronized generated instructions and a composition
binding gap. These were repaired in source rather than baselined away. The final
whole suite and drift gate were rerun after the fixes.

## Independent whole-change findings

The first Linux CI run exposed a test-fixture cleanup incompatibility with its
Python 3.11 runtime: `shutil.rmtree(onexc=...)` requires Python 3.12. The cleanup
callback now uses the supported `onerror` argument. That targeted suite passes
locally: 34 cases with two platform skips. A compatibility audit also found that
Python 3.11 lacks Path.is_junction on Windows. Both the protocol and retention
helpers now check lstat reparse-point attributes independently of that API. Their patch and release versions
advance rather than rewriting the already pushed commit. CI is rerun on 30.0.1.

Corrected protocol suite: 35 cases pass locally (three sandbox/platform skips).
The new junction case was separately exercised on a real owned Windows junction
with the newer junction API unavailable. It reproduced the old escape and confirms
the corrected helper refuses both live and dangling junctions, preserving external
evidence and the previous record revision. Final packages rebuild at 30.0.1.
The retention helper has the same attribute check. Its 22-case suite passes;
a real same-run junction alias to required evidence is independently rejected
while preserving the exact protected bytes. Protection keys resolve actual paths
before comparison.

Both new junction regressions were rerun together on real Windows junctions after
the final rebuild: 2 tests passed, with no skips. The final deterministic drift,
dependency, bundled-path, registration, fact-anchor, host-vocabulary and instruction
parity checks pass.

Two fresh reviewers examined domain integration and operational safety. Confirmed
findings produced these changes:

- Composed review and knowledge methods declare all allowable named workers in
  sidecar dispatch metadata. Generic isolated tasks use one protocol-owned role.
  Scheduling phases no longer determine the whole reusable dispatch inventory.
  Critics can consume coordinator-declared reports; independent reviewers cannot
  consume peer results before their own delivery. Intermediate report ownership
  and exclusive final-report ownership are explicit.
- Delivered workers require real run-owned output. Remote checks require an actual
  source revision whose committed inputs match the candidate, including dirty and
  untracked content. Git index flags do not replace comparison with actual blobs.
- Retention compares canonical path identities, checks ancestor links and exact
  protocol/project/output bindings, and refuses to overwrite evidence or existing
  files when creating its plan. Owned targets are rechecked against original records.
- Instruction examples and canonical testing agree on source ownership at unit,
  behavioral ownership above unit and protection-preserving retirement. A fact
  anchor now guards the independently loaded ownership statements.
- Retired generated packages are pruned only after all hosts validate and render,
  using confined paths and compiler provenance. Unknown directories are not deleted.

## Practical limits

No installed execution of the new lifecycle paths has been measured on the five
hosts. Existing universal migration probes are historical evidence for their
recorded versions. Source rendering, catalogs, generated dispatch resources and
loader tests establish structural integration; they do not establish live model
behavior, external upstream availability or Tri-Tech Code runtime integration.

Behavioral cases are authored under evals/project-lifecycle, evals/testing and
evals/project-knowledge. They are not counted as live executed cases. Kernel
workflows remain prompt-driven coordination, with mechanically enforced boundaries
for the helpers and explicit prompt obligations for other tool actions.

Private app output roots outside the project remain unsupported until an adapter
permission binding is proved. Tri-Tech Code is an external OpenCode V2 consumer.
X-ray remains static, with runtime coverage explicitly absent. Human permission
provenance, correctness of a test oracle and truth of a summary require actual
evidence; valid JSON alone cannot prove them.

Retention reports content bytes moved and deleted. Quarantine reports zero bytes
deleted. File sizes alone are not a measurement of physical space recovered.

## Experiment consolidation

Subsystem validation records and temporary fixture output are owned by this
implementation session. Meaningful results are reduced into this report before
removing that disposable scratch. Source fixtures and behavioral cases remain as
development assets. Preexisting user files, including .playwright-mcp/, are outside
this cleanup. The final owned scratch inventory contained 129 files and 137,226
content bytes, plus one link used to exercise the ancestor-escape regression.
Subsystem workers separately recorded removal of 44,681 and 59,214 owned content
bytes. These are content totals, not measurements of physical space recovered.
Local final gates are complete; Git publication and release status are
reported separately by the publication workflow and the delivery message.
