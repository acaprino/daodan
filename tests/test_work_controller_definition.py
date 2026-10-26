from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

import yaml

import work_controller_test_support  # noqa: F401: load the bundled runtime.

from work_controller.compose import compose_process
from work_controller.definition import (
    Definition,
    dump_definition,
    load_definition,
    parse_definition,
)
from work_controller.errors import DefinitionError
from work_controller.util import digest_value

SCHEMA = "work-controller/process/v1"


def make_artifact(
    name: str = "report",
    path: str = "artifacts/report.md",
    artifact_type: str = "markdown",
) -> dict[str, str]:
    return {"name": name, "type": artifact_type, "path": path}


def make_job(job_id: str = "analyze", job_type: str = "agent", **changes):
    job = {
        "id": job_id,
        "type": job_type,
        "summary": f"Summary for {job_id}",
    }
    if job_type == "command":
        job["command"] = {"argv": ["echo", "ok"]}
    job.update(changes)
    return job


def make_process(jobs=None, **changes):
    data = {
        "schema": SCHEMA,
        "kind": "graph",
        "id": "example",
        "objective": "Exercise the process definition",
        "jobs": [make_job()] if jobs is None else jobs,
    }
    data.update(changes)
    return data


def parse_data(data) -> Definition:
    return parse_definition(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


class DefinitionTests(unittest.TestCase):
    def assert_invalid(self, data) -> None:
        with self.assertRaises(DefinitionError):
            parse_data(data)

    def test_roundtrip_defaults_digest_and_load(self) -> None:
        source = make_process()
        snapshot = copy.deepcopy(source)

        definition = Definition(source)
        self.assertEqual(source, snapshot)
        self.assertEqual(definition.data["inputs"], [])
        self.assertEqual(
            definition.data["budget"], {"max_attempts": 20, "max_seconds": 3600}
        )
        job = definition.job("analyze")
        self.assertEqual(job["needs"], [])
        self.assertEqual(job["consumes"], [])
        self.assertEqual(job["produces"], [])
        self.assertEqual(job["write_set"], [])
        self.assertEqual(job["max_attempts"], 2)
        self.assertEqual(job["timeout_seconds"], 300)
        self.assertEqual(definition.dependencies, {"analyze": set()})
        self.assertEqual(definition.order, ("analyze",))
        self.assertEqual(definition.digest, digest_value(definition.data))

        dumped = dump_definition(source)
        self.assertEqual(source, snapshot)
        roundtripped = parse_definition(dumped)
        self.assertEqual(roundtripped.data, definition.data)
        self.assertEqual(roundtripped.digest, definition.digest)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "process.yaml"
            path.write_text(dumped, encoding="utf-8")
            self.assertEqual(load_definition(path).data, definition.data)

        with self.assertRaises(DefinitionError):
            definition.job("missing")

    def test_legacy_schema_is_accepted_and_preserved(self) -> None:
        for legacy_schema in ("process-controller/process/v1", "deadly-brain/process/v1"):
            with self.subTest(schema=legacy_schema):
                definition = parse_data(make_process(schema=legacy_schema))

                self.assertEqual(definition.data["schema"], legacy_schema)
                self.assertEqual(
                    parse_definition(dump_definition(definition.data)).data["schema"],
                    legacy_schema,
                )

    def test_unknown_fields_are_rejected_at_every_level(self) -> None:
        def base():
            produced = make_artifact()
            return make_process(
                [
                    make_job(
                        "run",
                        "command",
                        produces=[produced],
                        write_set=[produced["path"]],
                        commit={"message": "Save output"},
                    )
                ],
                inputs=[make_artifact("external", "artifacts/input.md")],
            )

        mutations = {
            "root": lambda data: data.update(extra=True),
            "process input": lambda data: data["inputs"][0].update(extra=True),
            "job": lambda data: data["jobs"][0].update(extra=True),
            "produced artifact": lambda data: data["jobs"][0]["produces"][0].update(
                extra=True
            ),
            "command": lambda data: data["jobs"][0]["command"].update(extra=True),
            "commit": lambda data: data["jobs"][0]["commit"].update(extra=True),
            "budget": lambda data: data.update(budget={"extra": 1}),
        }
        for label, mutate in mutations.items():
            with self.subTest(level=label):
                data = base()
                mutate(data)
                self.assert_invalid(data)

    def test_dependency_cycle_is_rejected(self) -> None:
        data = make_process(
            [
                make_job("a", needs=["b"]),
                make_job("b", needs=["a"]),
            ]
        )
        self.assert_invalid(data)

    def test_consumed_artifact_requires_producer_or_external_input(self) -> None:
        self.assert_invalid(make_process([make_job("review", consumes=["report"])]))

        external = make_process(
            [make_job("review", consumes=["report"])],
            inputs=[make_artifact()],
        )
        definition = parse_data(external)
        self.assertEqual(definition.dependencies["review"], set())

    def test_duplicate_artifact_producer_is_rejected(self) -> None:
        first = make_artifact(path="artifacts/first.md")
        second = make_artifact(path="artifacts/second.md")
        data = make_process(
            [
                make_job(
                    "first", produces=[first], write_set=[first["path"]]
                ),
                make_job(
                    "second", produces=[second], write_set=[second["path"]]
                ),
            ]
        )
        self.assert_invalid(data)

    def test_consumes_adds_producer_and_explicit_dependencies(self) -> None:
        report = make_artifact()
        data = make_process(
            [
                make_job("setup"),
                make_job(
                    "analyze", produces=[report], write_set=[report["path"]]
                ),
                make_job("review", needs=["setup"], consumes=["report"]),
            ]
        )
        definition = parse_data(data)
        self.assertEqual(definition.dependencies["review"], {"setup", "analyze"})
        self.assertLess(definition.order.index("analyze"), definition.order.index("review"))
        self.assertLess(definition.order.index("setup"), definition.order.index("review"))

    def test_unsafe_paths_and_missing_write_set_are_rejected(self) -> None:
        for path in ("../escape.md", "/absolute.md", "C:\\escape.md"):
            with self.subTest(path=path):
                self.assert_invalid(
                    make_process(inputs=[make_artifact(path=path)])
                )

        produced = make_artifact(path="../escape.md")
        self.assert_invalid(
            make_process(
                [make_job(produces=[produced], write_set=[produced["path"]])]
            )
        )
        self.assert_invalid(make_process([make_job(write_set=["../escape"])]))
        self.assert_invalid(
            make_process(
                [make_job(produces=[make_artifact()], write_set=[])]
            )
        )

    def test_command_contract(self) -> None:
        valid = parse_data(make_process([make_job("run", "command")]))
        self.assertEqual(valid.job("run")["command"], {"argv": ["echo", "ok"]})

        missing = make_process([make_job("run", "command")])
        missing["jobs"][0].pop("command")
        self.assert_invalid(missing)
        self.assert_invalid(
            make_process([make_job("run", "command", command={"argv": []})])
        )
        self.assert_invalid(
            make_process([make_job("run", "command", command={"argv": ["echo", ""]})])
        )
        self.assert_invalid(
            make_process([make_job("run", "command", command={"argv": "echo"})])
        )
        self.assert_invalid(
            make_process([make_job(command={"argv": ["echo", "ok"]})])
        )

    def test_duplicate_list_entries_are_rejected(self) -> None:
        cases = {
            "needs": make_process(
                [make_job("a"), make_job("b", needs=["a", "a"])]
            ),
            "consumes": make_process(
                [make_job(consumes=["report", "report"])],
                inputs=[make_artifact()],
            ),
            "write_set": make_process(
                [make_job(write_set=["artifacts/a", "artifacts/a"])]
            ),
            "produces": make_process(
                [
                    make_job(
                        produces=[make_artifact(), make_artifact()],
                        write_set=["artifacts/report.md"],
                    )
                ]
            ),
            "process inputs": make_process(inputs=[make_artifact(), make_artifact()]),
        }
        for label, data in cases.items():
            with self.subTest(field=label):
                self.assert_invalid(data)

    def test_topological_order_is_independent_of_yaml_job_order(self) -> None:
        jobs = [
            make_job("a"),
            make_job("b", needs=["a"]),
            make_job("c", needs=["a"]),
            make_job("d", needs=["b", "c"]),
        ]
        forward = parse_data(make_process(jobs))
        reverse = parse_data(make_process(list(reversed(jobs))))

        self.assertEqual(forward.order, reverse.order)
        self.assertEqual(set(forward.order), {"a", "b", "c", "d"})
        for job_id, dependencies in forward.dependencies.items():
            for dependency in dependencies:
                self.assertLess(
                    forward.order.index(dependency), forward.order.index(job_id)
                )

    def test_invalid_numeric_defaults_and_commit_contract(self) -> None:
        for field, value in (("max_attempts", 0), ("max_attempts", 11), ("timeout_seconds", 3601)):
            with self.subTest(field=field, value=value):
                self.assert_invalid(make_process([make_job(**{field: value})]))
        self.assert_invalid(make_process(budget={"max_attempts": 101}))
        self.assert_invalid(
            make_process([make_job(commit={"message": "Save"})])
        )

    def test_external_input_cannot_shadow_a_producer(self) -> None:
        artifact = make_artifact()
        data = make_process(
            [make_job(produces=[artifact], write_set=[artifact["path"]])],
            inputs=[make_artifact()],
        )
        self.assert_invalid(data)

    def test_identifiers_are_stable_and_cli_safe(self) -> None:
        self.assert_invalid(make_process(id="Invalid Process"))
        self.assert_invalid(make_process([make_job("Invalid Job")]))
        self.assert_invalid(make_process(inputs=[make_artifact(name="Invalid Artifact")]))


class YamlSecurityTests(unittest.TestCase):
    def test_duplicate_yaml_keys_are_rejected(self) -> None:
        text = """\
schema: work-controller/process/v1
kind: graph
id: duplicate
objective: first
objective: second
jobs:
  - id: analyze
    type: agent
    summary: Analyze
"""
        with self.assertRaises(DefinitionError):
            parse_definition(text)

    def test_unsafe_yaml_tag_is_rejected(self) -> None:
        text = """\
schema: work-controller/process/v1
kind: graph
id: unsafe
objective: !!python/object/apply:builtins.str ["unsafe"]
jobs:
  - id: analyze
    type: agent
    summary: Analyze
"""
        with self.assertRaises(DefinitionError):
            parse_definition(text)

    def test_multiple_documents_and_non_mapping_root_are_rejected(self) -> None:
        document = yaml.safe_dump(make_process(), sort_keys=False)
        with self.assertRaises(DefinitionError):
            parse_definition(document + "\n---\n" + document)
        with self.assertRaises(DefinitionError):
            parse_definition("- not\n- a\n- mapping\n")

    def test_yaml_size_depth_and_collection_limits(self) -> None:
        with self.assertRaises(DefinitionError):
            parse_definition(" " * (1024 * 1024 + 1))

        too_deep = make_process(extra="leaf")
        for _ in range(40):
            too_deep["extra"] = [too_deep["extra"]]
        with self.assertRaises(DefinitionError):
            parse_data(too_deep)

        too_many = make_process(
            inputs=[
                make_artifact(f"input-{index}", f"artifacts/input-{index}.txt")
                for index in range(1001)
            ]
        )
        with self.assertRaises(DefinitionError):
            parse_data(too_many)


class ComposerTests(unittest.TestCase):
    def test_analysis_composer_builds_valid_pipeline(self) -> None:
        data = compose_process("Assess the engine")
        definition = Definition(data)

        self.assertEqual(definition.order, ("analyze", "review"))
        analyze = definition.job("analyze")
        self.assertEqual(analyze["type"], "agent")
        self.assertEqual(
            analyze["produces"],
            [{"name": "report", "type": "markdown", "path": "artifacts/report.md"}],
        )
        self.assertEqual(analyze["write_set"], ["artifacts/report.md"])
        review = definition.job("review")
        self.assertEqual(review["needs"], ["analyze"])
        self.assertEqual(review["consumes"], ["report"])
        self.assertEqual(
            review["produces"],
            [{"name": "review", "type": "markdown", "path": "artifacts/review.md"}],
        )

    def test_change_composer_builds_valid_edit_verify_pipeline(self) -> None:
        data = compose_process(
            "Fix the parser",
            archetype="change",
            target="src/parser.py",
            verify=["python", "-m", "unittest"],
            commit=True,
        )
        definition = Definition(data)
        edit = definition.job("edit")
        verification = definition.job("verify")

        self.assertEqual(edit["type"], "agent")
        self.assertEqual(edit["produces"][0]["name"], "target")
        self.assertEqual(edit["produces"][0]["path"], "src/parser.py")
        self.assertEqual(edit["write_set"], ["src/parser.py"])
        self.assertIn("commit", edit)
        self.assertTrue(edit["commit"]["message"].strip())
        self.assertEqual(verification["type"], "command")
        self.assertEqual(verification["needs"], ["edit"])
        self.assertEqual(verification["consumes"], ["target"])
        self.assertEqual(
            verification["command"], {"argv": ["python", "-m", "unittest"]}
        )
        self.assertEqual(definition.dependencies["verify"], {"edit"})

        without_commit = compose_process(
            "Fix the parser",
            archetype="change",
            target="src/parser.py",
            verify=["python", "-m", "unittest"],
        )
        self.assertNotIn("commit", Definition(without_commit).job("edit"))

    def test_composer_rejects_missing_or_invalid_arguments(self) -> None:
        invalid_calls = {
            "empty objective": lambda: compose_process("  "),
            "unknown archetype": lambda: compose_process("Objective", "unknown"),
            "missing target": lambda: compose_process(
                "Objective", "change", verify=["true"]
            ),
            "missing verify": lambda: compose_process(
                "Objective", "change", target="file.txt"
            ),
            "empty verify": lambda: compose_process(
                "Objective", "change", target="file.txt", verify=[]
            ),
            "empty argv item": lambda: compose_process(
                "Objective", "change", target="file.txt", verify=["true", ""]
            ),
            "argv not a list": lambda: compose_process(
                "Objective", "change", target="file.txt", verify="true"
            ),
            "escaping target": lambda: compose_process(
                "Objective", "change", target="../file.txt", verify=["true"]
            ),
        }
        for label, call in invalid_calls.items():
            with self.subTest(case=label), self.assertRaises(DefinitionError):
                call()


if __name__ == "__main__":
    unittest.main()
