"""Call one read-only Codebase Map MapService operation (same backend as the MCP tools) and print JSON.
Usage: python -B map_call.py <operation> '<json kwargs>' [out.json]"""
import json, sys, traceback
sys.path.insert(0, "D:/Projects/daodan/plugins/codebase-map/skills/map/scripts")
op, kwargs = sys.argv[1], json.loads(sys.argv[2])
out = sys.argv[3] if len(sys.argv) > 3 else None
ALLOWED = {"runs", "status", "search", "modules", "outline", "graph", "read", "edit_impact", "symbols_at", "stale_callers", "scope", "meta_query", "diff"}
assert op in ALLOWED, op
try:
    import mcp_service
    svc = mcp_service.MapService("D:/Projects/daodan")
    result = getattr(svc, op)(**kwargs)
    text = json.dumps(result, indent=1, ensure_ascii=False, default=str)
    status = 0
except Exception as exc:
    text = json.dumps({"error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()}, indent=1)
    status = 1
if out:
    open(out, "w", encoding="utf-8").write(text)
print(text[:6000])
sys.exit(status)
