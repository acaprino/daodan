"""The CSS parsers compared in README.md, re-run on Modal: the same inputs and the same comparator for every candidate.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run modal_candidates.py

Candidates (exact pins, installed with --ignore-scripts at image build; the network is closed at run): css-tree, its
ESLint fork, PostCSS (core and `postcss-safe-parser`), Lightning CSS (with and without error recovery), tinycss2, and
the reader Daodan has today (`daodan/core/languages/stylesheet.py`, taken from this checkout). Inputs: `inputs.json`,
197 texts with the expectations written before any candidate ran. Corpus: the npm packages of
`corpus-packages.txt` at exact versions, their `.css` files read as data. The summary, the per-input table, the corpus
tables, the depth limits and the versions land in `results/`.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
BASE = "node:22.23.5-bookworm"  # the Node of the recorded run (v22.23.5); Python 3.12 is added to it
WORK, CORPUS = "/tools/candidates", "/corpus/node_modules"
JS_TOOLS = ("css-tree", "css-tree-eslint", "postcss", "postcss-safe", "lightning", "lightning-recovery")
# The corpus is installed one package at a time, as the probe did: the files a later install brings are part of it.
INSTALL_CORPUS = ("mkdir -p /corpus && cd /corpus && echo '{\"name\":\"corpus\",\"private\":true}' > package.json "
                  "&& while read p; do npm install --ignore-scripts --no-audit --no-fund --loglevel=error \"$p\" "
                  ">/dev/null 2>&1 || echo \"FAILED $p\"; done < /corpus-packages.txt")

if LOCAL:
    REPO = HERE.parents[2]
    LANGUAGES = REPO / "daodan/core/languages"
    image = (
        modal.Image.from_registry(BASE, add_python="3.12")
        .add_local_file(HERE / "package.json", "/tools/package.json", copy=True)
        .run_commands("cd /tools && npm install --ignore-scripts --no-audit --no-fund --loglevel=error")
        .add_local_file(HERE / "corpus-packages.txt", "/corpus-packages.txt", copy=True)
        .run_commands(INSTALL_CORPUS)
        .run_commands("python -m pip install --no-cache-dir tinycss2==1.5.1 cssselect==1.6.0 webencodings==0.6.1")
        .add_local_dir(HERE, WORK, ignore=["results/**", "out/**", "**/__pycache__/**", "lang/**"])
        # The current reader: its three files from this checkout, unchanged, and the two stubs that keep the package
        # `languages` from loading tree-sitter (`parse_sheet` does not use it).
        .add_local_file(LANGUAGES / "stylesheet.py", f"{WORK}/lang/languages/stylesheet.py")
        .add_local_file(LANGUAGES / "base.py", f"{WORK}/lang/languages/base.py")
        .add_local_file(LANGUAGES / "comments.py", f"{WORK}/lang/languages/comments.py")
        .add_local_file(HERE / "stub/__init__.py", f"{WORK}/lang/languages/__init__.py")
        .add_local_file(HERE / "stub/_treesitter.py", f"{WORK}/lang/languages/_treesitter.py")
    )
else:
    image = modal.Image.debian_slim()
app = modal.App("css-parser-candidates", image=image)


def step(log: list[str], command: list[str], **env: str) -> None:
    result = subprocess.run(command, cwd=WORK, capture_output=True, text=True, timeout=2800,
                            env={**os.environ, "OUT": "/tools/out", "CORPUS": CORPUS, **env})
    log.append(f"$ {' '.join(command)}  {env or ''}\n{result.stdout}{'--- STDERR ---' + chr(10) + result.stderr if result.stderr else ''}"
               f"--- exit {result.returncode}\n")


@app.function(cpu=4, memory=8192, timeout=3000, block_network=True)
def run() -> dict[str, str]:
    log: list[str] = []
    for tool in JS_TOOLS:
        step(log, ["node", "norm.mjs", tool])
    step(log, ["python", "-B", "norm_tinycss2.py"])
    step(log, ["python", "-B", "norm_current.py"])
    step(log, ["node", "compare.mjs"])
    step(log, ["node", "corpus.mjs"], CSSTREE="css-tree")
    step(log, ["node", "corpus.mjs"], CSSTREE="css-tree-eslint", TAG="_fork")
    for tool in JS_TOOLS[2:]:
        step(log, ["node", "corpus_tools.mjs", tool])
    step(log, ["python", "-B", "corpus_tinycss2.py"])
    step(log, ["python", "-B", "corpus_current.py"])
    step(log, ["node", "depth.mjs"], CSSTREE="css-tree")
    step(log, ["node", "depth.mjs"], CSSTREE="css-tree-eslint", TAG="_fork")
    versions = []
    for command in ("node --version", "python --version", "npm ls --all",
                    "pip list --format=freeze | grep -i -E '^(tinycss2|cssselect|webencodings)=='"):
        result = subprocess.run(command, shell=True, cwd="/tools", capture_output=True, text=True)
        versions.append(f"$ {command}\n{result.stdout}{result.stderr}")
    corpus = subprocess.run(["npm", "ls", "--depth=0"], cwd="/corpus", capture_output=True, text=True)
    count = subprocess.run("find /corpus/node_modules -name '*.css' | wc -l", shell=True, capture_output=True, text=True)
    versions.append(f"$ npm ls --depth=0   (the corpus)\n{corpus.stdout}\n.css files under node_modules: {count.stdout}")
    kept = {"console.txt": "\n".join(log), "versions.txt": "\n".join(versions)}
    for path in sorted(Path("/tools/out").iterdir()):
        if path.name.startswith(("corpus", "depth", "summary", "per-input")):
            kept[path.name] = path.read_text(encoding="utf-8")
    return kept


@app.local_entrypoint()
def main(out: str = ""):
    folder = Path(out) if out else HERE / "results"
    folder.mkdir(exist_ok=True)
    for name, text in run.remote().items():
        (folder / name).write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
        print(f"=== {name}: {len(text)} chars")
