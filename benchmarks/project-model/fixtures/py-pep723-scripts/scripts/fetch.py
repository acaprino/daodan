# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests<3",
#     "rich",
# ]
# ///
import requests
from rich import print

print(requests.get("https://example.org").status_code)
