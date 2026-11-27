"""The patterns of the `.h` rule as it was before 25 November 2026 (commit 3960973d8 of `daodan/core/languages/__init__.py`),
frozen here, and the candidates that were measured against it, each written in full. `fixqc` was the product's rule from
25 November (commit cd19c05e8) until route R3dx took its place (`daodan/core/languages/detect/rules/header.py`): `CPP_FIXQC` is frozen at
that commit, `NOISE_FIXQ` is still the product's noise pattern, and the tests compare both. The results recorded in
`results/` are of the rule before, which is what R0 means in them. A candidate is never made from another pattern by a replace: a replace that finds nothing changes
nothing and says nothing. `test_header_patterns.py` checks that the frozen patterns are those of that commit (`git show`),
and that each candidate differs from them in the one edit it names. Standard library only (Python 3.11+: the possessive
quantifiers).

    fix    the comment pattern ends at `*/` or at the end of the text: a `/*` never closed is one match to the end,
           not one match for each `/*` (the quadratic cost of `/*` over and over)
    fixq   fix, and a string or character literal opens only at a quote no backslash precedes, and has no way back:
           `"\\"\\"\\"...` is not a string that opens at every quote (the quadratic cost of an escaped quote over and over)
    fixqc  fixq, and in the C++ pattern `class NAME ... {` stops at the next `class NAME`: the match from that one is
           there whenever the match from this one is, so the answer is the same, and the cost is linear
"""
from __future__ import annotations

import re

BEFORE_NOISE = r"""//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'"""
BEFORE_CPP = (r"\bnamespace\s+\w+(?:\s*::\s*(?:inline\s+)?\w+)*\s*\{|^[ \t]*namespace\s*\{|^[ \t]*namespace\s+\w+\s*=(?!=)"
             r"|\bclass\s+\w+[^;(){}]*\{|\btemplate\s*<|^[ \t]*(?:public|private|protected)\s*:|\busing\s+namespace\b|\bstd::\w"
             r"|^[ \t]*#\s*include\s*<(?:cstdint|string|vector|map|list|array|bitset|queue|stack|forward_list|unordered_map"
             r"|unordered_set|(?:i|o|io)stream)>")
BEFORE_OBJC = r"^[ \t]*@(?:interface|implementation|protocol|class|property|end)\b"

NOISE_FIX = r"""//[^\n]*|/\*.*?(?:\*/|\Z)|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'"""
NOISE_FIXQ = r"""//[^\n]*|/\*.*?(?:\*/|\Z)|(?<!\\)"(?:\\.|[^"\\\n])*+"|(?<!\\)\'(?:\\.|[^\'\\\n])*+\'"""
CPP_FIXQC = (r"\bnamespace\s+\w+(?:\s*::\s*(?:inline\s+)?\w+)*\s*\{|^[ \t]*namespace\s*\{|^[ \t]*namespace\s+\w+\s*=(?!=)"
             r"|\bclass\s+\w++(?:(?!\bclass\s+\w)[^;(){}])*+\{|\btemplate\s*<|^[ \t]*(?:public|private|protected)\s*:|\busing\s+namespace\b|\bstd::\w"
             r"|^[ \t]*#\s*include\s*<(?:cstdint|string|vector|map|list|array|bitset|queue|stack|forward_list|unordered_map"
             r"|unordered_set|(?:i|o|io)stream)>")

_FLAGS = {"noise": re.DOTALL, "cpp": re.MULTILINE, "objc": re.MULTILINE}
OBJC = re.compile(BEFORE_OBJC, _FLAGS["objc"])
VARIANTS = {  # name -> (the comment and string pattern, the C++ pattern)
    "fix": (re.compile(NOISE_FIX, _FLAGS["noise"]), re.compile(BEFORE_CPP, _FLAGS["cpp"])),
    "fixq": (re.compile(NOISE_FIXQ, _FLAGS["noise"]), re.compile(BEFORE_CPP, _FLAGS["cpp"])),
    "fixqc": (re.compile(NOISE_FIXQ, _FLAGS["noise"]), re.compile(CPP_FIXQC, _FLAGS["cpp"])),
}
BEFORE = (re.compile(BEFORE_NOISE, _FLAGS["noise"]), re.compile(BEFORE_CPP, _FLAGS["cpp"]))


def answer(content: str, variant: str | None = None) -> str:
    """The rule before (`variant` None) or a candidate (`fixqc` is the product's now) for a `.h` file: "objc", "cpp" or "c"."""
    noise, cpp = BEFORE if variant is None else VARIANTS[variant]
    code = noise.sub(" ", content)
    return "objc" if OBJC.search(code) else "cpp" if cpp.search(code) else "c"
