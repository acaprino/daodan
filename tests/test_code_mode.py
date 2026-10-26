"""Behavioral checks of the real local Code Mode execution boundary."""

import asyncio
from dataclasses import replace
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map-method/scripts"
sys.path.insert(0, str(SCRIPTS))
try:
    import code_mode
except ImportError:
    code_mode = None

DENO = os.environ.get("DAODAN_TEST_DENO") or shutil.which("deno")


class RuntimeSelectionTests(unittest.TestCase):
    def test_missing_runtime_is_an_explicit_configuration_error(self):
        self.assertIsNotNone(code_mode, "local Code Mode has not been implemented")
        with self.assertRaisesRegex(code_mode.CodeModeError, "Deno"):
            code_mode.DenoExecutor("/missing/daodan-deno")

    def test_project_executable_and_relative_paths_cannot_select_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            executable = project / "deno"
            executable.write_text("untrusted project executable", encoding="utf8")
            executable.chmod(0o755)
            with self.assertRaisesRegex(code_mode.CodeModeError, "outside the project"):
                code_mode.DenoExecutor(executable, project_root=project)
            with self.assertRaisesRegex(code_mode.CodeModeError, "absolute path"):
                code_mode.DenoExecutor("./deno", project_root=project)
            with patch.dict(os.environ, {"PATH": "."}):
                with self.assertRaises(code_mode.CodeModeError):
                    code_mode.DenoExecutor(project_root=project)


@unittest.skipUnless(DENO, "requires Deno; set DAODAN_TEST_DENO to its executable")
class CodeModeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.assertIsNotNone(code_mode, "local Code Mode has not been implemented")
        self.executor = code_mode.DenoExecutor(DENO)

    async def run_code(self, code, *, catalog=(), call=None, names=(), limits=None):
        if limits is not None:
            self.executor = code_mode.DenoExecutor(DENO, limits=limits)
        return await self.executor.run(code, catalog=list(catalog), call_tool=call,
                                       allowed_tools=set(names))

    async def test_discovery_selects_schemas_without_operation_access(self):
        result = await self.run_code(
            'async () => catalog.filter(t => t.name.includes("read"))',
            catalog=[{"name": "read_source", "inputSchema": {"type": "object"}},
                     {"name": "scope", "inputSchema": {"type": "object"}}],
        )
        self.assertEqual(result["value"], [{"name": "read_source", "inputSchema": {"type": "object"}}])
        self.assertEqual(result["calls"], [])

    async def test_composition_keeps_intermediate_data_out_of_result(self):
        async def call(name, arguments):
            if name == "list_items":
                return {"items": [{"id": 1, "active": True}, {"id": 2, "active": False}],
                        "irrelevant": "intermediate-only-" * 1000}
            self.assertEqual((name, arguments), ("details", {"id": 1}))
            return {"name": "selected", "unneeded": [1, 2, 3]}

        result = await self.run_code('''async () => {
            const items = (await tools.list_items({})).items.filter(x => x.active);
            const names = [];
            for (const item of items) names.push((await tools.details({id: item.id})).name);
            return names;
        }''', call=call, names=("list_items", "details"))
        self.assertEqual(result["value"], ["selected"])
        self.assertEqual([item["tool"] for item in result["calls"]], ["list_items", "details"])
        self.assertTrue(all(item["ok"] for item in result["calls"]))
        self.assertNotIn("intermediate-only", json.dumps(result))
        self.assertGreater(result["stats"]["intermediate_bytes"], 15000)
        self.assertEqual(result["stats"]["selected_value_bytes"], len(b'["selected"]'))
        self.assertEqual(result["stats"]["receipt_bytes"],
                         len(json.dumps(result["calls"], separators=(",", ":")).encode()))

    async def test_trailing_stdout_after_result_cannot_block_process_reaping(self):
        # Inject a runner that deterministically produces the result/flood race
        # a Worker can trigger by posting a result and then writing raw stdout.
        with tempfile.TemporaryDirectory() as temporary:
            runner = Path(temporary) / "code_mode_runner.js"
            runner.write_text('''const input = new Uint8Array(8192);
const count = await Deno.stdin.read(input);
const {token} = JSON.parse(new TextDecoder().decode(input.subarray(0, count)));
const frame = new TextEncoder().encode(JSON.stringify({token, type: "result", value: 1}) + "\\n");
await Deno.stdout.write(frame);
const flood = new Uint8Array(1000000).fill(65);
let written = 0;
while (written < flood.length) written += await Deno.stdout.write(flood.subarray(written));
''', encoding="utf8")
            with patch.object(code_mode, "__file__", str(Path(temporary) / "code_mode.py")):
                with self.assertRaisesRegex(code_mode.CodeModeError, "output after final result"):
                    await asyncio.wait_for(self.run_code('async () => 1', limits=replace(
                        code_mode.Limits(), timeout_seconds=.3)), timeout=2)

    async def test_invalid_unicode_after_a_call_preserves_its_receipt(self):
        for ending in (r'return "\ud800";', r'await tools.atomic({text: "\ud800"});',
                       r'throw "\ud800";'):
            with self.subTest(ending=ending):
                completed = []

                async def atomic(name, arguments):
                    completed.append(arguments)
                    return {"saved": True}

                with self.assertRaises(code_mode.CodeModeError) as caught:
                    await self.run_code('async () => { await tools.atomic({}); ' + ending + ' }',
                                        call=atomic, names=("atomic",))
                self.assertEqual(completed, [{}])
                self.assertTrue(caught.exception.calls[0]["ok"])
                self.assertIn("admitted calls", str(caught.exception))
                str(caught.exception).encode("utf-8")

    async def test_direct_host_capabilities_are_denied(self):
        with tempfile.TemporaryDirectory() as temporary:
            secret = Path(temporary) / "private.txt"
            secret.write_text("must-not-be-read", encoding="utf8")
            operations = [
                f"await Deno.readTextFile({json.dumps(str(secret))})",
                f"await Deno.writeTextFile({json.dumps(str(secret))}, 'modified')",
                "await fetch('http://127.0.0.1:9/')",
                "Deno.env.get('PATH')",
                "await new Deno.Command('echo', {args: ['unsafe']}).output()",
                "Deno.dlopen('/missing/native-library', {})",
                "await import('https://example.com/untrusted.js')",
            ]
            for operation in operations:
                with self.subTest(operation=operation):
                    result = await self.run_code(
                        f'async () => {{ try {{ {operation}; return "allowed"; }} '
                        'catch (error) { return "denied"; } }')
                    self.assertEqual(result["value"], "denied")
            self.assertEqual(secret.read_text(encoding="utf8"), "must-not-be-read")

    async def test_worker_cannot_forge_authenticated_stdout(self):
        with self.assertRaisesRegex(code_mode.CodeModeError, "protocol"):
            await self.run_code('''async () => {
                Deno.stdout.writeSync(new TextEncoder().encode('{"type":"result","value":"forged"}\\n'));
                return 3;
            }''')

    async def test_unknown_operation_cannot_cross_the_bridge(self):
        admitted = []

        async def call(name, arguments):
            admitted.append(name)
            return {}

        with self.assertRaises(code_mode.CodeModeError):
            await self.run_code('''async () => {
                self.postMessage({type: "call", id: 1, name: "forbidden_write", arguments: {}});
                return await new Promise(() => {});
            }''', call=call, names=("read",))
        self.assertEqual(admitted, [])

    async def test_infinite_loop_and_unresolved_promise_have_deadlines(self):
        limits = replace(code_mode.Limits(), timeout_seconds=0.4)
        for code in ('async () => { while (true) {} }',
                     'async () => await new Promise(() => {})'):
            with self.subTest(code=code):
                start = time.monotonic()
                with self.assertRaisesRegex(code_mode.CodeModeError, "deadline"):
                    await self.run_code(code, limits=limits)
                self.assertLess(time.monotonic() - start, 4)

    async def test_timeout_waits_for_an_admitted_operation_and_stops_next_call(self):
        completed = []

        async def call(name, arguments):
            await asyncio.sleep(0.6)
            completed.append(name)
            return {"done": True}

        with self.assertRaises(code_mode.CodeModeError) as error:
            await self.run_code('''async () => {
                await tools.atomic({}); await tools.atomic({}); return true;
            }''', call=call, names=("atomic",),
                limits=replace(code_mode.Limits(), timeout_seconds=0.3))
        self.assertEqual(completed, ["atomic"])
        self.assertEqual(len(error.exception.calls), 1)
        self.assertTrue(error.exception.calls[0]["ok"])

    async def test_call_and_output_limits_fail_explicitly(self):
        admitted = []

        async def call(name, arguments):
            admitted.append(name)
            return {"value": 1}

        with self.assertRaisesRegex(code_mode.CodeModeError, "call limit"):
            await self.run_code('''async () => {
                for (let i=0; i<3; i++) await tools.read({}); return true;
            }''', call=call, names=("read",),
                limits=replace(code_mode.Limits(), max_calls=2))
        self.assertEqual(admitted, ["read", "read"])
        with self.assertRaisesRegex(code_mode.CodeModeError, "output"):
            await self.run_code('async () => "x".repeat(20000)',
                limits=replace(code_mode.Limits(), max_output_bytes=1024))

    async def test_call_limit_reaps_a_process_with_queued_stdout(self):
        processes = []
        create_process = asyncio.create_subprocess_exec

        async def capture_process(*args, **kwargs):
            process = await create_process(*args, **kwargs)
            processes.append(process)
            return process

        async def call(name, arguments):
            # Let the worker fill the protocol pipe while an admitted call runs.
            await asyncio.sleep(0.25)
            return True

        with patch("code_mode.asyncio.create_subprocess_exec", capture_process):
            task = asyncio.create_task(self.run_code('''async () => {
                for (let id=1; id<=10000; id++)
                    self.postMessage({type: "call", id, name: "read", arguments: {}});
                return await new Promise(() => {});
            }''', call=call, names=("read",),
                limits=replace(code_mode.Limits(), max_calls=1, timeout_seconds=2)))
            try:
                completed, _ = await asyncio.wait({task}, timeout=3)
                self.assertIn(task, completed, "cleanup blocked on unread protocol output")
                with self.assertRaisesRegex(code_mode.CodeModeError, "call limit") as error:
                    task.result()
                self.assertEqual(len(error.exception.calls), 1)
                self.assertTrue(error.exception.calls[0]["ok"])
                self.assertIsNotNone(processes[0].returncode)
                self.assertTrue(processes[0].stdout.at_eof())
                self.assertTrue(processes[0].stderr.at_eof())
            finally:
                if not task.done():
                    task.cancel()
                await asyncio.gather(task, return_exceptions=True)
                # A regressed cleanup must not strand resources in the test loop.
                for process in processes:
                    if process.returncode is None:
                        process.kill()
                    while await process.stdout.read(65536):
                        pass
                    await process.wait()

    async def test_cancellation_finishes_atomic_call_and_drains_queued_stdout(self):
        processes = []
        create_process = asyncio.create_subprocess_exec
        admitted = asyncio.Event()
        completed = []

        async def capture_process(*args, **kwargs):
            process = await create_process(*args, **kwargs)
            processes.append(process)
            return process

        async def call(name, arguments):
            admitted.set()
            await asyncio.sleep(0.35)
            completed.append(name)
            return True

        with patch("code_mode.asyncio.create_subprocess_exec", capture_process):
            task = asyncio.create_task(self.run_code('''async () => {
                for (let id=1; id<=10000; id++)
                    self.postMessage({type: "call", id, name: "atomic", arguments: {}});
                return await new Promise(() => {});
            }''', call=call, names=("atomic",)))
            try:
                await asyncio.wait_for(admitted.wait(), 3)
                await asyncio.sleep(0.2)
                task.cancel()
                await asyncio.sleep(0.02)
                task.cancel()
                finished, _ = await asyncio.wait({task}, timeout=3)
                self.assertIn(task, finished, "cancellation cleanup did not finish")
                with self.assertRaises(asyncio.CancelledError):
                    task.result()
                self.assertEqual(completed, ["atomic"])
                self.assertIsNotNone(processes[0].returncode)
                self.assertTrue(processes[0].stdout.at_eof())
                self.assertTrue(processes[0].stderr.at_eof())
            finally:
                if not task.done():
                    task.cancel()
                await asyncio.gather(task, return_exceptions=True)
                for process in processes:
                    if process.returncode is None:
                        process.kill()
                    while await process.stdout.read(65536):
                        pass
                    await process.wait()

    async def test_caught_tool_failure_remains_in_broker_receipts(self):
        async def call(name, arguments):
            raise ValueError("source is stale")

        result = await self.run_code('''async () => {
            try { await tools.read({}); } catch (_) {} return "handled";
        }''', call=call, names=("read",))
        self.assertEqual(result["value"], "handled")
        self.assertFalse(result["calls"][0]["ok"])
        self.assertIn("source is stale", result["calls"][0]["error"])

    async def test_executions_do_not_share_state_or_inherit_permission_broker(self):
        await self.run_code('async () => { globalThis.previousRun = 7; return true; }')
        with patch.dict(os.environ, {"DENO_PERMISSION_BROKER_PATH": "/missing/broker"}):
            result = await self.run_code('async () => typeof globalThis.previousRun')
        self.assertEqual(result["value"], "undefined")


if __name__ == "__main__":
    unittest.main()
