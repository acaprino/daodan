from dataclasses import dataclass


@dataclass(frozen=True)
class Addition:
    type: str  # "planned" or "free"
    dish_id: str | None  # plan dish fulfilled, only when type == "planned"
    name: str
    kcal: int


@dataclass(frozen=True)
class Record:
    """What the user logged for one slot."""

    meal_id: str
    additions: tuple[Addition, ...] = ()
    skipped: bool = False  # the user marked the meal as skipped
    deleted: bool = False  # tombstone kept for sync


def states_nothing(record: Record | None) -> bool:
    """True when the slot has nothing logged: no record, a tombstone or no additions."""
    return record is None or record.deleted or not record.additions


def kcal(records: dict[str, Record]) -> int:
    return sum(a.kcal for r in records.values() if not r.deleted for a in r.additions)
