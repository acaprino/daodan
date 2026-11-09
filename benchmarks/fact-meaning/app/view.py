from log import Record, kcal, states_nothing
from plan import Dish, Slot


def slot_badge(slot: Slot, records: dict[str, Record]) -> str:
    return "empty" if states_nothing(records.get(slot.meal_id)) else "logged"


def dish_eaten(slot: Slot, dish: Dish, records: dict[str, Record]) -> bool:
    """Tick next to a plan dish."""
    return not states_nothing(records.get(slot.meal_id))


def skipped(slot: Slot, records: dict[str, Record]) -> bool:
    """Grey "skipped" label on a slot."""
    return states_nothing(records.get(slot.meal_id))


def ring(records: dict[str, Record], goal: int) -> float:
    """Daily ring: share of the kcal goal reached."""
    return min(kcal(records) / goal, 1.0)
