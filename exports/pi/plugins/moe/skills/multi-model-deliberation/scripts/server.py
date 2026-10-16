# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp>=2.0.0,<3"]
# ///
"""MoE transport MCP. The workflow owns deliberation; the host owns execution.

No automatic retry, key disclosure, provider selection or background goal loop.
Tri-Tech binds this server to its native context broker instead of direct HTTP.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import time
import urllib.error
import urllib.parse
import urllib.request

from mcp.server.mcpserver import MCPServer
from moe_payload import read_payload

mcp = MCPServer("moe")
MAX_PAYLOAD_BYTES = 24_000
MAX_BRIEF_BYTES = 6_000
MAX_REPLY_BYTES = 8_000
MAX_FRAMING_BYTES = 2_000
assert MAX_BRIEF_BYTES + 2 * MAX_REPLY_BYTES + MAX_FRAMING_BYTES <= MAX_PAYLOAD_BYTES
MAX_RESPONSE_BYTES = 1_000_000


def _connection():
    bridge = os.environ.get("MOE_BRIDGE_URL")
    base = bridge if bridge is not None else os.environ.get("MOE_API_BASE", "")
    key = os.environ.get("MOE_BRIDGE_TOKEN", "") if bridge is not None else os.environ.get("MOE_API_KEY", "")
    url = urllib.parse.urlsplit(base)
    if (url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query or url.fragment
            or any(part in (".", "..") for part in url.path.split("/"))):
        raise ValueError("Configure a valid MoE endpoint without URL credentials")
    if bridge is not None and (url.scheme != "http" or url.hostname != "127.0.0.1" or url.path not in ("", "/")):
        raise ValueError("Tri-Tech MoE requires its private loopback broker; direct fallback is forbidden")
    if not key:
        raise ValueError("MoE authentication is not configured")
    base = base.rstrip("/")
    return base if base.endswith("/v1") else base + "/v1", key


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _call(path, body=None, binding=""):
    base, key = _connection()
    headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
    if binding:
        headers["X-Moe-Binding"] = binding
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    request = urllib.request.Request(base + path, data=data, headers=headers, method="POST" if data else "GET")
    # The broker is private local traffic and must not honor a configured system proxy.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    with opener.open(request, timeout=600) as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("MoE response exceeds its transport bound")
        return json.loads(raw)


def _payload(content_path):
    cwd = Path.cwd().resolve(strict=True)
    relative = Path(os.environ.get("MOE_RUN_ROOT", ".moe"))
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("MoE run root must stay inside the active project")
    root = cwd / relative
    path = Path(content_path)
    if not path.is_absolute():
        path = cwd / path
    if ".." in path.parts or root not in path.parents:
        raise ValueError("MoE payload must be in its project run directory")
    current = cwd
    for part in path.relative_to(cwd).parts:
        current = current / part
        metadata = current.lstat()
        if (stat.S_ISLNK(metadata.st_mode) or getattr(metadata, "st_file_attributes", 0) & 0x400
                or stat.S_ISREG(metadata.st_mode) and metadata.st_nlink != 1):
            raise ValueError("MoE payload contains a linked component")
    if root.resolve(strict=True) not in path.resolve(strict=True).parents or not path.is_file():
        raise ValueError("MoE payload escaped its run root")
    raw = read_payload(cwd, path, MAX_PAYLOAD_BYTES)
    if not raw.strip() or len(raw) > MAX_PAYLOAD_BYTES:
        raise ValueError("MoE payload is empty or exceeds 24000 bytes")
    return path, raw, raw.decode("utf-8")


@mcp.tool()
def moe_models() -> dict:
    """List actual configured model IDs and endpoint, never credentials. No generation."""
    try:
        base, _ = _connection()
        data = _call("/models")
        models = [{"id": item["id"]} for item in data.get("data", [])
                  if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"]]
        return {"models": models, "endpoint": base, "run_root": os.environ.get("MOE_RUN_ROOT", ".moe"),
                "transport": "tritech-native-context" if "MOE_BRIDGE_URL" in os.environ else "openai-compatible",
                "limits": {"brief_bytes": MAX_BRIEF_BYTES, "reply_bytes": MAX_REPLY_BYTES, "framing_bytes": MAX_FRAMING_BYTES, "payload_bytes": MAX_PAYLOAD_BYTES}}
    except (OSError, ValueError, KeyError, TypeError):
        return {"error": "MoE model discovery failed; verify endpoint, authentication and host binding"}


class MoeRequestError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _identity(value):
    return (isinstance(value, str) and bool(value) and value == value.strip()
            and len(value.encode("utf-8")) <= 200 and not any(ord(char) < 32 for char in value))


@mcp.tool()
def moe_ask(model: str, system: str, content_path: str, max_output_tokens: int = 4096, binding: str = "",
            phase: str = "proposal", peer_model: str | None = None, expected_model: str | None = None) -> dict:
    """Send one bounded original payload to a model. No retry, routing or deliberation.

    binding is an opaque host-injected capability. Never invent one or copy it to
    reports. Proposals reserve space for two replies. For the second proposal set
    peer_model to the first reply's returned model. Critiques require both the
    other participant's returned peer_model and this participant's expected_model.
    The returned sent digest describes exactly the UTF-8 user message.
    """
    started = time.monotonic()
    try:
        if (not isinstance(model, str) or not model.strip() or len(model) > 200
                or not isinstance(system, str) or not system.strip() or len(system.encode("utf-8")) > 4096
                or isinstance(max_output_tokens, bool) or not isinstance(max_output_tokens, int)
                or not 1 <= max_output_tokens <= 4096
                or not isinstance(binding, str) or len(binding) > 200):
            raise ValueError("Invalid MoE model, system instruction, output limit or binding")
        if (phase not in ("proposal", "critique") or peer_model is not None and not _identity(peer_model)
                or expected_model is not None and not _identity(expected_model)
                or phase == "critique" and (peer_model is None or expected_model is None)):
            raise MoeRequestError("identity_contract", "Critiques require two distinct returned model identities")
        if peer_model is not None and expected_model is not None and peer_model.casefold() == expected_model.casefold():
            raise MoeRequestError("model_collision", "Both participants resolved to the same model")
        path, raw, text = _payload(content_path)
        if phase == "proposal" and len(raw) > MAX_BRIEF_BYTES:
            raise MoeRequestError("brief_bound", "Reduce the brief to 6000 UTF-8 bytes before spending; space is reserved for two complete replies")
        data = _call("/chat/completions", {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": text}],
                     "stream": False, "max_tokens": max_output_tokens}, binding)
        if not isinstance(data, dict):
            raise ValueError("Invalid completion response")
        actual = data.get("model")
        if not _identity(actual):
            raise MoeRequestError("model_identity_missing", "The endpoint did not identify the actual model; no independence claim is possible")
        if peer_model is not None and actual.casefold() == peer_model.casefold():
            raise MoeRequestError("model_collision", "Both participants resolved to the same model; stop this exchange")
        if expected_model is not None and actual != expected_model:
            raise MoeRequestError("model_changed", "The participant changed its actual model; stop this exchange")
        choice = data["choices"][0]
        message = choice["message"]
        reply = message.get("content")
        if (message.get("role") != "assistant" or message.get("tool_calls") or not isinstance(reply, str) or not reply.strip()
                or len(reply.encode("utf-8")) > MAX_REPLY_BYTES or choice.get("finish_reason") not in ("stop", "unknown")):
            raise ValueError("Model returned an empty, incomplete or unsupported reply")
        return {"text": reply, "model": actual, "usage": data.get("usage"), "finish_reason": choice.get("finish_reason"),
                "latency_ms": round((time.monotonic() - started) * 1000), "sent_path": str(path), "sent_bytes": len(raw), "sent_sha256": hashlib.sha256(raw).hexdigest()}
    except MoeRequestError as error:
        return {"error": str(error), "code": error.code}
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        # Do not echo headers, request bodies, token values or upstream HTML errors.
        return {"error": "MoE request failed or delivery was incomplete. No retry was made; a sent request may have been charged."}


if __name__ == "__main__":
    mcp.run()
