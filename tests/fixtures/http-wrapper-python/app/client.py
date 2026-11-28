# The wrappers of requests the proof proves: the URL is a parameter, the method is the function's or a literal.
import requests


def load(url):
    return requests.get(url).json()


def create(url, body):
    return requests.post(url, json=body)


def second(token, url):
    return requests.put(url, headers={"Authorization": token})


def typed(url: str, timeout: float = 5.0):
    return requests.patch(url, timeout=timeout)


def defaulted(url="/api/health"):
    return requests.head(url)


def positional(url, /):
    return requests.delete(url)


def probe(url):
    return requests.options(url)


def generic(url):
    return requests.request("POST", url)


class Api:
    def fetch(self, url):
        return requests.get(url)
