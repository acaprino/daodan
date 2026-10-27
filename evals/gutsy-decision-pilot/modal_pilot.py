"""Ephemeral CPU-only Modal transport for frozen, synthetic pilot requests."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

import modal

MODEL = "gutsy-0.8b-v04-q4"
GUTSY_COMMIT = "db5c2ec62fc81703938adbd714915b53a9fb0de1"
HF_REVISION = "f9995fe26a337f1a4ea3f1a5ed38c9799e5a8f63"
WEIGHT_NAME = "gutsy-0.8b-v04-q4_k_m.gguf"
CALIBRATION_NAME = "gutsy-0.8b-v04-q4_k_m.calibration.json"
WEIGHT_BYTES = 529296832
WEIGHT_SHA256 = "ddf9c23b8a07c008172f1731f4dd93c464b651b9a70409f0feaf8c2d4e089152"
HARD_MEMORY = 2048 * 2**20
RSS_STOP = HARD_MEMORY - 128 * 2**20

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "build-essential", "cmake")
    .env({"CMAKE_ARGS": "-DGGML_NATIVE=OFF", "OMP_NUM_THREADS": "4",
          "OPENBLAS_NUM_THREADS": "4", "MKL_NUM_THREADS": "4"})
    .pip_install("numpy==2.3.4", "llama-cpp-python==0.3.36",
                 extra_index_url="https://abetlen.github.io/llama-cpp-python/whl/cpu")
    .pip_install(f"git+https://github.com/kouhxp/gutsy.git@{GUTSY_COMMIT}#subdirectory=gutsy-inference")
)
app = modal.App(name="gutsy-q4-preliminary-pilot")


def _json_write(path: Path, value: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _file_hash(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(2**20), b""):
            value.update(chunk)
    return value.hexdigest()


def _download(name: str, destination: Path, deadline: float) -> dict:
    url = f"https://huggingface.co/kouhxp/gutsy/resolve/{HF_REVISION}/{name}?download=true"
    started = time.monotonic()
    request = urllib.request.Request(url, headers={"User-Agent": "gutsy-decision-pilot/1"})
    digest = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as target:
        for chunk in iter(lambda: response.read(2**20), b""):
            if time.monotonic() >= deadline:
                raise TimeoutError("Global deadline during model download")
            target.write(chunk)
            digest.update(chunk)
            size += len(chunk)
    return {"name": name, "revision": HF_REVISION, "bytes": size,
            "sha256": digest.hexdigest(), "seconds": time.monotonic() - started}


def _read_optional(path: str) -> str | None:
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def _process_rss(root_pid: int) -> tuple[int, dict[str, int]]:
    rows = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / "stat").read_text().rsplit(") ", 1)[1].split()
            parent_pid = int(fields[1])
            rss = 0
            for line in (entry / "status").read_text().splitlines():
                if line.startswith("VmRSS:"):
                    rss = int(line.split()[1]) * 1024
                    break
            rows[int(entry.name)] = (parent_pid, rss)
        except (OSError, ValueError, IndexError):
            continue
    members = {root_pid}
    while True:
        expanded = members | {pid for pid, (parent, _rss) in rows.items() if parent in members}
        if expanded == members:
            break
        members = expanded
    amounts = {str(pid): rows[pid][1] for pid in members if pid in rows}
    return sum(amounts.values()), amounts


class MemorySampler:
    def __init__(self):
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._sample, daemon=True)
        self.peak = 0
        self.latest = 0
        self.samples = 0
        self.peak_members = {}
        self.cgroup_peak = 0
        self.exceeded = False
        self.server = None

    def _sample(self):
        while not self.stop.is_set():
            try:
                total, members = _process_rss(os.getpid())
                self.latest = total
                self.samples += 1
                if total > self.peak:
                    self.peak, self.peak_members = total, members
                current = _read_optional("/sys/fs/cgroup/memory.current")
                if current and current.isdigit():
                    self.cgroup_peak = max(self.cgroup_peak, int(current))
                if total >= RSS_STOP:
                    self.exceeded = True
                    if self.server and self.server.poll() is None:
                        self.server.terminate()
            except OSError:
                pass
            self.stop.wait(0.2)

    def start(self):
        self.thread.start()

    def close(self):
        self.stop.set()
        self.thread.join(timeout=2)

    def report(self) -> dict:
        return {"sampled_peak_combined_rss_bytes": self.peak,
                "last_combined_rss_bytes": self.latest,
                "peak_process_members_rss_bytes": self.peak_members,
                "samples": self.samples, "interval_seconds": 0.2,
                "sampled_peak_cgroup_memory_bytes": self.cgroup_peak,
                "kernel_cgroup_memory_peak": _read_optional("/sys/fs/cgroup/memory.peak"),
                "rss_stop_bytes": RSS_STOP, "stop_triggered": self.exceeded,
                "lightweight_target_met": self.peak <= 2**30,
                "method": "VmRSS summed for worker PID and descendants; shared pages may be counted more than once. Cgroup values include the entire container. Sampling is not a hard memory limit."}


def _http_json(url: str, body: dict | None = None, timeout: float = 180) -> dict:
    data = None if body is None else json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
    request = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json"} if body is not None else {})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def _bounded(value) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and 0 <= value <= 1


def _check_response(body: dict, response: dict) -> None:
    if response.get("model") != MODEL:
        raise ValueError(f"Unexpected answering model: {response.get('model')!r}")
    answers = response.get("answers")
    if not isinstance(answers, dict):
        raise ValueError("Response has no answers object")
    for key, question in body["questions"].items():
        answer = answers.get(key)
        if not isinstance(answer, dict):
            raise ValueError(f"Missing answer {key}")
        if question["type"] == "noul":
            if not _bounded(answer.get("noul")):
                raise ValueError(f"Invalid bounded noul {key}")
        elif question["type"] == "choice":
            probabilities = answer.get("probabilities", {})
            expected = set(question["criteria"])
            if set(probabilities) != expected or not all(_bounded(p) for p in probabilities.values()):
                raise ValueError(f"Invalid choice probabilities {key}")
            if answer.get("choice") not in expected or not _bounded(answer.get("reject")):
                raise ValueError(f"Invalid selected option or reject {key}")
            if abs(sum(probabilities.values()) - 1) > 1e-4:
                raise ValueError(f"Unnormalized choice probabilities {key}")
        else:
            raise ValueError(f"Unsupported pilot question type {question['type']}")


def _versions() -> dict:
    versions = {}
    for name in ("numpy", "llama-cpp-python", "gutsy-inference", "modal"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    libraries = {}
    try:
        distribution = importlib.metadata.distribution("llama-cpp-python")
        for item in distribution.files or []:
            if Path(item).name in {"libllama.so", "libggml.so", "libggml-cpu.so"}:
                location = Path(distribution.locate_file(item))
                libraries[str(item)] = _file_hash(location)
    except (OSError, importlib.metadata.PackageNotFoundError):
        pass
    cpu_info = _read_optional("/proc/cpuinfo")
    return {"packages": versions, "native_library_sha256": libraries,
            "python": sys.version, "platform": platform.platform(),
            "cpu_description": cpu_info.split("\n\n", 1)[0] if cpu_info else None,
            "logical_processors_visible": os.cpu_count(),
            "cgroup_cpu_max": _read_optional("/sys/fs/cgroup/cpu.max"),
            "cgroup_memory_max": _read_optional("/sys/fs/cgroup/memory.max")}


@app.function(image=image, cpu=(4.0, 4.0), memory=(1024, 2048), timeout=2400,
              max_containers=1, retries=0, scaledown_window=2)
def run_pilot(payload: dict) -> dict:
    started = time.monotonic()
    max_seconds = min(1800, max(1, int(payload.get("max_seconds", 1800))))
    max_questions = min(500, max(1, int(payload.get("max_questions", 500))))
    deadline = started + max_seconds
    records = []
    runtime = {"gutsy_commit": GUTSY_COMMIT, "model": MODEL,
               "hf_revision": HF_REVISION, "max_seconds": max_seconds,
               "max_questions": max_questions, "cpu_request_and_limit": 4,
               "threads": 4, "n_ctx": 4096, "cache_entries": 1, "cache_mb": 128,
               "gpu_layers": 0, "question_budget_scope": "Submitted pilot questions, including failed attempts; startup self-check is separate.",
               "checkpoint_method": "Atomic ephemeral JSON after each case, plus complete PILOT_RECORD lines in Modal logs."}
    result = {"records": records, "runtime": runtime, "complete": False, "stop_reason": "initializing"}
    sampler = MemorySampler()
    sampler.start()
    server = None
    server_log = None
    attempted_questions = 0
    temporary = tempfile.TemporaryDirectory(prefix="gutsy-pilot-")
    directory = Path(temporary.name)
    checkpoint = directory / "checkpoint.json"
    log_path = directory / "server.log"
    try:
        runtime["environment"] = _versions()
        requests = payload.get("requests")
        if not isinstance(requests, list) or not requests:
            raise ValueError("Nonempty requests list required")
        ids = [request["id"] for request in requests]
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate opaque case identifiers")
        for request in requests:
            body = request["body"]
            if set(body) != {"model", "state", "questions"} or body["model"] != MODEL:
                raise ValueError("Each body must contain only model, state and questions for the Q4 model")
            if not isinstance(body["questions"], dict) or len(body["questions"]) > 64:
                raise ValueError("Invalid question count")
        smoke = {"R01": 0, "C01-A": 1, "T01": 2}
        requests = sorted(enumerate(requests), key=lambda pair: (smoke.get(pair[1]["id"], 3), pair[0]))
        requests = [request for _, request in requests]
        runtime["request_order"] = [request["id"] for request in requests]
        weight = directory / WEIGHT_NAME
        calibration = directory / CALIBRATION_NAME
        runtime["weights"] = _download(WEIGHT_NAME, weight, deadline)
        if runtime["weights"]["bytes"] != WEIGHT_BYTES or runtime["weights"]["sha256"] != WEIGHT_SHA256:
            raise ValueError("GGUF size or SHA256 differs from the frozen Q4 artifact")
        runtime["calibration"] = _download(CALIBRATION_NAME, calibration, deadline)
        json.loads(calibration.read_text())
        config = {"default": MODEL, "models": {MODEL: {"gguf": str(weight),
                  "calibration": str(calibration), "n_ctx": 4096,
                  "reject_slot": True, "cache_tol": 0.02}},
                  "n_threads": 4, "n_gpu_layers": 0, "cache_entries": 1, "cache_mb": 128}
        config_path = directory / "models.json"
        _json_write(config_path, config)
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        base_url = f"http://127.0.0.1:{port}"
        server_log = log_path.open("wb")
        server_started = time.monotonic()
        server = subprocess.Popen([sys.executable, "-m", "gutsy_inference.cli", "serve",
                                   "--config", str(config_path), "--host", "127.0.0.1",
                                   "--port", str(port), "--quiet"],
                                  stdout=server_log, stderr=subprocess.STDOUT,
                                  env={**os.environ, "OMP_NUM_THREADS": "4", "OPENBLAS_NUM_THREADS": "4"})
        sampler.server = server
        startup_deadline = min(deadline, server_started + 300)
        while True:
            if server.poll() is not None:
                raise RuntimeError(f"Official server exited during startup ({server.returncode})")
            if sampler.exceeded:
                raise MemoryError("RSS guard stopped the server during startup")
            if time.monotonic() >= startup_deadline:
                raise TimeoutError("Official server startup timed out")
            try:
                runtime["health"] = _http_json(base_url + "/health", timeout=2)
                break
            except (urllib.error.URLError, TimeoutError):
                time.sleep(0.2)
        runtime["server_startup_seconds"] = time.monotonic() - server_started
        models = runtime["health"].get("models", {})
        if set(models) != {MODEL} or not models[MODEL].get("loaded"):
            raise ValueError("Health does not attest exactly one loaded Q4 model")
        print("PILOT_RUNTIME " + json.dumps({"model": MODEL, "weights": runtime["weights"],
              "health": runtime["health"], "startup_seconds": runtime["server_startup_seconds"]}), flush=True)
        for request in requests:
            question_count = len(request["body"]["questions"])
            if sampler.exceeded:
                result["stop_reason"] = "memory_guard"
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                result["stop_reason"] = "time_budget"
                break
            if attempted_questions + question_count > max_questions:
                result["stop_reason"] = "question_budget"
                break
            attempted_questions += question_count
            case_started = time.monotonic()
            record = {"id": request["id"], "domain": request["domain"], "attempted_questions": question_count}
            try:
                if question_count:
                    response = _http_json(base_url + "/v1/systemone", request["body"], timeout=min(180, remaining))
                    record["response"] = response
                    _check_response(request["body"], response)
                else:
                    record["response"] = {"model": MODEL, "answers": {}, "usage": {"model_calls": 0}}
                    record["transport"] = "not_called_empty_questions"
            except urllib.error.HTTPError as error:
                record["error"] = {"type": "http_error", "status": error.code,
                                   "body": error.read().decode("utf-8", errors="replace")[:8000]}
            except Exception as error:
                record["error"] = {"type": type(error).__name__, "message": str(error)}
            record["elapsed_seconds"] = time.monotonic() - case_started
            record["combined_rss_bytes_after"] = sampler.latest
            records.append(record)
            runtime["attempted_questions"] = attempted_questions
            result["stop_reason"] = "running"
            _json_write(checkpoint, result)
            print("PILOT_RECORD " + json.dumps(record, ensure_ascii=False, allow_nan=False), flush=True)
            if "error" in record:
                # A timed-out inference may still hold the model lock. Never enqueue blindly.
                result["stop_reason"] = "api_failure"
                break
        else:
            result["complete"] = True
            result["stop_reason"] = "completed"
    except Exception as error:
        result["stop_reason"] = "initialization_failure" if not records else "runtime_failure"
        runtime["error"] = {"type": type(error).__name__, "message": str(error)}
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
            runtime["server_exit_code"] = server.returncode
            runtime["server_stopped"] = server.poll() is not None
        if server_log is not None:
            server_log.close()
        sampler.close()
        runtime["memory"] = sampler.report()
        if not runtime.get("health", {}).get("models", {}).get(MODEL, {}).get("loaded"):
            runtime["memory"]["lightweight_target_met"] = None
        runtime["elapsed_seconds"] = time.monotonic() - started
        runtime["attempted_questions"] = attempted_questions
        runtime["requested_cases"] = len(payload.get("requests", []))
        runtime["recorded_cases"] = len(records)
        if log_path.exists():
            runtime["server_log_tail"] = log_path.read_text(errors="replace")[-12000:]
        _json_write(checkpoint, result)
        print("PILOT_COMPLETE " + json.dumps({"complete": result["complete"],
              "stop_reason": result["stop_reason"], "cases": len(records),
              "questions": attempted_questions, "memory": runtime["memory"]}), flush=True)
        temporary.cleanup()
    return result


@app.local_entrypoint()
def main(input_path: str, output_path: str):
    source = Path(input_path).resolve()
    target = Path(output_path).resolve()
    if not target.is_relative_to(Path.cwd().resolve()):
        raise ValueError("Output must be inside the active workspace")
    if target.exists():
        raise FileExistsError("Output already exists; use a new run path")
    payload = json.loads(source.read_text(encoding="utf-8"))
    target.parent.mkdir(parents=True, exist_ok=True)
    call = run_pilot.spawn(payload)
    invocation = {"app_id": getattr(app, "app_id", None),
                  "function_call_id": getattr(call, "object_id", None),
                  "input_sha256": _file_hash(source),
                  "modal_pilot_source_sha256": _file_hash(Path(__file__).resolve())}
    print("PILOT_INVOCATION " + json.dumps(invocation), flush=True)
    try:
        result = call.get()
    except KeyboardInterrupt:
        call.cancel()
        _json_write(target, {"complete": False, "stop_reason": "caller_cancelled", "records": [], "invocation": invocation})
        raise
    except Exception as error:
        _json_write(target, {"complete": False, "stop_reason": "remote_failure", "records": [],
                            "runtime": {"error": {"type": type(error).__name__, "message": str(error)}},
                            "invocation": invocation})
        raise
    result["invocation"] = invocation
    _json_write(target, result)
    print(json.dumps({"output": str(target), "complete": result["complete"],
                      "stop_reason": result["stop_reason"], "records": len(result["records"])}), flush=True)
