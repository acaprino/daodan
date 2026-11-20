#!/usr/bin/env python3
"""Check a whole-system reference map against the project it describes. It opens files and runs nothing.

    python reference.py check EXPECTED.json PROJECT_ROOT
    python reference.py pin EXPECTED.json PROJECT_ROOT [REPOSITORY_FOLDER ...]

A reference is the system map a person who knows the product would draw (README, «Riferimenti dell'intero
sistema»): the fields of `daodan/system-map/v1` plus `inside`, `what`, `proof`, `routes`, `registry`, `family`,
`role` and `mode` on a node, `has`, `entries` and `effects` on a flow, and `packages` and `gaps` on the map. Every
node and every arrow cites a line of the project and a text that line holds, so a wrong citation is found without
reading the reference by hand. With `commit` (an id, or folder to id when the case spans repositories) the files are
those of that commit, read with git: the project goes on, the reference stays where it was written. `pin` binds a
reference to the commit each repository is at, moves a citation whose text moved, and names the ones it cannot.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "daodan" / "core"))
import service_registry  # noqa: E402
import system_map  # noqa: E402

ENTRY_KINDS = ("controllo dell'interfaccia", "rotta", "comando", "messaggio", "evento hardware", "orario",
               "cambio di un dato", "avvio di un processo", "evento del repository",
               "evento del sistema operativo")  # the last four given by the owner on 20 November 2026
SERVICE_FIELDS = {"family", "role", "mode"}
NEAR = 3  # a cited text is looked for this many lines around the cited line
SECRETS = re.compile(r"(^|/)(secrets?\.json|\.env(\.[\w-]+)?|.*\.(pem|key|p12|keystore|jks))$")
TEMPLATES = re.compile(r"\.env\.(example|sample|template|dist)$")


class Project:
    """The project's files, read once each."""

    def __init__(self, root: Path):
        self.root, self.lines = root, {}

    def kind(self, rel: str) -> str | None:
        path = self.root / rel
        return "dir" if path.is_dir() else "file" if path.is_file() else None

    def text(self, rel: str) -> list[str]:
        if rel not in self.lines:
            self.lines[rel] = (self.root / rel).read_text(encoding="utf-8", errors="replace").splitlines()
        return self.lines[rel]

    def cited(self, at: str, has: str | None, where: str) -> list[str]:
        """What is wrong with the citation `path` or `path:line`, and with the text it must hold."""
        rel, _, line = at.partition(":")
        if not rel:
            return [f"{where}: an empty citation"]
        if SECRETS.search(rel) and not TEMPLATES.search(rel):
            return [f"{where}: {rel} is a file of secrets: cite the code that reads it"]
        if self.kind(rel) != "file":
            return [f"{where}: {rel} is not a file of the project"] if not (self.kind(rel) and not line) else []
        if not line:
            return [f"{where}: {at} needs a line to hold «{has}»"] if has else []
        lines = self.text(rel)
        if not line.isdigit() or not 1 <= int(line) <= len(lines):
            return [f"{where}: {at} is outside the file ({len(lines)} lines)"]
        if has and has not in "\n".join(lines[max(0, int(line) - 1 - NEAR):int(line) + NEAR]):
            return [f"{where}: «{has}» is not within {NEAR} lines of {at}"]
        return []

    def member(self, member: str, where: str) -> list[str]:
        if member.startswith(("store:", "module:")):
            return []
        rel, _, symbol = member.partition("::")
        if not rel or not self.kind(rel):
            return [f"{where}: member {rel} is not in the project"]
        if symbol and not re.search(rf"\b{re.escape(symbol.split('.')[-1])}\b", "\n".join(self.text(rel))):
            return [f"{where}: {rel} does not name {symbol}"]
        return []


class Committed(Project):
    """The files as one commit of each repository holds them, read with `git ls-tree` and `git cat-file`."""

    def __init__(self, root: Path, commits: dict[str, str]):
        super().__init__(root)
        self.commits, self.trees = commits, {}

    def _held(self, rel: str) -> tuple[str, str] | None:
        """The repository folder that holds `rel` and the path inside it."""
        rel = rel.replace("\\", "/").strip("/")
        rel = "" if rel == "." else rel
        for folder in self.commits:
            if not folder or rel == folder or rel.startswith(folder + "/"):
                return folder, rel[len(folder):].strip("/")
        return None

    def _git(self, folder: str, *args: str) -> str:
        done = subprocess.run(["git", "-C", str(self.root / folder), *args], check=True, capture_output=True)
        return done.stdout.decode("utf-8", errors="replace")

    def kind(self, rel: str) -> str | None:
        held = self._held(rel)
        if held is None:  # above the repositories: the folder that holds them, or nothing
            return "dir" if rel.strip("./") == "" else None
        folder, path = held
        if folder not in self.trees:
            files = set(self._git(folder, "ls-tree", "-r", "--name-only", "-z", self.commits[folder]).split("\0")) - {""}
            self.trees[folder] = files, {"/".join(f.split("/")[:k]) for f in files for k in range(f.count("/") + 1)}
        files, folders = self.trees[folder]
        return "file" if path in files else "dir" if path in folders else None

    def text(self, rel: str) -> list[str]:
        if rel not in self.lines:
            folder, path = self._held(rel)
            self.lines[rel] = self._git(folder, "cat-file", "blob", f"{self.commits[folder]}:{path}").splitlines()
        return self.lines[rel]


def _service(node: dict, where: str) -> list[str]:
    """An external node that is a system of others says its family, what it is for and how the program connects."""
    service = node.get("position") == "external" and node.get("type") not in system_map.NOT_SERVICES
    if not service:
        return [f"{where}: only an external service has family, role and mode"] if SERVICE_FIELDS & node.keys() else []
    if node.get("family") not in system_map.FAMILIES or not node.get("role") or not node.get("mode"):
        return [f"{where}: an external service has family, role and mode "
                f"(family one of {', '.join(system_map.FAMILIES)})"]
    return []


def _nodes(value: dict, project: Project) -> tuple[dict, list[str]]:
    nodes, problems = {}, []
    for node in value.get("nodes", []):
        name = node.get("name") or "?"
        where = f"node {name}"
        if system_map.key(name) in nodes:
            problems.append(f"{where}: the name is used twice")
        nodes[system_map.key(name)] = node
        position = node.get("position", "internal")
        if node.get("type") not in system_map.NODE_TYPES:
            problems.append(f"{where}: type {node.get('type')!r}")
        if position not in system_map.POSITIONS:
            problems.append(f"{where}: position {position!r}")
        if (position == "internal") != bool(node.get("members")):
            problems.append(f"{where}: only an internal node has members, and it has at least one")
        if position == "unseen" and not node.get("where"):
            problems.append(f"{where}: an unseen node says where its files are")
        if not node.get("what"):
            problems.append(f"{where}: what is missing")
        if not node.get("proof"):
            problems.append(f"{where}: no proof")
        problems += _service(node, where)
        for member in node.get("members", []):
            problems += project.member(member, where)
        for at in node.get("evidence", []):
            problems += project.cited(at, None, where)
        for proof in node.get("proof", []):
            problems += project.cited(proof.get("at", ""), proof.get("has"), where)
    for node in nodes.values():
        for field in ("inside", "on"):
            for other in ([node[field]] if isinstance(node.get(field), str) else node.get(field) or []):
                if system_map.key(other) not in nodes:
                    problems.append(f"node {node['name']}: {field} {other} is not a node")
        seen, at = set(), node
        while at.get("inside") and system_map.key(at["inside"]) in nodes:
            if at["name"] in seen:
                problems.append(f"node {node['name']}: inside goes round in a circle")
                break
            seen.add(at["name"])
            at = nodes[system_map.key(at["inside"])]
    return nodes, problems


def _flows(value: dict, nodes: dict, project: Project) -> list[str]:
    problems, names = [], set()
    areas = {system_map.key(a.get("name", "")): a.get("present") for a in value.get("areas", [])}
    problems += [f"area {a}: say whether it is present" for a in system_map.AREAS if not isinstance(areas.get(system_map.key(a)), bool)]
    for flow in value.get("flows", []):
        where = f"flow {flow.get('name') or '?'}"
        if system_map.key(flow.get("name", "")) in names:
            problems.append(f"{where}: the name is used twice")
        if problem := system_map.flow_name_problem(flow.get("name") or ""):
            problems.append(f"{where}: {problem}")
        names.add(system_map.key(flow.get("name", "")))
        if areas.get(system_map.key(flow.get("area", ""))) is not True:
            problems.append(f"{where}: area {flow.get('area')!r} is not declared present")
        if not flow.get("types") or set(flow["types"]) - set(system_map.FLOW_TYPES):
            problems.append(f"{where}: types {flow.get('types')!r}")
        inside = {system_map.key(n) for n in flow.get("nodes", [])}
        problems += [f"{where}: {n} is not a node" for n in flow.get("nodes", []) if system_map.key(n) not in nodes]
        if not flow.get("arrows") or not flow.get("entries"):
            problems.append(f"{where}: a flow has arrows and at least one entry")
        for arrow in flow.get("arrows", []):
            link = f"{where}: {arrow.get('from')} -> {arrow.get('to')}"
            if {system_map.key(arrow.get("from", "")), system_map.key(arrow.get("to", ""))} - inside:
                problems.append(f"{link}: an end is not a node of the flow")
            if not arrow.get("data") or arrow.get("kind") not in system_map.ARROW_KINDS:
                problems.append(f"{link}: data and kind")
            problems += project.cited(arrow.get("cite", ""), arrow.get("has"), link) if arrow.get("cite") else [f"{link}: no cite"]
        for end, kinds in (("entries", ENTRY_KINDS), ("effects", None)):
            for item in flow.get(end, []):
                if system_map.key(item.get("node", "")) not in inside or not item.get("what"):
                    problems.append(f"{where}: {end} name a node of the flow and say what")
                if kinds and item.get("kind") not in kinds:
                    problems.append(f"{where}: entry kind {item.get('kind')!r}")
    return problems


def _registry(nodes: dict) -> tuple[list[str], list[str]]:
    """An external node's `registry` is the id of its entry in `service-registry.json`; an id the registry does not
    have yet is a note, since the registry grows after the reference."""
    ids = {entry["id"] for entry in service_registry.load()["entries"]}
    problems, notes = [], []
    for node in nodes.values():
        if "registry" not in node:
            continue
        if node.get("position", "internal") != "external":
            problems.append(f"node {node['name']}: only an external node has a registry id")
        elif node["registry"] not in ids:
            notes.append(f"node {node['name']}: registry {node['registry']} is not in the registry yet")
        elif problem := system_map.registry_name_problem(node["name"], node["registry"]):
            problems.append(f"node {node['name']}: {problem}")
    return problems, notes


def check(value: dict, root: Path) -> dict:
    commit = value.get("commit")
    project = Committed(root, {"": commit} if isinstance(commit, str) else commit) if commit else Project(root)
    nodes, problems = _nodes(value, project)
    problems += _flows(value, nodes, project)
    registry_problems, notes = _registry(nodes)
    problems += registry_problems
    for package in value.get("packages", []):
        if project.kind(package.get("manifest", "")) != "file":
            problems.append(f"package {package.get('path')}: manifest {package.get('manifest')} is not a file")
    depth = Counter()
    for node in nodes.values():
        level, at = 0, node
        while at.get("inside") and system_map.key(at["inside"]) in nodes and level < 20:
            level, at = level + 1, nodes[system_map.key(at["inside"])]
        depth[level] += 1
    return {"case": value.get("case"), "nodes": len(nodes), "flows": len(value.get("flows", [])),
            "arrows": sum(len(f.get("arrows", [])) for f in value.get("flows", [])),
            "by_type": dict(Counter(n.get("type") for n in nodes.values()).most_common()),
            "by_position": dict(Counter(n.get("position", "internal") for n in nodes.values())),
            "by_depth": dict(sorted(depth.items())), "gaps": len(value.get("gaps", [])), "problems": problems, "notes": notes}


def pin(value: dict, root: Path, commit: str | dict) -> dict:
    """Bind a reference to a commit: a citation whose text moved goes to the nearest line that holds it, one whose
    text is gone stays where it was. The check of the result, and how many citations moved."""
    project, moved = Committed(root, {"": commit} if isinstance(commit, str) else commit), 0
    cited = [(proof, "at") for node in value.get("nodes", []) for proof in node.get("proof", [])]
    cited += [(arrow, "cite") for flow in value.get("flows", []) for arrow in flow.get("arrows", [])]
    for item, key in cited:
        rel, _, line = str(item.get(key, "")).partition(":")
        has = item.get("has")
        if not (has and line.isdigit() and project.kind(rel) == "file") or SECRETS.search(rel) and not TEMPLATES.search(rel):
            continue
        if not project.cited(item[key], has, ""):
            continue
        lines, span = project.text(rel), has.count("\n") + 1
        holds = [n for n in range(1, len(lines) + 1) if has in "\n".join(lines[n - 1:n - 1 + span])]
        if holds:
            item[key] = f"{rel}:{min(holds, key=lambda n: abs(n - int(line)))}"
            moved += 1
    value["commit"] = commit
    return {**check(value, root), "moved": moved}


def _head(repository: Path) -> str:
    done = subprocess.run(["git", "-C", str(repository), "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
    return done.stdout.strip()


def main(argv: list[str]) -> int:
    if len(argv) < 4 or argv[1] not in ("check", "pin") or argv[1] == "check" and len(argv) != 4:
        print(__doc__)
        return 2
    value, root = json.loads(Path(argv[2]).read_text(encoding="utf-8")), Path(argv[3])
    if argv[1] == "pin":
        report = pin(value, root, {folder: _head(root / folder) for folder in argv[4:]} or _head(root))
        Path(argv[2]).write_bytes(json.dumps(value, ensure_ascii=False).encode("utf-8"))
    else:
        report = check(value, root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["problems"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
