"""What Daodan's runner gives the container for a project, as JSON on the standard output, for `modal_probe.py`.

    python benchmarks/flask-routes/plan.py [folder]        (Daodan's own Python dependencies, the ones its tests use; default `fixture`)

It runs Daodan's code only: the pre-map's own `requirements` source and Flask's (`premap.write` with the module graph and a runner that answers nothing,
to take the commands `flask_app.commands` gives for the folder), the restore lines of the folders (`container_runner._python`, read
from the file names of the copy) and the setup command and the files it unpacks (`container_runner.plan`). Nothing of the project
is imported or run: that happens in the container, from these lines. Its working files go under `DAODAN_PROBE_TMP` when it is set.
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "daodan/core"))

import entries  # noqa: E402
import preparation  # noqa: E402
import premap  # noqa: E402
import snapshot  # noqa: E402
from premap import container_runner, flask_app  # noqa: E402


def plan(folder: Path) -> dict:
    entries.QUERIES.setdefault("flask", {"route": {"kind": "rotta"}})  # the table `entry-queries.json` no longer has: the source is not wired
    with tempfile.TemporaryDirectory(dir=os.environ.get("DAODAN_PROBE_TMP")) as scratch:
        project = Path(scratch) / "project"
        shutil.copytree(folder, project, ignore=shutil.ignore_patterns("__pycache__", ".venv"))
        manifest = Path(scratch) / "out" / "manifest.sqlite"
        snapshot.write_snapshot(project, manifest)
        taken = []

        def run(commands):
            taken.extend(commands)
            return [{"returncode": 0, "stdout": "", "stderr": "", "root": "/work"} for _ in commands]
        premap.write(manifest, sources=(premap.module_graph, premap.requirements, flask_app), runner=run)
        restored = container_runner._python(project)
        first, files, hosts, gaps = container_runner.plan("flask", taken, [], restored["lines"], restored["needs"])
    return {"image": container_runner.IMAGE, "env": container_runner.ENV, "setup": first, "files": files, "hosts": hosts,
            "gaps": gaps + restored["gaps"], "commands": taken, "version": flask_app.VERSION,
            "state": preparation.STATE, "inputs": preparation.IN, "tools": preparation.T, "venvs": preparation.VENVS}


if __name__ == "__main__":
    print(json.dumps(plan(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "fixture"), indent=1))
