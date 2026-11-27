"""Runs as the preparation of a project inside Daodan's container (`container.run_in_container`), behind Daodan's proxy:
each way out the plan names (`T0.C.8`), tried once, one `ROW {...}` line each. Standard library only: the image is
`container.PROXY_IMAGE`, Python with nothing added. argv[1] is a JSON object: `mode` ("rows" or "fetch"), the canary
hosts `allowed` (approved for the run) and `outside` (never approved), `outside_ip`, `host_ip` (the VM's address),
`token` (in every name looked up, to find it on the wire), `internal` (approved names the proxy's container resolves to
an internal address, `T3.A.2` row a) and, for "fetch", `url` (exit 1 when it is not reached).

A row is `reached` when the way out answered (an answer of the proxy other than its refusal, 403 for `PROXY_SCRIPT` and
407 for Smokescreen: a 502 says it tried to connect; a TCP connection, a DNS answer, the target's HTTP answer),
`blocked` otherwise; `detail` says what came back.
"""
import json
import os
import socket
import struct
import sys
import urllib.error
import urllib.parse
import urllib.request

ARGS = json.loads(sys.argv[1])
PROXY = os.environ.get("HTTPS_PROXY", "")  # http://proxy:3128, set by `run_in_container`
TIMEOUT = 5
REFUSALS = (["403"], ["407"], [])  # the refusal of `PROXY_SCRIPT`, Smokescreen's, no status line


def row(name, kind, reached, detail):
    print("ROW " + json.dumps({"row": name, "kind": kind, "outcome": "reached" if reached else "blocked",
                               "detail": str(detail)[:300]}), flush=True)


def ask_proxy(name, request_line, timeout=TIMEOUT):
    """One request line to the proxy, raw: its status line is the proxy's answer (a refusal, 200 tunnel open)."""
    host, port = PROXY.removeprefix("http://").rsplit(":", 1)
    words = request_line.split()
    if words[0] == "GET":  # HTTP/1.1 wants its Host header: without one Smokescreen's server answers 400 first
        request_line += "\r\nHost: " + urllib.parse.urlsplit(words[1]).netloc
    try:
        with socket.create_connection((host, int(port)), timeout=timeout) as link:
            link.sendall(request_line.encode("latin-1") + b"\r\n\r\n")
            status = link.recv(4096).split(b"\r\n", 1)[0].decode("latin-1")
    except OSError as error:
        return row(name, "proxy", False, f"no answer: {error}")
    row(name, "proxy", status.split()[1:2] not in REFUSALS, status)


def connect(name, host, port, family=socket.AF_UNSPEC):
    """A TCP connection with no proxy: reached when it opens."""
    try:
        info = socket.getaddrinfo(host, port, family, socket.SOCK_STREAM)[0]
        with socket.socket(info[0], socket.SOCK_STREAM) as link:
            link.settimeout(TIMEOUT)
            link.connect(info[4])
        row(name, "direct", True, f"connected to {info[4]}")
    except OSError as error:
        row(name, "direct", False, error)


def get(name, url, proxy=True):
    """An HTTP(S) GET with urllib, following redirects as a client does: reached on any answer of the target."""
    handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY} if proxy else {})
    try:
        with urllib.request.build_opener(handler).open(url, timeout=TIMEOUT * 3) as answer:
            row(name, "http", True, f"{answer.status} {answer.geturl()}")
    except urllib.error.HTTPError as error:
        row(name, "http", True, f"{error.code} {error.geturl()}")
    except OSError as error:  # the proxy's 403 to a CONNECT is a tunnel error, not the target's answer
        row(name, "http", False, error)
        return False
    return True


def dns_query(name, server, label, tcp=False):
    """A DNS query for `label`, A record, straight to `server` port 53. dnspython is not in the image, and the
    question is the fixed 12-byte header of RFC 1035 4.1.1 and one QNAME: written here with `struct`."""
    question = b"".join(bytes([len(part)]) + part.encode("ascii") for part in label.split(".")) + b"\0"
    packet = struct.pack(">HHHHHH", 0x5151, 0x0100, 1, 0, 0, 0) + question + struct.pack(">HH", 1, 1)
    try:
        if tcp:
            with socket.create_connection((server, 53), timeout=TIMEOUT) as link:
                link.sendall(struct.pack(">H", len(packet)) + packet)
                answer = link.recv(4096)[2:]
        else:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as link:
                link.settimeout(TIMEOUT)
                link.sendto(packet, (server, 53))
                answer = link.recv(4096)
        rcode = answer[3] & 0x0F
        # REFUSED (5) or SERVFAIL (2) from a resolver that did not forward is no way out; the wire capture says if it did
        row(name, "dns", rcode not in (2, 5), f"answer rcode {rcode}")
    except OSError as error:
        row(name, "dns", False, error)


def lookup(name, host):
    try:
        row(name, "dns", True, socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)[0][4])
    except OSError as error:
        row(name, "dns", False, error)


def own_gateway():
    """The first address of this container's network: the engine's bridge on the host side."""
    mine = socket.gethostbyname(socket.gethostname())  # /etc/hosts, written by the engine
    return ".".join(mine.split(".")[:3] + ["1"])


def rows():
    allowed, outside, token = ARGS["allowed"], ARGS["outside"], ARGS["token"]
    # Positive controls: the proxy opens a canonical registry and the approved canary.
    ask_proxy("control-canonical-connect", "CONNECT registry.npmjs.org:443 HTTP/1.1")
    get("control-approved-get", f"https://{allowed}/control-approved")
    # Direct exit, without the proxy.
    get("direct-name", f"https://{outside}/direct-name", proxy=False)
    connect("direct-ip-outside", ARGS["outside_ip"], 443)
    connect("direct-ipv4-literal", "1.1.1.1", 443)
    connect("direct-ipv6-literal", "2606:4700:4700::1111", 443, socket.AF_INET6)
    # Redirects of an approved host to a host outside the list, followed by the client.
    for code in ("301", "302"):
        get(f"redirect-{code}", f"https://{allowed}/r{code}?to=https://{outside}/from-{code}")
    # DNS from the container: the engine's resolver, a public resolver over UDP and TCP 53.
    lookup("dns-lookup-outside", outside)
    lookup("dns-lookup-token", f"lookup-{token}.example.com")
    dns_query("dns-udp-embedded", "127.0.0.11", f"embedded-{token}.example.com")
    dns_query("dns-udp-public", "8.8.8.8", f"udp-{token}.example.com")
    dns_query("dns-tcp-public", "8.8.8.8", f"tcp-{token}.example.com", tcp=True)
    # The proxy refuses a name outside the list without resolving it (the wire capture has its token).
    ask_proxy("proxy-refused-unresolved", f"CONNECT refused-{token}.example.com:443 HTTP/1.1")
    ask_proxy("proxy-outside-connect", f"CONNECT {outside}:443 HTTP/1.1")
    # Literal addresses through the proxy.
    ask_proxy("proxy-ipv4-literal", "CONNECT 1.1.1.1:443 HTTP/1.1")
    ask_proxy("proxy-ipv6-literal", "CONNECT [2606:4700:4700::1111]:443 HTTP/1.1")
    # Internal addresses: cloud metadata, 10.x, the host's loopback and its addresses.
    ask_proxy("proxy-metadata-connect", "CONNECT 169.254.169.254:443 HTTP/1.1")
    ask_proxy("proxy-metadata-get", "GET http://169.254.169.254/latest/meta-data/ HTTP/1.1")
    connect("direct-metadata", "169.254.169.254", 80)
    ask_proxy("proxy-10x-connect", "CONNECT 10.0.0.1:443 HTTP/1.1")
    connect("direct-10x", "10.0.0.1", 8099)
    ask_proxy("proxy-loopback-get", "GET http://127.0.0.1:8098/proxy-loopback HTTP/1.1")
    ask_proxy("proxy-localhost-connect", "CONNECT localhost:8098 HTTP/1.1")
    ask_proxy("proxy-host-ip-connect", f"CONNECT {ARGS['host_ip']}:8099 HTTP/1.1")
    connect("direct-network-gateway", own_gateway(), 8099)
    connect("direct-docker0-gateway", "172.17.0.1", 8099)
    connect("direct-host-ip", ARGS["host_ip"], 8099)
    connect("direct-host-docker-internal", "host.docker.internal", 8099)
    # CONNECT at a port other than 443, also to an approved host; plain HTTP to a host that is not an apt archive.
    ask_proxy("proxy-connect-port-80", f"CONNECT {allowed}:80 HTTP/1.1")
    ask_proxy("proxy-connect-port-8443", f"CONNECT {allowed}:8443 HTTP/1.1")
    ask_proxy("proxy-connect-port-22", "CONNECT registry.npmjs.org:22 HTTP/1.1")
    ask_proxy("proxy-plain-http", f"GET http://{allowed}/plain-http HTTP/1.1")
    # Approved names the proxy's container resolves to an internal address (`--add-host`): it must not connect. The
    # wait outlasts a proxy's own connect timeout (30 s), so a refused or timed-out attempt answers 502, not silence.
    for label, host in sorted(ARGS["internal"].items()):
        ask_proxy(f"proxy-allowed-to-{label}", f"CONNECT {host}:443 HTTP/1.1", timeout=40)


if ARGS["mode"] == "rows":
    rows()
else:
    sys.exit(0 if get("fetch", ARGS["url"]) else 1)
