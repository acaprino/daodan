"""Corepack reading `packageManager`. Corepack has no read command: it names the declared manager and the file
when asked for another one (`This project is configured to use X because <file> has a "packageManager" field`),
so the adapter asks for yarn and then pnpm with the network off, and only then asks for the declared manager's
version, which makes Corepack download it (hash-checked when the field carries `+sha512.`) into COREPACK_HOME.
Without a download the version is not known and is left out. Standard library only."""
from __future__ import annotations

import re
from pathlib import Path

from _versions import confine, rel, sh

VERSION = "0.36.0"
MISMATCH = re.compile(r'configured to use (\S+) because (\S+) has a "packageManager" field')


def run(fixture_dir, work_dir) -> dict:
    env = {"COREPACK_ENABLE_AUTO_PIN": "0", "COREPACK_ENABLE_DOWNLOAD_PROMPT": "0", "NO_COLOR": "1"}
    if confine():
        base = Path(work_dir) / "cache" / "corepack"
        (base / "tmp").mkdir(parents=True, exist_ok=True)
        env["COREPACK_HOME"] = str(base)
        env["TMPDIR"] = str(base / "tmp")  # Node writes its compile cache under the temp dir
    offline = dict(env, COREPACK_ENABLE_NETWORK="0")
    name = path = None
    for ask in ("yarn", "pnpm"):
        r = sh(["corepack", ask, "--version"], fixture_dir, offline, timeout=120)
        m = MISMATCH.search(r["out"] + r["err"])
        if m:
            name, path = m.group(1), rel(m.group(2), fixture_dir)
            break
        if r["rc"] == 0:
            name, path = None, None
            continue
        if "Network access disabled" in r["err"]:
            continue  # yarn or nobody declared; the next ask tells
    if name is None:
        # yarn answered offline from the cache, or both were refused for the network: yarn is declared only
        # when pnpm was refused by name, which the loop already caught. Nothing declared.
        return {"toolchains": []}
    item = {"tool": name, "declared_in": path}
    r = sh(["corepack", name, "--version"], fixture_dir, env, timeout=600)
    if r["rc"] == 0 and r["out"].strip():
        item["version"] = r["out"].strip().splitlines()[-1]
    return {"toolchains": [item]}
