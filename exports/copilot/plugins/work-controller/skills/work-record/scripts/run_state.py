"""Versioned, snapshot-bound operational work records. Standard library only."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import copy
import errno
import platform
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from itertools import combinations
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import tomllib
import uuid

SCHEMA = "daodan/work/v1"
QUESTION_PREFIX = "question:"
RUN_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,95}$")
OPERATION = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
CONTRACT = Path(__file__).resolve().parents[3] / "contracts/work.toml"
LOCK_WAIT = 30
IMMUTABLE = frozenset({"schema", "revision", "run_id", "project", "scope", "authorizations",
                       "operation", "objective", "output_root", "created_at", "candidate"})


class ProtocolError(ValueError):
    pass


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProtocolError(f"Cannot read JSON object: {path}") from error
    if not isinstance(data, dict):
        raise ProtocolError("Payload must be a JSON object")
    return data


def contract():
    with CONTRACT.open("rb") as handle:
        return tomllib.load(handle)


def no_links(path, boundary):
    """Refuse symlinks and Windows junctions on every owned path component."""
    current = Path(path).absolute()
    boundary = Path(boundary).absolute()
    if not current.is_relative_to(boundary):
        raise ProtocolError("Path escapes its declared root")
    for item in (current, *current.parents):
        try:
            metadata = item.lstat()
        except FileNotFoundError:
            metadata = None
        if metadata is not None and (stat.S_ISLNK(metadata.st_mode)
                                     or getattr(metadata, "st_file_attributes", 0) & 0x400):
            raise ProtocolError(f"Link is not an owned writable path: {item.name}")
        if item == boundary:
            break


def checkout_home(project):
    """The main checkout of the repository that holds the project.

    Run records and the agenda live there, so a linked worktree's records survive
    its removal and every worktree and session sees one agenda. Outside Git, or
    when the common directory is not a plain `.git`, the project is its own home.
    """
    common = git_value(project, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if not common:
        return project
    ignored = subprocess.run(["git", "-C", str(project), "check-ignore", "-q", "."],
                             capture_output=True, check=False)
    if ignored.returncode == 0:
        # The enclosing repository ignores this directory, so the project is not
        # that repository's: a project kept under a tool's run directory keeps
        # its own records, as the Codebase Map keeps its own root.
        return project
    common_path = Path(common).resolve()
    if common_path.name != ".git" or not common_path.parent.is_dir():
        return project
    return common_path.parent


STATE_DIRECTORIES = (".codebase-map", ".daodan")


def first_use_probe(project):
    """Whether a project has any Daodan state yet (ADR-0005). Writes nothing."""
    project = Path(project).resolve()
    if not project.is_dir():
        raise ProtocolError("Project root must be a directory")
    home = checkout_home(project)
    found = sorted(name for name in STATE_DIRECTORIES if (home / name).is_dir() or (project / name).is_dir())
    records = any((base / "docs/adr/README.md").is_file() for base in (home, project))
    return {"first_use": not found, "records": records}


def roots(project):
    """The project and its one record home, `.daodan/` of the main checkout."""
    project = Path(project).resolve()
    if not project.is_dir():
        raise ProtocolError("Project root must be a directory")
    home = checkout_home(project)
    raw = home / ".daodan"
    no_links(raw, home)
    root = raw.resolve()
    if root.exists() and not (root / ".daodan-root").is_file() and any(root.iterdir()):
        raise ProtocolError(".daodan must be dedicated and carry .daodan-root")
    no_links(root / ".daodan-root", home)
    return project, root


def run_paths(project, root, run_id):
    if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
        raise ProtocolError("Invalid exact run ID")
    directory = root / "runs" / run_id
    no_links(directory, root)
    return directory, directory / "work.json"


def git_value(project, *args):
    result = subprocess.run(["git", "-C", str(project), *args], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def head_matches_inputs(project, head, paths, entries, excluded_path, equivalent=None):
    """Compare actual scoped bytes with HEAD blobs, independently of index flags."""
    tree = git_value(project, "ls-tree", "-r", "-z", "--full-name", head, "--", *paths)
    prefix = git_value(project, "rev-parse", "--show-prefix")
    if tree is None or prefix is None:
        return False
    blobs = {}
    for row in tree.split("\0"):
        if not row:
            continue
        metadata, separator, name = row.partition("\t")
        if not separator or not name.startswith(prefix):
            return False
        name = name[len(prefix):]
        if excluded_path(project / name):
            continue
        fields = metadata.split()
        if len(fields) != 3 or fields[1] != "blob" or fields[0] not in {"100644", "100755"}:
            return False
        blobs[name] = (fields[2], fields[0])
    inputs = {name: value for name, value in entries.items() if value is not None}
    if set(blobs) != set(inputs):
        return False
    process = subprocess.Popen(["git", "-C", str(project), "cat-file", "--batch"],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        for name, (blob, mode) in blobs.items():
            if "executable" in inputs[name] and inputs[name]["executable"] != (mode == "100755"):
                return False
            process.stdin.write((blob + "\n").encode("ascii"))
            process.stdin.flush()
            header = process.stdout.readline().split()
            if len(header) != 3 or header[1] != b"blob":
                return False
            remaining = size = int(header[2])
            digest = hashlib.sha256()
            while remaining:
                chunk = process.stdout.read(min(64 * 1024, remaining))
                if not chunk:
                    return False
                digest.update(chunk)
                remaining -= len(chunk)
            if process.stdout.read(1) != b"\n":
                return False
            blob_digest = digest.hexdigest()
            if inputs[name]["sha256"] != blob_digest or inputs[name]["bytes"] != size:
                if equivalent is None or not equivalent(name, inputs[name], blob, blob_digest, size):
                    return False
        return True
    finally:
        process.stdin.close()
        process.stdout.close()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def project_binding(project, scope, output_root):
    paths = scope.get("paths")
    if not isinstance(paths, list) or not paths or any(not isinstance(p, str) for p in paths):
        raise ProtocolError("scope.paths must be a nonempty array of project-relative paths")
    excluded = scope.get("excluded", [])
    if not isinstance(excluded, list) or any(not isinstance(p, str) for p in excluded):
        raise ProtocolError("scope.excluded must be an array of paths")
    excluded_paths = []
    for exclusion in excluded:
        item = Path(exclusion)
        if item.is_absolute() or ".." in item.parts:
            raise ProtocolError("Scope exclusions must stay inside the project")
        excluded_paths.append(project / item)
    entries = {}

    def excluded_path(path):
        return (path == output_root or path.is_relative_to(output_root)
                or any(path == p or path.is_relative_to(p) for p in excluded_paths)
                or ".git" in path.relative_to(project).parts)

    def include_file(path):
        if excluded_path(path):
            return
        no_links(path, project)
        relative = path.relative_to(project).as_posix()
        if not path.exists():
            entries[relative] = None
        elif path.is_file():
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(64 * 1024), b""):
                    digest.update(chunk)
            metadata = path.stat()
            entries[relative] = {"sha256": digest.hexdigest(), "bytes": metadata.st_size, "kind": "file"}
            if os.name != "nt":
                entries[relative]["executable"] = bool(metadata.st_mode & 0o111)
        else:
            raise ProtocolError(f"Snapshot input is not a regular file: {relative}")

    for value in paths:
        relative = Path(value)
        if relative.is_absolute() or ".." in relative.parts:
            raise ProtocolError("Scope path must stay inside the project")
        path = project / relative
        no_links(path, project)
        if excluded_path(path):
            continue
        if path.is_dir():
            for directory, names, files in os.walk(path):
                current = Path(directory)
                for name in list(names):
                    child = current / name
                    if excluded_path(child):
                        names.remove(name)
                    else:
                        no_links(child, project)
                for name in files:
                    include_file(current / name)
        else:
            include_file(path)
    canonical = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
    worktree = git_value(project, "rev-parse", "--show-toplevel")
    git_dir = git_value(project, "rev-parse", "--path-format=absolute", "--git-common-dir")
    head = git_value(project, "rev-parse", "HEAD")
    committed = False
    if head:
        committed = head_matches_inputs(project, head, paths, entries, excluded_path)
    return {"root": str(project), "worktree": str(Path(worktree).resolve()) if worktree else str(project),
            "git_dir": str(Path(git_dir).resolve()) if git_dir else None,
            "head": head, "head_matches_snapshot": committed,
            "snapshot": {"digest": hashlib.sha256(canonical).hexdigest(), "files": entries}}



def relative_file(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ProtocolError(f"{label} must be a nonempty project-relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ProtocolError(f"{label} must stay inside the project: {value}")
    return path.as_posix()


def validate_workspace(section, rules):
    missing = sorted(set(rules["required"]) - set(section))
    if missing:
        raise ProtocolError("Workspace section is missing: " + ", ".join(missing))
    if section["mode"] not in rules["modes"]:
        raise ProtocolError(f"Unknown workspace mode: {section['mode']}")
    for key in ("branch", "base_sha"):
        if not isinstance(section[key], str) or not section[key].strip():
            raise ProtocolError(f"Workspace {key} must be a nonempty string")
    if section["mode"] == "WORKTREE" and not isinstance(section.get("worktree_path"), str):
        raise ProtocolError("A WORKTREE workspace records its worktree_path")
    for binding in section.get("environment_bindings", []):
        if not isinstance(binding, dict) or set(rules["binding_required"]) - set(binding):
            raise ProtocolError("Each environment binding names path, kind and secret")
        if not isinstance(binding["secret"], bool):
            raise ProtocolError("Environment binding secret must be a boolean")
        if binding["secret"] and "value" in binding:
            raise ProtocolError("A secret environment binding never records its value")


def validate_preflight(section, rules):
    baseline = section.get("baseline")
    if baseline not in rules["baseline"]:
        raise ProtocolError(f"Unknown preflight baseline: {baseline}")
    if baseline == "KNOWN_RED" and not isinstance(section.get("failing_fingerprint"), str):
        raise ProtocolError("A KNOWN_RED baseline records the fingerprint of its accepted failures")
    if section.get("migrations", "NOT_APPLICABLE") not in rules["migrations"]:
        raise ProtocolError(f"Unknown migration state: {section.get('migrations')}")


def validate_adr(section, rules):
    pattern = re.compile(rules["id_pattern"])
    active = section.get("active", [])
    if not isinstance(active, list) or any(not isinstance(i, str) or not pattern.fullmatch(i) for i in active):
        raise ProtocolError("adr.active must list ADR identifiers")
    proposed = section.get("proposed")
    if proposed is not None and (not isinstance(proposed, str) or not pattern.fullmatch(proposed)):
        raise ProtocolError("adr.proposed must be an ADR identifier or null")


def validate_task(task, rules):
    if not isinstance(task, dict):
        raise ProtocolError("A wave task must be an object")
    missing = sorted(set(rules["task_required"]) - set(task))
    if missing:
        raise ProtocolError(f"Task is missing: {', '.join(missing)}")
    if not isinstance(task["id"], str) or not task["id"].strip():
        raise ProtocolError("Task id must be a nonempty string")
    if task["status"] not in rules["task_states"]:
        raise ProtocolError(f"Unknown task status: {task['status']}")
    writes = task["write_set"]
    if not isinstance(writes, list) or not writes:
        raise ProtocolError(f"Task {task['id']} needs a nonempty write_set")
    paths = {relative_file(item, f"Task {task['id']} write_set entry") for item in writes}
    if len(paths) != len(writes):
        raise ProtocolError(f"Task {task['id']} repeats a write_set entry")
    limit = rules["max_write_files"]
    exception = task.get("granularity_exception")
    if exception is not None:
        if not isinstance(exception, dict) or not isinstance(exception.get("reason"), str) or not exception["reason"].strip():
            raise ProtocolError(f"Task {task['id']} granularity_exception needs a reason")
        limit = rules["max_write_files_with_exception"]
    if len(paths) > limit:
        raise ProtocolError(f"Task {task['id']} edits {len(paths)} files; the budget is {limit}")
    for key, field in (("oracle", "command"), ("verification", "command")):
        block = task[key]
        if not isinstance(block, dict) or not isinstance(block.get(field), str) or not block[field].strip():
            raise ProtocolError(f"Task {task['id']} {key} needs a command")
    if not isinstance(task["oracle"].get("expected_failure"), str) or not task["oracle"]["expected_failure"].strip():
        raise ProtocolError(f"Task {task['id']} oracle names the failure it must produce before the change")
    for key in ("resource_locks", "produces", "consumes"):
        value = task.get(key, [])
        if not isinstance(value, list) or any(not isinstance(i, str) or not i for i in value):
            raise ProtocolError(f"Task {task['id']} {key} must list identifiers")
    return paths


PLAN_TASK_FIELDS = ("id", "write_set", "oracle", "verification", "resource_locks", "produces", "consumes")


def plan_fingerprint(wave):
    definition = {"id": wave["id"], "parallel": wave.get("parallel", False),
                  "tasks": [{key: task.get(key) for key in PLAN_TASK_FIELDS if key in task}
                            for task in wave["tasks"]]}
    return hashlib.sha256(json.dumps(definition, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def validate_candidate_receipt(receipt, label):
    if not isinstance(receipt, dict):
        raise ProtocolError(f"{label} must be an object")
    digest = receipt.get("digest")
    head = receipt.get("head")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ProtocolError(f"{label}.digest must be a SHA256 digest")
    if head is not None and (not isinstance(head, str) or not head.strip()):
        raise ProtocolError(f"{label}.head must be null or a revision")


def validate_pass_review(review, candidate, receipt, review_rules, deliveries,
                         expected_shape="light", expected_stage=None, expected_kind="changeset"):
    if (not isinstance(receipt, dict) or receipt.get("verdict") != "PASS"
            or receipt.get("snapshot") != candidate["digest"]
            or receipt.get("head") != candidate["head"]
            or not isinstance(receipt.get("id"), str) or not receipt["id"]):
        raise ProtocolError("A PASS review receipt must name its exact candidate")
    if (review is None or review.get("shape") != expected_shape or review.get("kind") != expected_kind
            or (expected_stage is not None and review.get("stage") != expected_stage)
            or review.get("grounding", {}).get("candidate") != candidate):
        raise ProtocolError("The pre-commit review must be a light changeset review bound to its candidate")
    if not all(field in review for field in ("required_specialists", "jobs")):
        raise ProtocolError("A PASS review needs a composition plan: required_specialists and jobs")
    bound = {key: delivery for key, delivery in deliveries.items()
             if isinstance(delivery, dict) and delivery.get("review") == receipt["id"]}
    validate_reviews([review], review_rules, bound, complete=True)


def validate_task_commit(task, reviews, review_rules, deliveries):
    identity = task["id"]
    candidate = task.get("candidate")
    validate_candidate_receipt(candidate, f"Task {identity} candidate")
    digest, head = candidate["digest"], candidate["head"]
    verification = task.get("verification_receipt")
    if (not isinstance(verification, dict) or verification.get("status") != "passed"
            or verification.get("snapshot") != digest or verification.get("head") != head
            or verification.get("command") != task["verification"]["command"]):
        raise ProtocolError(f"Task {identity} needs passing verification on its exact pre-commit candidate")
    receipt = task.get("pre_commit_review")
    review = reviews.get(receipt.get("id")) if isinstance(receipt, dict) else None
    try:
        validate_pass_review(review, candidate, receipt, review_rules, deliveries)
    except ProtocolError as error:
        raise ProtocolError(f"Task {identity} pre-commit review is not delivered and passing: {error}") from error
    commit_sha = task.get("commit_sha")
    if not isinstance(commit_sha, str) or not commit_sha.strip():
        raise ProtocolError(f"Task {identity} committed status requires commit_sha")


def validate_waves(section, rules, workspace, reviews, review_rules, deliveries):
    if not isinstance(section, list):
        raise ProtocolError("waves must be an array")
    seen_waves, seen_tasks = set(), set()
    review_by_id = {review.get("id"): review for review in reviews if isinstance(review, dict)}
    for wave in section:
        if not isinstance(wave, dict) or not isinstance(wave.get("id"), str) or not wave["id"]:
            raise ProtocolError("Each wave needs an id")
        if wave["id"] in seen_waves:
            raise ProtocolError(f"Wave id repeated: {wave['id']}")
        seen_waves.add(wave["id"])
        if wave.get("status") not in rules["states"]:
            raise ProtocolError(f"Unknown wave status: {wave.get('status')}")
        tasks = wave.get("tasks")
        if not isinstance(tasks, list) or not tasks:
            raise ProtocolError(f"Wave {wave['id']} needs at least one task")
        parallel = wave.get("parallel", False)
        if not isinstance(parallel, bool):
            raise ProtocolError(f"Wave {wave['id']} parallel must be a boolean")
        if parallel and len(tasks) > 1 and (workspace is None or workspace.get("mode") != "WORKTREE"):
            raise ProtocolError(f"Wave {wave['id']} runs tasks in parallel, which needs a WORKTREE workspace")
        details = []
        for task in tasks:
            if task.get("id") in seen_tasks:
                raise ProtocolError(f"Task id repeated: {task.get('id')}")
            seen_tasks.add(task.get("id"))
            details.append((task, validate_task(task, rules)))
            if task["status"] == "committed":
                validate_task_commit(task, review_by_id, review_rules, deliveries)
        if any(task.get("status") in {"running", "green", "committed"} for task in tasks):
            plan_candidate = wave.get("plan_candidate")
            validate_candidate_receipt(plan_candidate, f"Wave {wave['id']} plan candidate")
            receipt = wave.get("plan_review")
            fingerprint = plan_fingerprint(wave)
            if (not isinstance(receipt, dict) or receipt.get("plan_sha256") != fingerprint):
                raise ProtocolError(f"Wave {wave['id']} plan changed after its adversarial review")
            review = review_by_id.get(receipt.get("id")) if isinstance(receipt, dict) else None
            if review is not None and review.get("grounding", {}).get("plan_sha256") != fingerprint:
                raise ProtocolError(f"Wave {wave['id']} review covered a different plan digest")
            try:
                validate_pass_review(review, plan_candidate, receipt, review_rules, deliveries,
                                     expected_stage="plan", expected_kind="plan")
            except ProtocolError as error:
                raise ProtocolError(f"Wave {wave['id']} cannot execute without a delivered adversarial PASS plan review: {error}") from error
        for (first, first_paths), (second, second_paths) in combinations(details, 2):
            shared = first_paths & second_paths
            if shared:
                raise ProtocolError(f"Tasks {first['id']} and {second['id']} share write_set files in wave {wave['id']}: {', '.join(sorted(shared))}")
            locks = set(first.get("resource_locks", [])) & set(second.get("resource_locks", []))
            if locks:
                raise ProtocolError(f"Tasks {first['id']} and {second['id']} share resource locks in wave {wave['id']}: {', '.join(sorted(locks))}")
            for producer, consumer in ((first, second), (second, first)):
                crossing = set(producer.get("produces", [])) & set(consumer.get("consumes", []))
                if crossing:
                    raise ProtocolError(f"Task {consumer['id']} consumes what {producer['id']} produces inside wave {wave['id']}: {', '.join(sorted(crossing))}")
        if wave["status"] == "sealed" and any(task["status"] != rules["sealed_requires_task_state"] for task in tasks):
            raise ProtocolError(f"Wave {wave['id']} cannot be sealed while a task is not committed")
        if wave["status"] == "sealed":
            candidate = wave.get("candidate")
            validate_candidate_receipt(candidate, f"Wave {wave['id']} candidate")
            receipt = wave.get("wave_review")
            review = review_by_id.get(receipt.get("id")) if isinstance(receipt, dict) else None
            try:
                validate_pass_review(review, candidate, receipt, review_rules, deliveries)
            except ProtocolError as error:
                raise ProtocolError(f"Wave {wave['id']} cannot seal without its delivered PASS wave review: {error}") from error


def validate_delivery_completion(record, review_rules):
    if record.get("status") != "complete" or not record.get("waves"):
        return
    if any(wave.get("status") != "sealed" for wave in record["waves"]):
        raise ProtocolError("A delivery run cannot complete with an unsealed wave")
    integration = record.get("integration")
    if (not isinstance(integration, dict) or not isinstance(integration.get("merged_sha"), str)
            or not integration["merged_sha"].strip() or integration.get("realigned") is not True):
        raise ProtocolError("A delivery run requires merged_sha and completed realignment before completion")
    receipt = integration.get("candidate_review")
    reviews = {review.get("id"): review for review in record.get("reviews", [])}
    review = reviews.get(receipt.get("id")) if isinstance(receipt, dict) else None
    candidate = ({"digest": receipt["snapshot"], "head": receipt["head"]}
                 if isinstance(receipt, dict) and "snapshot" in receipt and "head" in receipt else None)
    if candidate is None:
        raise ProtocolError("A delivery run requires a branch candidate review before completion")
    validate_pass_review(review, candidate, receipt, review_rules, record.get("deliveries", {}),
                         expected_shape="branch", expected_stage="candidate")


def validate_rulings(section, rules):
    if not isinstance(section, list):
        raise ProtocolError("rulings must be an array")
    seen = set()
    for ruling in section:
        if not isinstance(ruling, dict) or set(rules["required"]) - set(ruling):
            raise ProtocolError("Each ruling records " + ", ".join(rules["required"]))
        if ruling["id"] in seen:
            raise ProtocolError(f"Ruling id repeated: {ruling['id']}")
        seen.add(ruling["id"])
        if not isinstance(ruling["evidence"], list) or not ruling["evidence"]:
            raise ProtocolError(f"Ruling {ruling['id']} cites evidence")


def validate_questions(section, rules):
    if not isinstance(section, list):
        raise ProtocolError("questions must be a list")
    seen = set()
    for question in section:
        if not isinstance(question, dict):
            raise ProtocolError("Each question must be an object")
        for key in rules["required"]:
            if not isinstance(question.get(key), str) or not question[key].strip():
                raise ProtocolError(f"A question needs a nonempty {key}")
        if question["id"] in seen:
            raise ProtocolError(f"Question id repeated: {question['id']}")
        seen.add(question["id"])
        if "answer" in question and (not isinstance(question["answer"], str) or not question["answer"].strip()):
            raise ProtocolError(f"Question {question['id']} has an empty answer; omit the field until it is answered")


def consumed_questions(task):
    """The question ids a wave task waits for, named question:<id> in its consumes."""
    return [item[len(QUESTION_PREFIX):] for item in task.get("consumes", [])
            if isinstance(item, str) and item.startswith(QUESTION_PREFIX)]


def is_open(question):
    return not question.get("answer")


def is_settled(question):
    """Answered and not withdrawn: only then does a consumer go on."""
    return not is_open(question) and not question.get("withdrawn")


def validate_question_consumers(waves, questions):
    known = {q.get("id"): q for q in questions if isinstance(q, dict)}
    for wave in waves:
        for task in wave.get("tasks", []):
            for qid in consumed_questions(task):
                if qid not in known:
                    raise ProtocolError(f"Task {task['id']} consumes question:{qid}, but the record does not ask {qid}")
                if task["status"] in ("running", "green", "committed") and not is_settled(known[qid]):
                    raise ProtocolError(f"Task {task['id']} consumes question:{qid}, which is not answered")


def validate_environment(section, rules):
    if not isinstance(section, dict):
        raise ProtocolError("environment must be an object")
    for key in rules["required"]:
        if not isinstance(section.get(key), str) or not section[key].strip():
            raise ProtocolError(f"environment.{key} is required")
    commands = section.get("commands", {})
    if not isinstance(commands, dict):
        raise ProtocolError("environment.commands must be an object")
    for name, command in commands.items():
        if name not in rules["commands"]:
            raise ProtocolError(f"environment.commands.{name} is not one of {', '.join(rules['commands'])}")
        if not isinstance(command, str) or not command.strip():
            raise ProtocolError(f"environment.commands.{name} must be a nonempty command")
    if "models" in section:
        validate_model_assignments(section["models"], rules["models"])


def validate_model_assignments(models, rules):
    """Validate recorded bindings, without claiming to prove human consent or host support."""
    if not isinstance(models, dict):
        raise ProtocolError("environment.models must be an object")
    assignments = models.get("assignments", {})
    if not isinstance(assignments, dict):
        raise ProtocolError("environment.models.assignments must be an object")
    for flag in ("model_override_supported", "effort_override_supported"):
        if flag in models and not isinstance(models[flag], bool):
            raise ProtocolError(f"environment.models.{flag} must be boolean")
    if assignments and (not isinstance(models.get("host"), str) or not models["host"].strip()):
        raise ProtocolError("Confirmed model assignments must name the active host")
    for digest, entry in assignments.items():
        if not isinstance(entry, dict) or set(rules["required"]) - set(entry):
            raise ProtocolError("Each model assignment records " + ", ".join(rules["required"]))
        if entry["schema"] != rules["schema"] or entry["tier"] not in rules["tiers"]:
            raise ProtocolError("Unknown task binding schema or tier")
        if digest != entry["request_sha256"]:
            raise ProtocolError("A model assignment key must match its request_sha256")
        for field in ("request_sha256", "models_sha256", "catalog_sha256"):
            value = entry[field]
            if field == "catalog_sha256" and value is None:
                continue
            if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
                raise ProtocolError(f"Task binding {field} must be a SHA256 digest")
        model_id, effort = entry["model_id"], entry["effort"]
        if not isinstance(model_id, str) or not model_id.strip() or "#" in model_id:
            raise ProtocolError("Task binding model_id must name a model without an effort suffix")
        if effort is not None and (not isinstance(effort, str) or not effort.strip() or "#" in effort):
            raise ProtocolError("Task binding effort must be null or a nonempty variant")
        if entry["model_param"] != (f"{model_id}#{effort}" if effort else model_id):
            raise ProtocolError("Task binding model_param must match model_id and effort")
        confirmation = entry["confirmation"]
        if (not isinstance(confirmation, dict) or confirmation.get("confirmed") is not True
                or not isinstance(confirmation.get("source"), str) or not confirmation["source"].strip()):
            raise ProtocolError("Each model assignment records the user's explicit confirmation source")
        if not isinstance(confirmation.get("host"), str) or not confirmation["host"].strip():
            raise ProtocolError("A model confirmation must record its original host")
        if confirmation.get("model_override_supported") is not True:
            raise ProtocolError("A model confirmation requires recorded host model support")
        if not isinstance(confirmation.get("effort_override_supported"), bool):
            raise ProtocolError("A model confirmation records boolean host effort support")
        if effort is not None and confirmation["effort_override_supported"] is not True:
            raise ProtocolError("A model confirmation with effort requires recorded host effort support")


def report_path(value):
    """One lexical boundary for planned and delivered worker outputs."""
    if not isinstance(value, str) or not value.strip():
        raise ProtocolError("Delivery report must be a nonempty relative path")
    output = Path(value)
    if output.is_absolute() or ".." in output.parts:
        raise ProtocolError("Delivery output must stay inside its owned run")
    if (any(":" in part for part in output.parts)
            or output.as_posix().rstrip(" .").casefold() in {"work.json", "result.json", ".write-lock"}):
        raise ProtocolError("A coordinator record or lock is not a worker report")
    return output


def validate_review_checks(review, deliveries, *, complete=True):
    """Check required independent deliveries, without judging their conclusions."""
    outputs = {}
    for key, delivery in deliveries.items():
        if isinstance(delivery, dict) and "output" in delivery:
            outputs.setdefault(report_path(delivery["output"]), []).append(key)
    jobs = {job["id"]: job for job in review.get("jobs", [])}
    discovery_outputs = {report_path(job["output_path"]) for job in jobs.values()}
    rows = []
    verdicts = {0: ("HOLDS", "REFUTED", "UNCERTAIN"),
                1: ("REAL", "FALSE_POSITIVE", "UNCERTAIN"), 2: ("REAL", "FALSE_POSITIVE", "UNCERTAIN"),
                3: ("REAL",)}
    for key, delivery in deliveries.items():
        if not isinstance(delivery, dict) or delivery.get("review") != review["id"] or "check" not in delivery:
            continue
        if "job_id" in delivery or key in jobs:
            raise ProtocolError(f"Delivery {key}: an independent check cannot consume a discovery job")
        check = delivery["check"]
        if not isinstance(check, dict) or check.get("kind") not in ("blind-derivation", "verification", "critic"):
            raise ProtocolError(f"Delivery {key}: invalid independent check kind")
        kind, lens = check["kind"], check.get("lens")
        if kind == "verification" and (type(lens) is not int or lens not in verdicts):
            raise ProtocolError(f"Delivery {key}: verification check requires a lens from 0 to 3")
        if kind != "verification" and "lens" in check:
            raise ProtocolError(f"Delivery {key}: only verification checks have a lens")
        mode = "blind" if kind == "blind-derivation" else "critic" if kind == "critic" else "full-context" if lens == 0 else "verification"
        if "input_mode" in check and check["input_mode"] != mode:
            raise ProtocolError(f"Delivery {key}: independent check input mode mismatch")
        if "independent" in check and not isinstance(check["independent"], bool):
            raise ProtocolError(f"Delivery {key}: independent check declaration must be boolean")
        if "evidence" in check and (not isinstance(check["evidence"], list) or not check["evidence"]
                or any(not isinstance(item, (str, dict)) or not item for item in check["evidence"])):
            raise ProtocolError(f"Delivery {key}: independent check evidence must be a nonempty array")
        if "targets" in check:
            targets = check["targets"]
            if (not isinstance(targets, list) or not targets or any(not isinstance(target, dict)
                    or not all(isinstance(target.get(field), str) and target[field].strip()
                               for field in ("job_id", "finding_id")) for target in targets)):
                raise ProtocolError(f"Delivery {key}: invalid independent check targets")
        if "verdict" in check and (lens is None or check["verdict"] not in verdicts[lens]):
            raise ProtocolError(f"Delivery {key}: invalid independent check verdict")
        for field in ("counterexample", "target", "severity_vote"):
            if field in check and (not isinstance(check[field], str) or not check[field].strip()):
                raise ProtocolError(f"Delivery {key}: independent check {field} must be a nonempty string")
        if "coverage" in delivery and delivery["coverage"] not in ("complete", "incomplete"):
            raise ProtocolError(f"Delivery {key}: invalid independent check coverage")
        if "gaps" in delivery:
            required_gaps(delivery["gaps"])
        if "output" in delivery:
            output = report_path(delivery["output"])
            if output in discovery_outputs or len(outputs[output]) != 1:
                raise ProtocolError(f"Delivery {key}: independent check requires its own output report")
        rows.append(delivery)

    if not complete:
        return

    def obtain(kind, target=None, lens=None):
        selected = [d for d in rows if isinstance(d["check"], dict) and d["check"].get("kind") == kind
                    and (target is None or target in d["check"].get("targets", []))
                    and (lens is None or d["check"].get("lens") == lens)]
        label = f"{kind} check" + (f" lens {lens}" if lens is not None else "")
        if len(selected) != 1:
            raise ProtocolError(f"Review {review['id']}: missing or duplicate {label}")
        result = selected[0]
        expected_role = "senior-review:premise-auditor" if kind == "blind-derivation" or lens == 0 else "work-controller:isolated-worker"
        expected_roles = {expected_role}
        # Read historical worker evidence only under its recorded support binding.
        legacy_role = "project-protocol:isolated-worker"
        if expected_role == "work-controller:isolated-worker" and legacy_role in review.get("support", []):
            expected_roles.add(legacy_role)
        expected_mode = "blind" if kind == "blind-derivation" else "critic" if kind == "critic" else "full-context" if lens == 0 else "verification"
        if (result.get("role") not in expected_roles or result.get("status") != "delivered"
                or result.get("coverage") != "complete" or required_gaps(result.get("gaps", []))
                or result.get("candidate") != review.get("grounding", {}).get("candidate")
                or result["check"].get("input_mode") != expected_mode
                or result["check"].get("independent") is not True or not result["check"].get("evidence")):
            raise ProtocolError(f"Review {review['id']}: incomplete {label}")
        if lens is not None and result["check"].get("verdict") not in verdicts[lens]:
            raise ProtocolError(f"Review {review['id']}: missing {label} verdict")
        return result["check"]

    for flag, kind in (("blind_derivation", "blind-derivation"), ("critic", "critic")):
        if review.get(flag):
            obtain(kind)
    for job_id, delivery in ((d["job_id"], d) for d in deliveries.values()
                              if d.get("review") == review["id"] and "job_id" in d):
        for finding in delivery.get("findings", []):
            severity, confidence = finding.get("severity"), finding.get("confidence")
            if (not isinstance(severity, str) or type(confidence) not in (int, float) or not 0 <= confidence <= 100):
                raise ProtocolError(f"Review {review['id']}: finding lacks verification eligibility")
            if review.get("review_basis", "changeset") == "changeset" and finding.get("introduced_by_candidate") is False:
                continue
            level = review["verification"]
            selected = confidence >= 50 if level == "all-above-floor" else severity.lower() in {"critical", "high"}
            if not selected:
                continue
            target = {"job_id": job_id, "finding_id": finding["id"]}
            light = review["shape"] == "light"
            provenance = finding.get("premise_provenance")
            universal = re.search(r"\b(no|never|cannot|always|only)\b", str(finding.get("premise", "")), re.IGNORECASE)
            if light or provenance != "independent" or universal:
                premise = obtain("verification", target, 0)
                refuted = premise.get("verdict") == "REFUTED" and re.search(r".+:\d+", str(premise.get("counterexample", "")))
                if refuted and (premise.get("target") == "PREMISE" or
                                premise.get("target") == "SUPPORT" and provenance == "shared-context"):
                    continue
            first = obtain("verification", target, 1)
            if not light:
                second = obtain("verification", target, 2)
                if not all(r.get("verdict") == "FALSE_POSITIVE" for r in (first, second)):
                    obtain("verification", target, 3)


def required_gaps(gaps):
    """Unassigned limitations may be recorded without waiving mandatory checks."""
    if not isinstance(gaps, list):
        raise ProtocolError("Coverage gaps must be an array")
    if any(isinstance(gap, dict) and gap.get("required") is False and
           (not isinstance(gap.get("reason"), str) or not gap["reason"].strip()) for gap in gaps):
        raise ProtocolError("An unassigned limitation requires its reason")
    return any(not isinstance(gap, dict) or gap.get("required") is not False for gap in gaps)


def validate_reviews(section, rules, deliveries, *, complete=False):
    """Each review records the roster its helper computed and bounds the deliveries bound to it."""
    if not isinstance(section, list):
        raise ProtocolError("reviews must be an array")
    allowed, plans = {}, {}
    for review in section:
        if not isinstance(review, dict) or set(rules["required"]) - set(review):
            raise ProtocolError("Each review records " + ", ".join(rules["required"]))
        name = review["id"]
        if not isinstance(name, str) or not name.strip():
            raise ProtocolError("Review identity must be a nonempty string")
        if name in allowed:
            raise ProtocolError(f"Review id repeated: {name}")
        for key, values in (("schema", [rules["schema"]]), ("shape", rules["shapes"]),
                            ("kind", rules["kinds"]), ("tier", rules["tiers"])):
            if review[key] not in values:
                raise ProtocolError(f"Review {name}: {key} must be one of {', '.join(values)}")
        roles = [review["roster"], review.get("support", [])]
        if not roles[0] or not all(isinstance(group, list) and all(isinstance(r, str) and r for r in group)
                                   for group in roles):
            raise ProtocolError(f"Review {name}: roster must be a nonempty list of role identities")
        allowed[name] = set(roles[0]) | set(roles[1])
        for flag in ("blind_derivation", "critic"):
            if flag in review and not isinstance(review[flag], bool):
                raise ProtocolError(f"Review {name}: {flag} must be boolean")
        for field in ("required_specialists", "jobs"):
            if field in review and not isinstance(review[field], list):
                raise ProtocolError(f"Review {name}: {field} must be an array")
        if "required_specialists" in review or "jobs" in review:
            if not all(field in review for field in ("required_specialists", "jobs")):
                raise ProtocolError(f"Review {name}: a composition plan requires both obligations and jobs")
            if review["verification"] not in rules["verification_levels"]:
                raise ProtocolError(f"Review {name}: invalid verification level")
            if complete and (not review["required_specialists"] or not review["jobs"]):
                raise ProtocolError(f"Review {name}: completion requires a nonempty composition plan")
            if "grounding" in review and not isinstance(review["grounding"], dict):
                raise ProtocolError(f"Review {name}: grounding must be an object")
            required, covered, jobs = set(), [], {}
            for member in review.get("required_specialists", []):
                if (not isinstance(member, dict) or not all(isinstance(member.get(k), str) and member[k]
                        for k in ("specialist_id", "scope_id")) or not isinstance(member.get("evidence"), list)
                        or not member["evidence"] or any(not isinstance(item, (str, dict)) or not item for item in member["evidence"])):
                    raise ProtocolError(f"Review {name}: invalid specialist obligation")
                required.add((member["specialist_id"], member["scope_id"]))
            for job in review.get("jobs", []):
                fields = rules["job_required"]
                if not isinstance(job, dict) or not all(job.get(k) for k in fields):
                    raise ProtocolError(f"Review {name}: incomplete job binding")
                if not all(isinstance(job[k], str) and job[k].strip() for k in ("id", "role", "scope_id", "input_mode", "body_sha256", "output_path")):
                    raise ProtocolError(f"Review {name}: job identities and paths must be strings")
                if "knowledge_selection" in job and (not isinstance(job["knowledge_selection"], str) or not job["knowledge_selection"].strip()):
                    raise ProtocolError(f"Review {name}: job knowledge selection must be a fingerprint string")
                if "source_bindings" in job and not isinstance(job["source_bindings"], dict):
                    raise ProtocolError(f"Review {name}: job source bindings must be an object")
                report_path(job["output_path"])
                if job["id"] in jobs:
                    raise ProtocolError(f"Review {name}: duplicate job identity")
                members = job["specialist_ids"]
                if not isinstance(members, list) or not all(isinstance(m, str) and m for m in members):
                    raise ProtocolError(f"Review {name}: invalid job members")
                if not isinstance(job["candidate"], dict) or not job["candidate"] or job["candidate"] != review.get("grounding", {}).get("candidate"):
                    raise ProtocolError(f"Review {name}: job candidate mismatch")
                if job["role"] not in allowed[name]:
                    raise ProtocolError(f"Review {name}: job role outside roster and support")
                if job["input_mode"] != "discovery" and len(members) != 1:
                    raise ProtocolError(f"Review {name}: independent job cannot merge members")
                jobs[job["id"]] = job
                covered.extend((m, job["scope_id"]) for m in members)
            if set(covered) != required or len(covered) != len(set(covered)):
                raise ProtocolError(f"Review {name}: jobs do not cover every scoped obligation exactly once")
            if review["shape"] == "light" and jobs and len(jobs) != 1:
                raise ProtocolError(f"Review {name}: light review has exactly one discovery")
            plans[name] = jobs
    accounted = set()
    for key, delivery in deliveries.items():
        if not isinstance(delivery, dict) or "review" not in delivery:
            continue
        bound = delivery["review"]
        if not isinstance(bound, str) or not isinstance(delivery.get("role"), str):
            raise ProtocolError(f"Delivery {key}: review and role must be strings")
        if bound not in allowed:
            raise ProtocolError(f"Delivery {key} names review {bound}, which the run does not record")
        if delivery.get("role") not in allowed[bound]:
            raise ProtocolError(f"Delivery {key} dispatches {delivery.get('role')}, "
                                f"which the computed roster of review {bound} does not contain")
        if "job_id" not in delivery:
            continue
        if not isinstance(delivery["job_id"], str) or not delivery["job_id"].strip():
            raise ProtocolError(f"Delivery {key}: review job identity must be a nonempty string")
        identity = (bound, delivery["job_id"])
        job = plans.get(bound, {}).get(delivery["job_id"])
        if job is None or identity in accounted:
            raise ProtocolError(f"Delivery {key}: unknown or duplicate review job")
        accounted.add(identity)
        if delivery.get("role") != job["role"]:
            raise ProtocolError(f"Delivery {key}: job role mismatch")
        if delivery.get("status") != "delivered":
            if complete:
                raise ProtocolError(f"Delivery {key}: mandatory job not delivered")
            continue
        for field in ("scope_id", "body_sha256", "candidate", "specialist_ids"):
            if delivery.get(field) != job[field]:
                raise ProtocolError(f"Delivery {key}: job {field} mismatch")
        for field in ("knowledge_selection", "source_bindings"):
            if field in job and delivery.get(field) != job[field]:
                raise ProtocolError(f"Delivery {key}: job {field} mismatch")
        if str(delivery.get("output", "")).replace("\\", "/") != str(job["output_path"]).replace("\\", "/"):
            raise ProtocolError(f"Delivery {key}: job output path mismatch")
        outcomes = delivery.get("member_results")
        if not isinstance(outcomes, list) or len(outcomes) != len(job["specialist_ids"]):
            raise ProtocolError(f"Delivery {key}: missing member results")
        seen_members = set()
        findings = delivery.get("findings")
        if not isinstance(findings, list) or any(not isinstance(f, dict) or not isinstance(f.get("id"), str) or not f["id"] for f in findings):
            raise ProtocolError(f"Delivery {key}: canonical findings require unique IDs")
        finding_ids = {f["id"] for f in findings}
        if len(finding_ids) != len(findings):
            raise ProtocolError(f"Delivery {key}: duplicate canonical finding")
        referenced = set()
        for result in outcomes:
            if not isinstance(result, dict) or result.get("specialist_id") not in job["specialist_ids"]:
                raise ProtocolError(f"Delivery {key}: unknown member result")
            member = result["specialist_id"]
            if member in seen_members:
                raise ProtocolError(f"Delivery {key}: duplicate member result")
            seen_members.add(member)
            if (result.get("status") not in ("delivered", "failed")
                    or result.get("coverage") not in ("complete", "incomplete")
                    or not isinstance(result.get("findings"), list) or not isinstance(result.get("gaps"), list)):
                raise ProtocolError(f"Delivery {key}: invalid member outcome")
            if any(not isinstance(f, str) or f not in finding_ids for f in result["findings"]):
                raise ProtocolError(f"Delivery {key}: member references unknown canonical finding")
            referenced.update(result["findings"])
            if complete and (result["status"] != "delivered" or result["coverage"] != "complete" or required_gaps(result["gaps"])):
                raise ProtocolError(f"Delivery {key}: member {member} has unsuccessful coverage")
        if referenced != finding_ids:
            raise ProtocolError(f"Delivery {key}: canonical finding has no member attribution")
    if complete and {(review, job) for review, jobs in plans.items() for job in jobs} - accounted:
        raise ProtocolError("Completion requires every expected review job and member delivery")
    for review in section:
        if review["id"] in plans:
            validate_review_checks(review, deliveries, complete=complete)


def validate_grants(record):
    """Authorizations asked after init: each names its kind, scope and the user's answer."""
    rules = contract()["grants"]
    grants = record.get("grants", [])
    if not isinstance(grants, list):
        raise ProtocolError("grants must be an array")
    seen = set()
    for grant in grants:
        if not isinstance(grant, dict) or set(rules["required"]) - set(grant):
            raise ProtocolError("Each grant records " + ", ".join(rules["required"]))
        if grant["id"] in seen:
            raise ProtocolError(f"Grant id repeated: {grant['id']}")
        seen.add(grant["id"])
        if grant["kind"] not in rules["kinds"]:
            raise ProtocolError(f"Grant {grant['id']}: kind must be one of {', '.join(rules['kinds'])}")
        source = grant["source"]
        if not isinstance(source, dict) or source.get("kind") != "user" or not str(source.get("reference", "")).strip():
            raise ProtocolError(f"Grant {grant['id']} names the user's answer as its source")


def validate_loop(record):
    """Validate the optional loop sections a lifecycle run carries."""
    rules = contract()["loop"]
    present = {name: record[name] for name in rules["sections"] if name in record}
    if "workspace" in present:
        validate_workspace(present["workspace"], rules["workspace"])
    if "preflight" in present:
        validate_preflight(present["preflight"], rules["preflight"])
    if "adr" in present:
        validate_adr(present["adr"], rules["adr"])
    if "waves" in present:
        validate_waves(present["waves"], rules["waves"], present.get("workspace"),
                       record.get("reviews", []), rules["reviews"], record.get("deliveries", {}))
    if "rulings" in present:
        validate_rulings(present["rulings"], rules["rulings"])
    validate_reviews(record.get("reviews", []), rules["reviews"], record.get("deliveries", {}),
                     complete=record.get("status") == "complete")
    validate_delivery_completion(record, rules["reviews"])
    if "questions" in present:
        validate_questions(present["questions"], rules["questions"])
    if "waves" in present:
        validate_question_consumers(present["waves"], present.get("questions", []))
    if "environment" in present:
        validate_environment(present["environment"], rules["environment"])


def validate_loop_transitions(old, new):
    rules = contract()["loop"]
    for section, entry in (("rulings", "a recorded decision"), ("reviews", "a computed roster")):
        before = old.get(section, [])
        if rules[section].get("append_only") and new.get(section, [])[:len(before)] != before:
            raise ProtocolError(f"{section.capitalize()} are append-only; {entry} cannot be altered or removed")


def validate_record(record, project=None, root=None, historical=False):
    rules = contract()
    missing = sorted(set(rules["required"]) - set(record))
    if missing:
        raise ProtocolError("Missing work fields: " + ", ".join(missing))
    if record["schema"] != SCHEMA or not RUN_ID.fullmatch(str(record["run_id"])):
        raise ProtocolError("Unknown work schema or invalid run identity")
    if not isinstance(record["revision"], int) or isinstance(record["revision"], bool) or record["revision"] < 0:
        raise ProtocolError("Invalid record revision")
    for key in ("project", "scope", "authorizations", "budget", "phases", "deliveries", "gates"):
        if not isinstance(record[key], dict):
            raise ProtocolError(f"{key} must be an object")
    for key in ("plan", "required_gates"):
        if not isinstance(record[key], list):
            raise ProtocolError(f"{key} must be an array")
    gates = record["required_gates"]
    if any(not isinstance(gate, str) or not gate for gate in gates) or len(set(gates)) != len(gates):
        raise ProtocolError("Required gates must be distinct nonempty identifiers")
    if not isinstance(record["objective"], str) or not record["objective"].strip():
        raise ProtocolError("An objective is required")
    if not isinstance(record["operation"], str) or not OPERATION.fullmatch(record["operation"]):
        raise ProtocolError("operation must be a lowercase name of letters, digits and hyphens")
    if record["status"] not in rules["fields"]["status"]["values"]:
        raise ProtocolError("Invalid run status")
    if "process_required" in record and not isinstance(record["process_required"], bool):
        raise ProtocolError("process_required must be a boolean")
    delivery_reports = []
    for container, state_kind in (("phases", "phases"), ("deliveries", "deliveries"), ("gates", "gates")):
        for identity, item in record[container].items():
            if not isinstance(identity, str) or not isinstance(item, dict):
                raise ProtocolError(f"Invalid {container} entry")
            if item.get("status") not in rules["states"][state_kind]["values"]:
                raise ProtocolError(f"Invalid {container} status: {identity}")
            if container == "phases" and item["status"] == "skipped" and not item.get("reason"):
                raise ProtocolError("A skipped phase requires a reason")
            if container == "deliveries" and item["status"] == "delivered" and not item.get("output"):
                raise ProtocolError(f"Delivered worker requires an explicit report: {identity}")
            if container == "deliveries" and "output" in item:
                output = report_path(item["output"])
                if project is not None and item["status"] == "delivered":
                    report = root / "runs" / record["run_id"] / output
                    no_links(report, root)
                    if not report.is_file():
                        raise ProtocolError(f"Delivered report is missing: {identity}")
                    if report.stat().st_size == 0:
                        raise ProtocolError(f"Delivered report is empty: {identity}")
                    directory = root / "runs" / record["run_id"]
                    if any(reserved.exists() and report.samefile(reserved)
                           for reserved in (directory / name for name in ("work.json", "result.json", ".write-lock"))):
                        raise ProtocolError("A coordinator record or lock is not a worker report")
                    if any(("check" in item or is_check) and report.samefile(other)
                           for other, is_check in delivery_reports):
                        raise ProtocolError("An independent check requires its own output report")
                    delivery_reports.append((report, "check" in item))
    validate_grants(record)
    if not historical:
        validate_loop(record)
    if project is not None and not historical:
        if record["project"].get("root") != str(project):
            raise ProtocolError("Project identity does not match this invocation")
        if record.get("output_root") != str(root):
            raise ProtocolError("Output root does not match the recorded identity")
    if not historical and "process" in record:
        validate_process_binding(record, project, root)
    if record["status"] == "complete":
        if record.get("process_required") and "process" not in record:
            raise ProtocolError("Completion requires the admitted process binding")
        if record["interruption"] is not None:
            raise ProtocolError("An interrupted run cannot be complete")
        if any(p["status"] not in rules["completion"]["phases"] for p in record["phases"].values()):
            raise ProtocolError("Completion requires closed phases")
        if any(d["status"] not in rules["completion"]["deliveries"] for d in record["deliveries"].values()):
            raise ProtocolError("Completion requires every expected delivery")
        candidate = record.get("candidate", record["project"])
        for name in record["required_gates"]:
            gate = record["gates"].get(name)
            if not gate or gate.get("status") != "passed":
                raise ProtocolError(f"Missing or unsuccessful required gate: {name}")
            if gate.get("snapshot") != candidate["snapshot"]["digest"] or gate.get("head") != candidate.get("head"):
                raise ProtocolError(f"Stale candidate gate: {name}")
            evidence = gate.get("evidence")
            if not isinstance(evidence, dict) or not (evidence.get("command") or evidence.get("job")):
                raise ProtocolError(f"Missing gate evidence: {name}")
            if evidence.get("job") and not evidence.get("command"):
                if (not candidate.get("head") or candidate.get("head_matches_snapshot") is not True
                        or not evidence.get("attempt") or not evidence.get("source_revision")
                        or evidence["source_revision"] != candidate["head"]):
                    raise ProtocolError(f"Remote gate lacks candidate revision and job attempt: {name}")
    return record


def validate_process_binding(record, project, root):
    """Load the bundled bridge only for records that opt into process execution."""
    location = Path(__file__).with_name("process_binding.py")
    spec = importlib.util.spec_from_file_location("daodan_process_binding", location)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    try:
        helper.validate(record, project, root, no_links, report_path)
    except Exception as error:
        raise ProtocolError(f"Invalid process binding: {error}") from error


def validate_task_commit_current(project, task, current, run_id, wave_number):
    identity = task["id"]
    commit_sha = task.get("commit_sha")
    if (task["candidate"]["digest"] != current["snapshot"]["digest"]
            or commit_sha != current.get("head")):
        raise ProtocolError(f"Task {identity} commit evidence is stale or does not name the current commit")
    lineage = git_value(project, "rev-list", "--parents", "-n", "1", commit_sha)
    parts = lineage.split() if lineage else []
    expected = 1 if task["candidate"]["head"] is None else 2
    if len(parts) != expected or (expected == 2 and parts[1] != task["candidate"]["head"]):
        raise ProtocolError(f"Task {identity} commit parent differs from its reviewed HEAD")
    message = git_value(project, "log", "-1", "--format=%B", commit_sha) or ""
    trailers = re.findall(r"(?m)^Daodan-Task: \S+ wave ([1-9][0-9]*)/([1-9][0-9]*)\s*$", message)
    if not any(f"Daodan-Task: {run_id} wave {number}/{total}" in message
               and int(number) == wave_number and int(total) >= wave_number for number, total in trailers):
        raise ProtocolError(f"Task {identity} commit lacks the correct run and wave trailer")
    changed = git_value(project, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", commit_sha, "--")
    prefix = git_value(project, "rev-parse", "--show-prefix") or ""
    paths = set()
    for name in changed.splitlines() if changed is not None else []:
        if prefix and not name.startswith(prefix):
            raise ProtocolError(f"Task {identity} commit contains a path outside its project")
        paths.add(name[len(prefix):] if prefix else name)
    owned = set(task["write_set"])
    if not paths or not paths.issubset(owned):
        raise ProtocolError(f"Task {identity} commit contains paths outside its write_set")


def validate_commit_transitions(old, new, project):
    previous = {task.get("id"): task for wave in old.get("waves", []) for task in wave.get("tasks", [])}
    for wave in new.get("waves", []):
        for task in wave.get("tasks", []):
            before = previous.get(task.get("id"), {})
            if before.get("status") == "committed" and task.get("status") == "committed" and task != before:
                raise ProtocolError(f"Task {task['id']} committed evidence is immutable; reopen it with fresh evidence")
    committed = [task for wave in new.get("waves", []) for task in wave.get("tasks", [])
                 if task.get("status") == "committed" and previous.get(task.get("id"), {}).get("status") != "committed"]
    previous_waves = {wave.get("id"): wave for wave in old.get("waves", [])}
    for identity, before in previous_waves.items():
        if before.get("status") != "sealed":
            continue
        after = next((wave for wave in new.get("waves", []) if wave.get("id") == identity), None)
        if after is None or after != before:
            raise ProtocolError(f"Wave {identity} sealed membership and evidence are immutable; reopen with a fresh review")
    sealed = [wave for wave in new.get("waves", []) if wave.get("status") == "sealed"
              and previous_waves.get(wave.get("id"), {}).get("status") != "sealed"]
    started = [(wave, task) for wave in new.get("waves", []) for task in wave.get("tasks", [])
               if task.get("status") == "running" and previous.get(task.get("id"), {}).get("status") == "pending"]
    if not committed and not sealed and not started:
        return
    if project is None:
        raise ProtocolError("Committed task transitions require project binding")
    current = project_binding(project, new["scope"], Path(new["output_root"]))
    for wave, task in started:
        if wave["plan_candidate"]["digest"] != current["snapshot"]["digest"]:
            raise ProtocolError(f"Task {task['id']} cannot start on bytes changed after the plan review")
    for task in committed:
        wave_number = next(index for index, entry in enumerate(new["waves"], 1)
                           if any(item is task for item in entry["tasks"]))
        validate_task_commit_current(project, task, current, new["run_id"], wave_number)
    for wave in sealed:
        receipt = wave["wave_review"]
        if receipt["snapshot"] != current["snapshot"]["digest"] or receipt["head"] != current.get("head"):
            raise ProtocolError(f"Wave {wave['id']} seal review is stale or does not name the current candidate")


def squash_inputs_match_commit(project, current, scope, output_root):
    """Match raw blobs first; prove only Git's built-in CRLF equivalence otherwise."""
    if current.get("head_matches_snapshot") is True:
        return True
    if scope is None or output_root is None:
        return False
    autocrlf = (git_value(project, "config", "--type=bool", "--get", "core.autocrlf")
                or git_value(project, "config", "--get", "core.autocrlf"))
    attributes = ("text", "crlf", "eol", "filter", "working-tree-encoding", "ident")

    def equivalent(relative, entry, blob, blob_digest, blob_size):
        # These inspection commands never clean/smudge content or run filters.
        # Pin conversion attributes to the committed tree and require the live
        # attributes to agree, even when an attributes file is outside scope.
        values = None
        for source in (("--source", current["head"]), ()):
            result = git_value(project, "check-attr", "-z", *source, *attributes, "--", relative)
            fields = result.split("\0") if result is not None else []
            if (len(fields) != len(attributes) * 3 + 1
                    or any(fields[index] != relative for index in range(0, len(fields) - 1, 3))):
                return False
            found = {fields[index + 1]: fields[index + 2]
                     for index in range(0, len(fields) - 1, 3)}
            if values is not None and found != values:
                return False
            values = found
        if any(values.get(name) not in {"unspecified", "unset"}
               for name in ("filter", "working-tree-encoding", "ident")):
            return False
        # Git resolves legacy crlf only when text has no recognized setting.
        text_mode = values["text"]
        if text_mode not in {"set", "unset", "auto", "input"}:
            text_mode = values["crlf"]
        if text_mode == "unset":
            return False
        forced = text_mode in {"set", "input"} or (
            text_mode != "auto" and values["eol"] in {"lf", "crlf"})
        automatic = text_mode == "auto" or (not forced and autocrlf in {"true", "input"})
        if not forced and not automatic:
            return False
        eol = git_value(project, "ls-files", "--stage", "--eol", "-z", "--", f":(literal){relative}")
        if eol is None or not eol.endswith("\0") or eol.count("\0") != 1:
            return False
        fields = eol[:-1].split("\t", 2)
        if len(fields) != 3 or fields[2] != relative:
            return False
        staged, stats = fields[0].split(), fields[1].split()
        if len(staged) != 3 or staged[1:] != [blob, "0"] or len(stats) < 2:
            return False
        # Git's own statistics cover lone CR, NUL, the control-byte threshold
        # and terminal EOF. Auto conversion also preserves CRLF in the index.
        if automatic and (stats[1] not in {"w/lf", "w/crlf", "w/mixed", "w/none"}
                          or stats[0] in {"i/crlf", "i/mixed"}):
            return False
        path = project / relative
        no_links(path, project)
        raw_digest, lf_digest = hashlib.sha256(), hashlib.sha256()
        raw_size = lf_size = 0
        pending = b""
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(64 * 1024), b""):
                raw_digest.update(chunk)
                raw_size += len(chunk)
                data = pending + chunk
                pending = b"\r" if data.endswith(b"\r") else b""
                if pending:
                    data = data[:-1]
                data = data.replace(b"\r\n", b"\n")
                lf_digest.update(data)
                lf_size += len(data)
        lf_digest.update(pending)
        lf_size += len(pending)
        return (raw_digest.hexdigest() == entry["sha256"] and raw_size == entry["bytes"]
                and lf_digest.hexdigest() == blob_digest and lf_size == blob_size)

    exclusions = [project / item for item in scope.get("excluded", [])]

    def excluded_path(path):
        return (path == output_root or path.is_relative_to(output_root)
                or any(path == item or path.is_relative_to(item) for item in exclusions)
                or ".git" in path.relative_to(project).parts)

    return head_matches_inputs(project, current["head"], scope["paths"], current["snapshot"]["files"],
                               excluded_path, equivalent)


def validate_integrated_commit(project, integration, current, scope=None, output_root=None):
    """Bind integration to Git ancestry or a pinned, content-identical squash."""
    merged = integration["merged_sha"]
    if merged != current.get("head"):
        raise ProtocolError("Completion merge SHA does not name current HEAD")
    receipt = integration["candidate_review"]
    reviewed = receipt["head"]
    if integration.get("strategy") != "squash":
        if git_value(project, "merge-base", "--is-ancestor", reviewed, merged) is None:
            raise ProtocolError("Completion merge does not descend from the reviewed candidate")
        return

    target = integration.get("target_sha")
    for value in (target, reviewed, merged):
        if not isinstance(value, str) or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value):
            raise ProtocolError("Squash integration requires full target, reviewed and merged commit IDs")
        if git_value(project, "rev-parse", "--verify", f"{value}^{{commit}}") != value:
            raise ProtocolError("Squash integration references an unavailable commit")
    if git_value(project, "merge-base", "--is-ancestor", target, reviewed) is None:
        raise ProtocolError("Reviewed squash candidate does not include the pinned target")
    if git_value(project, "show", "-s", "--format=%P", merged) != target:
        raise ProtocolError("Squash integration must have exactly the pinned target as its parent")
    reviewed_tree = git_value(project, "rev-parse", f"{reviewed}^{{tree}}")
    if not reviewed_tree or git_value(project, "rev-parse", f"{merged}^{{tree}}") != reviewed_tree:
        raise ProtocolError("Squash integration tree differs from the reviewed candidate")
    if (current["snapshot"]["digest"] != receipt.get("snapshot")
            or not squash_inputs_match_commit(project, current, scope, output_root)):
        raise ProtocolError("Squash review snapshot must match the clean integrated content")


def validate_transitions(old, new, project=None):
    rules = contract()
    if "process" in old and new.get("process") != old["process"]:
        raise ProtocolError("Process binding is immutable; a changed graph needs a new work record")
    if old.get("process_required") and new.get("process_required") is not True:
        raise ProtocolError("The required process binding cannot be disabled")
    if new.get("process_required") and "process" not in new and any(
        task.get("status") == "running"
        for wave in new.get("waves", []) for task in wave.get("tasks", [])
    ):
        raise ProtocolError("A process-required task cannot dispatch before its process is bound")
    if new["status"] == "complete":
        waiting = [q["id"] for q in new.get("questions", []) if is_open(q)]
        if waiting:
            raise ProtocolError(f"Completion requires every question answered or withdrawn: {', '.join(waiting)}")
    if new["required_gates"][:len(old["required_gates"])] != old["required_gates"]:
        raise ProtocolError("Required gates are append-only; a check cannot be removed or weakened")
    if new.get("grants", [])[:len(old.get("grants", []))] != old.get("grants", []):
        raise ProtocolError("Grants are append-only; an authorization cannot be altered or withdrawn")
    validate_loop_transitions(old, new)
    validate_commit_transitions(old, new, project)
    if new.get("status") == "complete" and new.get("waves"):
        current = project_binding(project, new["scope"], Path(new["output_root"]))
        validate_integrated_commit(project, new["integration"], current,
                                   new["scope"], Path(new["output_root"]))
    for key in ("phases", "deliveries"):
        for identity, before in old[key].items():
            after = new[key].get(identity)
            if after is None or after["status"] not in rules["states"][key][before["status"]]:
                raise ProtocolError(f"Invalid {key} transition: {identity}")
            if key == "deliveries" and before["status"] == "failed" and after["status"] != "failed":
                history = after.get("attempts", [])
                if not any(attempt.get("status") == "failed" for attempt in history if isinstance(attempt, dict)):
                    raise ProtocolError("A retry must retain its failed attempt")


def validate_result(result, work):
    """Validate the envelope and its references without interpreting domain payloads."""
    rules = contract()["result"]
    if "process" in work and result.get("process") != work["process"]:
        raise ProtocolError("Result must reference its bound process and definition")
    missing = sorted(set(rules["required"]) - set(result))
    if missing:
        raise ProtocolError("Missing result fields: " + ", ".join(missing))
    if result["schema"] != rules["schema"]:
        raise ProtocolError("Unknown project-result schema")
    if result["run_id"] != work["run_id"] or result["work_revision"] != work["revision"]:
        raise ProtocolError("Result does not identify this exact work revision")
    if result["scope"] != work["scope"]:
        raise ProtocolError("Result scope differs from its work record")
    candidate = work.get("candidate", work["project"])
    if result["snapshot"] != candidate["snapshot"]["digest"]:
        raise ProtocolError("Result snapshot differs from its candidate")
    for key in ("deliveries", "checks"):
        if not isinstance(result[key], dict):
            raise ProtocolError(f"Result {key} must be an object")
    if not isinstance(result["outputs"], list) or any(not isinstance(item, dict) for item in result["outputs"]):
        raise ProtocolError("Result outputs must be an array of references")
    if not isinstance(result["limitations"], list) or any(not isinstance(item, str) for item in result["limitations"]):
        raise ProtocolError("Result limitations must be an array of strings")
    if not isinstance(result["complete"], bool):
        raise ProtocolError("Result complete must be a boolean")
    if result["complete"] and work["status"] != "complete":
        raise ProtocolError("An unfinished work record cannot have a complete result")
    if set(result["deliveries"]) != set(work["deliveries"]):
        raise ProtocolError("Result must account for every expected delivery")
    for identity, item in result["deliveries"].items():
        if not isinstance(item, dict) or item.get("status") != work["deliveries"][identity]["status"]:
            raise ProtocolError(f"Result misstates delivery: {identity}")
    for identity in work["required_gates"]:
        item = result["checks"].get(identity)
        if not isinstance(item, dict) or item.get("status") != work["gates"].get(identity, {}).get("status", "pending"):
            raise ProtocolError(f"Result omits or misstates required check: {identity}")
    return result


def merge(base, patch):
    result = copy.deepcopy(base)
    for key, value in patch.items():
        result[key] = merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else copy.deepcopy(value)
    return result


ASK_FIELDS = frozenset({"id", "phase", "text"})
ANSWER_FIELDS = frozenset({"question", "text", "source", "withdraw"})
QUESTION_MARKS = ("?", "\uff1f", "\u061f")


def decision(text):
    """The question's first line, normalized: two questions asking it are one."""
    lines = text.strip().splitlines()
    return " ".join(lines[0].split()).casefold() if lines else ""


def ask_question(record, question):
    """Return the updated record, or None when the question is already recorded, and its id."""
    if set(question) - ASK_FIELDS:
        raise ProtocolError("ask records a question only; answers go through answer")
    text = question.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ProtocolError("A question needs a nonempty text")
    if not text.strip().splitlines()[0].rstrip().endswith(QUESTION_MARKS):
        raise ProtocolError("The first line must be the question, ending with a question mark")
    questions = record.get("questions") or []
    for existing in questions:
        if existing.get("id") == question.get("id"):
            if {key: existing[key] for key in ASK_FIELDS if key in existing} != question:
                raise ProtocolError(f"Question {question['id']} already asks something else")
            return None, existing["id"]
    # Only an open question of the same phase is the same request; whether an
    # earlier answer still applies is the coordinator's judgment, not a match.
    for existing in questions:
        if (is_open(existing) and existing.get("phase") == question.get("phase")
                and decision(existing.get("text", "")) == decision(text)):
            return None, existing["id"]
    updated = copy.deepcopy(record)
    updated.setdefault("questions", []).append({**question, "asked_at": timestamp()})
    return updated, question.get("id")


def answer_question(record, reply):
    """Return the record with the user's answer, or None when it repeats the recorded one."""
    if set(reply) - ANSWER_FIELDS:
        raise ProtocolError("answer takes question, text, source and withdraw")
    qid, withdraw = reply.get("question"), reply.get("withdraw", False)
    if not isinstance(withdraw, bool):
        raise ProtocolError("withdraw must be a boolean")
    sources = contract()["loop"]["questions"]["sources"]
    if reply.get("source") not in sources:
        raise ProtocolError(f"answer source is not one of {', '.join(sources)}")
    target = next((q for q in record.get("questions") or [] if q.get("id") == qid), None)
    if target is None:
        raise ProtocolError(f"The record does not ask {qid}")
    if not is_open(target):
        if (target["answer"], bool(target.get("withdrawn"))) == (reply.get("text"), withdraw):
            return None
        raise ProtocolError(f"Question {qid} is answered; a changed answer is a new question")
    updated = copy.deepcopy(record)
    entry = next(q for q in updated["questions"] if q.get("id") == qid)
    entry.update(answer=reply.get("text"), source=reply.get("source"), answered_at=timestamp())
    if withdraw:
        entry["withdrawn"] = True
    return updated


def pending_consumers(record):
    questions = {q.get("id"): q for q in record.get("questions") or []}
    for wave in record.get("waves") or []:
        for task in wave.get("tasks", []):
            consumed = consumed_questions(task)
            if task.get("status") == "pending" and consumed:
                yield task["id"], [questions[qid] for qid in consumed if qid in questions]


def waiting(record):
    """Pending tasks and the open questions each still waits for."""
    return {task: [q["id"] for q in consumed if is_open(q)]
            for task, consumed in pending_consumers(record) if any(is_open(q) for q in consumed)}


def stranded(record):
    """Pending tasks that consume a withdrawn question: only a new plan drops them."""
    return [task for task, consumed in pending_consumers(record) if any(q.get("withdrawn") for q in consumed)]


def unblocked(record, qid):
    return [task for task, consumed in pending_consumers(record)
            if qid in {q["id"] for q in consumed} and all(is_settled(q) for q in consumed)]


def reconcile_interrupted_commit(before, project, root):
    current = project_binding(project, before["scope"], root)
    for wave_number, wave in enumerate(before.get("waves", []), 1):
        for task in wave.get("tasks", []):
            if (task.get("status") == "committed" or "commit_sha" in task
                    or not isinstance(task.get("candidate"), dict)
                    or not isinstance(task.get("pre_commit_review"), dict)):
                continue
            candidate = copy.deepcopy(task)
            candidate["status"] = "committed"
            candidate["commit_sha"] = current.get("head")
            try:
                validate_task_commit_current(project, candidate, current, before["run_id"], wave_number)
            except ProtocolError:
                continue
            updated = copy.deepcopy(before)
            target = next(item for entry in updated["waves"] for item in entry["tasks"]
                          if item["id"] == task["id"])
            target.update(status="committed", commit_sha=current["head"])
            return updated
    return None


def reconcile_interrupted_integration(before, project, root):
    """Recover the recorded integration handoff without changing any receipt."""
    integration = before.get("integration")
    receipt = integration.get("candidate_review") if isinstance(integration, dict) else None
    if not isinstance(receipt, dict):
        return None
    previous = before.get("candidate", before["project"])
    current = project_binding(project, before["scope"], root)
    if (any(current.get(key) != before["project"].get(key) or current.get(key) != previous.get(key)
            for key in ("root", "worktree", "git_dir"))
            or current["snapshot"] != previous["snapshot"]
            or previous.get("head") != receipt.get("head")
            or previous["snapshot"]["digest"] != receipt.get("snapshot")
            or current.get("head") != integration.get("merged_sha")
            or git_value(project, "symbolic-ref", "-q", "HEAD") is not None):
        return None
    branch = before.get("workspace", {}).get("branch")
    if not branch or git_value(project, "rev-parse", "--verify", f"refs/heads/{branch}") != previous["head"]:
        return None
    review = next((item for item in before.get("reviews", []) if item.get("id") == receipt.get("id")), None)
    candidate = {"head": previous["head"], "digest": previous["snapshot"]["digest"]}
    try:
        validate_pass_review(review, candidate, receipt, contract()["loop"]["reviews"],
                             before.get("deliveries", {}), expected_shape="branch", expected_stage="candidate")
        validate_integrated_commit(project, integration, current, before["scope"], root)
        if not squash_inputs_match_commit(project, current, before["scope"], root):
            return None
    except ProtocolError:
        return None
    # commit_change refreshes only the candidate/revision and holder. Questions,
    # grants, gates, sealed waves, review inputs and interruption stay intact.
    return copy.deepcopy(before)


def commit_change(project, root, path, session, take_over, change):
    """Apply change(before) under the writer lock and return the record; None writes nothing.

    Update, ask and answer share this path: revision, candidate binding,
    validation, transitions and the agenda row are the same for every write.
    """
    with writer_lock(root / ".write-lock", root), writer_lock(path.with_name(".write-lock"), root):
        before = validate_record(read_json(path), project, root)
        updated = change(before)
        if updated is None:
            return before
        if before["status"] == "complete":
            raise ProtocolError("A completed run is immutable; create a new run")
        updated["revision"] += 1
        updated["updated_at"] = timestamp()
        updated["candidate"] = project_binding(project, before["scope"], root)
        validate_record(updated, project, root)
        validate_transitions(before, updated, project)
        agenda = plan_agenda(root, project, updated, session, take_over)
        atomic_write(path, updated, root)
        atomic_write(root / "agenda.json", agenda, root)
        return updated


AGENDA_SCHEMA = "daodan/agenda/v1"


def agenda_row(record, project, holder):
    """One line per task: where it is, who holds it, what it waits for."""
    waves = record.get("waves") or []
    phases = record.get("phases", {})
    phase = next((k for k, p in phases.items() if p.get("status") == "in_progress"), None)
    if phase is None:
        phase = next((k for k, p in reversed(list(phases.items())) if p.get("status") == "complete"), None)
    workspace = record.get("workspace") or {}
    return {
        "run_id": record["run_id"], "operation": record["operation"], "objective": record["objective"],
        "status": record["status"], "loop": "workspace" in record,
        "branch": workspace.get("branch") or git_value(project, "rev-parse", "--abbrev-ref", "HEAD"),
        "worktree": record["project"].get("worktree"), "head": git_value(project, "rev-parse", "HEAD"),
        "phase": phase,
        "waves": {"sealed": sum(1 for w in waves if w.get("status") == "sealed"), "total": len(waves)},
        "adr": (record.get("adr") or {}).get("proposed"),
        "review": next((f"{r['stage']} {r['tier']}" for r in reversed(record.get("reviews") or [])), None),
        "questions": sum(1 for q in record.get("questions") or [] if not q.get("answer")),
        "holder": holder, "updated_at": timestamp(),
    }


def plan_agenda(root, project, record, session, take_over):
    """Return the agenda with this run's row refreshed, refusing a held or shared task.

    The lock is the row: a task is written only by the session that holds it,
    until the user confirms that session is closed (`--take-over`). A branch
    belongs to one open loop task at a time. A completed run releases its row.
    """
    path = root / "agenda.json"
    agenda = read_json(path) if path.is_file() else {"schema": AGENDA_SCHEMA, "tasks": {}}
    if agenda.get("schema") != AGENDA_SCHEMA or not isinstance(agenda.get("tasks"), dict):
        raise ProtocolError("agenda.json is not a daodan/agenda/v1 document")
    tasks = agenda["tasks"]
    previous = tasks.get(record["run_id"], {})
    holder = previous.get("holder")
    if holder and holder.get("session") != session and not take_over:
        raise ProtocolError(
            f"Task {record['run_id']} is held by session {holder['session']} on {holder.get('host')} "
            f"since {holder.get('since')}; write as that session, or pass --take-over once the user "
            "confirms it is closed")
    if record["status"] == "complete":
        holder = None
    elif session and (not holder or holder.get("session") != session):
        holder = {"session": session, "host": platform.node(), "since": timestamp()}
    row = agenda_row(record, project, holder)
    if row["loop"] and row["status"] != "complete" and row["branch"]:
        for other_id, other in tasks.items():
            if (other_id != row["run_id"] and other.get("loop") and other.get("status") != "complete"
                    and other.get("branch") == row["branch"]):
                raise ProtocolError(f"Branch {row['branch']} already holds open task {other_id}; finish or resume it")
    tasks[row["run_id"]] = row
    return agenda


@contextmanager
def writer_lock(path, root):
    """One writer at a time on `path`, a lock file inside the project's record home."""
    no_links(path, root)
    if path.exists() and path.stat().st_nlink > 1:
        raise ProtocolError("Writer lock has external hardlinks; refuse to write")
    handle = path.open("a+b")
    locked = False
    try:
        if handle.seek(0, os.SEEK_END) == 0:
            handle.write(b"\0")
            handle.flush()
        deadline = time.monotonic() + LOCK_WAIT
        while not locked:
            handle.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except OSError as error:
                if error.errno not in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                    raise ProtocolError(f"Cannot lock the project's records: {error}") from error
                if time.monotonic() > deadline:
                    raise ProtocolError("Another writer holds the project's records; retry") from error
                time.sleep(0.05)
        yield
    finally:
        try:
            if locked:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def atomic_write(path, record, boundary):
    no_links(path, boundary)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    no_links(temporary, boundary)
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "show", "update", "validate", "resume", "snapshot", "agenda", "ask", "answer", "first-use", "bind-process"))
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--session", help="identity of the session doing the work; recorded as the task's holder")
    parser.add_argument("--take-over", action="store_true", help="take a task held by another session, after the user confirmed it is closed")
    parser.add_argument("--branch", help="agenda: only the task bound to this branch")
    parser.add_argument("--worktree", type=Path, help="agenda: tasks bound to this exact checkout path")
    parser.add_argument("--payload", type=Path)
    parser.add_argument("--expected-revision", type=int)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--current", action="store_true")
    parser.add_argument("--historical", action="store_true", help="show a legacy record without enforcing current execution gates")
    args = parser.parse_args(argv)
    try:
        if args.take_over and not args.session:
            raise ProtocolError("--take-over needs --session, the session taking the task")
        if args.command == "first-use":
            # Read-only and run before the first write: it resolves no record
            # home, so the home's dedication check never refuses the probe.
            print(json.dumps(first_use_probe(args.project), indent=2, sort_keys=True))
            return 0
        project, root = roots(args.project)
        payload = read_json(args.payload) if args.payload else {}
        if args.historical and args.command != "show":
            raise ProtocolError("--historical is available only for show")
        if args.command == "agenda":
            path = root / "agenda.json"
            agenda = read_json(path) if path.is_file() else {"schema": AGENDA_SCHEMA, "tasks": {}}
            rows = [row for row in agenda.get("tasks", {}).values()
                    if (not args.branch or row.get("branch") == args.branch)
                    and (not args.run_id or row.get("run_id") == args.run_id)
                    and (not args.worktree or row.get("worktree") == str(args.worktree.resolve()))]
            rows.sort(key=lambda row: row.get("updated_at") or "", reverse=True)
            output = {"schema": AGENDA_SCHEMA, "root": str(root), "tasks": rows}
        elif args.command == "init":
            for required in ("operation", "objective", "scope", "authorizations", "budget"):
                if required not in payload:
                    raise ProtocolError(f"Init requires {required}")
            if "questions" in payload:
                raise ProtocolError("Questions change only through ask and answer")
            identity = args.run_id or f"{args.command}-{uuid.uuid4().hex}"
            directory, path = run_paths(project, root, identity)
            binding = project_binding(project, payload["scope"], root)
            record = {**copy.deepcopy(payload), "schema": SCHEMA, "revision": 0, "run_id": identity,
                      "project": binding, "candidate": copy.deepcopy(binding), "output_root": str(root),
                      "status": "in_progress", "interruption": None, "created_at": timestamp(),
                      "updated_at": timestamp()}
            for key, default in (("phases", {}), ("plan", []), ("deliveries", {}), ("required_gates", []), ("gates", {})):
                record.setdefault(key, default)
            if "integration" in payload or any(
                    wave.get("status") == "sealed" and "plan_review" in wave
                    for wave in payload.get("waves", [])) or any(
                    task.get("status") in {"running", "green"}
                    for wave in payload.get("waves", []) for task in wave.get("tasks", [])):
                raise ProtocolError("Init accepts only pending work; resume or explicitly adopt executed work")
            validate_record(record, project, root)
            if "integration" in payload or any(
                    wave.get("status") == "sealed" or task.get("status") in {"running", "green", "committed"}
                    for wave in payload.get("waves", []) for task in wave.get("tasks", [])):
                raise ProtocolError("Init accepts only pending work; resume or explicitly adopt executed work")
            root.mkdir(parents=True, exist_ok=True)
            (root / ".daodan-root").touch(exist_ok=True)
            with writer_lock(root / ".write-lock", root):
                if directory.exists():
                    raise ProtocolError("Run already exists; choose another exact ID or resume")
                agenda = plan_agenda(root, project, record, args.session, args.take_over)
                directory.mkdir(parents=True, exist_ok=False)
                atomic_write(path, record, root)
                atomic_write(root / "agenda.json", agenda, root)
            output = record
        else:
            directory, path = run_paths(project, root, args.run_id)
            no_links(path, root)
            record = validate_record(read_json(path), project, root, historical=args.historical)
            if record["run_id"] != args.run_id:
                raise ProtocolError("Record does not match the exact run ID")
            if args.command == "show":
                output = {**record, "historical": True} if args.historical else record
            elif args.command == "snapshot":
                binding = project_binding(project, record["scope"], root)
                output = {"digest": binding["snapshot"]["digest"], "head": binding["head"],
                          "head_matches_snapshot": binding["head_matches_snapshot"]}
            elif args.command == "validate":
                if args.current and project_binding(project, record["scope"], root) != record.get("candidate", record["project"]):
                    raise ProtocolError("Current candidate snapshot or workspace identity changed")
                if args.result:
                    no_links(args.result.absolute(), directory)
                    validate_result(read_json(args.result), record)
                output = {"valid": True, "run_id": record["run_id"], "revision": record["revision"]}
            elif args.command == "resume":
                if payload.get("authorizations") != record["authorizations"]:
                    raise ProtocolError("Resume requires identical current authorizations")
                if "scope" in payload and payload["scope"] != record["scope"]:
                    raise ProtocolError("Resume scope changed; reassess in a new run")
                if project_binding(project, record["scope"], root) != record.get("candidate", record["project"]):
                    record = commit_change(project, root, path, args.session, args.take_over,
                                           lambda before: reconcile_interrupted_commit(before, project, root)
                                           or reconcile_interrupted_integration(before, project, root))
                    if project_binding(project, record["scope"], root) != record.get("candidate", record["project"]):
                        raise ProtocolError("Resume candidate snapshot or workspace changed; no matching interrupted commit or integration was found")
                with writer_lock(root / ".write-lock", root):
                    record = validate_record(read_json(path), project, root)
                    atomic_write(root / "agenda.json", plan_agenda(root, project, record, args.session,
                                                                   args.take_over), root)
                output = {**record,
                          "pending_phases": [k for k, p in record["phases"].items() if p["status"] not in {"complete", "skipped"}],
                          "pending_deliveries": [k for k, d in record["deliveries"].items() if d["status"] != "delivered"],
                          "pending_questions": [q for q in record.get("questions", []) if not q.get("answer")],
                          "waiting": waiting(record), "replan": stranded(record)}
            elif args.command == "bind-process":
                if args.expected_revision is None:
                    raise ProtocolError("Binding a process requires --expected-revision")

                def change(before):
                    if before["revision"] != args.expected_revision:
                        raise ProtocolError("Record revision changed; read the current record")
                    if "process" in before:
                        if before["process"] != payload:
                            raise ProtocolError("Work record already binds a different process")
                        return None
                    return {**before, "process": copy.deepcopy(payload), "process_required": True}

                final = commit_change(project, root, path, args.session, args.take_over, change)
                output = {"run_id": final["run_id"], "revision": final["revision"], "process": final["process"]}
            elif args.command == "ask":
                found = {}

                def change(before):
                    updated, found["id"] = ask_question(before, payload)
                    found["new"] = updated is not None
                    return updated
                final = commit_change(project, root, path, args.session, args.take_over, change)
                question = next(q for q in final["questions"] if q.get("id") == found["id"])
                output = {"question": found["id"], "revision": final["revision"],
                          "open": sum(1 for q in final["questions"] if is_open(q))}
                if not found["new"]:
                    output["existing"] = True
                    if not is_open(question):
                        output["answer"] = question["answer"]
                        if question.get("withdrawn"):
                            output["withdrawn"] = True
            elif args.command == "answer":
                wrote = {}

                def change(before):
                    updated = answer_question(before, payload)
                    wrote["yes"] = updated is not None
                    return updated
                final = commit_change(project, root, path, args.session, args.take_over, change)
                qid = payload["question"]
                output = {"question": qid, "revision": final["revision"],
                          "open": sum(1 for q in final["questions"] if is_open(q)), "unblocked": unblocked(final, qid)}
                if next(q for q in final["questions"] if q.get("id") == qid).get("withdrawn"):
                    output["replan"] = stranded(final)
                if not wrote["yes"]:
                    output["unchanged"] = True
            else:
                if args.expected_revision is None:
                    raise ProtocolError("Update requires --expected-revision")
                if set(payload) & IMMUTABLE:
                    raise ProtocolError("Patch cannot replace identity, scope, authorization or baseline")
                if "questions" in payload:
                    raise ProtocolError("Questions change only through ask and answer")

                def change(before):
                    if before["revision"] != args.expected_revision:
                        raise ProtocolError("Record revision changed; read the current record")
                    return merge(before, payload)
                output = commit_change(project, root, path, args.session, args.take_over, change)
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0
    except (ProtocolError, OSError, KeyError, TypeError) as error:
        print(f"Protocol error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
