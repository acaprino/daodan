from diary_store import Addition, DiaryStore
from plan_store import Dish


def add_food(store: DiaryStore, meal_id: str, name: str, kcal: int) -> None:
    """Food picked from the search box."""
    store.entry(meal_id).additions.append(Addition("free", None, name, kcal))


def log_planned(store: DiaryStore, meal_id: str, dish: Dish) -> None:
    """"I ate it" button next to a plan dish."""
    store.entry(meal_id).additions.append(Addition("planned", dish.id, dish.name, dish.kcal))


def is_logged(store: DiaryStore, meal_id: str) -> bool:
    entry = store.entries.get(meal_id)
    return entry is not None and bool(entry.additions)
