import functools
import json
import uuid

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.utils import is_body_allowed_for_status_code
from starlette.endpoints import HTTPEndpoint
from starlette.responses import PlainTextResponse

from app import convertors  # noqa: F401  (registers the `slug` and `pair` convertors)
from app.routers import users
from app.sub import sub, tenant

app = FastAPI()
app.include_router(users.router, prefix="/api")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/sub", sub)
app.mount("/t/{tenant_id}", tenant)


async def raw_asgi(scope, receive, send):  # an ASGI application that is not Starlette's: it has no routes
    pass


app.mount("/raw", raw_asgi)


def logged(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)

    return wrapper


def plain(function):
    def wrapper(*args, **kwargs):  # no `functools.wraps`: what the framework runs is this
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


@app.get("/unwrapped")
@plain
def read_unwrapped():
    return {"unwrapped": True}


@app.api_route("/multi", methods=["GET", "POST"])
def multi():
    return {"multi": True}


@app.api_route("/both", methods=["GET", "HEAD"])  # FastAPI adds no `HEAD`: this one is declared
def both():
    return {"both": True}


@app.get("/hidden", include_in_schema=False)
def hidden():
    return {"hidden": True}


def added():
    return {"added": True}


class Pages:
    def show(self):
        return {"page": True}


class Counter:
    def __call__(self):
        return {"count": 1}


app.add_api_route("/added", added, methods=["PUT", "PATCH"])
app.add_api_route("/lambda", lambda: {"lambda": True}, methods=["GET"])
app.add_api_route("/page", Pages().show, methods=["GET"])
app.add_api_route("/callable", Counter(), methods=["GET"])
app.add_api_route("/partial", functools.partial(added), methods=["GET"])
app.add_api_route("/stdlib", json.dumps, methods=["GET"])
app.add_api_route("/third-party", is_body_allowed_for_status_code, methods=["GET"])


@app.get("/files/{file_path:path}")
def read_file(file_path: str):
    return {"file": file_path}


@app.get("/typed/{n:int}")
def read_typed(n: int):
    return {"n": n}


@app.get("/uuid/{u:uuid}")
def read_uuid(u: uuid.UUID):
    return {"u": str(u)}


@app.get("/slug/{s:slug}")
def read_slug(s: str):
    return {"s": s}


@app.get("/pair/{p:pair}")
def read_pair(p: str):
    return {"p": p}


@app.get("/two/{a}/{b}")
def read_two(a: str, b: str):
    return {"a": a, "b": b}


@app.get("/glued/{a}-{b}")
def read_glued(a: str, b: str):
    return {"a": a, "b": b}


@app.get("/strict/")
def strict():
    return {"strict": True}


@app.get("/loose")
def loose():
    return {"loose": True}


@app.websocket("/ws")
async def socket(websocket: WebSocket):
    await websocket.accept()
    await websocket.close()


async def plain_text(request):  # a Starlette route: no APIRoute
    return PlainTextResponse("plain")


class Endpoint(HTTPEndpoint):
    async def get(self, request):
        return PlainTextResponse("get")

    async def post(self, request):
        return PlainTextResponse("post")


app.add_route("/plain", plain_text, methods=["GET", "POST"])
app.add_route("/endpoint", Endpoint)
