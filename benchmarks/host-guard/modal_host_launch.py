"""A probe of the host, not of Daodan: how Claude Code starts a stdio MCP server a plugin declares. No model call.

A plugin made here declares a server that records its command line, working directory and three variables, then
ends. `claude mcp list` starts it from a project's folder.

    modal run modal_host_launch.py
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import modal

image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git", "curl", "ca-certificates", "nodejs", "npm")
    .run_commands("npm install -g @anthropic-ai/claude-code", "useradd -m runner")
)
app = modal.App("daodan-host-launch-probe", image=image)

PROBE = '''import json, os, sys, time
out = "/tmp/probe/%d-%d.json" % (int(time.time() * 1000), os.getpid())
os.makedirs("/tmp/probe", exist_ok=True)
json.dump({"argv": sys.argv[1:], "cwd": os.getcwd(),
           "env": {name: os.environ.get(name) for name in ("CLAUDE_PROJECT_DIR", "CLAUDE_PLUGIN_ROOT", "PWD")}},
          open(out, "w"))
'''


@app.function(cpu=2, memory=2048, timeout=900)
def probe() -> dict:
    market, home = Path("/probe-market"), Path("/home/runner")
    plugin = market / "probe"
    (market / ".claude-plugin").mkdir(parents=True)
    (plugin / ".claude-plugin").mkdir(parents=True)
    (market / ".claude-plugin/marketplace.json").write_text(json.dumps({
        "name": "probe-market", "owner": {"name": "probe"},
        "plugins": [{"name": "probe", "source": "./probe", "description": "launch probe"}]}))
    (plugin / ".claude-plugin/plugin.json").write_text(json.dumps({"name": "probe", "version": "1.0.0",
                                                                    "description": "launch probe"}))
    (plugin / "probe.py").write_text(PROBE)
    (plugin / ".mcp.json").write_text(json.dumps({"mcpServers": {"probe": {
        "command": "python3", "args": ["${CLAUDE_PLUGIN_ROOT}/probe.py", "--project", "${CLAUDE_PROJECT_DIR}",
                                       "--unset", "${DAODAN_PROBE_UNSET}"]}}}))
    project = home / "project"
    (project / "sub").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(project)], check=False)
    subprocess.run(["chown", "-R", "runner:runner", str(home), str(market)], check=True)
    Path("/tmp/probe").mkdir(exist_ok=True)
    subprocess.run(["chmod", "777", "/tmp/probe"], check=True)
    said = {}

    def run(label: str, cwd: Path, *words: str) -> None:
        done = subprocess.run(["runuser", "-u", "runner", "--", "env", f"HOME={home}", "claude", *words], cwd=cwd,
                              capture_output=True, text=True, timeout=300)
        said[label] = {"exit": done.returncode, "out": (done.stdout + done.stderr)[-1200:]}

    run("version", project, "--version")
    run("marketplace add", project, "plugin", "marketplace", "add", str(market))
    run("install", project, "plugin", "install", "probe@probe-market")
    run("mcp list in the project", project, "mcp", "list")
    first = sorted(Path("/tmp/probe").glob("*.json"))
    run("mcp list in a subfolder", project / "sub", "mcp", "list")
    records = {"in the project": [json.loads(path.read_text()) for path in first],
               "in a subfolder": [json.loads(path.read_text()) for path in sorted(Path("/tmp/probe").glob("*.json"))
                                  if path not in first]}
    return {"said": said, "records": records, "plugin root": str(plugin), "project": str(project)}


@app.local_entrypoint()
def main():
    print(json.dumps(probe.remote(), indent=1), flush=True)
