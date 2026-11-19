"""
Shared dataclasses and the LanguageAdapter protocol.

The dataclasses are the stable contract returned by every language adapter,
so analyze_file.py and downstream consumers do not branch on language. Some
fields are language-specific (decorators apply to Python/JS/TS, annotations
to Python/Java/TS); they remain optional strings so the shape stays uniform.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Literal, Protocol, runtime_checkable

__all__ = [
    "ParameterInfo",
    "FunctionInfo",
    "ClassInfo",
    "ImportInfo",
    "ExternalCallInfo",
    "NestedDefinition",
    "ParseResult",
    "LanguageAdapter",
    "CallType",
    "Visibility",
    "Kind",
    "SIGNATURE_FIELDS",
]


# Categories of external system calls. The "other" entry is a future-proofing
# fallback; no adapter currently emits it.
CallType = Literal["database", "network", "filesystem", "messaging", "ipc", "other"]

# Function/class visibility modifiers across the supported languages, plus the
# SQL/PL-SQL marker that distinguishes a stored procedure from a function.
Visibility = Literal["public", "private", "protected", "procedure"]

# All ClassInfo.kind values emitted across the supported languages. Includes
# OO kinds (class/interface/enum/record/annotation), TS-only "type-alias",
# SQL DDL kinds (table/view/index/sequence/type/schema/trigger), and PL/SQL
# container kinds (package/package-body/type-body).
Kind = Literal[
    "class",
    "interface",
    "enum",
    "record",
    "annotation",
    "type-alias",
    "namespace",
    "table",
    "view",
    "index",
    "sequence",
    "type",
    "schema",
    "trigger",
    "package",
    "package-body",
    "type-body",
    # Rust-specific kinds:
    "struct",
    "trait",
    "impl",
    "mod",
    "union",
    # Stylesheet kinds:
    "rule",
    "at-rule",
    "variable",
]

# The signature fields an adapter can declare as extracted exhaustively, in
# `FunctionInfo.signature_fields` and `ClassInfo.signature_fields`. A declared
# field that is empty is empty in the source; an undeclared one may only be
# missing from the extraction.
SIGNATURE_FIELDS = frozenset({
    "parameters",       # every parameter, in order
    "parameter_kinds",  # ParameterInfo.kind of every parameter
    "annotations",      # ParameterInfo.annotation of every parameter
    "defaults",         # ParameterInfo.default of every parameter
    "returns",          # FunctionInfo.return_annotation
    "async",            # FunctionInfo.is_async
    "generator",        # FunctionInfo.is_generator
    "decorators",       # decorators of a function or class
    "bases",            # ClassInfo.bases
    "attributes",       # ClassInfo.attributes
})


@dataclass
class ParameterInfo:
    name: str
    annotation: str | None = None
    default: str | None = None
    # How a caller passes an argument that is not an ordinary positional-or-
    # keyword one: positional_only, var_positional, keyword_only or var_keyword
    # (Python, Java varargs), or optional (TypeScript `x?`). None for an
    # ordinary parameter where the adapter declares "parameter_kinds", and
    # unknown otherwise.
    kind: str | None = None


@dataclass
class FunctionInfo:
    name: str
    parameters: list[ParameterInfo] = field(default_factory=list)
    return_annotation: str | None = None
    is_async: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False
    is_property: bool = False
    # Visibility hint, populated by adapters that know (Java public/private,
    # JS/TS export, SQL CREATE vs CREATE OR REPLACE). "procedure" is the
    # SQL/PL-SQL marker for a stored procedure (vs a function).
    visibility: Visibility | None = None
    docstring: str | None = None
    line_number: int = 0
    # Last line of the symbol body, when the adapter knows it exactly: Python
    # from the stdlib AST, Java, JavaScript, TypeScript and Rust from their
    # Tree-sitter node, stylesheets from their own parser. None from a regex
    # parser: snapshot.py then infers the span from the next symbol's start.
    end_line: int | None = None
    # Outgoing function/method call names inside the callable's body, in source
    # order without duplicates.
    calls_made: list[str] = field(default_factory=list)
    # Decorator expressions in source order, where the adapter extracts them.
    decorators: list[str] = field(default_factory=list)
    is_generator: bool = False
    # Members of SIGNATURE_FIELDS this adapter extracts exhaustively.
    signature_fields: tuple[str, ...] = ()


@dataclass
class ClassInfo:
    name: str
    bases: list[str] = field(default_factory=list)
    methods: list[FunctionInfo] = field(default_factory=list)
    class_variables: list[str] = field(default_factory=list)
    # Distinguish class / interface / enum / record / type-alias / DDL kinds.
    # See `Kind` for the full enumeration.
    kind: Kind = "class"
    visibility: Visibility | None = None
    docstring: str | None = None
    line_number: int = 0
    # Last line of the symbol body, when the adapter knows it exactly: Python
    # from the stdlib AST, Java, JavaScript, TypeScript and Rust from their
    # Tree-sitter node, stylesheets from their own parser. None from a regex
    # parser: snapshot.py then infers the span from the next symbol's start.
    end_line: int | None = None
    decorators: list[str] = field(default_factory=list)
    # Class-level attributes with their annotation and value, where the adapter
    # extracts them; class_variables keeps only the names.
    attributes: list[ParameterInfo] = field(default_factory=list)
    # Members of SIGNATURE_FIELDS this adapter extracts exhaustively.
    signature_fields: tuple[str, ...] = ()


@dataclass
class ImportInfo:
    module: str
    names: list[str] = field(default_factory=list)
    is_from_import: bool = False
    is_internal: bool = False
    # Local alias from a direct ES default clause (`import Alias from ...`).
    # Named default specifiers retain source name `default` in names instead.
    default_import: str | None = None


@dataclass
class ExternalCallInfo:
    call_type: CallType
    pattern: str
    line_number: int
    context: str


@dataclass
class NestedDefinition:
    """
    A definition the two top-level lists omit, qualified by its enclosing chain.

    `qualified_name` joins the enclosing class/def names with ".", the identity
    the snapshot records as the symbol name: `inner` inside `Outer` is
    `Outer.inner`, and a method of a nested class is `Outer.Inner.method`.
    `kind` is "method" when the nearest enclosing definition is a class,
    "function" when it is not, the `ClassInfo.kind` for a class, and
    "type-alias" for a PEP 695 alias.

    These exist so a call into one has an arrival node in the graph. They are
    not part of the file outline: `functions` and `classes` keep their documented
    meaning, and only the graph consumers read this list.
    """

    qualified_name: str
    kind: str
    info: "FunctionInfo | ClassInfo"


@dataclass
class ParseResult:
    """
    Convention for `functions` vs `classes[*].methods`:

    - `functions` contains TOP-LEVEL callables (Python top-level def, JS top-level
      function/arrow declarations, SQL CREATE FUNCTION/PROCEDURE, PL/SQL inner
      PROCEDURE/FUNCTION declarations).
    - Methods of a class/interface/etc. live inside `classes[*].methods` and
      are NOT duplicated into `functions`.
    - Java has no top-level functions, so `functions` is always empty for
      Java files; all callables are class methods.

    Consumers enumerating "every callable in the file" must visit both lists:
    `functions + [m for c in classes for m in c.methods]`. Add `nested` when the
    subject is the graph rather than the file outline: it holds the definitions
    those two lists deliberately omit, already qualified by their enclosing chain.

    Convention for `notes`:

    - `notes[0]` starts with `parser=<source>` where source is one of:
      `stdlib-ast` (Python), `tree-sitter` (Java/JS), `tree-sitter (ts)` (TS),
      `regex-fallback` (Java/JS), `regex-fallback (ts)` (TS),
      `regex (sql)` (SQL), `regex (plsql)` (PL/SQL),
      `stylesheet (css)`, `stylesheet (scss)`, `stylesheet (less)` (CSS, SCSS, LESS).
    - Additional notes may be appended for syntax errors, tree-sitter
      exceptions, lossy encoding, etc.
    - A `recovered prefix: line <N>, <M> closed definitions` note means the file
      was rejected and the symbols present come from the longest prefix that
      parses, keeping only the definitions that prefix closes. The
      `syntax error:` note stays, so the file is still reported as a parse error:
      recovery widens what a broken file yields, it never claims it parses.
    """

    file_path: str
    language: str = "unknown"
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    # Definitions neither list holds: a nested function or class, a definition
    # inside a compound statement (if/try/with/for/while/match) at module or class
    # level, and a PEP 695 `type` alias. They carry the qualified name the
    # snapshot records, so a call into one has an arrival node. Adapters that do
    # not extract them leave the list empty, which is a convention, not an
    # absence of nesting in the source.
    nested: list[NestedDefinition] = field(default_factory=list)
    imports: list[ImportInfo] = field(default_factory=list)
    constants: list[str] = field(default_factory=list)
    external_calls: list[ExternalCallInfo] = field(default_factory=list)
    exported_symbols: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    # Named declaration or local identifier exported as default. Anonymous
    # expressions and unresolved re-exports retain None.
    default_export: str | None = None
    # Additive syntax evidence from the existing native tree. Regex or invalid
    # syntax cannot supply authoritative lexical bindings or reference spans.
    semantic: dict | None = None


@runtime_checkable
class LanguageAdapter(Protocol):
    """
    Each language module exposes a module-level `adapter` matching this.

    `language` is a class-level constant (each adapter sets it on the class,
    not the instance) and must equal one of the canonical identifiers in
    `languages.Language`.
    """

    language: ClassVar[str]

    def parse(self, content: str, file_path: str) -> ParseResult:
        ...

    def count_imports(self, content: str) -> int:
        ...

    def strip_comments_and_blanks(self, content: str) -> int:
        """Return number of non-empty, non-comment lines."""
        ...

    def extract_comments(
        self, content: str
    ) -> list["CommentToken"]:
        """
        Return all comments in the file with their token info.

        See comments.CommentToken for the shape.
        """
        ...


# Forward import declared here so adapters can import the type from base.
from .comments import CommentToken  # noqa: E402  (placed after Protocol on purpose)

__all__.append("CommentToken")
