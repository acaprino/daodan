"""Fixture of test_dynamic_record.py: one shape of call per definition."""
import contextlib
import functools


def trace(fn):
    @functools.wraps(fn)
    def wrapper(*args):
        return fn(*args)

    return wrapper


@trace
def add(a, b):
    return a + b


def apply(fn, value):
    return fn(value)


class Base:
    @classmethod
    def make(cls):
        return cls()

    def speak(self):
        return "base"


class Child(Base):
    def speak(self):
        return "child" + super().speak()


class Box:
    def __init__(self, size):
        self._size = size

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = value

    def __lt__(self, other):
        return self._size < other._size


def count(n):
    i = 0
    while i < n:
        yield i
        i += 1


def fail():
    raise ValueError("no")


class Guard:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@contextlib.contextmanager
def opened():
    yield 1
