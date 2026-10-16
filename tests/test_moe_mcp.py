"""Real MCP SDK wire test against a local deterministic model endpoint, no paid call."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SERVER=Path(__file__).resolve().parents[1]/"plugins/moe/skills/multi-model-deliberation/scripts/server.py"

@unittest.skipUnless(importlib.util.find_spec("mcp"), "live MCP SDK requires the declared plugin runtime")
class MoeMcpWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_discovery_and_exact_original_request(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        received=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_GET(self):
                self.reply({"data":[{"id":"expert-a"},{"id":"expert-b"}]})
            def do_POST(self):
                data=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                received.append(data)
                self.reply({"model":"expert-a" if data["model"] == "expert-alias" else data["model"],"choices":[{"finish_reason":"stop","message":{"role":"assistant","content":"Checked proposal"}}],"usage":{"total_tokens":17}})
            def reply(self,data):
                raw=json.dumps(data).encode()
                self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
        endpoint=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        thread=threading.Thread(target=endpoint.serve_forever,daemon=True); thread.start()
        try:
            with tempfile.TemporaryDirectory() as folder:
                root=Path(folder); packet=root/".moe/run/original.md"; packet.parent.mkdir(parents=True); packet.write_bytes(b"Exact original\r\nconstraints")
                env={**os.environ,"MOE_API_BASE":f"http://127.0.0.1:{endpoint.server_port}/v1","MOE_API_KEY":"fixture","PYTHONDONTWRITEBYTECODE":"1"}
                for name in ["MOE_BRIDGE_URL","MOE_BRIDGE_TOKEN","MOE_RUN_ROOT"]: env.pop(name,None)
                params=StdioServerParameters(command=sys.executable,args=["-B",str(SERVER)],env=env,cwd=folder)
                async with stdio_client(params) as (read,write):
                    async with ClientSession(read,write) as client:
                        await client.initialize()
                        tools=await client.list_tools()
                        self.assertEqual({tool.name for tool in tools.tools},{"moe_models","moe_ask"})
                        models=await client.call_tool("moe_models",{})
                        self.assertFalse(models.is_error)
                        discovery=json.loads(models.content[0].text)
                        self.assertEqual([m["id"] for m in discovery["models"]],["expert-a","expert-b"])
                        answer=await client.call_tool("moe_ask",{"model":"expert-a","system":"Propose a solution","content_path":str(packet),"max_output_tokens":1024})
                        self.assertFalse(answer.is_error)
                        reply=json.loads(answer.content[0].text)
                        self.assertEqual(reply["text"],"Checked proposal")
                        self.assertEqual(reply["usage"]["total_tokens"],17)
                        self.assertEqual(received[0]["messages"][1]["content"],"Exact original\r\nconstraints")
                        self.assertEqual(received[0]["max_tokens"],1024)
                        collision=await client.call_tool("moe_ask",{"model":"expert-alias","system":"Independent proposal","content_path":str(packet),"peer_model":"expert-a"})
                        self.assertFalse(collision.is_error)
                        self.assertEqual(json.loads(collision.content[0].text)["code"],"model_collision")
                        critique=await client.call_tool("moe_ask",{"model":"expert-a","system":"Critique","content_path":str(packet),"phase":"critique","expected_model":"expert-a","peer_model":"expert-b"})
                        self.assertFalse(critique.is_error)
                        self.assertEqual(json.loads(critique.content[0].text)["model"],"expert-a")
                        self.assertEqual(len(received),3)
        finally:
            endpoint.shutdown(); endpoint.server_close(); thread.join(timeout=5)

if __name__ == "__main__": unittest.main()
