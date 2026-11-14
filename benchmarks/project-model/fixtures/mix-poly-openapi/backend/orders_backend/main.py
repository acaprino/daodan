from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Orders API", version="1.2.0")


class NewOrder(BaseModel):
    total: float


class Order(NewOrder):
    id: str


ORDERS: list[Order] = []


@app.get("/orders", operation_id="listOrders", response_model=list[Order])
def list_orders() -> list[Order]:
    return ORDERS


@app.post("/orders", operation_id="createOrder", response_model=Order, status_code=201)
def create_order(order: NewOrder) -> Order:
    created = Order(id=str(uuid4()), total=order.total)
    ORDERS.append(created)
    return created
