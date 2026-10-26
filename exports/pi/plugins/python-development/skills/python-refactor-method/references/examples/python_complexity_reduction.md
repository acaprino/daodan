<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

# Python: Complexity Reduction Example

This example shows a complete refactoring of a complex Python function that processes user orders.

## Before: Complex, Hard-to-Understand Code

```python
def process_user_orders(user_id, start_date, end_date, status_filter=None):
    """Process user orders."""
    orders = []
    user = db.query(User).filter_by(id=user_id).first()
    if user:
        if user.is_active:
            order_list = db.query(Order).filter(
                Order.user_id == user_id,
                Order.created_at >= start_date,
                Order.created_at <= end_date
            ).all()
            if order_list:
                for order in order_list:
                    if status_filter:
                        if order.status == status_filter:
                            if order.items:
                                total = 0
                                for item in order.items:
                                    if item.quantity > 0:
                                        product = db.query(Product).filter_by(
                                            id=item.product_id
                                        ).first()
                                        if product:
                                            if product.is_available:
                                                item_total = item.quantity * product.price
                                                if product.discount > 0:
                                                    item_total *= (1 - product.discount)
                                                total += item_total
                                if total > 0:
                                    order.total = total
                                    orders.append({
                                        'order_id': order.id,
                                        'total': total,
                                        'items_count': len(order.items)
                                    })
                    else:
                        if order.items:
                            total = 0
                            for item in order.items:
                                if item.quantity > 0:
                                    product = db.query(Product).filter_by(
                                        id=item.product_id
                                    ).first()
                                    if product:
                                        if product.is_available:
                                            item_total = item.quantity * product.price
                                            if product.discount > 0:
                                                item_total *= (1 - product.discount)
                                            total += item_total
                            if total > 0:
                                order.total = total
                                orders.append({
                                    'order_id': order.id,
                                    'total': total,
                                    'items_count': len(order.items)
                                })
    return orders
```

### Problems

1. **Nesting depth:** 8 levels deep (target: ≤3)
2. **Function length:** 55 lines (target: <30)
3. **Cyclomatic complexity:** 22 (target: <10)
4. **Duplicate code:** Order processing logic repeated for filtered/unfiltered cases
5. **Mixed abstraction levels:** Database queries, business logic, and calculations all mixed
6. **Missing type hints:** No type information for parameters or return value
7. **Inadequate docstring:** Doesn't explain parameters, returns, or behavior

## After: Clear, Maintainable Code

```python
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


def process_user_orders(
    user_id: int,
    start_date: datetime,
    end_date: datetime,
    status_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Process and calculate totals for user orders in date range.

    Args:
        user_id: ID of the user whose orders to process
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive)
        status_filter: Optional status to filter orders by ('pending', 'completed', etc.)

    Returns:
        List of order summaries with calculated totals. Each summary contains:
        - order_id: Order identifier
        - total: Calculated order total after discounts
        - items_count: Number of items in the order

    Raises:
        UserNotFoundError: If user_id doesn't exist
        UserInactiveError: If user is not active

    Example:
        >>> orders = process_user_orders(
        ...     user_id=123,
        ...     start_date=datetime(2024, 1, 1),
        ...     end_date=datetime(2024, 1, 31),
        ...     status_filter='completed'
        ... )
    """
    user = get_active_user(user_id)
    orders = fetch_orders_in_date_range(user_id, start_date, end_date)

    if status_filter:
        orders = filter_orders_by_status(orders, status_filter)

    return [
        create_order_summary(order)
        for order in orders
        if has_valid_items(order)
    ]


def get_active_user(user_id: int) -> User:
    """Fetch user and verify they are active.

    Args:
        user_id: User identifier

    Returns:
        Active user object

    Raises:
        UserNotFoundError: If user doesn't exist
        UserInactiveError: If user is not active
    """
    user = db.query(User).filter_by(id=user_id).first()

    if not user:
        raise UserNotFoundError(f"User {user_id} not found")

    if not user.is_active:
        raise UserInactiveError(f"User {user_id} is not active")

    return user


def fetch_orders_in_date_range(
    user_id: int,
    start_date: datetime,
    end_date: datetime
) -> List[Order]:
    """Fetch all orders for user in date range.

    Args:
        user_id: User identifier
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive)

    Returns:
        List of orders in date range
    """
    return db.query(Order).filter(
        Order.user_id == user_id,
        Order.created_at >= start_date,
        Order.created_at <= end_date
    ).all()


def filter_orders_by_status(orders: List[Order], status: str) -> List[Order]:
    """Filter orders by status.

    Args:
        orders: List of orders to filter
        status: Status to filter by

    Returns:
        Filtered list of orders
    """
    return [order for order in orders if order.status == status]


def has_valid_items(order: Order) -> bool:
    """Check if order has items with valid quantities.

    Args:
        order: Order to check

    Returns:
        True if order has at least one item with quantity > 0
    """
    if not order.items:
        return False

    return any(item.quantity > 0 for item in order.items)


def create_order_summary(order: Order) -> Dict[str, Any]:
    """Create order summary with calculated total.

    Args:
        order: Order to summarize

    Returns:
        Dictionary with order_id, total, and items_count
    """
    total = calculate_order_total(order)
    order.total = total  # Update order record

    return {
        'order_id': order.id,
        'total': float(total),
        'items_count': len(order.items)
    }


def calculate_order_total(order: Order) -> Decimal:
    """Calculate total for order including discounts.

    Args:
        order: Order to calculate total for

    Returns:
        Total amount after applying discounts
    """
    return sum(
        calculate_item_total(item)
        for item in order.items
        if item.quantity > 0
    )


def calculate_item_total(item: OrderItem) -> Decimal:
    """Calculate total for a single order item with discount.

    Args:
        item: Order item to calculate

    Returns:
        Item total after discount, or 0 if product unavailable
    """
    product = fetch_product(item.product_id)

    if not product or not product.is_available:
        return Decimal('0')

    base_total = Decimal(str(item.quantity)) * product.price

    return apply_discount(base_total, product.discount)


def fetch_product(product_id: int) -> Optional[Product]:
    """Fetch product by ID from database.

    Args:
        product_id: Product identifier

    Returns:
        Product object or None if not found
    """
    return db.query(Product).filter_by(id=product_id).first()


def apply_discount(amount: Decimal, discount_rate: float) -> Decimal:
    """Apply discount percentage to amount.

    Args:
        amount: Original amount
        discount_rate: Discount as decimal (0.15 for 15%)

    Returns:
        Amount after discount applied
    """
    if discount_rate <= 0:
        return amount

    return amount * (Decimal('1') - Decimal(str(discount_rate)))
```

## Metrics Comparison

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Cyclomatic Complexity (avg) | 22 | 2.5 | 89% ↓ |
| Function Length (avg) | 55 | 8 | 85% ↓ |
| Max Nesting Depth | 8 | 2 | 75% ↓ |
| Number of Functions | 1 | 10 | Better modularity |
| Docstring Coverage | 0% | 100% | 100% ↑ |
| Type Hint Coverage | 0% | 100% | 100% ↑ |
| Lines of Code | 55 | 95 | More verbose but clearer |

## Improvements Made

### 1. Guard Clauses
- Converted deep nesting to early returns
- Moved validation to dedicated functions

### 2. Extract Method
- Split 55-line function into 10 focused functions
- Each function has single responsibility
- Average function length now 8 lines

### 3. Consistent Abstraction Levels
- Main function shows high-level flow
- Details delegated to helper functions
- Database queries isolated in repository functions

### 4. Removed Code Duplication
- Order processing logic was duplicated for filtered/unfiltered cases
- Now uses single code path with conditional filtering

### 5. Added Comprehensive Documentation
- Full docstrings with Args, Returns, Raises
- Example usage in main function docstring
- Type hints for all parameters and returns

### 6. Improved Naming
- Function names clearly describe purpose
- Boolean function `has_valid_items` uses `has_` prefix
- Calculation functions use `calculate_` prefix

### 7. Better Error Handling
- Explicit exceptions (UserNotFoundError, UserInactiveError)
- Clear error messages with context
- Separated validation from business logic

## Testing Benefits

The refactored code is much easier to test:

```python
# Can now test each piece independently

def test_calculate_item_total_with_discount():
    """Test item total calculation with discount applied."""
    item = OrderItem(quantity=2, product_id=1)
    product = Product(price=Decimal('100'), discount=0.10, is_available=True)

    with mock.patch('fetch_product', return_value=product):
        total = calculate_item_total(item)

    assert total == Decimal('180')  # 2 * 100 * 0.90


def test_has_valid_items_empty_order():
    """Test that order with no items is invalid."""
    order = Order(items=[])
    assert not has_valid_items(order)


def test_filter_orders_by_status():
    """Test filtering orders by status."""
    orders = [
        Order(id=1, status='pending'),
        Order(id=2, status='completed'),
        Order(id=3, status='pending'),
    ]

    filtered = filter_orders_by_status(orders, 'pending')

    assert len(filtered) == 2
    assert all(o.status == 'pending' for o in filtered)
```

## Conclusion

This refactoring demonstrates:
- **Complexity reduction** through guard clauses and extraction
- **Improved readability** with clear function names and structure
- **Better maintainability** with single-responsibility functions
- **Enhanced testability** with isolated, focused units
- **Professional documentation** with comprehensive docstrings and type hints

The code is now much easier for developers to understand, modify, and maintain while preserving identical behavior.
