"""Confined, resumable retention of a lifecycle run's owned files.

The helper checks ownership declarations, fingerprints, references and grants.
Semantic verification of the summary remains the coordinator's responsibility.
It never cleans arbitrary project paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import tempfile

ELIGIBLE = frozenset({"reproducible-output", "completed-output"})
CONTROL = frozenset({"work.json", "result.json", ".retention.lock"})


class RetentionError(ValueError):
    pass


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_hash(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _read(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RetentionError(f"Cannot read JSON record {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RetentionError(f"Expected an object: {path}")
    return value


def _no_link(path: Path) -> None:
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        raise RetentionError(f"Links are not retention targets: {path}")
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return
    if getattr(metadata, "st_file_attributes", 0) & 0x400:
        raise RetentionError(f"Reparse points are not retention targets: {path}")
    if path.is_file() and metadata.st_nlink != 1:
        raise RetentionError(f"Hardlinked file is not exclusively owned: {path}")


def _root(run: Path) -> tuple[Path, str]:
    run = Path(run).absolute()
    for ancestor in (run, *run.parents):
        _no_link(ancestor)
    if not run.is_dir():
        raise RetentionError("Run directory does not exist")
    run = run.resolve()
    work = _path(run, "work.json")
    record = _read(work)
    run_id = record.get("run_id")
    if not isinstance(run_id, str) or not run_id or run.name != run_id:
        raise RetentionError("work.json must identify this exact run directory")
    if record.get("schema") != "daodan/work/v1":
        raise RetentionError("Retention requires a protocol work record")
    project_value = record.get("project", {}).get("root")
    output_value = record.get("output_root")
    if not isinstance(project_value, str) or not isinstance(output_value, str):
        raise RetentionError("Run must declare its project and output root")
    project, output = Path(project_value), Path(output_value)
    if not project.is_absolute() or not output.is_absolute():
        raise RetentionError("Project and output bindings must be absolute")
    for bound in (project, output):
        for ancestor in (bound, *bound.parents):
            _no_link(ancestor)
    project, output = project.resolve(), output.resolve()
    if (not project.is_dir() or output == project or not output.is_relative_to(project)
            or run != output / "runs" / run_id):
        raise RetentionError("Run directory does not match its confined protocol binding")
    _path(output, ".daodan-root")
    return run, run_id


def _path(root: Path, relative: str, *, missing: bool = False) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise RetentionError(f"Invalid run-relative path: {relative!r}")
    posix, windows = PurePosixPath(relative), PureWindowsPath(relative)
    if (posix.as_posix() != relative or posix.is_absolute() or windows.is_absolute()
            or ".." in relative.split("/") or "." in relative.split("/")
            or any(part.endswith((" ", ".")) for part in relative.split("/"))):
        raise RetentionError(f"Path escapes the run or is ambiguous: {relative}")
    node = root
    for part in posix.parts:
        node = node / part
        _no_link(node)
    if not node.resolve().is_relative_to(root):
        raise RetentionError(f"Path escapes the run: {relative}")
    if not missing and not node.is_file():
        raise RetentionError(f"Expected an existing regular file: {relative}")
    return node


def _key(root: Path, relative: str) -> str:
    """One path identity for protected records, including Windows case aliases."""
    return os.path.normcase(str(_path(root, relative, missing=True).resolve()))


def _inside(root: Path, path: Path) -> tuple[Path, str]:
    path = Path(path)
    if not path.is_absolute():
        path = root / path
    try:
        relative = path.absolute().relative_to(root).as_posix()
    except ValueError as exc:
        raise RetentionError("Input record must be inside the run") from exc
    return _path(root, relative), relative


def _write(root: Path, relative: str, record: dict) -> None:
    target = _path(root, relative, missing=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".retention-", suffix=".json", dir=target.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _evidence(root: Path, report: dict) -> list[dict]:
    entries = report.get("retained_evidence")
    if not isinstance(entries, list) or not entries:
        raise RetentionError("A verified summary requires retained evidence")
    for entry in entries:
        if not isinstance(entry, dict):
            raise RetentionError("Invalid retained evidence entry")
        path = _path(root, entry.get("path"))
        if _hash(path) != entry.get("sha256"):
            raise RetentionError(f"Retained evidence changed: {entry.get('path')}")
    return entries


def make_plan(run: Path, manifest: Path, report: Path) -> dict:
    root, run_id = _root(run)
    manifest_path, manifest_name = _inside(root, manifest)
    report_path, report_name = _inside(root, report)
    inventory, summary = _read(manifest_path), _read(report_path)
    if inventory.get("schema") != "daodan/artifacts/v1" or inventory.get("run_id") != run_id:
        raise RetentionError("Artifact manifest must belong to this run")
    if summary.get("schema") != "daodan/evidence-summary/v1" or summary.get("run_id") != run_id:
        raise RetentionError("Summary must belong to this run")
    verification = summary.get("verification", {})
    if not summary.get("summary") or verification.get("status") != "verified" or not verification.get("by"):
        raise RetentionError("Summary has not been verified against its evidence")
    if summary.get("unresolved") != []:
        raise RetentionError("Resolve or retain outstanding evidence before retention")
    evidence = _evidence(root, summary)
    required = summary.get("required_artifacts")
    if not isinstance(required, list):
        raise RetentionError("Summary must enumerate required artifacts")
    protected = {_key(root, name) for name in
                 set(CONTROL) | {manifest_name, report_name} | set(required) | {e["path"] for e in evidence}}
    for relative in required:
        _path(root, relative)
    entries = inventory.get("artifacts")
    if not isinstance(entries, list):
        raise RetentionError("Manifest must enumerate artifacts")
    items, kept, seen = [], [], set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise RetentionError("Invalid artifact entry")
        relative = entry.get("path")
        path = _path(root, relative)
        identity = _key(root, relative)
        if identity in seen:
            raise RetentionError(f"Duplicate artifact path: {relative}")
        seen.add(identity)
        if identity in protected or relative.lower().startswith(("quarantine/", "retention-")):
            reason = "required evidence or run control"
        elif entry.get("owned_by") != run_id:
            reason = "ownership belongs elsewhere or is unknown"
        elif entry.get("classification") not in ELIGIBLE or entry.get("status") != "concluded":
            reason = "not a concluded disposable output"
        elif entry.get("classification") == "reproducible-output" and not entry.get("reproduce"):
            reason = "reproduction conditions missing"
        else:
            expected = entry.get("sha256")
            if not isinstance(expected, str) or _hash(path) != expected:
                raise RetentionError(f"Artifact changed since registration: {relative}")
            items.append({"path": relative, "sha256": expected, "size": path.stat().st_size,
                          "classification": entry["classification"]})
            continue
        kept.append({"path": relative, "reason": reason})
    plan = {"schema": "daodan/retention-plan/v1", "run_id": run_id,
            "manifest": {"path": manifest_name, "sha256": _hash(manifest_path)},
            "report": {"path": report_name, "sha256": _hash(report_path)},
            "retained_evidence": evidence, "items": items, "kept": kept,
            "potential_bytes_deleted": sum(item["size"] for item in items)}
    plan["plan_id"] = _json_hash(plan)
    return plan


def _grant(run_id: str, plan: dict, authorization: dict | None) -> dict:
    paths = {item["path"] for item in plan["items"]}
    if not isinstance(authorization, dict):
        raise RetentionError("Purge requires explicit user authorization")
    source = authorization.get("source", {})
    if (authorization.get("run_id") != run_id or authorization.get("operation") != "purge"
            or not isinstance(authorization.get("paths"), list)
            or not paths.issubset(set(authorization["paths"]))
            or source.get("kind") != "user" or not source.get("reference")):
        raise RetentionError("Purge authorization does not cover this exact run and paths")
    return authorization


def _validate_selection(root: Path, run_id: str, plan: dict) -> None:
    """Authorize targets against the original records, not a self-hashed plan."""
    manifest = _read(_path(root, plan["manifest"]["path"]))
    summary = _read(_path(root, plan["report"]["path"]))
    if (manifest.get("schema") != "daodan/artifacts/v1" or manifest.get("run_id") != run_id
            or summary.get("schema") != "daodan/evidence-summary/v1"
            or summary.get("run_id") != run_id
            or summary.get("unresolved") != []
            or summary.get("verification", {}).get("status") != "verified"):
        raise RetentionError("Original records do not authorize retention")
    required = summary.get("required_artifacts", [])
    for relative in required:
        _path(root, relative)
    protected_names = set(CONTROL) | set(required) | {
        plan["manifest"]["path"], plan["report"]["path"],
        *(entry["path"] for entry in _evidence(root, summary)),
    }
    protected = {_key(root, name) for name in protected_names}
    entries = manifest.get("artifacts", [])
    inventory = {entry.get("path"): entry for entry in entries}
    if len(inventory) != len(entries):
        raise RetentionError("Duplicate manifest paths")
    seen = set()
    for item in plan["items"]:
        relative = item["path"]
        _path(root, relative, missing=True)
        identity = _key(root, relative)
        original = inventory.get(relative, {})
        if (identity in seen or identity in protected
                or relative.lower().startswith(("quarantine/", "retention-"))
                or original.get("owned_by") != run_id
                or original.get("status") != "concluded"
                or original.get("classification") not in ELIGIBLE
                or item.get("classification") != original.get("classification")
                or item.get("sha256") != original.get("sha256")
                or not isinstance(item.get("size"), int) or item["size"] < 0
                or (original.get("classification") == "reproducible-output"
                    and not original.get("reproduce"))):
            raise RetentionError(f"Original manifest does not authorize this target: {relative}")
        seen.add(identity)


def apply_plan(run: Path, plan: dict, *, purge: bool = False, authorization: dict | None = None) -> dict:
    root, run_id = _root(run)
    identity = plan.get("plan_id")
    body = {key: value for key, value in plan.items() if key != "plan_id"}
    if plan.get("schema") != "daodan/retention-plan/v1" or plan.get("run_id") != run_id or identity != _json_hash(body):
        raise RetentionError("Retention plan is invalid or changed")
    for key in ("manifest", "report"):
        ref = plan[key]
        if _hash(_path(root, ref["path"])) != ref["sha256"]:
            raise RetentionError(f"{key} changed after planning")
    _validate_selection(root, run_id, plan)
    _evidence(root, {"retained_evidence": plan["retained_evidence"]})
    grant = _grant(run_id, plan, authorization) if purge else None
    mode = "purge" if purge else "quarantine"
    receipt_name = f"retention-{identity}.json"
    lock = _path(root, ".retention.lock", missing=True)
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RetentionError("Retention is locked; verify the owning process before recovering a stale lock") from exc
    try:
        os.close(descriptor)
        receipt_path = _path(root, receipt_name, missing=True)
        if receipt_path.exists():
            receipt = _read(receipt_path)
            if receipt.get("plan_id") != identity or receipt.get("mode") != mode:
                raise RetentionError("Existing receipt belongs to a different plan or mode")
        else:
            receipt = {"schema": "daodan/retention-receipt/v1", "run_id": run_id,
                       "plan_id": identity, "mode": mode, "authorization": grant,
                       "entries": {}, "bytes_deleted": 0, "bytes_moved": 0}
        # Preflight every target before mutating any one of them.
        for item in plan["items"]:
            source = _path(root, item["path"], missing=True)
            previous = receipt["entries"].get(item["path"])
            if source.exists():
                if previous and previous["state"] == "applied":
                    raise RetentionError(f"New file occupies an already retained path: {item['path']}")
                if _hash(source) != item["sha256"] or source.stat().st_size != item["size"]:
                    raise RetentionError(f"Artifact changed after planning: {item['path']}")
            elif not previous:
                raise RetentionError(f"Missing target without a recorded operation: {item['path']}")
            if not purge:
                target = _path(root, f"quarantine/{identity}/{item['path']}", missing=True)
                if target.exists() and (source.exists() or _hash(target) != item["sha256"]):
                    raise RetentionError(f"Quarantine collision: {item['path']}")
                if not source.exists() and not target.exists():
                    raise RetentionError(f"Missing quarantined artifact: {item['path']}")
        for item in plan["items"]:
            relative = item["path"]
            previous = receipt["entries"].get(relative)
            if previous and previous["state"] == "applied":
                continue
            receipt["entries"][relative] = {**item, "state": "prepared"}
            _write(root, receipt_name, receipt)
            source = _path(root, relative, missing=True)
            if source.exists():
                if _hash(source) != item["sha256"]:
                    raise RetentionError(f"Target changed during apply: {relative}")
                if purge:
                    source.unlink()
                else:
                    target = _path(root, f"quarantine/{identity}/{relative}", missing=True)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if target.exists():
                        raise RetentionError(f"Quarantine collision: {relative}")
                    os.rename(source, target)
            receipt["entries"][relative]["state"] = "applied"
            receipt["bytes_deleted"] = sum(e["size"] for e in receipt["entries"].values()
                                           if e["state"] == "applied") if purge else 0
            receipt["bytes_moved"] = sum(e["size"] for e in receipt["entries"].values()
                                         if e["state"] == "applied") if not purge else 0
            _write(root, receipt_name, receipt)
        _write(root, receipt_name, receipt)
        return receipt
    finally:
        lock.unlink(missing_ok=True)


def save_plan(run: Path, relative: str, plan: dict) -> None:
    """Create a plan without replacing any existing run artifact."""
    root, _ = _root(run)
    target = _path(root, relative, missing=True)
    summary = _read(_path(root, plan["report"]["path"]))
    protected = {_key(root, name) for name in
                 set(CONTROL) | {plan["manifest"]["path"], plan["report"]["path"]}
                 | set(summary["required_artifacts"])
                 | {entry["path"] for entry in plan["retained_evidence"]}}
    if (_key(root, relative) in protected
            or not PurePosixPath(relative).name.startswith("retention-plan")
            or PurePosixPath(relative).suffix != ".json"):
        raise RetentionError("Plan output must be a dedicated unoccupied retention-plan JSON file")
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        stream = target.open("x", encoding="utf-8", newline="\n")
    except FileExistsError as exc:
        raise RetentionError("Plan output already exists; choose another dedicated filename") from exc
    try:
        with stream:
            json.dump(plan, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        target.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    planning = commands.add_parser("plan")
    planning.add_argument("--run", type=Path, required=True)
    planning.add_argument("--manifest", type=Path, required=True)
    planning.add_argument("--report", type=Path, required=True)
    planning.add_argument("--output", default="retention-plan.json")
    applying = commands.add_parser("apply")
    applying.add_argument("--run", type=Path, required=True)
    applying.add_argument("--plan", type=Path, required=True)
    applying.add_argument("--purge", action="store_true")
    applying.add_argument("--authorization", type=Path)
    args = parser.parse_args()
    try:
        root, _ = _root(args.run)
        if args.command == "plan":
            result = make_plan(root, args.manifest, args.report)
            save_plan(root, args.output, result)
        else:
            plan_path, _ = _inside(root, args.plan)
            authorization = None
            if args.authorization:
                grant_path, _ = _inside(root, args.authorization)
                authorization = _read(grant_path)
            result = apply_plan(root, _read(plan_path), purge=args.purge, authorization=authorization)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (RetentionError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Retention refused: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())

