"""Client of the external card-payment provider."""
import json
import urllib.request

GATEWAY_URL = "https://payments.provider.example/v1/charges"


def charge(amount_cents: int, reference: str) -> str:
    request = urllib.request.Request(
        GATEWAY_URL,
        data=json.dumps({"amount": amount_cents, "reference": reference}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)["status"]
