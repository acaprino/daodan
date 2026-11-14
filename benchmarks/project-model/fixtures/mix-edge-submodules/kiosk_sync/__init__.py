import httpx
import proto_py


def push(order: dict) -> int:
    payload = proto_py.encode_order(order)
    return httpx.post("https://kiosk.example/api/orders", content=payload).status_code
