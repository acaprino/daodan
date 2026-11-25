from fastapi import APIRouter

router = APIRouter(prefix="/orders")


@router.get("/")
def list_orders():
    return []


@router.post("/{order_id}/ship")
async def ship_order(order_id: int):
    return {"shipped": order_id}
