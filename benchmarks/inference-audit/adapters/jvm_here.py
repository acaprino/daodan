"""The two phases of the plugin's JVM indexers (`indexers.jvm`) in this process's own container, for Modal.

No container engine runs on Modal, and the function's container is the isolation: the same bash scripts run
here as subprocesses, over the files the container operation would copy (`container.copy_perimeter`) and
the tools it would carry (`indexers.jvm.tools`, placed at their own paths), with the outputs under
`<work_dir>/container/out` as the operation brings them back. The preparation reaches the network
through the operation's registry proxy (`container.PROXY_SCRIPT`, with `indexers.jvm.registries()`); here it is
only a check, since nothing forces a tool through it, and the hosts it refused are returned. The execution has
the proxy variables empty. Never used on a user's machine: there the build runs only in a container.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

PORT = 3128
# As `code_graph.measured`: the peak resident memory of the largest process, here per phase.
PROBE = ("import resource,subprocess,sys;r=subprocess.run(sys.argv[1:]);"
         "print('DAODAN_MAXRSS_KB=%d' % resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss, file=sys.stderr);"
         "sys.exit(r.returncode)")


def run(project_dir: Path, work_dir: Path, prepare: str, execute: str, *, prepare_timeout: float = 1800,
        timeout: float = 600) -> tuple[dict, list[dict], Path]:
    """`(result, runs, out)` as `indexers.jvm.run` returns them, `result["refused"]` the hosts the proxy refused."""
    import container
    from indexers import jvm
    work_dir = Path(work_dir)
    out_dir, copy = work_dir / "container", work_dir / "work"
    out = out_dir / Path(jvm.OUT).name
    for folder in (out_dir, copy):
        shutil.rmtree(folder, ignore_errors=True)
    out.mkdir(parents=True)
    bundle = out_dir / "copy.tar"
    container.copy_perimeter(Path(project_dir), bundle)
    with tarfile.open(bundle) as archive:
        archive.extractall(work_dir, filter="tar")  # `work/...`, modes kept: a wrapper stays executable
    bundle.unlink()
    try:
        inputs = jvm.tools(Path(project_dir))
    except container.Gap as gap:
        return {"state": "gap", "cause": gap.cause, "remedy": gap.remedy, "refused": []}, [], out
    for destination, source in inputs.items():
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    env = {key: value for key, value in os.environ.items() if key not in container.PROXY_VARIABLES}
    env.update(jvm.ENV, DAODAN_WORK=str(copy), DAODAN_OUT=str(out))
    proxy_log = out_dir / "proxy.log"
    with proxy_log.open("wb") as handle:
        proxy = subprocess.Popen([sys.executable, "-c", container.PROXY_SCRIPT, str(PORT), *jvm.registries()],
                                 stdin=subprocess.DEVNULL, stdout=handle, stderr=subprocess.STDOUT)
    result, runs, prepared = {"state": "done"}, [], ""
    try:
        for _ in range(50):
            if b"ready" in proxy_log.read_bytes():
                break
            time.sleep(0.2)
        for phase, body, limit in (("prepare", prepare, prepare_timeout), ("execute", execute, timeout)):
            address = f"http://127.0.0.1:{PORT}" if phase == "prepare" else ""
            log = out_dir / f"{phase}.log"
            with log.open("wb") as handle:
                try:
                    code = subprocess.run([sys.executable, "-c", PROBE, "bash", "-c", jvm.script(phase, body)],
                                          cwd=copy, env={**env, **container.proxy_environment(address)},
                                          stdin=subprocess.DEVNULL, stdout=handle, stderr=subprocess.STDOUT,
                                          timeout=limit).returncode
                except subprocess.TimeoutExpired:
                    code = None
            text = log.read_text(encoding="utf-8", errors="replace")
            prepared = text if phase == "prepare" else prepared
            peak = re.findall(r"DAODAN_MAXRSS_KB=(\d+)", text)
            for item in jvm.steps(text, phase):
                runs.append({**item, "peak_mb": round(int(peak[-1]) / 1024) if peak else item["peak_mb"]})
            if phase == "prepare" and code != 0:
                result = {"state": "failed", "cause": f"preparation {'timeout' if code is None else 'exited with code'}"
                                                      f"{'' if code is None else f' {code}'}; see {log}"}
                break
    finally:
        proxy.terminate()
        proxy.wait(timeout=30)
    result = jvm.judged(result, prepared)
    result["refused"] = sorted(set(re.findall(r"refused \[b'CONNECT', b'([^']+)'\]",
                                              proxy_log.read_text(encoding="utf-8", errors="replace"))))
    return result, runs, out
