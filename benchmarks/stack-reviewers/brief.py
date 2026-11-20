"""Scrive il brief di un job per il worker: gli stessi campi in ogni braccio, presi dal piano legato.

    python benchmarks/stack-reviewers/brief.py PREPARED.json ROLE PLUGIN CASE OUT [RIGA]

`PREPARED.json` è l'uscita di `composition.py bind`, `ROLE` il ruolo del job, `PLUGIN` la copia del plugin del
braccio, `CASE` la cartella con `tree/`, `target.diff` e `impact.json`, `OUT` dove il worker scrive.
`RIGA` è la riga di `stack-dichiarato`: la riceve quel solo braccio.
"""

import json
import sys
from pathlib import Path

TEXT = """This prompt is the whole brief of one discovery job of a senior-review branch review. Execute it once.

## Job

- job_id: {job_id} | role: {role} | scope_id: {scope_id} | input_mode: {input_mode} | permissions: {permissions}
- body_sha256: {body_sha256}
- Members (`specialist_ids`). Read each role file and apply all of its checks:
{members}
- Conventions every member applies: {plugin}/{common}. The role files name it `${{CLAUDE_PLUGIN_ROOT}}/skills/review-quality-gates/references/reviewer-common.md`: it is this file.

## Target

- Review basis: changeset. The candidate tree is {case}/tree; the change under review is {case}/target.diff, base to candidate.
- candidate: {candidate}. This is the snapshot's identity: its `root` is where the snapshot was taken, not where to read.
- Conclusion paths, where findings belong: {conclusion}
- Read scope, where to start; read anything else inside the tree that judging a finding needs: {read_scope}
- Map impact packet of the changed symbols, leads only: {case}/impact.json
- knowledge_selection: "" (none assigned; `knowledge_usage` is `[]`){extra}

## Constraints

- Read-only. Write only the output path. Run no command of the project: no test, build, install, package manager, script or interpreter on project code. No network.
- Read only inside {case}/tree, the two input files above and the role files named here. Nothing else on this machine is part of the assignment.

## Output

- output_path: {out}/{job_id}.md
- One report in the reviewer-result envelope of the conventions, with `job_id`, `specialist_ids`, `scope_id`, `candidate`, `body_sha256` and one `member_results` row per member: specialist_id, delivered or failed, complete or incomplete coverage, finding ids, gaps. Every finding has `file` and `line`.
- Return the output path and a two-line summary.
"""


def brief(prepared: dict, role: str, plugin: str, case: str, out: str, line: str = "") -> str:
    job = next(job for job in prepared["jobs"] if job["role"] == role)
    members = "\n".join(f"  - {member}: {plugin}/{job['source_bindings'][member]['path']} "
                        f"(sha256 {job['source_bindings'][member]['sha256']})" for member in job["specialist_ids"])
    grounding = prepared["grounding"]
    return TEXT.format(**{key: job[key] for key in ("job_id", "role", "scope_id", "input_mode", "permissions",
                                                    "body_sha256")},
                       members=members, plugin=plugin, common=prepared["common"]["path"], case=case, out=out,
                       candidate=json.dumps(job["candidate"]), conclusion=json.dumps(grounding["conclusion_paths"]),
                       read_scope=json.dumps(grounding["read_scope"]),
                       extra=f"\n- Stack the map declares for the unit: {line}" if line else "")


if __name__ == "__main__":
    prepared_path, role, plugin, case, out, *line = sys.argv[1:]
    text = brief(json.loads(Path(prepared_path).read_text(encoding="utf-8")), role, plugin, case, out, *line)
    sys.stdout.buffer.write(text.encode("utf-8"))  # LF on every platform: the brief's bytes are the same in each arm
