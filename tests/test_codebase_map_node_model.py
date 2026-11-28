"""The model of a node: species, derived natures, concrete or abstract."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
import flows  # noqa: E402
import node_model  # noqa: E402
import system_map  # noqa: E402

ENVELOPE_TYPES = ("module", "component", "feature", "virtual", "build", "directory", "file", "symbol", "store", "external")


class NodeModelTests(unittest.TestCase):
    def test_every_species_has_a_nature(self):
        self.assertEqual(set(node_model.NATURE_OF), set(node_model.SPECIES) - {"gruppo"})
        self.assertLessEqual(set(node_model.NATURE_OF.values()), set(node_model.NATURES))

    def test_every_type_of_the_envelope_and_of_the_system_map_has_a_species(self):
        for kind in ENVELOPE_TYPES + tuple(node_model.ENVELOPE_SPECIES):
            self.assertIn(node_model.species_of({"type": kind}), node_model.SPECIES, kind)
        for kind in flows.NODE_TYPES + system_map.NODE_TYPES:
            self.assertEqual(node_model.species_of({"type": kind}), kind)
        with self.assertRaises(ValueError):
            node_model.species_of({"type": "nessuno"})

    def test_an_external_node_takes_the_species_of_its_entry(self):
        self.assertEqual(node_model.species_of({"type": "external", "node_type": "database"}), "database")
        self.assertEqual(node_model.species_of({"type": "external", "node_type": None}), "servizio o API")

    def test_an_external_service_is_logical_and_physical(self):
        self.assertEqual(node_model.natures("servizio o API", "external"), ["logico", "fisico"])
        self.assertEqual(node_model.natures("servizio o API"), ["logico"])
        self.assertEqual(node_model.natures("database", "external"), ["fisico"])
        self.assertEqual(node_model.natures("file"), ["codice"])

    def test_a_group_has_the_natures_of_what_it_holds(self):
        held = [node_model.natures("tecnologia"), node_model.natures("gateway", "external"), node_model.natures("store")]
        self.assertEqual(node_model.natures("gruppo", "internal", held), ["logico", "dati", "codice", "fisico"])
        self.assertEqual(node_model.natures("gruppo"), [])

    def test_actors_entities_features_groups_and_logical_modules_are_abstract(self):
        for species in ("attore", "entità", "funzionalità", "gruppo"):
            self.assertFalse(node_model.concrete(species), species)
        self.assertFalse(node_model.concrete("modulo", "logical"))
        self.assertTrue(node_model.concrete("modulo", "concrete"))
        self.assertTrue(node_model.concrete("modulo", "virtual"))
        self.assertTrue(node_model.concrete("servizio o API"))


if __name__ == "__main__":
    unittest.main()
