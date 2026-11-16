"""The test suites on Modal: pytest in a Linux container over the working tree, nothing on this PC.

    python tests/modal_pytest.py tests/test_codebase_map_premap.py -q -k toolchains
    python tests/modal_pytest.py -q                      # every suite under tests/

The launcher starts `modal run` on this file with the arguments as given; the container holds the checkout as it
is on disk (plugins, tests, benchmarks without their results), runs `python -B -m pytest -p no:cacheprovider` in
it, streams the output and ends with pytest's exit code. Several suites at once: `-n 4` (pytest-xdist is there).
"""
from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
REMOTE = "/repo"  # a container path: a POSIX string, whatever runs the client
PROXIES = ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy")

if __name__ == "__main__":  # the launcher: Modal's client does not go through a proxy of this shell
    environment = {key: value for key, value in os.environ.items() if key not in PROXIES}
    environment.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    raise SystemExit(subprocess.run(["modal", "run", str(Path(__file__).resolve()), "--args",
                                     shlex.join(sys.argv[1:])], env=environment, cwd=REPO).returncode)

import modal  # noqa: E402

LOCAL = (REPO / "AGENTS.md").is_file()
image = (modal.Image.debian_slim(python_version="3.13")
         .apt_install("git", "ca-certificates", "xz-utils")
         .pip_install("pytest", "pytest-xdist", "uv", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5",
                      "sqlglot>=30"))
if LOCAL:
    skipped = ["**/__pycache__/**", "**/node_modules/**", "**/.pytest_cache/**", "**/results/**"]
    for folder in ("plugins", "tests", "benchmarks"):
        image = image.add_local_dir(REPO / folder, f"{REMOTE}/{folder}", ignore=skipped)
    image = image.add_local_file(REPO / "AGENTS.md", f"{REMOTE}/AGENTS.md")
app = modal.App("daodan-tests", image=image)


@app.function(cpu=4, memory=8192, timeout=3600)
def pytest(arguments: list) -> int:
    """pytest over the checkout in the container, its output streamed; pytest's exit code."""
    subprocess.run(["git", "init", "-q", REMOTE], check=False)  # suites that ask for the work tree's root
    command = [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", *arguments]
    print("$", shlex.join(command), flush=True)
    return subprocess.run(command, cwd=REMOTE, env={**os.environ, "PYTHONUTF8": "1"}).returncode


@app.local_entrypoint()
def main(args: str = ""):
    code = pytest.remote(shlex.split(args))
    if code:
        raise SystemExit(code)
