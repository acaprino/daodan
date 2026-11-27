CREATE TABLE "Order Items" (
  "order id" INTEGER NOT NULL,
  "sku" VARCHAR(40) -- a trailing comment with CREATE VIEW ghost_view AS SELECT 1;
);
CREATE TABLE sales."Region.Totals" (region TEXT, total NUMERIC);
CREATE VIEW v_open AS SELECT * FROM "Order Items" WHERE 'create table fake_string (x int)' IS NOT NULL;
CREATE FUNCTION add_one(a integer) RETURNS integer AS $$
  BEGIN
    RETURN a + 1; -- CREATE TABLE ghost_in_body (x int)
  END;
$$ LANGUAGE plpgsql;
CREATE FUNCTION tag_it(a text) RETURNS text AS $body$ SELECT 'x' $body$ LANGUAGE sql;
