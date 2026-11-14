import os

import redis
from fastapi import FastAPI
from sqlalchemy import create_engine

app = FastAPI()
engine = create_engine(os.environ["DATABASE_URL"])
cache = redis.Redis.from_url(os.environ["REDIS_URL"])


@app.get("/health")
def health():
    return {"ok": True}
