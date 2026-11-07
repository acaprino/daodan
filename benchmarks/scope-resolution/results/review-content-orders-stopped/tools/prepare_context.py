"""Build CONTEXT.json for review_roster.py and a structural census of the scope. Writes only under OUT."""
import ast
import collections
import hashlib
import json
import sys
from pathlib import Path

work_tree, out = Path(sys.argv[1]), Path(sys.argv[2])
prefix = "benchmarks/scope-resolution/app/packages/orders"
files = sorted(p for p in (work_tree / prefix).iterdir() if p.suffix == ".py")
candidate = (out / "tools/candidate.txt").read_text(encoding="utf-8").strip()

rows = []
for path in files:
    rel = path.relative_to(work_tree).as_posix()
    text = path.read_text(encoding="utf-8")
    rows.append({"path": rel, "status": "available", "text": text,
                 "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})

context = {
    "review_basis": "content",
    "scope_id": "orders-module",
    "candidate": candidate,
    "conclusion_paths": [row["path"] for row in rows],
    "read_scope": ["benchmarks/scope-resolution/app/packages/payments/refunds.py",
                   "benchmarks/scope-resolution/app/packages/payments/gateway.py",
                   "benchmarks/scope-resolution/app/packages/shipping/rates.py",
                   "benchmarks/scope-resolution/app/pyproject.toml",
                   "benchmarks/scope-resolution/test_app_structures.py"],
    "inventory": [{"path": row["path"], "status": "available", "sha256": row["sha256"]} for row in rows],
    "sources": rows,
    "catalog": json.loads((out / "CATALOG.json").read_text(encoding="utf-8")),
}
(out / "CONTEXT.json").write_text(json.dumps(context, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class Normalize(ast.NodeTransformer):
    """Erase the per-function name, docstring and label literal so only logic differs."""

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        node.name = "_"
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(getattr(node.body[0], "value", None), ast.Constant):
            node.body = node.body[1:]
        return node


big = work_tree / prefix / "big_module.py"
tree = ast.parse(big.read_text(encoding="utf-8"))
clusters = collections.defaultdict(list)
others = []
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        label = next((n.value.func.value.value for n in ast.walk(node)
                      if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)
                      and isinstance(n.value.func, ast.Attribute) and n.value.func.attr == "upper"
                      and isinstance(n.value.func.value, ast.Constant)), None)
        shape = ast.dump(Normalize().visit(ast.parse(ast.unparse(node)))).replace(repr(label), "'LABEL'")
        clusters[hashlib.sha256(shape.encode()).hexdigest()[:12]].append(
            {"name": node.name, "line": node.lineno, "end": node.end_lineno, "label": label})
    else:
        others.append({"type": type(node).__name__, "line": node.lineno, "end": node.end_lineno})

census = {
    "file": big.relative_to(work_tree).as_posix(),
    "top_level_functions": sum(len(v) for v in clusters.values()),
    "distinct_normalized_bodies": len(clusters),
    "cluster_sizes": sorted((len(v) for v in clusters.values()), reverse=True),
    "other_top_level": others,
    "small_clusters": {k: v for k, v in clusters.items() if len(v) <= 5},
    "labels": sorted(collections.Counter(i["label"] for v in clusters.values() for i in v).items(), key=str),
}
(out / "tools/big_module-census.json").write_text(json.dumps(census, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"context_files": len(rows), **{k: census[k] for k in
      ("top_level_functions", "distinct_normalized_bodies", "cluster_sizes", "other_top_level")}}))
