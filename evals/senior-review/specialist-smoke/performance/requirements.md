# Storage access requirements

Both functions return every order's ID and its customer's name. An order always
has a valid customer. A page can contain 1,000 orders. Each db.query call executes
one SQL query over the network with no implicit cache, eager loading or batching.
The requirement is at most two database round trips per page. These functions
are the complete access paths. Existing indexes support both queries; timing and
query plans are not supplied. Static review only, no runtime probe authorized.
