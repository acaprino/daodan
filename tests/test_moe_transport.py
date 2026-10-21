"""Transport contract: no paid request without a bounded original payload."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

SERVER = Path(__file__).resolve().parents[1] / "plugins/moe/skills/multi-model-deliberation/scripts/server.py"

class MoeTransportTests(unittest.TestCase):
    def load(self):
        class MCP:
            def __init__(self, *args, **kwargs): pass
            def tool(self): return lambda function: function
        with patch.object(sys, "path", [str(SERVER.parent), *sys.path]), patch.dict(sys.modules, {"mcp": types.ModuleType("mcp"), "mcp.server": types.ModuleType("mcp.server"), "mcp.server.mcpserver": types.SimpleNamespace(MCPServer=MCP)}):
            spec = importlib.util.spec_from_file_location("moe_transport_test", SERVER)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

    def test_exact_payload_digest_limits_and_no_retry(self):
        module = self.load()
        with tempfile.TemporaryDirectory() as folder, patch.object(module.Path, "cwd", return_value=Path(folder)), patch.dict(os.environ, {"MOE_API_BASE": "https://fixture.invalid/v1", "MOE_API_KEY": "fixture"}, clear=True):
            directory=Path(folder)/".moe/run"; directory.mkdir(parents=True)
            source=directory/"packet.md"; source.write_bytes(b"Original\r\nconstraints")
            requests=[]
            def call(path, body=None, binding=""):
                requests.append((path,body,binding))
                return {"choices":[{"message":{"role":"assistant","content":"Proposal"},"finish_reason":"stop"}],"model":"expert-a","usage":{"total_tokens":42}}
            with patch.object(module,"_call",side_effect=call):
                result=module.moe_ask("expert-a","Solve the problem",str(source))
                self.assertEqual(result["sent_bytes"],len(source.read_bytes()))
                self.assertEqual(result["text"],"Proposal")
                self.assertEqual(requests[0][1]["messages"][1]["content"],"Original\r\nconstraints")
                self.assertEqual(requests[0][1]["max_tokens"],4096)
                self.assertIn("error",module.moe_ask("expert-a","Solve",str(source),max_output_tokens=99999))
                self.assertEqual(len(requests),1)
            with patch.object(module,"_call",side_effect=TimeoutError("uncertain")) as transport:
                self.assertIn("error",module.moe_ask("expert-a","Solve",str(source)))
                self.assertEqual(transport.call_count,1)

    def test_payload_cannot_escape_run_root_or_follow_links(self):
        module=self.load()
        with tempfile.TemporaryDirectory() as folder, patch.object(module.Path,"cwd",return_value=Path(folder)), patch.dict(os.environ,{},clear=True):
            root=Path(folder); outside=root/"private.md"; outside.write_text("secret")
            run=root/".moe/run"; run.mkdir(parents=True)
            with patch.object(module,"_call") as transport:
                self.assertIn("error",module.moe_ask("a","s",str(outside)))
                os.link(outside,run/"linked.md")
                self.assertIn("error",module.moe_ask("a","s",str(run/"linked.md")))
                self.assertFalse(transport.called)

    def test_payload_replaced_after_validation_is_never_sent(self):
        module = self.load()
        with tempfile.TemporaryDirectory() as folder, patch.object(module.Path, "cwd", return_value=Path(folder)), patch.dict(os.environ, {}, clear=True):
            root = Path(folder)
            packet = root / ".moe/run/packet.md"
            packet.parent.mkdir(parents=True)
            packet.write_text("approved")
            outside = root / "outside.md"
            outside.write_text("outside scope fixture")
            original = Path.is_file
            swapped = []
            def replace_after_check(path):
                result = original(path)
                if path == packet and not swapped:
                    packet.unlink()
                    os.link(outside, packet)
                    swapped.append(True)
                return result
            with patch.object(module.Path, "is_file", replace_after_check), patch.object(module, "_call") as transport:
                result = module.moe_ask("expert-a", "Solve", str(packet))
                self.assertEqual(swapped, [True])
                self.assertIn("error", result)
                self.assertFalse(transport.called)

    def test_proposal_reserves_space_before_spending(self):
        module = self.load()
        with tempfile.TemporaryDirectory() as folder, patch.object(module.Path, "cwd", return_value=Path(folder)):
            packet = Path(folder) / ".moe/run/brief.md"
            packet.parent.mkdir(parents=True)
            packet.write_bytes(b"B" * 6001)
            with patch.object(module, "_call") as transport:
                self.assertIn("error", module.moe_ask("expert-a", "Solve", str(packet)))
                self.assertFalse(transport.called)

    def test_full_reserved_replies_fit_the_reciprocal_payload(self):
        module = self.load()
        with tempfile.TemporaryDirectory() as folder, patch.object(module.Path, "cwd", return_value=Path(folder)):
            run = Path(folder) / ".moe/run"
            run.mkdir(parents=True)
            brief = run / "brief.md"
            brief.write_bytes(b"B" * 6000)
            def answer(path, body=None, binding=""):
                return {"model": body["model"], "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": "R" * 8000}}]}
            with patch.object(module, "_call", side_effect=answer) as transport:
                a = module.moe_ask("expert-a", "Solve", str(brief))
                b = module.moe_ask("expert-b", "Solve", str(brief), peer_model=a["model"])
                self.assertNotIn("error", b)
                critique = run / "critique.md"
                text = brief.read_text() + "\n\nMODEL " + a["model"] + "\n" + a["text"] + "\n\nMODEL " + b["model"] + "\n" + b["text"] + "\nChallenge these claims."
                critique.write_text(text, encoding="utf-8")
                result = module.moe_ask("expert-a", "Critique", str(critique), phase="critique", expected_model=a["model"], peer_model=b["model"])
                self.assertNotIn("error", result)
                self.assertLessEqual(result["sent_bytes"], 24000)
                self.assertEqual(transport.call_count, 3)

    def test_model_alias_collision_stops_the_second_participant(self):
        module = self.load()
        with tempfile.TemporaryDirectory() as folder, patch.object(module.Path, "cwd", return_value=Path(folder)):
            packet = Path(folder) / ".moe/run/brief.md"
            packet.parent.mkdir(parents=True)
            packet.write_text("Solve")
            same = {"model": "actual-model", "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": "Answer"}}]}
            with patch.object(module, "_call", return_value=same) as transport:
                first = module.moe_ask("alias-a", "Solve", str(packet))
                second = module.moe_ask("alias-b", "Solve", str(packet), peer_model=first["model"])
                self.assertEqual(second.get("code"), "model_collision")
                self.assertEqual(transport.call_count, 2)

    def test_every_failure_names_its_cause_and_whether_a_request_was_charged(self):
        """One generic message hid four causes; each now carries a stable code and a charged flag."""
        module = self.load()
        with tempfile.TemporaryDirectory() as folder, patch.object(module.Path, "cwd", return_value=Path(folder)), patch.dict(os.environ, {"MOE_API_BASE": "https://fixture.invalid/v1", "MOE_API_KEY": "fixture"}, clear=True):
            run = Path(folder) / ".moe/run"
            run.mkdir(parents=True)
            packet = run / "brief.md"
            packet.write_text("Solve")

            def reply(content="Answer", finish="stop", **extra):
                message = {"role": "assistant", "content": content, **extra}
                return {"model": "expert-a", "choices": [{"finish_reason": finish, "message": message}]}

            before_send = [
                (dict(max_output_tokens=0), "invalid_request"),
                (dict(phase="critique"), "identity_contract"),
                (dict(peer_model="same", expected_model="SAME", phase="critique"), "model_collision"),
            ]
            with patch.object(module, "_call") as transport:
                for kwargs, code in before_send:
                    with self.subTest(code=code):
                        result = module.moe_ask("expert-a", "Solve", str(packet), **kwargs)
                        self.assertEqual(result["code"], code)
                        self.assertFalse(result["charged"])
                result = module.moe_ask("expert-a", "Solve", str(Path(folder) / "outside.md"))
                self.assertEqual((result["code"], result["charged"]), ("payload_invalid", False))
                self.assertFalse(transport.called)

            after_send = [
                (reply(finish="length"), "reply_truncated"),
                (reply(finish="content_filter"), "finish_reason_unsupported"),
                (reply(content="R" * 8001), "reply_bound"),
                (reply(content=""), "reply_empty"),
                (reply(tool_calls=[{"id": "call"}]), "reply_tool_calls"),
                ({"model": "expert-a", "choices": []}, "response_shape"),
                ({"choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": "A"}}]}, "model_identity_missing"),
            ]
            for data, code in after_send:
                with self.subTest(code=code), patch.object(module, "_call", return_value=data):
                    result = module.moe_ask("expert-a", "Solve", str(packet))
                    self.assertEqual(result["code"], code)
                    self.assertTrue(result["charged"])
            with patch.object(module, "_call", side_effect=OSError("reset")):
                result = module.moe_ask("expert-a", "Solve", str(packet))
                self.assertEqual((result["code"], result["charged"]), ("transport", True))

    def test_provider_vocabulary_for_a_complete_reply_is_accepted(self):
        """A gateway that forwards end_turn or omits finish_reason still delivers a complete reply."""
        module = self.load()
        with tempfile.TemporaryDirectory() as folder, patch.object(module.Path, "cwd", return_value=Path(folder)):
            packet = Path(folder) / ".moe/run/brief.md"
            packet.parent.mkdir(parents=True)
            packet.write_text("Solve")
            for finish, reported in (("end_turn", "end_turn"), ("stop_sequence", "stop_sequence"), (None, "unknown")):
                data = {"model": "expert-a", "choices": [{"finish_reason": finish, "message": {"role": "assistant", "content": "Answer"}}]}
                with self.subTest(finish=finish), patch.object(module, "_call", return_value=data):
                    result = module.moe_ask("expert-a", "Solve", str(packet))
                    self.assertNotIn("error", result)
                    self.assertEqual(result["finish_reason"], reported)

    def test_critique_identity_pins_and_unknown_identity_fail_closed(self):
        module = self.load()
        with tempfile.TemporaryDirectory() as folder, patch.object(module.Path, "cwd", return_value=Path(folder)):
            packet = Path(folder) / ".moe/run/brief.md"
            packet.parent.mkdir(parents=True)
            packet.write_text("Solve")
            with patch.object(module, "_call") as transport:
                self.assertIn("error", module.moe_ask("alias-a", "Critique", str(packet), phase="critique"))
                self.assertFalse(transport.called)
            answer = {"choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": "Answer"}}]}
            with patch.object(module, "_call", return_value=answer):
                self.assertEqual(module.moe_ask("alias-a", "Solve", str(packet)).get("code"), "model_identity_missing")
                answer["model"] = "changed-model"
                result = module.moe_ask("alias-a", "Critique", str(packet), phase="critique", expected_model="original-model", peer_model="other-model")
                self.assertEqual(result.get("code"), "model_changed")

    def test_tritech_bridge_has_no_direct_gateway_fallback(self):
        module=self.load()
        with patch.dict(os.environ,{"MOE_API_BASE":"https://foreign.invalid/v1","MOE_API_KEY":"key","MOE_BRIDGE_URL":"https://foreign.invalid/","MOE_BRIDGE_TOKEN":"local"},clear=True):
            with self.assertRaises(ValueError): module._connection()
        with patch.dict(os.environ,{"MOE_BRIDGE_URL":"http://127.0.0.1:1234","MOE_BRIDGE_TOKEN":"local"},clear=True):
            url,secret=module._connection()
            self.assertEqual(url,"http://127.0.0.1:1234/v1")
            self.assertEqual(secret,"local")

    def test_managed_deliberation_creates_run_dir_composes_critiques_and_updates_exchange(self):
        module = self.load()
        with tempfile.TemporaryDirectory() as folder, patch.object(module.Path, "cwd", return_value=Path(folder)), patch.dict(os.environ, {"MOE_API_BASE": "https://fixture.invalid/v1", "MOE_API_KEY": "fixture"}, clear=True):
            calls = []
            def answer(path, body=None, binding=""):
                calls.append(body)
                model = "resolved-a" if body["model"] == "alias-a" else "resolved-b"
                return {
                    "model": model,
                    "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": f"Reply from {model} (#{len(calls)})"}}],
                    "usage": {"total_tokens": 10 * len(calls)},
                }
            with patch.object(module, "_call", side_effect=answer):
                r1a = module.moe_ask("alias-a", brief="Compare schema A and schema B for migration.")
                self.assertNotIn("error", r1a)
                run_id = r1a["run_id"]
                self.assertEqual((r1a["round"], r1a["slot"], r1a["model"]), (1, "1", "resolved-a"))
                run_dir = Path(folder) / ".moe" / run_id
                self.assertTrue((run_dir / "brief.md").is_file())
                self.assertTrue((run_dir / "round-1-proposal-1.md").is_file())

                # Second proposal reuses brief.md and pins peer_model automatically
                r1b = module.moe_ask("alias-b", run_id=run_id)
                self.assertNotIn("error", r1b)
                self.assertEqual((r1b["round"], r1b["slot"], r1b["model"]), (1, "2", "resolved-b"))
                self.assertEqual(calls[0]["messages"][1]["content"], calls[1]["messages"][1]["content"])

                # Round 2 critiques compose brief + both round 1 replies and pin expected_model/peer_model
                r2a = module.moe_ask("alias-a", phase="critique", run_id=run_id)
                self.assertNotIn("error", r2a)
                self.assertEqual((r2a["round"], r2a["slot"]), (2, "1"))
                self.assertIn("Reply from resolved-a (#1)", calls[2]["messages"][1]["content"])
                self.assertIn("Reply from resolved-b (#2)", calls[2]["messages"][1]["content"])

                r2b = module.moe_ask("alias-b", phase="critique", run_id=run_id, focus="Focus on rollback safety.")
                self.assertNotIn("error", r2b)
                self.assertEqual((r2b["round"], r2b["slot"]), (2, "2"))
                self.assertIn("Focus on rollback safety.", calls[3]["messages"][1]["content"])

                state = json.loads((run_dir / "exchange.json").read_text(encoding="utf-8"))
                self.assertEqual(state["status"], "completed")
                self.assertEqual(len(state["calls"]), 4)
                self.assertEqual(state["participants"]["1"]["actual_model"], "resolved-a")
                self.assertEqual(state["participants"]["2"]["actual_model"], "resolved-b")

                # Round 3: first half puts status back to in_progress, second half completes it
                r3a = module.moe_ask("alias-a", phase="critique", run_id=run_id, focus="Resolve edge case.")
                self.assertEqual((r3a["round"], r3a["slot"]), (3, "1"))
                state = json.loads((run_dir / "exchange.json").read_text(encoding="utf-8"))
                self.assertEqual(state["status"], "in_progress")
                r3b = module.moe_ask("alias-b", phase="critique", run_id=run_id, focus="Resolve edge case.")
                self.assertEqual((r3b["round"], r3b["slot"]), (3, "2"))
                state = json.loads((run_dir / "exchange.json").read_text(encoding="utf-8"))
                self.assertEqual(state["status"], "completed")
                self.assertEqual(len(state["calls"]), 6)

    def test_managed_deliberation_records_collision_and_blocks_failed_run(self):
        module = self.load()
        with tempfile.TemporaryDirectory() as folder, patch.object(module.Path, "cwd", return_value=Path(folder)):
            same = {"model": "same-backend", "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": "Proposal"}}]}
            with patch.object(module, "_call", return_value=same) as transport:
                # Oversized custom system on first proposal fails before creating a run directory
                bad_sys = module.moe_ask("alias-a", system="S" * 4097, brief="Problem statement", run_id="bad-sys-run")
                self.assertEqual((bad_sys["code"], bad_sys["charged"]), ("invalid_request", False))
                self.assertFalse((Path(folder) / ".moe/bad-sys-run").exists())

                r1a = module.moe_ask("alias-a", brief="Problem statement")
                run_id = r1a["run_id"]
                # Requesting the exact same model on slot 2 is rejected before spending (charged=False)
                same_req = module.moe_ask("alias-a", run_id=run_id)
                self.assertEqual((same_req["code"], same_req["charged"]), ("model_collision", False))
                self.assertEqual(transport.call_count, 1)

            with patch.object(module, "_call", return_value=same) as transport:
                r1a = module.moe_ask("alias-a", brief="Problem statement")
                run_id = r1a["run_id"]
                r1b = module.moe_ask("alias-b", run_id=run_id)
                self.assertEqual((r1b["code"], r1b["charged"], r1b["run_id"]), ("model_collision", True, run_id))
                state = json.loads((Path(folder) / ".moe" / run_id / "exchange.json").read_text(encoding="utf-8"))
                self.assertEqual(state["status"], "failed")
                self.assertEqual(state["calls"][-1]["code"], "model_collision")
                # Further calls on a failed run are rejected before spending
                after = module.moe_ask("alias-a", phase="critique", run_id=run_id)
                self.assertEqual((after["code"], after["charged"]), ("invalid_request", False))
                self.assertEqual(transport.call_count, 2)

if __name__ == "__main__": unittest.main()
