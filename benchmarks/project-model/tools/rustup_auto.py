"""rustup installing the toolchain the project asks for: `rustup show active-toolchain` with
RUSTUP_AUTO_INSTALL=1 (the default since 1.28.1) downloads the channel's components through static.rust-lang.org,
checked against the channel manifest's sha256, into RUSTUP_HOME. Same answer as `rustup`, after the install.
Standard library only."""
from __future__ import annotations

import re

from _versions import rel, sh
from rustup import TRIPLE, env_for

VERSION = "1.29.3"


def run(fixture_dir, work_dir) -> dict:
    probe = sh(["rustup", "show"], fixture_dir, env_for(work_dir, "0"), timeout=120)
    if "overridden by" not in probe["out"]:
        return {"toolchains": []}  # nothing in the project selects a toolchain: no install
    r = sh(["rustup", "show", "active-toolchain"], fixture_dir, env_for(work_dir, "1"), timeout=1800)
    m = re.search(r"^(\S+)\s+\(overridden by '([^']+)'\)", r["out"], re.M)
    if r["rc"] != 0 or not m or rel(m.group(2), fixture_dir) is None:
        raise RuntimeError(f"rustup exit {r['rc']}: {(r['err'] or r['out']).strip()[-400:]}")
    return {"toolchains": [{"tool": "rust", "version": TRIPLE.sub("", m.group(1)),
                            "declared_in": rel(m.group(2), fixture_dir)}]}
