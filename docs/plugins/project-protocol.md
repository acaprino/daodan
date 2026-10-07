# Project Protocol

A dependency-free leaf owns operational work and project-result contracts,
run identities, exact file snapshots, state transitions, delivery accounting,
candidate gates and recovery obligations. It does not define domain findings or
execute automatic Git rollback. Its isolated-worker role provides the neutral
task, owned-scope and report contract for explicitly declared generic workers.

Canonical schemas live in contracts/ and are explicitly exported by plugin.toml.
Consumers declare shared_schemas rather than copying required fields into their
own kernels. The seven senior-review schemas remain review-domain payloads.

Load project-protocol:project-protocol. Its stdlib run_state.py exposes init,
show, update, validate, resume and snapshot. Payloads are JSON; updates require an
expected revision and use locking plus atomic replacement. Roots are confined to a
dedicated directory in the project, with .daodan-root sentinel and exact run ID.

Declare expected deliveries and required gates. Mandatory checks can only be added,
not removed. A delivered worker must identify an existing run-owned report.
Completion requires every delivery, current candidate-bound successful
gates, closed phases and no interruption. Result validation correlates the envelope
with the persisted record; it does not prove the payload's semantic truth.

Baseline, pre-phase snapshot/SHA and exclusive workspace ownership precede mutation.
Recovery preserves prior successful phases and preexisting/foreign files.
Remote checks identify the exact candidate revision and job attempt, and require
the candidate inputs to match that committed revision. Published
changes need authorized revert instead of history rewrite.

Helpers mechanically confine their own writes. Other agent tools remain subject
to prompt obligations until an installed runtime enforcement mechanism is proved.

