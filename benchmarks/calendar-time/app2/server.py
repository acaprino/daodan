from datetime import date, datetime
from zoneinfo import ZoneInfo

from model import Rule, State, User
from planner import next_occurrence


def tick(now: datetime, user: User, rules: list[Rule], state: State) -> list[tuple[str, datetime]]:
    """Runs every minute; returns (rule id, scheduled instant) of the pushes sent now."""
    pushed = []
    for rule in rules:
        due = state.next_at.get(rule.id)
        if due is not None and due <= now:
            state.last_rung[rule.id] = now
            state.next_at[rule.id] = next_occurrence(rule, now, user.device_zone)
            pushed.append((rule.id, due))
    return pushed


def on_zone_change(user: User, zone: ZoneInfo, rules: list[Rule], state: State, now: datetime) -> None:
    """The phone reported a new zone: plan every reminder again in it."""
    user.device_zone = zone
    for rule in rules:
        state.next_at[rule.id] = next_occurrence(rule, now, zone)


def today(user: User, now: datetime) -> date:
    """Local day shown by the "Today" list."""
    return now.astimezone(user.account_zone).date()
