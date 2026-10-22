"""Syntax-feature corpus: one construct per case, with the definitions it must yield.

`min` is the first CPython version whose grammar accepts the case, or None when
no Python 3 grammar does (`valid: False`). For a valid case the reference parser
must accept it on every interpreter at or above `min` and reject it below. For an
invalid case the reference parser must reject it everywhere; `expect` then names
what a recovering parser would have to emit to be useful, and the question is
whether what it emits is right.

`expect` is a multiset of qualified names, outermost first, joined by ".", in
source order. Conditional definitions appear once per definition.

This file is imported by workers running under CPython 3.11, so it must not use
syntax newer than 3.11 itself; the constructs under test live only inside
strings.
"""

FEATURES = [
    # ------------------------------------------------------------- 3.8 to 3.11
    {"id": "py38-walrus", "min": "3.8",
     "source": "if (n := len([1])) > 0:\n    def inside(): pass\n",
     "expect": ["inside"]},
    {"id": "py38-positional-only", "min": "3.8",
     "source": "def f(a, b, /, c, *, d): pass\n",
     "expect": ["f"]},
    {"id": "py38-fstring-self-documenting", "min": "3.8",
     "source": "x = 1\nprint(f\"{x=}\")\ndef g(): pass\n",
     "expect": ["g"]},
    {"id": "py39-relaxed-decorator", "min": "3.9",
     "source": "buttons = [object()]\n@buttons[0].clicked.connect\ndef handler(): pass\n",
     "expect": ["handler"]},
    {"id": "py310-match", "min": "3.10",
     "source": ("def route(cmd):\n    match cmd:\n        case {'action': 'go', **rest}:\n"
                "            def go(): pass\n        case Point(x=0, y=0) | [_, *_]:\n"
                "            pass\n        case _:\n            pass\n"),
     "expect": ["route", "route.go"]},
    {"id": "py310-parenthesized-with", "min": "3.10",
     "source": "def f():\n    with (open('a') as x,\n          open('b') as y):\n        pass\n",
     "expect": ["f"]},
    {"id": "py311-except-star", "min": "3.11",
     "source": "def f():\n    try:\n        pass\n    except* ValueError:\n        def handler(): pass\n",
     "expect": ["f", "f.handler"]},
    {"id": "py311-starred-annotation", "min": "3.11",
     "source": "def f(*args: *Ts): pass\n",
     "expect": ["f"]},

    # --------------------------------------------------------------------- 3.12
    {"id": "py312-generic-function", "min": "3.12",
     "source": "def first[T](xs: list[T]) -> T:\n    return xs[0]\n",
     "expect": ["first"]},
    {"id": "py312-generic-class", "min": "3.12",
     "source": "class Box[T: (int, str), *Ts, **P]:\n    def get(self) -> T: ...\n",
     "expect": ["Box", "Box.get"]},
    {"id": "py312-type-alias", "min": "3.12",
     "source": "type Pair[T] = tuple[T, T]\ndef after(): pass\n",
     "expect": ["Pair", "after"]},
    {"id": "py312-fstring-nested-quotes", "min": "3.12",
     "source": ("items = {'k': 1}\nmsg = f\"{items[\"k\"]} and {'\\n'.join(['a'])}\"\n"
                "def after(): pass\n"),
     "expect": ["after"]},
    {"id": "py312-fstring-multiline-comment", "min": "3.12",
     "source": "x = 1\nmsg = f\"{\n    x  # a comment inside the replacement field\n}\"\ndef after(): pass\n",
     "expect": ["after"]},

    # --------------------------------------------------------------- 3.13, 3.14
    {"id": "py313-type-parameter-default", "min": "3.13",
     "source": "def f[T = int](x: T) -> T: return x\nclass C[T = str]: pass\n",
     "expect": ["f", "C"]},
    {"id": "py314-except-without-parentheses", "min": "3.14",
     "source": ("def f():\n    try:\n        pass\n    except ValueError, TypeError:\n"
                "        pass\ndef after(): pass\n"),
     "expect": ["f", "after"]},
    {"id": "py314-template-string", "min": "3.14",
     "source": "name = 'x'\ntemplate = t\"hello {name}\"\ndef after(): pass\n",
     "expect": ["after"]},

    # ------------------------------------------- version-independent structure
    {"id": "soft-keywords-as-names", "min": "3.10",
     "source": ("match = 1\ncase = 2\ntype = 3\ndef type_(): pass\nclass match_: pass\n"
                "print(match, case, type)\n"),
     "expect": ["type_", "match_"]},
    {"id": "function-named-type", "min": "3.8",
     "source": "def type(x): return x\ntype(1)\n",
     "expect": ["type"]},
    {"id": "async-constructs", "min": "3.8",
     "source": ("class S:\n    async def run(self):\n        async with self.lock:\n"
                "            async for x in self.items():\n                await x\n"
                "        return [y async for y in self.items()]\n"),
     "expect": ["S", "S.run"]},
    {"id": "decorated-and-nested", "min": "3.8",
     "source": ("import functools\n@functools.lru_cache(maxsize=None)\ndef outer():\n"
                "    @staticmethod\n    def inner(): pass\n    class Local:\n"
                "        @property\n        def p(self): return 1\n    return inner, Local\n"),
     "expect": ["outer", "outer.inner", "outer.Local", "outer.Local.p"]},
    {"id": "conditional-definitions", "min": "3.8",
     "source": ("import sys\nif sys.platform == 'win32':\n    def path(): return 'w'\nelse:\n"
                "    def path(): return 'p'\ntry:\n    import ujson as json\nexcept ImportError:\n"
                "    import json\n    def dumps(o): return json.dumps(o)\n"),
     "expect": ["path", "path", "dumps"]},
    {"id": "class-keywords", "min": "3.8",
     "source": ("class Meta(type): pass\nclass A(object, metaclass=Meta, flag=True):\n"
                "    x: int = 0\n    def m(self): pass\n"),
     "expect": ["Meta", "A", "A.m"]},
    {"id": "unicode-identifiers", "min": "3.8",
     "source": "def caf\u00e9(): pass\nclass Gr\u00f6\u00dfe: pass\n",
     "expect": ["caf\u00e9", "Gr\u00f6\u00dfe"]},
    {"id": "nfkc-normalised-identifier", "min": "3.8",
     "source": "def \ufb01le(): pass\n",
     "expect": ["file"]},
    {"id": "backslash-continuation", "min": "3.8",
     "source": "def f(a, \\\n      b): pass\n",
     "expect": ["f"]},
    {"id": "form-feed", "min": "3.8",
     "source": "def f(): pass\n\x0c\ndef g(): pass\n",
     "expect": ["f", "g"]},
    {"id": "byte-order-mark", "min": "3.8",
     "source": "\ufeffdef f(): pass\n",
     "expect": ["f"]},
    {"id": "latin1-encoding-cookie", "min": "3.8", "enc": "latin-1",
     "source": "# -*- coding: latin-1 -*-\ns = 'caf\u00e9'\ndef f(): pass\n",
     "expect": ["f"]},

    # ------------------------- invalid in every Python 3: must be rejected
    {"id": "python2-print-statement", "min": None, "valid": False,
     "source": "print 'hello'\ndef f(): pass\n",
     "expect": ["f"]},
    {"id": "inconsistent-tabs-and-spaces", "min": None, "valid": False,
     "source": "def f():\n\tif True:\n        return 1\n\treturn 2\ndef g(): pass\n",
     "expect": ["f", "g"]},
    {"id": "null-byte", "min": None, "valid": False,
     "source": "def f(): pass\n\x00\ndef g(): pass\n",
     "expect": ["f", "g"]},
]
