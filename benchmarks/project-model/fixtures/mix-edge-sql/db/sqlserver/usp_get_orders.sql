CREATE PROCEDURE [dbo].[usp_get_orders]
    @CustomerId BIGINT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT id, total_cents FROM dbo.orders WHERE customer_id = @CustomerId;
END
GO
