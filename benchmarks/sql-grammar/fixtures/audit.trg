CREATE OR REPLACE TRIGGER trg_orders_bi
BEFORE INSERT ON orders
FOR EACH ROW
BEGIN
  :new.created_at := SYSDATE;
  IF :new.status IS NULL THEN
    :new.status := 'OPEN';
  END IF;
END trg_orders_bi;
/

CREATE OR REPLACE TRIGGER trg_orders_audit
FOR UPDATE ON orders
COMPOUND TRIGGER
  TYPE t_ids IS TABLE OF orders.id%TYPE;
  g_ids t_ids := t_ids();
  AFTER EACH ROW IS
  BEGIN
    g_ids.EXTEND;
    g_ids(g_ids.COUNT) := :new.id;
  END AFTER EACH ROW;
  AFTER STATEMENT IS
  BEGIN
    NULL;
  END AFTER STATEMENT;
END trg_orders_audit;
/
