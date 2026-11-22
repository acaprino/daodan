"""The secrets in a text that leaves this machine or goes to a model, found by Secretlint and masked.

A project's configuration is the project's code. Each of these loads it when the pinned 14.0.1 executable is
started the naive way, in the project or with the variable set (measured on Linux x64, 20 November 2026,
`test_the_real_secretlint_loads_nothing_of_the_project`):
- the project's `.secretlintrc.js`, found from the working directory up to the root, is run;
- the project's `.secretlintrc.json` that names a rule imports that rule's module from the project's `node_modules`;
- the project's `bunfig.toml`, read by Bun from the working directory, runs the scripts it preloads;
- `BUN_OPTIONS=--preload <script>` runs that script;
- `NODE_PATH` leads a configuration's rule id to a module in the project's `node_modules`.
So it runs in its own folder, outside every project, with Daodan's configuration named (`--secretlintrc`,
`daodan/data/secretlintrc.json`: only the built-in recommended preset), without the `BUN_`, `NODE_` and `DEBUG`
variables (`DEBUG=*secretlint*` would print the text to stderr), and with the text on its standard input under the
file's bare name (`--stdinFileName`): no path into the project reaches it. Started so, it loads none of the five.

One process per text with `--format=json`, and the ranges it reports masked here: `--format=mask-result`, its own
masking, gives the text without the rules that matched, so it would cost a second process, and it masks line
breaks too, which would move the lines of everything after a private key. The ranges are UTF-16 code units, as
JavaScript counts them.
"""
from __future__ import annotations

import functools
import hashlib
import json
import os
import subprocess
from pathlib import Path, PurePosixPath

from container import Gap

VERSION = "14.0.1"
# The release's own `secretlint-14.0.1-sha256sum.txt`, per platform key of `engine_tools._platform()`.
ASSETS = {
    "win-x64": ("windows-x64.exe", "e38bd0d066fd12e281942c052d4e56309de67b82d94252c2b6169e21cb720ad7"),
    "linux-x64": ("linux-x64", "4fe869e7fe3d1bb3bf24003bea6b556d3a6d5343c393ca85301cae70c935fa98"),
    "linux-arm64": ("linux-arm64", "2c7a8d6001aff8342895b35008f94f55bc49bb4cd9f6c3b8b637998a82558a2f"),
    "osx-x64": ("darwin-x64", "2bab03da1a1da8589e7a5fdfa3c36983139c17e0fa5512a269eb197c26555c94"),
    "osx-arm64": ("darwin-arm64", "533830b60fb38b7746b5a0d0949d74667479c58fc3fcc60951014de76fab7c42"),
}
CONFIG = Path(__file__).resolve().parents[1] / "data" / "secretlintrc.json"
TIMEOUT = 120  # seconds for one text, start included; the real start and scan times are not measured yet
UNSET = ("BUN_", "NODE_")  # what the executable would read as its own options or module paths


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@functools.cache
def executable() -> Path:
    """The pinned Secretlint of this platform, downloaded on the first call into Daodan's shared tool folder and
    checked by its release's sha256 before its first start in this process."""
    import engine_tools
    platform = engine_tools._platform()
    if platform not in ASSETS:
        raise Gap(f"Secretlint {VERSION} publishes no executable for {platform}", "check the text elsewhere")
    asset, digest = ASSETS[platform]
    binary = engine_tools.shared_engine_dir("secretlint") / VERSION / engine_tools.executable_name("secretlint")
    try:
        if not binary.is_file():
            engine_tools.download("https://github.com/secretlint/secretlint/releases/download/"
                                  f"v{VERSION}/secretlint-{VERSION}-{asset}", binary, sha256=digest)
        elif _sha256(binary) != digest:
            raise ValueError(f"{binary} is not the release's file (sha256 differs)")
        if os.name != "nt":
            binary.chmod(0o755)
    except (OSError, ValueError) as error:
        raise Gap(f"Secretlint {VERSION} could not be downloaded and verified: {error}",
                  "check the connection to github.com, or remove the file and retry") from error
    return binary


def command(program: Path, name: str) -> list[str]:
    """The command line that checks a text named `name` on standard input."""
    bare = PurePosixPath(name.replace("\\", "/")).name or "text"
    return [str(program), f"--secretlintrc={CONFIG}", "--format=json", f"--stdinFileName={bare}"]


def _environment() -> dict:
    return {key: value for key, value in os.environ.items()
            if not key.upper().startswith(UNSET) and key.upper() != "DEBUG"}


def _mask(text: str, ranges: list) -> str:
    """`text` with every unit of each range a `*`, line breaks kept."""
    original = text.encode("utf-16-le")
    units = bytearray(original)
    for start, end in ranges:
        if not (type(start) is int and type(end) is int and 0 <= start < end <= len(units) // 2):
            raise ValueError(f"range {start}..{end} is outside the text")
        if any(0xdc <= original[2 * edge + 1] <= 0xdf for edge in (start, end) if 2 * edge < len(units)):
            raise ValueError("range splits a UTF-16 surrogate pair")
        for unit in range(start, end):
            if units[2 * unit:2 * unit + 2] not in (b"\n\x00", b"\r\x00"):
                units[2 * unit:2 * unit + 2] = b"*\x00"
    return units.decode("utf-16-le")


def masked(text: str, name: str) -> dict:
    """`{text, found, kinds}`: the text with each secret Secretlint finds masked, how many it found, the rules that
    found them. Without the executable, on a timeout, a failure or an answer it cannot read: `Gap`, and no text."""
    if not text.strip():
        return {"text": text, "found": 0, "kinds": []}
    program = executable()
    bom = "﻿" if text.startswith("﻿") else ""  # the executable decodes its input without it
    try:
        run = subprocess.run(command(program, name), input=text[len(bom):].encode("utf-8"),
                             capture_output=True, cwd=program.parent, env=_environment(), timeout=TIMEOUT)
    except subprocess.TimeoutExpired as error:
        raise Gap(f"Secretlint did not answer within {TIMEOUT} s on {name}", "check a smaller text") from error
    except UnicodeError as error:
        raise Gap("The text contains invalid Unicode", "check the source encoding") from error
    except OSError as error:
        raise Gap(f"Secretlint could not start: {error}", "check the executable in Daodan's tool folder") \
            from error
    said = run.stderr.decode("utf-8", "replace").strip()[-400:]
    try:
        if run.returncode not in (0, 1):
            raise ValueError(f"exit status {run.returncode}")
        results = json.loads(run.stdout)
        if not isinstance(results, list) or len(results) != 1 or not isinstance(results[0]["messages"], list):
            raise ValueError("expected one scan result for standard input")
        messages = results[0]["messages"]
        if run.returncode == 1 and not messages:
            raise ValueError("scanner reported a finding without a range")
        ranges = [tuple(message["range"]) for message in messages]
        text = bom + _mask(text[len(bom):], ranges)
    except (ValueError, KeyError, TypeError) as error:
        raise Gap(f"Secretlint failed on {name}: {error}; {said or 'no message'}",
                        "check the executable in Daodan's tool folder") from error
    return {"text": text, "found": len(messages), "kinds": sorted({str(message.get("ruleId")) for message in messages})}


UNAVAILABLE = "Project content withheld: Secretlint could not verify the response."


def _source_field(block):
    """Strip only source_reader's verified display prefixes. Restore them after scanning the actual lines."""
    start, end = block["start"], block["end"]
    lines = block["source"].split("\n")
    if (type(start) is not int or type(end) is not int or start < 1 or end < start
            or len(lines) != end - start + 2 or lines[-1] != ""):
        raise ValueError("invalid numbered source block")
    raw = []
    for number, line in enumerate(lines[:-1], start):
        prefix = f"{number}: "
        if not line.startswith(prefix):
            raise ValueError("invalid source line number")
        raw.append(line[len(prefix):])

    def serialize(text):
        return json.dumps("".join(f"{number}: {line}\n" for number, line in enumerate(text.split("\n")[:-1], start)))

    return "\n".join(raw) + "\n", serialize


def _tool_parts(item):
    """Pairs of scanner text and its JSON output. Only string contents have an editable serializer.

    json.dumps alone escapes newlines and quotes inside source. Give the text scanner decoded values,
    keeping key/value punctuation and consecutive lines, and let json.dumps quote the result for output.
    """
    if isinstance(item, dict):
        yield "{", "{"
        for index, (key, child) in enumerate(item.items()):
            name = key
            if not isinstance(key, str):
                if key is not None and not isinstance(key, (int, float)):
                    raise ValueError("invalid JSON key")
                name = json.dumps(key, allow_nan=False)
                if name in item:
                    raise ValueError("ambiguous JSON key")
            if index:
                yield ",\n", ","
            yield '"', '"'
            yield name, json.dumps(name)[1:-1]
            yield '": ', '": '
            if key == "source" and "start" in item and "end" in item and isinstance(child, str):
                yield '"\n', ""
                yield _source_field(item)
                yield '"', ""
            else:
                yield from _tool_parts(child)
        yield "}", "}"
    elif isinstance(item, (list, tuple)):
        yield "[\n", "["
        for index, child in enumerate(item):
            if index:
                yield "\n", ","
            if isinstance(child, str):
                yield child, json.dumps
            else:
                yield from _tool_parts(child)
        yield "\n]", "]"
    elif isinstance(item, str):
        yield '"\n' if "\n" in item else '"', ""
        yield item, json.dumps
        yield '\n"' if "\n" in item else '"', ""
    else:
        literal = json.dumps(item, allow_nan=False)
        yield literal, literal


def tool_result(value: dict) -> dict:
    """Check the whole local response once. Keep its JSON shape, or withhold it if redaction would change it."""
    try:
        parts = list(_tool_parts(value))
        source = "".join(raw for raw, _output in parts)
        checked = masked(source, "tool-output.txt")
        if not checked["found"]:
            if checked["text"] != source:
                raise ValueError("unexpected clean scan")
            return value
        encoded = checked["text"].encode("utf-16-le")
        offset, redactions = 0, {}
        for raw, output in parts:
            end = offset + len(raw.encode("utf-16-le"))
            replacement = encoded[offset:end].decode("utf-16-le")
            if replacement != raw:
                if not callable(output) or replacement != redactions.setdefault(raw, replacement):
                    raise ValueError("ambiguous redaction")
            offset = end
        if offset != len(encoded) or "masked_secrets" in value:
            raise ValueError("invalid masked response")
        wire = []
        for raw, output in parts:
            if callable(output):
                wire.append(output(redactions.get(raw, raw)))
            elif raw in redactions:
                raise ValueError("a protected JSON token also contains a redacted value")
            else:
                wire.append(output)
        return {**json.loads("".join(wire)), "masked_secrets": checked["found"]}
    except Exception:
        # A diagnostic from the scanner can quote its input.
        return {"status": "withheld", "error": UNAVAILABLE}
