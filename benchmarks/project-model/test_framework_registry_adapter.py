"""Compare the service baseline on declarations while retaining mentions for inspection."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))
import daodan_registry


def test_only_declared_services_are_scored_and_evidence_comes_from_the_declaration():
    mention = {"sign": "host", "strength": "mentioned", "value": "api.stripe.com", "path": "ui.ts"}
    declaration = {"sign": "package", "strength": "declared", "value": "stripe", "path": "package.json"}
    stripe = {"id": "stripe", "name": "Stripe", "type": "gateway", "kind": "service", "signs": [mention]}
    only_mentioned = daodan_registry.normalise([stripe])
    assert only_mentioned["services"] == []
    assert only_mentioned["detail"]["ids"] == ["stripe"]
    assert only_mentioned["detail"]["entries"]["stripe"]["signs"] == ["host:api.stripe.com@ui.ts"]

    result = daodan_registry.normalise([{**stripe, "signs": [mention, declaration]}])
    assert result["services"] == [{"name": "Stripe", "kind": "gateway", "evidence": "package.json"}]
    assert len(result["detail"]["entries"]["stripe"]["signs"]) == 2
