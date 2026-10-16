"""Strict oracle for the one generated execution binding in host Markdown."""
from pathlib import Path

from scripts.daodan.adapter import load_adapter
from scripts.daodan.render import _operational_binding

ADAPTERS = Path(__file__).resolve().parents[1] / "adapters"


def without_host_binding(case, text, host):
    """Remove only this host's exact generated block; reject absent/changed/duplicate blocks."""
    expected = _operational_binding(load_adapter(ADAPTERS, host), ADAPTERS).rstrip() + "\n\n"
    case.assertEqual(text.count("<daodan_host_binding"), 1, "Exactly one generated binding must exist")
    case.assertEqual(text.count(f'<daodan_host_binding host="{host}">'), 1,
                     "The binding must name the actual export host")
    case.assertEqual(text.count("</daodan_host_binding>"), 1, "Exactly one binding must close")
    case.assertEqual(text.count(expected), 1, "The binding must equal the current generated contract")
    return text.replace(expected, "", 1)


def canonical_markdown(text):
    """Source parity permits LF line endings and one terminal newline only."""
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"


def shared_instruction_resource(path):
    """Resolve only the explicit local shared-entry/role reference in a wrapper."""
    import re
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if "<!-- Codebase Map shared instruction wrapper. -->" not in text:
        return None
    match = re.search(r"references/((?:entry|role)-[a-z0-9-]+\.md)", text)
    if match is None:
        return None
    for ancestor in path.parents:
        if ancestor.name == "codebase-map":
            owner = ancestor
            resource = owner / "skills/map-method/references" / match.group(1)
            if not resource.is_file():
                raise FileNotFoundError(resource)
            return resource
    raise ValueError(f"Shared instruction has no owning plugin: {path}")


def source_instruction_text(path):
    """Read the behavior's canonical source, rather than a registered wrapper."""
    resource = shared_instruction_resource(path)
    return (resource or Path(path)).read_text(encoding="utf-8")


def loaded_instruction_text(case, path, host):
    """Keep the real harness and validate its separately loaded host resource."""
    text = Path(path).read_text(encoding="utf-8")
    resource = shared_instruction_resource(path)
    if resource is not None:
        shared = resource.read_text(encoding="utf-8")
        text += "\n\n" + without_host_binding(case, shared, host)
    return text
