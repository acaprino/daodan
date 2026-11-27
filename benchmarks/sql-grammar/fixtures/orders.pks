-- Order API. The words in this comment ("CREATE TABLE ghost") are not an object.
/* a block comment with CREATE TABLE ghost_block (id NUMBER);
   over two lines */
CREATE OR REPLACE PACKAGE orders_api AS
  c_max_items CONSTANT PLS_INTEGER := 100;
  e_closed EXCEPTION;
  CURSOR c_open (p_customer NUMBER) IS SELECT id FROM orders WHERE customer_id = p_customer;
  PROCEDURE add_item(p_order IN NUMBER, p_sku IN VARCHAR2);
  FUNCTION total(p_order IN NUMBER) RETURN NUMBER;
END orders_api;
/
