"""A minimal Build Server Protocol 2.2 client over stdio: start the server, ask for the model, write it as JSON.

    python bsp_client.py <project root> <out.json> <timeout seconds> -- <server command...>

Requests: build/initialize, build/initialized, workspace/buildTargets, buildTarget/sources,
buildTarget/dependencyModules, buildTarget/javacOptions, build/shutdown, build/exit. Notifications from the
server (logs, task progress) are kept, the last 50, in `log`. Nothing is compiled.
"""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from pathlib import Path


class Server:
    def __init__(self, argv, cwd):
        self.proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
        self.next_id, self.replies, self.log = 0, {}, []
        self.cond = threading.Condition()
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=self._drain, daemon=True).start()
        self.stderr = []

    def _drain(self):
        for line in self.proc.stderr:
            self.stderr.append(line.decode("utf-8", "replace").rstrip())
            del self.stderr[:-40]

    def _read(self):
        out = self.proc.stdout
        while True:
            headers = {}
            while True:
                line = out.readline()
                if not line:
                    with self.cond:
                        self.cond.notify_all()
                    return
                line = line.decode("ascii", "replace").strip()
                if not line:
                    break
                key, _, value = line.partition(":")
                headers[key.strip().lower()] = value.strip()
            body = out.read(int(headers.get("content-length", "0")))
            try:
                message = json.loads(body)
            except ValueError:
                continue
            if "id" in message and ("result" in message or "error" in message):
                with self.cond:
                    self.replies[message["id"]] = message
                    self.cond.notify_all()
            elif "id" in message:  # a request from the server: answer null
                self._send({"jsonrpc": "2.0", "id": message["id"], "result": None})
            else:
                self.log.append({"method": message.get("method"), "params": str(message.get("params"))[:300]})
                del self.log[:-50]

    def _send(self, message):
        body = json.dumps(message).encode("utf-8")
        self.proc.stdin.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body)
        self.proc.stdin.flush()

    def notify(self, method, params=None):
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def request(self, method, params, deadline):
        self.next_id += 1
        ident = self.next_id
        self._send({"jsonrpc": "2.0", "id": ident, "method": method, "params": params})
        with self.cond:
            while ident not in self.replies:
                left = deadline - time.time()
                if left <= 0 or self.proc.poll() is not None:
                    raise TimeoutError(f"{method}: no answer" + ("" if left > 0 else " in time"))
                self.cond.wait(min(left, 5))
        reply = self.replies.pop(ident)
        if "error" in reply:
            raise RuntimeError(f"{method}: {reply['error']}")
        return reply["result"]


def main():
    root, out, timeout = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), float(sys.argv[3])
    argv = sys.argv[sys.argv.index("--") + 1:]
    deadline = time.time() + timeout
    result, steps = {"errors": []}, []
    server = Server(argv, str(root))
    try:
        started = time.time()
        result["initialize"] = server.request("build/initialize", {
            "displayName": "pm-native", "version": "1.0", "bspVersion": "2.2.0", "rootUri": root.as_uri(),
            "capabilities": {"languageIds": ["java", "kotlin", "scala", "groovy"]}}, deadline)
        server.notify("build/initialized")
        steps.append(["initialize", round(time.time() - started, 2)])
        started = time.time()
        targets = server.request("workspace/buildTargets", None, deadline)["targets"]
        result["targets"] = targets
        steps.append(["workspace/buildTargets", round(time.time() - started, 2)])
        ids = [t["id"] for t in targets]
        for method, key in (("buildTarget/sources", "sources"), ("buildTarget/dependencyModules", "modules"),
                            ("buildTarget/javacOptions", "javac")):
            started = time.time()
            try:
                result[key] = server.request(method, {"targets": ids}, deadline)
            except (RuntimeError, TimeoutError) as error:
                result["errors"].append(str(error)[:600])
            steps.append([method, round(time.time() - started, 2)])
        try:
            server.request("build/shutdown", None, min(deadline, time.time() + 30))
            server.notify("build/exit")
        except (RuntimeError, TimeoutError) as error:
            result["errors"].append(f"shutdown: {error}"[:300])
    except (RuntimeError, TimeoutError, OSError, KeyError) as error:
        result["errors"].append(f"{type(error).__name__}: {error}"[:800])
    finally:
        result["steps"], result["log"], result["server_stderr"] = steps, server.log, server.stderr[-20:]
        try:
            server.proc.wait(20)
        except subprocess.TimeoutExpired:
            server.proc.kill()
        out.write_text(json.dumps(result), encoding="utf-8")
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
