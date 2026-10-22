"""Oracle PL/SQL and PostgreSQL corpus for the grammar-parity harness.

Every file here is hand-written to contain constructs a Code Graph has to see:
declarations, calls inside bodies, keyword/identifier collisions, and
dialect-specific SQL. Nothing in this corpus was taken from a real project,
because neither of the two projects this harness was first measured against
contains any Oracle or PostgreSQL code at all. That absence is itself recorded
in RESULTS.md and it bounds every conclusion drawn from these files.

Corpus history: the first version of 01_pkg_spec carried
`PROCEDURE ... DETERMINISTIC`, which is not valid Oracle (DETERMINISTIC applies
to functions only). The grammar rejected it and the rejection was correct. The
invalid form is preserved as an explicit negative control in
isolate_constructs.py, case N1, so the mistake cannot be repeated silently.
"""
from __future__ import annotations

FILES: dict[str, str] = {}

# ---------------------------------------------------------------- Oracle PL/SQL

FILES["01_pkg_spec.pks"] = r'''
CREATE OR REPLACE PACKAGE order_mgmt AUTHID DEFINER AS
  gc_max_retries CONSTANT PLS_INTEGER := 3;
  SUBTYPE t_amount IS NUMBER(18,2);
  TYPE t_order_rec IS RECORD (
    order_id   orders.order_id%TYPE,
    customer   customers.name%TYPE,
    total      t_amount
  );
  TYPE t_order_tab IS TABLE OF t_order_rec INDEX BY PLS_INTEGER;
  CURSOR c_open_orders (p_status VARCHAR2) IS
    SELECT order_id, total FROM orders WHERE status = p_status;
  e_payment_failed EXCEPTION;
  PRAGMA EXCEPTION_INIT(e_payment_failed, -20001);

  FUNCTION get_order_total (p_order_id IN orders.order_id%TYPE) RETURN t_amount;
  PROCEDURE close_order (p_order_id IN orders.order_id%TYPE, p_reason IN VARCHAR2);
  FUNCTION purge_old_orders (p_cutoff IN DATE) RETURN NUMBER DETERMINISTIC;
END order_mgmt;
/
'''

# The call-edge file. Every cross-unit call in here is enumerated in RESULTS.md
# so that recall can be checked by hand rather than assumed from a node count.
FILES["02_pkg_body.pkb"] = r'''
CREATE OR REPLACE PACKAGE BODY order_mgmt AS

  FUNCTION get_order_total (p_order_id IN orders.order_id%TYPE) RETURN t_amount IS
    l_total t_amount;
  BEGIN
    SELECT NVL(SUM(total), 0) INTO l_total
      FROM order_lines ol
      JOIN orders o ON o.order_id = ol.order_id
     WHERE o.order_id = p_order_id
       AND o.status <> 'CANCELLED';
    RETURN l_total;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      RETURN 0;
    WHEN OTHERS THEN
      logging_pkg.log_error('get_order_total', SQLERRM);
      RAISE;
  END get_order_total;

  PROCEDURE close_order (p_order_id IN orders.order_id%TYPE, p_reason IN VARCHAR2) IS
    l_total t_amount;
    l_user  VARCHAR2(64) := audit_ctx.current_user();
    PRAGMA AUTONOMOUS_TRANSACTION;
  BEGIN
    l_total := get_order_total(p_order_id);
    payment_gateway.settle(p_order_id, l_total);
    UPDATE orders
       SET status = 'CLOSED', closed_by = l_user, close_reason = p_reason
     WHERE order_id = p_order_id;
    IF SQL%ROWCOUNT = 0 THEN
      RAISE_APPLICATION_ERROR(-20002, 'order not found: ' || p_order_id);
    END IF;
    audit_pkg.write_entry('CLOSE', p_order_id, l_total);
    COMMIT;
  EXCEPTION
    WHEN e_payment_failed THEN
      ROLLBACK;
      notify_service.alert_payment_failure(p_order_id, l_total);
      RAISE;
  END close_order;

  PROCEDURE purge_old_orders (p_cutoff IN DATE) IS
    TYPE t_ids IS TABLE OF orders.order_id%TYPE;
    l_ids t_ids;
    CURSOR c_old IS SELECT order_id FROM orders WHERE created_at < p_cutoff;
  BEGIN
    OPEN c_old;
    LOOP
      FETCH c_old BULK COLLECT INTO l_ids LIMIT 500;
      EXIT WHEN l_ids.COUNT = 0;
      FORALL i IN 1 .. l_ids.COUNT
        DELETE FROM order_lines WHERE order_id = l_ids(i);
      FORALL i IN 1 .. l_ids.COUNT
        DELETE FROM orders WHERE order_id = l_ids(i);
      COMMIT;
    END LOOP;
    CLOSE c_old;
    FOR rec IN (SELECT order_id, total FROM orders WHERE created_at < p_cutoff) LOOP
      archive_pkg.archive_order(rec.order_id, rec.total);
    END LOOP;
    EXECUTE IMMEDIATE 'BEGIN stats_pkg.refresh(:1); END;' USING p_cutoff;
  END purge_old_orders;

BEGIN
  logging_pkg.init('order_mgmt');
END order_mgmt;
/
'''

FILES["03_object_type.sql"] = r'''
CREATE OR REPLACE TYPE address_t AS OBJECT (
  street VARCHAR2(200),
  city   VARCHAR2(100),
  MEMBER FUNCTION format_address (p_upper IN BOOLEAN DEFAULT FALSE) RETURN VARCHAR2,
  MEMBER PROCEDURE normalize,
  CONSTRUCTOR FUNCTION address_t (p_city IN VARCHAR2) RETURN SELF AS RESULT,
  OVERRIDING MEMBER FUNCTION to_string RETURN VARCHAR2,
  MAP MEMBER FUNCTION sort_key RETURN VARCHAR2
) NOT FINAL;
/
CREATE OR REPLACE TYPE BODY address_t AS
  MEMBER FUNCTION format_address (p_upper IN BOOLEAN DEFAULT FALSE) RETURN VARCHAR2 IS
  BEGIN
    IF p_upper THEN
      RETURN UPPER(TRIM(street || ' ' || city));
    END IF;
    RETURN TRIM(street || ' ' || city);
  END;
  MEMBER PROCEDURE normalize IS
  BEGIN
    SELF.street := TRIM(street);
  END;
  CONSTRUCTOR FUNCTION address_t (p_city IN VARCHAR2) RETURN SELF AS RESULT IS
  BEGIN
    SELF.city := p_city;
    RETURN;
  END;
  OVERRIDING MEMBER FUNCTION to_string RETURN VARCHAR2 IS
  BEGIN
    RETURN SELF.format_address(TRUE);
  END;
  MAP MEMBER FUNCTION sort_key RETURN VARCHAR2 IS
  BEGIN
    RETURN city || street;
  END;
END;
/
'''

# Oracle keywords are not reserved, so all of these are legal identifiers. A
# grammar without an external scanner splits them (LOOP + Contacts).
FILES["04_keyword_traps.sql"] = r'''
CREATE OR REPLACE PROCEDURE proc_traps AS
  LoopContacts PLS_INTEGER := 0;
  newPeriod    DATE := SYSDATE;
  ordernr      NUMBER;
  outer        VARCHAR2(10);
  level_id     PLS_INTEGER;
BEGIN
  SELECT COUNT(*) INTO LoopContacts FROM contacts;
  FOR outer IN (SELECT id, level_id, "comment" FROM t_hierarchy
                 START WITH parent_id IS NULL
               CONNECT BY PRIOR id = parent_id) LOOP
    ordernr := outer.id;
    newPeriod := ADD_MONTHS(newPeriod, 1);
  END LOOP;
END;
/
CREATE VIEW v_traps AS
SELECT o.order_id, o."number", o."date", o."level"
  FROM orders o, order_lines ol
 WHERE o.order_id = ol.order_id(+)
   AND o.status IN ('NEW','PAID');
'''

FILES["05_oracle_sql.sql"] = r'''
MERGE INTO target_orders t
USING (SELECT order_id, SUM(total) AS tot FROM order_lines GROUP BY order_id) s
   ON (t.order_id = s.order_id)
 WHEN MATCHED THEN UPDATE SET t.total = s.tot DELETE WHERE t.total IS NULL
 WHEN NOT MATCHED THEN INSERT (order_id, total) VALUES (s.order_id, s.tot);

SELECT e.employee_id, e.last_name, LEVEL AS depth,
       SYS_CONNECT_BY_PATH(e.last_name, '/') AS chain,
       CONNECT_BY_ROOT e.last_name AS root_name,
       SUM(e.salary) OVER (PARTITION BY e.department_id ORDER BY e.hire_date) AS running
  FROM employees e
 START WITH e.manager_id IS NULL
CONNECT BY NOCYCLE PRIOR e.employee_id = e.manager_id
 ORDER SIBLINGS BY e.last_name;

WITH dept_tree (dept_id, parent_id, lvl) AS (
  SELECT dept_id, parent_id, 1 FROM departments WHERE parent_id IS NULL
  UNION ALL
  SELECT d.dept_id, d.parent_id, t.lvl + 1
    FROM departments d JOIN dept_tree t ON d.parent_id = t.dept_id
) SEARCH DEPTH FIRST BY dept_id SET seq CYCLE dept_id SET is_cycle TO 'Y' DEFAULT 'N'
SELECT * FROM dept_tree;

SELECT j.order_id, jt.line_no, jt.qty
  FROM orders j, JSON_TABLE(j.payload, '$.lines[*]'
        COLUMNS (line_no NUMBER PATH '$.no', qty NUMBER PATH '$.qty')) jt
 WHERE j.order_id = 1;

SELECT q'[it's here]' AS s, seq_orders.NEXTVAL AS n FROM dual;
'''

FILES["06_trigger.sql"] = r'''
CREATE OR REPLACE TRIGGER trg_orders_biu
  BEFORE INSERT OR UPDATE ON orders
  REFERENCING NEW AS NEW OLD AS OLD
  FOR EACH ROW
  WHEN (NEW.status = 'PAID')
DECLARE
  l_prev orders.total%TYPE;
BEGIN
  IF UPDATING THEN
    l_prev := :OLD.total;
    audit_pkg.log_change(:NEW.order_id, l_prev, :NEW.total);
  END IF;
  :NEW.updated_at := SYSTIMESTAMP;
  :NEW.updated_by := SYS_CONTEXT('USERENV','SESSION_USER');
END;
/
'''

# The README declares Oracle-wrapped bodies a deliberate gap. Pinned so that a
# fix is noticed rather than silently changing what we claim.
FILES["07_wrapped_body.sql"] = r'''
CREATE OR REPLACE PACKAGE BODY secret_pkg WRAPPED AS
aaabcd
aaabc
aaabb
ABCD
abcd
xyz
/
'''

# Escaped quotes inside a quoted identifier. The generic SQL grammar fails on
# this; the Oracle grammar does not; our regex adapter returns a mangled name.
FILES["10_quoted_identifiers.sql"] = r'''
CREATE TABLE "sales data"."order""items" (id INT, name TEXT);
CREATE TABLE "CREATE VIEW ghost AS SELECT 1" (id INT);
SELECT "weird col" FROM "Mixed Case Table" t WHERE t."a""b" = 1;
'''

# ------------------------------------------------------------------ PostgreSQL

# Neither available grammar handles a real PL/pgSQL body. This file is the
# declared gap, pinned by case G8.
FILES["08_pg_plpgsql.sql"] = r'''
CREATE OR REPLACE FUNCTION calc_order_total(p_order_id BIGINT)
RETURNS NUMERIC
LANGUAGE plpgsql
AS $$
DECLARE
  l_total NUMERIC;
  l_rec   orders%ROWTYPE;
BEGIN
  SELECT COALESCE(SUM(total), 0) INTO l_total FROM order_lines WHERE order_id = p_order_id;
  SELECT * INTO l_rec FROM orders WHERE order_id = p_order_id;
  IF l_rec.status = 'CANCELLED' THEN
    RAISE EXCEPTION 'order % is cancelled', p_order_id USING ERRCODE = '22023';
  END IF;
  PERFORM audit_write('CALC', p_order_id, l_total);
  RETURN l_total;
EXCEPTION
  WHEN no_data_found THEN
    RETURN 0;
END;
$$;

CREATE OR REPLACE PROCEDURE purge_old(p_cutoff TIMESTAMPTZ)
LANGUAGE plpgsql AS $$
DECLARE r RECORD;
BEGIN
  FOR r IN SELECT order_id FROM orders WHERE created_at < p_cutoff LOOP
    PERFORM archive_order(r.order_id);
  END LOOP;
END;
$$;

DO $$ BEGIN PERFORM 1; END $$;
'''

# Nested block comments are legal in PostgreSQL and not in standard SQL, so
# this file separates "the grammar is SQL-generic" from "the grammar is Oracle".
FILES["09_pg_sql.sql"] = r'''
/* outer /* nested */ still a comment */
CREATE TABLE IF NOT EXISTS orders (
  order_id BIGSERIAL PRIMARY KEY,
  payload  JSONB NOT NULL DEFAULT '{}'::jsonb,
  tags     TEXT[] DEFAULT ARRAY[]::TEXT[],
  created  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_orders_payload ON orders USING GIN (payload jsonb_path_ops);
ALTER TABLE orders ADD CONSTRAINT chk_total CHECK ((payload->>'total')::numeric >= 0);
WITH RECURSIVE tree AS (
  SELECT id, parent_id, 1 AS lvl FROM nodes WHERE parent_id IS NULL
  UNION ALL
  SELECT n.id, n.parent_id, t.lvl + 1 FROM nodes n JOIN tree t ON n.id = t.parent_id
) SELECT * FROM tree;
SELECT o.order_id,
       o.payload->'lines'->0->>'qty' AS first_qty,
       o.payload #>> '{customer,name}' AS cust,
       jsonb_array_elements(o.payload->'lines') AS line
  FROM orders o
 WHERE o.payload @> '{"status":"PAID"}' AND 'vip' = ANY(o.tags);
CREATE OR REPLACE VIEW v_paid AS SELECT * FROM orders WHERE (payload->>'status') = 'PAID';
SELECT $$dollar body$$ AS lit, $tag$tagged$tag$ AS lit2;
'''

ORACLE_FILES = [k for k in FILES if not k.startswith(("08_", "09_"))]
POSTGRES_FILES = [k for k in FILES if k.startswith(("08_", "09_"))]

# The cross-unit calls a reader can verify by hand in 02_pkg_body.pkb. Used by
# case G1 to check recall against a hand-counted ground truth instead of
# trusting whatever node count the parser happened to emit.
EXPECTED_CALLS_IN_PACKAGE_BODY = [
    "logging_pkg.log_error",
    "audit_ctx.current_user",
    "get_order_total",
    "payment_gateway.settle",
    "audit_pkg.write_entry",
    "notify_service.alert_payment_failure",
    "archive_pkg.archive_order",
    "logging_pkg.init",
]

# Measured false positives: a collection subscript is emitted as ref_call.
EXPECTED_FALSE_CALLS_IN_PACKAGE_BODY = ["l_ids(i)"]
