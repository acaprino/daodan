"""Quick probe of llama-server startup and HTTP endpoints."""

import subprocess
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
LLAMA_SERVER = HERE / ".cache/gutsy/llama-bin/llama-server.exe"
MODEL = HERE / ".cache/gutsy/gutsy-0.8b-v04-q4_k_m.gguf"
PORT = 8089
LOG_OUT = HERE / ".cache/gutsy/server_test.log"

with open(LOG_OUT, "w", encoding="utf-8") as log_file:
    proc = subprocess.Popen(
        [
            str(LLAMA_SERVER),
            "-m",
            str(MODEL),
            "-c",
            "2048",
            "-t",
            "4",
            "--port",
            str(PORT),
            "--host",
            "127.0.0.1",
            "--no-warmup",
        ],
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )

try:
    print("Process started PID:", proc.pid, flush=True)
    time.sleep(3.0)
    # Check endpoints
    endpoints = ["/health", "/v1/models", "/props", "/slots"]
    for ep in endpoints:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{PORT}{ep}")
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                print(f"Endpoint {ep}: status={resp.status}, data={resp.read().decode('utf-8')[:100]}", flush=True)
        except Exception as e:
            print(f"Endpoint {ep}: error={e}", flush=True)
finally:
    proc.terminate()
    try:
        proc.wait(timeout=3.0)
    except Exception:
        proc.kill()
    print("Server stopped. Log contents:", flush=True)
    if LOG_OUT.exists():
        print(LOG_OUT.read_text(encoding="utf-8", errors="replace")[-1000:], flush=True)
