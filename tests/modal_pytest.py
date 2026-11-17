"""The test suites on Modal: pytest in a Linux container over the working tree, nothing on this PC.

    python tests/modal_pytest.py tests/test_codebase_map_premap.py -q -k toolchains
    python tests/modal_pytest.py -q                      # every suite under tests/

The launcher starts `modal run` on this file with the arguments as given; the container holds the checkout as it
is on disk (plugins, tests, benchmarks), runs `python -B -m pytest -p no:cacheprovider` in
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
# Daodan's Node (`preparation.NODE`, checked by its sha256) runs `indexers/components.cjs` in its own tests
# (test_codebase_map_components.py), over the packages its recorded outputs were made with, in /opt/components.
NODE = ("https://nodejs.org/dist/v24.22.3/node-v24.22.3-linux-x64.tar.gz",
        "061ec3e3062115705b56b51fa9cc330ab50d34b6969387d4e4b1a50c6809acc2")
FETCH_NODE = ("python -c \"import hashlib, urllib.request; data = urllib.request.urlopen('%s').read(); "
              "assert hashlib.sha256(data).hexdigest() == '%s'; open('/tmp/node.tar.gz', 'wb').write(data)\"" % NODE)
COMPONENTS = ("vue@3.5.22", "typescript@5.6.3", "@vue/language-core@3.3.14", "svelte2tsx@0.7.63")
# The @babel/core the JavaScript recorder prints with (`dynamic/javascript.py`, BABEL), in a layer of its own: its
# tests under a real Node (test_codebase_map_dynamic_javascript.py) find it through DAODAN_TEST_BABEL.
BABEL = ("7.29.7", "/opt/babel/node_modules/@babel/core")
# Debian's headless JDK 17 builds and runs the JVM recorder in its own tests (test_codebase_map_dynamic_jvm.py);
# its package wants the manual folder the slim image leaves out.
image = (modal.Image.debian_slim(python_version="3.13")
         .run_commands("mkdir -p /usr/share/man/man1")
         .apt_install("git", "ca-certificates", "xz-utils", "openjdk-17-jdk-headless")
         .run_commands(FETCH_NODE, "tar -xzf /tmp/node.tar.gz -C /opt && rm /tmp/node.tar.gz",
                       "ln -s /opt/node-v24.22.3-linux-x64/bin/node /usr/local/bin/node",
                       "ln -s /opt/node-v24.22.3-linux-x64/bin/npm /usr/local/bin/npm",
                       "npm install --prefix /opt/components --no-audit --no-fund --ignore-scripts "
                       + " ".join(COMPONENTS))
         .run_commands(f"npm install --prefix /opt/babel --no-audit --no-fund --ignore-scripts @babel/core@{BABEL[0]}")
         .pip_install("pytest", "pytest-xdist", "uv==0.11.28", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5",
                      "sqlglot>=30"))
if LOCAL:
    # The results stay: suites replay the recorded answers kept there. The explorer's sources are no suite's.
    skipped = ["**/__pycache__/**", "**/node_modules/**", "**/.pytest_cache/**", "codebase-explorer/**"]
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
    environment = {**os.environ, "PYTHONUTF8": "1", "DAODAN_TEST_BABEL": BABEL[1]}
    return subprocess.run(command, cwd=REMOTE, env=environment).returncode


@app.local_entrypoint()
def main(args: str = ""):
    code = pytest.remote(shlex.split(args))
    if code:
        raise SystemExit(code)
