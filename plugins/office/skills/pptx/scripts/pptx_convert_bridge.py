"""Discover and invoke the Office HTML to PPTX conversion driver.

This bridge owns argument transport and the vendored-engine hash guard, not the
conversion itself. The pinned engine bundle, its manifest and the driver live
under ``../lib/open-slide-pptx``; the input contract, runtime prerequisites and
recovery steps are in ``references/html-to-pptx.md``.
"""

import argparse
import contextlib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


LIB = Path(__file__).resolve().parent.parent / "lib" / "open-slide-pptx"
DRIVER = LIB / "driver.mjs"
BUNDLE = LIB / "bundle" / "open-slide-pptx.js"
MANIFEST = LIB / "manifest.json"
UPSTREAM_NOTE = LIB / "UPSTREAM.md"
PROBE_TIMEOUT_SECONDS = 120
CONVERT_TIMEOUT_SECONDS = 900
VERSION_TIMEOUT_SECONDS = 30


class BridgeError(ValueError):
    """A runtime, job or vendored-engine guard cannot be satisfied.

    ``code`` is the process exit status: the driver's own code (2 job or design
    contract, 3 missing runtime, 4 conversion failure) when the driver decided,
    otherwise 1 for a bridge-side check.
    """

    def __init__(self, message, code=1):
        super().__init__(message)
        self.code = code


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_node_version(text):
    parts = (text or "").strip().lstrip("v").split(".")
    if len(parts) < 2:
        return None
    try:
        return (int(parts[0]), int(parts[1]))
    except ValueError:
        return None


def node_supported(version):
    """The vendored engine declares Node ^20.19.0 or >=22.12.0."""
    major, minor = version
    if major > 22:
        return True
    if major == 22:
        return minor >= 12
    if major == 20:
        return minor >= 19
    return False


def verify_manifest(lib=LIB):
    """Recompute every recorded hash so a silent edit of the vendor fails here."""
    path = Path(lib) / "manifest.json"
    if not path.is_file():
        raise BridgeError(f"The engine manifest is missing: {path}. Rebuild the vendor with: node rebuild.mjs")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BridgeError(f"Cannot read the engine manifest {path}: {exc}") from exc
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise BridgeError(f"The engine manifest records no file hashes: {path}")
    for name, digest in sorted(files.items()):
        target = Path(lib) / name
        if not target.is_file():
            raise BridgeError(f"A file recorded in manifest.json is missing: {target}")
        if not isinstance(digest, str) or sha256(target) != digest:
            content = target.read_bytes()
            if b"\r\n" in content and hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest() == digest:
                raise BridgeError(
                    f"The checkout converted the line endings of {name}. Reinstall the plugin from a "
                    "clone that honours the repository .gitattributes (or with core.autocrlf=false); "
                    "the engine itself is unchanged.")
            raise BridgeError(
                f"Vendored engine content changed: {name}. Those files are read-only; refresh them "
                f"through the protocol in {UPSTREAM_NOTE.name} and rebuild the bundle.")
    bundle = manifest.get("bundle") or {}
    if bundle.get("sha256") != files.get("bundle/open-slide-pptx.js"):
        raise BridgeError("manifest.json disagrees with itself about the bundle hash")
    return manifest


def discover(node=None, environ=None):
    env = os.environ if environ is None else environ
    selected = node or env.get("OFFICE_PPTX_NODE")
    if selected:
        executable = Path(selected).expanduser().resolve()
    else:
        found = shutil.which("node", path=env.get("PATH", ""))
        if not found:
            raise BridgeError(
                "node is unavailable. Install Node.js 20.19+ or 22.12+, or set OFFICE_PPTX_NODE to its "
                "executable; see references/html-to-pptx.md.")
        executable = Path(found).resolve()
    if not executable.is_file():
        raise BridgeError(f"The Node executable is missing: {executable}")
    try:
        probe = subprocess.run([str(executable), "--version"], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=VERSION_TIMEOUT_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BridgeError(f"Cannot probe Node at {executable}: {exc}") from exc
    if probe.returncode:
        raise BridgeError(f"Invalid Node version response: {probe.stderr.strip() or probe.stdout.strip()}")
    version = parse_node_version(probe.stdout)
    if version is None:
        raise BridgeError(f"Cannot parse the Node version: {probe.stdout.strip()}")
    if not node_supported(version):
        raise BridgeError(
            f"Node {version[0]}.{version[1]} is unsupported; the vendored engine requires ^20.19.0 or >=22.12.0.")
    if not DRIVER.is_file():
        raise BridgeError(f"The conversion driver is missing: {DRIVER}")
    if not BUNDLE.is_file():
        raise BridgeError(
            f"The engine bundle is missing: {BUNDLE}. Rebuild the vendor with: node rebuild.mjs (see {UPSTREAM_NOTE}).")
    manifest = verify_manifest()
    return {
        "node": str(executable),
        "node_version": f"{version[0]}.{version[1]}",
        "lib": str(LIB),
        "bundle": str(BUNDLE),
        "bundle_sha256": manifest["bundle"]["sha256"],
        "engine": {
            "package": manifest["upstream"]["package"],
            "version": manifest["upstream"]["version"],
            "git_ref": manifest["upstream"]["git_ref"],
            "license": manifest["upstream"]["license"],
        },
    }


def last_json(text):
    for line in reversed((text or "").strip().splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return None


def probe(runtime, timeout=PROBE_TIMEOUT_SECONDS):
    """Report the actual driver runtime; any missing prerequisite is a stop."""
    try:
        completed = subprocess.run([runtime["node"], str(DRIVER), "--probe"], capture_output=True,
                                   text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BridgeError(f"Cannot probe the conversion driver: {exc}") from exc
    payload = last_json(completed.stdout)
    if payload is None:
        raise BridgeError(
            f"The conversion driver produced no probe record (exit {completed.returncode}): "
            f"{completed.stderr.strip() or completed.stdout.strip()}")
    if not (payload.get("bundle") or {}).get("present"):
        raise BridgeError(
            f"The engine bundle is missing or unreadable: {BUNDLE}. Rebuild the vendor with: node rebuild.mjs")
    playwright = payload.get("playwright") or {}
    if not playwright.get("available"):
        raise BridgeError(
            f"The Playwright Node module is unavailable or too old. {playwright.get('recovery', '')}".strip())
    browser = payload.get("browser") or {}
    if not browser.get("available"):
        raise BridgeError(browser.get("recovery") or "No usable Chromium-family browser was found.")
    return payload


def convert_html(runtime, html, output, evidence=None, assets_root=None, browser=None,
                 timeout_ms=None, headless=True, timeout=CONVERT_TIMEOUT_SECONDS):
    """Run one conversion and verify the saved package against the driver's own record."""
    source = Path(html).expanduser()
    if not source.is_file():
        raise BridgeError(f"The design HTML does not exist: {source}")
    if source.suffix.lower() not in {".html", ".htm"}:
        raise BridgeError(f"The design source must be an .html file: {source}")
    destination = Path(output).expanduser()
    if destination.suffix.lower() != ".pptx":
        raise BridgeError(f"The output must be a .pptx path: {destination}")
    if not destination.parent.is_dir():
        raise BridgeError(f"The output directory does not exist: {destination.parent}")
    record = Path(evidence).expanduser() if evidence else destination.with_name(destination.stem + ".conversion.json")
    if record.suffix.lower() != ".json":
        raise BridgeError(f"The evidence record must be a .json path: {record}")
    if not record.parent.is_dir():
        raise BridgeError(f"The evidence directory does not exist: {record.parent}")
    for existing in (destination, record):
        if existing.exists():
            raise BridgeError(
                f"Refusing to overwrite {existing}: earlier candidates and their evidence stay intact; "
                "choose a new candidate name.")
    job = {
        "html": str(source.resolve()),
        "output": str(destination.resolve()),
        "evidence": str(record.resolve()),
        "headless": bool(headless),
    }
    if assets_root is not None:
        root = Path(assets_root).expanduser()
        if not root.is_dir():
            raise BridgeError(f"The asset root does not exist: {root}")
        if not source.resolve().is_relative_to(root.resolve()):
            raise BridgeError(f"The design HTML must sit inside the asset root {root.resolve()}: {source}")
        job["assets_root"] = str(root.resolve())
    if browser is not None:
        job["browser_executable"] = str(Path(browser).expanduser())
    if timeout_ms is not None:
        if not isinstance(timeout_ms, int) or timeout_ms < 1000 or timeout_ms > 600000:
            raise BridgeError(f"timeout_ms must be an integer between 1000 and 600000: {timeout_ms}")
        job["timeout_ms"] = timeout_ms

    handle, job_path = tempfile.mkstemp(prefix="office-pptx-job-", suffix=".json")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(job, stream)
        try:
            completed = subprocess.run([runtime["node"], str(DRIVER), "--job", job_path],
                                       capture_output=True, text=True, encoding="utf-8",
                                       errors="replace", timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            raise BridgeError(f"The conversion did not finish within {timeout}s: {exc}") from exc
        except OSError as exc:
            raise BridgeError(f"Cannot run the conversion driver: {exc}") from exc
    finally:
        with contextlib.suppress(OSError):
            os.unlink(job_path)

    payload = last_json(completed.stdout)
    if payload is None:
        raise BridgeError(
            f"The conversion driver produced no record (exit {completed.returncode}): "
            f"{completed.stderr.strip() or completed.stdout.strip()}")
    if completed.returncode or payload.get("status") != "ok":
        detail = {key: payload.get(key) for key in ("page_errors", "console_warnings", "blocked_requests",
                                                   "missing_local_requests") if payload.get(key)}
        suffix = f" ({json.dumps(detail, sort_keys=True)})" if detail else ""
        code = payload.get("code") if payload.get("code") in (2, 3, 4) else 4
        raise BridgeError(
            f"Conversion failed (exit {completed.returncode}, code {payload.get('code')}): "
            f"{payload.get('message', 'no driver message')}{suffix}", code=code)
    if not destination.is_file():
        raise BridgeError(f"The driver reported success but wrote no package: {destination}")
    actual = sha256(destination)
    if actual != payload.get("output_sha256"):
        raise BridgeError(
            f"The saved package does not match the driver record: expected {payload.get('output_sha256')}, found {actual}")
    if not record.is_file():
        raise BridgeError(f"The driver reported success but wrote no evidence record: {record}")
    return {
        "output": str(destination.resolve()),
        "output_sha256": actual,
        "output_bytes": destination.stat().st_size,
        "evidence": str(record.resolve()),
        "panels": payload.get("panels"),
        "parts": payload.get("parts"),
        "conversion_ms": payload.get("conversion_ms"),
        "console_warnings": payload.get("console_warnings", []),
        "page_errors": payload.get("page_errors", []),
        "blocked_requests": payload.get("blocked_requests", []),
        "missing_local_requests": payload.get("missing_local_requests", []),
        "runtime": {"node": runtime["node_version"], "engine": runtime["engine"],
                    "bundle_sha256": runtime["bundle_sha256"]},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Office HTML to PPTX conversion bridge.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (("probe", "Report the conversion runtime."),
                            ("convert", "Convert one design HTML file into a native PPTX.")):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--node", help="Node executable; defaults to OFFICE_PPTX_NODE or PATH.")
        if name == "convert":
            command.add_argument("--html", required=True, help="Design HTML with data-office-slide panels.")
            command.add_argument("--output", required=True, help="Destination .pptx path.")
            command.add_argument("--evidence", help="Conversion evidence .json path.")
            command.add_argument("--assets-root",
                                 help="Directory served to the page; must contain the HTML. Relative URLs "
                                      "still resolve from the HTML's directory, /-rooted URLs from this root.")
            command.add_argument("--browser", help="Chrome, Edge or Chromium executable.")
            command.add_argument("--timeout-ms", type=int, help="Per-step browser timeout in milliseconds.")
            command.add_argument("--headed", action="store_true", help="Run with a visible browser window.")
    args = parser.parse_args(argv)
    try:
        runtime = discover(node=args.node)
        if args.command == "probe":
            result = {"runtime": runtime, "driver": probe(runtime)}
        else:
            result = convert_html(runtime, html=args.html, output=args.output, evidence=args.evidence,
                                  assets_root=args.assets_root, browser=args.browser,
                                  timeout_ms=args.timeout_ms, headless=not args.headed)
    except BridgeError as error:
        print(str(error), file=sys.stderr)
        return error.code
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
