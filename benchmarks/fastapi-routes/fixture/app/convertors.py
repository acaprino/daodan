from starlette.convertors import Convertor, register_url_convertor


class SlugConvertor(Convertor):
    regex = "[a-z0-9-]+"

    def convert(self, value: str) -> str:
        return value

    def to_string(self, value: str) -> str:
        return value


class PairConvertor(Convertor):
    regex = "[a-z]+/[a-z]+"  # a `/` inside: the value is two segments

    def convert(self, value: str) -> str:
        return value

    def to_string(self, value: str) -> str:
        return value


register_url_convertor("slug", SlugConvertor())
register_url_convertor("pair", PairConvertor())
