"""Overloads: a call ends on the definition that runs; on the stub only when no other definition exists."""
import typing
from typing import Protocol, overload
from typing import overload as variant


@overload
def convert(value: int) -> str: ...


@overload
def convert(value: str) -> int: ...


def convert(value):
    return value


@variant
def scale(value: int) -> int: ...


@variant
def scale(value: float) -> float: ...


def scale(value):
    return value


class Codec:
    @typing.overload
    def encode(self, value: int) -> str: ...

    @typing.overload
    def encode(self, value: str) -> int: ...

    def encode(self, value):
        return value


class Reader(Protocol):
    @overload
    def read(self, size: int) -> bytes: ...

    @overload
    def read(self, size: None) -> str: ...


def use(codec: Codec, reader: Reader):
    return convert(1), scale(2), codec.encode(3), reader.read(4)
