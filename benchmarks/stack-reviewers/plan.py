"""Ricalcola il piano di un caso dalla mappa: i due snapshot, il diff del target, e ne scrive il roster.

    python benchmarks/stack-reviewers/plan.py BASE.sqlite CANDIDATE.sqlite TARGET.diff OUT

I due snapshot sono della stessa cartella, scritti prima e dopo il commit target con `snapshot.py write --no-engine`:
`review_roster.py` rifiuta un confronto fra radici diverse. In `OUT` restano `stale.json`, `impact.json`,
`technologies.json`, `files.json`, `context.json` e `roster.json`. Stampa rigor, job con i membri, le voci di stack
soppresse o tenute per l'uso e la riga di `stack-dichiarato` per ogni unità che il diff tocca.
"""

import json
import subprocess
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[2] / "daodan/core"
sys.path.insert(0, str(CORE))

import composition  # noqa: E402
import review_roster  # noqa: E402


def tool(script: str, *args: str) -> str:
    return subprocess.run([sys.executable, "-B", str(CORE / script), *args], check=True, capture_output=True,
                          text=True, encoding="utf-8").stdout


def main(base: str, candidate: str, diff: str, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    stale = json.loads(tool("snapshot.py", "stale-callers", candidate, "--base", base))
    (out / "stale.json").write_text(json.dumps(stale), encoding="utf-8")
    targets = [arg for row in stale["changed"] if row.get("new") is not None for arg in ("--target", row["symbol_id"])]
    (out / "impact.json").write_text(tool("snapshot.py", "edit-impact", candidate, "--no-source", *targets),
                                     encoding="utf-8")
    tool("snapshot.py", "technologies", candidate, "--out", str(out / "technologies.json"))
    tool("snapshot.py", "files", candidate, "--out", str(out / "files.json"))
    catalog = composition.load_catalog(composition.DEFAULT_ROOT)
    context = {"candidate": stale["candidate"], "base": stale["base"], "stale_callers": stale, "catalog": catalog}
    (out / "context.json").write_text(json.dumps(context), encoding="utf-8")
    tool("review_roster.py", "compute", "--shape", "branch", "--rigor", "standard", "--diff", diff,
         "--impact", str(out / "impact.json"), "--technologies", str(out / "technologies.json"),
         "--files", str(out / "files.json"), "--context", str(out / "context.json"), "--out", str(out / "roster.json"))

    roster = json.loads((out / "roster.json").read_text(encoding="utf-8"))
    entries = {row["id"]: row for row in catalog["entries"]}
    print(f"rigor {roster['rigor']}, {len(roster['roster'])} job, mappa {roster['signals']['map_available']}")
    for row in roster["signals"]["suppressed"]:
        print(f"soppresso {row['role'].removeprefix('senior-review:')}: {row['reason']} ({len(row['checked'])} file)")
    for gap in roster["gaps"]:
        if gap.split(":", 1)[0] in review_roster.TECHNOLOGY_IMPORTS:
            print(f"tenuto: {gap}")
    for role in roster["roster"]:
        print(f"  {role.removeprefix('senior-review:')} {len(composition.leaf_roles(role, entries))}")
    changed = [row["path"] for row in roster["grounding"]["changes"]]
    for unit in json.loads((out / "technologies.json").read_text(encoding="utf-8"))["units"]:
        if not any(review_roster.in_scope(path, unit["paths"]) for path in changed):
            continue
        known = list(dict.fromkeys(f"{lib['id']} {lib.get('version', '?')}" for lib in unit["libraries"]
                                   if lib.get("id")))
        print(f"stack di {', '.join(unit['paths'])}: framework {', '.join(unit['frameworks']) or 'nessuno'}; "
              f"librerie {', '.join(known) or 'nessuna'}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], Path(sys.argv[4]))
