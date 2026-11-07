"""Binding spike (Task 1): prova headless di MapService.create_run + una chiamata per tool.

Gate del build di benchmarks/scope-resolution. Scrive results/spike-binding.md con le
quattro risposte TO-JUDGE; exit 0 solo se il binding headless funziona.
"""
import json
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "plugins" / "codebase-map" / "skills" / "map-method" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from mcp_service import MapService  # noqa: E402

RUN_ID = "spike-1"
TEMP_BASE = tempfile.gettempdir()


def build_tmp_project(root: Path) -> None:
    (root / "packages" / "tmp_alpha").mkdir(parents=True)
    (root / "packages" / "tmp_alphabeta").mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "spike-demo"\nversion = "0.1.0"\n\n'
        '[tool.uv.workspace]\nmembers = ["packages/*"]\n',
        encoding="utf-8")
    (root / "packages" / "tmp_alpha" / "__init__.py").write_text("", encoding="utf-8")
    (root / "packages" / "tmp_alpha" / "alpha.py").write_text(
        "from tmp_alphabeta.beta import beta_helper\n\n\n"
        "def alpha_entry(payload):\n    return beta_helper(payload)\n",
        encoding="utf-8")
    (root / "packages" / "tmp_alphabeta" / "__init__.py").write_text("", encoding="utf-8")
    (root / "packages" / "tmp_alphabeta" / "beta.py").write_text(
        "def beta_helper(payload):\n    return payload\n", encoding="utf-8")


def main() -> int:
    results_dir = HERE / "results"
    results_dir.mkdir(exist_ok=True)
    report = ["# Spike binding headless (Task 1)", ""]
    tmp = Path(tempfile.mkdtemp(prefix="scope-resolution-spike-", dir=TEMP_BASE))
    ok = True
    try:
        build_tmp_project(tmp)
        service = MapService(project_root=tmp)
        status = service.create_run(target=".", run_id=RUN_ID)
        report += ["## (a) Binding headless: OK", "",
                   "```json", json.dumps(status, indent=2, default=str)[:2000], "```", ""]
        calls = {
            "search": service.search(RUN_ID, "tmp_alpha", limit=10),
            "modules_list": service.modules(RUN_ID),
            "modules_query": service.modules(RUN_ID, query="tmp_alpha"),
            "outline": service.outline(RUN_ID, path="packages/tmp_alpha/alpha.py"),
            "graph": service.graph(RUN_ID, paths=["packages/tmp_alpha/alpha.py"], hops=1),
            "read": service.read(RUN_ID, [{"path": "packages/tmp_alpha/alpha.py"}]),
        }
        report += ["## (b) Moduli dichiarati esposti senza run di analisi", "",
                   "```json", json.dumps(calls["modules_list"], indent=2, default=str)[:3000], "```", "",
                   "## (d) Forma della risposta a query di modulo con nomi simili", "",
                   "```json", json.dumps(calls["modules_query"], indent=2, default=str)[:3000], "```", ""]
        search2 = service.search(RUN_ID, "tmp_alpha", limit=10)
        graph2 = service.graph(RUN_ID, paths=["packages/tmp_alpha/alpha.py"], hops=1)
        stable = (json.dumps(calls["search"], default=str) == json.dumps(search2, default=str)
                  and json.dumps(calls["graph"], default=str) == json.dumps(graph2, default=str))
        report += [f"## (c) Ordinamento search/graph stabile su ripetizione: {'si' if stable else 'no'}", ""]
        for name in ("outline", "graph", "read"):
            report += [f"### Estratto {name}", "",
                       "```json", json.dumps(calls[name], indent=2, default=str)[:1500], "```", ""]
    except Exception:
        ok = False
        report += ["## ESITO: KO", "", "```", traceback.format_exc(), "```"]
    finally:
        (results_dir / "spike-binding.md").write_text("\n".join(report), encoding="utf-8")
        shutil.rmtree(tmp, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
