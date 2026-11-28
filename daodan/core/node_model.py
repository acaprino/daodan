#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""The model of a node of the map (`docs/specs/architettura.md`, «La mappa», «Proprietà»): its species, its natures
and whether it is concrete. The nature is never written: it is derived from species and position.

A node of the envelope (`daodan/visual@1`) has its species from its `type` (`ENVELOPE_SPECIES`); an external one
takes the type of its registry entry or rule (`node_type`) when that is a species. A node of the system map has a
`type` that is already a species (`flows.NODE_TYPES` and the system map's own).
"""
from __future__ import annotations

SPECIES = ("attore", "applicazione", "schermata",
           "funzionalità", "servizio o API", "gateway", "autenticazione", "lavoro a orario", "altro",
           "entità", "store",
           "modulo", "cartella", "file", "simbolo",
           "database", "coda", "filesystem", "dispositivo", "container", "servizio in esecuzione", "rete",
           "tecnologia", "gruppo")
NATURES = ("persone", "logico", "dati", "codice", "fisico")
NATURE_OF = {
    **dict.fromkeys(("attore", "applicazione", "schermata"), "persone"),
    **dict.fromkeys(("funzionalità", "servizio o API", "gateway", "autenticazione", "lavoro a orario", "altro"), "logico"),
    **dict.fromkeys(("entità", "store"), "dati"),
    **dict.fromkeys(("modulo", "cartella", "file", "simbolo", "tecnologia"), "codice"),
    **dict.fromkeys(("database", "coda", "filesystem", "dispositivo", "container", "servizio in esecuzione", "rete"),
                    "fisico"),
}
ENVELOPE_SPECIES = {"module": "modulo", "component": "modulo", "build": "modulo", "virtual": "modulo",
                    "feature": "funzionalità", "directory": "cartella", "file": "file", "symbol": "simbolo",
                    "store": "store", "external": "servizio o API", "technology": "tecnologia", "group": "gruppo"}
ABSTRACT = ("attore", "entità", "funzionalità", "gruppo")


def species_of(node: dict) -> str:
    """The species of a node of the envelope or of the system map, by its `type`."""
    kind = node["type"]
    if kind in SPECIES:
        return kind
    if kind == "external" and node.get("node_type") in SPECIES:
        return node["node_type"]
    if kind not in ENVELOPE_SPECIES:
        raise ValueError(f"no species for the node type {kind!r}")
    return ENVELOPE_SPECIES[kind]


def natures(species: str, position: str = "internal", contained=()) -> list[str]:
    """A node's natures, in the order of NATURES: its species' one; an external service is also physical; a group
    has the natures of what it holds (`contained`, the natures of each node inside)."""
    if species == "gruppo":
        held = {nature for found in contained for nature in found}
        return [nature for nature in NATURES if nature in held]
    home = NATURE_OF[species]
    return [home, "fisico"] if position == "external" and home == "logico" else [home]


def concrete(species: str, realization: str | None = None) -> bool:
    """Whether a node has a thing of its own to point at: actors, entities, features and groups are abstract, and so
    is a module that only names related responsibilities (the module graph's `nature` `logical`)."""
    return species not in ABSTRACT and not (species == "modulo" and realization == "logical")
