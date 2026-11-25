"""Runs INSIDE the VM Sandbox of `modal_engine.py`, where a real Docker daemon answers: the exploration through Daodan's
own `container.run_in_container` (not the Modal substitute), as `container.find_engine` finds the engine on Linux."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path[:0] = ["/daodan/map/core"]
os.environ["PATH"] = "/opt/docker:" + os.environ["PATH"]
os.environ.pop("DAODAN_CONTAINER", None)

import container  # noqa: E402
import premap  # noqa: E402
import snapshot  # noqa: E402
from dynamic import app  # noqa: E402

started = time.monotonic()
project, manifest, out = Path("/work/project"), Path("/runs/m/manifest.sqlite"), Path("/runs/out")
for command in (["git", "init", "-q"], ["git", "add", "-A"],
                ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "fixture"]):
    subprocess.run(command, cwd=project, check=True)
engine = container.find_engine()
print("ENGINE", engine.name, engine.argv, flush=True)
snapshot.read_project(project, manifest)
record = premap.write(manifest, sources=[item for item in premap.SOURCES if not hasattr(item, "commands")])
planned = app.plan(record, explore=True)
print("PLAN", json.dumps({"apps": [one["declared_in"] for one in planned["apps"]], "gaps": planned["gaps"]}), flush=True)
seen = app.observe(project, planned, out)  # engine=None: `container.find_engine()`, the real one
explored = {}
for path in sorted((out / "out").glob("explore-*.json")):
    explored[path.name] = json.loads(path.read_text(encoding="utf-8"))
controls = [{"name": c["name"], "state": c.get("state"), "calls": [[x["source"], x["line"], x["name"]] for x in c.get("calls", [])]}
            for data in explored.values() for page in data["pages"] for c in page["controls"]]
print("RESULT", json.dumps({"engine": engine.name, "state": seen["state"], "apps": seen["apps"], "gaps": seen["gaps"],
                            "cause": seen.get("cause"), "remedy": seen.get("remedy"),
                            "totals": [data["totals"] for data in explored.values()], "controls": controls,
                            "logs": {name: (out / name).read_text(encoding="utf-8", errors="replace")[-1500:]
                                     for name in ("prepare.log", "execute.log") if (out / name).is_file()},
                            "seconds": round(time.monotonic() - started, 1)}, default=str), flush=True)
