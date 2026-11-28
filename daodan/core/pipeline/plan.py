"""The plan (spec 8.4): which adapter runs on which files, and what each needs first, as plain data.

`plan(rows)` takes `(path, {"language": ...})` pairs, `stored` reads them from a store (every executor takes its rows
from it); a row may carry the file's `status` and, when it stands for a group of files, their number (`files`).
It reads the adapters' own declarations (`engine_pass.ENGINES`, which the stages are built from, and
`dynamic.observers()`), and gives `{"nodes": [...], "gaps": [...]}`. It states no fact about
the project, only choices; the steps run the nodes it gives and nothing else (`snapshot.write_reading`,
`engine_pass.pass_plan`, `dynamic.run`).

A node is `{id, step, adapter, [version], on, container, needs}`: `step` is the id of the step that runs it and `id` is
`<step>:<adapter>` (`read_code:<language>`, `read_code:file-level` for the files with no language,
`link_calls:<analyzer name>`, `run_and_observe:<observer entry>`); `on` is
`{"languages", "files"}` (counts, never paths), and for a resolver also `unit_kinds`; `container` is whether it runs
in Daodan's container; `needs` are the ids of the nodes it waits for. A gap is `{kind, language, files, detail}`:
`no-analyzer` (a language no analyzer lists) or `no-observer` (a language with a resolver and no observer).

A node whose need failed does not start, and says which (`blocked`), per language: a resolver needs the parser of
each of its languages, an observer the resolver of each of its.

`current(manifest)` is the one plan for the app, MCP and the command line: the steps with their state, the policy, the
actions with theirs and the gaps, computed at each call from the store, the journal and `egress`; it is never saved.
"""
from __future__ import annotations

import collections

FILE_LEVEL = "file-level"  # the adapter of the files with no language: their entry holds no reading
# The steps that run the nodes, by their ids: the reading (`snapshot.write_reading`), `engine_pass.STEP`, `dynamic.STEP`.
READ_CODE, LINK_CALLS, RUN_AND_OBSERVE = "read_code", "link_calls", "run_and_observe"


def node_of(row: dict) -> str:
    """The reading's node a file belongs to, from its inventory row."""
    return f"{READ_CODE}:{row.get('language') or FILE_LEVEL}"


def coverage(connection) -> list[tuple[str, dict]]:
    """The snapshot's files as grouped rows: per language and parse status, how many (`sem_coverage`)."""
    return [("", {"language": language, "status": status, "files": count}) for language, status, count in
            connection.execute("SELECT language, status, COUNT(*) FROM sem_coverage GROUP BY language, status")]


def stored(store) -> list[tuple[str, dict]]:
    """The rows of a snapshot, one source for every step: the parse status of each language once the snapshot is read
    (`coverage`), else its inventory, else, for a store that has none (JSON, a store written before it), its files'
    headers' languages."""
    connection = getattr(store, "connection", None)
    if connection is not None and connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='sem_coverage'").fetchone():
        rows = coverage(connection)
        if rows:
            return rows
    return list(store.iter_listed())


def _analyzers() -> list:
    """The resolvers as the pass holds them (`engine_pass.ENGINES`), each with its adapter's declaration."""
    import importlib
    import types
    import engine_pass
    found = []
    for spec in engine_pass.ENGINES:
        module = importlib.import_module(f"indexers.{spec.indexer}")
        found.append(types.SimpleNamespace(
            NAME=spec.name, LANGUAGES=spec.languages, VERSION=getattr(module, "VERSION", None),
            UNIT_KINDS=module.UNIT_KINDS, NEEDS_CONTAINER=spec.needs_container,
            SNAPSHOT_LANGUAGES=getattr(module, "SNAPSHOT_LANGUAGES", ())))
    return found


def _owner(language: str):
    """The analyzer that resolves `language`: the first that lists it."""
    return next((analyzer for analyzer in _analyzers() if language in analyzer.LANGUAGES), None)


def need(node: dict, language: str) -> str | None:
    """The id of the node of `node`'s `needs` that `language` waits for: its parser (a resolver), its resolver (an
    observer); None where it waits for none."""
    if node["step"] == LINK_CALLS:
        needed = node_of({"language": language})
    else:
        owner = _owner(language)
        needed = f"{LINK_CALLS}:{owner.NAME}" if owner else None
    return needed if needed in node["needs"] else None


def blocked(node: dict, failed: dict) -> dict[str, tuple[str, str]]:
    """The languages of `node` whose need failed, each with the need and why: `failed` maps a node id to the reason
    it failed, or to `{language: reason}` where it failed for some of the languages that wait for it."""
    found = {}
    for language in node["on"]["languages"]:
        needed = need(node, language)
        reason = failed.get(needed) if needed else None
        if isinstance(reason, dict):
            reason = reason.get(language)
        if reason is not None:
            found[language] = (needed, reason)
    return found


def _node(step: str, adapter: str, version, on: dict, container: bool, needs: list[str]) -> dict:
    return {"id": f"{step}:{adapter}", "step": step, "adapter": adapter, **({"version": version} if version else {}),
            "on": on, "container": container, "needs": needs}


def _tally(rows) -> tuple[collections.Counter, dict, set]:
    """The files per language (None: no language), the statuses each language's files have, and the languages
    held at all, outside the perimeter or not."""
    files, statuses, held = collections.Counter(), collections.defaultdict(set), set()
    for _path, row in rows:
        language = row.get("language")
        if language:
            held.add(language)
        if row.get("status") == "excluded":  # outside the perimeter: in no node, and the inventory says why
            continue
        files[language] += row.get("files", 1)
        statuses[language].add(row.get("status"))
    return files, statuses, held


def _read(files: collections.Counter) -> list[dict]:
    nodes = [_node(READ_CODE, language, None, {"languages": [language], "files": files[language]}, False, [])
             for language in sorted(language for language in files if language)]
    if files[None]:
        nodes.append(_node(READ_CODE, FILE_LEVEL, None, {"languages": [], "files": files[None]}, False, []))
    return nodes


def parse_nodes(rows) -> list[dict]:
    """The reading's nodes alone, which need no adapter registry: what the reading takes its files from."""
    return _read(_tally(rows)[0])


def plan(rows) -> dict:
    """The nodes and gaps for `rows`."""
    import dynamic
    from semantic_store import READ
    files, statuses, held = _tally(rows)
    read = {language for language, found in statuses.items() if found & set(READ)}
    languages = sorted(language for language in files if language)
    nodes = _read(files)
    analyzers = _analyzers()
    owner: dict = {}
    for analyzer in analyzers:  # a language's resolver is the first analyzer that lists it
        for language in analyzer.LANGUAGES:
            owner.setdefault(language, analyzer)
    planned = set(languages)
    for analyzer in analyzers:  # a graph built from other languages' files is planned when the snapshot holds one
        if held & set(analyzer.SNAPSHOT_LANGUAGES):
            planned.update(analyzer.LANGUAGES)
    resolved = []
    for analyzer in analyzers:
        mine = [language for language in analyzer.LANGUAGES if language in planned and owner[language] is analyzer]
        if not mine:
            continue
        sources = sorted(language for language in analyzer.SNAPSHOT_LANGUAGES if files[language])
        # A graph of other languages' files reads them with its own parsers: no reading node of the snapshot is its need.
        needs = [] if analyzer.SNAPSHOT_LANGUAGES else [node_of({"language": language}) for language in mine
                                                        if files[language]]
        nodes.append(_node(LINK_CALLS, analyzer.NAME, analyzer.VERSION,
                           {"languages": mine, "files": sum(files[language] for language in {*mine, *sources}),
                            "unit_kinds": sorted(analyzer.UNIT_KINDS)}, bool(analyzer.NEEDS_CONTAINER), needs))
        resolved += mine
    watched = set()
    for observer in dynamic.observers():
        mine = sorted(language for language in observer.LANGUAGES if language in resolved)
        watched.update(observer.LANGUAGES)
        if mine:
            nodes.append(_node(RUN_AND_OBSERVE, observer.NAME, getattr(observer, "VERSION", None),
                               {"languages": mine, "files": sum(files[language] for language in mine)}, True,
                               sorted({f"{LINK_CALLS}:{owner[language].NAME}" for language in mine})))
    gaps = []
    served = {language for analyzer in analyzers for language in analyzer.SNAPSHOT_LANGUAGES}
    for language in languages:  # a graph of other languages' files serves one whose files it reads no code of
        if language not in owner and (language not in served or language in read):
            gaps.append({"kind": "no-analyzer", "language": language, "files": files[language], "detail":
                         f"{files[language]} {language} files are in the snapshot and no analyzer lists the language: "
                         "no graph"})
    for language in sorted(resolved):
        if language not in watched:
            gaps.append({"kind": "no-observer", "language": language, "files": files[language], "detail":
                         f"{language}: no observer runs its tests, so its graph holds no observed edge"})
    return {"nodes": nodes, "gaps": gaps}


# ---------------------------------------------------------------- the one plan

# The kinds of action, a closed list, each with its step and whether it may run the project's code (only ever in the
# container: an action's `project_code` holds only where its `container` does).
ACTIONS = ("read", "recognize", "model", "entries", "resolve", "observe", "explore", "assemble")
KINDS = {"read": (READ_CODE, False), "recognize": ("recognize_stack", False), "model": ("find_modules", True),
         "entries": ("find_entry_points", False), "resolve": (LINK_CALLS, True), "observe": (RUN_AND_OBSERVE, True),
         "explore": (RUN_AND_OBSERVE, True), "assemble": ("assemble_graph", False)}
NODE_KIND = {READ_CODE: "read", LINK_CALLS: "resolve", RUN_AND_OBSERVE: "observe"}
STEPWIDE = ("recognize", "model", "entries", "assemble")  # the steps with no adapter: one action each
STATES = ("pending", "running", "done", "failed", "skipped")  # a step's; an action adds these
ACTION_STATES = (*STATES, "not_possible", "awaiting_approval")
DOWNLOADS = {"kind": "download_size_unknown",
             "detail": "how much a run downloads is not known before it runs: no source gives its size"}


def current(manifest) -> dict:
    """The one plan of the snapshot `manifest`, computed at each call from its owners (no file of its own):

    - `steps`: the eight ids in order, each `{id, state, executes, stops}`, `state` one of `STATES` (with `cause` and
      `remedy` when failed, and `started_at` and `ended_at` where the journal has them): `list_files` and `read_code`
      from the store's header (`reading`), the others from the journal (`events.read`); `executes` is the step's
      `EXECUTES`, `stops` whether the steps after it need it (`WITHOUT is None`).
    - `policy`: what a run may reach (`egress`) and the container engine (`DAODAN_CONTAINER`).
    - `actions`: each `{id, step, kind, target, project_code, container, state}`, `kind` one of `ACTIONS`: the nodes
      of the plan of the store (`plan(stored(store))`, `target` their `on`); those the steps 3–5 find in their fresh
      records (`_found`: `recognize`, `model` and `entries` per source, with its `tools` and `network`, `explore` per
      app), else one for the step. The state, one of `ACTION_STATES`, comes from the step's `analyzer.*` events since
      it began (`fresh` is `skipped`) or the record; `not_possible`, with `cause` and `remedy`, from
      `analyzer.unavailable`, a need that failed (`blocked`) or a host the user refused (`host_denied`);
      `awaiting_approval`, with `hosts`, while a request of one of its tools waits for an answer (`_asked`).
    - `gaps`: the plan's, and the size of the downloads, which no source gives."""
    from pathlib import Path
    from pipeline import events
    manifest = Path(manifest).resolve()
    header, rows, unparsed, unreadable = None, [], {}, None
    if manifest.is_file():
        from snapshot_store import open_snapshot
        try:
            with open_snapshot(manifest) as store:
                header, rows = dict(store.metadata), stored(store)
                if header.get("reading") != "not-started" and getattr(store, "connection", None) is not None:
                    import engine_pass
                    unparsed = {node_of({"language": language}): reason
                                for language, reason in engine_pass.unparsed(store.connection).items()}
        except (OSError, ValueError) as error:  # a refused or broken store: the plan says why, and holds no node
            header, unreadable = None, f"{type(error).__name__}: {error}"
    recorded = events.read(manifest.with_name(events.JOURNAL))[0] if header is not None else []
    steps, begun = _steps(header, unreadable, recorded)
    planned = plan(rows) if header is not None else {"nodes": [], "gaps": []}
    by_step = {step["id"]: step for step in steps}
    project = _project(manifest) if header is not None else None
    asked = _asked(project)
    actions = [_node_action(node, by_step, begun, recorded, unparsed, asked) for node in planned["nodes"]]
    found = _found(manifest, by_step, begun, recorded, asked, project) if header is not None else {}
    for kind in STEPWIDE:
        if found.get(kind) is not None:  # the actions the step's fresh record shows
            actions.extend(found[kind])
            continue
        step = by_step[KINDS[kind][0]]
        container = step["executes"] == "container"
        actions.append(_action(step["id"], step["id"], kind, {}, KINDS[kind][1] and container, container,
                               {key: step[key] for key in ("state", "cause", "remedy") if key in step}))
    actions.extend(found.get("explore") or ())
    return {"steps": steps, "policy": _policy(project), "actions": actions, "gaps": [*planned["gaps"], DOWNLOADS]}


def _asked(project: str | None):
    """The state of an action that asked for hosts, from `egress`: `awaiting_approval` with the `hosts` a request of one of
    its `tools` waits for (`egress.pending`: the tool `egress.asking` named), else `not_possible` with `host_denied` for
    the hosts of its gaps the user refused (`egress.decide`), else None. The requests' ports, addresses and declaring
    files stay in `egress.groups`."""
    import egress
    waiting = egress.pending(project) if project else []
    state, answers = (egress.load(), egress.session(project)) if project else (None, None)

    def asked(tools, hosts=()) -> dict | None:
        held = sorted({row["host"] for row in waiting if row.get("tool") in tools})
        if held:
            return {"state": "awaiting_approval", "hosts": held}
        refused = sorted({host for host in hosts if project and egress.decide(host, project, state, answers) == "deny"})
        if refused:
            return {"state": "not_possible", "gap": "host_denied", "hosts": refused,
                    "cause": f"the user refused {', '.join(refused)}", "remedy": "analyze again: the hosts are asked again"}
        return None
    return asked


def _found(manifest, steps: dict, begun: dict, recorded: list[dict], asked, project: str | None = None) -> dict:
    """The actions `recognize_stack`, `find_modules` and `find_entry_points` find, by kind, from their records when the
    records' owners say they are fresh (a kind without one is None): the stack's tool, the pre-map's and the entry points'
    sources that are not `not_needed` (of the pre-map, those with commands; a source with no command reads files), and the apps the pre-map declares
    (`starts`) or the user or the assistant states for the `project` (`commands`), which `run_and_observe` explores: its
    target is the root with the `argv`, `surface` and `declared_in` of the start that runs there (`_started`), and an
    app whose start is a stated command carries that start's `by` and `grade`; while a host the exploration's run
    asked for (the tool `dynamic.APP`) waits for an answer, each is `awaiting_approval` with the hosts. A folder on a
    surface not run yet (`dynamic.app.plan`, with the modules of the stack record as last written,
    `technologies.recorded`) is `not_possible` with the gap `ui_execution_deferred:<surface>`, also where no start is
    declared."""
    import json
    import commands
    import entry_points
    import premap
    import stack_recognition
    import technologies
    from dynamic import APP, app
    found = {}
    try:
        if stack_recognition.state(manifest) == "fresh":
            record = stack_recognition.recorded(manifest)
            checker = next((c for c in record.get("checkers", ()) if c.get("checker") == "stack-analyser"), {})
            state = ({"state": "done"} if checker.get("state") == "ran" else
                     {"state": "failed", "cause": checker.get("reason")} if checker else {"state": "pending"})
            found["recognize"] = [_action("recognize_stack:stack-analyser", "recognize_stack", "recognize",
                                          {"technologies": len(record.get("found", ()))}, False, False, state)]
        for kind, owner in (("model", premap), ("entries", entry_points)):
            if owner.state(manifest)["state"] != "fresh":
                continue
            record = json.loads(owner.path(manifest).read_text(encoding="utf-8"))
            step = KINDS[kind][0]
            found[kind] = [_source_action(step, kind, status, record.get("gaps", ()), asked)
                           for status in record.get("sources", ()) if status.get("state") != "not_needed"
                           and (kind == "entries" or status.get("tools") or status.get("rank") == "model")]
            if kind == "model":
                record = commands.merged(record, project) if project else record
                starts = record.get("starts", ())
                chosen = app.chosen(record)  # the start the exploration runs in each folder: its words and surface
                waiting = {}  # the roots on a surface not run yet: never run, whatever the app's events say
                for gap in app.plan(record, units=technologies.recorded(manifest).get("units") or ())["gaps"]:
                    if gap["kind"].startswith(f"{app.DEFERRED}:"):
                        waiting.setdefault(gap["root"], []).append(gap)
                # the hosts its run asked for (`dynamic._app`) first, then its events
                state = asked({APP}) or _events(RUN_AND_OBSERVE, APP, begun, recorded)
                found["explore"] = [_action(f"{RUN_AND_OBSERVE}:{APP}:{root}", RUN_AND_OBSERVE, "explore",
                                            {"root": root, **_started(chosen.get(root))}, True, True,
                                            {**state, **{key: value for key, value in chosen.get(root, {}).items()
                                                         if key in ("by", "grade")}, **_deferred(waiting.get(root))})
                                    for root in sorted({entry["root"] for entry in starts} | set(waiting))]
    except (OSError, ValueError, KeyError):  # a record that cannot be read: its step's own action says the step
        pass
    return found


def _deferred(gaps: list[dict] | None) -> dict:
    """The state of an app whose surface is not run yet (`dynamic.app.DEFERRED`): `not_possible` with the gap, its
    causes and remedy; nothing without one."""
    if not gaps:
        return {}
    return {"state": "not_possible", "gap": gaps[0]["kind"], "cause": "; ".join(gap["detail"] for gap in gaps),
            "remedy": gaps[0]["remedy"]}


def _started(entry: dict | None) -> dict:
    """What an `explore` action's target says of the start the exploration runs in its folder (`dynamic.app.chosen`):
    its words, its surface (`web` where it states none: the address it opens) and where it is declared."""
    from dynamic import app
    if entry is None:
        return {}
    return {"argv": entry.get("argv"), "surface": entry.get("surface") or app.WEB, "declared_in": entry["declared_in"]}


def _source_action(step: str, kind: str, status: dict, gaps, asked) -> dict:
    """A source of a record as an action: `done` when it ran, `failed`, `not_possible` where it could not run (with the
    `model_not_run` gap where a cause is known), `pending` where its commands wait for a runner; or waiting for, or refused,
    the hosts it asked for."""
    name, tools = status["source"], status.get("tools") or ()
    mine = [gap for gap in gaps if gap.get("source") == name]
    unrun = next((gap for gap in mine if gap.get("kind") == "model_not_run"), None)
    state = ({"state": "done"} if status["state"] == "ran" else
             {"state": "failed", "cause": status.get("reason")} if status["state"] == "failed" else
             {"state": "not_possible", "cause": status.get("reason"), "remedy": status.get("install")}
             if status["state"] == "unavailable" else
             {"state": "not_possible", "gap": "model_not_run", "cause": unrun.get("cause") or unrun["detail"],
              "remedy": unrun["remedy"]} if unrun and unrun.get("remedy") else
             {"state": "pending", **({"gap": "model_not_run"} if unrun else {})})
    hosts = {host for gap in mine for host in (gap.get("hosts") or [gap.get("host")] if gap.get("kind") in
                                                  ("approval_required", "host_denied") else ()) if host}
    state = asked(tools, hosts) or state
    container = bool(tools)  # its commands run in Daodan's container; a reader runs nothing
    return _action(f"{step}:{name}", step, kind, {"source": name}, KINDS[kind][1] and container, container,
                   {**({"tools": list(tools)} if tools else {}),
                    **({"network": status["network"]} if status.get("network") else {}), **state})


def _events(step: str, analyzer: str, begun: dict, recorded: list[dict]) -> dict:
    """The state the last `analyzer.*` event of `analyzer` gives since `step` began; `pending` without one."""
    state = {"state": "pending"}
    for event in recorded[begun[step]:] if step in begun else ():
        if event.get("step") == step and event.get("analyzer") == analyzer \
                and str(event.get("kind")).startswith("analyzer."):
            state = _analyzer_state(event)
    return state


def _steps(header: dict | None, unreadable: str | None, recorded: list[dict]) -> tuple[list[dict], dict]:
    """The eight steps with their state, and the journal's index where each of the pipeline's began last. A step's last
    event decides its state; one older than the last event of a step before it belongs to an analysis before, and the
    step is `pending` in this one. A step of the pipeline carries its times from the journal: `started_at`, the `at` of
    its `step.started` or `step.skipped`, and `ended_at`, the `at` of its `step.finished`, `step.failed` or
    `step.skipped`. A failed step carries its `cause` and `remedy`, and so does a skipped one whose `step.skipped`
    says them (`run_and_observe` with nothing to run)."""
    import pipeline
    listed = ({"state": "failed", "cause": unreadable, "remedy": "write the snapshot again"} if unreadable else
              {"state": "pending" if header is None else "done"})
    read = {"state": "done" if header is not None and header.get("reading") != "not-started" else "pending"}
    steps = [{"id": "list_files", **listed, "executes": "no", "stops": True},
             {"id": READ_CODE, **read, "executes": "no", "stops": True}]
    last, begun = {}, {}
    for number, event in enumerate(recorded):
        if str(event.get("kind")).startswith("step."):
            _, before = last.get(event.get("step"), (-1, None))
            last[event.get("step")] = (number, event)
            # a step that ran and found nothing to do began at its `step.started`
            if event["kind"] == "step.started" or event["kind"] == "step.skipped" and (
                    before is None or before["kind"] != "step.started"):
                begun[event.get("step")] = number
    floor = -1
    for step in pipeline.STEPS:
        number, event = last.get(step.NAME, (-1, None))
        entry = {"state": "pending"}
        if event is not None and number > floor:
            floor, data = number, event.get("data") or {}
            entry = {"state": {"step.started": "running", "step.skipped": "skipped", "step.failed": "failed",
                               "step.finished": "failed" if data.get("failed") else "done"}[event["kind"]]}
            if entry["state"] == "failed":
                entry.update({"cause": data.get("cause") or data.get("failed") or event.get("message"),
                              "remedy": data.get("remedy") or step.WITHOUT})
            elif entry["state"] == "skipped" and data.get("cause"):  # one that ran nothing says why, as a failed one
                entry.update({"cause": data["cause"], **({"remedy": data["remedy"]} if data.get("remedy") else {})})
            began = recorded[begun[step.NAME]].get("at") if step.NAME in begun else None
            ended = event.get("at") if event["kind"] != "step.started" else None
            entry.update({**({"started_at": began} if began else {}), **({"ended_at": ended} if ended else {})})
        else:
            begun.pop(step.NAME, None)
        steps.append({"id": step.NAME, **entry, "executes": step.EXECUTES, "stops": step.WITHOUT is None})
    return steps, begun


def _action(identifier: str, step: str, kind: str, target: dict, project_code: bool, container: bool,
            state: dict) -> dict:
    return {"id": identifier, "step": step, "kind": kind, "target": target, "project_code": project_code,
            "container": container, **state}


def _node_action(node: dict, steps: dict, begun: dict, recorded: list[dict], unparsed: dict, asked) -> dict:
    """A node of the plan as an action: a reading's from the store; a resolver's or an observer's from its analyzer's
    events since its step began, `not_possible` when the need of each of its languages failed, or waiting for the hosts
    its adapter asked for (the tool `egress.asking` names)."""
    kind = NODE_KIND[node["step"]]
    state = {"state": "pending"}
    if node["step"] == READ_CODE:
        if node["id"] in unparsed:
            state = {"state": "failed", "cause": unparsed[node["id"]], "remedy": _parser_install()}
        elif steps[READ_CODE]["state"] == "done":
            state = {"state": "done"}
    else:
        state = _events(node["step"], node["adapter"], begun, recorded)
        stopped = blocked(node, unparsed) if node["step"] == LINK_CALLS else {}
        if state["state"] == "pending" and stopped and set(stopped) == set(node["on"]["languages"]):
            state = {"state": "not_possible", "cause": "; ".join(reason for _need, reason in stopped.values()),
                     "remedy": _parser_install()}
        state = asked({node["adapter"]}) or state
    return _action(node["id"], node["step"], kind, node["on"], KINDS[kind][1] and node["container"], node["container"],
                   state)


def _analyzer_state(event: dict) -> dict:
    data = event.get("data") or {}
    said = {key: data[key] for key in ("cause", "remedy") if data.get(key)}
    if event["kind"] == "analyzer.started":
        return {"state": "running"}
    if event["kind"] == "analyzer.unavailable":
        return {"state": "not_possible", **said}
    if event.get("level") == "error":
        return {"state": "failed", **said}
    return {"state": "skipped" if data.get("fresh") else "done", **said}


def _parser_install() -> str:
    import engine_pass
    return engine_pass.PARSER_INSTALL


def _project(manifest) -> str | None:
    import egress
    try:
        return egress.project_of(manifest)
    except (OSError, ValueError, KeyError):
        return None


def _policy(project: str | None) -> dict:
    """What a run may reach and where it runs: the canonical hosts of `package-managers.json` and the project's approved
    ones are open, a blocked one is refused, every other asks, and only the app answers (`egress.reply`); the container
    engine is off with `DAODAN_CONTAINER=off`, else Daodan's own on Windows and the user's elsewhere
    (`container.find_engine`, asked when a run starts)."""
    import os
    import container
    import egress
    state = egress.load()
    off = os.environ.get("DAODAN_CONTAINER") == "off"
    return {"network": {"canonical": list(container.REGISTRIES),
                        "approved": state["whitelist"].get(project, []) if project else [],
                        "blocked": state["blacklist"], "other": "ask", "answered_in": "app"},
            "container": ({"engine": "off", "cause": container.OFF_CAUSE,
                           "remedy": "unset DAODAN_CONTAINER to run in a container"} if off else
                          {"engine": "daodan" if os.name == "nt" else "user"})}
