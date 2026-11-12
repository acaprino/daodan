"""Phase 3 runs on Modal: the same review of phazly with groups by path (A), units (B), or groups plus flows (C).

One container per run, a fresh `claude -p` session each, Daodan plugins from this checkout. The app is
deployed and the runs are spawned, so a lost local connection does not cancel them; each run writes its
review directory and the session's JSON result to the volume `daodan-flow-results`.

    modal deploy benchmarks/phazly-flow/phase3/modal_review.py
    python benchmarks/phazly-flow/phase3/modal_review.py spawn --archive PHAZLY.tar --tag TAG
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
PLUGINS = HERE.parents[2] / "plugins" if modal.is_local() else Path("/daodan/plugins")

REQUEST = ("Fai una review con senior-review, branch review sul contenuto, con il metodo completo (review-method), "
           "senza chiedere conferme: area «la logica dei widget della home e dell'inserimento». Perimetro: esattamente "
           "i file elencati in /home/runner/inputs/perimeter.txt, percorsi relativi alla radice del progetto. Revisori, "
           "uguali per tutte le run: logic-integrity-auditor, local-correctness-auditor, react-auditor, ui-race-auditor. "
           "Mappa: usa Codebase Map; se non c'è un run utilizzabile crealo lite su react-app. Consegna il rapporto finale.")
ARMS = {
    "A": REQUEST,
    "B": REQUEST + (" Nei binding di composition.py bind aggiungi a coverage il campo units con il contenuto di "
                    "/home/runner/inputs/units.json (lista di gruppi di file): ogni unità è un incarico."),
    "C": REQUEST + (" Prima di preparare gli incarichi aggiungi a 01-context.md una sezione «Flussi» con il contenuto di "
                    "/home/runner/inputs/flows.md, senza modificarlo."),
}

image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git", "curl", "ca-certificates", "nodejs", "npm")
    .run_commands("npm install -g @anthropic-ai/claude-code", "useradd -m runner")
    .pip_install("uv", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
    .add_local_dir(PLUGINS, "/daodan/plugins",
                   ignore=["**/__pycache__/**", "**/node_modules/**", "**/tests/**", "**/viewer/**"])
    .add_local_dir(HERE, "/inputs", ignore=["*.py", "results/**"])
)
app = modal.App("daodan-phase3-review", image=image)
# The account the runs bill: its OAuth token (`claude setup-token`) as CLAUDE_CODE_OAUTH_TOKEN.
CLAUDE_SECRET = "claude-code-alt"
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


@app.function(cpu=4, memory=16384, timeout=2 * 3600, volumes={"/results": volume},
              secrets=[modal.Secret.from_name(CLAUDE_SECRET)])
def review(arm: str, rep: int, archive: bytes, tag: str) -> dict:
    import io
    import os
    import shutil
    import subprocess
    import tarfile
    import time

    home = Path("/home/runner")
    project, inputs = home / "phazly", home / "inputs"
    project.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(project, filter="data")
    shutil.copytree("/inputs", inputs)
    subprocess.run(["chown", "-R", "runner:runner", str(home)], check=True)
    as_runner = ["runuser", "-u", "runner", "--"]
    for command in (["git", "init", "-q"], ["git", "add", "-A"],
                    ["git", "-c", "user.name=bench", "-c", "user.email=bench@local", "commit", "-qm", "case"]):
        subprocess.run([*as_runner, *command], cwd=project, check=True, capture_output=True)
    env = {**os.environ, "HOME": str(home), "USER": "runner"}
    command = [*as_runner, "env", f"HOME={home}", "claude", "-p", ARMS[arm], "--model", "claude-sonnet-5-5",
               "--plugin-dir", "/daodan/plugins/codebase-map", "--plugin-dir", "/daodan/plugins/senior-review",
               "--dangerously-skip-permissions", "--output-format", "stream-json", "--verbose"]
    # The session streams one event per line to a local file: progress is readable during the run
    # (`modal container exec ... tail /home/runner/stream.jsonl`) and a run cut by the timeout keeps its trace.
    stream = home / "stream.jsonl"
    started, timed_out = time.time(), False
    with stream.open("w", encoding="utf-8") as sink:
        process = subprocess.Popen(command, cwd=project, env=env, stdout=sink, stderr=subprocess.PIPE, text=True)
        try:
            _, error = process.communicate(timeout=2 * 3600 - 600)
        except subprocess.TimeoutExpired:
            process.kill()
            _, error = process.communicate()
            timed_out = True
    seconds = round(time.time() - started)
    out = Path("/results") / tag / f"{arm}{rep}"
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(stream, out / "stream.jsonl")
    (out / "stderr.txt").write_text((error or "")[-20000:], encoding="utf-8")
    # The review chooses its own directory: keep every place a run of 12 November used.
    for name, place in (("review", project / ".daodan" / "review"), ("team-review", project / ".team-review"),
                        ("tmp-rv", Path("/tmp/rv"))):
        if place.is_dir():
            shutil.make_archive(str(out / name), "gztar", place)
    result = {}
    for line in stream.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "result":
            result = event
    summary = {"arm": arm, "rep": rep, "returncode": process.returncode, "timed_out": timed_out, "seconds": seconds,
               "cost_usd": result.get("total_cost_usd"), "turns": result.get("num_turns"),
               "result": (result.get("result") or "")[-4000:]}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    volume.commit()
    return summary


@app.function(cpu=2, memory=4096, timeout=900, secrets=[modal.Secret.from_name(CLAUDE_SECRET)])
def probe() -> dict:
    """One short session in the same setup: the CLI authenticates, loads both plugins and reaches the map server."""
    import os
    import subprocess

    home = Path("/home/runner")
    work = home / "probe"
    work.mkdir(parents=True, exist_ok=True)
    (work / "hello.py").write_text("def greet():\n    return 'hi'\n", encoding="utf-8")
    subprocess.run(["chown", "-R", "runner:runner", str(home)], check=True)
    as_runner = ["runuser", "-u", "runner", "--", "env", f"HOME={home}"]
    subprocess.run([*as_runner, "git", "init", "-q"], cwd=work, check=True)
    version = subprocess.run([*as_runner, "claude", "--version"], capture_output=True, text=True)
    prompt = ("Rispondi solo con una riga JSON: {\"skills\": [le skill disponibili il cui nome contiene review o map], "
              "\"mcp\": [gli strumenti MCP il cui nome contiene codebase_map], "
              "\"runs\": il risultato di codebase_map_runs chiamato davvero}")
    done = subprocess.run([*as_runner, "claude", "-p", prompt, "--model", "claude-sonnet-5-5",
                           "--plugin-dir", "/daodan/plugins/codebase-map", "--plugin-dir", "/daodan/plugins/senior-review",
                           "--dangerously-skip-permissions", "--output-format", "json"],
                          cwd=work, env={**os.environ, "HOME": str(home)}, capture_output=True, text=True, timeout=800)
    result = {"version": (version.stdout + version.stderr).strip(), "returncode": done.returncode,
              "stdout": done.stdout[-6000:], "stderr": done.stderr[-3000:],
              "auth_env": sorted(key for key in os.environ if "ANTHROPIC" in key or "CLAUDE" in key)}
    print(json.dumps(result, ensure_ascii=False))
    return result


def spawn(archive: str, tag: str, arms: str = "A,B,C", reps: int = 2) -> None:
    function = modal.Function.from_name("daodan-phase3-review", "review")
    data = Path(archive).read_bytes()
    calls = {f"{arm}{rep}": function.spawn(arm, rep, data, tag).object_id
             for arm in arms.split(",") for rep in range(1, reps + 1)}
    print(json.dumps(calls, indent=2))


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "spawn":
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("command")
        parser.add_argument("--archive", required=True)
        parser.add_argument("--tag", required=True)
        parser.add_argument("--arms", default="A,B,C")
        parser.add_argument("--reps", type=int, default=2)
        args = parser.parse_args()
        spawn(args.archive, args.tag, args.arms, args.reps)
