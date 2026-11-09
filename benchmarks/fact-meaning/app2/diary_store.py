from dataclasses import dataclass, field


@dataclass(frozen=True)
class Addition:
    type: str  # "planned" or "free"
    dish_id: str | None
    name: str
    kcal: int


@dataclass
class Entry:
    meal_id: str
    additions: list[Addition] = field(default_factory=list)


class DiaryStore:
    """Food diary written by the user."""

    def __init__(self) -> None:
        self.entries: dict[str, Entry] = {}

    def entry(self, meal_id: str) -> Entry:
        return self.entries.setdefault(meal_id, Entry(meal_id))
