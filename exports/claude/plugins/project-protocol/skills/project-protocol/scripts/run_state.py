"""Versioned, snapshot-bound operational work records. Standard library only."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib
import uuid

SCHEMA = "daodan/work/v1"
RUN_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,95}$")
CONTRACT = Path(__file__).resolve().parents[3] / "contracts/work.toml"
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
        if item.is_symlink() or (hasattr(item, "is_junction") and item.is_junction()):
            raise ProtocolError(f"Link is not an owned writable path: {item.name}")
        if item == boundary:
            break


def roots(project, output):
    project = Path(project).resolve()
    if not project.is_dir():
        raise ProtocolError("Project root must be a directory")
    selected = Path(output) if output else Path(".daodan")
    if ".." in selected.parts:
        raise ProtocolError("Output root contains traversal")
    raw = selected if selected.is_absolute() else project / selected
    no_links(raw, project)
    root = raw.resolve()
    if root == project or not root.is_relative_to(project):
        raise ProtocolError("Output root must be strictly inside the project")
    if root.exists() and not (root / ".daodan-root").is_file() and any(root.iterdir()):
        raise ProtocolError("Output root must be dedicated and carry .daodan-root")
    no_links(root / ".daodan-root", project)
    return project, root


def run_paths(project, root, run_id):
    if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
        raise ProtocolError("Invalid exact run ID")
    directory = root / "runs" / run_id
    no_links(directory, project)
    return directory, directory / "work.json"


def git_value(project, *args):
    result = subprocess.run(["git", "-C", str(project), *args], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def head_matches_inputs(project, head, paths, entries, excluded_path):
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
            if inputs[name]["sha256"] != digest.hexdigest() or inputs[name]["bytes"] != size:
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


def validate_record(record, project=None, root=None, current=False):
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
    if record["operation"] not in {"assess", "repair", "change", "verify", "consolidate"}:
        raise ProtocolError("Unknown lifecycle operation")
    if record["status"] not in rules["fields"]["status"]["values"]:
        raise ProtocolError("Invalid run status")
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
                if not isinstance(item["output"], str) or not item["output"].strip():
                    raise ProtocolError("Delivery report must be a nonempty relative path")
                output = Path(item["output"])
                if output.is_absolute() or ".." in output.parts:
                    raise ProtocolError("Delivery output must stay inside its owned run")
                if (any(":" in part for part in output.parts)
                        or output.as_posix().rstrip(" .").casefold() in {"work.json", "result.json", ".write-lock"}):
                    raise ProtocolError("A coordinator record or lock is not a worker report")
                if project is not None and item["status"] == "delivered":
                    report = root / "runs" / record["run_id"] / output
                    no_links(report, project)
                    if not report.is_file():
                        raise ProtocolError(f"Delivered report is missing: {identity}")
                    directory = root / "runs" / record["run_id"]
                    if any(reserved.exists() and report.samefile(reserved)
                           for reserved in (directory / name for name in ("work.json", "result.json", ".write-lock"))):
                        raise ProtocolError("A coordinator record or lock is not a worker report")
    if project is not None:
        if record["project"].get("root") != str(project):
            raise ProtocolError("Project identity does not match this invocation")
        if record.get("output_root") != str(root):
            raise ProtocolError("Output root does not match the recorded identity")
    if record["status"] == "complete":
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
        if current and project is not None and project_binding(project, record["scope"], root) != candidate:
            raise ProtocolError("Current candidate snapshot differs from the completed record")
    return record


def validate_transitions(old, new):
    rules = contract()
    if old["status"] == "complete" and new["status"] != "complete":
        raise ProtocolError("A complete run cannot be reopened")
    if new["required_gates"][:len(old["required_gates"])] != old["required_gates"]:
        raise ProtocolError("Required gates are append-only; a check cannot be removed or weakened")
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
    path = CONTRACT.with_name("project-result.toml")
    with path.open("rb") as handle:
        rules = tomllib.load(handle)
    missing = sorted(set(rules["required"]) - set(result))
    if missing:
        raise ProtocolError("Missing result fields: " + ", ".join(missing))
    if result["schema"] != rules["record_schema"]:
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


@contextmanager
def writer_lock(directory, project):
    path = directory / ".write-lock"
    no_links(path, project)
    if path.exists() and path.stat().st_nlink > 1:
        raise ProtocolError("Run lock has external hardlinks; refuse to write")
    handle = path.open("a+b")
    locked = False
    try:
        if handle.seek(0, os.SEEK_END) == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        locked = True
        yield
    except OSError as error:
        raise ProtocolError("Run writer is busy or unavailable; retry with the current revision") from error
    finally:
        if locked:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def atomic_write(path, record, project):
    no_links(path, project)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    no_links(temporary, project)
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
    parser.add_argument("command", choices=("init", "show", "update", "validate", "resume", "snapshot"))
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--out")
    parser.add_argument("--payload", type=Path)
    parser.add_argument("--expected-revision", type=int)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--current", action="store_true")
    args = parser.parse_args(argv)
    try:
        project, root = roots(args.project, args.out)
        payload = read_json(args.payload) if args.payload else {}
        if args.command == "snapshot":
            output = project_binding(project, payload.get("scope", {}), root)
        elif args.command == "init":
            for required in ("operation", "objective", "scope", "authorizations", "budget"):
                if required not in payload:
                    raise ProtocolError(f"Init requires {required}")
            identity = args.run_id or f"{args.command}-{uuid.uuid4().hex}"
            directory, path = run_paths(project, root, identity)
            binding = project_binding(project, payload["scope"], root)
            record = {**copy.deepcopy(payload), "schema": SCHEMA, "revision": 0, "run_id": identity,
                      "project": binding, "candidate": copy.deepcopy(binding), "output_root": str(root),
                      "status": "in_progress", "interruption": None, "created_at": timestamp(),
                      "updated_at": timestamp()}
            for key, default in (("phases", {}), ("plan", []), ("deliveries", {}), ("required_gates", []), ("gates", {})):
                record.setdefault(key, default)
            validate_record(record, project, root)
            if directory.exists():
                raise ProtocolError("Run already exists; choose another exact ID or resume")
            root.mkdir(parents=True, exist_ok=True)
            (root / ".daodan-root").touch(exist_ok=True)
            directory.mkdir(parents=True, exist_ok=False)
            atomic_write(path, record, project)
            output = record
        else:
            directory, path = run_paths(project, root, args.run_id)
            no_links(path, project)
            record = validate_record(read_json(path), project, root)
            if record["run_id"] != args.run_id:
                raise ProtocolError("Record does not match the exact run ID")
            if args.command == "show":
                output = record
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
                    raise ProtocolError("Resume candidate snapshot or workspace identity changed")
                output = {**record,
                          "pending_phases": [k for k, p in record["phases"].items() if p["status"] not in {"complete", "skipped"}],
                          "pending_deliveries": [k for k, d in record["deliveries"].items() if d["status"] != "delivered"]}
            else:
                if args.expected_revision is None:
                    raise ProtocolError("Update requires --expected-revision")
                if set(payload) & IMMUTABLE:
                    raise ProtocolError("Patch cannot replace identity, scope, authorization or baseline")
                with writer_lock(directory, project):
                    before = validate_record(read_json(path), project, root)
                    if before["revision"] != args.expected_revision:
                        raise ProtocolError("Record revision changed; read the current record")
                    if before["status"] == "complete":
                        raise ProtocolError("A completed run is immutable; create a new run")
                    updated = merge(before, payload)
                    updated["revision"] += 1
                    updated["updated_at"] = timestamp()
                    updated["candidate"] = project_binding(project, before["scope"], root)
                    validate_record(updated, project, root, current=True)
                    validate_transitions(before, updated)
                    atomic_write(path, updated, project)
                    output = updated
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0
    except (ProtocolError, OSError, KeyError, TypeError) as error:
        print(f"Protocol error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
