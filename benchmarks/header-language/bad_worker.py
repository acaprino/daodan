"""One timed run of one target on one bad text, in a process of its own so a hard timeout can end it.

    python -I bad_worker.py CORE_DIR HL_DIR TARGET KIND SIZE [MODE]

TARGET: `r0` (today's detector), `r0fix`, `r0fixq` and `r0fixqc` (the candidates, `Probe.r0_variant`), `c`, `cpp`, `objc` (one grammar's parse and query), `scan` (the linear check of an
open comment), `product` (the product's own `detect_language` on a `.h`), `parse` (the adapter's parse of it, in the language found, which the
product does next). MODE: `bound:N` (`product` and `parse`: the product with `languages.detect.MAX_CHARS` set to N, 0 for none), `raw` (the text as it is), `cut:N` (cut at a line within N bytes), `safe:N` (the same, and cut
back before a `/*` left open). Prints one JSON line: the milliseconds of the target alone, the grammar and the
detector having been warmed on a small text first.
"""
import json
import sys
import time
from pathlib import Path

core, hl, target, kind, size = sys.argv[1:6]
mode = sys.argv[6] if len(sys.argv) > 6 else "raw"
sys.path.insert(0, hl)
import header_probe  # noqa: E402
import header_routes as routes  # noqa: E402

text = routes.bad_text(kind, int(size))
if mode.startswith("cut:"):
    cap = int(mode[4:])
    text = text[:text.rfind("\n", 0, cap) + 1] if len(text) > cap else text
elif mode.startswith("safe:"):
    text = routes.safe_prefix(text, int(mode[5:]))
probe = header_probe.Probe(core)
warm = "int a;\n"
if target == "r0":
    probe.r0(warm)
    ms = probe.r0(text)[1]
    extra = {}
elif target in ("r0fix", "r0fixq", "r0fixqc"):
    probe.r0_variant(warm, target[2:])
    ms = probe.r0_variant(text, target[2:])[1]
    extra = {}
elif target in ("product", "parse"):  # the product's detection, and the parse it does next with the adapter of the language found
    sys.path.insert(0, core)
    from languages import detect_language, get_adapter  # noqa: E402
    import languages.detect as detection  # noqa: E402
    if mode.startswith("bound:"):
        detection.MAX_CHARS = int(mode[6:]) or 1 << 40  # 0: no bound
    for language in ("c", "cpp"):
        get_adapter(language).parse(warm, "x.h")
    detect_language(Path("x.h"), warm)
    t0 = time.perf_counter_ns()
    found = detect_language(Path("x.h"), text)
    ms, extra = (time.perf_counter_ns() - t0) / 1e6, {"language": found}
    if target == "parse":
        t0 = time.perf_counter_ns()
        get_adapter(found or "c").parse(text, "x.h")
        ms = (time.perf_counter_ns() - t0) / 1e6
elif target == "scan":
    t0 = time.perf_counter_ns()
    found = routes.open_comment_start(text)
    ms, extra = (time.perf_counter_ns() - t0) / 1e6, {"open_at": found}
else:
    probe._part(target, warm.encode())
    part = probe._part(target, text.encode())
    ms, extra = part["ms"] + part["q_ms"], {"parse_ms": part["ms"], "err": part["err"], "missing": part["missing"]}
print(json.dumps({"target": target, "kind": kind, "size": int(size), "mode": mode, "used": len(text.encode()),
                  "ms": round(ms, 3), **extra}))
