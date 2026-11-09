from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from model import Rule


def resolve(day: date, at: time, zone: ZoneInfo, fold: int = 0) -> datetime:
    """Instant of a wall-clock time on a local day."""
    return datetime.combine(day, at, tzinfo=zone).replace(fold=fold).astimezone(timezone.utc)


def next_occurrence(rule: Rule, after: datetime, zone: ZoneInfo) -> datetime:
    """First ring strictly after `after` (UTC)."""
    start = after.astimezone(zone).date()
    for offset in range(8):
        day = start + timedelta(days=offset)
        ring = resolve(day, rule.at, zone)
        if ring > after and ring.weekday() in rule.weekdays:
            return ring
    raise ValueError(f"rule {rule.id} has no weekday")
