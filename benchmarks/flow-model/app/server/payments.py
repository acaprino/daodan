import uuid

from . import billing, db, gateway
from .http import route

CARTS: dict[str, list[str]] = {}


def charge_order(order_id: str) -> dict:
    attempt = uuid.uuid4().hex
    status = gateway.charge(billing.amount_for(CARTS.get(order_id, [])), attempt)
    db.put("payments", attempt, {"order": order_id, "status": status})
    return {"orderId": order_id, "status": status}


@route("POST", "/payments")
def create_payment(body: dict) -> dict:
    return charge_order(body["orderId"])
