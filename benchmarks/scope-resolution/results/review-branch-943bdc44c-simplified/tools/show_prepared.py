"""Print the prepared review's jobs and policy."""
import json
import sys

r = json.load(open(sys.argv[1], encoding="utf-8"))
print(r["tier"], r["verification"], r["critic"], r["roster"], r.get("selection"))
print(r["common"])
for j in r["jobs"]:
    print(j["job_id"], j["role"], j["specialist_ids"], j["output_path"], j["status"], j["body_sha256"][:12], j["source_bindings"])
print("required", r["required_specialists"])
print("gaps", r["gaps"])
