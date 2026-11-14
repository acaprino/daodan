from unittest.mock import patch

from fx.shapes import Shape, area as shape_area


def show(s: Shape):
    return s.describe()


def build(items):
    first = Shape.make(len(items))
    text = Shape.describe(first)
    patched = patch("fx.shapes.area")
    size = shape_area(first)
    return first, text, patched, size


def apply(action):
    return action.perform()
