"""Le varianti di catalogo sono il catalogo di riferimento più ciò che dichiarano, e `bind` ne ricava i job dei bracci.

I ruoli candidati sono quelli registrati nel README: un testo cambiato fa fallire il suo SHA-256.
"""

import hashlib
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT / "daodan/core"))
sys.path.insert(0, str(HERE))

import composition  # noqa: E402
import plugin_copy  # noqa: E402

P = "senior-review:"
ROLE_SHA256 = {
    "fastapi-auditor": "2b72e8c0f76a5cdb7ca6f3c7057930fb71fd46824f954911a6c4524157eee260",
    "nextjs-auditor": "3752e839330c04ca02bc696edf5dec995f35ea262e7661174c0f25c3fa243513",
    "sqlalchemy-auditor": "769854e4c870bc29cf06ac278244374e9fd19f1b4fc24cbd01e757bb7217d617",
    "zod-auditor": "b953b67230feb3bf908400dcd57cd986085aa60ac4a2f3d403055eee455681b1",
}
# Per variante: i ruoli aggiunti al catalogo e le composizioni che cambiano; `+` aggiunge in coda a quella di riferimento.
VARIANTS = {
    "S1-ospiti": {"roles": ["fastapi-auditor", "stack-host"],
                  "compositions": {"stack-host": ["fastapi-auditor"]}},
    "S1-foglia": {"roles": ["fastapi-auditor", "sqlalchemy-auditor", "stack-host"],
                  "compositions": {"stack-host": ["fastapi-auditor", "sqlalchemy-auditor"],
                                   "data-integrity-auditor": ["+", "sqlalchemy-auditor"]}},
    "N1-ruolo": {"roles": ["nextjs-auditor"], "compositions": {}},
    "Z1-ospiti": {"roles": ["nextjs-auditor", "stack-host"],
                  "compositions": {"stack-host": ["nextjs-auditor"]}},
    "Z1-foglia": {"roles": ["nextjs-auditor", "zod-auditor", "stack-host"],
                  "compositions": {"stack-host": ["nextjs-auditor", "zod-auditor"],
                                   "security-auditor": ["+", "zod-auditor"]}},
}
# Per caso con foglia: le due varianti, l'ospite di dominio, la foglia e il ruolo che è l'ospite di stack.
LEAF_CASES = {"S1": ("data-integrity-auditor", "sqlalchemy-auditor", "fastapi-auditor"),
              "Z1": ("security-auditor", "zod-auditor", "nextjs-auditor")}
CANDIDATE = {"ref": "target", "snapshot": "snapshot"}


def catalog(path: Path) -> tuple[list[str], dict[str, list[str]]]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return data["components"]["roles"], {name: table["members"]
                                         for name, table in data["reviewers"]["compositions"].items()}


def jobs(variant: str, selection: list[str]) -> dict[str, dict]:
    """I job che `bind` lega dalla copia del plugin della variante, per ruolo."""
    roster = {"schema": composition.ROSTER_SCHEMA, "shape": "branch", "roster": [], "required_specialists": [],
              "jobs": [], "grounding": {"scope_id": "candidate", "candidate": CANDIDATE}, "gaps": []}
    bindings = {"candidate": CANDIDATE, "knowledge_selection": "", "selection": [P + name for name in selection]}
    with tempfile.TemporaryDirectory() as tmp:
        prepared = composition.bind(roster, bindings, plugin_copy.build(variant, Path(tmp) / "plugin"))
    return {job["role"].removeprefix(P): job for job in prepared["jobs"]}


class VariantTest(unittest.TestCase):
    def test_candidate_roles_are_the_recorded_texts(self):
        for name, digest in ROLE_SHA256.items():
            self.assertEqual(hashlib.sha256((HERE / "roles" / f"{name}.md").read_bytes()).hexdigest(), digest, name)

    def test_variant_is_the_reference_catalog_plus_what_it_declares(self):
        roles, compositions = catalog(plugin_copy.REVIEW / "catalog.toml")
        for name, declared in VARIANTS.items():
            got_roles, got = catalog(HERE / "catalogs" / f"{name}.toml")
            self.assertEqual(got_roles, roles + declared["roles"], name)
            expected = dict(compositions)
            for key, members in declared["compositions"].items():
                tail = [P + member for member in members if member != "+"]
                expected[key] = (compositions[key] if members[0] == "+" else []) + tail
            self.assertEqual(got, expected, name)

    def test_hosts_differ_between_the_variants_by_the_leaf_only(self):
        for case, (domain, leaf, stack) in LEAF_CASES.items():
            hosts = [domain, "stack-host"]
            without, with_leaf = jobs(f"{case}-ospiti", hosts), jobs(f"{case}-foglia", hosts)
            for host in hosts:
                self.assertEqual(with_leaf[host]["specialist_ids"], without[host]["specialist_ids"] + [P + leaf],
                                 (case, host))
                self.assertEqual(with_leaf[host]["status"], "bound", (case, host))
                self.assertEqual(with_leaf[host]["source_bindings"][P + leaf]["sha256"], ROLE_SHA256[leaf])
            self.assertEqual(without["stack-host"]["specialist_ids"], [P + stack], case)
            self.assertEqual(without["stack-host"]["source_bindings"][P + stack]["sha256"], ROLE_SHA256[stack])

    def test_the_candidate_alone_is_one_job(self):
        for variant, name in (("S1-foglia", "sqlalchemy-auditor"), ("Z1-foglia", "zod-auditor"),
                              ("N1-ruolo", "nextjs-auditor")):
            job = jobs(variant, [name])[name]
            self.assertEqual(job["specialist_ids"], [P + name], variant)
            self.assertEqual(job["status"], "bound", variant)
            self.assertEqual(job["source_bindings"][P + name]["sha256"], ROLE_SHA256[name])


if __name__ == "__main__":
    unittest.main()
