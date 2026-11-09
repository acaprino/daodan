from datetime import date, datetime, timedelta

from model import Rule, User
from planner import resolve


def local_alarms(rule: Rule, user: User, start: date, days: int = 7) -> list[datetime]:
    """Offline fallback: OS alarms for the next days, as instants."""
    alarms = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        if day.weekday() in rule.weekdays:
            alarms.append(resolve(day, rule.at, user.device_zone, fold=1))
    return alarms


def should_show_push(push_at: datetime, alarms: list[datetime]) -> bool:
    """A push that matches a local alarm is not shown twice."""
    return push_at not in alarms
