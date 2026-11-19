"""Probe the existing HTTP/service boundary without MCP or model execution."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import http.client
import json
from pathlib import Path
import platform
import sys
import tempfile
import threading
import time
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "daodan/core"
sys.path.insert(0, str(SCRIPTS))

import mcp_service  # noqa: E402

assert "visual" not in sys.modules, "MapService imported the UI transport"
assert not any(name == "mcp" or name.startswith("mcp.") for name in sys.modules)

import visual  # noqa: E402


def probe(requests):
    with tempfile.TemporaryDirectory(prefix="daodan-boundary-") as temporary:
        project = Path(temporary).resolve()
        assets = project / "assets"
        assets.mkdir()
        (assets / "index.html").write_text("<!doctype html><title>Boundary probe</title>", encoding="utf-8")
        service = mcp_service.MapService(project)
        server = visual.make_server(None, assets, routes=visual.live_routes(service),
                                    actions=visual.live_actions(service), token="probe-token")
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        port = server.server_address[1]
        base = f"http://127.0.0.1:{port}"

        def request(path, body=None, *, token=True, origin=None):
            headers = {"X-Daodan-Token": "probe-token"} if token else {}
            if body is not None:
                headers.update({"Content-Type": "application/json", "Origin": origin or base})
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            try:
                connection.request("GET" if body is None else "POST", path,
                                   body=None if body is None else json.dumps(body), headers=headers)
                response = connection.getresponse()
                content = response.read()
                return response.status, json.loads(content) if path.startswith("/api/") else content
            finally:
                connection.close()

        try:
            assert server.server_address[0] == "127.0.0.1"
            assert request("/")[0] == 200
            assert request("/api/requests", token=False)[0] == 403
            body = {"kind": "map", "scope": "prompt", "text": "boundary probe"}
            assert request("/api/requests", body, origin="https://other.invalid")[0] == 403
            identifiers = []
            for number in range(requests):
                body["kind"] = "map" if number % 2 == 0 else "review"
                status, result = request("/api/requests", body)
                assert status == 200 and result["state"] == "pending"
                identifiers.append(result["id"])
            assert len(set(identifiers)) == requests
            assert len(request("/api/requests")[1]["requests"]) == requests
            with ThreadPoolExecutor(max_workers=2) as consumers:
                claims = list(consumers.map(lambda _: service.ui_requests(take=True)["taken"], range(2)))
            assert sorted(item for claim in claims for item in claim) == sorted(identifiers)
            released = service.ui_requests(release=[identifiers[0]])
            assert released["released"] == [identifiers[0]]
            assert service.ui_requests(take=True)["taken"] == [identifiers[0]]
            for identifier in identifiers:
                service.ui_done(identifier, message="probe completed")
            assert all(item["state"] == "done" for item in request("/api/requests")[1]["requests"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
        assert not thread.is_alive() and server.socket.fileno() == -1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--requests", type=int, default=4)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if not 1 <= args.repeat <= 10 or not 1 <= args.requests <= 10:
        parser.error("repeat and requests must be between 1 and 10")
    started = time.perf_counter()
    with patch("subprocess.Popen", side_effect=AssertionError("the boundary probe must not start processes")):
        for _ in range(args.repeat):
            probe(args.requests)
    result = {"python": platform.python_version(), "system": platform.system(),
              "parameters": {"repeat": args.repeat, "requests_per_repeat": args.requests, "consumers": 2},
              "passed": True, "elapsed_seconds": round(time.perf_counter() - started, 3),
              "checks": ["core_without_mcp_or_ui_import", "independent_http_bootstrap", "loopback_and_token",
                         "origin_refusal", "persistent_request_roundtrip", "concurrent_claim_once",
                         "release_and_complete", "clean_shutdown", "no_child_process"]}
    rendered = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
