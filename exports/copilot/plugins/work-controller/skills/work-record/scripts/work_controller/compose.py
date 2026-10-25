"""Deterministic built-in process archetypes."""

from __future__ import annotations

from typing import Any

from .definition import SCHEMA
from .errors import DefinitionError
from .util import relative_path


def _verify_argv(verify: list[str] | None) -> list[str]:
    if not isinstance(verify, list) or not verify:
        raise DefinitionError("change archetype requires a nonempty verify argv list")
    if any(not isinstance(argument, str) or not argument.strip() for argument in verify):
        raise DefinitionError("verify argv entries must be nonempty strings")
    return list(verify)


def compose_process(
    objective: str,
    archetype: str = "analysis",
    target: str | None = None,
    verify: list[str] | None = None,
    commit: bool = False,
) -> dict[str, Any]:
    """Compose a valid raw process definition for a built-in archetype."""

    if not isinstance(objective, str) or not objective.strip():
        raise DefinitionError("objective must be a nonempty string")
    if not isinstance(commit, bool):
        raise DefinitionError("commit must be a boolean")

    if archetype == "analysis":
        jobs = [
            {
                "id": "analyze",
                "type": "agent",
                "summary": "Analyze the objective and write a report",
                "produces": [
                    {
                        "name": "report",
                        "type": "markdown",
                        "path": "artifacts/report.md",
                    }
                ],
                "write_set": ["artifacts/report.md"],
            },
            {
                "id": "review",
                "type": "agent",
                "summary": "Review the analysis report",
                "needs": ["analyze"],
                "consumes": ["report"],
                "produces": [
                    {
                        "name": "review",
                        "type": "markdown",
                        "path": "artifacts/review.md",
                    }
                ],
                "write_set": ["artifacts/review.md"],
            },
        ]
    elif archetype == "change":
        target_path = relative_path(target, field="target")
        argv = _verify_argv(verify)
        target_text = str(target)
        target_artifact = {"name": "target", "type": "file", "path": target_text}
        edit: dict[str, Any] = {
            "id": "edit",
            "type": "agent",
            "summary": f"Edit {target_path.as_posix()}",
            "produces": [target_artifact],
            "write_set": [target_text],
        }
        if commit:
            edit["commit"] = {"message": f"Update {target_text}"}
        jobs = [
            edit,
            {
                "id": "verify",
                "type": "command",
                "summary": "Verify the requested change",
                "needs": ["edit"],
                "consumes": ["target"],
                "command": {"argv": argv},
            },
        ]
    else:
        raise DefinitionError(f"unknown process archetype: {archetype!r}")

    return {
        "schema": SCHEMA,
        "kind": "graph",
        "id": archetype,
        "objective": objective,
        "jobs": jobs,
    }
