"""Feature probe for LibCST: does its own grammar cover current Python syntax?

LibCST is the only other strict Python parser with its own grammar, i.e. one
whose accepted syntax does not depend on the interpreter running it. That is its
one possible advantage over the stdlib. This probe decides whether that advantage
is real by parsing the same feature corpus the main comparison uses.
"""
from __future__ import annotations

import sys
from pathlib import Path

import libcst

sys.path.insert(0, str(Path(__file__).resolve().parent))
from features import FEATURES  # noqa: E402


def main() -> int:
    print(f"libcst {getattr(libcst, '__version__', '?')} on CPython {sys.version.split()[0]}")
    accepted = rejected = 0
    for case in FEATURES:
        source = case["source"]
        valid = case.get("valid", True)
        try:
            libcst.parse_module(source)
            verdict = "accepts"
        except Exception as error:  # noqa: BLE001
            verdict = f"REJECTS ({type(error).__name__}: {str(error).splitlines()[0][:60]})"
        correct = (verdict == "accepts") == valid
        accepted += verdict == "accepts"
        rejected += verdict != "accepts"
        flag = "" if correct else "   <-- wrong"
        print(f"  {case['id']:36} min={str(case['min']):5} {verdict}{flag}")
    print(f"\n  accepted {accepted}, rejected {rejected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
