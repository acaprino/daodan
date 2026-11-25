class FourDigits:
    regex = "[0-9]{4}"

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return "%04d" % value


class Pair:
    regex = "[^/]+/[^/]+"

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
