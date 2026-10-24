# Requirement: Return all order/customer pairs; a request must use at most two database calls for up to 500 orders. Database methods below each perform one round trip; no lazy loading or cache.

def orders_view(db):
    rows = db.orders(limit=500)
    return [(r.id, db.customer(r.customer_id).name) for r in rows]
