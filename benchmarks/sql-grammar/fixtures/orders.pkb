CREATE OR REPLACE PACKAGE BODY orders_api AS

  -- the fee on an amount
  FUNCTION fee(p_amount NUMBER) RETURN NUMBER IS
  BEGIN
    RETURN p_amount * 0.02;
  END fee;

  PROCEDURE add_item(p_order IN NUMBER, p_sku IN VARCHAR2) IS
    l_sql VARCHAR2(400);
  BEGIN
    l_sql := q'[INSERT INTO order_items (order_id, sku) VALUES (:1, :2)]';
    EXECUTE IMMEDIATE l_sql USING p_order, p_sku;
    EXECUTE IMMEDIATE 'CREATE TABLE tmp_audit (id NUMBER)';
  EXCEPTION
    WHEN OTHERS THEN
      RAISE e_closed;
  END add_item;

  FUNCTION total(p_order IN NUMBER) RETURN NUMBER IS
    l_total NUMBER;
  BEGIN
    SELECT SUM(price) INTO l_total FROM order_items WHERE order_id = p_order;
    RETURN l_total + fee(l_total);
  END total;

END orders_api;
/
