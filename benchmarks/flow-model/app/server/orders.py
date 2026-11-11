from . import db
from .http import route


def is_paid(order_id: str) -> bool:
    document = db.get("payments", order_id)
    return document is not None and document["status"] == "captured"


@route("GET", "/orders")
def list_orders(body: dict) -> list[dict]:
    return [{"id": order_id, "paid": is_paid(order_id)} for order_id in sorted(body.get("ids", []))]
