"""Task 2: la mini-app in app/ contiene le strutture intenzionali ed è importabile."""
import compileall
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP = HERE / "app"
PACKAGES = APP / "packages"


def _read(rel):
    return (APP / rel).read_text(encoding="utf-8")


def test_app_compiles():
    assert APP.is_dir(), "app/ assente"
    assert compileall.compile_dir(str(APP), quiet=1)


def test_packages_importable():
    sys.path.insert(0, str(PACKAGES))
    try:
        import orders.api  # noqa: F401
        import payments.gateway  # noqa: F401
        import shipping.rates  # noqa: F401
    finally:
        sys.path.remove(str(PACKAGES))


def test_callback_dispatch_structures():
    api = _read("packages/orders/api.py")
    assert "EVENT_REGISTRY" in api
    assert "def on_event(" in api
    assert "def _invoke(" in api
    assert "KeyError" in api


def test_pay_online_alias_chain():
    gw = _read("packages/payments/gateway.py")
    assert 'REGISTRY["pay_online"]' in gw
    lines = gw.splitlines()
    idx = next(i for i, ln in enumerate(lines) if 'REGISTRY["pay_online"]' in ln)
    assert any("handler(" in ln for ln in lines[idx:idx + 3])


def test_unknown_receiver_pipeline():
    svc = _read("packages/orders/service.py")
    assert "self._pipeline.step(" in svc
    assert "setattr(" in svc


def test_dynamic_send_via():
    notif = _read("packages/orders/notifications.py")
    assert "def send_via(" in notif
    # destinazione fuori dai sorgenti: letta da variabile d'ambiente e caricata con importlib
    assert "os.environ[" in notif
    assert "importlib.import_module(" in notif
    assert "globals()[" not in notif
    assert "def channel_" not in notif, "un destinatario nei sorgenti rende il collegamento confermabile"


def test_reporting_incidental_pricing_use():
    rep = _read("packages/orders/reporting.py")
    assert "from . import pricing" in rep or "from .pricing import" in rep
    assert "pricing.VAT_RATE" in rep
    # uso esclusivamente accessorio: nessun altro simbolo di pricing
    assert rep.count("pricing.") == rep.count("pricing.VAT_RATE")


def test_ambiguous_discount_terms():
    assert "def compute_discount(" in _read("packages/orders/pricing.py")
    assert "def volume_discount(" in _read("packages/shipping/rates.py")


def test_vat_spread_at_least_8_files():
    hits = [p for p in APP.rglob("*.py")
            if "VAT" in p.read_text(encoding="utf-8") or "IVA" in p.read_text(encoding="utf-8")]
    assert len(hits) >= 8


def test_big_module_size():
    text = _read("packages/orders/big_module.py")
    assert len(text.splitlines()) >= 700
    # >100 simboli: l'outline di C7 deve troncare al limit di default (100)
    assert text.count("def ") >= 101


def test_refunds_feature_terms():
    text = _read("packages/payments/refunds.py")
    assert "refund" in text.lower()
    assert "rimborsi" in text.lower()
