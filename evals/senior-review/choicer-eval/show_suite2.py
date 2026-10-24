"""Show Suite 2 (team problems) results from gutsy-comparison.json."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
j = json.loads((HERE / "runs/20261020T100258Z/gutsy-comparison.json").read_text(encoding="utf-8"))
s2 = j.get("suite2_grounded_noul", {})

for th, v in sorted(s2.items()):
    print(f"=== threshold {th} ===")
    print(f"acceptable_teams: {v['acceptable_teams']}")
    print(f"mandatory_found: {v['mandatory_found']}")
    print(f"out_of_scope_selections: {v['out_of_scope_selections']} (mean per team {v['mean_out_of_scope_per_team']})")
    print(f"total_selected: {v['total_selected']}")

print()
print("=== per-team detail at threshold 0.50 ===")
for t in s2.get("0.50", {}).get("per_team", []):
    missing = ", ".join(r.split(":")[-1].replace("-auditor", "") for r in t["missing"]) or "none"
    oos = ", ".join(r.split(":")[-1].replace("-auditor", "").replace("abstraction-architect-agent", "abstraction") for r in t["out_of_scope"]) or "none"
    print(f"{t['id']}: req={t['required_found']} missing=({missing}) out_of_scope=({oos}) acceptable={t['acceptable']}")
