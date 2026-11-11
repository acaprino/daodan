from . import db


def receipt_lines(order_id: str) -> list[str]:
    captured = [doc for doc in db.find("payments", order=order_id) if doc["status"] == "captured"]
    return [f"{order_id}: pagamento confermato"] if captured else []
