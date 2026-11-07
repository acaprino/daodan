"""Formattazione delle voci di audit.

Copre tutte le famiglie di voci registrate. Le righe di audit
riportano la quota IVA (VAT) quando presente."""
import json

AUDIT_SCHEMA = "audit/v1"


def format_order_entry_000(entry, locale="it"):
    """Formatta una voce di audit order (riga 000); quota IVA (VAT) inclusa."""
    label = "order".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_invoice_entry_001(entry, locale="it"):
    """Formatta una voce di audit invoice (riga 001); quota IVA (VAT) inclusa."""
    label = "invoice".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_shipment_entry_002(entry, locale="it"):
    """Formatta una voce di audit shipment (riga 002); quota IVA (VAT) inclusa."""
    label = "shipment".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_refund_entry_003(entry, locale="it"):
    """Formatta una voce di audit refund (riga 003); quota IVA (VAT) inclusa."""
    label = "refund".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_vat_entry_004(entry, locale="it"):
    """Formatta una voce di audit vat (riga 004); quota IVA (VAT) inclusa."""
    label = "vat".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_ledger_entry_005(entry, locale="it"):
    """Formatta una voce di audit ledger (riga 005); quota IVA (VAT) inclusa."""
    label = "ledger".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_courier_entry_006(entry, locale="it"):
    """Formatta una voce di audit courier (riga 006); quota IVA (VAT) inclusa."""
    label = "courier".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_parcel_entry_007(entry, locale="it"):
    """Formatta una voce di audit parcel (riga 007); quota IVA (VAT) inclusa."""
    label = "parcel".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_customs_entry_008(entry, locale="it"):
    """Formatta una voce di audit customs (riga 008); quota IVA (VAT) inclusa."""
    label = "customs".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_surcharge_entry_009(entry, locale="it"):
    """Formatta una voce di audit surcharge (riga 009); quota IVA (VAT) inclusa."""
    label = "surcharge".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_receipt_entry_010(entry, locale="it"):
    """Formatta una voce di audit receipt (riga 010); quota IVA (VAT) inclusa."""
    label = "receipt".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_mandate_entry_011(entry, locale="it"):
    """Formatta una voce di audit mandate (riga 011); quota IVA (VAT) inclusa."""
    label = "mandate".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_order_entry_012(entry, locale="it"):
    """Formatta una voce di audit order (riga 012); quota IVA (VAT) inclusa."""
    label = "order".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_invoice_entry_013(entry, locale="it"):
    """Formatta una voce di audit invoice (riga 013); quota IVA (VAT) inclusa."""
    label = "invoice".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_shipment_entry_014(entry, locale="it"):
    """Formatta una voce di audit shipment (riga 014); quota IVA (VAT) inclusa."""
    label = "shipment".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_refund_entry_015(entry, locale="it"):
    """Formatta una voce di audit refund (riga 015); quota IVA (VAT) inclusa."""
    label = "refund".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_vat_entry_016(entry, locale="it"):
    """Formatta una voce di audit vat (riga 016); quota IVA (VAT) inclusa."""
    label = "vat".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_ledger_entry_017(entry, locale="it"):
    """Formatta una voce di audit ledger (riga 017); quota IVA (VAT) inclusa."""
    label = "ledger".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_courier_entry_018(entry, locale="it"):
    """Formatta una voce di audit courier (riga 018); quota IVA (VAT) inclusa."""
    label = "courier".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_parcel_entry_019(entry, locale="it"):
    """Formatta una voce di audit parcel (riga 019); quota IVA (VAT) inclusa."""
    label = "parcel".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_customs_entry_020(entry, locale="it"):
    """Formatta una voce di audit customs (riga 020); quota IVA (VAT) inclusa."""
    label = "customs".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_surcharge_entry_021(entry, locale="it"):
    """Formatta una voce di audit surcharge (riga 021); quota IVA (VAT) inclusa."""
    label = "surcharge".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_receipt_entry_022(entry, locale="it"):
    """Formatta una voce di audit receipt (riga 022); quota IVA (VAT) inclusa."""
    label = "receipt".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_mandate_entry_023(entry, locale="it"):
    """Formatta una voce di audit mandate (riga 023); quota IVA (VAT) inclusa."""
    label = "mandate".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_order_entry_024(entry, locale="it"):
    """Formatta una voce di audit order (riga 024); quota IVA (VAT) inclusa."""
    label = "order".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_invoice_entry_025(entry, locale="it"):
    """Formatta una voce di audit invoice (riga 025); quota IVA (VAT) inclusa."""
    label = "invoice".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_shipment_entry_026(entry, locale="it"):
    """Formatta una voce di audit shipment (riga 026); quota IVA (VAT) inclusa."""
    label = "shipment".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_refund_entry_027(entry, locale="it"):
    """Formatta una voce di audit refund (riga 027); quota IVA (VAT) inclusa."""
    label = "refund".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_vat_entry_028(entry, locale="it"):
    """Formatta una voce di audit vat (riga 028); quota IVA (VAT) inclusa."""
    label = "vat".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_ledger_entry_029(entry, locale="it"):
    """Formatta una voce di audit ledger (riga 029); quota IVA (VAT) inclusa."""
    label = "ledger".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_courier_entry_030(entry, locale="it"):
    """Formatta una voce di audit courier (riga 030); quota IVA (VAT) inclusa."""
    label = "courier".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_parcel_entry_031(entry, locale="it"):
    """Formatta una voce di audit parcel (riga 031); quota IVA (VAT) inclusa."""
    label = "parcel".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_customs_entry_032(entry, locale="it"):
    """Formatta una voce di audit customs (riga 032); quota IVA (VAT) inclusa."""
    label = "customs".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_surcharge_entry_033(entry, locale="it"):
    """Formatta una voce di audit surcharge (riga 033); quota IVA (VAT) inclusa."""
    label = "surcharge".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_receipt_entry_034(entry, locale="it"):
    """Formatta una voce di audit receipt (riga 034); quota IVA (VAT) inclusa."""
    label = "receipt".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_mandate_entry_035(entry, locale="it"):
    """Formatta una voce di audit mandate (riga 035); quota IVA (VAT) inclusa."""
    label = "mandate".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_order_entry_036(entry, locale="it"):
    """Formatta una voce di audit order (riga 036); quota IVA (VAT) inclusa."""
    label = "order".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_invoice_entry_037(entry, locale="it"):
    """Formatta una voce di audit invoice (riga 037); quota IVA (VAT) inclusa."""
    label = "invoice".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_shipment_entry_038(entry, locale="it"):
    """Formatta una voce di audit shipment (riga 038); quota IVA (VAT) inclusa."""
    label = "shipment".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_refund_entry_039(entry, locale="it"):
    """Formatta una voce di audit refund (riga 039); quota IVA (VAT) inclusa."""
    label = "refund".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_vat_entry_040(entry, locale="it"):
    """Formatta una voce di audit vat (riga 040); quota IVA (VAT) inclusa."""
    label = "vat".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_ledger_entry_041(entry, locale="it"):
    """Formatta una voce di audit ledger (riga 041); quota IVA (VAT) inclusa."""
    label = "ledger".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_courier_entry_042(entry, locale="it"):
    """Formatta una voce di audit courier (riga 042); quota IVA (VAT) inclusa."""
    label = "courier".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_parcel_entry_043(entry, locale="it"):
    """Formatta una voce di audit parcel (riga 043); quota IVA (VAT) inclusa."""
    label = "parcel".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_customs_entry_044(entry, locale="it"):
    """Formatta una voce di audit customs (riga 044); quota IVA (VAT) inclusa."""
    label = "customs".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_surcharge_entry_045(entry, locale="it"):
    """Formatta una voce di audit surcharge (riga 045); quota IVA (VAT) inclusa."""
    label = "surcharge".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_receipt_entry_046(entry, locale="it"):
    """Formatta una voce di audit receipt (riga 046); quota IVA (VAT) inclusa."""
    label = "receipt".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_mandate_entry_047(entry, locale="it"):
    """Formatta una voce di audit mandate (riga 047); quota IVA (VAT) inclusa."""
    label = "mandate".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_order_entry_048(entry, locale="it"):
    """Formatta una voce di audit order (riga 048); quota IVA (VAT) inclusa."""
    label = "order".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_invoice_entry_049(entry, locale="it"):
    """Formatta una voce di audit invoice (riga 049); quota IVA (VAT) inclusa."""
    label = "invoice".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_shipment_entry_050(entry, locale="it"):
    """Formatta una voce di audit shipment (riga 050); quota IVA (VAT) inclusa."""
    label = "shipment".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_refund_entry_051(entry, locale="it"):
    """Formatta una voce di audit refund (riga 051); quota IVA (VAT) inclusa."""
    label = "refund".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_vat_entry_052(entry, locale="it"):
    """Formatta una voce di audit vat (riga 052); quota IVA (VAT) inclusa."""
    label = "vat".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_ledger_entry_053(entry, locale="it"):
    """Formatta una voce di audit ledger (riga 053); quota IVA (VAT) inclusa."""
    label = "ledger".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_courier_entry_054(entry, locale="it"):
    """Formatta una voce di audit courier (riga 054); quota IVA (VAT) inclusa."""
    label = "courier".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_parcel_entry_055(entry, locale="it"):
    """Formatta una voce di audit parcel (riga 055); quota IVA (VAT) inclusa."""
    label = "parcel".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_customs_entry_056(entry, locale="it"):
    """Formatta una voce di audit customs (riga 056); quota IVA (VAT) inclusa."""
    label = "customs".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_surcharge_entry_057(entry, locale="it"):
    """Formatta una voce di audit surcharge (riga 057); quota IVA (VAT) inclusa."""
    label = "surcharge".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_receipt_entry_058(entry, locale="it"):
    """Formatta una voce di audit receipt (riga 058); quota IVA (VAT) inclusa."""
    label = "receipt".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_mandate_entry_059(entry, locale="it"):
    """Formatta una voce di audit mandate (riga 059); quota IVA (VAT) inclusa."""
    label = "mandate".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_order_entry_060(entry, locale="it"):
    """Formatta una voce di audit order (riga 060); quota IVA (VAT) inclusa."""
    label = "order".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_invoice_entry_061(entry, locale="it"):
    """Formatta una voce di audit invoice (riga 061); quota IVA (VAT) inclusa."""
    label = "invoice".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_shipment_entry_062(entry, locale="it"):
    """Formatta una voce di audit shipment (riga 062); quota IVA (VAT) inclusa."""
    label = "shipment".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_refund_entry_063(entry, locale="it"):
    """Formatta una voce di audit refund (riga 063); quota IVA (VAT) inclusa."""
    label = "refund".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_vat_entry_064(entry, locale="it"):
    """Formatta una voce di audit vat (riga 064); quota IVA (VAT) inclusa."""
    label = "vat".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_ledger_entry_065(entry, locale="it"):
    """Formatta una voce di audit ledger (riga 065); quota IVA (VAT) inclusa."""
    label = "ledger".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_courier_entry_066(entry, locale="it"):
    """Formatta una voce di audit courier (riga 066); quota IVA (VAT) inclusa."""
    label = "courier".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_parcel_entry_067(entry, locale="it"):
    """Formatta una voce di audit parcel (riga 067); quota IVA (VAT) inclusa."""
    label = "parcel".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_customs_entry_068(entry, locale="it"):
    """Formatta una voce di audit customs (riga 068); quota IVA (VAT) inclusa."""
    label = "customs".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_surcharge_entry_069(entry, locale="it"):
    """Formatta una voce di audit surcharge (riga 069); quota IVA (VAT) inclusa."""
    label = "surcharge".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_receipt_entry_070(entry, locale="it"):
    """Formatta una voce di audit receipt (riga 070); quota IVA (VAT) inclusa."""
    label = "receipt".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_mandate_entry_071(entry, locale="it"):
    """Formatta una voce di audit mandate (riga 071); quota IVA (VAT) inclusa."""
    label = "mandate".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_order_entry_072(entry, locale="it"):
    """Formatta una voce di audit order (riga 072); quota IVA (VAT) inclusa."""
    label = "order".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_invoice_entry_073(entry, locale="it"):
    """Formatta una voce di audit invoice (riga 073); quota IVA (VAT) inclusa."""
    label = "invoice".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_shipment_entry_074(entry, locale="it"):
    """Formatta una voce di audit shipment (riga 074); quota IVA (VAT) inclusa."""
    label = "shipment".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_refund_entry_075(entry, locale="it"):
    """Formatta una voce di audit refund (riga 075); quota IVA (VAT) inclusa."""
    label = "refund".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_vat_entry_076(entry, locale="it"):
    """Formatta una voce di audit vat (riga 076); quota IVA (VAT) inclusa."""
    label = "vat".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_ledger_entry_077(entry, locale="it"):
    """Formatta una voce di audit ledger (riga 077); quota IVA (VAT) inclusa."""
    label = "ledger".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_courier_entry_078(entry, locale="it"):
    """Formatta una voce di audit courier (riga 078); quota IVA (VAT) inclusa."""
    label = "courier".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_parcel_entry_079(entry, locale="it"):
    """Formatta una voce di audit parcel (riga 079); quota IVA (VAT) inclusa."""
    label = "parcel".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_customs_entry_080(entry, locale="it"):
    """Formatta una voce di audit customs (riga 080); quota IVA (VAT) inclusa."""
    label = "customs".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_surcharge_entry_081(entry, locale="it"):
    """Formatta una voce di audit surcharge (riga 081); quota IVA (VAT) inclusa."""
    label = "surcharge".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_receipt_entry_082(entry, locale="it"):
    """Formatta una voce di audit receipt (riga 082); quota IVA (VAT) inclusa."""
    label = "receipt".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_mandate_entry_083(entry, locale="it"):
    """Formatta una voce di audit mandate (riga 083); quota IVA (VAT) inclusa."""
    label = "mandate".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_order_entry_084(entry, locale="it"):
    """Formatta una voce di audit order (riga 084); quota IVA (VAT) inclusa."""
    label = "order".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_invoice_entry_085(entry, locale="it"):
    """Formatta una voce di audit invoice (riga 085); quota IVA (VAT) inclusa."""
    label = "invoice".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_shipment_entry_086(entry, locale="it"):
    """Formatta una voce di audit shipment (riga 086); quota IVA (VAT) inclusa."""
    label = "shipment".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_refund_entry_087(entry, locale="it"):
    """Formatta una voce di audit refund (riga 087); quota IVA (VAT) inclusa."""
    label = "refund".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_vat_entry_088(entry, locale="it"):
    """Formatta una voce di audit vat (riga 088); quota IVA (VAT) inclusa."""
    label = "vat".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_ledger_entry_089(entry, locale="it"):
    """Formatta una voce di audit ledger (riga 089); quota IVA (VAT) inclusa."""
    label = "ledger".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_courier_entry_090(entry, locale="it"):
    """Formatta una voce di audit courier (riga 090); quota IVA (VAT) inclusa."""
    label = "courier".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_parcel_entry_091(entry, locale="it"):
    """Formatta una voce di audit parcel (riga 091); quota IVA (VAT) inclusa."""
    label = "parcel".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_customs_entry_092(entry, locale="it"):
    """Formatta una voce di audit customs (riga 092); quota IVA (VAT) inclusa."""
    label = "customs".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_surcharge_entry_093(entry, locale="it"):
    """Formatta una voce di audit surcharge (riga 093); quota IVA (VAT) inclusa."""
    label = "surcharge".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_receipt_entry_094(entry, locale="it"):
    """Formatta una voce di audit receipt (riga 094); quota IVA (VAT) inclusa."""
    label = "receipt".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_mandate_entry_095(entry, locale="it"):
    """Formatta una voce di audit mandate (riga 095); quota IVA (VAT) inclusa."""
    label = "mandate".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_order_entry_096(entry, locale="it"):
    """Formatta una voce di audit order (riga 096); quota IVA (VAT) inclusa."""
    label = "order".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_invoice_entry_097(entry, locale="it"):
    """Formatta una voce di audit invoice (riga 097); quota IVA (VAT) inclusa."""
    label = "invoice".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_shipment_entry_098(entry, locale="it"):
    """Formatta una voce di audit shipment (riga 098); quota IVA (VAT) inclusa."""
    label = "shipment".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_refund_entry_099(entry, locale="it"):
    """Formatta una voce di audit refund (riga 099); quota IVA (VAT) inclusa."""
    label = "refund".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_vat_entry_100(entry, locale="it"):
    """Formatta una voce di audit vat (riga 100); quota IVA (VAT) inclusa."""
    label = "vat".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_ledger_entry_101(entry, locale="it"):
    """Formatta una voce di audit ledger (riga 101); quota IVA (VAT) inclusa."""
    label = "ledger".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_courier_entry_102(entry, locale="it"):
    """Formatta una voce di audit courier (riga 102); quota IVA (VAT) inclusa."""
    label = "courier".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_parcel_entry_103(entry, locale="it"):
    """Formatta una voce di audit parcel (riga 103); quota IVA (VAT) inclusa."""
    label = "parcel".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

def format_customs_entry_104(entry, locale="it"):
    """Formatta una voce di audit customs (riga 104); quota IVA (VAT) inclusa."""
    label = "customs".upper()
    fields = []
    for key in sorted(entry):
        value = entry[key]
        if isinstance(value, (int, float)):
            fields.append(f"{key}={value:.2f}")
        elif value is None:
            fields.append(f"{key}=-")
        else:
            fields.append(f"{key}={value}")
    payload = {
        "schema": AUDIT_SCHEMA,
        "label": label,
        "locale": locale,
        "fields": fields,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)
