"""Test structural source facts and original published Boolean questions."""
from __future__ import annotations

import argparse
import ast
import copy
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from run_eval import BASE, digest, encoded, load_julia, read_json, utc_now, write_json

RUN = BASE / "runs/20261020T-diagnostic"
OUT = RUN / "phase3"


def source_facts(source: str) -> dict:
    """Read syntax only; do not infer a reviewer, bug, relevance or gold label."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        candidates = set(re.findall(
            r"\b([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*\(", source
        ))
        declarations = set(re.findall(r"\bfunction\s+([A-Za-z_$][\w$]*)", source))
        return {
            "language": "JavaScript or TypeScript",
            "imported_modules": sorted(set(re.findall(r'\bfrom\s+["\']([^"\']+)["\']', source))),
            "called_names": sorted(candidates - declarations - {"if", "for", "while", "switch", "return", "catch"}),
            "jsx_element_names": sorted(set(
                re.findall(r"</([A-Za-z][A-Za-z0-9.]*)\s*>", source)
                + re.findall(r"<([A-Za-z][A-Za-z0-9.]*)\b[^<>]*/>", source)
            )),
        }

    def dotted(node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = dotted(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return None

    imports, calls = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
        elif isinstance(node, ast.Call):
            name = dotted(node.func)
            if name:
                calls.add(name)
    return {
        "language": "Python",
        "imported_modules": sorted(imports),
        "called_names": sorted(calls),
        "jsx_element_names": [],
    }


def prepare() -> None:
    controls = read_json(RUN / "fresh-controls.json")["cases"]
    existing = {x["id"]: x for x in read_json(RUN / "phase2/fresh-requests.json")}
    requests = []
    for control in controls:
        original = existing[control["id"]]
        questions = copy.deepcopy(original["questions"])
        facts = source_facts(control["state"])
        requests.append({
            "id": control["id"] + "-facts", "state": facts, "questions": questions,
            "source_sha256": digest(control["state"]),
            "transform": "source_facts; syntax only, no labels",
        })
        statements = copy.deepcopy(questions)
        statements.pop("family")
        statements["react"]["instructions"] = "The code uses React components or React hooks."
        statements["persistence"]["instructions"] = "The code reads or writes a database or cache."
        requests.append({
            "id": control["id"] + "-statements", "state": original["state"],
            "questions": statements, "source_sha256": digest(control["state"]),
            "transform": "Only interrogative instructions changed to declarative propositions.",
        })
    published = read_json(RUN / "official-controls.json")
    for entry in published["submissions"]:
        requests.append({
            "id": "official-" + entry["id"],
            "state": entry["state"], "questions": entry["questions"],
            "source_url": entry["source_url"], "transform": "None; exact original noul questions.",
        })
    write_json(OUT / "requests.json", requests, freeze=True)
    write_json(OUT / "plan.json", {
        "prepared_at": utc_now(), "script_sha256": digest(Path(__file__).read_bytes()),
        "purpose": __doc__,
        "interpretation": (
            "Development controls, not a new pilot comparison. Structural cards are automatically "
            "extracted without reviewer/gold labels. They approximate a map producer's input contract; "
            "this experiment does not integrate or validate the actual Codebase Map. "
            "Published gold probabilities are annotations, not Julia predictions."
        ),
        "threshold": 0.5,
    }, freeze=True)


def execute() -> None:
    requests = read_json(OUT / "requests.json")
    if any((OUT / "results").glob("*.json")):
        raise ValueError("Refusing to overwrite completed probe output")
    args = argparse.Namespace(
        batch_size=1, threads=4, allow_download=False,
        variant="facts-published", require_complete_catalog=True,
    )
    engine = load_julia(OUT, args)
    for request in requests:
        raw = engine.predict(state=request["state"], questions=request["questions"])
        write_json(OUT / "results" / f"{request['id']}.json", {
            "id": request["id"], "request_sha256": digest(encoded(request)),
            "raw_output": raw,
        }, freeze=True)
        print(f"Completed {request['id']}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "run"])
    args = parser.parse_args()
    {"prepare": prepare, "run": execute}[args.action]()
