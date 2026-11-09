from diary import is_logged
from diary_store import DiaryStore
from plan_store import PlanStore


def adherence(plan: PlanStore, diary: DiaryStore, days: list[str]) -> float:
    """Share of planned dishes the user ate this week."""
    slots = plan.week(days)
    if not slots:
        return 0.0
    return sum(1 for s in slots if is_logged(diary, s.meal_id)) / len(slots)
