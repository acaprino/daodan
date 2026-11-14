CREATE OR REPLACE PACKAGE orders_pkg AUTHID DEFINER AS
  FUNCTION next_order_id RETURN NUMBER;
END orders_pkg;
/

CREATE OR REPLACE PACKAGE BODY orders_pkg AS
  FUNCTION next_order_id RETURN NUMBER IS
  BEGIN
    RETURN orders_seq.nextval;
  END next_order_id;
END orders_pkg;
/
