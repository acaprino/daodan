from diary import is_logged
from diary_store import DiaryStore
from plan_store import PlanSlot


def rows(slot: PlanSlot, diary: DiaryStore) -> list[tuple[str, bool]]:
    """Plan dishes of a slot with their check mark."""
    done = is_logged(diary, slot.meal_id)
    return [(dish.name, done) for dish in slot.dishes]


def slot_kcal(slot: PlanSlot, diary: DiaryStore) -> int:
    """Kcal eaten in the slot, shown in its header."""
    entry = diary.entries.get(slot.meal_id)
    return sum(a.kcal for a in entry.additions) if entry else 0
