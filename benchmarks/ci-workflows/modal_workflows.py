"""The reader of GitHub's workflows on Modal: Renovate's YAML library with `premap/renovate.py`'s rules against
GitHub's own parser (`@actions/workflow-parser`), on the same files. Passo `T3.B.4` di `docs/plans/refactoring.md`.

The container holds what Daodan's Renovate container holds (Node 24.22.3, Renovate 44.239.1 and the `yaml` 2.9.1 it
pins, every package with `--ignore-scripts`) and `@actions/workflow-parser` 0.3.61. The workflows are this folder's
fixtures (`fixtures/valid`, `fixtures/invalid`), the corpus fixture with workflows (`mix-infra-gha`) and five real
repositories, each cloned at the commit of its `source.json`. Nothing of a project runs: both readers only read YAML.

For each workflow: (a) `node <yaml>/bin.mjs --json --single --strict --merge`, `renovate.EACH`'s command, and the
steps as `renovate.py` reads them (`_directory`, `_shell`, `_env`, `_services`); (b) `workflows.mjs`, the schema's
errors and the converted model. Per job: the steps' `run`, `uses`, `working-directory` (the step's, else the
defaults'), `shell`, `env` (its names), `if`; the services (name and image); `container`. Result in
`results/<date>.json`; the decision rule is in the README.

    modal run benchmarks/ci-workflows/modal_workflows.py
"""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = (HERE / "workflows.mjs").is_file() and (HERE.parents[1] / "daodan/core").is_dir()
REPO = HERE.parents[1] if LOCAL else Path("/")
NODE = "v24.22.3"  # `premap/renovate.py`'s Node
RENOVATE = "44.239.1"  # `container_runner.TOOLS["renovate"]`
PARSER = "0.3.61"  # @actions/workflow-parser, MIT, 4 August 2026
REAL = ("real-sveltekit-realworld", "real-svc-otel-demo", "real-bank-of-anthos", "real-app-full-stack-fastapi",
        "real-stack-plausible")
CORPUS = ("mix-infra-gha",)
YAML = f"/opt/node-{NODE}-linux-x64/lib/node_modules/renovate/node_modules/yaml/bin.mjs"

image = (modal.Image.debian_slim(python_version="3.12")
         .apt_install("curl", "ca-certificates", "git", "xz-utils")
         .run_commands(
             f"cd /tmp && curl -sSfLO https://nodejs.org/dist/{NODE}/node-{NODE}-linux-x64.tar.xz"
             f" && curl -sSfL https://nodejs.org/dist/{NODE}/SHASUMS256.txt | grep ' node-{NODE}-linux-x64.tar.xz$'"
             f" | sha256sum -c - && tar -C /opt -xJf node-{NODE}-linux-x64.tar.xz && rm node-{NODE}-linux-x64.tar.xz",
             f"PATH=/opt/node-{NODE}-linux-x64/bin:$PATH npm install -g --ignore-scripts renovate@{RENOVATE}",
             f"mkdir -p /wp && cd /wp && PATH=/opt/node-{NODE}-linux-x64/bin:$PATH npm init -y >/dev/null"
             f" && PATH=/opt/node-{NODE}-linux-x64/bin:$PATH npm install --ignore-scripts @actions/workflow-parser@{PARSER}")
         .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6",
                      "pip-requirements-parser==32.0.1")  # what `premap` imports, as `modal_premap.py`
         .env({"PATH": f"/opt/node-{NODE}-linux-x64/bin:/usr/local/bin:/usr/bin:/bin"}))
if LOCAL:
    image = (image.add_local_dir(REPO / "daodan/core", "/daodan/core", ignore=["**/__pycache__/**"])
             .add_local_dir(REPO / "daodan/data", "/daodan/data")
             .add_local_dir(HERE, "/bench", ignore=["results/**", "**/__pycache__/**"]))
    for name in (*REAL, *CORPUS):
        image = image.add_local_dir(REPO / "benchmarks/project-model/fixtures" / name, f"/cases/{name}")
app = modal.App("daodan-ci-workflows", image=image)


def _clone(name: str) -> Path:
    source = json.loads(Path(f"/cases/{name}/source.json").read_text(encoding="utf-8"))
    project = Path("/work") / name
    project.mkdir(parents=True)
    for argv in (["git", "init", "-q"], ["git", "remote", "add", "origin", source["repo"]],
                 ["git", "fetch", "-q", "--depth", "1", "origin", source["commit"]], ["git", "checkout", "-q", "FETCH_HEAD"]):
        done = subprocess.run(argv, cwd=project, capture_output=True, text=True, timeout=900,
                              env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
        if done.returncode:
            raise RuntimeError(f"{name}: {' '.join(argv[:3])}: {done.stderr.strip()[-300:]}")
    return project


def _workflows(root: Path) -> list[Path]:
    folder = root / ".github/workflows"
    return sorted(path for pattern in ("*.yml", "*.yaml") for path in folder.glob(pattern)
                  if path.is_file() and not path.is_symlink())


def _token(value):
    """A template token of the converted model as plain data: a mapping, a sequence, `{"expr"}`, or a literal."""
    if isinstance(value, dict) and value.get("type") == 2:
        return {str(_token(item["Key"])): _token(item["Value"]) for item in value.get("map", [])}
    if isinstance(value, dict) and value.get("type") == 1:
        return [_token(item) for item in value.get("seq", [])]
    if isinstance(value, dict) and value.get("type") == 3:
        return {"expr": value.get("expr")}
    return value


def _condition(text) -> str | None:
    """A step's `if` as an expression, its `${{ }}` dropped."""
    if text is None:
        return None
    text = str(text).strip()
    return text[3:-2].strip() if text.startswith("${{") and text.endswith("}}") else text


def _image(container):
    container = _token(container)
    return container.get("image") if isinstance(container, dict) and "expr" not in container else container


def from_yaml(rel: str, doc) -> dict:
    """The jobs of a workflow document as `premap/renovate.py` reads them."""
    from premap import renovate
    jobs = {}
    top_dir, top_shell = renovate._directory(doc), renovate._shell(doc)
    services = {}
    for service in renovate._services(rel, doc):
        job = service["declared_in"].split("#jobs.", 1)[1].split(".services.", 1)[0]
        services.setdefault(job, {})[service["name"]] = service["image"]
    for job_id, job in (doc.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        folder, shell = renovate._directory(job) or top_dir, renovate._shell(job) or top_shell
        steps = [{"run": step.get("run"), "uses": step.get("uses"),
                  "working-directory": step.get("working-directory") or folder, "shell": step.get("shell") or shell,
                  "env": sorted(renovate._env(step)), "if": _condition(step.get("if"))}
                 for step in job.get("steps") or [] if isinstance(step, dict)]
        jobs[str(job_id)] = {"steps": steps, "services": services.get(str(job_id), {}),
                             "container": _image(job.get("container"))}
    return jobs


def from_parser(template: dict) -> dict:
    """The jobs of GitHub's converted model, the same fields."""
    jobs = {}
    for job in template.get("jobs") or []:
        steps = []
        for step in job.get("steps") or []:
            run = _token(step.get("run"))
            condition = _token(step.get("if"))
            steps.append({"run": run, "uses": _token(step.get("uses")),
                          "working-directory": _token(step.get("working-directory")), "shell": _token(step.get("shell")),
                          "env": sorted(_token(step.get("env")) or {}),
                          "if": condition.get("expr") if isinstance(condition, dict) else condition})
        declared = _token(job.get("services")) or {}
        jobs[str(job["id"])] = {"steps": steps,
                                "services": {name: _image(service) for name, service in declared.items()}
                                if isinstance(declared, dict) else {"expr": declared},
                                "container": _image(job.get("container"))}
    return jobs


def _same_if(ours, theirs) -> bool:
    """GitHub's model wraps a step's condition in `success() && (...)`, and gives `success()` for none."""
    if ours is None:
        return theirs in (None, "success()")
    return theirs in (ours, f"success() && ({ours})")


FIELDS = ("run", "uses", "working-directory", "shell", "env", "if")


def compare(ours: dict, theirs: dict) -> dict:
    """Per field, the steps on which the two readers agree and differ, with the first examples of a difference."""
    said = {"jobs": len(ours), "jobs_missing": sorted(set(ours) - set(theirs)), "steps": 0,
            "steps_count_differs": [], "fields": {field: {"same": 0, "differs": 0, "examples": []} for field in FIELDS},
            "services_differ": [], "container_differs": []}
    for job_id, job in ours.items():
        other = theirs.get(job_id)
        if other is None:
            continue
        if job["services"] != other["services"]:
            said["services_differ"].append({"job": job_id, "yaml": job["services"], "parser": other["services"]})
        if job["container"] != other["container"]:
            said["container_differs"].append({"job": job_id, "yaml": job["container"], "parser": other["container"]})
        if len(job["steps"]) != len(other["steps"]):
            said["steps_count_differs"].append(job_id)
            continue
        for index, (step, given) in enumerate(zip(job["steps"], other["steps"])):
            said["steps"] += 1
            for field in FIELDS:
                same = _same_if(step["if"], given["if"]) if field == "if" else step[field] == given[field]
                kept = said["fields"][field]
                kept["same" if same else "differs"] += 1
                if not same and len(kept["examples"]) < 3:
                    kept["examples"].append({"step": f"{job_id}.steps.{index}", "yaml": step[field],
                                             "parser": given[field]})
    return said


@app.function(cpu=1.0, memory=2048, timeout=1800)
def measure() -> dict:
    sys.path.insert(0, "/daodan/core")
    roots = {"fixtures/valid": Path("/bench/fixtures/valid"), "fixtures/invalid": Path("/bench/fixtures/invalid")}
    roots.update({name: Path(f"/cases/{name}") for name in CORPUS})
    roots.update({name: _clone(name) for name in REAL})
    commits = {name: json.loads(Path(f"/cases/{name}/source.json").read_text())["commit"] for name in REAL}
    Path("/wp/workflows.mjs").write_text(Path("/bench/workflows.mjs").read_text())
    versions = {"node": subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip(),
                "yaml": json.loads(Path(YAML).with_name("package.json").read_text())["version"],
                "workflow-parser": json.loads(Path("/wp/node_modules/@actions/workflow-parser/package.json")
                                              .read_text())["version"]}
    files, totals = [], {"workflows": 0, "read_by_yaml": 0, "read_by_parser": 0, "schema_errors": 0,
                         "errors_yaml_misses": 0, "steps": 0, "services_differ": 0, "container_differs": 0,
                         "fields_differ": {field: 0 for field in FIELDS}, "jobs_missing": 0, "steps_count_differs": 0}
    for case, root in roots.items():
        paths = _workflows(root)
        if not paths:
            continue
        parsed = subprocess.run(["node", "workflows.mjs", *map(str, paths)], cwd="/wp", capture_output=True, text=True,
                                timeout=600)
        answers = {Path(line["file"]): line for line in map(json.loads, parsed.stdout.splitlines())}
        for path in paths:
            rel = path.relative_to(root).as_posix()
            done = subprocess.run(["node", YAML, "--json", "--single", "--strict", "--merge"], stdin=path.open("rb"),
                                  capture_output=True, timeout=120)
            doc = json.loads(done.stdout) if done.returncode == 0 else None
            answer = answers.get(path, {"failed": parsed.stderr[-400:] or "no answer"})
            row = {"case": case, "file": rel, "yaml_error": None if done.returncode == 0 else done.stderr.decode()[-300:],
                   "parser_errors": answer.get("errors", []), "parser_failed": answer.get("failed")}
            ours = from_yaml(rel, doc) if isinstance(doc, dict) else None
            template = answer.get("template") or {}
            theirs = from_parser(template) if template.get("jobs") else None
            totals["workflows"] += 1
            totals["read_by_yaml"] += ours is not None
            totals["read_by_parser"] += theirs is not None and not row["parser_errors"]
            totals["schema_errors"] += bool(row["parser_errors"])
            totals["errors_yaml_misses"] += bool(row["parser_errors"]) and ours is not None
            if ours is not None and theirs is not None:
                said = compare(ours, theirs)
                row["compare"] = said
                totals["steps"] += said["steps"]
                totals["services_differ"] += len(said["services_differ"])
                totals["container_differs"] += len(said["container_differs"])
                totals["jobs_missing"] += len(said["jobs_missing"])
                totals["steps_count_differs"] += len(said["steps_count_differs"])
                for field in FIELDS:
                    totals["fields_differ"][field] += said["fields"][field]["differs"]
            files.append(row)
    return {"versions": versions, "commits": commits, "totals": totals, "files": files}


@app.local_entrypoint()
def main(out: str = ""):
    result = measure.remote()
    target = Path(out) if out else HERE / "results" / f"{datetime.date.today().isoformat()}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"], indent=1))
    print(f"written to {target}")
