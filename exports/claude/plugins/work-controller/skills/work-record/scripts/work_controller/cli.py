"""Bounded command-line interface for composition and durable execution."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

from .compose import compose_process
from .definition import dump_definition, load_definition, parse_definition
from .engine import Engine
from .errors import ProcessError, StateError
from .store import Store
from .util import atomic_write_text

_STATE_MUTATIONS = frozenset({
    "interview", "start", "claim", "drive", "start-attempt", "complete",
    "resume", "retry-attempt", "finish", "map-open", "ticket-add",
    "ticket-claim", "ticket-close",
})
_STORE_BOOTSTRAP = frozenset({"mcp", "console"})


def resolve_home(
    workspace: Path,
    explicit_home: Path | None = None,
    *,
    create: bool = False,
    require_store: bool = False,
) -> Path:
    """Resolve the shared record home without silently adopting legacy state."""
    if explicit_home is not None:
        home = explicit_home.resolve()
    else:
        import run_state

        try:
            project, record_root = run_state.roots(workspace)
            run_state.no_links(record_root / "processes", record_root)
            for name in ("process.db", "process.db-wal", "process.db-shm",
                         "brain.db", "brain.db-wal", "brain.db-shm"):
                run_state.no_links(record_root / "processes" / name, record_root)
        except run_state.ProtocolError as exc:
            raise StateError(str(exc)) from exc
        legacy_homes = sorted({
            base / name
            for base in (project, record_root.parent)
            for name in (".process-controller", ".deadly-brain")
            if (base / name).exists()
        })
        if legacy_homes:
            names = ", ".join(str(path) for path in legacy_homes)
            raise StateError(
                f"legacy process state requires an explicit home: {names}; "
                "pass --home PATH to select one store, or migrate it explicitly "
                "before using the shared .daodan/processes home"
            )
        home = record_root / "processes"
        if create:
            record_root.mkdir(parents=True, exist_ok=True)
            (record_root / ".daodan-root").touch(exist_ok=True)
    if require_store and not any((home / name).is_file() for name in ("process.db", "brain.db")):
        raise StateError(f"no process store at {home}; start a process first or pass --home PATH")
    return home


def prepare_home(args: argparse.Namespace) -> None:
    """Initialize state for mutations or interface bootstrap, never validation."""
    if args.command in {"validate", "compose"}:
        return
    mutating = args.command in _STATE_MUTATIONS or args.command in _STORE_BOOTSTRAP
    args.home = resolve_home(
        args.workspace, args.home, create=mutating, require_store=not mutating
    )


def emit(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def engine(args: argparse.Namespace) -> Engine:
    return Engine(args.home, args.workspace)


def write_definition(path: Path, source: str, *, force: bool = False) -> None:
    if path.exists() and not force and path.read_text(encoding="utf-8") != source:
        raise StateError(f"definition already exists with different content: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, source)


def composed(args: argparse.Namespace) -> dict[str, Any]:
    verify = shlex.split(args.verify) if args.verify else None
    return compose_process(
        args.objective,
        archetype=args.archetype,
        target=args.target,
        verify=verify,
        commit=args.commit,
    )


def interview(args: argparse.Namespace) -> dict[str, Any]:
    store = Store(args.home)
    try:
        current = store.interview(args.id)
        payload = current["payload"]
        if current["status"] == "complete":
            return {"id": args.id, "status": "complete", "definition": payload["definition"]}
    except StateError:
        payload = {}
    supplied = {
        "objective": args.objective,
        "archetype": args.archetype,
        "target": args.target,
        "verify": args.verify,
        "commit": args.commit or None,
    }
    payload.update({key: value for key, value in supplied.items() if value is not None})
    if not payload.get("objective"):
        payload["objective"] = input("Obiettivo del processo? ").strip()
        store.save_interview(args.id, payload, "in_progress")
    if not payload.get("archetype"):
        payload["archetype"] = input("Archetipo [analysis/change] (analysis)? ").strip() or "analysis"
        store.save_interview(args.id, payload, "in_progress")
    if payload["archetype"] == "change" and not payload.get("target"):
        payload["target"] = input("File o artefatto da modificare? ").strip()
        store.save_interview(args.id, payload, "in_progress")
    if payload["archetype"] == "change" and not payload.get("verify"):
        payload["verify"] = input("Comando di verifica (argv, senza shell)? ").strip()
        store.save_interview(args.id, payload, "in_progress")
    data = compose_process(
        payload["objective"],
        archetype=payload["archetype"],
        target=payload.get("target"),
        verify=shlex.split(payload["verify"]) if payload.get("verify") else None,
        commit=bool(payload.get("commit")),
    )
    source = dump_definition(data)
    parse_definition(source)
    output = args.output or args.workspace / "work-controller.yaml"
    write_definition(output, source, force=args.force)
    payload["definition"] = str(output.resolve())
    store.save_interview(args.id, payload, "complete")
    return {
        "id": args.id,
        "status": "complete",
        "definition": payload["definition"],
        "digest": parse_definition(source).digest,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="work-controller", description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument(
        "--home", type=Path, default=None,
        help="explicit store override; default is the main checkout's .daodan/processes",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="validate YAML without creating a run")
    validate.add_argument("definition", type=Path)

    for name in ("compose", "interview"):
        sub = commands.add_parser(name)
        sub.add_argument("--objective")
        sub.add_argument("--archetype", choices=("analysis", "change"))
        sub.add_argument("--target")
        sub.add_argument("--verify", help="verification argv as one quoted command line")
        sub.add_argument("--commit", action="store_true")
        sub.add_argument("--output", type=Path)
        sub.add_argument("--force", action="store_true")
        if name == "compose":
            sub.set_defaults(archetype="analysis")
        else:
            sub.add_argument("--id", required=True)

    start = commands.add_parser("start")
    start.add_argument("definition", type=Path)
    start.add_argument("--run-id")
    start.add_argument("--grant", action="append", default=[], choices=("shell", "commit"))

    for name in ("frontier", "status", "resume", "finish"):
        sub = commands.add_parser(name)
        sub.add_argument("run_id")

    for name in ("claim", "drive"):
        sub = commands.add_parser(name)
        sub.add_argument("run_id")
        sub.add_argument("--holder", required=True)
        if name == "drive":
            sub.add_argument("--max-steps", type=int, default=100)

    for name in ("packet", "start-attempt", "complete"):
        sub = commands.add_parser(name)
        sub.add_argument("attempt_id")
        sub.add_argument("--holder", required=True)
        if name == "complete":
            sub.add_argument("--event-id", required=True)
            sub.add_argument("--verdict", required=True, choices=("pass", "fail"))
            sub.add_argument("--error")

    retry = commands.add_parser("retry-attempt")
    retry.add_argument("attempt_id")
    retry.add_argument("--confirm-stopped", action="store_true")
    retry.add_argument("--commit-sha")
    retry.add_argument("--discard-commit-outcome", action="store_true")

    supervise = commands.add_parser("supervise")
    supervise.add_argument("attempt_id")

    events = commands.add_parser("events")
    events.add_argument("run_id")
    events.add_argument("--after", type=int, default=0)
    events.add_argument("--limit", type=int, default=20)

    map_open = commands.add_parser("map-open")
    map_open.add_argument("--id", required=True)
    map_open.add_argument("--destination", required=True)

    ticket_add = commands.add_parser("ticket-add")
    ticket_add.add_argument("map_id")
    ticket_add.add_argument("--id", required=True)
    ticket_add.add_argument("--kind", required=True, choices=("decision", "research", "execution"))
    ticket_add.add_argument("--summary", required=True)
    ticket_add.add_argument("--blocked-by", action="append", default=[])
    ticket_add.add_argument("--run-id")

    for name in ("map-next", "map-status"):
        sub = commands.add_parser(name)
        sub.add_argument("map_id")

    ticket_claim = commands.add_parser("ticket-claim")
    ticket_claim.add_argument("map_id")
    ticket_claim.add_argument("ticket_id")
    ticket_claim.add_argument("--holder", required=True)

    ticket_close = commands.add_parser("ticket-close")
    ticket_close.add_argument("map_id")
    ticket_close.add_argument("ticket_id")
    ticket_close.add_argument("--holder", required=True)
    ticket_close.add_argument("--source", required=True, choices=("user", "evidence", "run"))
    ticket_close.add_argument("--resolution")
    ticket_close.add_argument("--run-id")

    map_events = commands.add_parser("map-events")
    map_events.add_argument("map_id")
    map_events.add_argument("--after", type=int, default=0)
    map_events.add_argument("--limit", type=int, default=20)

    console = commands.add_parser("console")
    console.add_argument("--host", default="127.0.0.1")
    console.add_argument("--port", type=int, default=8765)

    commands.add_parser("mcp")
    return parser


def run(args: argparse.Namespace) -> Any:
    if args.command == "validate":
        definition = load_definition(args.definition)
        return {
            "valid": True,
            "id": definition.data["id"],
            "digest": definition.digest,
            "jobs": len(definition.order),
            "order": list(definition.order),
        }
    if args.command == "compose":
        source = dump_definition(composed(args))
        definition = parse_definition(source)
        output = args.output or args.workspace / "work-controller.yaml"
        write_definition(output, source, force=args.force)
        return {"definition": str(output.resolve()), "digest": definition.digest, "jobs": len(definition.order)}
    if args.command == "interview":
        return interview(args)
    if args.command == "start":
        return engine(args).start(args.definition, grants=args.grant, run_id=args.run_id)
    if args.command == "frontier":
        return {"jobs": engine(args).frontier(args.run_id)}
    if args.command == "claim":
        return {"packet": engine(args).claim(args.run_id, args.holder)}
    if args.command == "packet":
        return engine(args).packet(args.attempt_id, args.holder)
    if args.command == "start-attempt":
        return engine(args).start_attempt(args.attempt_id, args.holder)
    if args.command == "complete":
        return engine(args).complete(
            args.attempt_id,
            args.holder,
            args.event_id,
            args.verdict,
            error=args.error,
        )
    if args.command == "drive":
        return engine(args).drive(args.run_id, args.holder, max_steps=args.max_steps)
    if args.command == "resume":
        return engine(args).resume(args.run_id)
    if args.command == "retry-attempt":
        return engine(args).resolve_unknown(
            args.attempt_id,
            confirm_stopped=args.confirm_stopped,
            commit_sha=args.commit_sha,
            discard_commit_outcome=args.discard_commit_outcome,
        )
    if args.command == "supervise":
        return engine(args).supervise(args.attempt_id)
    if args.command == "finish":
        return engine(args).finish(args.run_id)
    if args.command == "status":
        return engine(args).status(args.run_id)
    if args.command == "events":
        return {"events": engine(args).events(args.run_id, after=args.after, limit=args.limit)}
    if args.command == "map-open":
        return Store(args.home).map_open(args.id, args.destination)
    if args.command == "ticket-add":
        return Store(args.home).ticket_add(
            args.map_id, args.id, args.kind, args.summary,
            blocked_by=args.blocked_by, run_id=args.run_id,
        )
    if args.command == "map-next":
        return {"ticket": Store(args.home).map_next(args.map_id)}
    if args.command == "map-status":
        return Store(args.home).map_status(args.map_id)
    if args.command == "ticket-claim":
        return Store(args.home).ticket_claim(args.map_id, args.ticket_id, args.holder)
    if args.command == "ticket-close":
        return Store(args.home).ticket_close(
            args.map_id, args.ticket_id, args.holder,
            source=args.source, resolution=args.resolution, run_id=args.run_id,
        )
    if args.command == "map-events":
        return {"events": Store(args.home).map_events(args.map_id, after=args.after, limit=args.limit)}
    if args.command == "console":
        from .web import serve

        serve(args.home, args.workspace, host=args.host, port=args.port)
        return {"status": "stopped"}
    if args.command == "mcp":
        from .mcp import run_stdio

        run_stdio(args.home, args.workspace)
        return None
    raise StateError(f"unsupported command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.workspace = args.workspace.resolve()
    try:
        prepare_home(args)
        result = run(args)
        if args.command != "mcp":
            emit(result)
        return 0
    except (ProcessError, OSError, ValueError) as exc:
        print(f"work-controller: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
