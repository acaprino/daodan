from . import db, payments
from .scheduler import scheduled


@scheduled("*/10 * * * *")
def retry_declined() -> int:
    retried = 0
    for document in db.find("payments", status="declined"):
        payments.charge_order(document["order"])
        retried += 1
    return retried
