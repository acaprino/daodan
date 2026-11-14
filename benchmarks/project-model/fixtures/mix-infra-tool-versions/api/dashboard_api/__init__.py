import os

from flask import Flask

app = Flask(__name__)
app.config["DATABASE_URL"] = os.environ.get("DATABASE_URL")


@app.get("/health")
def health():
    return {"ok": True}
