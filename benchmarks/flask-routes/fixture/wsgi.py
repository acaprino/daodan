import functools
import json

from flask import Flask
from flask.views import MethodView, View
from werkzeug.routing import BaseConverter, PathConverter
from werkzeug.utils import redirect

from admin.blueprint import assets, bp, make_blueprint


class SlugConverter(BaseConverter):
    regex = "[a-z0-9-]+"


class TailConverter(PathConverter):
    pass


class TailRegexConverter(PathConverter):
    regex = ".+"


class PairConverter(BaseConverter):
    regex = "[^/]+/[^/]+"


app = Flask(__name__)
app.url_map.converters.update(slug=SlugConverter, tail=TailConverter, tailre=TailRegexConverter, pair=PairConverter)
app.register_blueprint(bp)
app.register_blueprint(assets)
app.register_blueprint(make_blueprint())


def guarded(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        return view(*args, **kwargs)

    return wrapper


def plain(view):
    def wrapper(*args, **kwargs):
        return view(*args, **kwargs)

    return wrapper


@app.route("/")
def index():
    return "index"


@app.post("/items")
def create_item():
    return "created"


@app.get("/wrapped")
@guarded
def wrapped():
    return "wrapped"


@app.get("/unwrapped")
@plain
def unwrapped():
    return "unwrapped"


class Pages:
    def show(self):
        return "page"


app.add_url_rule("/page", view_func=Pages().show)
app.add_url_rule("/lambda", endpoint="lam", view_func=lambda: "lam")


def greet(name):
    return name


app.add_url_rule("/partial", endpoint="partial", view_func=functools.partial(greet, "x"))


class Counter:
    def __call__(self):
        return "counter"


app.add_url_rule("/callable", endpoint="callable", view_func=Counter())


class Orders(MethodView):
    def get(self):
        return "orders"

    def post(self):
        return "created"


class Hello(View):
    methods = ["GET"]

    def dispatch_request(self):
        return "hello"


app.add_url_rule("/orders", view_func=Orders.as_view("orders"))
app.add_url_rule("/hello", view_func=Hello.as_view("hello"))


@app.route("/options", methods=["OPTIONS"])
def options_only():
    return ""


@app.get("/int/<int:id>")
def by_int(id):
    return str(id)


@app.get("/string/<string:name>")
def by_string(name):
    return name


@app.get("/uuid/<uuid:u>")
def by_uuid(u):
    return str(u)


@app.route("/files/<path:name>", methods=["GET", "PUT"])
def by_path(name):
    return name


@app.get("/slug/<slug:s>")
def by_slug(s):
    return s


@app.get("/tail/<tail:rest>")
def by_tail(rest):
    return rest


@app.get("/tailre/<tailre:rest>")
def by_tailre(rest):
    return rest


@app.get("/pair/<pair:p>")
def by_pair(p):
    return p


@app.get("/glued/<a>-<b>")
def glued(a, b):
    return a + b


@app.get("/two/<int:x>/<int:y>")
def two(x, y):
    return f"{x}{y}"


@app.get("/strict/")
def strict_with_slash():
    return "strict"


@app.get("/loose")
def loose_without_slash():
    return "loose"


@app.get("/relaxed/", strict_slashes=False)
def relaxed():
    return "relaxed"


def on_subdomain():
    return "sub"


app.add_url_rule("/sub", endpoint="sub", view_func=on_subdomain, subdomain="api")
app.add_url_rule("/stdlib", endpoint="stdlib", view_func=json.dumps)


@app.route("/head-only", methods=["HEAD"])
def head_only():
    return ""


@app.route("/get-options", methods=["GET", "OPTIONS"])
def get_options():
    return ""


app.add_url_rule("/built", endpoint="built", build_only=True)
app.add_url_rule("/old", endpoint="old", redirect_to="/new")
app.add_url_rule("/third-party", endpoint="third_party", view_func=redirect)


class Docs:
    def page(self):
        return """first line
second line at column zero
"""


app.add_url_rule("/docs", endpoint="docs", view_func=Docs().page)


def make_view():
    @app.get("/nested-doc")
    def nested_doc():
        return """a
at column zero
"""

    return nested_doc


make_view()
