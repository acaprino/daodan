CREATE OR REPLACE FUNCTION order_total(p_customer BIGINT)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_total BIGINT;
BEGIN
    SELECT COALESCE(SUM(total_cents), 0) INTO v_total FROM orders WHERE customer_id = p_customer;
    RETURN v_total;
END;
$$;
