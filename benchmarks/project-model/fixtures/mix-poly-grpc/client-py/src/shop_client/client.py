import sys
from pathlib import Path

import grpc

sys.path.insert(0, str(Path(__file__).parent / "gen"))

from shop.v1 import order_pb2, order_pb2_grpc  # noqa: E402


def get_order(order_id: str, target: str = "localhost:50051") -> int:
    with grpc.insecure_channel(target) as channel:
        stub = order_pb2_grpc.OrderServiceStub(channel)
        return stub.GetOrder(order_pb2.GetOrderRequest(id=order_id)).total_cents
