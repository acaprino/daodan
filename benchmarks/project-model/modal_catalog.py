"""The benchmark's own scripts on Modal: corpus check, ANAGRAFICA.md, score tables, round report; nothing on this PC.

    python benchmarks/project-model/modal_catalog.py                  # check, ANAGRAFICA.md, tables of every tool
    python benchmarks/project-model/modal_catalog.py syft,trivy js    # the tables of some tools on some fixtures
    python benchmarks/project-model/modal_catalog.py report ROUND.json [MORE.json ...] [--out MD] [--compare OLD]

The launcher starts `modal run` on this file. In a container with no network, over the benchmark folder as it is on
disk, `score.py --check all`, `catalog.py` and `score.py <tools> <fixtures>` run; the client prints the check and
the tables, writes ANAGRAFICA.md, the only file it writes, and ends with the check's exit code. `report` runs
`pipeline_report.py` with the same arguments, files inside the benchmark folder; the client writes the report's
two files as the container wrote them and prints what the report prints.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import os
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REMOTE = "/pm"  # a container path: a POSIX string, whatever runs the client
PROXIES = ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy")

if __name__ == "__main__":  # the launcher: Modal's client does not go through a proxy of this shell
    environment = {key: value for key, value in os.environ.items() if key not in PROXIES}
    environment.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    raise SystemExit(subprocess.run(["modal", "run", str(Path(__file__).resolve()), "--args",
                                     shlex.join(sys.argv[1:])], env=environment).returncode)

import modal  # noqa: E402

image = modal.Image.debian_slim(python_version="3.13")
if modal.is_local():
    image = image.add_local_dir(HERE, REMOTE, ignore=["**/__pycache__/**"])
app = modal.App("daodan-pm-catalog", image=image)


@app.function(cpu=1, memory=2048, timeout=600, block_network=True)
def run(tools: str, fixtures: str) -> dict:
    """The check's output and exit code, ANAGRAFICA.md's text and the tables, from the uploaded folder."""
    sys.path.insert(0, REMOTE)
    import catalog
    import score

    with contextlib.redirect_stdout(io.StringIO()) as check:
        code = score.run_check("all")
    with contextlib.redirect_stdout(io.StringIO()) as tables:
        score.run_tables(tools, fixtures)
    return {"check": check.getvalue(), "code": code, "catalog": catalog.render(*catalog.load()),
            "tables": tables.getvalue()}


@app.function(cpu=1, memory=2048, timeout=600, block_network=True)
def report(sent: list) -> dict:
    """pipeline_report.py over the uploaded folder."""
    sys.path.insert(0, REMOTE)
    return report_here(sent, Path(REMOTE))


def report_args(argv: list, root: Path = HERE) -> tuple:
    """`report`'s arguments as they go up, their paths relative to `root`, and where the Markdown goes here."""
    parser = argparse.ArgumentParser(prog="modal_catalog.py report", description="pipeline_report.py on Modal")
    parser.add_argument("files", nargs="+", help="outputs of modal_pipeline.py; later ones replace earlier cases")
    parser.add_argument("--out", help="the Markdown to write; the numbers go beside it as .json")
    parser.add_argument("--compare", help="the .json of an earlier report, or an earlier round's output")
    args = parser.parse_args(argv)
    out = Path(args.out) if args.out else Path(args.files[-1]).with_suffix(".report.md")

    def inside(path):  # the folder goes up whole, so a path travels as its place in it
        try:
            return Path(path).resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            raise SystemExit(f"{path}: outside {root}, the only folder the container has; move it there") from None

    sent = [inside(file) for file in args.files] + ["--out", inside(out)]
    return sent + (["--compare", inside(args.compare)] if args.compare else []), out


def report_here(sent: list, root: Path) -> dict:
    """pipeline_report.py on `sent`, paths relative to `root`: what it prints and the bytes of the files it writes."""
    import pipeline_report

    argv = [arg if arg.startswith("--") else str(root / arg) for arg in sent]
    with contextlib.redirect_stdout(io.StringIO()) as printed:
        pipeline_report.main(argv)
    out = Path(argv[argv.index("--out") + 1])
    return {"printed": printed.getvalue(), "md": out.read_bytes(), "json": out.with_suffix(".json").read_bytes()}


def write_report(result: dict, out: Path) -> None:
    """The report's two files here, byte for byte as the container wrote them."""
    out.write_bytes(result["md"])
    out.with_suffix(".json").write_bytes(result["json"])


@app.local_entrypoint()
def main(args: str = ""):
    argv = shlex.split(args)
    if argv[:1] == ["report"]:
        sent, out = report_args(argv[1:])
        result = report.remote(sent)
        write_report(result, out)
        print(result["printed"], end="")
        return
    tools, fixtures = (argv + ["all", "all"])[:2]
    out = run.remote(tools, fixtures)
    print(out["check"] + out["tables"], end="")
    with open(HERE / "ANAGRAFICA.md", "w", encoding="utf-8", newline="\n") as f:
        f.write(out["catalog"])
    print(f"\nwrote {HERE / 'ANAGRAFICA.md'}")
    if out["code"]:
        raise SystemExit(out["code"])
