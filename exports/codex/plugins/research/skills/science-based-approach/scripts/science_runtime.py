"""Science Mode, routing checkpoints and scientific archive command interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

from science_storage import (
    ScienceError, append_check as _append_check, atomic, checkout_root, digest, encoded, no_links, now,
    project_home, publish as _publish, read_json, records, render_views, revision, select,
    state_root, text_value, timestamp, unpublished, writing,
)


def validate_mode(value: dict) -> None:
    if value.get("schema") != "daodan/science-mode/v1" or type(value.get("enabled")) is not bool:
        raise ScienceError("Science Mode configuration-error: invalid schema or enabled value")
    revision(value.get("revision"), 1)
    for field in ("updated_at", "source"):
        text_value(value.get(field), field)
    timestamp(value["updated_at"], "updated_at")


def mode(home: Path) -> dict:
    path = state_root(home) / "science-mode.json"
    no_links(path, home)
    if not path.exists():
        return {"status": "ok", "enabled": True, "revision": 0, "origin": "default", "project": str(home)}
    value = read_json(path, home)
    validate_mode(value)
    return {**value, "status": "ok", "origin": "explicit", "project": str(home)}


def set_mode(home: Path, enabled: bool, expected: int, source: str) -> dict:
    revision(expected)
    text_value(source, "source")
    # A read-only, already-effective request must not create implicit state.
    current = mode(home)
    if current["revision"] != expected:
        raise ScienceError("Concurrent mode revision; reread before changing Science Mode")
    if current["enabled"] == enabled:
        return {**current, "changed": False}
    with writing(home):
        current = mode(home)
        if current["revision"] != expected:
            raise ScienceError("Concurrent mode revision; reread before changing Science Mode")
        number = expected + 1
        receipt_path = state_root(home) / "science-mode-history" / f"r{number:04d}.json"
        no_links(receipt_path, home)
        value = {"schema": "daodan/science-mode/v1", "enabled": enabled, "revision": number, "updated_at": now(), "source": source}
        if receipt_path.exists():
            previous = read_json(receipt_path, home)
            validate_mode(previous)
            if previous.get("enabled") != enabled or previous.get("source") != source or previous.get("revision") != number:
                raise ScienceError("Unpublished mode change is preserved; reconcile before another mutation")
            value = previous
        atomic(receipt_path, encoded(value), home, immutable=True)
        atomic(state_root(home) / "science-mode.json", encoded(value), home)
        return {**mode(home), "changed": True, "receipt": str(receipt_path)}


def automatic_mode(home: Path, automatic: bool) -> dict:
    try:
        value = mode(home)
    except ScienceError as error:
        if automatic:
            return {"status": "configuration-error", "reason": str(error)}
        return {"status": "explicit", "enabled": False, "revision": "configuration-error"}
    if automatic and not value["enabled"]:
        return {"status": "disabled", "reason": "Science Mode is OFF", "revision": value["revision"]}
    return value


def publish(home: Path, payload: dict) -> dict:
    return archive_operation(home, payload, "publish")


def append_check(home: Path, payload: dict) -> dict:
    return archive_operation(home, payload, "check")


def archive_operation(home: Path, payload: dict, operation: str) -> dict:
    automatic = payload.get("automatic", False)
    if type(automatic) is not bool:
        raise ScienceError("automatic must be boolean")
    shared_home = project_home(home)
    state = automatic_mode(shared_home, automatic)
    if state["status"] in ("disabled", "configuration-error"):
        return state
    def guard() -> dict | None:
        latest = automatic_mode(shared_home, automatic)
        return latest if latest["status"] in ("disabled", "configuration-error") else None
    return (_publish if operation == "publish" else _append_check)(home, payload, guard)


def read_checkpoint(path: Path, home: Path, key: str) -> dict | None:
    if not path.exists():
        return None
    value = read_json(path, home)
    if value.get("schema") != "daodan/science-checkpoint/v1" or value.get("key") != key or value.get("status") not in ("running", "not-applicable", "reused", "updated", "created", "partial", "unavailable"):
        raise ScienceError("Invalid stored checkpoint; preserve it and recover the original run")
    return value


def checkpoint(home: Path, payload: dict, record: bool = False) -> dict:
    automatic = payload.get("automatic", True)
    if type(automatic) is not bool:
        raise ScienceError("automatic must be boolean")
    state = automatic_mode(home, automatic)
    if state["status"] in ("disabled", "configuration-error"):
        return state
    task_id = text_value(payload.get("task_id"), "task_id")
    phase = text_value(payload.get("phase"), "phase")
    context = payload.get("context")
    if not isinstance(context, dict):
        raise ScienceError("context must be a JSON object with relevant intent and versions")
    # The semantic caller identifies owned research maintenance; keywords do not.
    if type(payload.get("research_maintenance", False)) is not bool:
        raise ScienceError("research_maintenance must be boolean")
    if payload.get("research_maintenance", False):
        return {"status": "not-applicable", "reason": "Research maintenance does not recursively trigger research"}
    key = digest(encoded({"task_id": task_id, "phase": phase, "context": context,
                          "mode_revision": state["revision"], "automatic": automatic}))
    path = state_root(home) / "science-checkpoints" / f"{key}.json"
    no_links(path, home)
    existing = read_checkpoint(path, home, key)
    if not record:
        return {"status": "duplicate" if existing else "needed", "key": key, "checkpoint": existing}
    with writing(home):
        latest = automatic_mode(home, automatic)
        if latest["status"] in ("disabled", "configuration-error"):
            return latest
        if latest["revision"] != state["revision"]:
            raise ScienceError("Science Mode changed; repeat checkpoint with the current mode")
        existing = read_checkpoint(path, home, key)
        outcome = payload.get("outcome")
        if outcome is None:
            if existing:
                return {"status": "duplicate", "key": key, "checkpoint": existing}
            value = {"schema": "daodan/science-checkpoint/v1", "key": key, "status": "running",
                     "task_id": task_id, "phase": phase, "context_digest": digest(encoded(context)),
                     "mode_revision": state["revision"], "created_at": now()}
        else:
            if outcome not in ("not-applicable", "reused", "updated", "created", "partial", "unavailable"):
                raise ScienceError("Invalid checkpoint outcome")
            if not existing:
                raise ScienceError("Claim the checkpoint before recording its outcome")
            if existing["status"] != "running":
                return {"status": "duplicate", "key": key, "checkpoint": existing}
            refs = payload.get("references", [])
            if not isinstance(refs, list) or any(not isinstance(item, str) for item in refs):
                raise ScienceError("references must be an array of strings")
            value = {**existing, "status": outcome, "reason": text_value(payload.get("reason"), "reason"),
                     "references": refs, "finished_at": now()}
        atomic(path, encoded(value), home)
        return {"status": "claimed" if outcome is None else "recorded", "key": key, "checkpoint": value}


def hook(payload: dict) -> dict | None:
    event = payload.get("hook_event_name")
    if event not in ("SessionStart", "UserPromptSubmit"):
        raise ScienceError("Unsupported science hook event")
    project = text_value(payload.get("cwd"), "cwd")
    home = project_home(project)
    state = automatic_mode(home, True)
    if state["status"] == "disabled":
        return None
    if state["status"] == "configuration-error":
        context = "Science Mode configuration-error. Suspend automatic scientific work and report the local configuration error without altering its bytes. Explicit research commands remain available. " + state["reason"]
    else:
        context = (
            "Science Mode is ON. Before substantive brainstorming, specifications, ADR/FRD or problem-solving, "
            "load the research plugin's science-based-approach skill and apply its checkpoint using the existing task, phase and relevant context. "
            "Consult relevant docs/research evidence when useful; choose reuse, refresh, new research or not-applicable. "
            "Deduplicate through the method; do not start a second coordinator. Reread mode before automatic work. "
            "Research maintenance itself does not trigger another checkpoint. Preserve the task's permissions."
        )
    return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": context}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    mode_parser = commands.add_parser("mode")
    mode_parser.add_argument("value", nargs="?", choices=("on", "off"))
    mode_parser.add_argument("--project", required=True)
    mode_parser.add_argument("--expected-revision", type=int)
    mode_parser.add_argument("--source")
    commands.add_parser("hook")
    for command in ("checkpoint", "publish", "check"):
        child = commands.add_parser(command)
        child.add_argument("--project", required=True)
        child.add_argument("--payload", required=True)
        if command == "checkpoint":
            child.add_argument("--record", action="store_true")
    for command in ("list", "select", "reindex"):
        child = commands.add_parser(command)
        child.add_argument("--project", required=True)
        if command == "select":
            child.add_argument("selector")
    args = parser.parse_args(argv)
    try:
        if args.command == "hook":
            payload = json.loads(sys.stdin.read(1_048_577))
            if not isinstance(payload, dict):
                raise ScienceError("Hook input must be a JSON object")
            result = hook(payload)
        else:
            home = project_home(args.project) if args.command in ("mode", "checkpoint") else checkout_root(args.project)
            if args.command == "mode":
                if args.value is None:
                    result = mode(home)
                elif args.expected_revision is None or not args.source:
                    raise ScienceError("Mode changes require --expected-revision and --source")
                else:
                    result = set_mode(home, args.value == "on", args.expected_revision, args.source)
            elif args.command in ("publish", "check", "checkpoint"):
                payload_path = Path(args.payload).resolve()
                payload = read_json(payload_path, payload_path.parent)
                result = {"checkpoint": lambda: checkpoint(home, payload, args.record),
                          "publish": lambda: publish(home, payload),
                          "check": lambda: append_check(home, payload)}[args.command]()
            elif args.command == "list":
                result = {"research": records(home), "unpublished": unpublished(home)}
            elif args.command == "select":
                result = {"research": select(home, args.selector)}
            else:
                with writing(home):
                    result = {"research": render_views(home), "unpublished": unpublished(home), "status": "rebuilt"}
        if result is not None:
            print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ScienceError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "configuration-error" if args.command == "mode" and args.value is None else "error", "reason": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
