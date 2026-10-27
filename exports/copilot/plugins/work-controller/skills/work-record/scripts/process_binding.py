"""Read-only admission of process evidence into the existing work record."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import re
import sys


SCHEMA = "daodan/process-binding/v1"
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]{0,95}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")


def _store_class():
    package = Path(__file__).with_name("work_controller")
    loaded = sys.modules.get("work_controller")
    if loaded is not None:
        if Path(loaded.__file__).resolve() != (package / "__init__.py").resolve():
            raise ValueError("A different work_controller package is already loaded")
    else:
        spec = importlib.util.spec_from_file_location(
            "work_controller", package / "__init__.py",
            submodule_search_locations=[str(package)],
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    from work_controller.store import Store

    return Store


def _digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate(record, project, root, no_links, report_path):
    """Reuse engine readers; never grant execution or create a store during validation."""
    binding = record["process"]
    if not isinstance(binding, dict) or set(binding) != {
        "schema", "run_id", "definition_digest", "deliveries",
    }:
        raise ValueError("Process binding requires schema, run_id, definition_digest and deliveries")
    if binding["schema"] != SCHEMA or not IDENTIFIER.fullmatch(str(binding["run_id"])):
        raise ValueError("Unknown process binding schema or invalid run ID")
    if not isinstance(binding["definition_digest"], str) or not DIGEST.fullmatch(binding["definition_digest"]):
        raise ValueError("Process binding requires the admitted definition digest")
    mappings = binding["deliveries"]
    if not isinstance(mappings, dict) or not set(mappings).issubset(record["deliveries"]):
        raise ValueError("Process binding may map only declared work deliveries")
    used = set()
    for entry in mappings.values():
        if (not isinstance(entry, dict) or set(entry) != {"job", "artifact"}
                or any(not isinstance(value, str) or not value for value in entry.values())):
            raise ValueError("Each process delivery requires a job and artifact name")
        identity = (entry["job"], entry["artifact"])
        if identity in used:
            raise ValueError("Independent work deliveries require distinct process artifacts")
        used.add(identity)
    if project is None or root is None:
        raise ValueError("Process evidence requires the bound project and record home")
    home = root / "processes"
    no_links(home, root)
    for name in ("process.db", "process.db-wal", "process.db-shm", "brain.db", "brain.db-wal", "brain.db-shm"):
        no_links(home / name, root)
    store = _store_class().open_readonly(home)
    run = store.run(binding["run_id"])
    if Path(run["workspace"]).resolve() != project.resolve():
        raise ValueError("Process workspace differs from the work record")
    if run["definition_digest"] != binding["definition_digest"]:
        raise ValueError("Process definition differs from the bound immutable revision")
    agent_jobs = {job["id"] for job in store.jobs(binding["run_id"])
                  if store.job(binding["run_id"], job["id"])["payload"]["type"] == "agent"}
    if not agent_jobs.issubset({entry["job"] for entry in mappings.values()}):
        raise ValueError("Every process agent job requires a mapped work delivery")
    if "commit" in run["grants"]:
        raise ValueError("Bound processes leave Git commits to the work record's reviewed domain workflow")
    for identity, entry in mappings.items():
        job = store.job(binding["run_id"], entry["job"])
        if entry["artifact"] not in {item["name"] for item in job["payload"]["produces"]}:
            raise ValueError(f"Process job does not declare the delivery artifact: {identity}")
        delivery = record["deliveries"][identity]
        if delivery["status"] != "delivered":
            continue
        artifact = store.latest_artifact(binding["run_id"], entry["artifact"])
        if (job["status"] != "succeeded" or artifact is None
                or artifact["status"] != "admitted" or artifact["producer_job"] != entry["job"]):
            raise ValueError(f"Process delivery is not admitted from a succeeded job: {identity}")
        attempt = store.attempt(artifact["producer_attempt"])
        if (attempt["status"] != "delivered" or attempt["job_id"] != entry["job"]
                or attempt["run_id"] != binding["run_id"]):
            raise ValueError(f"Process artifact has no delivered producer attempt: {identity}")
        digest = artifact["digest"]
        if not isinstance(digest, str) or not DIGEST.fullmatch(digest):
            raise ValueError("Process artifact has an invalid digest")
        output = root / "runs" / record["run_id"] / report_path(delivery["output"])
        content = home / "artifacts" / "objects" / digest[:2] / (digest + ".blob")
        for path in (output, content):
            no_links(path, root)
            if not path.is_file() or _digest(path) != digest:
                raise ValueError(f"Work report or stored process artifact bytes differ: {identity}")
    if record["status"] == "complete" and (
        run["status"] != "complete" or run["outcome"] != "VERIFIED_SUCCESS"
    ):
        raise ValueError("Work completion requires the bound process to finish successfully")
