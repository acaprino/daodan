"""Periodic jobs of the shop service."""
from typing import Callable

JOBS: list[tuple[str, Callable]] = []


def scheduled(cron: str):
    def register(job: Callable) -> Callable:
        JOBS.append((cron, job))
        return job
    return register
