from dataclasses import dataclass, field
from datetime import datetime, time
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Rule:
    """Rings at `at` on each listed weekday, at most once per date, in the user's current zone."""

    id: str
    at: time
    weekdays: frozenset[int]  # 0 = Monday


@dataclass
class User:
    account_zone: ZoneInfo  # chosen at sign-up
    device_zone: ZoneInfo  # last zone reported by the phone


@dataclass
class State:
    next_at: dict[str, datetime] = field(default_factory=dict)  # UTC
    last_rung: dict[str, datetime] = field(default_factory=dict)  # UTC
