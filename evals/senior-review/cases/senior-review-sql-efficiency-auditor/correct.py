# Requirement: Return all order/customer pairs; a request must use at most two database calls for up to 500 orders. Database methods below each perform one round trip; no lazy loading or cache.

def orders_view(db):
    rows = db.orders(limit=500)
    customers = db.customers_by_ids({r.customer_id for r in rows})
    return [(r.id, customers[r.customer_id].name) for r in rows]
