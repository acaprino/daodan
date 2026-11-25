"""Registry host mentions from absolute HTTP(S) URLs in configuration values and source literals."""
from pathlib import PurePosixPath
from urllib.parse import urlsplit

from languages import _treesitter as ts
from source_files import MAX_PARSE_BYTES


GRAMMARS = {".py": "python", ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
            ".ts": "typescript", ".tsx": "tsx", ".mts": "typescript", ".cts": "typescript", ".cs": "csharp",
            ".ex": "elixir", ".exs": "elixir", ".go": "go", ".java": "java", ".kt": "kotlin", ".kts": "kotlin",
            ".php": "php", ".rs": "rust"}
STRING_NODES = {"python": ("string",), "javascript": ("string", "template_string"),
                "typescript": ("string", "template_string"), "tsx": ("string", "template_string"),
                "csharp": ("string_literal", "interpolated_string_expression"), "elixir": ("string",),
                "go": ("interpreted_string_literal", "raw_string_literal"), "java": ("string_literal",),
                "kotlin": ("string_literal",), "php": ("string", "encapsed_string"),
                "rust": ("string_literal", "raw_string_literal")}
CONTENT = {"quoted_content", "string_content", "string_fragment", "string_literal_content",
           "interpreted_string_literal_content", "raw_string_literal_content"}
CONFIG = {".json", ".yml", ".yaml"}
LOCKFILES = {"package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "composer.lock"}


def _yaml_values(text, yaml):
    # JSON is a YAML subset. Composition gives source marks and never constructs objects.
    for root in yaml.compose_all(text, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader)):
        pending, seen = [root], set()
        while pending:
            node = pending.pop()
            if node is None or id(node) in seen:
                continue
            seen.add(id(node))
            if isinstance(node, yaml.MappingNode):
                pending.extend(value for _, value in node.value)
            elif isinstance(node, yaml.SequenceNode):
                pending.extend(node.value)
            elif node.tag == "tag:yaml.org,2002:str":
                yield node.value, node.start_mark.line + 1


def _source_values(grammar, text):
    query = "[" + " ".join(f"({kind})" for kind in STRING_NODES[grammar]) + "] @literal"
    pair = ts.get_parser(grammar)
    if pair is None:
        raise LookupError(ts.load_failure(grammar) or f"{grammar} grammar unavailable")
    if ts.get_query(grammar, query) is None:
        raise ValueError(f"{grammar} grammar rejected string-literal query")
    root = pair[0].parse(text.encode("utf-8")).root_node
    for node in ts.query_captures(grammar, query, root).get("literal", []):
        children = [c for c in node.named_children if c.type not in {"string_start", "string_end", "interpolation_start"}]
        if not children or children[0].type not in CONTENT:
            continue
        value = children[0].text.decode("utf-8")
        # A following interpolation or escape can change the authority until its first /, ? or #.
        if len(children) > 1 and not any(c in value.partition("://")[2] for c in "/?#"):
            continue
        yield value, children[0].start_point[0] + 1


def _host(value):
    if not value.lower().startswith(("http://", "https://")) or any(ord(c) < 32 for c in value):
        return None
    try:
        url = urlsplit(value)
        if "\\" in url.netloc or any(c.isspace() for c in url.netloc):
            return None
        # Accessing port also validates a malformed or out-of-range port.
        _ = url.port
        return (url.hostname or "").removesuffix(".")
    except ValueError:
        return None


def check_hosts(entries, project):
    owners = {}
    for entry in entries:
        for host in entry.get("hosts", ()):
            owners.setdefault(host.lower(), []).append(entry["id"])
    found, gaps = set(), []
    if not owners:
        return {"signs": [], "gaps": []}
    for rel in project.files:
        path = PurePosixPath(rel)
        suffix = path.suffix.lower()
        if suffix not in CONFIG and suffix not in GRAMMARS:
            continue
        if path.name in LOCKFILES:
            continue
        lines = project.lines(rel)
        if not any("://" in line for line in lines):
            continue
        if any('"daodan/service-registry/' in line or '"daodan/registry-additions/' in line for line in lines[:3]):
            continue
        text = "\n".join(lines)
        lowered = text.lower()
        if not any(host in lowered for host in owners):
            continue
        if len(text.encode("utf-8")) > MAX_PARSE_BYTES:
            gaps.append({"kind": "host_values_unreadable", "path": rel, "detail": "file exceeds parse size limit"})
            continue
        try:
            if suffix in CONFIG:
                import yaml
                try:
                    values = list(_yaml_values(text, yaml))
                except yaml.YAMLError as err:
                    # YAML diagnostics quote source lines, which can contain credentials.
                    raise ValueError("invalid configuration") from err
            else:
                values = _source_values(GRAMMARS[suffix], text)
            for value, line in values:
                host = _host(value)
                found.update((ident, host, rel, line) for ident in owners.get(host, ()))
        except LookupError as err:
            gaps.append({"kind": "source_grammar_unavailable", "language": GRAMMARS[suffix], "path": rel, "detail": str(err)})
        except (ImportError, ValueError, RecursionError) as err:
            gaps.append({"kind": "host_values_unreadable", "path": rel, "detail": str(err)})
    return {"signs": sorted(found), "gaps": gaps}
