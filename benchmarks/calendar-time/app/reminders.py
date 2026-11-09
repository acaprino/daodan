"""Floating reminders: a reminder rings at its wall-clock time in the user's current zone."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


@dataclass
class User:
    zone: ZoneInfo


@dataclass
class Reminder:
    id: str
    at: time  # wall-clock time, e.g. 09:00
    every_days: int = 1
    next_at: datetime | None = None  # next ring, UTC
    last_fired: datetime | None = None  # UTC


def ring_at(rem: Reminder, day: date, user: User) -> datetime:
    return datetime.combine(day, rem.at, tzinfo=user.zone).astimezone(timezone.utc)


def create(rem_id: str, at: time, start: date, user: User, every_days: int = 1) -> Reminder:
    rem = Reminder(rem_id, at, every_days)
    rem.next_at = ring_at(rem, start, user)
    return rem


def set_zone(user: User, name: str) -> None:
    """Called when the device reports a new zone."""
    user.zone = ZoneInfo(name)


def tick(now: datetime, reminders: list[Reminder]) -> list[Reminder]:
    """Runs every minute on the server; returns the reminders that ring."""
    rung = []
    for rem in reminders:
        if rem.next_at is not None and rem.next_at <= now:
            rem.last_fired = now
            while rem.next_at <= now:
                rem.next_at += timedelta(days=rem.every_days)
            rung.append(rem)
    return rung


def done_on(rem: Reminder, day: date) -> bool:
    return rem.last_fired is not None and rem.last_fired.date() == day


def card(rem: Reminder, day: date) -> str:
    """Text of the reminder card for a local day."""
    shown = datetime.combine(day, rem.at).strftime("%H:%M")
    return f"{shown} {'done' if done_on(rem, day) else 'to do'}"
