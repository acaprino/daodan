"""Adapters of the SCIP indexers: what each index states its own way, read by `code_graph`.

An adapter module that declares `ENTRY`, `LANGUAGES`, `UNIT_KINDS` and `NEEDS_CONTAINER` is an analyzer of the
pass (`analyzers`): the pass's entries are built from these declarations, not from a list of its own.
"""


def analyzers() -> list:
    """Every adapter module that declares itself an analyzer, the lightest first (`MIN_FREE`, then the entry's
    name): a stage that runs out of memory stops the ones after it, so the heavy ones come last."""
    import importlib
    import pkgutil
    found = []
    for item in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f"{__name__}.{item.name}")
        if hasattr(module, "ENTRY"):
            found.append(module)
    return sorted(found, key=lambda module: (module.MIN_FREE, module.ENTRY))
