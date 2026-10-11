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
