import json, sys
p = sys.argv[1]
s = json.load(open(p, encoding="utf-8"))
for kv in sys.argv[2:]:
    k, v = kv.split("=", 1)
    if k == "file": s["files_created"].append(v)
    elif k == "current_phase": s["current_phase"] = v
    elif k == "status": s["status"] = v
    else: s["phases"][k] = v
json.dump(s, open(p, "w", encoding="utf-8"), indent=2)
print(s["phases"])
