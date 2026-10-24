"""Show gutsy benchmark details: per-case selections and critical-role diagnosis."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
j = json.loads((HERE / "runs/20261020T100258Z/gutsy-comparison.json").read_text(encoding="utf-8"))
s3 = j["suite3_c01_c11"]
modes = s3.get("modes", s3)


def short(role: str) -> str:
    return role.split(":")[-1].replace("-auditor", "").replace("abstraction-architect-agent", "abstraction")


dataset = json.loads((HERE / "runs/20261020T100258Z/dataset.json").read_text(encoding="utf-8"))
expected = {c["id"]: c["expected_roles"] for c in dataset["cases"]}
labels = {c["id"]: c["label_status"] for c in dataset["cases"]}

shown = 0
for name, m in modes.items():
    pcs = m.get("per_case_selected")
    if not pcs:
        continue
    print(f"=== {name} ===")
    for cid, sel in sorted(pcs.items()):
        exp = ", ".join(short(r) for r in expected.get(cid, [])) or "(unlabeled)"
        got = ", ".join(short(r) for r in sel) or "(none)"
        print(f"  {cid} [{labels[cid][:4]}] expected: {exp}")
        print(f"  {cid}           selected: {got}")
    print()
    shown += 1
    if shown >= 3:
        break

# Critical-role diagnosis on gutsy exact catalog th 0.50
crit = {
    "senior-review:security-auditor": "security",
    "senior-review:premise-auditor": "premise",
    "senior-review:data-integrity-auditor": "data-integrity",
}
probs = j["suite3_raw_probs"]
print("=== Critical roles: gutsy probabilities on expected cases ===")
for cid, exp in sorted(expected.items()):
    for role, shortname in crit.items():
        if role in exp:
            p = probs[cid][role]
            mark = "OK " if p >= 0.5 else "MISS"
            print(f"  {cid} {shortname:14s} P={p:.3f} {mark} (th 0.50)")
