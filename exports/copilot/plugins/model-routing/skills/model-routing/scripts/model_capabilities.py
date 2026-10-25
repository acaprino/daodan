"""One capability vocabulary for the catalog and both routers, read from every host shape.

The vocabulary is the model schema that OpenCode and models.dev share: six features and
five modalities on each side. OpenCode's ``ConfigProviderV1.Model`` declares
``attachment``, ``reasoning``, ``temperature``, ``tool_call`` and ``interleaved`` as
top-level fields and ``modalities`` as two lists over text, audio, image, video and pdf;
models.dev adds ``structured_output``. Pi's ``models.json`` declares ``reasoning`` and an
``input`` list. Every reader of a model entry goes through ``normalize``, so the catalog,
the per-request router and the tier screening expose the same capabilities under the same
names, and a capability one of them learns to read reaches all three.

Every value is True, False or None. None means the source never reported it: a gap in the
harvest, never evidence of absence, because treating it as False would let an unharvested
capability silently delete every candidate. A source that declares a feature as false is
read as false: ``temperature: false`` is how models.dev marks a model that refuses the
parameter, and reading presence instead of value turned it into true.

Standard library only.
"""

from __future__ import annotations

FEATURES = ("tool_call", "reasoning", "attachment", "structured_output", "temperature",
            "interleaved")
MODALITIES = ("text", "audio", "image", "video", "pdf")
# A spelling a host uses for a modality of the vocabulary.
MODALITY_ALIASES = {"file": "pdf"}
VOCABULARY = (FEATURES
              + tuple(f"input.{m}" for m in MODALITIES)
              + tuple(f"output.{m}" for m in MODALITIES)
              + ("output.non_text",))


def _flag(value):
    return None if value is None else bool(value)


def _interleaved(value):
    """OpenCode accepts a boolean, a field name or ``{field}``; the feature is whether any is set."""
    if value is None:
        return None, None
    if isinstance(value, dict):
        field = value.get("field")
        return bool(field), field if isinstance(field, str) else None
    if isinstance(value, str):
        return bool(value), value or None
    return bool(value), None


def _modalities(values):
    """The declared list, lowercased and de-aliased; None when nothing was declared."""
    if not isinstance(values, list) or not values:
        return None
    out = []
    for value in values:
        name = str(value).lower()
        name = MODALITY_ALIASES.get(name, name)
        if name not in out:
            out.append(name)
    return out


def normalize(entry):
    """The capabilities one model entry declares: ``{input, output, features, interleaved_field}``.

    Reads a models.dev or OpenCode config entry (top-level flags and ``modalities``), a Pi
    entry (an ``input`` list), and a view already in this shape, which is what the catalog
    stores under ``capabilities``.
    """
    entry = entry if isinstance(entry, dict) else {}
    if isinstance(entry.get("features"), dict):
        flags, inputs, outputs = entry["features"], entry.get("input"), entry.get("output")
        interleaved, field = _interleaved(flags.get("interleaved"))
        field = entry.get("interleaved_field") or field
    else:
        flags = entry
        mods = entry.get("modalities") if isinstance(entry.get("modalities"), dict) else {}
        inputs = mods.get("input")
        if inputs is None:
            inputs = entry.get("input")
        outputs = mods.get("output")
        interleaved, field = _interleaved(entry.get("interleaved"))
    features = {name: _flag(flags.get(name)) for name in FEATURES if name != "interleaved"}
    features["interleaved"] = interleaved
    return {"input": _modalities(inputs), "output": _modalities(outputs),
            "features": {name: features[name] for name in FEATURES},
            "interleaved_field": field}


def has(view, requirement):
    """True, False, or None when the source never reported the capability."""
    if requirement in FEATURES:
        return view["features"].get(requirement)
    side, _, modality = requirement.partition(".")
    declared = view.get(side)
    if not declared:
        return None
    if modality == "non_text":
        return bool(set(declared) - {"text"})
    return modality in declared


def unknown_requirements(requirements):
    """The requirements the vocabulary does not name, so a caller's typo fails loudly."""
    return sorted(set(requirements) - set(VOCABULARY))


def disagreements(declared, reference):
    """Capabilities two sources both report, with different values.

    The host's inventory and the catalog answer different questions: the catalog says what
    the model accepts at its vendor, the host says what reaches it through this gateway. A
    gateway that drops video for a model whose vendor accepts it shows up here.
    """
    out = []
    for requirement in VOCABULARY:
        if requirement == "output.non_text":
            continue
        a, b = has(declared, requirement), has(reference, requirement)
        if a is not None and b is not None and a != b:
            out.append({"capability": requirement, "host": a, "catalog": b})
    return out
