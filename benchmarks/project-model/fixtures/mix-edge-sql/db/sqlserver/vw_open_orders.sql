CREATE VIEW dbo.vw_open_orders
AS
SELECT TOP (100) o.id, o.total_cents, c.email
FROM dbo.orders AS o
JOIN dbo.customers AS c ON c.id = o.customer_id
WHERE o.status = N'open'
ORDER BY o.id DESC;
