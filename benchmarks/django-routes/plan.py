"""What Daodan's runner gives the container for a project, as JSON on the standard output, for `modal_probe.py`.

    python benchmarks/django-routes/plan.py [folder]        (Daodan's own Python dependencies, the ones its tests use; default `fixture`)

It runs Daodan's code only: the restore lines of the folders (`container_runner._python`, read from the file names of the copy), the setup command
and the files it unpacks (`container_runner.plan`), the Python of each environment the restore makes (`preparation.python_environments`,
`python_interpreter`) and, when `premap/django_app.py` exists, the commands it gives for the folder (`premap.write` with the module graph and a
runner that answers nothing). Nothing of the project is imported or run: that happens in the container, from these lines. Its working files go
under `DAODAN_PROBE_TMP` when it is set.

`container_runner.TOOLS["django"]` is the entry the wiring adds (`TOOL` below, the same dict as in the report of task 14b); it is taken here
with `setdefault`, so a tree that already has it keeps its own.
"""
import json
import os
import shutil
import sys
import tempfile
import types
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "daodan/core"))

import preparation  # noqa: E402
import premap  # noqa: E402
import snapshot  # noqa: E402
import container_runner  # noqa: E402
from premap import noir  # noqa: E402

try:
    from premap import django_app  # noqa: E402
except ImportError:  # the source is not written yet: the exploratory runs need no command of it
    django_app = None

TOOL = {"files": [(None, None, "django_routes.py")], "setup": [f"cp {preparation.IN}/django_routes.py {preparation.T}/django_routes.py"],
        "registries": True, "restores": "python", "memory": 3}
container_runner.TOOLS.setdefault("django", TOOL)


def plan(folder: Path) -> dict:
    with tempfile.TemporaryDirectory(dir=os.environ.get("DAODAN_PROBE_TMP")) as scratch:
        project = Path(scratch) / "project"
        if (folder / ".git").exists():  # a checkout of a public project (`real_probe.py`): read where it is, names only
            project = folder
        else:
            shutil.copytree(folder, project, ignore=shutil.ignore_patterns("__pycache__", ".venv"))
        manifest = Path(scratch) / "out" / "manifest.sqlite"
        snapshot.read_project(project, manifest)
        taken = []

        def run(commands):
            taken.extend(commands)
            return [{"returncode": 0, "stdout": "", "stderr": "", "root": "/work"} for _ in commands]
        if django_app is not None:
            premap.write(manifest, sources=(premap.module_graph, premap.requirements, django_app), runner=run)
        noir_commands = noir.commands(types.SimpleNamespace(inventory=types.SimpleNamespace(files=["a"])))  # the one command: a scan of the copy
        restored = container_runner._python(project)
        # the tools the runner installs as root before the setup (`container.tool_phase`, uv) go back into the setup, where they were before
        # T3.A.6b, ahead of the restore: the image build runs as root, and the measurement stays the one the results hold
        *_, tools = container_runner.plan("django", taken, [], restored["lines"], restored["needs"])
        first, files, hosts, gaps, _ = container_runner.plan("django", taken, [], [*(tools or {}).get("lines", ()), *restored["lines"]],
                                                         restored["needs"])
        listed = sorted(p.relative_to(project).as_posix() for p in project.rglob("*") if p.is_file() and ".git" not in p.relative_to(project).parts)
        held = preparation.python_environments(listed, lambda rel: (project / rel).is_file())
        interpreters = {env: preparation.python_interpreter(env, manager, "/work") for env, manager in held.items()}
    return {"image": container_runner.IMAGE, "env": container_runner.ENV, "setup": first, "files": files, "hosts": hosts,
            "gaps": gaps + restored["gaps"], "commands": taken, "version": getattr(django_app, "VERSION", None),
            "state": preparation.STATE, "inputs": preparation.IN, "tools": preparation.T, "venvs": preparation.VENVS,
            "interpreters": interpreters, "noir": list(noir.DOWNLOAD), "noir_commands": noir_commands}


if __name__ == "__main__":
    print(json.dumps(plan(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "fixture"), indent=1))
