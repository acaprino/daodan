"""The benchmark's two scripts 137512c11 moved to the new signatures, run as they run (D-233): a real proof on Modal.

    python tests/modal_pytest.py benchmarks/inference-audit/test_scripts_on_modal.py -q

`adapters/ts_compiler.py` on two TypeScript files with the checker from npm; `modal_scip.py`'s `scip_case` on semver
over the inputs an earlier run kept on the volume, with a label of its own and nothing written back to the volume.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ON_MODAL = pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"),
                              reason="a real proof on Modal (tests/modal_pytest.py)")


@ON_MODAL
def test_on_modal_ts_compiler_checks_a_project_through_the_tsconfig_it_generates(tmp_path, monkeypatch):
    """The project's tsconfig.json moves to tsconfig.project.json, which the generated one extends and widens to
    the files; the checker gives the call of a.ts to b.ts's function, by its signature."""
    from adapters import ts_compiler
    tools = tmp_path / "tools"
    subprocess.run(["npm", "install", "--prefix", str(tools), "--no-audit", "--no-fund", "--ignore-scripts",
                    f"@typescript/typescript6@{ts_compiler.VERSION}"], check=True, capture_output=True, timeout=600)
    monkeypatch.setattr(ts_compiler, "TOOLS", tools)
    monkeypatch.setattr(ts_compiler, "NODE", Path(shutil.which("node")).resolve().parent)
    project = tmp_path / "project"
    project.mkdir()
    (project / "tsconfig.json").write_text('{"compilerOptions": {"strict": true}}\n', encoding="utf-8")
    (project / "b.ts").write_text("export function greet(name: string): string {\n  return name;\n}\n",
                                  encoding="utf-8")
    (project / "a.ts").write_text('import { greet } from "./b";\ngreet("x");\n', encoding="utf-8")
    work = tmp_path / "work"
    result = ts_compiler.analyze(project, work)
    here = work / "mirror-strong-js"
    config = json.loads((here / "tsconfig.json").read_text(encoding="utf-8"))
    print("TS", json.dumps({"run": result["run"], "edges": result["edges"], "counts": result["counts"]})[:2000])
    assert config["extends"] == "./tsconfig.project.json" and {"a.ts", "b.ts"} <= set(config["include"])
    assert json.loads((here / "tsconfig.project.json").read_text(encoding="utf-8")) == {
        "compilerOptions": {"strict": True}}
    assert (project / "tsconfig.json").read_text(encoding="utf-8").startswith('{"compilerOptions"')  # untouched
    assert [(edge["site"], edge["callee"], edge["via"]) for edge in result["edges"]] == [("a.ts:2:0", "b.ts:1:7",
                                                                                         "signature")]
    assert (result["counts"]["errors"], result["counts"]["version"]) == (0, "6.0.3")


@ON_MODAL
def test_on_modal_modal_scip_joins_semver_s_kept_inputs(monkeypatch):
    """semver's snapshot, road A's answers and rust-analyzer's indexes, as an earlier run kept them on the volume,
    copied to the container's /results; the join runs over them with no error."""
    import modal
    monkeypatch.setattr(modal, "is_local", lambda: True)  # the checkout's plugin, not the image's mount
    import modal_scip
    volume = modal_scip.volume
    name, base = "semver", f"{modal_scip.TAG}/scip-inputs"
    kept = Path("/results") / base / name
    kept.mkdir(parents=True, exist_ok=True)
    for entry in volume.listdir(f"{base}/{name}"):
        file = Path(entry.path).name
        if entry.type != modal.volume.FileEntryType.FILE or file.startswith("graph-") or file == "source.tar":
            continue
        with (kept / file).open("wb") as handle:
            for chunk in volume.read_file(entry.path):
                handle.write(chunk)
    monkeypatch.setattr(volume, "commit", lambda: None)  # nothing goes back to the volume
    result = modal_scip.scip_case.local(name, modal_scip.CASES[name], "d233")
    join = result["join"]
    assert result["inputs"].startswith("kept") and "error" not in join
    assert [tuple(tool) for tool in join["index_tools"]] == [("rust-analyzer", "0.3.3113-standalone")] * 2
    graph = join["languages"]["rust"]["graph"]
    print("JOIN", json.dumps({"answers": join["answers"], "nodes": graph["nodes"], "edges": graph["edges"]}))
    assert (join["answers"], graph["nodes"], graph["edges"]) == (721, 1073, 3960)
