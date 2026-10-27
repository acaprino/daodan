"""Discover and invoke an external DeckCraft CLI without shell interpolation.

This bridge owns argument transport, not a presentation engine or a filesystem
sandbox. DeckCraft's separately configured headless MCP server offers root limits.
"""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


REFERENCE_VERSION = "0.10.0"
MAX_PLAN_BYTES = 1024 * 1024


class BridgeError(ValueError):
    """An executable or command plan cannot be used as requested."""


def installed(environ):
    """The CLI that office:intake's engine_install.py put in the owned engine home, if any."""
    script = Path(__file__).resolve().parents[2] / "intake" / "scripts" / "engine_install.py"
    spec = importlib.util.spec_from_file_location("office_engine_install", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.find("deckcraft", environ)


def discover(binary=None, environ=None):
    env = os.environ if environ is None else environ
    selected = binary or env.get("DECKCRAFT_CLI")
    if selected:
        path = Path(selected).expanduser().resolve()
    else:
        found = shutil.which("deckcraft-cli", path=env.get("PATH", "")) or installed(env)
        if not found:
            raise BridgeError("deckcraft-cli is unavailable. Ask the user once, then run office:intake's engine_install.py install deckcraft --approved; or set DECKCRAFT_CLI to an existing executable. See references/runtime.md.")
        path = Path(found).resolve()
    if not path.is_file():
        raise BridgeError(f"DeckCraft executable is missing: {path}")
    try:
        probe = subprocess.run([str(path), "--version"], capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BridgeError(f"Cannot probe DeckCraft at {path}: {exc}") from exc
    match = re.fullmatch(r"deckcraft-cli (\d+\.\d+\.\d+(?:[-+][\w.-]+)?)", probe.stdout.strip())
    if probe.returncode or not match:
        raise BridgeError(f"Invalid DeckCraft version response: {probe.stderr.strip() or probe.stdout.strip()}")
    return {"binary": str(path), "version": match[1],
            "reference_version": REFERENCE_VERSION,
            "matches_reference": match[1] == REFERENCE_VERSION}


def invoke(binary, arguments):
    argv = [str(binary), *arguments]
    if os.name == "nt" and len(subprocess.list2cmdline(argv)) > 30000:
        raise BridgeError("Command plan exceeds the Windows argument limit. Split it into smaller saved-deck batches or use DeckCraft's MCP interface.")
    try:
        return subprocess.run(argv).returncode
    except OSError as exc:
        raise BridgeError(f"Cannot run DeckCraft: {exc}") from exc


def load_commands(path, editing=False):
    try:
        with Path(path).open("rb") as stream:
            data = stream.read(MAX_PLAN_BYTES + 1)
        if len(data) > MAX_PLAN_BYTES:
            raise BridgeError("Command plan exceeds the 1 MiB limit.")
        commands = json.loads(data.decode("utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BridgeError(f"Cannot read command plan: {exc}") from exc
    if not isinstance(commands, list) or not commands:
        raise BridgeError("Command plan must be a nonempty array of {command, params} objects.")
    for index, item in enumerate(commands):
        if (not isinstance(item, dict) or set(item) != {"command", "params"}
                or not isinstance(item["command"], str)
                or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.]*", item["command"])
                or not isinstance(item["params"], dict)):
            raise BridgeError(f"Invalid command at index {index}; expected {{command, params}}.")
        command = item["command"]
        if command.startswith(("file.", "app.")):
            if command != "file.new" or editing or index != 0:
                raise BridgeError(f"File operations are not allowed in apply plans: {command}. Use --input and --output; file.new is allowed only first for a new deck.")
    return commands


def apply_plan(binary, plan, output, source=None):
    output = Path(output).resolve()
    if source is not None:
        source = Path(source).resolve()
        if not source.is_file():
            raise BridgeError(f"Input presentation is missing: {source}")
        if source == output or (output.exists() and os.path.samefile(source, output)):
            raise BridgeError("Input and output must be different files.")
    if output.exists():
        raise BridgeError("Output already exists. Choose a new candidate path to preserve earlier results.")
    if output.suffix.lower() not in {".pptx", ".deckcraft"}:
        raise BridgeError("Output must be .pptx or .deckcraft; export PDF or images separately.")
    if not output.parent.is_dir():
        raise BridgeError(f"Output directory does not exist: {output.parent}")
    commands = load_commands(plan, editing=source is not None)
    arguments = ["run", "--print"]
    if source is not None:
        arguments.extend(["--in", str(source)])
    for item in commands:
        arguments.extend(["--cmd", item["command"] + "=" + json.dumps(item["params"], ensure_ascii=False, allow_nan=False, separators=(",", ":"))])
    arguments.extend(["--save", str(output)])
    code = invoke(binary, arguments)
    if code == 0 and not output.is_file():
        raise BridgeError("DeckCraft returned success without the requested output file.")
    return code


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", help="Absolute DeckCraft CLI executable path")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("discover")
    cli = commands.add_parser("cli", add_help=False)
    cli.add_argument("arguments", nargs=argparse.REMAINDER)
    apply = commands.add_parser("apply")
    apply.add_argument("--commands", required=True, type=Path)
    apply.add_argument("--input", type=Path)
    apply.add_argument("--output", required=True, type=Path)
    # REMAINDER owns upstream options, including --help and --version.
    arguments = list(sys.argv[1:] if argv is None else argv)
    prefix = (2 if arguments[:1] == ["--binary"] else
              1 if arguments and arguments[0].startswith("--binary=") else 0)
    if arguments[prefix:prefix + 1] == ["cli"]:
        arguments.insert(prefix + 1, "--")
    args = parser.parse_args(arguments)
    try:
        runtime = discover(args.binary)
        if args.command == "discover":
            print(json.dumps(runtime, indent=2))
            return 0
        if args.command == "cli":
            forwarded = args.arguments
            while forwarded[:1] == ["--"]:
                forwarded = forwarded[1:]
            return invoke(runtime["binary"], forwarded)
        return apply_plan(runtime["binary"], args.commands, args.output, args.input)
    except (BridgeError, ValueError) as exc:
        print(f"deckcraft-bridge: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
