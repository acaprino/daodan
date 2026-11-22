"""The offline replay must not credit go-enry paths the stack would leave out."""
import json

import replay_registry_coverage as replay


def test_provider_is_identified_by_the_recorded_product_id():
    assert replay.product_key("gcp.gcs", "Cloud Storage") == replay.score._framework("Google Cloud Storage")
    assert replay.product_key("other", "Cloud Storage") != replay.score._framework("Google Cloud Storage")
    assert replay.product_key("azure.storage", "Azure Storage") != replay.score._framework("Azure Blob Storage")


def test_filename_evidence_respects_snapshot_and_go_enry_exclusions():
    # A copied config is tempting evidence for every entry using that name.
    rows = [
        {"path": "vendor/sub/vite.config.js"},
        {"path": ".cache/vite.config.js"},
        {"path": "docs/vite.config.js", "documentation": True},
        {"path": "out/vite.config.js", "generated": True},
        {"path": "unknown-file.uninventoried"},
        {"path": "source.json"},
        {"path": "expected.json"},
        {"path": "profiles/debug"},
        {"path": "app/Native.SWIFT"},
        {"path": "app/handler.php"},
        {"path": "app/vite.config.js"},
    ]
    run = {"command": {"tool": "daodan-enry", "argv": ["daodan-enry", "."]},
           "result": {"returncode": 0, "stdout": json.dumps(rows)}}
    project, sources = replay.recorded_project([run])
    assert sources == ["go-enry"]
    assert project.files == ["app/Native.SWIFT", "app/handler.php", "app/vite.config.js", "profiles/debug"]
    entry = {"id": "vite", "name": "Vite", "signs": {"files": ["vite.config.js"]}}
    assert replay.detected([entry], project)["frameworks"]["vite"]["path"] == "app/vite.config.js"
