"""External services found in pinned project-model fixtures."""

import csv
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "benchmarks/project-model"
sys.path.insert(0, str(ROOT / "daodan/core"))
import service_registry  # noqa: E402


class CorpusServiceRulesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = {entry["id"]: entry for entry in service_registry.load()["entries"]}
        with (CORPUS / "service-rule-evidence.tsv").open(encoding="utf-8", newline="") as stream:
            cls.evidence = list(csv.DictReader(stream, delimiter="\t"))

    def test_corpus_evidence_identifies_a_labelled_service(self):
        labels = {}
        for row in self.evidence:
            fixture = row["fixture"]
            with self.subTest(fixture=fixture, signal=row["signal"]):
                if fixture not in labels:
                    expected = CORPUS / "fixtures" / fixture / "expected.json"
                    labels[fixture] = {s["name"] for s in json.loads(expected.read_text(encoding="utf-8"))["services"]}
                self.assertIn(row["expected_service"], labels[fixture])
                self.assertGreater(int(row["line"]), 0)
                self.assertEqual(service_registry.entry_category(self.entries[row["id"]]), "service")

    def test_corpus_signals_survive_the_registry_build(self):
        for row in self.evidence:
            ident, selector, signal = row["id"], row["selector"], row["signal"]
            with self.subTest(ident=ident, selector=selector, signal=signal):
                signs = self.entries[ident]["signs"]
                if selector in {"env", "hosts"}:
                    self.assertIn(signal, signs[selector])
                else:
                    path, line = row["path"], int(row["line"])
                    facts = [(selector, signal, path, line, None)]
                    project = service_registry.Project(facts, [], lambda _: [])
                    answer = service_registry.check_packages([self.entries[ident]], project)
                    self.assertEqual(answer["signs"], [(ident, signal, path, line)])

    def test_related_packages_do_not_identify_specific_services(self):
        cases = (
            ("firebase.messaging", "maven", "com.google.firebase:firebase-bom"),
            ("firebase.messaging", "maven", "org.example:firebase-messaging"),
            ("firebase.analytics", "maven", "com.google.firebase:firebase-messaging"),
            ("azure.keyvault", "nuget", "Azure.Identity"),
            ("google.oauth", "npm", "openid-client"),
            ("flagd", "go", "github.com/open-feature/go-sdk"),
            ("minio", "go", "github.com/minio/md5-simd"),
            ("openldap", "pypi", "python-ldap"),
            ("gotenberg", "docker", "acme/gotenberg"),
            ("apple.signin", "npm", "apple-signin-auth-mock"),
        )
        for ident, ecosystem, name in cases:
            with self.subTest(ident=ident, package=name):
                project = service_registry.Project([(ecosystem, name, None, None, None)], [], lambda _: [])
                self.assertEqual(service_registry.check_packages([self.entries[ident]], project)["signs"], [])

    def test_azure_storage_clients_identify_the_supported_service(self):
        entries = [self.entries["azure.storage"], self.entries["azure.blobstorage"]]
        choices = (
            ("rubygems", "azure-blob", "azure.blobstorage"),
            ("npm", "@azure/storage-blob", "azure.blobstorage"),
            ("pypi", "azure-storage-blob", "azure.blobstorage"),
            ("rubygems", "azure-storage-common", "azure.storage"),
            ("npm", "@azure/storage-queue", "azure.storage"),
            ("npm", "@azure/storage-file-share", "azure.storage"),
        )
        for ecosystem, name, ident in choices:
            with self.subTest(ecosystem=ecosystem, package=name):
                project = service_registry.Project([(ecosystem, name, None, None, None)], [], lambda _: [])
                self.assertEqual(service_registry.check_packages(entries, project)["signs"], [(ident, name, None, None)])
