"""rustup, read only: `rustup show` with RUSTUP_AUTO_INSTALL=0. It names the active toolchain and the file that
overrides the default (`rust-toolchain.toml`, or the legacy `rust-toolchain`, which wins when both exist);
`channel` comes back normalised (the host triple is dropped here). Nothing is installed. Standard library
only."""
from __future__ import annotations

import re
from pathlib import Path

from _versions import confine, rel, sh

VERSION = "1.29.3"
TRIPLE = re.compile(r"-(?:x86_64|aarch64|i686|armv7)-[a-z0-9_.-]+$")


def parse(text: str, fixture_dir) -> list[dict]:
    """The `active toolchain` block of `rustup show`: a `name:` line and an `active because:` line."""
    block = text.split("active toolchain", 1)[-1] if "active toolchain" in text else ""
    name = re.search(r"^name:\s*(\S+)", block, re.M)
    why = re.search(r"^active because:\s*overridden by '([^']+)'", block, re.M)
    if not name or not why:
        return []  # no active toolchain, or one that is the default and not the project's
    path = rel(why.group(1), fixture_dir)
    if path is None:
        return []
    return [{"tool": "rust", "version": TRIPLE.sub("", name.group(1)), "declared_in": path}]


def env_for(work_dir, auto: str) -> dict:
    env = {"RUSTUP_AUTO_INSTALL": auto, "NO_COLOR": "1"}
    if confine():
        base = Path(work_dir) / "cache" / "rust"
        env.update({"RUSTUP_HOME": str(base / "rustup"), "CARGO_HOME": str(base / "cargo"), "TMPDIR": str(base / "tmp")})
        (base / "tmp").mkdir(parents=True, exist_ok=True)
    return env


def run(fixture_dir, work_dir) -> dict:
    r = sh(["rustup", "show"], fixture_dir, env_for(work_dir, "0"), timeout=120)
    if "active toolchain" not in r["out"]:
        raise RuntimeError(f"rustup exit {r['rc']}: {(r['err'] or r['out']).strip()[-300:]}")
    return {"toolchains": parse(r["out"], fixture_dir)}
