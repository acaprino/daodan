"""Project-bound MCP service contracts over real Codebase Map artifacts."""

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import mcp_service
import snapshot


class MapServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="map-mcp-service-")
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name).resolve()
        self.source = self.project / "src"
        self.source.mkdir()
        self.module = self.source / "module.py"
        self.module.write_text("LIMIT = 7\n\ndef selected():\n    return LIMIT\n", encoding="utf-8")
        self.service = mcp_service.MapService(self.project)

    def create(self, **options):
        return self.service.create_run("src", "example", **options)

    def context_request(self):
        from snapshot_store import open_snapshot
        with open_snapshot(self.run_dir / 'snapshot/manifest.sqlite') as manifest:
            file = self.module.relative_to(Path(manifest['root'])).as_posix()
        return {'schema': 'daodan/context-request/v1', 'task_id': 'mcp-context',
            'intent': 'analysis', 'query': '', 'read_boundary': ['.'], 'write_boundary': [],
            'anchors': [{'entity_id': file + '::selected'}], 'base': None, 'candidate': None,
            'diff': [], 'proposed_edits': [], 'mandatory_requirements': [], 'required_gates': [{'id': 'tests'}],
            'budget': {'max_candidates': 100, 'max_edges': 1000, 'max_rounds': 100,
                'max_seconds': 120, 'max_input_tokens': 100000, 'max_output_tokens': 100000},
            'policy_version': 'scope-v1'}

    def test_context_uses_bound_non_git_run_and_returns_compact_immutable_artifacts(self):
        self.create()
        request = self.context_request()
        recipient = {'id': 'host', 'available_tokens': 100000, 'reserve_tokens': 1000,
                     'max_chars': 100000, 'max_evaluations': 100, 'policy': 'ordered'}
        result = self.service.context('example', request, recipient)
        packet = json.loads(Path(result['path']).read_text(encoding='utf8'))
        self.assertEqual(result['status'], 'ready')
        self.assertNotIn('blocks', result)
        self.assertNotIn('input', result)
        self.assertIn('return LIMIT', packet['input'])
        self.assertFalse(packet['budget']['dispatch_verified'])
        self.assertTrue(Path(result['cursor_path']).is_file())
        request['candidate'] = {'manifest': str(self.project / 'foreign.sqlite')}
        with self.assertRaises(ValueError):
            self.service.context('example', request, recipient)

    def test_context_output_and_resume_paths_cannot_escape_run(self):
        self.create()
        recipient = {'id': 'host', 'available_tokens': 100000, 'reserve_tokens': 0,
                     'max_chars': 100000, 'max_evaluations': 100}
        for output in ['../outside', str(self.project / 'outside')]:
            with self.subTest(output=output), self.assertRaises(ValueError):
                self.service.context('example', self.context_request(), recipient, out=output)
        with self.assertRaises(ValueError):
            self.service.context('example', self.context_request(), recipient, cursor='../outside.json')
        with self.assertRaises(ValueError):
            self.service.context('example', self.context_request(), recipient, embedding_result='../outside.json')

    def test_context_base_is_resolved_by_run_identity(self):
        self.create()
        self.service.create_run('src', 'candidate')
        recipient = {'id': 'host', 'available_tokens': 100000, 'reserve_tokens': 0,
                     'max_chars': 100000, 'max_evaluations': 100}
        result = self.service.context('candidate', self.context_request(), recipient, base_run_id='example')
        packet = json.loads(Path(result['path']).read_text(encoding='utf8'))
        self.assertIsNotNone(packet['engine_callee_drift'])

    def test_context_resume_has_same_input_through_cli_and_service(self):
        from snapshot_store import open_snapshot
        self.create()
        request = self.context_request()
        recipient = {'id': 'host', 'available_tokens': 100000, 'reserve_tokens': 1000,
                     'max_chars': 100000, 'max_evaluations': 100}
        first = self.service.context('example', request, recipient)
        via_service = self.service.context('example', request, recipient, out='service-resume', cursor=first['cursor'])
        manifest = self.run_dir / 'snapshot/manifest.sqlite'
        with open_snapshot(manifest) as store:
            authority = {'root': str(self.project), 'source_root': str(Path(store['root'])),
                         'read_boundary': [store['target']], 'write_boundary': []}
        for name, value in [('request', request), ('recipient', recipient), ('authority', authority)]:
            self.write('snapshot/' + name + '.json', json.dumps(value))
        run = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'snapshot.py'), 'context', str(manifest),
            '--request', str(manifest.parent / 'request.json'), '--recipient', str(manifest.parent / 'recipient.json'),
            '--authority', str(manifest.parent / 'authority.json'), '--out', str(manifest.parent / 'cli-resume'),
            '--cursor', first['cursor_path']], capture_output=True, text=True, encoding='utf8')
        self.assertEqual(run.returncode, 0, run.stderr)
        via_cli = json.loads(run.stdout)
        self.assertEqual(via_cli['sha256'], via_service['sha256'])
        self.assertEqual(via_cli['status'], via_service['status'])

    def test_context_git_subproject_cannot_read_sibling_source(self):
        import retrieval
        import source_reader
        subprocess.run(['git', 'init', str(self.project)], capture_output=True, check=True)
        (self.project / 'outside.py').write_bytes(b'OUTSIDE_PROJECT_SENTINEL = 999\n')
        self.create()
        request = self.context_request()
        request.update(query='selected', anchors=[], read_boundary=['src'])
        service = mcp_service.MapService(self.source)
        service.create_run('.', 'subproject')
        manifest = self.source / '.codebase-map/runs/subproject/snapshot/manifest.sqlite'
        retrieval.refresh_index(manifest, manifest.parent / 'retrieval.sqlite')
        recipient = {'id': 'host', 'available_tokens': 100000, 'reserve_tokens': 1000,
                     'max_chars': 100000, 'max_evaluations': 200}
        original = source_reader.read_packet
        def bounded(store, requests):
            self.assertTrue(all(r['path'].startswith('src/') for r in requests))
            return original(store, requests)
        with mock.patch.object(source_reader, 'read_packet', side_effect=bounded):
            result = service.context('subproject', request, recipient)
        self.assertEqual(result['status'], 'ready')
        packet = json.loads(Path(result['path']).read_text(encoding='utf8'))
        self.assertIn('return LIMIT', packet['input'])
        self.assertNotIn('OUTSIDE_PROJECT_SENTINEL', packet['input'])
        request['read_boundary'] = ['.']
        with self.assertRaises(ValueError):
            service.context('subproject', request, recipient)

    def test_engine_paths_are_run_bound_and_missing_pass_is_explicit(self):
        self.create()
        for value in ("../escape.sqlite", str(self.project / "escape.sqlite"), "manifest.sqlite"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.service.graph("example", engine_store=value)
        graph = self.service.graph("example", engine_store="engine-edges.sqlite")
        self.assertEqual(graph["edge_view"]["coverage"]["status"], "missing_store")
        impact = self.service.edit_impact("example", ["src/module.py::selected"],
                                          engine_store="engine-edges.sqlite")
        self.assertEqual(impact["freshness_basis"], "lexical")
        compared = self.service.stale_callers(
            "example", "example", base_engine_store="engine-edges.sqlite",
            candidate_engine_store="engine-edges.sqlite")
        self.assertEqual(compared["engine_callee_drift"]["status"], "unavailable")

    def test_engine_store_symlink_is_rejected_before_query(self):
        self.create()
        outside = self.project / "outside.sqlite"
        outside.write_bytes(b"not an engine store")
        try:
            (self.run_dir / "snapshot/engine-edges.sqlite").symlink_to(outside)
        except OSError:
            self.skipTest("host does not allow symlinks")
        with self.assertRaises(ValueError):
            self.service.graph("example")

    @property
    def run_dir(self):
        return self.project / ".codebase-map/runs/example"

    def write(self, name, value="# Read and cited evidence\n"):
        path = self.run_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8", newline="")

    def deliver(self, *phases):
        self.write("knowledge/navigation.md")
        self.write("knowledge/documentation-leads.md")
        for phase in phases:
            self.write(snapshot.PHASE_FILES[phase - 1])

    def test_scope_and_creation_prepare_real_snapshot_without_starting_an_agent(self):
        self.assertEqual(self.service.scope("src")["files"], 1)
        result = self.create()
        self.assertEqual(result["state"]["mode"], "classic")
        self.assertEqual(result["state"]["delivery"]["run_phases"], list(range(8)))
        self.assertFalse(result["check"]["complete"])
        from snapshot_store import open_snapshot, resolve_run_snapshot
        self.assertEqual(result["state"]["snapshot"]["format"], "sqlite")
        with open_snapshot(resolve_run_snapshot(self.run_dir, result["state"])) as manifest:
            self.assertEqual(manifest.file_count, 1)
        registry = json.loads((self.project / ".codebase-map/runs.json").read_text())
        self.assertEqual(registry["active"][0]["run_id"], "example")
        self.assertFalse((self.run_dir / "01-structure.md").exists())

    def test_scope_keeps_git_dot_and_forbidden_file_perimeter(self):
        (self.source / ".private").mkdir()
        (self.source / ".private/hidden.py").write_text("raise RuntimeError()")
        (self.source / ".env").write_text("sensitive=do-not-read")
        self.assertEqual(self.service.scope("src")["files"], 1)
        self.assertIn(".private", str(self.service.scope("src")["scope"]))

    def test_output_root_spellings_and_resolved_aliases_are_refused(self):
        self.create()
        for target in (".CODEBASE-MAP", ".Codebase-Map/runs/example", ".CODEBASE-XRAY"):
            with self.subTest(target=target), self.assertRaisesRegex(ValueError, "analysis output"):
                self.service.scope(target)
        alias = self.project / "archive-alias"
        alias.mkdir()
        resolved_root = self.service.root.resolve()
        original = Path.resolve
        def resolve(path, *args, **kwargs):
            if path == alias:
                return resolved_root
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, "resolve", resolve), self.assertRaisesRegex(ValueError, "analysis output"):
            self.service.scope("archive-alias")
        (self.project / ".github").mkdir()
        (self.project / ".github/ci.yml").write_text("name: Example\n")
        self.assertEqual(self.service.scope(".github")["files"], 1)

    def test_invalid_target_and_run_identity_make_no_output(self):
        for target in ("../outside", str(self.source), "src/../src", "src\\module.py", ".codebase-map"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                self.service.create_run(target, "example")
        for run_id in ("..", "../foreign", "a/b", "A", "con", "a:b", ""):
            with self.subTest(run_id=run_id), self.assertRaises(ValueError):
                self.service.create_run("src", run_id)
        self.assertFalse((self.project / ".codebase-map").exists())

    def test_flag_validation_and_collision_preserve_existing_run(self):
        for options in ({"depth": "huge"}, {"critical": 1}, {"comments": "yes"},
                        {"phase": True}, {"phase": 7}, {"stop_after": 0},
                        {"phase": 2, "docs_only": True}, {"phase": 2, "stop_after": 3}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.create(**options)
        self.create()
        before = (self.run_dir / "state.json").read_bytes()
        with self.assertRaises(ValueError):
            self.create()
        self.assertEqual((self.run_dir / "state.json").read_bytes(), before)

    def test_source_queries_use_own_manifest_and_reject_changed_bytes(self):
        self.create()
        packet = self.service.outline("example", pattern="selected")
        path = packet["items"][0]["path"]
        packet = self.service.read("example", [{"path": path, "symbols": ["selected"]}])
        self.assertIn("return LIMIT", json.dumps(packet))
        self.assertEqual(self.service.graph("example", [path])["schema"], "xray/source-graph/v1")
        self.module.write_text("def selected():\n    return 99\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.service.read("example", [{"path": path, "full_file": True}])

    def test_diff_is_read_only_and_observes_real_source_changes(self):
        self.create()
        before = {path.relative_to(self.run_dir).as_posix(): path.read_bytes()
                  for path in self.run_dir.rglob("*") if path.is_file()}
        self.assertTrue(self.service.diff("example")["unchanged"])
        self.module.write_text("LIMIT = 9\n\ndef selected():\n    return LIMIT\n", encoding="utf-8")
        result = self.service.diff("example")
        self.assertTrue(result["files"]["modified"])
        after = {path.relative_to(self.run_dir).as_posix(): path.read_bytes()
                 for path in self.run_dir.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_diff_reports_raw_newline_changes_even_when_claim_hashes_are_unchanged(self):
        self.module.write_bytes(b"def selected():\n    return 7\n")
        self.create()
        self.module.write_bytes(b"def selected():\r\n    return 7\r\n")
        result = self.service.diff("example")
        self.assertEqual(result["files"]["modified"], [])
        self.assertTrue(result["raw_changed"])
        self.assertFalse(result["unchanged"])

    def test_unknown_state_flag_and_unowned_delivery_path_are_refused(self):
        self.create()
        path = self.run_dir / "state.json"
        original = json.loads(path.read_text())
        state = json.loads(json.dumps(original))
        state["flags"]["run_arbitrary_command"] = "anything"
        path.write_text(json.dumps(state))
        with self.assertRaises(ValueError):
            self.service.status("example")
        state = original
        state["delivery"]["artifacts"]["../foreign.txt"] = {"phase": 1, "status": "produced"}
        path.write_text(json.dumps(state))
        with self.assertRaises(ValueError):
            self.service.status("example")

    def test_completed_checkpoint_requires_phase_outputs_and_keeps_run_open(self):
        self.create()
        before = (self.run_dir / "state.json").read_bytes()
        with self.assertRaises(ValueError):
            self.service.checkpoint("example", 1, "phase_completed")
        self.assertEqual((self.run_dir / "state.json").read_bytes(), before)
        self.deliver(1)
        result = self.service.checkpoint("example", 1, "phase_completed", "Structure delivered")
        self.assertIn(1, result["state"]["completed_phases"])
        self.assertEqual(result["state"]["status"], "in_progress")
        self.assertFalse(result["check"]["may_publish"])
        self.write("01-structure.md", "<!-- xray:stale -->\n# stale claim\n")
        with self.assertRaises(ValueError):
            self.service.checkpoint("example", 1, "phase_completed")

    def test_phase_zero_requires_both_knowledge_files_and_controls_are_strict(self):
        self.create(depth="lite")
        self.write("knowledge/navigation.md")
        with self.assertRaises(ValueError):
            self.service.checkpoint("example", 0, "phase_completed")
        self.write("knowledge/documentation-leads.md")
        self.service.checkpoint("example", 0, "phase_completed")
        for phase, event in ((3, "phase_started"), (True, "phase_started"),
                             (1, "complete"), (8, "phase_completed")):
            with self.subTest(phase=phase, event=event), self.assertRaises(ValueError):
                self.service.checkpoint("example", phase, event)

    def test_events_replay_with_cursor_and_cross_process_serialization(self):
        self.create()
        script = ("import sys;sys.path.insert(0,sys.argv[1]);from mcp_service import MapService;"
                  "MapService(sys.argv[2]).checkpoint('example',1,'phase_started',sys.argv[3])")
        def invoke(index):
            proc = subprocess.run([sys.executable, "-B", "-c", script, str(SCRIPTS),
                                   str(self.project), str(index)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(invoke, range(6)))
        first = self.service.events("example", limit=2)
        self.assertEqual(len(first["events"]), 2)
        self.assertTrue(first["has_more"])
        rest = self.service.events("example", after=first["next_cursor"])
        events = first["events"] + rest["events"]
        self.assertEqual([item["cursor"] for item in events], list(range(1, 8)))
        self.assertEqual({item["message"] for item in events[1:]}, {str(i) for i in range(6)})
        self.assertFalse(self.service.events("example", after=events[-1]["cursor"])["events"])

    def test_event_input_validation_and_read_after_restart(self):
        self.create()
        self.service.checkpoint("example", 1, "blocked", "Need host recovery")
        fresh = mcp_service.MapService(self.project)
        self.assertEqual(fresh.events("example")["events"][-1]["event"], "blocked")
        for values in ({"after": -1}, {"after": True}, {"limit": 0}, {"limit": 1001}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                fresh.events("example", **values)

    def test_invalid_checkpoint_event_and_read_requests_fail_as_value_errors(self):
        self.create()
        with self.assertRaises(ValueError):
            self.service.checkpoint("example", 1, ["phase_started"])
        for requests in (None, {}, [], [{"path": "../outside.py", "full_file": True}]):
            with self.subTest(requests=requests), self.assertRaises(ValueError):
                self.service.read("example", requests)

    def test_event_write_failure_preserves_observable_canonical_change(self):
        self.create()
        with mock.patch.object(mcp_service.MapService, "_event", side_effect=OSError("journal unavailable")):
            with self.assertRaises(OSError):
                self.service.checkpoint("example", 1, "phase_started")
        self.assertEqual(self.service.status("example")["state"]["current_phase"], 1)
        self.assertEqual(len(self.service.events("example")["events"]), 1)

    def test_queries_read_existing_team_run_without_creating_worker_or_phase_outputs(self):
        self.create()
        state = json.loads((self.run_dir / "state.json").read_text())
        state.update(mode="team", partitions=[], agents_spawned=[])
        state.pop("delivery")
        (self.run_dir / "state.json").write_text(json.dumps(state))
        self.service._command("prepare", self.run_dir)
        self.assertEqual(self.service.status("example")["state"]["mode"], "team")
        self.assertTrue(self.service.outline("example")["items"])
        self.assertFalse((self.run_dir / "08-interconnect-map.md").exists())

    def test_stop_preserves_evidence_and_resume_uses_existing_gate(self):
        self.create(stop_after=2)
        self.deliver(1, 2)
        prior = (self.run_dir / "01-structure.md").read_bytes()
        stopped = self.service.stop("example", "Host stopped workers")
        self.assertEqual(stopped["state"]["status"], "partial")
        self.assertEqual(self.service.runs()["registry"]["active"], [])
        resumed = self.service.resume("example")
        self.assertEqual(resumed["state"]["delivery"]["resume_from"], 3)
        self.assertEqual((self.run_dir / "01-structure.md").read_bytes(), prior)
        self.assertEqual(resumed["state"]["delivery"]["artifacts"]["01-structure.md"]["status"], "inherited")

    def test_resume_clears_blocker_and_aligns_progress_with_canonical_start(self):
        self.create()
        initial_flags = self.service.status("example")["state"]["flags"]
        self.service.checkpoint("example", 1, "blocked", "Worker cannot continue")
        self.service.stop("example", "Workers stopped")
        resumed = self.service.resume("example")
        self.assertEqual(resumed["state"]["status"], "in_progress")
        self.assertNotIn("blocker", resumed["state"])
        self.assertEqual(resumed["state"]["delivery"]["resume_from"], 0)
        self.assertEqual(resumed["state"]["current_phase"], 0)
        self.assertEqual(resumed["state"]["flags"], initial_flags)
        self.deliver(1, 2, 4)
        for phase in (1, 2, 4):
            self.service.checkpoint("example", phase, "phase_completed")
        before = (self.run_dir / "01-structure.md").read_bytes()
        self.service.stop("example", "Workers stopped again")
        resumed = self.service.resume("example", phase=2)
        self.assertEqual(resumed["state"]["current_phase"], 2)
        self.assertEqual(resumed["state"]["completed_phases"], [0, 1])
        self.assertEqual(resumed["state"]["delivery"]["artifacts"]["01-structure.md"]["status"], "inherited")
        self.assertEqual((self.run_dir / "01-structure.md").read_bytes(), before)
        self.assertEqual(resumed["state"]["flags"], initial_flags)

    def test_deleted_directory_keeps_history_diff_and_stop_available(self):
        self.create()
        recorded = self.service.events("example")
        shutil.rmtree(self.source)
        result = self.service.status("example")
        self.assertFalse(result["source_available"])
        self.assertIsNone(result["check"])
        self.assertTrue(result["check_unavailable"])
        self.assertEqual(self.service.events("example"), recorded)
        self.assertEqual(len(self.service.diff("example")["files"]["removed"]), 1)
        for operation in (lambda: self.service.read("example", [{"path": "module.py", "full_file": True}]),
                          lambda: self.service.graph("example"), lambda: self.service.resume("example"),
                          lambda: self.service.publish("example")):
            with self.assertRaises(ValueError):
                operation()
        self.assertEqual(self.service.stop("example", "Host workers stopped")["state"]["status"], "partial")
        self.assertEqual(self.service.runs()["registry"]["active"], [])

    def test_renamed_directory_with_forbidden_file_name_remains_observable(self):
        directory = self.project / "secret-service"
        directory.mkdir()
        (directory / "module.py").write_text("def selected():\n    return 1\n")
        self.service.create_run("secret-service", "example")
        recorded = self.service.events("example")
        directory.rename(self.project / "renamed-service")
        self.assertFalse(self.service.status("example")["source_available"])
        self.assertEqual(self.service.events("example"), recorded)
        self.assertEqual(self.service.stop("example", "Workers stopped")["state"]["status"], "partial")

    def test_missing_target_does_not_bypass_delivery_project_binding(self):
        self.create()
        shutil.rmtree(self.source)
        state = json.loads((self.run_dir / "state.json").read_text())
        state["delivery"]["binding"]["project"] = str(self.project.parent / "foreign")
        (self.run_dir / "state.json").write_text(json.dumps(state))
        with self.assertRaises(ValueError):
            self.service.status("example")

    def test_deleted_single_file_and_directory_in_standalone_and_nested_repositories(self):
        for mode in ("standalone", "nested"):
            for kind in ("file", "directory"):
                run_id = f"{mode}-{kind}"
                directory = self.project / run_id
                directory.mkdir()
                source = directory / "module.py"
                source.write_text("def selected():\n    return 1\n")
                if mode == "nested":
                    if not shutil.which("git"):
                        continue
                    subprocess.run(["git", "init", str(directory)], check=True, capture_output=True)
                target = f"{run_id}/module.py" if kind == "file" else run_id
                with self.subTest(mode=mode, kind=kind), mock.patch.dict(
                        os.environ, {"GIT_CEILING_DIRECTORIES": str(self.project.parent)}):
                    self.service.create_run(target, run_id)
                    source.unlink() if kind == "file" else shutil.rmtree(directory)
                    result = self.service.status(run_id)
                    self.assertFalse(result["source_available"])
                    self.assertIsNone(result["check"])
                    self.assertEqual(len(self.service.diff(run_id)["files"]["removed"]), 1)
                    self.assertTrue(self.service.events(run_id)["events"])
                    self.assertEqual(self.service.stop(run_id, "Workers stopped")["state"]["status"], "partial")

    def test_existing_absolute_stored_targets_keep_canonical_classic_and_team_compatibility(self):
        self.create()
        for mode in ("classic", "team"):
            state = json.loads((self.run_dir / "state.json").read_text())
            state.update(target=str(self.source), mode=mode)
            if mode == "team":
                state.update(partitions=[], agents_spawned=[])
            state.pop("delivery")
            (self.run_dir / "state.json").write_text(json.dumps(state))
            self.service._command("prepare", self.run_dir)
            self.assertEqual(snapshot.check_delivery(self.run_dir)["mode"], mode)
            result = self.service.status("example")
            self.assertEqual(result["state"]["mode"], mode)
            self.assertEqual(result["state"]["target"], str(self.source))
            self.assertEqual(self.service.runs()["runs"][0]["run_id"], "example")
        for operation in (lambda: self.service.scope(str(self.source)),
                          lambda: self.service.create_run(str(self.source), "foreign")):
            with self.assertRaises(ValueError):
                operation()
        state = json.loads((self.run_dir / "state.json").read_text())
        state["target"] = str(self.project.parent / "foreign")
        state["delivery"]["binding"]["target"] = state["target"]
        (self.run_dir / "state.json").write_text(json.dumps(state))
        with self.assertRaises(ValueError):
            self.service.status("example")

    def test_resume_refuses_changed_source_without_rewriting_existing_state(self):
        self.create(stop_after=2)
        self.deliver(1, 2)
        self.module.write_text("def other():\n    return 1\n", encoding="utf-8")
        before = (self.run_dir / "state.json").read_bytes()
        with self.assertRaises(ValueError):
            self.service.resume("example")
        self.assertEqual((self.run_dir / "state.json").read_bytes(), before)

    def test_publish_requires_real_delivery_and_rejects_changed_source(self):
        self.create()
        self.assertFalse(self.service.publish("example")["published"])
        self.assertFalse((self.project / ".codebase-map/07-final-report.md").exists())
        self.deliver(1, 2, 3, 4, 5, 6, 7)
        self.assertTrue(self.service.publish("example")["published"])
        self.assertEqual(self.service.status("example")["state"]["status"], "complete")
        self.assertEqual(self.service.runs()["registry"]["latest_completed"], "example")
        for operation in (lambda: self.service.stop("example", "stale stop"),
                          lambda: self.service.checkpoint("example", 1, "phase_started")):
            with self.assertRaises(ValueError):
                operation()
        self.module.write_text("def changed():\n    pass\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.service.publish("example")

    def test_artifact_reads_declared_content_and_refuses_unowned_paths(self):
        self.create()
        self.deliver(1)
        self.assertEqual(self.service.artifact("example", "01-structure.md")["content"],
                         "# Read and cited evidence\n")
        self.write("foreign.txt", "not a declared artifact")
        for name in ("../src/module.py", "foreign.txt", "snapshot/manifest.json", "knowledge/", "state.json"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.service.artifact("example", name)

    def test_artifact_content_is_capped_with_whole_file_digest(self):
        self.create()
        self.deliver(1)
        body = "x" * (mcp_service.MAX_ARTIFACT_BYTES + 10)
        self.write("01-structure.md", body)
        packet = self.service.artifact("example", "01-structure.md")
        self.assertTrue(packet["truncated"])
        self.assertEqual(packet["bytes"], len(body))
        self.assertEqual(len(packet["content"]), mcp_service.MAX_ARTIFACT_BYTES)
        self.assertEqual(packet["sha256"], __import__("hashlib").sha256(body.encode()).hexdigest())

    def test_outline_pattern_is_literal_not_a_regular_expression(self):
        self.create()
        self.assertTrue(self.service.outline("example", pattern="SELECTED|absent")["items"])
        self.assertFalse(self.service.outline("example", pattern="sel.cted")["items"])
        self.assertFalse(self.service.outline("example", pattern="(a+)+$")["items"])

    def test_runs_lists_a_damaged_run_without_hiding_the_others(self):
        self.create()
        damaged = self.project / ".codebase-map/runs/damaged"
        damaged.mkdir()
        (damaged / "state.json").write_text("{not json", encoding="utf-8")
        listed = {item["run_id"]: item for item in self.service.runs()["runs"]}
        self.assertTrue(listed["example"]["readable"])
        self.assertFalse(listed["damaged"]["readable"])
        self.assertIn("error", listed["damaged"])

    def test_service_state_writes_keep_concurrent_worker_fields(self):
        self.create()
        self.deliver(1)
        original = mcp_service._json

        def worker_writes_first(path):
            value = original(path)
            if path.name == "state.json" and not getattr(worker_writes_first, "done", False):
                worker_writes_first.done = True
                fresh = original(path)
                fresh["files_created"] = ["worker-note.md"]
                mcp_service._write(path, fresh)
            return value

        with mock.patch.object(mcp_service, "_json", worker_writes_first):
            self.service.checkpoint("example", 1, "phase_completed")
        state = json.loads((self.run_dir / "state.json").read_text())
        self.assertEqual(state["files_created"], ["worker-note.md"])
        self.assertIn(1, state["completed_phases"])

    def test_checkpoint_never_moves_progress_backwards(self):
        self.create()
        self.service.checkpoint("example", 3, "phase_started")
        result = self.service.checkpoint("example", 1, "phase_started")
        self.assertEqual(result["state"]["current_phase"], 3)

    def test_published_run_is_not_resumed_and_partial_run_is_not_published(self):
        self.create()
        self.deliver(1, 2, 3, 4, 5, 6, 7)
        self.service.stop("example", "Workers stopped")
        with self.assertRaisesRegex(ValueError, "in-progress"):
            self.service.publish("example")
        self.service.resume("example", phase=7)
        self.assertTrue(self.service.publish("example")["published"])
        with self.assertRaisesRegex(ValueError, "published run"):
            self.service.resume("example")

    def test_failed_preparation_leaves_no_run_directory(self):
        with mock.patch.object(mcp_service.snapshot, "update_registration", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.create()
        self.assertFalse(self.run_dir.exists())
        self.assertEqual(self.create()["state"]["run_id"], "example")

    def test_event_journal_is_bounded(self):
        self.create()
        with mock.patch.object(mcp_service, "MAX_EVENTS", 1):
            with self.assertRaisesRegex(ValueError, "event journal"):
                self.service.checkpoint("example", 1, "phase_started")

    def test_scope_and_status_report_the_bound_project(self):
        self.assertEqual(self.service.scope("src")["project_root"], self.project.as_posix())
        self.create()
        self.assertEqual(self.service.status("example")["project_root"], self.project.as_posix())

    def test_helpers_never_run_a_git_from_the_project_or_a_relative_path(self):
        import tree_scope
        fake = self.project / ("git.exe" if os.name == "nt" else "git")
        fake.write_text("planted", encoding="utf-8")
        with mock.patch.dict(os.environ, {"PATH": os.pathsep.join([".", str(self.project.name)])}):
            self.assertIsNone(tree_scope.git_executable())
        self.assertEqual(mcp_service.SCRIPT_DIR, SCRIPTS.resolve())

    def test_registry_lock_left_by_a_crashed_holder_does_not_block(self):
        self.create()
        (self.project / ".codebase-map/.registry.lock").write_text("stale", encoding="utf-8")
        self.service.stop("example", "Workers stopped")
        self.assertEqual(self.service.runs()["registry"]["active"], [])

    def test_new_credential_files_are_forbidden(self):
        for name in ("prod-service-account.json", "kubeconfig", "main.tfstate", "main.tfstate.backup",
                     "release.keystore", "app.jks"):
            with self.subTest(name=name):
                self.assertTrue(snapshot.is_forbidden(name))

    def test_foreign_manifest_and_state_bindings_are_refused_even_for_outline(self):
        # Explicit JSON compatibility remains an upstream-only supported format.
        self.create(format="json")
        path = self.run_dir / "snapshot/manifest.json"
        original = path.read_text()
        manifest = json.loads(original)
        manifest["root"] = self.project.parent.as_posix()
        path.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            self.service.outline("example")
        path.write_text(original)
        state = json.loads((self.run_dir / "state.json").read_text())
        state["target"] = "../outside"
        (self.run_dir / "state.json").write_text(json.dumps(state))
        with self.assertRaises(ValueError):
            self.service.status("example")

    def test_source_and_artifact_links_are_refused_before_reading(self):
        outside = self.project / "outside.py"
        outside.write_text("raise RuntimeError('must not read')")
        linked = self.source / "linked.py"
        try:
            linked.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable")
        with self.assertRaises(ValueError):
            self.create()
        linked.unlink()
        self.create()
        (self.run_dir / "01-structure.md").symlink_to(outside)
        with self.assertRaises(ValueError):
            self.service.artifact("example", "01-structure.md")

    def test_windows_reparse_path_is_refused_without_symlink_privileges(self):
        original = Path.lstat
        def lstat(path, *args, **kwargs):
            info = original(path, *args, **kwargs)
            if path == self.source:
                return type("Reparse", (), {"st_mode": info.st_mode, "st_file_attributes": 0x400})()
            return info
        with mock.patch.object(Path, "lstat", lstat), self.assertRaises(ValueError):
            self.service.scope("src")

    def test_legacy_pending_migration_is_read_only_and_write_preflight_migrates(self):
        old = self.project / ".codebase-xray"
        old.mkdir()
        (old / "runs.json").write_text('{"schema":2,"active":[],"latest_completed":null}')
        (old / "07-final-report.md").write_text("# Previous report\n")
        with self.assertRaisesRegex(ValueError, "migration"):
            self.service.runs()
        self.assertTrue((old / "07-final-report.md").exists())
        self.create()
        self.assertEqual((self.project / ".codebase-map/07-final-report.md").read_text(), "# Previous report\n")


class CustomStoreTests(unittest.TestCase):
    STORE = ".app/codebase-map"

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="map-mcp-store-")
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name).resolve()
        self.source = self.project / "src"
        self.source.mkdir()
        self.module = self.source / "module.py"
        self.module.write_text("LIMIT = 7\n\ndef selected():\n    return LIMIT\n", encoding="utf-8")
        self.service = mcp_service.MapService(self.project, self.STORE)

    @property
    def store(self):
        return self.project / self.STORE

    @property
    def run_dir(self):
        return self.store / "runs/example"

    def deliver(self, *phases):
        for name in ("knowledge/navigation.md", "knowledge/documentation-leads.md",
                     *(snapshot.PHASE_FILES[phase - 1] for phase in phases)):
            path = self.run_dir / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Read and cited evidence\n", encoding="utf-8", newline="")

    def test_custom_store_runs_the_canonical_lifecycle_without_the_default_root(self):
        self.assertEqual(self.service.runs(), {"runs": [], "registry": None})
        self.assertFalse(self.store.exists())
        self.service.create_run("src", "example")
        self.assertEqual(json.loads((self.store / snapshot.STORE_MARKER).read_text()),
                         {"schema": snapshot.STORE_SCHEMA, "store": self.STORE})
        self.assertEqual(self.service.status("example")["state"]["delivery"]["binding"]["project"],
                         self.project.as_posix())
        self.deliver(1, 2, 3, 4, 5, 6, 7)
        self.assertTrue(self.service.publish("example")["published"])
        self.assertTrue((self.store / "07-final-report.md").is_file())
        self.assertEqual(self.service.runs()["registry"]["latest_completed"], "example")
        self.assertFalse((self.project / ".codebase-map").exists())
        reopened = mcp_service.MapService(self.project, self.STORE)
        self.assertEqual(reopened.status("example")["state"]["status"], "complete")
        self.assertEqual(mcp_service.MapService(self.project).runs(), {"runs": [], "registry": None})

    def test_standalone_cli_binds_the_custom_store_through_its_marker(self):
        self.service.create_run("src", "example")
        self.deliver(1)
        proc = subprocess.run([sys.executable, "-B", str(SCRIPTS / "snapshot.py"), "check",
                               str(self.run_dir), "--json"], capture_output=True, text=True,
                              cwd=SCRIPTS)
        self.assertEqual(json.loads(proc.stdout)["mode"], "classic", proc.stderr)
        _, root, _ = snapshot._run_context(self.run_dir)
        self.assertEqual(snapshot.store_project(root), self.project)

    def test_store_inside_an_occupied_dot_directory_and_bom_marker_bind_the_project(self):
        (self.project / ".app").mkdir()
        (self.project / ".app/settings.json").write_text("{}")
        self.service.create_run("src", "example")
        marker = self.store / snapshot.STORE_MARKER
        marker.write_text(marker.read_text(encoding="utf-8"), encoding="utf-8-sig")
        _, root, _ = snapshot._run_context(self.run_dir)
        self.assertEqual(snapshot.store_project(root), self.project)
        self.deliver(1, 2, 3, 4, 5, 6, 7)
        proc = subprocess.run([sys.executable, "-B", str(SCRIPTS / "snapshot.py"), "publish",
                               str(self.run_dir)], capture_output=True, text=True, cwd=SCRIPTS)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((self.store / "07-final-report.md").is_file())
        self.assertTrue((self.project / ".app/settings.json").is_file())

    def test_unmarked_or_foreign_marked_store_is_refused(self):
        self.service.create_run("src", "example")
        marker = self.store / snapshot.STORE_MARKER
        marker.write_text(json.dumps({"schema": snapshot.STORE_SCHEMA, "store": ".other/codebase-map"}))
        with self.assertRaises(ValueError):
            snapshot._run_context(self.run_dir)
        with self.assertRaisesRegex(ValueError, "another store"):
            self.service.status("example")
        marker.unlink()
        with self.assertRaises(ValueError):
            snapshot._run_context(self.run_dir)
        with self.assertRaisesRegex(ValueError, "without its marker"):
            self.service.status("example")
        occupied = self.project / ".occupied"
        occupied.mkdir()
        (occupied / "notes.txt").write_text("someone else's directory")
        with self.assertRaisesRegex(ValueError, "without its marker"):
            mcp_service.MapService(self.project, ".occupied").create_run("src", "example")
        self.assertEqual(sorted(path.name for path in occupied.iterdir()), ["notes.txt"])

    def test_invalid_store_paths_are_refused_at_binding(self):
        for store in ("", ".", "..", "../outside", "app/map", "/abs", "C:/map", ".app\\map",
                      ".app/../map", ".app//map", ".codebase-map", ".CODEBASE-XRAY/map",
                      ".git/map", ".app/con", ".app/map.", ".app/ map", ".app/CONIN$",
                      ".app/com\u00b9", ".app/m?p", ".app/m\x01p", 7):
            with self.subTest(store=store), self.assertRaises(ValueError):
                mcp_service.MapService(self.project, store)

    def test_store_cannot_be_a_source_target_and_skips_legacy_migration(self):
        legacy = self.project / ".codebase-xray"
        legacy.mkdir()
        (legacy / "runs.json").write_text('{"schema":2,"active":[],"latest_completed":null}')
        self.service.create_run("src", "example")
        for target in (".app", ".APP/codebase-map", ".app/codebase-map/runs/example"):
            with self.subTest(target=target), self.assertRaisesRegex(ValueError, "analysis output"):
                self.service.scope(target)
        self.assertTrue((legacy / "runs.json").is_file())
        self.assertFalse((self.project / ".codebase-map").exists())


if __name__ == "__main__":
    unittest.main()
