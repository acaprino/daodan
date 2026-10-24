def page_a(db):
    orders = db.query("SELECT id, customer_id FROM orders LIMIT 1000")
    return [
        (order.id, db.query("SELECT name FROM customers WHERE id = ?", order.customer_id)[0].name)
        for order in orders
    ]


def page_b(db):
    rows = db.query("SELECT orders.id, customers.name FROM orders JOIN customers ON customers.id = orders.customer_id LIMIT 1000")
    return [(row.id, row.name) for row in rows]
