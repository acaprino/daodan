import functools

from fastapi import FastAPI

from app.routers import users

app = FastAPI()
app.include_router(users.router, prefix="/api")


def logged(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)

    return wrapper


@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item": item_id}


@app.post("/items", status_code=201)
async def create_item(name: str):
    return {"name": name}


@app.get("/logged")
@logged
def read_logged():
    return {"logged": True}


def added():
    return {"added": True}


app.add_api_route("/added", added, methods=["PUT", "PATCH"])
app.add_api_route("/lambda", lambda: {"lambda": True}, methods=["GET"])
