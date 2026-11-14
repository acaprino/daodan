class Shape:
    def __init__(self, n):
        self.n = n

    def describe(self):
        return "shape"

    @classmethod
    def make(cls, n):
        return cls(n)

    @classmethod
    def unit(cls):
        return cls.make(1)

    def clone(self):
        klass = type(self)
        return klass(self.n)


class Square(Shape):
    def describe(self):
        return "square " + super().describe()

    @classmethod
    def make(cls, n):
        return cls(n * n)


def area(shape):
    return shape.n * shape.n
