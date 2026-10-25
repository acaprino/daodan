# Native result wrappers

Keep each raw specialist report unchanged. Wrap it with role, role_version,
input_sha256, scope/snapshot, status, raw_report path/hash, wrapper_version, evidence
and gaps. Native payload stays domain-owned. A successful process without a required
report is missing, and an absent field stays unknown instead of a default value.

Use scripts/native_reports.py for provenance and the seven-way workspace mapping.
Workspace operations retain their native disposition:
KEEP, KEEP+IGNORE, REMOVE, REMOVE+IGNORE, UNIGNORE, REVIEW and REPORT-ONLY.
The generic plan decision is additional metadata. REPORT-ONLY never becomes an
executable Git-state action, and REVIEW never becomes an approved deletion.
Quarantine is not permanent removal.

A contract test compares the converter vocabulary with the canonical workspace
auditor output. Format changes require updating both in one change. Other payloads
are not coerced into this workspace schema.

Evidence class and premise provenance remain explicit. Consolidation uses
senior-review:review-consolidation to distinguish independently derived agreement
from echoed context, retaining conflicting conclusions and unsupported claims.

