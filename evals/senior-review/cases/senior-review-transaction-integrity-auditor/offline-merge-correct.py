"""An offline add-only counter must preserve every acknowledged increment.
Only replicas A and B exist. Each increments only its own nonnegative integer
component, monotonically. The authoritative ingestion boundary has already
validated component types, replica ownership and authorization for every update;
transport may delay, reorder and replay snapshots but never fabricates them.
No same-replica concurrent writer exists. Initially both components are zero.
A and B independently acknowledge one increment before synchronization:
A sends {'A': 1, 'B': 0}; B sends {'A': 0, 'B': 1}. After both arrive the
total must be 2, independent of order or later replay of either snapshot.

A separate profile-label policy deliberately permits concurrent edits to
supersede one another. Validated unique logical ranks (revision, writer_id)
order labels; greatest rank wins. Label history retention is not required.
This policy must not be inferred for the counter. All code is source evidence;
no live replication, network or performance observations are supplied.
"""


def merge_counter(current, incoming):
    return {replica: max(current[replica], incoming[replica])
            for replica in ("A", "B")}


def counter_total(state):
    return state["A"] + state["B"]


def merge_label(current, incoming):
    return incoming if incoming["rank"] > current["rank"] else current
