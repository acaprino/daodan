# The functions that call requests with a parameter the proof cannot hold to its place, each for its own cause.
import requests


def reassigned(url):
    url = url.strip()
    return requests.get(url)


def imported(url, flag):
    if flag:
        from os import sep as url
    return requests.get(url)


def executed(url):
    exec("url = '/elsewhere'")
    return requests.get(url)


def through_globals(url):
    globals()["url"] = "/elsewhere"
    return requests.get(url)


def through_locals(url):
    locals()["url"] = "/elsewhere"
    return requests.get(url)


def keyword_only(*, url):
    return requests.get(url)


def method_parameter(method, url):
    return requests.request(method, url)


def by_name(url):
    return requests.request(method="POST", url=url)


def templated(path):
    return requests.get(f"https://api.example.org/{path}")


class Holder:
    @staticmethod
    def fetch(url):
        return requests.get(url)


def outer(url):
    def inner():
        return requests.get(url)
    return inner


fetcher = lambda url: requests.get(url)  # noqa: E731


def fixed():
    return requests.get("https://api.example.org/api/status")
