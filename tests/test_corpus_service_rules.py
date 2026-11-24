"""External services found in pinned project-model fixtures."""

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "benchmarks/project-model"
sys.path.insert(0, str(ROOT / "daodan/core"))
import service_registry  # noqa: E402
from test_codebase_map_stack_recognition import fact, package_signs, recognized  # noqa: E402


class CorpusServiceRulesTests(unittest.TestCase):
    def work(self) -> Path:
        return Path(self.enterContext(tempfile.TemporaryDirectory(prefix="corpus-service-")))

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

    @pytest.mark.usefixtures("real_stack")
    def test_corpus_signals_survive_the_registry_build(self):
        # The `env` and `hosts` signals are the registry's (the registry's build, B5); a package is the release's.
        packages = [row for row in self.evidence if row["selector"] not in {"env", "hosts"}]
        found = package_signs(recognized(self.work(), packages=[
            fact(row["selector"], row["signal"], f"{row['path']}#L{row['line']}", "pre-map@1") for row in packages]))
        for row in self.evidence:
            ident, selector, signal = row["id"], row["selector"], row["signal"]
            with self.subTest(ident=ident, selector=selector, signal=signal):
                if selector in {"env", "hosts"}:
                    self.assertIn(signal, self.entries[ident]["signs"][selector])
                else:
                    self.assertIn((ident, signal, row["path"], int(row["line"])), found)

    @pytest.mark.usefixtures("real_stack")
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
                found = package_signs(recognized(self.work(), packages=[
                    fact(ecosystem, name, "manifest", "pre-map@1")]))
                self.assertNotIn(ident, {i for i, *_ in found})

    @pytest.mark.usefixtures("real_stack")
    def test_azure_storage_clients_identify_the_supported_service(self):
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
                found = package_signs(recognized(self.work(), packages=[
                    fact(ecosystem, name, "manifest", "pre-map@1")]))
                self.assertEqual({i for i, *_ in found} & {"azure.storage", "azure.blobstorage"}, {ident})
                self.assertIn((ident, name, "manifest", None), found)
