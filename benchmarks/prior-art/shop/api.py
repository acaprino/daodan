"""Ingresso HTTP: riceve JSON non fidato e chiama il dominio."""
from . import orders, returns


def post_order(body):
    for line in body["lines"]:
        if not isinstance(line.get("qty"), int):
            return 400, "qty deve essere un intero"
        if line["qty"] < 1 or line["qty"] > 20:
            return 400, "quantità non ammessa"
    try:
        return 201, orders.place(body["id"], body["customer_id"], body["lines"])
    except (KeyError, ValueError) as exc:
        return 400, str(exc)


def delete_order(order_id):
    try:
        orders.cancel(order_id)
    except (KeyError, ValueError) as exc:
        return 400, str(exc)
    return 204, None


def post_return(body):
    try:
        if body["kind"] == "void":
            returns.void(body["order_id"])
            return 204, None
        return 200, returns.refund(body["order_id"], body["skus"])
    except (KeyError, ValueError) as exc:
        return 400, str(exc)
