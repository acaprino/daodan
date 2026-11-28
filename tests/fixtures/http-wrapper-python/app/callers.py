# The calls of the wrappers, with the URLs a rule reads.
from app.client import Api, create, generic, load, second


def use_all():
    load("/api/users")
    create("/api/orders", {"id": 1})
    second("token", "/api/orders")
    generic("/api/orders")
    Api().fetch("/api/users")
