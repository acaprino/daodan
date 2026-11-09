from dataclasses import dataclass


@dataclass(frozen=True)
class Dish:
    id: str
    name: str
    kcal: int


@dataclass(frozen=True)
class Slot:
    meal_id: str  # e.g. "2026-11-09/lunch"
    dishes: tuple[Dish, ...]
