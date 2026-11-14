import requests


def main():
    print(requests.get("https://example.org").status_code)
