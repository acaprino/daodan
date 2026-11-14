"""Functions and classes held in a name before the call: the name leads to its value, a call result never."""
from fx import shapes
from fx.shapes import Shape, area


def measure(shape):
    calc = area
    return calc(shape)


def through_the_module(shape):
    calc = shapes.area
    return calc(shape)


def make_one():
    kind = Shape
    return kind(2)


def pick(function):
    return function


def not_an_alias(shape):
    calc = pick(area)
    return calc(shape)


ALIAS = area


def at_module_level(shape):
    return ALIAS(shape)
