"""Reportistica giornaliera: intestazione e righe del riepilogo.

L'intestazione riporta il tasso IVA (VAT) corrente;
le righe sono già formattate dal chiamante.
"""
from . import pricing


def format_daily_summary(rows):
    """Intestazione col tasso IVA (VAT) e righe pre-formattate."""
    header = f"Daily summary (VAT {pricing.VAT_RATE:.0%})"
    lines = [header]
    for row in rows:
        lines.append(f"{row['id']}: {row['total']}")
    return "\n".join(lines)
