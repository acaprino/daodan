> `<plugin-root>` names the directory that holds this plugin's `.codex-plugin/plugin.json`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

# Consolidate

Reduce experiments and run output into verified knowledge before disposing of data.
This is local evidence curation, distinct from the web research pipeline.

For each attempt preserve goal, source snapshot, environment/conditions, exact
command or procedure, inputs, outcome, errors, relevant measurements, decision,
limits and reproduction instructions. Compare the proposed summary with original
evidence, including failed attempts. Contradictory results remain visible.
Past results do not replace executable regression tests.

Keep sufficient evidence inside the run, or copy a minimal verified subset from an
external evidence source with provenance. Reference external heavy data; do not
claim ownership of it. Durable conclusions go through project-knowledge's authority
and documentation methods. Temporary status, attempts and pending work remain in
the run rather than AGENTS.md/CLAUDE.md.

## Retention records

Write artifacts.json: schema daodan/artifacts/v1, run_id and artifacts entries
{path, owned_by, sha256, classification, status, reproduce}. Paths are relative to
this run and files exclusively created/owned by this run. Concluded disposable
classes are reproducible-output and completed-output; reproduction conditions are
mandatory for the former. Unknown ownership, cache, resume data and unresolved
evidence remain retained.

Write summary.json: schema daodan/evidence-summary/v1, run_id, summary,
verification {status:verified, by:<coordinator>}, retained_evidence [{path,sha256}],
required_artifacts and unresolved. Semantic verification requires reading sources;
writing a verified flag is not the verification. Keep a nonempty evidence subset.
Outstanding evidence blocks retention until explicitly resolved and retained.

Run the installed helper:
python "<plugin-root>/skills/lifecycle-method/scripts/artifacts.py" plan --run RUN --manifest artifacts.json --report summary.json
This writes retention-plan.json. Show every proposed path/reason and potential
byte total; default planning makes no removal.

After authorization, apply quarantine with:
python "<plugin-root>/skills/lifecycle-method/scripts/artifacts.py" apply --run RUN --plan retention-plan.json
This moves data within the run and reports zero bytes deleted.

Permanent deletion is a separate explicit --purge grant, not implied by --fix.
Write authorization.json {run_id, operation:purge, paths:[exact relative paths],
source:{kind:user,reference:<actual permission>}} and invoke apply with --purge
--authorization authorization.json. Never fabricate permission from a generic
cleanup request. Only concluded owned outputs in the original manifest are eligible.

The helper rejects traversal, symlinks/reparse points, hardlinks, changed files,
changed summary/evidence, unresolved references and quarantine collisions. It
writes a receipt before mutation and resumes prepared operations idempotently.
A stale retention lock requires proving the owning process stopped before recovery;
do not delete a live session's lock. Artifact fingerprints and confinement are
mechanical; truth of the summary and of human permission remains the coordinator's
responsibility.

repo-hygiene:repo-hygiene handles separate filesystem/Git hygiene and preserves
untracked quarantine. It does not interpret lifecycle state or purge its artifacts.
Record content bytes moved/deleted, retained evidence, result and remaining limits.
Measure filesystem free-space changes separately when needed; deleted file sizes
do not prove physical space recovered on a compressed or concurrently used volume.

