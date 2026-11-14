"""Runs each shape of lib.py once; the expected pairs are written in test_dynamic_record.py."""
import json

from lib import Box, Child, Guard, add, apply, count, fail, opened


def double(x):
    return x * 2


def run():
    add(1, 2)
    apply(double, 3)
    apply(lambda v: v, 4)
    getattr(Child(), "speak")()
    Child.make()
    box = Box(1)
    box.size
    box.size = 2
    box < Box(3)
    total = 0
    for i in count(2):
        total += i
    try:
        fail()
    except ValueError:
        json.dumps(len("ab"))
    sorted([2, 1], key=double)
    with Guard():
        pass
    opened()


run()
