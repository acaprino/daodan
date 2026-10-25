"""Strict parsing, normalization and graph validation for process definitions."""

from __future__ import annotations

import re
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
from typing import Any

import yaml
from yaml.nodes import MappingNode

from .errors import DefinitionError
from .util import digest_value, relative_path

SCHEMA = "work-controller/process/v1"
_LEGACY_SCHEMAS = ("process-controller/process/v1", "deadly-brain/process/v1")
_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")

_MAX_YAML_BYTES = 1024 * 1024
_MAX_DEPTH = 32
_MAX_COLLECTION_ITEMS = 1000
_MAX_NODES = 50_000
_MISSING = object()

_ROOT_FIELDS = {"schema", "kind", "id", "objective", "inputs", "jobs", "budget"}
_JOB_FIELDS = {
    "id",
    "type",
    "summary",
    "needs",
    "consumes",
    "produces",
    "write_set",
    "max_attempts",
    "timeout_seconds",
    "command",
    "commit",
}
_ARTIFACT_FIELDS = {"name", "type", "path"}


class _DefinitionLoader(yaml.SafeLoader):
    """SafeLoader that also rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: _DefinitionLoader, node: MappingNode, deep: bool = False
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise DefinitionError("YAML mapping keys must be hashable") from exc
        if duplicate:
            raise DefinitionError(f"duplicate YAML mapping key: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_DefinitionLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


def _check_resource_limits(value: Any) -> None:
    visited = 0

    def visit(item: Any, depth: int, active: set[int]) -> None:
        nonlocal visited
        visited += 1
        if visited > _MAX_NODES:
            raise DefinitionError("definition contains too many YAML nodes")
        if depth > _MAX_DEPTH:
            raise DefinitionError(f"definition nesting exceeds {_MAX_DEPTH} levels")
        if not isinstance(item, (dict, list)):
            return
        if len(item) > _MAX_COLLECTION_ITEMS:
            raise DefinitionError(
                f"definition collections are limited to {_MAX_COLLECTION_ITEMS} items"
            )
        identity = id(item)
        if identity in active:
            raise DefinitionError("recursive YAML aliases are not supported")
        active.add(identity)
        try:
            children = item.keys() if isinstance(item, dict) else ()
            for child in children:
                visit(child, depth + 1, active)
            values = item.values() if isinstance(item, dict) else item
            for child in values:
                visit(child, depth + 1, active)
        finally:
            active.remove(identity)

    visit(value, 0, set())


def _mapping(value: Any, field: str) -> dict[Any, Any]:
    if not isinstance(value, dict):
        raise DefinitionError(f"{field} must be a mapping")
    return value


def _reject_unknown(
    mapping: dict[Any, Any], allowed: set[str], field: str
) -> None:
    unknown = [repr(key) for key in mapping if key not in allowed]
    if unknown:
        raise DefinitionError(
            f"unknown field(s) in {field}: {', '.join(sorted(unknown))}"
        )


def _required(mapping: dict[Any, Any], key: str, field: str) -> Any:
    value = mapping.get(key, _MISSING)
    if value is _MISSING:
        raise DefinitionError(f"{field}.{key} is required")
    return value


def _nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DefinitionError(f"{field} must be a nonempty string")
    return value


def _identifier(value: Any, field: str) -> str:
    text = _nonempty_string(value, field)
    if not _IDENTIFIER.fullmatch(text):
        raise DefinitionError(f"{field} must use lowercase letters, digits and hyphens")
    return text


def _bounded_integer(value: Any, field: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise DefinitionError(f"{field} must be an integer in {minimum}..{maximum}")
    return value


def _list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise DefinitionError(f"{field} must be a list")
    return value


def _string_list(
    value: Any,
    field: str,
    *,
    require_items: bool = False,
    unique: bool = False,
    paths: bool = False,
) -> list[str]:
    items = _list(value, field)
    if require_items and not items:
        raise DefinitionError(f"{field} must be a nonempty list")
    result: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(items):
        item_field = f"{field}[{index}]"
        text = _nonempty_string(item, item_field)
        if paths:
            relative_path(text, field=item_field)
        if unique and text in seen:
            raise DefinitionError(f"{field} contains duplicate entry: {text!r}")
        seen.add(text)
        result.append(text)
    return result


def _normalize_artifacts(value: Any, field: str) -> list[dict[str, str]]:
    artifacts: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, item in enumerate(_list(value, field)):
        item_field = f"{field}[{index}]"
        artifact = _mapping(item, item_field)
        _reject_unknown(artifact, _ARTIFACT_FIELDS, item_field)
        name = _identifier(_required(artifact, "name", item_field), f"{item_field}.name")
        artifact_type = _nonempty_string(
            _required(artifact, "type", item_field), f"{item_field}.type"
        )
        path = _nonempty_string(
            _required(artifact, "path", item_field), f"{item_field}.path"
        )
        relative_path(path, field=f"{item_field}.path")
        if name in seen:
            raise DefinitionError(f"{field} contains duplicate artifact: {name!r}")
        seen.add(name)
        artifacts.append({"name": name, "type": artifact_type, "path": path})
    return artifacts


def _normalize_command(value: Any, field: str) -> dict[str, list[str]]:
    command = _mapping(value, field)
    _reject_unknown(command, {"argv"}, field)
    argv = _string_list(
        _required(command, "argv", field), f"{field}.argv", require_items=True
    )
    return {"argv": argv}


def _normalize_commit(value: Any, field: str) -> dict[str, str]:
    commit = _mapping(value, field)
    _reject_unknown(commit, {"message"}, field)
    message = _nonempty_string(
        _required(commit, "message", field), f"{field}.message"
    )
    return {"message": message}


def _normalize_job(value: Any, field: str) -> dict[str, Any]:
    job = _mapping(value, field)
    _reject_unknown(job, _JOB_FIELDS, field)
    job_id = _identifier(_required(job, "id", field), f"{field}.id")
    job_type = _nonempty_string(_required(job, "type", field), f"{field}.type")
    if job_type not in {"agent", "command"}:
        raise DefinitionError(f"{field}.type must be agent or command")
    summary = _nonempty_string(_required(job, "summary", field), f"{field}.summary")
    needs = _string_list(job.get("needs", []), f"{field}.needs", unique=True)
    consumes = _string_list(
        job.get("consumes", []), f"{field}.consumes", unique=True
    )
    produces = _normalize_artifacts(job.get("produces", []), f"{field}.produces")
    write_set = _string_list(
        job.get("write_set", []), f"{field}.write_set", unique=True, paths=True
    )
    max_attempts = _bounded_integer(
        job.get("max_attempts", 2), f"{field}.max_attempts", 1, 10
    )
    timeout_seconds = _bounded_integer(
        job.get("timeout_seconds", 300), f"{field}.timeout_seconds", 1, 3600
    )

    normalized: dict[str, Any] = {
        "id": job_id,
        "type": job_type,
        "summary": summary,
        "needs": needs,
        "consumes": consumes,
        "produces": produces,
        "write_set": write_set,
        "max_attempts": max_attempts,
        "timeout_seconds": timeout_seconds,
    }
    if job_type == "command":
        normalized["command"] = _normalize_command(
            _required(job, "command", field), f"{field}.command"
        )
    elif "command" in job:
        raise DefinitionError(f"{field}.command is only valid for command jobs")

    if "commit" in job:
        if not write_set:
            raise DefinitionError(f"{field}.commit requires a nonempty write_set")
        normalized["commit"] = _normalize_commit(job["commit"], f"{field}.commit")

    declared_paths = set(write_set)
    for artifact in produces:
        if artifact["path"] not in declared_paths:
            raise DefinitionError(
                f"{field}.produces path {artifact['path']!r} must be in write_set"
            )
    return normalized


def _normalize_budget(value: Any) -> dict[str, int]:
    budget = _mapping(value, "budget")
    _reject_unknown(budget, {"max_attempts", "max_seconds"}, "budget")
    return {
        "max_attempts": _bounded_integer(
            budget.get("max_attempts", 20), "budget.max_attempts", 1, 100
        ),
        "max_seconds": _bounded_integer(
            budget.get("max_seconds", 3600), "budget.max_seconds", 1, 86400
        ),
    }


def _normalize_definition(value: Any) -> dict[str, Any]:
    _check_resource_limits(value)
    data = _mapping(value, "definition")
    _reject_unknown(data, _ROOT_FIELDS, "definition")
    schema = _required(data, "schema", "definition")
    if schema not in (SCHEMA, *_LEGACY_SCHEMAS):
        raise DefinitionError(
            f"definition.schema must be one of {(SCHEMA, *_LEGACY_SCHEMAS)!r}"
        )
    if _required(data, "kind", "definition") != "graph":
        raise DefinitionError("definition.kind must be 'graph'")

    process_id = _identifier(
        _required(data, "id", "definition"), "definition.id"
    )
    objective = _nonempty_string(
        _required(data, "objective", "definition"), "definition.objective"
    )
    inputs = _normalize_artifacts(data.get("inputs", []), "inputs")
    raw_jobs = _list(_required(data, "jobs", "definition"), "jobs")
    if not raw_jobs:
        raise DefinitionError("jobs must be a nonempty list")

    jobs: list[dict[str, Any]] = []
    job_ids: set[str] = set()
    for index, raw_job in enumerate(raw_jobs):
        job = _normalize_job(raw_job, f"jobs[{index}]")
        if job["id"] in job_ids:
            raise DefinitionError(f"duplicate job id: {job['id']!r}")
        job_ids.add(job["id"])
        jobs.append(job)

    return {
        "schema": schema,
        "kind": "graph",
        "id": process_id,
        "objective": objective,
        "inputs": inputs,
        "jobs": jobs,
        "budget": _normalize_budget(data.get("budget", {})),
    }


def _build_graph(
    jobs: list[dict[str, Any]], inputs: list[dict[str, str]]
) -> tuple[dict[str, set[str]], tuple[str, ...]]:
    job_ids = {job["id"] for job in jobs}
    external_inputs = {artifact["name"] for artifact in inputs}
    producers: dict[str, str] = {}
    for job in jobs:
        for artifact in job["produces"]:
            name = artifact["name"]
            if name in external_inputs:
                raise DefinitionError(f"artifact {name!r} is both external input and produced output")
            if name in producers:
                raise DefinitionError(
                    f"artifact {name!r} has multiple producers: "
                    f"{producers[name]!r} and {job['id']!r}"
                )
            producers[name] = job["id"]

    dependencies: dict[str, set[str]] = {}
    for job in jobs:
        required = set(job["needs"])
        unknown = required - job_ids
        if unknown:
            raise DefinitionError(
                f"job {job['id']!r} needs unknown job(s): {', '.join(sorted(unknown))}"
            )
        for name in job["consumes"]:
            if name in producers:
                required.add(producers[name])
            elif name not in external_inputs:
                raise DefinitionError(
                    f"artifact {name!r} consumed by {job['id']!r} has no "
                    "producer or external input"
                )
        dependencies[job["id"]] = required

    graph = {
        job_id: tuple(sorted(dependencies[job_id])) for job_id in sorted(dependencies)
    }
    try:
        order = tuple(TopologicalSorter(graph).static_order())
    except CycleError as exc:
        raise DefinitionError("job dependency graph contains a cycle") from exc
    return dependencies, order


class Definition:
    """A normalized, validated process definition and its deterministic graph."""

    def __init__(self, data: dict[str, Any]):
        self.data = _normalize_definition(data)
        self._jobs = {job["id"]: job for job in self.data["jobs"]}
        self.dependencies, self.order = _build_graph(
            self.data["jobs"], self.data["inputs"]
        )
        self.digest = digest_value(self.data)

    def job(self, job_id: str) -> dict[str, Any]:
        try:
            return self._jobs[job_id]
        except (KeyError, TypeError):
            raise DefinitionError(f"unknown job: {job_id!r}") from None


def parse_definition(text: str) -> Definition:
    """Parse one bounded, safe YAML document into a validated definition."""

    if not isinstance(text, str):
        raise DefinitionError("definition source must be text")
    try:
        size = len(text.encode("utf-8"))
    except UnicodeError as exc:
        raise DefinitionError("definition source is not valid UTF-8 text") from exc
    if size > _MAX_YAML_BYTES:
        raise DefinitionError("definition YAML exceeds the 1 MiB limit")
    try:
        data = yaml.load(text, Loader=_DefinitionLoader)
    except DefinitionError:
        raise
    except (yaml.YAMLError, RecursionError, ValueError, OverflowError) as exc:
        raise DefinitionError(f"invalid definition YAML: {exc}") from exc
    return Definition(data)


def load_definition(path: str | Path) -> Definition:
    """Read a UTF-8 definition file without bypassing the source size limit."""

    source = Path(path)
    try:
        if source.stat().st_size > _MAX_YAML_BYTES:
            raise DefinitionError("definition YAML exceeds the 1 MiB limit")
        text = source.read_text(encoding="utf-8")
    except DefinitionError:
        raise
    except (OSError, UnicodeError) as exc:
        raise DefinitionError(f"cannot read definition {source}: {exc}") from exc
    return parse_definition(text)


def dump_definition(data: dict[str, Any]) -> str:
    """Validate and serialize the normalized form without mutating the caller."""

    normalized = Definition(data).data
    return yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True)
