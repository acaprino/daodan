CREATE SEQUENCE seq_customer START WITH 1;
CREATE TABLE customers (
  id INTEGER PRIMARY KEY,
  name VARCHAR(100) NOT NULL
);
CREATE UNIQUE INDEX ix_customers_name ON customers (name);
CREATE OR REPLACE VIEW v_customers AS
  SELECT id, name FROM customers;
CREATE MATERIALIZED VIEW mv_totals AS SELECT count(*) AS n FROM customers;
CREATE OR REPLACE PROCEDURE touch(p_id IN NUMBER) IS
BEGIN
  UPDATE customers SET name = name WHERE id = p_id;
END;
/
CREATE OR REPLACE FUNCTION customer_name RETURN VARCHAR2 IS BEGIN RETURN 'x'; END;
/
