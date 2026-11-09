from dataclasses import dataclass


@dataclass(frozen=True)
class Dish:
    id: str
    name: str
    kcal: int


@dataclass(frozen=True)
class PlanSlot:
    meal_id: str  # "2026-11-09/lunch"
    dishes: tuple[Dish, ...]


class PlanStore:
    """Meal plan written by the coach screen."""

    def __init__(self) -> None:
        self.slots: dict[str, PlanSlot] = {}

    def put(self, slot: PlanSlot) -> None:
        self.slots[slot.meal_id] = slot

    def week(self, days: list[str]) -> list[PlanSlot]:
        return [s for s in self.slots.values() if s.meal_id.split("/")[0] in days]
