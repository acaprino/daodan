"""Runs INSIDE the VM Sandbox of `modal_engine.py`, where a real Docker daemon answers: the exploration through Daodan's
own `container.run_in_container` (not the Modal substitute), as `container.find_engine` finds the engine on Linux. The
pre-map is its readers' and Renovate's, run in the container as `find_modules` runs it (`container_runner.runner`): the
toolchains the exploration's preparation installs (Node, Bun) are Renovate's facts. A run whose preparation the proxy
refused a host is the app's question (`egress`): the driver answers "once" for the hosts asked, as the person does in
the app, and runs again, at most `ROUNDS` times; `rounds` keeps each run's gaps with the hosts it asked. What the
project's CI gives the tests of the app's folder (the plan's `beside`: services, variables, steps) is printed with the
pre-map's facts it comes from, the variables by name only, and `said` keeps the rows of the container record that say
how each service and step of the last run went."""
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
import container_runner  # noqa: E402
import egress  # noqa: E402
import premap  # noqa: E402
from premap import renovate  # noqa: E402
import snapshot  # noqa: E402
from dynamic import app  # noqa: E402

started = time.monotonic()
ROUNDS = 3  # the answers a person gives at most before the run stands as it is
project, manifest, out = Path("/work/project"), Path("/runs/m/manifest.sqlite"), Path("/runs/out")
for command in (["git", "init", "-q"], ["git", "add", "-A"],
                ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "fixture"]):
    subprocess.run(command, cwd=project, check=True)
engine = container.find_engine()
print("ENGINE", engine.name, engine.argv, flush=True)
snapshot.read_project(project, manifest)
record = premap.write(manifest, sources=[item for item in premap.SOURCES if not hasattr(item, "commands") or item is renovate],
                      runner=container_runner.runner(manifest, engine=engine))
planned = app.plan(record, explore=True)
beside = planned["beside"]
told = {"apps": [{key: one.get(key) for key in ("root", "runner", "argv", "surface", "declared_in")} for one in planned["apps"]],
        "toolchains": planned["toolchains"], "gaps": planned["gaps"],
        "beside": {"services": [[item["name"], item["image"]] for item in beside["services"]],
                   "env": sorted(beside["env"]), "steps": [[item["declared_in"], item["run"]] for item in beside["steps"]]},
        "premap": {"services": [item["declared_in"] for item in record.get("services", [])],
                   "tests": [[item.get("root"), item.get("runner"), item.get("declared_in")] for item in record.get("tests", [])],
                   "ci_steps": [[item["declared_in"], item.get("tests"), item.get("cause")] for item in record.get("ci_steps", [])]},
        "premap_gaps": [gap for gap in record.get("gaps", []) if str(gap.get("source") or "").startswith("renovate")]}
print("PLAN", json.dumps(told), flush=True)
runs = out / container.RECORD_NAME


def observed() -> tuple[dict, list[dict]]:
    """One run of the exploration, and the services' and the steps' rows its container record gained (`said`)."""
    before = len(runs.read_text(encoding="utf-8").splitlines()) if runs.is_file() else 0
    result = app.observe(project, planned, out)  # engine=None: `container.find_engine()`, the real one
    rows = [json.loads(line) for line in runs.read_text(encoding="utf-8").splitlines()[before:]] if runs.is_file() else []
    return result, [{key: row.get(key) for key in ("phase", "name", "image", "declared_in", "outcome", "exit_code", "cause")}
                    for row in rows if row.get("phase") in ("service", "ci_step")]


seen, said = observed()
rounds = []  # each run that asked for hosts nobody approved: the app's question, answered "once" as the user does there
while (asked := egress.pending(egress.name(project))) and len(rounds) < ROUNDS:
    rounds.append({"asked": asked, "apps": seen["apps"], "gaps": seen["gaps"], "said": said})
    print("ASKED", json.dumps([row["host"] for row in asked]), flush=True)
    egress.reply(egress.name(project), [row["host"] for row in asked], "once")
    seen, said = observed()  # analyze again, as the gap's remedy says
explored = {}
for path in sorted((out / "out").glob("explore-*.json")):
    explored[path.name] = json.loads(path.read_text(encoding="utf-8"))
controls = [{"name": c["name"], "state": c.get("state"), "calls": [[x["source"], x["line"], x["name"]] for x in c.get("calls", [])]}
            for data in explored.values() for page in data["pages"] for c in page["controls"]]
print("RESULT", json.dumps({"engine": engine.name, "plan": told, "state": seen["state"], "apps": seen["apps"], "gaps": seen["gaps"],
                            "cause": seen.get("cause"), "remedy": seen.get("remedy"), "said": said,
                            # the hosts the proxy refused and the user answered "once", round by round, and those
                            # still unanswered after the last round (`egress`)
                            "rounds": rounds, "asked": egress.pending(egress.name(project)),
                            "totals": [data["totals"] for data in explored.values()], "controls": controls,
                            "logs": {name: (out / name).read_text(encoding="utf-8", errors="replace")[-1500:]
                                     for name in ("prepare.log", "execute.log") if (out / name).is_file()},
                            "seconds": round(time.monotonic() - started, 1)}, default=str), flush=True)
